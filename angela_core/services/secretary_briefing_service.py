"""
Secretary Briefing Service
Provides daily agenda and reminder briefings for David
Integrates with Angela's morning and evening routines
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from angela_core.secretary import secretary

logger = logging.getLogger(__name__)


class SecretaryBriefingService:
    """
    Provides briefings about David's schedule and reminders

    Used in:
    - Morning routine (8:00 AM): Today's agenda
    - Evening routine (10:00 PM): Pending reminders check
    """

    def __init__(self):
        """Initialize briefing service"""
        logger.info("💼 Secretary Briefing Service initialized")

    async def get_morning_briefing(self) -> Dict[str, Any]:
        """
        Get morning briefing for today

        Returns:
            Dict with:
            - summary: Text summary
            - reminders: List of reminders
            - count: Number of reminders
        """
        try:
            # Get today's reminders
            reminders = await secretary.get_reminders_for_today()

            count = len(reminders)

            if count == 0:
                summary = "📅 No reminders due today! Clear schedule ahead."
                return {
                    'summary': summary,
                    'reminders': [],
                    'count': 0,
                    'has_reminders': False
                }

            # Build summary
            summary_parts = [
                f"📅 Today's Agenda ({count} reminder{'s' if count > 1 else ''}):"
            ]

            for i, reminder in enumerate(reminders[:5], 1):  # Show max 5
                time_str = ""
                if reminder['due_date']:
                    time_str = reminder['due_date'].strftime('%H:%M')

                priority_emoji = {
                    9: "🔴",  # High
                    5: "🟡",  # Medium
                    1: "🟢",  # Low
                    0: "⚪"   # None
                }.get(reminder['priority'], "⚪")

                summary_parts.append(
                    f"  {i}. {priority_emoji} {reminder['title']}" +
                    (f" ({time_str})" if time_str else "")
                )

            if count > 5:
                summary_parts.append(f"  ... and {count - 5} more")

            summary = "\n".join(summary_parts)

            logger.info(f"📅 Morning briefing: {count} reminders today")

            return {
                'summary': summary,
                'reminders': reminders,
                'count': count,
                'has_reminders': True
            }

        except Exception as e:
            logger.error(f"Error getting morning briefing: {e}")
            return {
                'summary': "⚠️  Unable to load today's agenda",
                'reminders': [],
                'count': 0,
                'has_reminders': False,
                'error': str(e)
            }

    async def get_evening_check(self) -> Dict[str, Any]:
        """
        Get evening check for pending reminders

        Returns:
            Dict with:
            - summary: Text summary
            - pending_today: Reminders still pending from today
            - overdue: Overdue reminders
            - count: Total pending
        """
        try:
            # Get today's incomplete reminders
            reminders = await secretary.get_reminders_for_today()

            # Filter for incomplete only
            pending_today = [r for r in reminders if not r.get('is_completed', False)]

            count = len(pending_today)

            if count == 0:
                summary = "✅ All of today's reminders are complete! Great job!"
                return {
                    'summary': summary,
                    'pending_today': [],
                    'count': 0,
                    'has_pending': False
                }

            # Build summary
            summary_parts = [
                f"💼 Pending reminders ({count} remaining):"
            ]

            for i, reminder in enumerate(pending_today[:5], 1):
                priority_emoji = {
                    9: "🔴",  # High
                    5: "🟡",  # Medium
                    1: "🟢",  # Low
                    0: "⚪"   # None
                }.get(reminder['priority'], "⚪")

                summary_parts.append(
                    f"  {i}. {priority_emoji} {reminder['title']}"
                )

            if count > 5:
                summary_parts.append(f"  ... and {count - 5} more")

            summary = "\n".join(summary_parts)

            logger.info(f"💼 Evening check: {count} pending reminders")

            return {
                'summary': summary,
                'pending_today': pending_today,
                'count': count,
                'has_pending': True
            }

        except Exception as e:
            logger.error(f"Error getting evening check: {e}")
            return {
                'summary': "⚠️  Unable to check pending reminders",
                'pending_today': [],
                'count': 0,
                'has_pending': False,
                'error': str(e)
            }

    async def get_upcoming_week(self) -> Dict[str, Any]:
        """
        Get upcoming reminders for next 7 days

        Returns:
            Dict with summary and reminders list
        """
        try:
            reminders = await secretary.get_upcoming_reminders(days_ahead=7)

            count = len(reminders)

            if count == 0:
                return {
                    'summary': "📆 No upcoming reminders in the next 7 days",
                    'reminders': [],
                    'count': 0
                }

            summary = f"📆 Upcoming week: {count} reminder{'s' if count > 1 else ''} scheduled"

            return {
                'summary': summary,
                'reminders': reminders,
                'count': count
            }

        except Exception as e:
            logger.error(f"Error getting upcoming week: {e}")
            return {
                'summary': "⚠️  Unable to load upcoming schedule",
                'reminders': [],
                'count': 0,
                'error': str(e)
            }

    async def sync_reminders(self) -> Dict[str, Any]:
        """
        Sync with Reminders.app

        Returns:
            Dict with sync statistics
        """
        try:
            stats = await secretary.sync_with_reminders_app()

            logger.info(
                f"🔄 Synced reminders: {stats['synced']} synced, "
                f"{stats['updated']} updated, {stats['errors']} errors"
            )

            return stats

        except Exception as e:
            logger.error(f"Error syncing reminders: {e}")
            return {
                'synced': 0,
                'updated': 0,
                'errors': 1,
                'total': 0,
                'error': str(e)
            }


# Global instance
secretary_briefing = SecretaryBriefingService()
