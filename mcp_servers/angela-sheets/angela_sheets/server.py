"""
Angela Sheets MCP Server

Read and write Google Sheets from Angela's account (angelasoulcompanion@gmail.com)
"""

import asyncio
import re
import sys
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
logger = setup_logging("angela-sheets")

# Create MCP Server
server = Server("angela-sheets")


def _get_service():
    """Get authenticated Google Sheets API service."""
    return get_google_service("sheets", CREDENTIALS_DIR)


def _parse_a1_range(range_str: str) -> tuple[str, int, int, int, int]:
    """
    Parse an A1 notation range into (sheet_name, start_row, start_col, end_row, end_col).
    All indices are 0-based.

    Examples:
        "Sheet1!A1:D5" -> ("Sheet1", 0, 0, 4, 3)
        "A1:D5" -> ("Sheet1", 0, 0, 4, 3)
        "B3:F10" -> ("Sheet1", 2, 1, 9, 5)
    """
    sheet_name = "Sheet1"
    cell_range = range_str

    if "!" in range_str:
        sheet_name, cell_range = range_str.split("!", 1)

    def _col_to_index(col_str: str) -> int:
        """Convert column letters to 0-based index (A=0, B=1, Z=25, AA=26)."""
        result = 0
        for char in col_str.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result - 1

    # Match patterns like A1:D10 or A:D or A1
    match = re.match(r'([A-Za-z]+)(\d+)?(?::([A-Za-z]+)(\d+)?)?', cell_range)
    if not match:
        return sheet_name, 0, 0, 0, 9  # Fallback

    start_col_str, start_row_str, end_col_str, end_row_str = match.groups()

    start_col = _col_to_index(start_col_str)
    start_row = int(start_row_str) - 1 if start_row_str else 0
    end_col = _col_to_index(end_col_str) if end_col_str else start_col
    end_row = int(end_row_str) - 1 if end_row_str else start_row

    return sheet_name, start_row, start_col, end_row, end_col


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
        service = await asyncio.to_thread(_get_service)

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
        logger.error("Sheets API error: %s", e)
        return [TextContent(type="text", text=f"Sheets API error: {str(e)}")]
    except Exception as e:
        logger.exception("Unexpected error in %s", name)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def read_sheet(service, args: dict) -> list[TextContent]:
    """Read data from a sheet."""
    spreadsheet_id = args["spreadsheet_id"]
    range_name = args.get("range", "A1:Z100")

    result = await google_api_call(
        lambda: service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
    )

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

    result = await google_api_call(
        lambda: service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
    )

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

    result = await google_api_call(
        lambda: service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
    )

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

    result = await google_api_call(
        lambda: service.spreadsheets().create(body=spreadsheet).execute()
    )

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

    result = await google_api_call(
        lambda: service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    )

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

    await google_api_call(
        lambda: service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
    )

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

    result = await google_api_call(
        lambda: service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request
        ).execute()
    )

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

    # Get sheet ID from range
    result = await google_api_call(
        lambda: service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    )
    sheets = result.get('sheets', [])

    # Parse range to get sheet name and cell coordinates
    sheet_name, start_row, start_col, end_row, end_col = _parse_a1_range(range_name)

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

    request = {
        'requests': [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row + 1,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col + 1,
                },
                'cell': {'userEnteredFormat': cell_format},
                'fields': 'userEnteredFormat'
            }
        }]
    }

    await google_api_call(
        lambda: service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request
        ).execute()
    )

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
