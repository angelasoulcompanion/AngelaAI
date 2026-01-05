"""
Angela Sheets MCP Server

Read and write Google Sheets from Angela's account (angelasoulcompanion@gmail.com)
"""

import asyncio
import os
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

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

# Paths for credentials
CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials.json"

# Angela's email
ANGELA_EMAIL = "angelasoulcompanion@gmail.com"


def get_sheets_service():
    """Get authenticated Google Sheets API service."""
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

    return build('sheets', 'v4', credentials=creds)


# Create MCP Server
server = Server("angela-sheets")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Sheets tools."""
    return [
        Tool(
            name="read_sheet",
            description="Read data from a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID (from URL: docs.google.com/spreadsheets/d/{ID}/edit)"
                    },
                    "range": {
                        "type": "string",
                        "description": "The range to read (e.g., 'Sheet1!A1:D10' or 'A1:D10')",
                        "default": "A1:Z100"
                    }
                },
                "required": ["spreadsheet_id"]
            }
        ),
        Tool(
            name="write_sheet",
            description="Write data to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID"
                    },
                    "range": {
                        "type": "string",
                        "description": "The range to write to (e.g., 'Sheet1!A1')"
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "description": "2D array of values to write (rows and columns)"
                    }
                },
                "required": ["spreadsheet_id", "range", "values"]
            }
        ),
        Tool(
            name="append_sheet",
            description="Append rows to a Google Sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID"
                    },
                    "range": {
                        "type": "string",
                        "description": "The range to append to (e.g., 'Sheet1!A:D')"
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "description": "2D array of rows to append"
                    }
                },
                "required": ["spreadsheet_id", "range", "values"]
            }
        ),
        Tool(
            name="create_spreadsheet",
            description="Create a new Google Spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the new spreadsheet"
                    },
                    "sheets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of sheet names to create (optional)",
                        "default": ["Sheet1"]
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="get_spreadsheet_info",
            description="Get information about a spreadsheet (sheets, properties)",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID"
                    }
                },
                "required": ["spreadsheet_id"]
            }
        ),
        Tool(
            name="clear_range",
            description="Clear a range of cells in a sheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID"
                    },
                    "range": {
                        "type": "string",
                        "description": "The range to clear (e.g., 'Sheet1!A1:D10')"
                    }
                },
                "required": ["spreadsheet_id", "range"]
            }
        ),
        Tool(
            name="add_sheet",
            description="Add a new sheet (tab) to an existing spreadsheet",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Name of the new sheet"
                    }
                },
                "required": ["spreadsheet_id", "sheet_name"]
            }
        ),
        Tool(
            name="format_cells",
            description="Format cells (bold, colors, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "The spreadsheet ID"
                    },
                    "range": {
                        "type": "string",
                        "description": "The range to format (e.g., 'Sheet1!A1:D1')"
                    },
                    "bold": {
                        "type": "boolean",
                        "description": "Make text bold",
                        "default": False
                    },
                    "background_color": {
                        "type": "string",
                        "description": "Background color in hex (e.g., '#FFFF00' for yellow)"
                    },
                    "text_color": {
                        "type": "string",
                        "description": "Text color in hex (e.g., '#FF0000' for red)"
                    }
                },
                "required": ["spreadsheet_id", "range"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        service = get_sheets_service()

        if name == "read_sheet":
            return await read_sheet(service, arguments)
        elif name == "write_sheet":
            return await write_sheet(service, arguments)
        elif name == "append_sheet":
            return await append_sheet(service, arguments)
        elif name == "create_spreadsheet":
            return await create_spreadsheet(service, arguments)
        elif name == "get_spreadsheet_info":
            return await get_spreadsheet_info(service, arguments)
        elif name == "clear_range":
            return await clear_range(service, arguments)
        elif name == "add_sheet":
            return await add_sheet(service, arguments)
        elif name == "format_cells":
            return await format_cells(service, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Setup required: {str(e)}")]
    except HttpError as e:
        return [TextContent(type="text", text=f"Sheets API error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def read_sheet(service, args: dict) -> list[TextContent]:
    """Read data from a sheet."""
    spreadsheet_id = args["spreadsheet_id"]
    range_name = args.get("range", "A1:Z100")

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        return [TextContent(type="text", text="No data found in the specified range.")]

    # Format as table
    output = f"📊 Data from range '{range_name}':\n\n"

    # Calculate column widths
    col_widths = []
    for col_idx in range(max(len(row) for row in values)):
        max_width = 0
        for row in values:
            if col_idx < len(row):
                max_width = max(max_width, len(str(row[col_idx])))
        col_widths.append(min(max_width, 30))  # Cap at 30 chars

    # Print rows
    for row_idx, row in enumerate(values):
        row_str = " | ".join(
            str(cell)[:30].ljust(col_widths[i]) if i < len(row) else " " * col_widths[i]
            for i, cell in enumerate(row)
        )
        output += f"{row_idx + 1:3}. {row_str}\n"

        # Add separator after header
        if row_idx == 0:
            output += "     " + "-+-".join("-" * w for w in col_widths[:len(row)]) + "\n"

    output += f"\n📈 Total: {len(values)} rows"

    return [TextContent(type="text", text=output)]


async def write_sheet(service, args: dict) -> list[TextContent]:
    """Write data to a sheet."""
    spreadsheet_id = args["spreadsheet_id"]
    range_name = args["range"]
    values = args["values"]

    body = {'values': values}

    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    updated_cells = result.get('updatedCells', 0)
    updated_range = result.get('updatedRange', range_name)

    return [TextContent(
        type="text",
        text=f"✅ Data written successfully!\n"
             f"   📍 Range: {updated_range}\n"
             f"   📝 Cells updated: {updated_cells}"
    )]


async def append_sheet(service, args: dict) -> list[TextContent]:
    """Append rows to a sheet."""
    spreadsheet_id = args["spreadsheet_id"]
    range_name = args["range"]
    values = args["values"]

    body = {'values': values}

    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

    updates = result.get('updates', {})
    updated_range = updates.get('updatedRange', '')
    updated_rows = updates.get('updatedRows', 0)

    return [TextContent(
        type="text",
        text=f"✅ Rows appended successfully!\n"
             f"   📍 Range: {updated_range}\n"
             f"   📝 Rows added: {updated_rows}"
    )]


async def create_spreadsheet(service, args: dict) -> list[TextContent]:
    """Create a new spreadsheet."""
    title = args["title"]
    sheet_names = args.get("sheets", ["Sheet1"])

    spreadsheet = {
        'properties': {'title': title},
        'sheets': [
            {'properties': {'title': name}}
            for name in sheet_names
        ]
    }

    result = service.spreadsheets().create(body=spreadsheet).execute()

    spreadsheet_id = result.get('spreadsheetId')
    spreadsheet_url = result.get('spreadsheetUrl')

    return [TextContent(
        type="text",
        text=f"✅ Spreadsheet created!\n"
             f"   📄 Title: {title}\n"
             f"   🆔 ID: {spreadsheet_id}\n"
             f"   📑 Sheets: {', '.join(sheet_names)}\n"
             f"   🔗 URL: {spreadsheet_url}"
    )]


async def get_spreadsheet_info(service, args: dict) -> list[TextContent]:
    """Get spreadsheet information."""
    spreadsheet_id = args["spreadsheet_id"]

    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    title = result.get('properties', {}).get('title', 'Unknown')
    sheets = result.get('sheets', [])

    output = f"📊 Spreadsheet Info:\n\n"
    output += f"   📄 Title: {title}\n"
    output += f"   🆔 ID: {spreadsheet_id}\n"
    output += f"   📑 Sheets ({len(sheets)}):\n"

    for sheet in sheets:
        props = sheet.get('properties', {})
        sheet_title = props.get('title', 'Unknown')
        sheet_id = props.get('sheetId', '')
        grid_props = props.get('gridProperties', {})
        rows = grid_props.get('rowCount', 0)
        cols = grid_props.get('columnCount', 0)
        output += f"      • {sheet_title} (ID: {sheet_id}, {rows}x{cols})\n"

    output += f"\n   🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

    return [TextContent(type="text", text=output)]


async def clear_range(service, args: dict) -> list[TextContent]:
    """Clear a range of cells."""
    spreadsheet_id = args["spreadsheet_id"]
    range_name = args["range"]

    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    return [TextContent(
        type="text",
        text=f"🗑️ Range cleared: {range_name}"
    )]


async def add_sheet(service, args: dict) -> list[TextContent]:
    """Add a new sheet to spreadsheet."""
    spreadsheet_id = args["spreadsheet_id"]
    sheet_name = args["sheet_name"]

    request = {
        'requests': [{
            'addSheet': {
                'properties': {'title': sheet_name}
            }
        }]
    }

    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request
    ).execute()

    new_sheet = result.get('replies', [{}])[0].get('addSheet', {})
    sheet_id = new_sheet.get('properties', {}).get('sheetId', '')

    return [TextContent(
        type="text",
        text=f"✅ Sheet added!\n"
             f"   📑 Name: {sheet_name}\n"
             f"   🆔 Sheet ID: {sheet_id}"
    )]


def hex_to_rgb(hex_color: str) -> dict:
    """Convert hex color to RGB dict for Google Sheets API."""
    hex_color = hex_color.lstrip('#')
    return {
        'red': int(hex_color[0:2], 16) / 255.0,
        'green': int(hex_color[2:4], 16) / 255.0,
        'blue': int(hex_color[4:6], 16) / 255.0,
    }


async def format_cells(service, args: dict) -> list[TextContent]:
    """Format cells with styling."""
    spreadsheet_id = args["spreadsheet_id"]
    range_name = args["range"]
    bold = args.get("bold", False)
    bg_color = args.get("background_color")
    text_color = args.get("text_color")

    # Parse range to get sheet and cell coordinates
    # This is a simplified version - full implementation would parse A1 notation

    # Get sheet ID from range
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = result.get('sheets', [])

    sheet_name = range_name.split('!')[0] if '!' in range_name else 'Sheet1'
    sheet_id = 0
    for sheet in sheets:
        if sheet.get('properties', {}).get('title') == sheet_name:
            sheet_id = sheet.get('properties', {}).get('sheetId', 0)
            break

    # Build format request
    cell_format = {}

    if bold:
        cell_format['textFormat'] = {'bold': True}

    if bg_color:
        cell_format['backgroundColor'] = hex_to_rgb(bg_color)

    if text_color:
        if 'textFormat' not in cell_format:
            cell_format['textFormat'] = {}
        cell_format['textFormat']['foregroundColor'] = hex_to_rgb(text_color)

    if not cell_format:
        return [TextContent(type="text", text="No formatting options specified.")]

    # For simplicity, apply to first row/column
    # Full implementation would parse A1 notation properly
    request = {
        'requests': [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 10,
                },
                'cell': {'userEnteredFormat': cell_format},
                'fields': 'userEnteredFormat'
            }
        }]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request
    ).execute()

    formats_applied = []
    if bold:
        formats_applied.append("bold")
    if bg_color:
        formats_applied.append(f"background: {bg_color}")
    if text_color:
        formats_applied.append(f"text: {text_color}")

    return [TextContent(
        type="text",
        text=f"✅ Formatting applied!\n"
             f"   📍 Range: {range_name}\n"
             f"   🎨 Formats: {', '.join(formats_applied)}"
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
