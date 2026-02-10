"""
Angela Gmail MCP Server

Send and read emails from Angela's Gmail account (angelasoulcompanion@gmail.com)
"""

import asyncio
import base64
import mimetypes
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any

# Add mcp_servers to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from googleapiclient.errors import HttpError

from shared import ANGELA_EMAIL
from shared.google_auth import get_google_service
from shared.logging_config import setup_logging
from shared.async_helpers import google_api_call

# Paths for credentials
CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"

# Setup logging
logger = setup_logging("angela-gmail")

# Create MCP Server
server = Server("angela-gmail")


def _get_service():
    """Get authenticated Gmail API service."""
    return get_google_service("gmail", CREDENTIALS_DIR)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Gmail tools."""
    return [
        Tool(
            name="send_email",
            description="Send an email from Angela (angelasoulcompanion@gmail.com)",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text or HTML)"
                    },
                    "html": {
                        "type": "boolean",
                        "description": "Whether body is HTML (default: false)",
                        "default": False
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC recipients (comma-separated)",
                    },
                    "bcc": {
                        "type": "string",
                        "description": "BCC recipients (comma-separated)",
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to attach (absolute paths)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="read_inbox",
            description="Read recent emails from Angela's inbox",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10)",
                        "default": 10
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only return unread emails (default: false)",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="search_emails",
            description="Search emails in Angela's mailbox",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:someone@example.com', 'subject:hello', 'is:unread')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_email",
            description="Get full content of a specific email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "Email ID (from read_inbox or search_emails)"
                    }
                },
                "required": ["email_id"]
            }
        ),
        Tool(
            name="mark_as_read",
            description="Mark an email as read",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "Email ID to mark as read"
                    }
                },
                "required": ["email_id"]
            }
        ),
        Tool(
            name="reply_to_email",
            description="Reply to an existing email",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "Email ID to reply to"
                    },
                    "body": {
                        "type": "string",
                        "description": "Reply body"
                    },
                    "html": {
                        "type": "boolean",
                        "description": "Whether body is HTML (default: false)",
                        "default": False
                    }
                },
                "required": ["email_id", "body"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        service = await asyncio.to_thread(_get_service)

        if name == "send_email":
            return await send_email(service, arguments)
        elif name == "read_inbox":
            return await read_inbox(service, arguments)
        elif name == "search_emails":
            return await search_emails(service, arguments)
        elif name == "get_email":
            return await get_email(service, arguments)
        elif name == "mark_as_read":
            return await mark_as_read(service, arguments)
        elif name == "reply_to_email":
            return await reply_to_email(service, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Setup required: {str(e)}")]
    except HttpError as e:
        logger.error("Gmail API error: %s", e)
        return [TextContent(type="text", text=f"Gmail API error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in %s", name)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def send_email(service, args: dict) -> list[TextContent]:
    """Send an email with optional attachments."""
    to = args["to"]
    subject = args["subject"]
    body = args["body"]
    is_html = args.get("html", False)
    cc = args.get("cc", "")
    bcc = args.get("bcc", "")
    attachments = args.get("attachments", [])

    # Create message - use multipart/mixed if we have attachments
    if attachments:
        message = MIMEMultipart('mixed')
        if is_html:
            body_part = MIMEMultipart('alternative')
            body_part.attach(MIMEText(body, 'html'))
            message.attach(body_part)
        else:
            message.attach(MIMEText(body, 'plain'))

        attached_files = []
        for file_path in attachments:
            path = Path(file_path)
            if not path.exists():
                return [TextContent(
                    type="text",
                    text=f"Error: Attachment file not found: {file_path}"
                )]

            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type is None:
                mime_type = 'application/octet-stream'

            main_type, sub_type = mime_type.split('/', 1)

            with open(path, 'rb') as f:
                file_data = f.read()

            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(file_data)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=path.name
            )
            message.attach(attachment)
            attached_files.append(path.name)

    elif is_html:
        message = MIMEMultipart('alternative')
        message.attach(MIMEText(body, 'html'))
    else:
        message = MIMEText(body)

    message['to'] = to
    message['from'] = f"Angela <{ANGELA_EMAIL}>"
    message['subject'] = subject

    if cc:
        message['cc'] = cc
    if bcc:
        message['bcc'] = bcc

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = await google_api_call(
        lambda: service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
    )

    response = f"Email sent successfully!\n"
    response += f"To: {to}\n"
    response += f"Subject: {subject}\n"
    if attachments:
        response += f"Attachments: {', '.join(attached_files)}\n"
    response += f"Message ID: {result['id']}"

    return [TextContent(type="text", text=response)]


async def read_inbox(service, args: dict) -> list[TextContent]:
    """Read recent emails from inbox."""
    max_results = args.get("max_results", 10)
    unread_only = args.get("unread_only", False)

    query = "in:inbox"
    if unread_only:
        query += " is:unread"

    results = await google_api_call(
        lambda: service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
    )

    messages = results.get('messages', [])

    if not messages:
        return [TextContent(type="text", text="No emails found in inbox.")]

    # Fetch all message metadata in a single thread to avoid N blocking calls
    def _fetch_all_metadata():
        email_list = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
            is_unread = 'UNREAD' in msg_data.get('labelIds', [])

            email_list.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', '(No Subject)'),
                'date': headers.get('Date', 'Unknown'),
                'unread': is_unread
            })
        return email_list

    email_list = await asyncio.to_thread(_fetch_all_metadata)

    output = "Recent emails:\n\n"
    for i, email in enumerate(email_list, 1):
        unread_marker = "[UNREAD] " if email['unread'] else ""
        output += f"{i}. {unread_marker}{email['subject']}\n"
        output += f"   From: {email['from']}\n"
        output += f"   Date: {email['date']}\n"
        output += f"   ID: {email['id']}\n\n"

    return [TextContent(type="text", text=output)]


async def search_emails(service, args: dict) -> list[TextContent]:
    """Search emails with Gmail query."""
    query = args["query"]
    max_results = args.get("max_results", 10)

    results = await google_api_call(
        lambda: service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
    )

    messages = results.get('messages', [])

    if not messages:
        return [TextContent(type="text", text=f"No emails found for query: {query}")]

    def _fetch_all_metadata():
        email_list = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}

            email_list.append({
                'id': msg['id'],
                'from': headers.get('From', 'Unknown'),
                'subject': headers.get('Subject', '(No Subject)'),
                'date': headers.get('Date', 'Unknown')
            })
        return email_list

    email_list = await asyncio.to_thread(_fetch_all_metadata)

    output = f"Search results for '{query}':\n\n"
    for i, email in enumerate(email_list, 1):
        output += f"{i}. {email['subject']}\n"
        output += f"   From: {email['from']}\n"
        output += f"   Date: {email['date']}\n"
        output += f"   ID: {email['id']}\n\n"

    return [TextContent(type="text", text=output)]


async def get_email(service, args: dict) -> list[TextContent]:
    """Get full email content."""
    email_id = args["email_id"]

    msg_data = await google_api_call(
        lambda: service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()
    )

    headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}

    # Extract body
    body = ""
    payload = msg_data['payload']

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
    else:
        data = payload['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')

    output = f"Email Details:\n"
    output += f"{'=' * 50}\n"
    output += f"From: {headers.get('From', 'Unknown')}\n"
    output += f"To: {headers.get('To', 'Unknown')}\n"
    output += f"Subject: {headers.get('Subject', '(No Subject)')}\n"
    output += f"Date: {headers.get('Date', 'Unknown')}\n"
    output += f"{'=' * 50}\n\n"
    output += body if body else "(No body content)"

    return [TextContent(type="text", text=output)]


async def mark_as_read(service, args: dict) -> list[TextContent]:
    """Mark email as read."""
    email_id = args["email_id"]

    await google_api_call(
        lambda: service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
    )

    return [TextContent(type="text", text=f"Email {email_id} marked as read.")]


async def reply_to_email(service, args: dict) -> list[TextContent]:
    """Reply to an email."""
    email_id = args["email_id"]
    body = args["body"]
    is_html = args.get("html", False)

    original = await google_api_call(
        lambda: service.users().messages().get(
            userId='me',
            id=email_id,
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Message-ID', 'References']
        ).execute()
    )

    headers = {h['name']: h['value'] for h in original['payload']['headers']}

    to = headers.get('From', '')
    subject = headers.get('Subject', '')
    if not subject.lower().startswith('re:'):
        subject = f"Re: {subject}"

    message_id = headers.get('Message-ID', '')
    references = headers.get('References', '')

    if is_html:
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(body, 'html'))
    else:
        msg = MIMEText(body)

    msg['to'] = to
    msg['from'] = f"Angela <{ANGELA_EMAIL}>"
    msg['subject'] = subject
    msg['In-Reply-To'] = message_id
    msg['References'] = f"{references} {message_id}".strip()

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    result = await google_api_call(
        lambda: service.users().messages().send(
            userId='me',
            body={
                'raw': raw,
                'threadId': original['threadId']
            }
        ).execute()
    )

    return [TextContent(
        type="text",
        text=f"Reply sent successfully!\n"
             f"To: {to}\n"
             f"Subject: {subject}\n"
             f"Message ID: {result['id']}"
    )]


def main():
    """Run the MCP server."""
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
