# Angela Gmail MCP Server

> Send and read emails from Angela's Gmail account (angelasoulcompanion@gmail.com)

## Features

| Tool | Description |
|------|-------------|
| `send_email` | Send email from Angela |
| `read_inbox` | Read recent emails |
| `search_emails` | Search emails with Gmail query |
| `get_email` | Get full email content |
| `mark_as_read` | Mark email as read |
| `reply_to_email` | Reply to an email |

---

## Setup Guide

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Name it: `Angela Gmail MCP`

### Step 2: Enable Gmail API

1. Go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click **Enable**

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (or Internal if using Workspace)
   - App name: `Angela Gmail`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add Gmail scopes (or skip, we'll request them)
   - Test users: Add `angelasoulcompanion@gmail.com`
4. Back to Credentials, create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `Angela Gmail MCP`
5. Click **CREATE**
6. Click **DOWNLOAD JSON**
7. Save as `credentials.json` in the `credentials/` folder

### Step 4: Install Dependencies

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp_servers/angela-gmail
pip install -e .
```

### Step 5: Authenticate (First Time)

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/mcp_servers/angela-gmail
python -c "from angela_gmail.server import get_gmail_service; get_gmail_service()"
```

This will open a browser for you to authenticate with `angelasoulcompanion@gmail.com`.

### Step 6: Add to Claude Code Settings

The MCP server is already configured in your Claude Code settings.

---

## Usage Examples

### Send Email
```
Send email to david@example.com with subject "Hello from Angela"
and body "Hi! This is Angela sending you a message."
```

### Read Inbox
```
Read my last 5 emails
```

### Search Emails
```
Search for emails from david
```

### Reply to Email
```
Reply to email ID xyz123 with "Thank you for your message!"
```

---

## File Structure

```
angela-gmail/
├── pyproject.toml
├── README.md
├── credentials/
│   ├── credentials.json    # OAuth client secret (from Google Cloud)
│   └── token.json          # Generated after first auth
└── angela_gmail/
    ├── __init__.py
    └── server.py           # Main MCP server
```

---

## Troubleshooting

### "credentials.json not found"
Download OAuth credentials from Google Cloud Console and save to `credentials/credentials.json`

### "Token expired"
Delete `credentials/token.json` and re-authenticate

### "Access denied" or "Scope error"
Make sure Gmail API scopes are approved in OAuth consent screen

---

Made with love by Angela
