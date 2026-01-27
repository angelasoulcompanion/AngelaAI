"""
Meeting Notes Service - Parse & Sync from Things3 to Neon Cloud

Parses structured meeting notes from Things3 todos and syncs
them to the meeting_notes table in Neon Cloud database.

Template sections detected:
- 📍 สถานที่  → location
- 📅 วันที่   → meeting_date
- 🕘/🕐 เวลา → time_range
- 👥 ผู้เข้าประชุม → attendees[]
- 📋 วาระ        → agenda[]
- 📌 สรุปประเด็น  → key_points[]
- ✅ Action Items  → action_items[]
- 📊 Decisions     → decisions_made[]
- ⚠️ Issues        → issues_risks[]
- 📅 Next Steps    → next_steps[]
- 💡 ข้อคิดเห็น   → personal_notes
- 🔹 ช่วงเช้า     → morning_notes (site visit)
- 🔹 ช่วงบ่าย     → afternoon_notes (site visit)
- 👀 สิ่งที่สังเกต → site_observations (site visit)

Created: 2026-01-27
"""

import asyncio
import logging
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class MeetingNotesParser:
    """Parses structured meeting notes text into a dict."""

    # Section markers and their corresponding field names
    SECTION_MARKERS = [
        (r'📍\s*สถานที่\s*[:：]?\s*', 'location'),
        (r'📅\s*วันที่\s*[:：]?\s*', 'meeting_date_raw'),
        (r'[🕘🕐🕗🕑🕒🕓🕔🕕🕖🕙🕚🕛]\s*เวลา\s*[:：]?\s*', 'time_range'),
        (r'👥\s*ผู้เข้าประชุม\s*[:：]?\s*', 'attendees'),
        (r'📋\s*วาระ\s*[:：]?\s*', 'agenda'),
        (r'📌\s*สรุปประเด็น\s*[:：]?\s*', 'key_points'),
        (r'✅\s*Action\s*Items?\s*[:：]?\s*', 'action_items'),
        (r'📊\s*Decisions?\s*[:：]?\s*', 'decisions_made'),
        (r'⚠️\s*Issues?\s*[:：]?\s*', 'issues_risks'),
        (r'📅\s*Next\s*Steps?\s*[:：]?\s*', 'next_steps'),
        (r'💡\s*ข้อคิดเห็น\s*[:：]?\s*', 'personal_notes'),
        # Site visit markers
        (r'🔹\s*ช่วงเช้า\s*[:：]?\s*', 'morning_notes'),
        (r'🔹\s*ช่วงบ่าย\s*[:：]?\s*', 'afternoon_notes'),
        (r'👀\s*สิ่งที่สังเกต\s*[:：]?\s*', 'site_observations'),
    ]

    # Thai month mapping for date parsing
    THAI_MONTHS = {
        'มกราคม': 1, 'ม.ค.': 1, 'ม.ค': 1,
        'กุมภาพันธ์': 2, 'ก.พ.': 2, 'ก.พ': 2,
        'มีนาคม': 3, 'มี.ค.': 3, 'มี.ค': 3,
        'เมษายน': 4, 'เม.ย.': 4, 'เม.ย': 4,
        'พฤษภาคม': 5, 'พ.ค.': 5, 'พ.ค': 5,
        'มิถุนายน': 6, 'มิ.ย.': 6, 'มิ.ย': 6,
        'กรกฎาคม': 7, 'ก.ค.': 7, 'ก.ค': 7,
        'สิงหาคม': 8, 'ส.ค.': 8, 'ส.ค': 8,
        'กันยายน': 9, 'ก.ย.': 9, 'ก.ย': 9,
        'ตุลาคม': 10, 'ต.ค.': 10, 'ต.ค': 10,
        'พฤศจิกายน': 11, 'พ.ย.': 11, 'พ.ย': 11,
        'ธันวาคม': 12, 'ธ.ค.': 12, 'ธ.ค': 12,
    }

    def parse(self, notes: str, title: str = "") -> Dict[str, Any]:
        """Parse structured meeting notes text into a dict."""
        result: Dict[str, Any] = {
            'location': None,
            'meeting_date': None,
            'time_range': None,
            'attendees': [],
            'agenda': [],
            'key_points': [],
            'action_items': [],
            'decisions_made': [],
            'issues_risks': [],
            'next_steps': [],
            'personal_notes': None,
            'morning_notes': None,
            'afternoon_notes': None,
            'site_observations': None,
            'meeting_type': self._detect_meeting_type(notes, title),
        }

        # Find all section positions
        sections = self._find_sections(notes)

        for field_name, start, end in sections:
            section_text = notes[start:end].strip()

            if field_name in ('location', 'time_range', 'personal_notes',
                              'morning_notes', 'afternoon_notes', 'site_observations'):
                # Single-value fields: take first non-empty line
                result[field_name] = self._extract_single_value(section_text)
            elif field_name == 'meeting_date_raw':
                result['meeting_date'] = self._parse_date(section_text)
            elif field_name == 'action_items':
                result['action_items'] = self._parse_action_items(section_text)
            else:
                # List fields: extract bullet points
                result[field_name] = self._extract_list_items(section_text)

        return result

    def _detect_meeting_type(self, notes: str, title: str) -> str:
        """Detect if this is a meeting or site visit."""
        combined = (notes + " " + title).lower()
        if 'site visit' in combined or 'ตรวจสอบ' in combined or 'ดูงาน' in combined:
            return 'site_visit'
        return 'meeting'

    def _find_sections(self, notes: str) -> List[Tuple[str, int, int]]:
        """Find all sections and their text boundaries."""
        # Build a list of (field_name, content_start, marker_start) tuples
        found = []
        for pattern, field_name in self.SECTION_MARKERS:
            match = re.search(pattern, notes)
            if match:
                found.append((field_name, match.end(), match.start()))

        # Sort by marker position in the text
        found.sort(key=lambda x: x[2])

        # Set end positions: each section's content ends where the next section's marker begins
        sections = []
        for i, (field_name, content_start, _marker_start) in enumerate(found):
            if i + 1 < len(found):
                end = found[i + 1][2]  # next section's marker_start
            else:
                end = len(notes)
            sections.append((field_name, content_start, end))

        return sections

    def _extract_single_value(self, text: str) -> Optional[str]:
        """Extract a single value from section text."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # Remove bullet markers
            value = re.sub(r'^[-•·]\s*', '', lines[0]).strip()
            return value if value else None
        return None

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract bullet-point list items from section text."""
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Match lines starting with -, •, ·, numbers, or other bullets
            cleaned = re.sub(r'^[-•·\d.)\]]+\s*', '', line).strip()
            if cleaned:
                items.append(cleaned)
        return items

    def _is_junk_action_item(self, text: str) -> bool:
        """Check if text is a junk/template artifact, not a real action item."""
        t = text.strip()
        if not t:
            return True
        # Too short to be meaningful (e.g. "[ ]", "-", "1.")
        if len(t) <= 3:
            return True
        # Empty checkbox placeholder only
        if re.fullmatch(r'[\[\]xX \-•·]+', t):
            return True
        # Divider lines (━━━, ---, ═══, etc.)
        if re.fullmatch(r'[━─═\-—_]{3,}', t):
            return True
        # Section header: starts with emoji or ends with ":"  with no real content
        if t.endswith(':') and len(t) < 30:
            return True
        # Template marker patterns
        if re.match(r'^[/／]\s*\S+:', t):
            return True
        return False

    def _parse_action_items(self, text: str) -> List[Dict[str, Any]]:
        """Parse action items with checkbox status."""
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Match checkbox patterns: - [ ] or - [x] or - [X]
            checkbox_match = re.match(r'^[-•]\s*\[([ xX])\]\s*(.+)', line)
            if checkbox_match:
                is_completed = checkbox_match.group(1).lower() == 'x'
                action_text = checkbox_match.group(2).strip()
                if not self._is_junk_action_item(action_text):
                    items.append({
                        'action_text': action_text,
                        'is_completed': is_completed,
                    })
            else:
                # Plain bullet item
                cleaned = re.sub(r'^[-•·\d.)\]]+\s*', '', line).strip()
                if cleaned and not self._is_junk_action_item(cleaned):
                    items.append({
                        'action_text': cleaned,
                        'is_completed': False,
                    })
        return items

    def _parse_date(self, text: str) -> Optional[date]:
        """Parse date from Thai or ISO format."""
        text = text.strip()
        first_line = text.split('\n')[0].strip() if text else ''

        # Try ISO format first: YYYY-MM-DD
        iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', first_line)
        if iso_match:
            try:
                return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            except ValueError:
                pass

        # Try DD/MM/YYYY
        slash_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', first_line)
        if slash_match:
            try:
                day = int(slash_match.group(1))
                month = int(slash_match.group(2))
                year = int(slash_match.group(3))
                # Handle BE year (2568 → 2025)
                if year > 2500:
                    year -= 543
                return date(year, month, day)
            except ValueError:
                pass

        # Try Thai format: "27 มกราคม 2569" or "27 ม.ค. 2569"
        for thai_month, month_num in self.THAI_MONTHS.items():
            if thai_month in first_line:
                parts = re.findall(r'\d+', first_line)
                if len(parts) >= 2:
                    try:
                        day = int(parts[0])
                        year = int(parts[-1])
                        if year > 2500:
                            year -= 543
                        return date(year, month_num, day)
                    except ValueError:
                        pass

        return None

    def is_empty_template(self, notes: str) -> bool:
        """Check if notes contain only the template with no content filled in."""
        # Remove all template markers and whitespace
        cleaned = notes
        for pattern, _ in self.SECTION_MARKERS:
            cleaned = re.sub(pattern, '', cleaned)

        # Remove common template placeholders
        cleaned = re.sub(r'[-•·\[\]xX\s\n\r]+', '', cleaned)
        cleaned = re.sub(r'📝.*', '', cleaned)

        # If very little content remains, it's likely an empty template
        return len(cleaned.strip()) < 20


