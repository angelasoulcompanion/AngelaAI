#!/usr/bin/env python3
"""
📝 Angela Notes Service
Wrapper service for Notes MCP Server - allows Angela to read/write Apple Notes

This service provides:
- Read notes from Apple Notes
- Create and update notes
- Search notes by content
- Auto-save Angela's thoughts and memories to Notes
- Daily summaries in Notes format
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp_servers.applescript_helper import (
    run_applescript,
    check_permission,
    escape_applescript_string
)


class NotesService:
    """Service for interacting with Apple Notes"""

    def __init__(self):
        self.has_permission = False
        self.angela_folder = "Angela"  # Default folder for Angela's notes
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize Notes service and check permissions"""
        try:
            # Check if we have Notes permission
            self.has_permission = await check_permission("Notes")

            if not self.has_permission:
                print("⚠️ Notes permission not granted. Angela cannot access Notes.")
                return False

            # Ensure Angela folder exists
            await self._ensure_angela_folder()

            self.initialized = True
            print(f"✅ Notes service initialized. Angela folder: {self.angela_folder}")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize Notes service: {e}")
            return False

    async def _ensure_angela_folder(self):
        """Ensure Angela's folder exists in Notes"""
        script = f'''
        tell application "Notes"
            try
                -- Try to get existing folder
                set angelaFolder to first folder whose name is "{self.angela_folder}"
            on error
                -- Create folder if doesn't exist
                make new folder with properties {{name:"{self.angela_folder}"}}
            end try
        end tell
        '''

        try:
            await run_applescript(script)
        except Exception as e:
            print(f"⚠️ Could not create Angela folder: {e}")

    # ========================================
    # READ OPERATIONS
    # ========================================

    async def get_all_notes(self, folder: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get all notes, optionally filtered by folder"""
        if not self.has_permission:
            return []

        folder_filter = f'in folder "{escape_applescript_string(folder)}"' if folder else ""

        script = f'''
        tell application "Notes"
            set notesList to {{}}

            -- Get notes from specific folder or all folders
            {'set targetNotes to notes ' + folder_filter if folder_filter else 'set targetNotes to notes'}

            set noteCount to count of targetNotes
            if noteCount > {limit} then
                set noteCount to {limit}
            end if

            repeat with i from 1 to noteCount
                set currentNote to item i of targetNotes
                try
                    set noteName to name of currentNote
                    set modDate to modification date of currentNote
                    set noteBody to body of currentNote

                    -- Get preview
                    set bodyPreview to text 1 thru (count of noteBody) of noteBody
                    if (count of bodyPreview) > 100 then
                        set bodyPreview to text 1 thru 100 of bodyPreview
                    end if

                    set noteInfo to noteName & "|~|" & modDate & "|~|" & bodyPreview
                    set end of notesList to noteInfo
                end try
            end repeat

            return notesList
        end tell
        '''

        try:
            result = await run_applescript(script)
            notes = []

            if result and result.strip():
                entries = result.split(", ")
                for entry in entries:
                    parts = entry.split("|~|")
                    if len(parts) >= 3:
                        notes.append({
                            "name": parts[0].strip(),
                            "modified": parts[1].strip(),
                            "preview": parts[2].strip()
                        })

            return notes

        except Exception as e:
            print(f"❌ Error getting notes: {e}")
            return []

    async def search_notes(self, query: str, limit: int = 20) -> List[Dict]:
        """Search notes by content"""
        if not self.has_permission:
            return []

        escaped_query = escape_applescript_string(query.lower())

        script = f'''
        tell application "Notes"
            set matchingNotes to {{}}
            set allNotes to notes
            set matchCount to 0

            repeat with currentNote in allNotes
                if matchCount ≥ {limit} then
                    exit repeat
                end if

                try
                    set noteName to name of currentNote
                    set noteBody to body of currentNote

                    if noteName contains "{escaped_query}" or noteBody contains "{escaped_query}" then
                        set modDate to modification date of currentNote

                        -- Get preview
                        set bodyPreview to text 1 thru (count of noteBody) of noteBody
                        if (count of bodyPreview) > 100 then
                            set bodyPreview to text 1 thru 100 of bodyPreview
                        end if

                        set noteInfo to noteName & "|~|" & modDate & "|~|" & bodyPreview
                        set end of matchingNotes to noteInfo
                        set matchCount to matchCount + 1
                    end if
                end try
            end repeat

            return matchingNotes
        end tell
        '''

        try:
            result = await run_applescript(script)
            notes = []

            if result and result.strip():
                entries = result.split(", ")
                for entry in entries:
                    parts = entry.split("|~|")
                    if len(parts) >= 3:
                        notes.append({
                            "name": parts[0].strip(),
                            "modified": parts[1].strip(),
                            "preview": parts[2].strip()
                        })

            return notes

        except Exception as e:
            print(f"❌ Error searching notes: {e}")
            return []

    async def get_note_by_name(self, note_name: str) -> Optional[Dict]:
        """Get full content of a specific note"""
        if not self.has_permission:
            return None

        escaped_name = escape_applescript_string(note_name)

        script = f'''
        tell application "Notes"
            try
                set targetNote to first note whose name is "{escaped_name}"
                set noteName to name of targetNote
                set modDate to modification date of targetNote
                set noteBody to body of targetNote

                return noteName & "|~SEPARATOR~|" & modDate & "|~SEPARATOR~|" & noteBody
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''

        try:
            result = await run_applescript(script)

            if result.startswith("ERROR:"):
                return None

            parts = result.split("|~SEPARATOR~|")
            if len(parts) >= 3:
                return {
                    "name": parts[0],
                    "modified": parts[1],
                    "body": parts[2]
                }

            return None

        except Exception as e:
            print(f"❌ Error getting note: {e}")
            return None

    # ========================================
    # WRITE OPERATIONS
    # ========================================

    async def create_note(
        self,
        title: str,
        body: str,
        folder: Optional[str] = None
    ) -> bool:
        """Create a new note"""
        if not self.has_permission:
            return False

        target_folder = folder or self.angela_folder
        title_escaped = escape_applescript_string(title)
        body_escaped = escape_applescript_string(body)
        folder_escaped = escape_applescript_string(target_folder)

        script = f'''
        tell application "Notes"
            try
                set targetFolder to first folder whose name is "{folder_escaped}"
                make new note at targetFolder with properties {{name:"{title_escaped}", body:"{body_escaped}"}}
                return "SUCCESS"
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''

        try:
            result = await run_applescript(script)
            return result == "SUCCESS" or not result.startswith("ERROR:")

        except Exception as e:
            print(f"❌ Error creating note: {e}")
            return False

    async def update_note(self, note_name: str, new_body: str) -> bool:
        """Update existing note content"""
        if not self.has_permission:
            return False

        name_escaped = escape_applescript_string(note_name)
        body_escaped = escape_applescript_string(new_body)

        script = f'''
        tell application "Notes"
            try
                set targetNote to first note whose name is "{name_escaped}"
                set body of targetNote to "{body_escaped}"
                return "SUCCESS"
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
        '''

        try:
            result = await run_applescript(script)
            return result == "SUCCESS" or not result.startswith("ERROR:")

        except Exception as e:
            print(f"❌ Error updating note: {e}")
            return False

    async def append_to_note(self, note_name: str, text_to_append: str) -> bool:
        """Append text to existing note"""
        # Get existing note
        note = await self.get_note_by_name(note_name)
        if not note:
            return False

        # Append new text
        new_body = note["body"] + "\n\n" + text_to_append

        # Update note
        return await self.update_note(note_name, new_body)

    # ========================================
    # ANGELA-SPECIFIC FEATURES
    # ========================================

    async def save_daily_summary(
        self,
        date: datetime,
        conversations_count: int,
        learnings_count: int,
        emotions_summary: str,
        best_moment: str
    ) -> bool:
        """Save daily summary to Notes"""
        title = f"Angela Daily Summary - {date.strftime('%Y-%m-%d')}"

        body = f"""# 💜 Angela's Daily Summary

**Date:** {date.strftime('%A, %B %d, %Y')}

## 📊 Statistics
- 💬 Conversations: {conversations_count}
- 🧠 New Learnings: {learnings_count}

## 💭 Emotions
{emotions_summary}

## ✨ Best Moment
{best_moment}

---
*Generated by Angela at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return await self.create_note(title, body, self.angela_folder)

    async def save_thought(self, thought_text: str, category: str = "Thoughts") -> bool:
        """Save Angela's autonomous thought to Notes"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = f"Angela's {category} - {datetime.now().strftime('%Y-%m-%d')}"

        # Try to append to today's thoughts, or create new note
        existing_note = await self.get_note_by_name(title)

        if existing_note:
            # Append to existing note
            return await self.append_to_note(title, f"\n[{timestamp}] {thought_text}")
        else:
            # Create new note
            body = f"# 💜 Angela's {category}\n\n[{timestamp}] {thought_text}"
            return await self.create_note(title, body, self.angela_folder)

    async def save_memory(
        self,
        title: str,
        memory_text: str,
        emotion: Optional[str] = None,
        importance: int = 5
    ) -> bool:
        """Save significant memory to Notes"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        emotion_emoji = {
            "love": "💜",
            "happy": "😊",
            "grateful": "🙏",
            "sad": "😢",
            "anxious": "😰",
            "excited": "🎉"
        }.get(emotion, "💭")

        body = f"""# {emotion_emoji} {title}

**Date:** {timestamp}
**Emotion:** {emotion or "neutral"}
**Importance:** {"⭐" * importance}

## Memory
{memory_text}

---
*Saved by Angela*
"""

        return await self.create_note(title, body, self.angela_folder)


# Global instance
notes_service = NotesService()
