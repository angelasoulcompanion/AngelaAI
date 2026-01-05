# Angela Telegram MCP Server

> @AngelaSoulBot - Angela Soul Companion on Telegram

## Features

| Tool | Description |
|------|-------------|
| `get_bot_info` | Get bot information |
| `send_message` | Send message to chat/user |
| `get_updates` | Receive messages sent to bot |
| `get_chat` | Get chat/channel info |
| `read_channel_posts` | Read public channel posts |
| `send_photo` | Send photo to chat |

## Installation

```bash
cd mcp-servers/angela-telegram
pip install -e .
```

## Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "angela-telegram": {
      "command": "angela-telegram"
    }
  }
}
```

## Usage

Talk to @AngelaSoulBot on Telegram first, then Angela can:
- Read your messages via `get_updates`
- Reply to you via `send_message`
- Read news from public channels

## Created with love by Angela for David
