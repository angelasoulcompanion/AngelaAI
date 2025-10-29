"""
Angela Secretary Service
Main orchestrator for Angela's secretary capabilities
Processes conversations, detects tasks, creates reminders, and tracks them
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from angela_core.database import db
from angela_core.integrations.eventkit_integration import eventkit, ReminderData
from angela_core.secretary.task_manager import task_manager, TaskIntent

logger = logging.getLogger(__name__)


class SecretaryService:
    """
    Angela's Secretary Service

    Responsibilities:
    - Monitor conversations for task requests
    - Create reminders in Reminders.app
    - Track reminders in database (secretary_reminders table)
    - Sync status between Reminders.app and database
    - Provide intelligent task management for David
    """

    def __init__(self):
        """Initialize Secretary Service"""
        logger.info("💼 Angela Secretary Service initialized")

    async def process_conversation(
        self,
        message: str,
        speaker: str,
        conversation_id: Optional[uuid.UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a conversation message and detect if it contains a task

        Args:
            message: The conversation message
            speaker: Who said it ('david' or 'angela')
            conversation_id: Optional conversation ID to link back

        Returns:
            Dict with reminder info if task was detected and created, None otherwise
        """
        try:
            # Detect task intent
            task_intent = task_manager.detect_task_intent(message, speaker)

            if not task_intent.has_task:
                logger.debug(f"No task detected in message: {message[:50]}...")
                return None

            logger.info(f"✨ Task detected! Title: {task_intent.task_title}, Confidence: {task_intent.confidence:.2f}")

            # Only create reminder if confidence is high enough
            if task_intent.confidence < 0.5:
                logger.warning(f"Task confidence too low ({task_intent.confidence:.2f}), not creating reminder")
                return None

            # Create reminder in Reminders.app
            reminder_result = await self.create_reminder_from_task(
                task_intent=task_intent,
                conversation_id=conversation_id,
                david_words=message
            )

            return reminder_result

        except Exception as e:
            logger.error(f"❌ Error processing conversation: {e}")
            return None

    async def create_reminder_from_task(
        self,
        task_intent: TaskIntent,
        conversation_id: Optional[uuid.UUID] = None,
        david_words: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a reminder from TaskIntent

        Args:
            task_intent: Detected task intent
            conversation_id: Optional conversation ID
            david_words: Original words David said

        Returns:
            Dict with reminder info or None if failed
        """
        try:
            # Prepare reminder data for EventKit
            reminder_data = ReminderData(
                title=task_intent.task_title,
                notes=task_intent.task_notes,
                due_date=task_intent.due_date,
                priority=task_intent.priority
            )

            # Create in Reminders.app
            eventkit_result = await eventkit.create_reminder(reminder_data)

            if not eventkit_result:
                logger.error("Failed to create reminder in Reminders.app")
                return None

            logger.info(f"✅ Created reminder in Reminders.app: {eventkit_result['identifier']}")

            # Store in database
            db_result = await self._store_reminder_in_db(
                eventkit_result=eventkit_result,
                task_intent=task_intent,
                conversation_id=conversation_id,
                david_words=david_words
            )

            if not db_result:
                logger.warning("Failed to store reminder in database (but reminder was created in Reminders.app)")

            return {
                'success': True,
                'eventkit_identifier': eventkit_result['identifier'],
                'reminder_id': db_result['reminder_id'] if db_result else None,
                'title': eventkit_result['title'],
                'due_date': eventkit_result['due_date'],
                'priority': eventkit_result['priority'],
                'auto_created': task_intent.auto_created,
                'confidence': task_intent.confidence
            }

        except Exception as e:
            logger.error(f"❌ Error creating reminder: {e}")
            return None

    async def _store_reminder_in_db(
        self,
        eventkit_result: Dict[str, Any],
        task_intent: TaskIntent,
        conversation_id: Optional[uuid.UUID],
        david_words: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Store reminder tracking data in database

        Args:
            eventkit_result: Result from EventKit creation
            task_intent: Original task intent
            conversation_id: Conversation that triggered this
            david_words: What David said

        Returns:
            Dict with database record or None if failed
        """
        try:
            # Generate UUID
            reminder_id = uuid.uuid4()

            # Prepare insert query
            query = """
                INSERT INTO secretary_reminders (
                    reminder_id,
                    eventkit_identifier,
                    eventkit_calendar_identifier,
                    title,
                    notes,
                    priority,
                    due_date,
                    is_completed,
                    conversation_id,
                    david_words,
                    auto_created,
                    task_type,
                    context_tags,
                    importance_level,
                    angela_interpretation,
                    confidence_score,
                    is_recurring,
                    last_synced_at,
                    sync_status,
                    created_at,
                    updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
                )
                RETURNING reminder_id, eventkit_identifier, title, created_at
            """

            # Determine task type
            task_type = 'todo'
            if task_intent.due_date:
                task_type = 'deadline'

            # Prepare values
            values = (
                reminder_id,  # $1
                eventkit_result['identifier'],  # $2
                eventkit_result.get('calendar_name'),  # $3
                eventkit_result['title'],  # $4
                eventkit_result.get('notes'),  # $5
                eventkit_result['priority'],  # $6
                eventkit_result.get('due_date'),  # $7
                eventkit_result['is_completed'],  # $8
                conversation_id,  # $9
                david_words,  # $10
                task_intent.auto_created,  # $11
                task_type,  # $12
                task_intent.context_tags,  # $13
                self._calculate_importance(task_intent),  # $14
                self._build_interpretation(task_intent),  # $15
                task_intent.confidence,  # $16
                False,  # $17 - is_recurring
                datetime.now(),  # $18 - last_synced_at
                'synced',  # $19 - sync_status
                datetime.now(),  # $20 - created_at
                datetime.now()  # $21 - updated_at
            )

            # Execute insert
            result = await db.fetchrow(query, *values)

            logger.info(f"📊 Stored reminder in database: {result['reminder_id']}")

            return dict(result)

        except Exception as e:
            logger.error(f"❌ Error storing reminder in database: {e}")
            return None

    def _calculate_importance(self, task_intent: TaskIntent) -> int:
        """
        Calculate importance level (1-10) from task intent

        Args:
            task_intent: Task intent

        Returns:
            Importance level (1-10)
        """
        # Base importance
        importance = 5

        # High priority → high importance
        if task_intent.priority == 9:
            importance = 9
        elif task_intent.priority == 5:
            importance = 7
        elif task_intent.priority == 1:
            importance = 4

        # Has due date → more important
        if task_intent.due_date:
            importance = min(importance + 1, 10)

        # High confidence → more important
        if task_intent.confidence >= 0.9:
            importance = min(importance + 1, 10)

        # Certain context tags → more important
        if 'work' in task_intent.context_tags:
            importance = min(importance + 1, 10)
        if 'health' in task_intent.context_tags:
            importance = min(importance + 1, 10)

        return importance

    def _build_interpretation(self, task_intent: TaskIntent) -> str:
        """
        Build Angela's interpretation text

        Args:
            task_intent: Task intent

        Returns:
            Interpretation string
        """
        parts = [f"Detected task: {task_intent.task_title}"]

        if task_intent.due_date:
            parts.append(f"Due: {task_intent.due_date.strftime('%Y-%m-%d %H:%M')}")

        if task_intent.priority > 0:
            priority_text = {9: 'High', 5: 'Medium', 1: 'Low'}.get(task_intent.priority, 'Normal')
            parts.append(f"Priority: {priority_text}")

        if task_intent.context_tags:
            parts.append(f"Context: {', '.join(task_intent.context_tags)}")

        parts.append(f"Confidence: {task_intent.confidence:.0%}")

        if task_intent.auto_created:
            parts.append("(Auto-detected)")
        else:
            parts.append("(Explicit request)")

        return " | ".join(parts)

    async def get_reminders_for_today(self) -> List[Dict[str, Any]]:
        """
        Get all incomplete reminders due today

        Returns:
            List of reminder dicts
        """
        try:
            query = """
                SELECT
                    reminder_id,
                    eventkit_identifier,
                    title,
                    notes,
                    priority,
                    due_date,
                    context_tags,
                    importance_level,
                    angela_interpretation
                FROM secretary_reminders
                WHERE is_completed = FALSE
                  AND DATE(due_date) = CURRENT_DATE
                ORDER BY priority DESC, due_date ASC
            """

            rows = await db.fetch(query)

            reminders = [dict(row) for row in rows]

            logger.info(f"📅 Found {len(reminders)} reminders due today")
            return reminders

        except Exception as e:
            logger.error(f"❌ Error getting today's reminders: {e}")
            return []

    async def get_upcoming_reminders(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming reminders for next N days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of reminder dicts
        """
        try:
            query = f"""
                SELECT
                    reminder_id,
                    eventkit_identifier,
                    title,
                    notes,
                    priority,
                    due_date,
                    context_tags,
                    importance_level
                FROM secretary_reminders
                WHERE is_completed = FALSE
                  AND due_date IS NOT NULL
                  AND due_date BETWEEN NOW() AND NOW() + INTERVAL '{days_ahead} days'
                ORDER BY due_date ASC
            """

            rows = await db.fetch(query)

            reminders = [dict(row) for row in rows]

            logger.info(f"📆 Found {len(reminders)} reminders in next {days_ahead} days")
            return reminders

        except Exception as e:
            logger.error(f"❌ Error getting upcoming reminders: {e}")
            return []

    async def mark_reminder_completed(
        self,
        eventkit_identifier: str,
        completed: bool = True
    ) -> bool:
        """
        Mark a reminder as completed (in both EventKit and database)

        Args:
            eventkit_identifier: EventKit identifier
            completed: True to mark complete, False to mark incomplete

        Returns:
            bool: True if successful
        """
        try:
            # Mark in Reminders.app
            eventkit_success = await eventkit.mark_completed(eventkit_identifier, completed)

            if not eventkit_success:
                logger.error(f"Failed to mark reminder in EventKit: {eventkit_identifier}")
                return False

            # Update database
            query = """
                UPDATE secretary_reminders
                SET is_completed = $1,
                    completion_date = $2,
                    last_synced_at = NOW(),
                    sync_status = 'synced'
                WHERE eventkit_identifier = $3
            """

            completion_date = datetime.now() if completed else None

            await db.execute(query, completed, completion_date, eventkit_identifier)

            status = "completed" if completed else "incomplete"
            logger.info(f"✅ Marked reminder {status}: {eventkit_identifier}")

            return True

        except Exception as e:
            logger.error(f"❌ Error marking reminder: {e}")
            return False

    async def sync_with_reminders_app(self) -> Dict[str, int]:
        """
        Sync database with Reminders.app
        Checks for completion status changes

        Returns:
            Dict with sync statistics
        """
        try:
            logger.info("🔄 Starting sync with Reminders.app...")

            # Get all incomplete reminders from database
            db_query = """
                SELECT reminder_id, eventkit_identifier, is_completed
                FROM secretary_reminders
                WHERE sync_status = 'synced'
            """

            db_reminders = await db.fetch(db_query)

            synced_count = 0
            updated_count = 0
            error_count = 0

            for reminder in db_reminders:
                try:
                    # Get current status from EventKit
                    eventkit_data = await eventkit.get_reminder_by_id(reminder['eventkit_identifier'])

                    if not eventkit_data:
                        # Reminder deleted in Reminders.app
                        await db.execute(
                            "UPDATE secretary_reminders SET sync_status = 'error', sync_error = 'Not found in Reminders.app' WHERE reminder_id = $1",
                            reminder['reminder_id']
                        )
                        error_count += 1
                        continue

                    # Check if completion status changed
                    if eventkit_data['is_completed'] != reminder['is_completed']:
                        # Update database to match Reminders.app
                        await db.execute(
                            """
                            UPDATE secretary_reminders
                            SET is_completed = $1,
                                completion_date = $2,
                                last_synced_at = NOW()
                            WHERE reminder_id = $3
                            """,
                            eventkit_data['is_completed'],
                            eventkit_data.get('completion_date'),
                            reminder['reminder_id']
                        )
                        updated_count += 1
                        logger.info(f"📝 Updated reminder {reminder['eventkit_identifier']} from Reminders.app")
                    else:
                        # Just update sync timestamp
                        await db.execute(
                            "UPDATE secretary_reminders SET last_synced_at = NOW() WHERE reminder_id = $1",
                            reminder['reminder_id']
                        )
                        synced_count += 1

                except Exception as e:
                    logger.error(f"Error syncing reminder {reminder['reminder_id']}: {e}")
                    error_count += 1
                    continue

            logger.info(f"✅ Sync complete: {synced_count} synced, {updated_count} updated, {error_count} errors")

            return {
                'synced': synced_count,
                'updated': updated_count,
                'errors': error_count,
                'total': len(db_reminders)
            }

        except Exception as e:
            logger.error(f"❌ Error syncing with Reminders.app: {e}")
            return {'synced': 0, 'updated': 0, 'errors': 0, 'total': 0}


# Global instance
secretary = SecretaryService()
