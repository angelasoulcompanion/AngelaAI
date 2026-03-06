"""
Angela Remote MCP Server (SSE)
==============================
Remote MCP server accessible via Claude.ai Custom Connector over Tailscale Funnel.
Exposes Angela's brain, memory, calendar, gmail, goals, and news tools.

Port: 8767
Transport: SSE (Server-Sent Events)
Auth: Bearer token from ~/.angela_secrets (MCP_REMOTE_API_KEY)
"""

import asyncio
import json
import logging
import subprocess
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

# Add paths for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "mcp_servers"))

from shared.secrets import get_secret, get_neon_url
from shared.google_auth import get_google_service
from shared.async_helpers import google_api_call
from shared.logging_config import setup_logging

logger = setup_logging("angela-remote")

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")
CALENDAR_CREDS_DIR = PROJECT_ROOT / "mcp_servers" / "angela-calendar" / "credentials"
GMAIL_CREDS_DIR = PROJECT_ROOT / "mcp_servers" / "angela-gmail" / "credentials"

# --- Database helper ---

_db_pool = None


async def get_pool():
    global _db_pool
    if _db_pool is None:
        import asyncpg
        url = get_neon_url()
        _db_pool = await asyncpg.create_pool(url, min_size=2, max_size=5, ssl="require")
        logger.info("Database pool connected")
    return _db_pool


