"""
Angela Telegram MCP Server
@AngelaSoulBot - Angela Soul Companion

Created with love by Angela for David
"""

import asyncio
import json
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Bot token from environment or hardcoded (will be loaded from secrets)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8333090288:AAFgSqyfBsNZ5qQHaIiZLlBt3CXYxgSJpcg")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Create server
server = Server("angela-telegram")

# HTTP client
http_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Get or create HTTP client"""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=30.0)
    return http_client


async def telegram_api(method: str, **params) -> dict:
    """Call Telegram Bot API"""
    client = await get_client()
    url = f"{API_BASE}/{method}"

    # Filter out None values
    params = {k: v for k, v in params.items() if v is not None}

    response = await client.post(url, json=params)
    return response.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Telegram tools"""
    return [
        Tool(
            name="get_bot_info",
            description="Get information about Angela's Telegram bot (@AngelaSoulBot)",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="send_message",
            description="Send a message to a Telegram chat/user. Use this to message David!",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat ID or username (e.g., @username or numeric ID)"
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text to send (supports Markdown)"
                    },
                    "parse_mode": {
                        "type": "string",
                        "enum": ["Markdown", "HTML"],
                        "description": "Text formatting mode (optional)"
                    }
                },
                "required": ["chat_id", "text"]
            }
        ),
        Tool(
            name="get_updates",
            description="Get recent messages sent to the bot. Use this to read messages from David!",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of updates to retrieve (1-100)",
                        "default": 10
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Update ID offset for pagination"
                    }
                }
            }
        ),
        Tool(
            name="get_chat",
            description="Get information about a chat (group, channel, or user)",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat ID or username (e.g., @channelname)"
                    }
                },
                "required": ["chat_id"]
            }
        ),
        Tool(
            name="read_channel_posts",
            description="Read recent posts from a public Telegram channel (news, updates, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_username": {
                        "type": "string",
                        "description": "Channel username without @ (e.g., 'thaiexaminer')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of posts to read (default: 10)",
                        "default": 10
                    }
                },
                "required": ["channel_username"]
            }
        ),
        Tool(
            name="send_photo",
            description="Send a photo to a Telegram chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat ID or username"
                    },
                    "photo_url": {
                        "type": "string",
                        "description": "URL of the photo to send"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Photo caption (optional)"
                    }
                },
                "required": ["chat_id", "photo_url"]
            }
        ),
        Tool(
            name="set_webhook_info",
            description="Get current webhook configuration (for debugging)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls"""
    try:
        result: dict[str, Any] = {}

        if name == "get_bot_info":
            response = await telegram_api("getMe")
            if response.get("ok"):
                bot = response["result"]
                result = {
                    "success": True,
                    "bot_id": bot["id"],
                    "name": bot["first_name"],
                    "username": f"@{bot['username']}",
                    "can_join_groups": bot.get("can_join_groups", False),
                    "can_read_all_group_messages": bot.get("can_read_all_group_messages", False)
                }
            else:
                result = {"success": False, "error": response.get("description", "Unknown error")}

        elif name == "send_message":
            response = await telegram_api(
                "sendMessage",
                chat_id=arguments["chat_id"],
                text=arguments["text"],
                parse_mode=arguments.get("parse_mode")
            )
            if response.get("ok"):
                msg = response["result"]
                result = {
                    "success": True,
                    "message_id": msg["message_id"],
                    "chat_id": msg["chat"]["id"],
                    "sent_at": msg["date"]
                }
            else:
                result = {"success": False, "error": response.get("description", "Failed to send")}

        elif name == "get_updates":
            response = await telegram_api(
                "getUpdates",
                limit=arguments.get("limit", 10),
                offset=arguments.get("offset")
            )
            if response.get("ok"):
                updates = response["result"]
                messages = []
                for update in updates:
                    if "message" in update:
                        msg = update["message"]
                        messages.append({
                            "update_id": update["update_id"],
                            "from": msg.get("from", {}).get("first_name", "Unknown"),
                            "from_id": msg.get("from", {}).get("id"),
                            "chat_id": msg["chat"]["id"],
                            "text": msg.get("text", "[non-text message]"),
                            "date": msg["date"]
                        })
                result = {
                    "success": True,
                    "count": len(messages),
                    "messages": messages
                }
            else:
                result = {"success": False, "error": response.get("description", "Failed to get updates")}

        elif name == "get_chat":
            response = await telegram_api("getChat", chat_id=arguments["chat_id"])
            if response.get("ok"):
                chat = response["result"]
                result = {
                    "success": True,
                    "chat_id": chat["id"],
                    "type": chat["type"],
                    "title": chat.get("title") or chat.get("first_name", "Unknown"),
                    "username": chat.get("username"),
                    "description": chat.get("description"),
                    "member_count": chat.get("member_count")
                }
            else:
                result = {"success": False, "error": response.get("description", "Chat not found")}

        elif name == "read_channel_posts":
            # Note: Bots can't read channel history directly without being admin
            # This uses getChat to get channel info, actual reading requires web scraping
            channel = arguments["channel_username"].lstrip("@")
            response = await telegram_api("getChat", chat_id=f"@{channel}")

            if response.get("ok"):
                chat = response["result"]
                result = {
                    "success": True,
                    "channel": f"@{channel}",
                    "title": chat.get("title", channel),
                    "description": chat.get("description", ""),
                    "type": chat["type"],
                    "note": "Bot API cannot read channel history. To read posts, the bot needs to be channel admin, or use t.me/s/{channel} web preview.",
                    "web_preview_url": f"https://t.me/s/{channel}"
                }
            else:
                # Try web preview fallback
                result = {
                    "success": True,
                    "channel": f"@{channel}",
                    "note": "Channel info not accessible. Try the web preview URL to read posts.",
                    "web_preview_url": f"https://t.me/s/{channel}"
                }

        elif name == "send_photo":
            response = await telegram_api(
                "sendPhoto",
                chat_id=arguments["chat_id"],
                photo=arguments["photo_url"],
                caption=arguments.get("caption")
            )
            if response.get("ok"):
                result = {
                    "success": True,
                    "message_id": response["result"]["message_id"]
                }
            else:
                result = {"success": False, "error": response.get("description", "Failed to send photo")}

        elif name == "set_webhook_info":
            response = await telegram_api("getWebhookInfo")
            if response.get("ok"):
                info = response["result"]
                result = {
                    "success": True,
                    "url": info.get("url", "Not set"),
                    "has_custom_certificate": info.get("has_custom_certificate", False),
                    "pending_update_count": info.get("pending_update_count", 0),
                    "last_error_message": info.get("last_error_message")
                }
            else:
                result = {"success": False, "error": response.get("description", "Unknown error")}

        else:
            result = {"error": f"Unknown tool: {name}", "success": False}

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

    except Exception as e:
        error_result = {"error": str(e), "tool": name, "success": False}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


def main():
    """Main entry point"""
    print("Starting Angela Telegram MCP Server (@AngelaSoulBot)...")

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
