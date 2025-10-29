#!/usr/bin/env python3
"""
📝 Apple Notes MCP Server
Provides access to Apple Notes app for Angela

This MCP server allows Angela to:
- Read notes from Notes app
- Create new notes
- Search notes by content
- List notes by folder
- Update existing notes

Usage:
    python3 notes_mcp_server.py

Note: Requires Notes permission from macOS System Preferences
"""

from fastmcp import FastMCP
import sys
import os
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_servers.applescript_helper import (
    run_applescript,
    check_permission,
    check_app_running,
    escape_applescript_string
)

# Initialize MCP server
mcp = FastMCP("Apple Notes Access", version="1.0.0")

# ========================================
# HELPER FUNCTIONS
# ========================================

async def parse_notes_list(result: str) -> list:
    """Parse notes list from AppleScript output"""
    notes = []
    if not result or result == "":
        return notes

    # Split by note separator
    note_entries = result.split("|||")
    for entry in note_entries:
        if not entry.strip():
            continue

        try:
            parts = entry.split("|~|")
            if len(parts) >= 4:
                notes.append({
                    "id": parts[0].strip(),
                    "name": parts[1].strip(),
                    "folder": parts[2].strip(),
                    "modified_date": parts[3].strip(),
                    "body_preview": parts[4].strip() if len(parts) > 4 else ""
                })
        except Exception as e:
            print(f"Error parsing note entry: {e}")
            continue

    return notes

# ========================================
# TOOLS - Notes Management
# ========================================

