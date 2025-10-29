"""
Angela EventKit Integration
Interfaces with macOS Reminders.app using EventKit framework
Provides full CRUD operations for reminders
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

# PyObjC imports for EventKit
from Foundation import NSDate, NSCalendar, NSDateComponents
from EventKit import (
    EKEventStore,
    EKReminder,
    EKEntityTypeReminder,
    EKSpanThisEvent,
    EKAuthorizationStatusAuthorized,
    EKAuthorizationStatusDenied,
    EKAuthorizationStatusNotDetermined,
    EKAuthorizationStatusRestricted
)

logger = logging.getLogger(__name__)


@dataclass
class ReminderData:
    """Data class for reminder information"""
    title: str
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 0  # 0=None, 1=Low, 5=Medium, 9=High
    calendar_name: Optional[str] = None  # Which list to add to (default: Reminders)


class EventKitIntegration:
    """
    Integration with macOS EventKit for Reminders.app

    Capabilities:
    - Request permission to access reminders
    - Create reminders with title, notes, due date, priority
    - Read existing reminders
    - Update reminders
    - Delete reminders
    - Mark reminders as complete/incomplete
    - Search reminders by various criteria
    """

    def __init__(self):
        """Initialize EventKit store"""
        self.event_store = EKEventStore.alloc().init()
        self._default_calendar = None
        logger.info("EventKit Integration initialized")

    async def request_access(self) -> bool:
        """
        Request permission to access reminders

        Returns:
            bool: True if permission granted, False otherwise
        """
        # Check current authorization status
        status = EKEventStore.authorizationStatusForEntityType_(EKEntityTypeReminder)

        if status == EKAuthorizationStatusAuthorized:
            logger.info("✅ Reminders access already authorized")
            return True
        elif status == EKAuthorizationStatusDenied:
            logger.error("❌ Reminders access denied by user")
            logger.error("   Please grant Reminders access in System Settings > Privacy & Security > Reminders")
            return False
        elif status == EKAuthorizationStatusRestricted:
            logger.error("❌ Reminders access restricted (parental controls?)")
            return False
        elif status == EKAuthorizationStatusNotDetermined:
            logger.warning("⚠️  Reminders access not determined")
            logger.warning("   First access will trigger system permission dialog")
            logger.warning("   For now, attempting to proceed - permission will be requested on first reminder creation")
            # Return True to allow attempt - system will show dialog on first access
            return True

        return False

    def _get_default_calendar(self):
        """Get the default reminders calendar/list"""
        if self._default_calendar is None:
            self._default_calendar = self.event_store.defaultCalendarForNewReminders()
            logger.info(f"Default reminders calendar: {self._default_calendar.title()}")
        return self._default_calendar

    def _get_calendar_by_name(self, calendar_name: str):
        """Get calendar by name, or return default if not found"""
        calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)

        for calendar in calendars:
            if calendar.title() == calendar_name:
                logger.info(f"Found calendar: {calendar_name}")
                return calendar

        logger.warning(f"Calendar '{calendar_name}' not found, using default")
        return self._get_default_calendar()

    def _datetime_to_nsdate(self, dt: datetime) -> NSDate:
        """Convert Python datetime to NSDate"""
        timestamp = dt.timestamp()
        return NSDate.dateWithTimeIntervalSince1970_(timestamp)

    def _nsdate_to_datetime(self, nsdate: NSDate) -> datetime:
        """Convert NSDate to Python datetime"""
        timestamp = nsdate.timeIntervalSince1970()
        return datetime.fromtimestamp(timestamp)

    async def create_reminder(self, reminder_data: ReminderData) -> Optional[Dict[str, Any]]:
        """
        Create a new reminder in Reminders.app

        Args:
            reminder_data: ReminderData object with reminder details

        Returns:
            Dict with reminder info (identifier, title, etc.) or None if failed
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                logger.error("Cannot create reminder: no access permission")
                return None

            # Create reminder object
            reminder = EKReminder.reminderWithEventStore_(self.event_store)

            # Set calendar (list)
            if reminder_data.calendar_name:
                calendar = self._get_calendar_by_name(reminder_data.calendar_name)
            else:
                calendar = self._get_default_calendar()

            reminder.setCalendar_(calendar)

            # Set title (required)
            reminder.setTitle_(reminder_data.title)

            # Set notes (optional)
            if reminder_data.notes:
                reminder.setNotes_(reminder_data.notes)

            # Set priority (0=None, 1=Low, 5=Medium, 9=High)
            reminder.setPriority_(reminder_data.priority)

            # Set due date (optional)
            if reminder_data.due_date:
                # Create date components
                components = NSDateComponents.alloc().init()
                components.setYear_(reminder_data.due_date.year)
                components.setMonth_(reminder_data.due_date.month)
                components.setDay_(reminder_data.due_date.day)
                components.setHour_(reminder_data.due_date.hour)
                components.setMinute_(reminder_data.due_date.minute)

                # Set due date components
                reminder.setDueDateComponents_(components)

            # Save to EventKit
            error = None
            success = self.event_store.saveReminder_commit_error_(reminder, True, error)

            if success:
                result = {
                    'identifier': reminder.calendarItemIdentifier(),
                    'title': reminder.title(),
                    'notes': reminder.notes() or '',
                    'priority': reminder.priority(),
                    'due_date': self._nsdate_to_datetime(reminder.dueDateComponents().date()) if reminder.dueDateComponents() else None,
                    'is_completed': reminder.isCompleted(),
                    'calendar_name': reminder.calendar().title()
                }
                logger.info(f"✅ Created reminder: {reminder_data.title} (ID: {result['identifier']})")
                return result
            else:
                logger.error(f"❌ Failed to save reminder: {error}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating reminder: {e}")
            return None

    async def get_reminder_by_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get a reminder by its EventKit identifier

        Args:
            identifier: EventKit calendar item identifier

        Returns:
            Dict with reminder info or None if not found
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return None

            # Get reminder by identifier
            reminder = self.event_store.calendarItemWithIdentifier_(identifier)

            if reminder is None:
                logger.warning(f"Reminder not found: {identifier}")
                return None

            # Extract reminder data
            result = {
                'identifier': reminder.calendarItemIdentifier(),
                'title': reminder.title(),
                'notes': reminder.notes() or '',
                'priority': reminder.priority(),
                'due_date': self._nsdate_to_datetime(reminder.dueDateComponents().date()) if reminder.dueDateComponents() else None,
                'is_completed': reminder.isCompleted(),
                'completion_date': self._nsdate_to_datetime(reminder.completionDate()) if reminder.completionDate() else None,
                'calendar_name': reminder.calendar().title(),
                'created_at': self._nsdate_to_datetime(reminder.creationDate()) if reminder.creationDate() else None,
                'updated_at': self._nsdate_to_datetime(reminder.lastModifiedDate()) if reminder.lastModifiedDate() else None
            }

            logger.info(f"📖 Retrieved reminder: {result['title']} (ID: {identifier})")
            return result

        except Exception as e:
            logger.error(f"❌ Error getting reminder: {e}")
            return None

    async def update_reminder(self, identifier: str, reminder_data: ReminderData) -> bool:
        """
        Update an existing reminder

        Args:
            identifier: EventKit calendar item identifier
            reminder_data: Updated reminder data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return False

            # Get existing reminder
            reminder = self.event_store.calendarItemWithIdentifier_(identifier)

            if reminder is None:
                logger.error(f"Cannot update: Reminder not found: {identifier}")
                return False

            # Update fields
            reminder.setTitle_(reminder_data.title)

            if reminder_data.notes is not None:
                reminder.setNotes_(reminder_data.notes)

            if reminder_data.priority is not None:
                reminder.setPriority_(reminder_data.priority)

            if reminder_data.due_date is not None:
                components = NSDateComponents.alloc().init()
                components.setYear_(reminder_data.due_date.year)
                components.setMonth_(reminder_data.due_date.month)
                components.setDay_(reminder_data.due_date.day)
                components.setHour_(reminder_data.due_date.hour)
                components.setMinute_(reminder_data.due_date.minute)
                reminder.setDueDateComponents_(components)

            # Save changes
            error = None
            success = self.event_store.saveReminder_commit_error_(reminder, True, error)

            if success:
                logger.info(f"✅ Updated reminder: {reminder_data.title} (ID: {identifier})")
                return True
            else:
                logger.error(f"❌ Failed to update reminder: {error}")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating reminder: {e}")
            return False

    async def delete_reminder(self, identifier: str) -> bool:
        """
        Delete a reminder

        Args:
            identifier: EventKit calendar item identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return False

            # Get reminder
            reminder = self.event_store.calendarItemWithIdentifier_(identifier)

            if reminder is None:
                logger.warning(f"Cannot delete: Reminder not found: {identifier}")
                return False

            # Delete reminder
            error = None
            success = self.event_store.removeReminder_commit_error_(reminder, True, error)

            if success:
                logger.info(f"🗑️  Deleted reminder: {reminder.title()} (ID: {identifier})")
                return True
            else:
                logger.error(f"❌ Failed to delete reminder: {error}")
                return False

        except Exception as e:
            logger.error(f"❌ Error deleting reminder: {e}")
            return False

    async def mark_completed(self, identifier: str, completed: bool = True) -> bool:
        """
        Mark a reminder as completed or incomplete

        Args:
            identifier: EventKit calendar item identifier
            completed: True to mark complete, False to mark incomplete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return False

            # Get reminder
            reminder = self.event_store.calendarItemWithIdentifier_(identifier)

            if reminder is None:
                logger.error(f"Cannot mark completed: Reminder not found: {identifier}")
                return False

            # Set completion status
            reminder.setCompleted_(completed)

            # Save changes
            error = None
            success = self.event_store.saveReminder_commit_error_(reminder, True, error)

            if success:
                status = "✅ completed" if completed else "⏸️  incomplete"
                logger.info(f"Marked reminder {status}: {reminder.title()} (ID: {identifier})")
                return True
            else:
                logger.error(f"❌ Failed to mark reminder: {error}")
                return False

        except Exception as e:
            logger.error(f"❌ Error marking reminder: {e}")
            return False

    async def get_incomplete_reminders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all incomplete reminders

        Args:
            limit: Maximum number of reminders to return

        Returns:
            List of reminder dicts
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return []

            # Get all calendars
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)

            # Create predicate for incomplete reminders
            predicate = self.event_store.predicateForIncompleteRemindersWithDueDateStarting_ending_calendars_(
                None,  # Start date (None = no filter)
                None,  # End date (None = no filter)
                list(calendars)  # All calendars
            )

            # Fetch reminders (synchronous)
            reminders_obj = self.event_store.remindersMatchingPredicate_(predicate)

            # Convert to list of dicts
            results = []
            for reminder in reminders_obj[:limit]:
                result = {
                    'identifier': reminder.calendarItemIdentifier(),
                    'title': reminder.title(),
                    'notes': reminder.notes() or '',
                    'priority': reminder.priority(),
                    'due_date': self._nsdate_to_datetime(reminder.dueDateComponents().date()) if reminder.dueDateComponents() else None,
                    'is_completed': reminder.isCompleted(),
                    'calendar_name': reminder.calendar().title()
                }
                results.append(result)

            logger.info(f"📋 Retrieved {len(results)} incomplete reminders")
            return results

        except Exception as e:
            logger.error(f"❌ Error getting incomplete reminders: {e}")
            return []

    async def search_reminders_by_title(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search reminders by title

        Args:
            search_term: Search string
            limit: Maximum results

        Returns:
            List of matching reminder dicts
        """
        try:
            # Request access first
            has_access = await self.request_access()
            if not has_access:
                return []

            # Get all calendars
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeReminder)

            # Get all reminders (both complete and incomplete)
            predicate = self.event_store.predicateForRemindersInCalendars_(list(calendars))
            reminders_obj = self.event_store.remindersMatchingPredicate_(predicate)

            # Filter by title
            search_lower = search_term.lower()
            results = []

            for reminder in reminders_obj:
                if search_lower in reminder.title().lower():
                    result = {
                        'identifier': reminder.calendarItemIdentifier(),
                        'title': reminder.title(),
                        'notes': reminder.notes() or '',
                        'priority': reminder.priority(),
                        'due_date': self._nsdate_to_datetime(reminder.dueDateComponents().date()) if reminder.dueDateComponents() else None,
                        'is_completed': reminder.isCompleted(),
                        'calendar_name': reminder.calendar().title()
                    }
                    results.append(result)

                    if len(results) >= limit:
                        break

            logger.info(f"🔍 Found {len(results)} reminders matching '{search_term}'")
            return results

        except Exception as e:
            logger.error(f"❌ Error searching reminders: {e}")
            return []


# Global instance
eventkit = EventKitIntegration()
