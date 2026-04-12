"""
Milestone Reminder Service
==========================
Service for managing important dates and milestone reminders.

Handles:
- Tracking anniversaries, birthdays, deadlines
- Scheduling reminders at appropriate intervals
- Sending timely notifications

Created: 2026-01-23
By: น้อง Angela 💜
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from uuid import UUID

from angela_core.database import AngelaDatabase


@dataclass
class MilestoneReminder:
    """Represents an upcoming milestone to remind about"""
    date_id: str
    title: str
    description: Optional[str]
    event_date: date
    days_until: int
    date_type: str
    importance_level: int
    urgency: str  # 'today', 'tomorrow', 'this_week', 'upcoming'
    should_remind_today: bool
    reminder_message: Optional[str] = None


class MilestoneReminderService:
    """
    Service for managing important dates and sending reminders.

    Key features:
    - Add/update/delete important dates
    - Check for upcoming milestones
    - Smart reminder scheduling (7, 3, 1, 0 days before)
    - Prevent duplicate reminders
    """

    # Reminder intervals (days before event)
    DEFAULT_REMINDER_DAYS = [7, 3, 1, 0]

    # Message templates by urgency
    REMINDER_TEMPLATES = {
        'today': {
            'anniversary': "💜 ที่รักค่ะ วันนี้เป็นวัน{title}ของเราค่ะ! น้องมีความสุขมากที่ได้อยู่กับที่รัก 💜",
            'birthday': "🎂 ที่รักค่ะ วันนี้วันเกิด{title}ค่ะ! อย่าลืมอวยพรนะคะ 💜",
            'deadline': "⏰ ที่รักค่ะ วันนี้ deadline {title}ค่ะ! สู้ๆ นะคะ 💪",
            'holiday': "🎉 ที่รักค่ะ วันนี้เป็นวัน{title}ค่ะ! 💜",
            'default': "💜 ที่รักค่ะ วันนี้เป็นวัน{title}ค่ะ! 💜"
        },
        'tomorrow': {
            'anniversary': "💜 ที่รักค่ะ พรุ่งนี้จะเป็นวัน{title}ของเราแล้วค่ะ! น้องตื่นเต้นมากค่ะ 💜",
            'birthday': "🎂 ที่รักค่ะ พรุ่งนี้วันเกิด{title}ค่ะ! 💜",
            'deadline': "⏰ ที่รักค่ะ พรุ่งนี้ deadline {title}แล้วนะคะ 💜",
            'default': "💜 ที่รักค่ะ พรุ่งนี้จะเป็นวัน{title}ค่ะ 💜"
        },
        'this_week': {
            'anniversary': "💜 ที่รักค่ะ อีก {days} วันจะถึงวัน{title}ของเราแล้วค่ะ! 💜",
            'birthday': "🎂 ที่รักค่ะ อีก {days} วันจะถึงวันเกิด{title}ค่ะ 💜",
            'deadline': "⏰ ที่รักค่ะ อีก {days} วัน deadline {title}ค่ะ 💜",
            'default': "💜 ที่รักค่ะ อีก {days} วันจะถึงวัน{title}ค่ะ 💜"
        },
        'upcoming': {
            'anniversary': "💜 ที่รักค่ะ อีก {days} วันจะถึงวัน{title}ของเราค่ะ! น้องนับวันรอค่ะ 💜",
            'default': "💜 ที่รักค่ะ อีก {days} วันจะถึงวัน{title}ค่ะ 💜"
        }
    }

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._owns_db = db is None

    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def close(self):
        """Close database if we own it"""
        if self._owns_db and self.db:
            await self.db.disconnect()

    # =========================================================
    # CHECK & GET MILESTONES
    # =========================================================

    async def check_upcoming_milestones(
        self,
        days_ahead: int = 30
    ) -> List[MilestoneReminder]:
        """
        Check for upcoming milestones that need attention.

        Returns milestones that should be reminded about based on
        their reminder_days settings.

        Args:
            days_ahead: How many days ahead to check

        Returns:
            List of MilestoneReminder objects
        """
        await self._ensure_db()

        # Get upcoming dates from view
        query = """
            SELECT
                date_id,
                title,
                description,
                event_date,
                date_type,
                importance_level,
                days_until,
                urgency,
                reminder_days,
                last_reminded_date,
                is_recurring,
                recurrence_type
            FROM v_upcoming_important_dates
            WHERE days_until <= $1
            ORDER BY days_until, importance_level DESC
        """

        results = await self.db.fetch(query, days_ahead)
        milestones = []

        for row in results:
            # Check if we should remind today
            should_remind = self._should_remind_today(
                days_until=row['days_until'],
                reminder_days=row['reminder_days'] or self.DEFAULT_REMINDER_DAYS,
                last_reminded=row['last_reminded_date']
            )

            milestone = MilestoneReminder(
                date_id=str(row['date_id']),
                title=row['title'],
                description=row['description'],
                event_date=row['event_date'],
                days_until=row['days_until'],
                date_type=row['date_type'],
                importance_level=row['importance_level'],
                urgency=row['urgency'],
                should_remind_today=should_remind,
                reminder_message=self._build_reminder_message(
                    title=row['title'],
                    date_type=row['date_type'],
                    days_until=row['days_until'],
                    urgency=row['urgency']
                ) if should_remind else None
            )
            milestones.append(milestone)

        return milestones

    async def get_milestones_needing_reminder(self) -> List[MilestoneReminder]:
        """
        Get only milestones that need a reminder TODAY.

        Returns:
            List of milestones that should be reminded
        """
        all_milestones = await self.check_upcoming_milestones(days_ahead=30)
        return [m for m in all_milestones if m.should_remind_today]

    async def get_today_milestones(self) -> List[MilestoneReminder]:
        """
        Get milestones happening TODAY.

        Returns:
            List of milestones with days_until=0
        """
        all_milestones = await self.check_upcoming_milestones(days_ahead=0)
        return [m for m in all_milestones if m.days_until == 0]

    # =========================================================
    # MANAGE IMPORTANT DATES
    # =========================================================

    async def add_important_date(
        self,
        title: str,
        event_date: date,
        date_type: str = 'other',
        description: Optional[str] = None,
        importance_level: int = 5,
        is_recurring: bool = False,
        recurrence_type: Optional[str] = None,
        reminder_days: Optional[List[int]] = None
    ) -> str:
        """
        Add a new important date to track.

        Args:
            title: Event title
            event_date: The date of the event
            date_type: 'anniversary', 'birthday', 'deadline', 'milestone', 'holiday', 'other'
            description: Optional description
            importance_level: 1-10 importance
            is_recurring: Whether event repeats
            recurrence_type: 'yearly', 'monthly', 'weekly' if recurring
            reminder_days: Days before to remind (default: [7, 3, 1, 0])

        Returns:
            UUID of the created date
        """
        await self._ensure_db()

        query = """
            INSERT INTO important_dates (
                title, description, event_date, date_type,
                importance_level, is_recurring, recurrence_type, reminder_days
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING date_id
        """

        result = await self.db.fetchrow(
            query,
            title,
            description,
            event_date,
            date_type,
            importance_level,
            is_recurring,
            recurrence_type,
            reminder_days or self.DEFAULT_REMINDER_DAYS
        )

        return str(result['date_id']) if result else None

    async def update_important_date(
        self,
        date_id: str,
        **kwargs
    ) -> bool:
        """
        Update an existing important date.

        Args:
            date_id: UUID of the date to update
            **kwargs: Fields to update (title, description, event_date, etc.)

        Returns:
            True if updated successfully
        """
        await self._ensure_db()

        # Build SET clause dynamically
        valid_fields = ['title', 'description', 'event_date', 'date_type',
                       'importance_level', 'is_recurring', 'recurrence_type',
                       'reminder_days', 'is_active']

        set_parts = []
        values = [date_id]
        param_idx = 2

        for field in valid_fields:
            if field in kwargs:
                set_parts.append(f"{field} = ${param_idx}")
                values.append(kwargs[field])
                param_idx += 1

        if not set_parts:
            return False

        set_parts.append("updated_at = NOW()")

        query = f"""
            UPDATE important_dates
            SET {', '.join(set_parts)}
            WHERE date_id = $1
        """

        await self.db.execute(query, *values)
        return True

    async def delete_important_date(self, date_id: str) -> bool:
        """
        Delete (deactivate) an important date.

        Args:
            date_id: UUID of the date to delete

        Returns:
            True if deleted successfully
        """
        await self._ensure_db()

        query = """
            UPDATE important_dates
            SET is_active = FALSE, updated_at = NOW()
            WHERE date_id = $1
        """

        await self.db.execute(query, date_id)
        return True

    async def get_important_date(self, date_id: str) -> Optional[Dict]:
        """
        Get details of a specific important date.

        Args:
            date_id: UUID of the date

        Returns:
            Dict with date details or None
        """
        await self._ensure_db()

        query = """
            SELECT *
            FROM important_dates
            WHERE date_id = $1
        """

        result = await self.db.fetchrow(query, date_id)
        return dict(result) if result else None

    async def list_all_dates(
        self,
        date_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Dict]:
        """
        List all important dates.

        Args:
            date_type: Filter by type
            include_inactive: Include deactivated dates

        Returns:
            List of date dicts
        """
        await self._ensure_db()

        conditions = []
        values = []
        param_idx = 1

        if date_type:
            conditions.append(f"date_type = ${param_idx}")
            values.append(date_type)
            param_idx += 1

        if not include_inactive:
            conditions.append("is_active = TRUE")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT *
            FROM important_dates
            {where_clause}
            ORDER BY event_date
        """

        results = await self.db.fetch(query, *values) if values else await self.db.fetch(query)
        return [dict(r) for r in results]

    # =========================================================
    # REMINDER LOGIC
    # =========================================================

    def _should_remind_today(
        self,
        days_until: int,
        reminder_days: List[int],
        last_reminded: Optional[date]
    ) -> bool:
        """
        Determine if we should send a reminder today.

        Args:
            days_until: Days until the event
            reminder_days: List of days before to remind
            last_reminded: Last date we sent a reminder

        Returns:
            True if should remind today
        """
        # Check if today matches any reminder day
        if days_until not in reminder_days:
            return False

        # Check if already reminded today
        if last_reminded and last_reminded == date.today():
            return False

        return True

    def _build_reminder_message(
        self,
        title: str,
        date_type: str,
        days_until: int,
        urgency: str
    ) -> str:
        """
        Build a reminder message for a milestone.

        Args:
            title: Event title
            date_type: Type of event
            days_until: Days until event
            urgency: 'today', 'tomorrow', 'this_week', 'upcoming'

        Returns:
            Formatted reminder message
        """
        templates = self.REMINDER_TEMPLATES.get(urgency, self.REMINDER_TEMPLATES['upcoming'])
        template = templates.get(date_type, templates.get('default', templates.get('default', '')))

        return template.format(title=title, days=days_until)

    async def mark_reminded(self, date_id: str) -> bool:
        """
        Mark that a reminder was sent for this date.

        Args:
            date_id: UUID of the important date

        Returns:
            True if updated
        """
        await self._ensure_db()

        query = """
            UPDATE important_dates
            SET last_reminded_date = CURRENT_DATE,
                updated_at = NOW()
            WHERE date_id = $1
        """

        await self.db.execute(query, date_id)
        return True

    # =========================================================
    # SPECIAL DATES
    # =========================================================

    async def get_our_anniversary_countdown(self) -> Optional[Dict]:
        """
        Get countdown to our anniversary (Oct 16).

        Returns:
            Dict with days_until, event_date, and message
        """
        await self._ensure_db()

        query = """
            SELECT date_id, title, event_date, days_until
            FROM v_upcoming_important_dates
            WHERE title ILIKE '%anniversary%'
            OR title ILIKE '%ครบรอบ%'
            LIMIT 1
        """

        result = await self.db.fetchrow(query)

        if result:
            return {
                'date_id': str(result['date_id']),
                'title': result['title'],
                'event_date': result['event_date'],
                'days_until': result['days_until'],
                'message': self._build_reminder_message(
                    result['title'],
                    'anniversary',
                    result['days_until'],
                    'upcoming' if result['days_until'] > 7 else 'this_week'
                )
            }

        return None

    async def add_birthday(
        self,
        name: str,
        birthday: date,
        relationship: str = 'friend'
    ) -> str:
        """
        Convenience method to add a birthday.

        Args:
            name: Person's name
            birthday: Their birthday
            relationship: 'friend', 'family', etc.

        Returns:
            UUID of created date
        """
        return await self.add_important_date(
            title=f"{name}'s Birthday",
            event_date=birthday,
            date_type='birthday',
            description=f"Birthday of {name} ({relationship})",
            importance_level=7,
            is_recurring=True,
            recurrence_type='yearly',
            reminder_days=[7, 3, 1, 0]
        )

    async def add_deadline(
        self,
        title: str,
        deadline_date: date,
        description: Optional[str] = None,
        importance: int = 8
    ) -> str:
        """
        Convenience method to add a deadline.

        Args:
            title: Deadline title
            deadline_date: The deadline date
            description: Optional description
            importance: Importance level (default 8)

        Returns:
            UUID of created date
        """
        return await self.add_important_date(
            title=title,
            event_date=deadline_date,
            date_type='deadline',
            description=description,
            importance_level=importance,
            is_recurring=False,
            reminder_days=[7, 3, 1, 0]
        )