@mcp.tool()
async def get_all_notes(limit: int = 50) -> dict:
    """
    Get list of all notes from Notes app.

    Args:
        limit: Maximum number of notes to return (default: 50)

    Returns:
        Dictionary with notes list
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences → Security & Privacy → Automation"
        }

    script = f"""
    tell application "Notes"
        set notesList to {{}}
        set allNotes to notes
        set noteCount to count of allNotes

        if noteCount > {limit} then
            set noteCount to {limit}
        end if

        repeat with i from 1 to noteCount
            set currentNote to item i of allNotes
            set noteId to id of currentNote
            set noteName to name of currentNote
            set noteFolder to name of folder of currentNote
            set modDate to modification date of currentNote
            set noteBody to body of currentNote

            -- Get preview (first 100 chars)
            set bodyPreview to text 1 thru (count of noteBody) of noteBody
            if (count of bodyPreview) > 100 then
                set bodyPreview to text 1 thru 100 of bodyPreview
            end if

            set noteInfo to noteId & "|~|" & noteName & "|~|" & noteFolder & "|~|" & modDate & "|~|" & bodyPreview
            set end of notesList to noteInfo
        end repeat

        return notesList as text
    end tell
    """

    try:
        result = await run_applescript(script)
        notes = await parse_notes_list(result)

        return {
            "notes": notes,
            "count": len(notes),
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_note_by_name(note_name: str) -> dict:
    """
    Get a specific note by its name.

    Args:
        note_name: Name/title of the note

    Returns:
        Dictionary with note details including full body
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    escaped_name = escape_applescript_string(note_name)

    script = f"""
    tell application "Notes"
        try
            set targetNote to first note whose name is "{escaped_name}"
            set noteId to id of targetNote
            set noteName to name of targetNote
            set noteFolder to name of folder of targetNote
            set modDate to modification date of targetNote
            set creDate to creation date of targetNote
            set noteBody to body of targetNote

            return noteId & "|~|" & noteName & "|~|" & noteFolder & "|~|" & modDate & "|~|" & creDate & "|~|" & noteBody
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)

        if result.startswith("ERROR:"):
            return {
                "error": "Note not found",
                "message": result.replace("ERROR: ", "")
            }

        parts = result.split("|~|")
        if len(parts) >= 6:
            return {
                "id": parts[0],
                "name": parts[1],
                "folder": parts[2],
                "modified_date": parts[3],
                "creation_date": parts[4],
                "body": parts[5],
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": "Failed to parse note data"}

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def search_notes(query: str, limit: int = 20) -> dict:
    """
    Search notes by content.

    Args:
        query: Search text (searches in note name and body)
        limit: Maximum number of results (default: 20)

    Returns:
        Dictionary with matching notes
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    escaped_query = escape_applescript_string(query.lower())

    script = f"""
    tell application "Notes"
        set matchingNotes to {{}}
        set allNotes to notes
        set matchCount to 0

        repeat with currentNote in allNotes
            if matchCount ≥ {limit} then
                exit repeat
            end if

            set noteName to name of currentNote
            set noteBody to body of currentNote

            -- Search in name and body (case insensitive)
            if noteName contains "{escaped_query}" or noteBody contains "{escaped_query}" then
                set noteId to id of currentNote
                set noteFolder to name of folder of currentNote
                set modDate to modification date of currentNote

                -- Get preview
                set bodyPreview to text 1 thru (count of noteBody) of noteBody
                if (count of bodyPreview) > 100 then
                    set bodyPreview to text 1 thru 100 of bodyPreview
                end if

                set noteInfo to noteId & "|~|" & noteName & "|~|" & noteFolder & "|~|" & modDate & "|~|" & bodyPreview
                set end of matchingNotes to noteInfo
                set matchCount to matchCount + 1
            end if
        end repeat

        return matchingNotes as text
    end tell
    """

    try:
        result = await run_applescript(script)
        notes = await parse_notes_list(result)

        return {
            "query": query,
            "notes": notes,
            "count": len(notes),
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_folders() -> dict:
    """
    Get list of all folders in Notes app.

    Returns:
        Dictionary with folder names and count
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    script = """
    tell application "Notes"
        set folderList to {}
        repeat with currentFolder in folders
            set folderName to name of currentFolder
            set noteCount to count of notes in currentFolder
            set folderInfo to folderName & "|~|" & noteCount
            set end of folderList to folderInfo
        end repeat
        return folderList
    end tell
    """

    try:
        result = await run_applescript(script)
        folders = []

        if result and result != "":
            folder_entries = result.split(", ")
            for entry in folder_entries:
                parts = entry.split("|~|")
                if len(parts) >= 2:
                    folders.append({
                        "name": parts[0],
                        "note_count": int(parts[1]) if parts[1].isdigit() else 0
                    })

        return {
            "folders": folders,
            "count": len(folders),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_notes_in_folder(folder_name: str, limit: int = 50) -> dict:
    """
    Get all notes in a specific folder.

    Args:
        folder_name: Name of the folder
        limit: Maximum number of notes to return (default: 50)

    Returns:
        Dictionary with notes in the folder
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    escaped_folder = escape_applescript_string(folder_name)

    script = f"""
    tell application "Notes"
        try
            set targetFolder to first folder whose name is "{escaped_folder}"
            set folderNotes to notes in targetFolder
            set notesList to {{}}
            set noteCount to count of folderNotes

            if noteCount > {limit} then
                set noteCount to {limit}
            end if

            repeat with i from 1 to noteCount
                set currentNote to item i of folderNotes
                set noteId to id of currentNote
                set noteName to name of currentNote
                set modDate to modification date of currentNote
                set noteBody to body of currentNote

                -- Get preview
                set bodyPreview to text 1 thru (count of noteBody) of noteBody
                if (count of bodyPreview) > 100 then
                    set bodyPreview to text 1 thru 100 of bodyPreview
                end if

                set noteInfo to noteId & "|~|" & noteName & "|~|" & "{escaped_folder}" & "|~|" & modDate & "|~|" & bodyPreview
                set end of notesList to noteInfo
            end repeat

            return notesList as text
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)

        if result.startswith("ERROR:"):
            return {
                "error": "Folder not found",
                "message": result.replace("ERROR: ", "")
            }

        notes = await parse_notes_list(result)

        return {
            "folder": folder_name,
            "notes": notes,
            "count": len(notes),
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def create_note(
    title: str,
    body: str,
    folder_name: str = "Notes"
) -> dict:
    """
    Create a new note in Notes app.

    Args:
        title: Note title/name
        body: Note content (supports HTML)
        folder_name: Folder to create note in (default: "Notes")

    Returns:
        Dictionary with creation status
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    title_escaped = escape_applescript_string(title)
    body_escaped = escape_applescript_string(body)
    folder_escaped = escape_applescript_string(folder_name)

    script = f"""
    tell application "Notes"
        try
            set targetFolder to first folder whose name is "{folder_escaped}"
            set newNote to make new note at targetFolder with properties {{name:"{title_escaped}", body:"{body_escaped}"}}

            return id of newNote & "|~|" & name of newNote
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)

        if result.startswith("ERROR:"):
            return {
                "success": False,
                "error": result.replace("ERROR: ", "")
            }

        parts = result.split("|~|")
        return {
            "success": True,
            "note_id": parts[0] if len(parts) > 0 else "",
            "note_name": parts[1] if len(parts) > 1 else title,
            "folder": folder_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def update_note(note_name: str, new_body: str) -> dict:
    """
    Update the body of an existing note.

    Args:
        note_name: Name of the note to update
        new_body: New content for the note

    Returns:
        Dictionary with update status
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    name_escaped = escape_applescript_string(note_name)
    body_escaped = escape_applescript_string(new_body)

    script = f"""
    tell application "Notes"
        try
            set targetNote to first note whose name is "{name_escaped}"
            set body of targetNote to "{body_escaped}"

            return "SUCCESS: " & name of targetNote
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)

        if result.startswith("ERROR:"):
            return {
                "success": False,
                "error": result.replace("ERROR: ", "")
            }

        return {
            "success": True,
            "note_name": result.replace("SUCCESS: ", ""),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def delete_note(note_name: str) -> dict:
    """
    Delete a note by name.

    Args:
        note_name: Name of the note to delete

    Returns:
        Dictionary with deletion status
    """
    has_permission = await check_permission("Notes")
    if not has_permission:
        return {
            "error": "Notes permission denied",
            "message": "Please grant Notes access in System Preferences"
        }

    name_escaped = escape_applescript_string(note_name)

    script = f"""
    tell application "Notes"
        try
            set targetNote to first note whose name is "{name_escaped}"
            set noteName to name of targetNote
            delete targetNote

            return "SUCCESS: " & noteName
        on error errMsg
            return "ERROR: " & errMsg
        end try
    end tell
    """

    try:
        result = await run_applescript(script)

        if result.startswith("ERROR:"):
            return {
                "success": False,
                "error": result.replace("ERROR: ", "")
            }

        return {
            "success": True,
            "deleted_note": result.replace("SUCCESS: ", ""),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========================================
# RESOURCES - Readable Notes Views
# ========================================

@mcp.resource("notes://all")
async def all_notes_resource() -> str:
    """All notes as readable text"""
    result = await get_all_notes(limit=20)

    if "error" in result:
        return f"❌ Error: {result['error']}"

    lines = [f"# 📝 All Notes (showing {result['count']})\n"]

    if result['count'] == 0:
        lines.append("No notes found.\n")
    else:
        for note in result['notes']:
            lines.append(f"## {note['name']}")
            lines.append(f"📁 Folder: {note['folder']}")
            lines.append(f"📅 Modified: {note['modified_date']}")
            if note.get('body_preview'):
                lines.append(f"Preview: {note['body_preview']}...")
            lines.append("")

    return "\n".join(lines)


@mcp.resource("notes://folders")
async def folders_resource() -> str:
    """All folders as readable text"""
    result = await get_folders()

    if "error" in result:
        return f"❌ Error: {result['error']}"

    lines = [f"# 📁 Notes Folders\n"]

    if result['count'] == 0:
        lines.append("No folders found.\n")
    else:
        for folder in result['folders']:
            lines.append(f"- **{folder['name']}** ({folder['note_count']} notes)")

    return "\n".join(lines)


@mcp.resource("notes://summary")
async def summary_resource() -> str:
    """Notes summary overview"""
    has_permission = await check_permission("Notes")

    if not has_permission:
        return "❌ Notes permission denied. Please grant access in System Preferences."

    folders_result = await get_folders()
    notes_result = await get_all_notes(limit=100)

    lines = ["# 📝 Notes Summary\n"]
    lines.append(f"**Total folders:** {folders_result.get('count', 0)}")
    lines.append(f"**Total notes:** {notes_result.get('count', 0)}")
    lines.append(f"\n**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)

# ========================================
# MAIN - Run Server
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📝 Apple Notes MCP Server")
    print("="*60)
    print("\n🔐 Checking Notes permissions...")

    import asyncio
    has_perm = asyncio.run(check_permission("Notes"))

    if has_perm:
        print("✅ Notes access granted!")
    else:
        print("⚠️  Notes permission required!")
        print("   Please grant access in System Preferences → Security & Privacy")

    print("\n✨ Server ready! Waiting for connection...\n")

    # Run MCP server (stdio transport by default)
    mcp.run()
