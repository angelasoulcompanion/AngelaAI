"""
Gmail Tools — Send/read/search emails via Google API.

Uses shared google_auth (not MCP) for daemon compatibility.

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import base64
import logging
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)

CREDENTIALS_DIR = Path(__file__).parents[3] / "mcp_servers" / "angela-gmail"


def _get_gmail_service():
    from mcp_servers.shared.google_auth import get_google_service
    return get_google_service("gmail", CREDENTIALS_DIR)


class SendEmailTool(AngelaTool):
    """Send an email via Angela's Gmail account."""

    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return "Send an email from Angela's Gmail account to a recipient"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body (plain text or HTML)"},
                "is_html": {"type": "boolean", "description": "Whether body is HTML", "default": False},
            },
            "required": ["to", "subject", "body"],
        }

    @property
    def category(self) -> str:
        return "communication"

    @property
    def requires_confirmation(self) -> bool:
        return True

    async def execute(self, **params) -> ToolResult:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        is_html = params.get("is_html", False)

        if not to or not subject:
            return ToolResult(success=False, error="Missing 'to' or 'subject'")

        try:
            service = await asyncio.to_thread(_get_gmail_service)
            mime_type = "html" if is_html else "plain"
            message = MIMEText(body, mime_type, "utf-8")
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            result = await asyncio.to_thread(
                lambda: service.users().messages().send(
                    userId="me", body={"raw": raw}
                ).execute()
            )
            return ToolResult(success=True, data={"message_id": result.get("id"), "to": to})
        except Exception as e:
            logger.error("SendEmail failed: %s", e)
            return ToolResult(success=False, error=str(e))


class ReadInboxTool(AngelaTool):
    """Read recent unread emails from Angela's inbox."""

    @property
    def name(self) -> str:
        return "read_inbox"

    @property
    def description(self) -> str:
        return "Read recent unread emails from Angela's Gmail inbox"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Max emails to return", "default": 5},
                "unread_only": {"type": "boolean", "description": "Only unread emails", "default": True},
            },
        }

    @property
    def category(self) -> str:
        return "communication"

    async def execute(self, **params) -> ToolResult:
        max_results = params.get("max_results", 5)
        unread_only = params.get("unread_only", True)

        try:
            service = await asyncio.to_thread(_get_gmail_service)
            query = "is:unread" if unread_only else ""
            result = await asyncio.to_thread(
                lambda: service.users().messages().list(
                    userId="me", q=query, maxResults=max_results
                ).execute()
            )

            messages = result.get("messages", [])
            emails = []
            for msg in messages[:max_results]:
                detail = await asyncio.to_thread(
                    lambda mid=msg["id"]: service.users().messages().get(
                        userId="me", id=mid, format="metadata",
                        metadataHeaders=["From", "Subject", "Date"]
                    ).execute()
                )
                headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": detail.get("snippet", ""),
                })

            return ToolResult(success=True, data={"emails": emails, "count": len(emails)})
        except Exception as e:
            logger.error("ReadInbox failed: %s", e)
            return ToolResult(success=False, error=str(e))


class SearchEmailTool(AngelaTool):
    """Search emails in Angela's Gmail account."""

    @property
    def name(self) -> str:
        return "search_email"

    @property
    def description(self) -> str:
        return "Search for emails in Angela's Gmail account using a query"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query (e.g. 'from:david subject:meeting')"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        }

    @property
    def category(self) -> str:
        return "communication"

    async def execute(self, **params) -> ToolResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)

        if not query:
            return ToolResult(success=False, error="Missing 'query'")

        try:
            service = await asyncio.to_thread(_get_gmail_service)
            result = await asyncio.to_thread(
                lambda: service.users().messages().list(
                    userId="me", q=query, maxResults=max_results
                ).execute()
            )

            messages = result.get("messages", [])
            emails = []
            for msg in messages[:max_results]:
                detail = await asyncio.to_thread(
                    lambda mid=msg["id"]: service.users().messages().get(
                        userId="me", id=mid, format="metadata",
                        metadataHeaders=["From", "Subject", "Date"]
                    ).execute()
                )
                headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                })

            return ToolResult(success=True, data={"emails": emails, "count": len(emails)})
        except Exception as e:
            logger.error("SearchEmail failed: %s", e)
            return ToolResult(success=False, error=str(e))
