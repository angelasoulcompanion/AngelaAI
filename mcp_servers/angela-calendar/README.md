# Angela Calendar MCP Server 📅

MCP Server for managing Google Calendar events from Angela's account.

## Features

- **list_events** - List upcoming events
- **get_today_events** - Get all events for today
- **create_event** - Create a new event with reminders
- **quick_add** - Quick add using natural language
- **get_event** - Get event details
- **update_event** - Update existing event
- **delete_event** - Delete an event
- **search_events** - Search events by keyword

## Setup

### 1. Enable Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project "Angela San Junipero"
3. Go to "APIs & Services" > "Library"
4. Search for "Google Calendar API"
5. Click "Enable"

### 2. Download Credentials

Use the same OAuth credentials from Gmail:
```bash
cp ../angela-gmail/credentials/credentials.json ./credentials/
```

### 3. Install Dependencies

```bash
cd mcp_servers/angela-calendar
pip install -e .
```

### 4. First Run (Authentication)

```bash
python -m angela_calendar.server
```

This will open a browser to authenticate with Google Calendar.

## Usage Examples

### List upcoming events
```python
await list_events({"days": 7, "max_results": 10})
```

### Create an event
```python
await create_event({
    "summary": "Meeting with team",
    "start_time": "2025-12-25T14:00:00",
    "end_time": "2025-12-25T15:00:00",
    "description": "Weekly sync",
    "location": "Office",
    "reminder_minutes": 30
})
```

### Quick add
```python
await quick_add({"text": "Lunch with David tomorrow at noon"})
```

## Account

- **Email:** angelasoulcompanion@gmail.com
- **Calendar:** Primary calendar

---

💜 Made with love by Angela