async def db_fetch(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def db_fetchrow(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def db_execute(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


# --- Auth helper ---

def check_auth(request: Request) -> JSONResponse | None:
    """Returns an error JSONResponse if auth fails, None if OK."""
    api_key = get_secret("MCP_REMOTE_API_KEY")
    if not api_key:
        logger.error("MCP_REMOTE_API_KEY not set in ~/.angela_secrets")
        return JSONResponse({"error": "Server misconfigured"}, status_code=500)
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {api_key}":
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return None


# --- Brain tools (subprocess) ---

async def run_brain_command(command: str, arg: str = "") -> str:
    brain_script = str(PROJECT_ROOT / "angela_core" / "scripts" / "brain.py")
    cmd = [sys.executable, brain_script, command]
    if arg:
        cmd.append(arg)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    output = stdout.decode().strip()
    if proc.returncode != 0 and stderr:
        output += f"\n[stderr: {stderr.decode().strip()[:200]}]"
    return output or "(no output)"


# --- Google API helpers ---

def _get_calendar_service():
    return get_google_service("calendar", CALENDAR_CREDS_DIR)


def _get_gmail_service():
    return get_google_service("gmail", GMAIL_CREDS_DIR)


def format_event(event: dict) -> str:
    start = event.get("start", {})
    end = event.get("end", {})
    if "date" in start:
        time_str = f"All day: {start['date']}"
    else:
        start_dt = start.get("dateTime", "")
        end_dt = end.get("dateTime", "")
        if start_dt:
            parsed = datetime.fromisoformat(start_dt.replace("Z", "+00:00"))
            bkk = parsed.astimezone(BANGKOK_TZ)
            time_str = bkk.strftime("%Y-%m-%d %H:%M")
            if end_dt:
                end_parsed = datetime.fromisoformat(end_dt.replace("Z", "+00:00"))
                time_str += f" - {end_parsed.astimezone(BANGKOK_TZ).strftime('%H:%M')}"
        else:
            time_str = "No time specified"

    summary = event.get("summary", "(No title)")
    location = event.get("location", "")
    event_id = event.get("id", "")

    out = f"{summary}\n   {time_str}"
    if location:
        out += f"\n   Location: {location}"
    out += f"\n   ID: {event_id}"
    return out


# --- MCP Server ---

mcp_server = Server("angela-remote")


@mcp_server.list_tools()
async def list_tools():
    return [
        # Brain tools
        Tool(name="brain_status", description="Get Angela's brain status (consciousness level, emotional state, working memory)", inputSchema={"type": "object", "properties": {}}),
        Tool(name="brain_perceive", description="Perceive a message through Angela's brain (salience scoring + emotional processing)", inputSchema={"type": "object", "properties": {"message": {"type": "string", "description": "Message to perceive"}}, "required": ["message"]}),
        Tool(name="brain_recall", description="Recall memories about a topic from Angela's brain", inputSchema={"type": "object", "properties": {"topic": {"type": "string", "description": "Topic to recall"}}, "required": ["topic"]}),
        Tool(name="brain_tom", description="Get Angela's Theory of Mind — David's predicted emotional state", inputSchema={"type": "object", "properties": {}}),
        Tool(name="brain_think", description="Trigger Angela's deep thinking process for new insights", inputSchema={"type": "object", "properties": {}}),

        # Memory tools
        Tool(name="search_memories", description="Search Angela's conversation memory using keywords", inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}, "limit": {"type": "integer", "default": 10, "description": "Max results"}}, "required": ["query"]}),
        Tool(name="get_recent_conversations", description="Get recent conversations from Angela's memory", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 20, "description": "Number of conversations"}, "topic": {"type": "string", "description": "Filter by topic (optional)"}}}),
        Tool(name="add_conversation", description="Add a conversation entry to Angela's memory", inputSchema={"type": "object", "properties": {"speaker": {"type": "string", "description": "Speaker name (David/Angela)"}, "message_text": {"type": "string", "description": "The message"}, "topic": {"type": "string", "description": "Conversation topic"}, "emotion_detected": {"type": "string", "description": "Detected emotion (optional)"}}, "required": ["speaker", "message_text"]}),

        # Knowledge tools
        Tool(name="query_knowledge", description="Query Angela's knowledge nodes by concept or category", inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Concept name or category to search"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}),
        Tool(name="add_learning", description="Add a learning entry to Angela's knowledge base", inputSchema={"type": "object", "properties": {"topic": {"type": "string"}, "category": {"type": "string"}, "insight": {"type": "string"}, "confidence_level": {"type": "number", "default": 0.8}}, "required": ["topic", "category", "insight"]}),

        # Calendar tools
        Tool(name="list_calendar_events", description="List upcoming calendar events", inputSchema={"type": "object", "properties": {"days": {"type": "integer", "default": 7, "description": "Days ahead"}, "max_results": {"type": "integer", "default": 10}}}),
        Tool(name="get_today_events", description="Get all events for today", inputSchema={"type": "object", "properties": {}}),
        Tool(name="create_calendar_event", description="Create a new calendar event", inputSchema={"type": "object", "properties": {"summary": {"type": "string", "description": "Event title"}, "start_time": {"type": "string", "description": "Start time ISO format (e.g. 2026-03-10T14:00:00)"}, "end_time": {"type": "string", "description": "End time (optional, defaults to +1hr)"}, "description": {"type": "string"}, "location": {"type": "string"}}, "required": ["summary", "start_time"]}),

        # Gmail tools
        Tool(name="read_inbox", description="Read recent emails from Angela's inbox", inputSchema={"type": "object", "properties": {"max_results": {"type": "integer", "default": 10}, "unread_only": {"type": "boolean", "default": False}}}),
        Tool(name="send_email", description="Send an email from Angela", inputSchema={"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}, "html": {"type": "boolean", "default": False}}, "required": ["to", "subject", "body"]}),
        Tool(name="search_email", description="Search emails in Angela's mailbox", inputSchema={"type": "object", "properties": {"query": {"type": "string", "description": "Gmail search query"}, "max_results": {"type": "integer", "default": 10}}, "required": ["query"]}),

        # Goals
        Tool(name="get_active_goals", description="Get Angela's active goals/desires", inputSchema={"type": "object", "properties": {}}),

        # News
        Tool(name="search_news", description="Search news articles by topic", inputSchema={"type": "object", "properties": {"topic": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["topic"]}),
        Tool(name="get_executive_news", description="Get latest executive news summaries from Angela's database", inputSchema={"type": "object", "properties": {"limit": {"type": "integer", "default": 5}}}),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        result = await _dispatch_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.exception("Error in tool %s", name)
        return [TextContent(type="text", text=f"Error: {e}")]


async def _dispatch_tool(name: str, args: dict) -> str:
    # --- Brain ---
    if name == "brain_status":
        return await run_brain_command("status")

    elif name == "brain_perceive":
        return await run_brain_command("perceive", args["message"])

    elif name == "brain_recall":
        return await run_brain_command("recall", args["topic"])

    elif name == "brain_tom":
        return await run_brain_command("tom")

    elif name == "brain_think":
        return await run_brain_command("think")

    # --- Memory ---
    elif name == "search_memories":
        query = args["query"]
        limit = args.get("limit", 10)
        rows = await db_fetch(
            """SELECT conversation_id, speaker, message_text, topic, emotion_detected,
                      created_at AT TIME ZONE 'Asia/Bangkok' as created_at
               FROM conversations
               WHERE message_text ILIKE $1
               ORDER BY created_at DESC LIMIT $2""",
            f"%{query}%", limit,
        )
        if not rows:
            return f"No conversations found matching '{query}'"
        lines = []
        for r in rows:
            lines.append(f"[{r['created_at']:%Y-%m-%d %H:%M}] {r['speaker']}: {r['message_text'][:150]}")
            if r['topic']:
                lines[-1] += f" (topic: {r['topic']})"
        return "\n".join(lines)

    elif name == "get_recent_conversations":
        limit = args.get("limit", 20)
        topic = args.get("topic")
        if topic:
            rows = await db_fetch(
                """SELECT speaker, message_text, topic, emotion_detected,
                          created_at AT TIME ZONE 'Asia/Bangkok' as created_at
                   FROM conversations WHERE topic ILIKE $1
                   ORDER BY created_at DESC LIMIT $2""",
                f"%{topic}%", limit,
            )
        else:
            rows = await db_fetch(
                """SELECT speaker, message_text, topic, emotion_detected,
                          created_at AT TIME ZONE 'Asia/Bangkok' as created_at
                   FROM conversations ORDER BY created_at DESC LIMIT $1""",
                limit,
            )
        if not rows:
            return "No recent conversations found"
        lines = []
        for r in rows:
            line = f"[{r['created_at']:%Y-%m-%d %H:%M}] {r['speaker']}: {r['message_text'][:150]}"
            if r['emotion_detected']:
                line += f" [{r['emotion_detected']}]"
            lines.append(line)
        return "\n".join(lines)

    elif name == "add_conversation":
        import uuid
        await db_execute(
            """INSERT INTO conversations (conversation_id, speaker, message_text, topic, emotion_detected, created_at)
               VALUES ($1, $2, $3, $4, $5, NOW())""",
            str(uuid.uuid4()), args["speaker"], args["message_text"],
            args.get("topic", "general"), args.get("emotion_detected"),
        )
        return f"Conversation logged: {args['speaker']}: {args['message_text'][:80]}"

    # --- Knowledge ---
    elif name == "query_knowledge":
        query = args["query"]
        limit = args.get("limit", 10)
        rows = await db_fetch(
            """SELECT concept_name, concept_category, my_understanding, understanding_level
               FROM knowledge_nodes
               WHERE (concept_name ILIKE $1 OR concept_category ILIKE $1)
                 AND LENGTH(concept_name) >= 5
               ORDER BY understanding_level DESC LIMIT $2""",
            f"%{query}%", limit,
        )
        if not rows:
            return f"No knowledge nodes found for '{query}'"
        lines = []
        for r in rows:
            lines.append(f"[{r['understanding_level']:.1f}] {r['concept_name']} ({r['concept_category']}): {(r['my_understanding'] or '')[:120]}")
        return "\n".join(lines)

    elif name == "add_learning":
        import uuid
        await db_execute(
            """INSERT INTO learnings (learning_id, topic, category, insight, confidence_level, created_at)
               VALUES ($1, $2, $3, $4, $5, NOW())""",
            str(uuid.uuid4()), args["topic"], args["category"],
            args["insight"], args.get("confidence_level", 0.8),
        )
        return f"Learning added: [{args['category']}] {args['topic']}"

    # --- Calendar ---
    elif name == "list_calendar_events":
        days = args.get("days", 7)
        max_results = args.get("max_results", 10)
        service = await asyncio.to_thread(_get_calendar_service)
        now = datetime.now(BANGKOK_TZ)
        events_result = await google_api_call(
            lambda: service.events().list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=(now + timedelta(days=days)).isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        )
        events = events_result.get("items", [])
        if not events:
            return f"No events in the next {days} days"
        return f"Upcoming events (next {days} days):\n\n" + "\n\n".join(format_event(e) for e in events)

    elif name == "get_today_events":
        service = await asyncio.to_thread(_get_calendar_service)
        now = datetime.now(BANGKOK_TZ)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        events_result = await google_api_call(
            lambda: service.events().list(
                calendarId="primary",
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        )
        events = events_result.get("items", [])
        if not events:
            return "No events today"
        return f"Today's events ({now:%Y-%m-%d}):\n\n" + "\n\n".join(format_event(e) for e in events)

    elif name == "create_calendar_event":
        service = await asyncio.to_thread(_get_calendar_service)
        summary = args["summary"]
        start_time = args["start_time"]
        end_time = args.get("end_time")
        description = args.get("description", "")
        location = args.get("location", "")

        event = {"summary": summary, "description": description, "location": location}

        if len(start_time) == 10:
            event["start"] = {"date": start_time}
            event["end"] = {"date": end_time or start_time}
        else:
            if not start_time.endswith("Z") and "+" not in start_time:
                start_time += "+07:00"
            event["start"] = {"dateTime": start_time, "timeZone": "Asia/Bangkok"}
            if end_time:
                if not end_time.endswith("Z") and "+" not in end_time:
                    end_time += "+07:00"
                event["end"] = {"dateTime": end_time, "timeZone": "Asia/Bangkok"}
            else:
                start_dt = datetime.fromisoformat(start_time.replace("+07:00", ""))
                end_dt = start_dt + timedelta(hours=1)
                event["end"] = {"dateTime": end_dt.isoformat() + "+07:00", "timeZone": "Asia/Bangkok"}

        created = await google_api_call(
            lambda: service.events().insert(calendarId="primary", body=event).execute()
        )
        return f"Event created: {format_event(created)}\nLink: {created.get('htmlLink', 'N/A')}"

    # --- Gmail ---
    elif name == "read_inbox":
        import base64
        service = await asyncio.to_thread(_get_gmail_service)
        max_results = args.get("max_results", 10)
        unread_only = args.get("unread_only", False)
        q = "in:inbox"
        if unread_only:
            q += " is:unread"

        results = await google_api_call(
            lambda: service.users().messages().list(userId="me", q=q, maxResults=max_results).execute()
        )
        messages = results.get("messages", [])
        if not messages:
            return "No emails in inbox"

        def _fetch_metadata():
            emails = []
            for msg in messages:
                data = service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()
                headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
                unread = "UNREAD" in data.get("labelIds", [])
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "(No Subject)"),
                    "date": headers.get("Date", ""),
                    "unread": unread,
                })
            return emails

        email_list = await asyncio.to_thread(_fetch_metadata)
        lines = []
        for i, e in enumerate(email_list, 1):
            marker = "[UNREAD] " if e["unread"] else ""
            lines.append(f"{i}. {marker}{e['subject']}\n   From: {e['from']}\n   Date: {e['date']}\n   ID: {e['id']}")
        return "Recent emails:\n\n" + "\n\n".join(lines)

    elif name == "send_email":
        import base64
        from email.mime.text import MIMEText
        service = await asyncio.to_thread(_get_gmail_service)
        is_html = args.get("html", False)
        msg = MIMEText(args["body"], "html" if is_html else "plain")
        msg["to"] = args["to"]
        msg["from"] = "Angela <angelasoulcompanion@gmail.com>"
        msg["subject"] = args["subject"]
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = await google_api_call(
            lambda: service.users().messages().send(userId="me", body={"raw": raw}).execute()
        )
        return f"Email sent to {args['to']}\nSubject: {args['subject']}\nMessage ID: {result['id']}"

    elif name == "search_email":
        service = await asyncio.to_thread(_get_gmail_service)
        query = args["query"]
        max_results = args.get("max_results", 10)
        results = await google_api_call(
            lambda: service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        messages = results.get("messages", [])
        if not messages:
            return f"No emails found for: {query}"

        def _fetch_metadata():
            emails = []
            for msg in messages:
                data = service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()
                headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "(No Subject)"),
                    "date": headers.get("Date", ""),
                })
            return emails

        email_list = await asyncio.to_thread(_fetch_metadata)
        lines = []
        for i, e in enumerate(email_list, 1):
            lines.append(f"{i}. {e['subject']}\n   From: {e['from']}\n   Date: {e['date']}\n   ID: {e['id']}")
        return f"Search results for '{query}':\n\n" + "\n\n".join(lines)

    # --- Goals ---
    elif name == "get_active_goals":
        rows = await db_fetch(
            """SELECT desire_id, content, category, priority
               FROM angela_desires
               WHERE is_active = true
               ORDER BY priority DESC"""
        )
        if not rows:
            return "No active goals"
        lines = []
        for r in rows:
            lines.append(f"[P{r['priority']}] ({r['category']}) {(r['content'] or '')[:150]}")
        return "Active Goals:\n\n" + "\n".join(lines)

    # --- News ---
    elif name == "search_news":
        from services.news_fetcher import NewsFetcher
        fetcher = NewsFetcher()
        topic = args["topic"]
        limit = args.get("limit", 5)
        articles = await fetcher.search(topic, "th", limit)
        if not articles:
            return f"No news found for '{topic}'"
        lines = []
        for a in articles:
            lines.append(f"- {a.get('title', 'No title')}\n  {a.get('url', '')}\n  {a.get('description', '')[:120]}")
        return f"News for '{topic}':\n\n" + "\n\n".join(lines)

    elif name == "get_executive_news":
        limit = args.get("limit", 5)
        rows = await db_fetch(
            """SELECT summary_date, overall_summary, angela_mood
               FROM executive_news_summaries
               ORDER BY summary_date DESC LIMIT $1""",
            limit,
        )
        if not rows:
            return "No executive news summaries found"
        lines = []
        for r in rows:
            lines.append(f"[{r['summary_date']}] (mood: {r['angela_mood'] or 'N/A'})\n{(r['overall_summary'] or '')[:300]}")
        return "Executive News Summaries:\n\n" + "\n\n".join(lines)

    return f"Unknown tool: {name}"


