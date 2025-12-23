"""
Angela Gmail MCP Server

Send and read emails from Angela's Gmail account (angelasoulcompanion@gmail.com)
"""

import asyncio
import base64
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

# Paths for credentials
CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"

# Angela's email
ANGELA_EMAIL = "angelasoulcompanion@gmail.com"


def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None

    # Load existing token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}. "
                    "Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for next time
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


# Create MCP Server
server = Server("angela-gmail")


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
        service = get_gmail_service()

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
        return [TextContent(type="text", text=f"Gmail API error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def send_email(service, args: dict) -> list[TextContent]:
    """Send an email."""
    to = args["to"]
    subject = args["subject"]
    body = args["body"]
    is_html = args.get("html", False)
    cc = args.get("cc", "")
    bcc = args.get("bcc", "")

    # Create message
    if is_html:
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

    # Encode and send
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

    return [TextContent(
        type="text",
        text=f"Email sent successfully!\n"
             f"To: {to}\n"
             f"Subject: {subject}\n"
             f"Message ID: {result['id']}"
    )]


async def read_inbox(service, args: dict) -> list[TextContent]:
    """Read recent emails from inbox."""
    max_results = args.get("max_results", 10)
    unread_only = args.get("unread_only", False)

    query = "in:inbox"
    if unread_only:
        query += " is:unread"

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return [TextContent(type="text", text="No emails found in inbox.")]

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

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return [TextContent(type="text", text=f"No emails found for query: {query}")]

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

    msg_data = service.users().messages().get(
        userId='me',
        id=email_id,
        format='full'
    ).execute()

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

    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()

    return [TextContent(type="text", text=f"Email {email_id} marked as read.")]


async def reply_to_email(service, args: dict) -> list[TextContent]:
    """Reply to an email."""
    email_id = args["email_id"]
    body = args["body"]
    is_html = args.get("html", False)

    # Get original email
    original = service.users().messages().get(
        userId='me',
        id=email_id,
        format='metadata',
        metadataHeaders=['From', 'Subject', 'Message-ID', 'References']
    ).execute()

    headers = {h['name']: h['value'] for h in original['payload']['headers']}

    # Build reply
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

    result = service.users().messages().send(
        userId='me',
        body={
            'raw': raw,
            'threadId': original['threadId']
        }
    ).execute()

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