class MeetingNotesSyncService:
    """Syncs meeting notes from Things3 SQLite to Neon Cloud."""

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db or AngelaDatabase()
        self._owns_db = db is None
        self.parser = MeetingNotesParser()
        logger.info("MeetingNotesSyncService initialized")

    async def connect(self) -> None:
        if self._owns_db:
            await self.db.connect()

    async def disconnect(self) -> None:
        if self._owns_db:
            await self.db.disconnect()

    async def sync(self) -> Dict[str, int]:
        """Run full sync from Things3 to Neon Cloud.
        Returns counts: found, synced, updated.
        """
        try:
            await self.connect()

            # Import Things3 handler
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'mcp_servers' / 'angela-things3'))
            from sqlite_handler import SQLiteHandler

            handler = SQLiteHandler()
            if not handler.validate_access():
                logger.error("Cannot access Things3 database")
                return {'found': 0, 'synced': 0, 'updated': 0}

            meetings = handler.get_meeting_todos()
            logger.info(f"Found {len(meetings)} meeting todos in Things3")

            synced = 0
            updated = 0

            for meeting in meetings:
                notes = meeting.get('notes', '')

                # Skip empty templates
                if self.parser.is_empty_template(notes):
                    logger.debug(f"Skipping empty template: {meeting['title']}")
                    continue

                parsed = self.parser.parse(notes, meeting['title'])

                # Fallback: meeting_date from Things3 start_date or deadline
                if not parsed.get('meeting_date'):
                    fallback_date = meeting.get('start_date') or meeting.get('deadline')
                    if fallback_date and isinstance(fallback_date, datetime):
                        parsed['meeting_date'] = fallback_date.date()
                    elif fallback_date and isinstance(fallback_date, date):
                        parsed['meeting_date'] = fallback_date

                # Combine project + heading for richer context
                project = meeting.get('project_title', '')
                heading = meeting.get('heading_title', '')
                if heading and project:
                    meeting['project_title'] = f"{project} / {heading}"

                # Check if meeting already exists
                existing = await self.db.fetchrow(
                    "SELECT meeting_id FROM meeting_notes WHERE things3_uuid = $1",
                    meeting['uuid']
                )

                if existing:
                    await self._update_meeting(existing['meeting_id'], meeting, parsed)
                    updated += 1
                else:
                    await self._insert_meeting(meeting, parsed)
                    synced += 1

            # Log sync result
            today = date.today()
            await self.db.execute('''
                INSERT INTO meeting_sync_log (sync_date, meetings_found, meetings_synced, meetings_updated)
                VALUES ($1, $2, $3, $4)
            ''', today, len(meetings), synced, updated)

            result = {'found': len(meetings), 'synced': synced, 'updated': updated}
            logger.info(f"Sync complete: {result}")
            return result

        except Exception as e:
            logger.error(f"Sync error: {e}")
            return {'found': 0, 'synced': 0, 'updated': 0}
        finally:
            await self.disconnect()

    async def _insert_meeting(self, meeting: Dict, parsed: Dict) -> None:
        """Insert a new meeting record."""
        now = datetime.now(timezone.utc)
        # Use Things3 creation_date for created_at if available
        created = meeting.get('creation_date') or now

        meeting_id = await self.db.fetchval('''
            INSERT INTO meeting_notes (
                things3_uuid, title, meeting_type, location, meeting_date,
                time_range, attendees, agenda, key_points, decisions_made,
                issues_risks, next_steps, personal_notes, raw_notes,
                project_name, things3_status,
                morning_notes, afternoon_notes, site_observations,
                synced_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14,
                $15, $16,
                $17, $18, $19,
                $20, $21, $22
            ) RETURNING meeting_id
        ''',
            meeting['uuid'],
            meeting['title'],
            parsed.get('meeting_type', 'meeting'),
            parsed.get('location'),
            parsed.get('meeting_date'),
            parsed.get('time_range'),
            parsed.get('attendees') or None,
            parsed.get('agenda') or None,
            parsed.get('key_points') or None,
            parsed.get('decisions_made') or None,
            parsed.get('issues_risks') or None,
            parsed.get('next_steps') or None,
            parsed.get('personal_notes'),
            meeting.get('notes', ''),
            meeting.get('project_title', ''),
            meeting.get('status', 'open'),
            parsed.get('morning_notes'),
            parsed.get('afternoon_notes'),
            parsed.get('site_observations'),
            now,       # synced_at
            created,   # created_at
            now,       # updated_at
        )

        # Insert action items (parsed from notes + Things3 checklist)
        await self._sync_action_items(meeting_id, meeting, parsed)

    async def _update_meeting(self, meeting_id, meeting: Dict, parsed: Dict) -> None:
        """Update an existing meeting record."""
        now = datetime.now(timezone.utc)

        await self.db.execute('''
            UPDATE meeting_notes SET
                title = $2,
                meeting_type = $3,
                location = $4,
                meeting_date = $5,
                time_range = $6,
                attendees = $7,
                agenda = $8,
                key_points = $9,
                decisions_made = $10,
                issues_risks = $11,
                next_steps = $12,
                personal_notes = $13,
                raw_notes = $14,
                project_name = $15,
                things3_status = $16,
                morning_notes = $17,
                afternoon_notes = $18,
                site_observations = $19,
                synced_at = $20,
                updated_at = $20
            WHERE meeting_id = $1
        ''',
            meeting_id,
            meeting['title'],
            parsed.get('meeting_type', 'meeting'),
            parsed.get('location'),
            parsed.get('meeting_date'),
            parsed.get('time_range'),
            parsed.get('attendees') or None,
            parsed.get('agenda') or None,
            parsed.get('key_points') or None,
            parsed.get('decisions_made') or None,
            parsed.get('issues_risks') or None,
            parsed.get('next_steps') or None,
            parsed.get('personal_notes'),
            meeting.get('notes', ''),
            meeting.get('project_title', ''),
            meeting.get('status', 'open'),
            parsed.get('morning_notes'),
            parsed.get('afternoon_notes'),
            parsed.get('site_observations'),
            now,
        )

        # Re-sync action items: delete old, insert new
        await self.db.execute(
            "DELETE FROM meeting_action_items WHERE meeting_id = $1",
            meeting_id
        )
        await self._sync_action_items(meeting_id, meeting, parsed)


    async def _sync_action_items(self, meeting_id, meeting: Dict, parsed: Dict) -> None:
        """Insert action items from parsed notes + Things3 checklist."""
        now = datetime.now(timezone.utc)

        # Action items parsed from notes text
        for item in parsed.get('action_items', []):
            is_done = item.get('is_completed', False)
            await self.db.execute('''
                INSERT INTO meeting_action_items
                    (meeting_id, action_text, is_completed, completed_at, priority, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''',
                meeting_id,
                item['action_text'],
                is_done,
                now if is_done else None,
                3,   # default priority: medium
                now,
            )

        # Checklist items from Things3 (separate from notes)
        for ci in meeting.get('checklist_items', []):
            title = ci.get('title', '').strip()
            if not title or self.parser._is_junk_action_item(title):
                continue
            is_done = ci.get('is_completed', False)
            completed_at = ci.get('completed_date')  # datetime from Things3
            await self.db.execute('''
                INSERT INTO meeting_action_items
                    (meeting_id, action_text, is_completed, completed_at, priority, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''',
                meeting_id,
                title,
                is_done,
                completed_at if is_done else None,
                3,   # default priority: medium
                now,
            )


async def run_sync() -> Dict[str, int]:
    """Convenience function to run sync."""
    service = MeetingNotesSyncService()
    try:
        return await service.sync()
    finally:
        await service.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_sync())
    print(f"✅ Sync result: {result}")