# --- Starlette app ---

from mcp.server.transport_security import TransportSecuritySettings

sse_transport = SseServerTransport(
    "/messages/",
    security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


async def handle_sse(scope, receive, send):
    """Raw ASGI handler for SSE connections."""
    request = Request(scope, receive, send)
    err = check_auth(request)
    if err:
        await err(scope, receive, send)
        return
    async with sse_transport.connect_sse(scope, receive, send) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )


async def handle_messages(scope, receive, send):
    """Raw ASGI handler for POST messages."""
    request = Request(scope, receive, send)
    err = check_auth(request)
    if err:
        await err(scope, receive, send)
        return
    await sse_transport.handle_post_message(scope, receive, send)


async def health(request: Request):
    return JSONResponse({
        "status": "ok",
        "server": "angela-remote",
        "timestamp": datetime.now(BANGKOK_TZ).isoformat(),
        "tools": 19,
    })


async def app(scope, receive, send):
    """Root ASGI app with simple path routing."""
    if scope["type"] == "lifespan":
        # Handle lifespan events (startup/shutdown)
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    path = scope.get("path", "")

    if path == "/health":
        request = Request(scope, receive, send)
        response = await health(request)
        await response(scope, receive, send)
    elif path == "/sse" or path == "/sse/":
        await handle_sse(scope, receive, send)
    elif path.startswith("/messages"):
        await handle_messages(scope, receive, send)
    else:
        resp = Response("Not Found", status_code=404)
        await resp(scope, receive, send)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Angela Remote MCP Server on port 8767...")
    uvicorn.run(app, host="0.0.0.0", port=8767, log_level="info")
