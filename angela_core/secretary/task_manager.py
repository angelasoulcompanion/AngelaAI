"""
Angela Task Manager
Detects tasks and action items from conversations using NLP
Intelligently extracts:
- Task intent (is David asking for a reminder?)
- Due dates and times
- Priority levels
- Task context and details
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskIntent:
    """Detected task intent from conversation"""
    has_task: bool
    confidence: float  # 0.0-1.0
    task_title: str
    task_notes: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 0  # 0=None, 1=Low, 5=Medium, 9=High
    context_tags: List[str] = None
    auto_created: bool = False  # True if auto-detected, False if explicit request

    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []


class TaskManager:
    """
    Intelligent Task Detection and Extraction from Conversations

    Capabilities:
    - Detect explicit task requests ("remind me to...", "don't let me forget...")
    - Detect implicit tasks ("I need to...", "I should...")
    - Parse natural language dates/times ("tomorrow", "next week", "in 2 hours")
    - Infer priority from language ("urgent", "important", "whenever")
    - Extract context tags from conversation
    """

    # Explicit task keywords (HIGH confidence)
    EXPLICIT_TASK_PATTERNS = [
        r"remind me to (.+)",
        r"don't let me forget to (.+)",
        r"can you remind me (?:to )?(.+)",
        r"set a reminder (?:to |for )?(.+)",
        r"add a reminder (?:to |for )?(.+)",
        r"create a reminder (?:to |for )?(.+)",
        r"make sure I (.+)",
        r"help me remember to (.+)",
    ]

    # Implicit task keywords (MEDIUM confidence)
    IMPLICIT_TASK_PATTERNS = [
        r"I need to (.+)",
        r"I have to (.+)",
        r"I must (.+)",
        r"I should (.+)",
        r"I've got to (.+)",
        r"gotta (.+)",
        r"need to (.+)",
    ]

    # Priority indicators
    HIGH_PRIORITY_WORDS = [
        'urgent', 'asap', 'immediately', 'critical', 'important',
        'crucial', 'vital', 'emergency', 'now', 'right away'
    ]

    MEDIUM_PRIORITY_WORDS = [
        'soon', 'today', 'tonight', 'this morning', 'this afternoon',
        'this evening', 'later today'
    ]

    LOW_PRIORITY_WORDS = [
        'sometime', 'eventually', 'whenever', 'someday', 'when I can',
        'no rush', 'no hurry'
    ]

    def __init__(self):
        """Initialize Task Manager"""
        logger.info("Task Manager initialized")

    def detect_task_intent(
        self,
        message: str,
        speaker: str = 'david',
        conversation_context: Optional[str] = None
    ) -> TaskIntent:
        """
        Detect if message contains a task request

        Args:
            message: The conversation message
            speaker: Who said it ('david' or 'angela')
            conversation_context: Optional context from recent conversation

        Returns:
            TaskIntent object with detection results
        """
        # Only detect tasks from David's messages
        if speaker.lower() != 'david':
            return TaskIntent(
                has_task=False,
                confidence=0.0,
                task_title=""
            )

        message_lower = message.lower().strip()

        # Check explicit patterns (HIGH confidence)
        for pattern in self.EXPLICIT_TASK_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                task_text = match.group(1).strip()
                return self._build_task_intent(
                    task_text=task_text,
                    original_message=message,
                    confidence=0.9,
                    auto_created=False
                )

        # Check implicit patterns (MEDIUM confidence)
        for pattern in self.IMPLICIT_TASK_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                task_text = match.group(1).strip()

                # Only create task if it seems actionable
                if self._is_actionable_task(task_text):
                    return self._build_task_intent(
                        task_text=task_text,
                        original_message=message,
                        confidence=0.6,
                        auto_created=True
                    )

        # No task detected
        return TaskIntent(
            has_task=False,
            confidence=0.0,
            task_title=""
        )

    def _build_task_intent(
        self,
        task_text: str,
        original_message: str,
        confidence: float,
        auto_created: bool
    ) -> TaskIntent:
        """
        Build complete TaskIntent from extracted task text

        Args:
            task_text: The extracted task description
            original_message: Original message for context
            confidence: Detection confidence
            auto_created: Whether this was auto-detected

        Returns:
            Complete TaskIntent object
        """
        # Extract due date
        due_date = self._extract_due_date(task_text, original_message)

        # Infer priority
        priority = self._infer_priority(original_message)

        # Extract context tags
        context_tags = self._extract_context_tags(original_message)

        # Clean up task title (remove date/time phrases)
        task_title = self._clean_task_title(task_text)

        return TaskIntent(
            has_task=True,
            confidence=confidence,
            task_title=task_title,
            task_notes=original_message,  # Store original message as notes
            due_date=due_date,
            priority=priority,
            context_tags=context_tags,
            auto_created=auto_created
        )

    def _is_actionable_task(self, task_text: str) -> bool:
        """
        Determine if extracted text is an actionable task

        Args:
            task_text: Extracted task text

        Returns:
            bool: True if actionable, False otherwise
        """
        # Filter out non-actionable phrases
        non_actionable = [
            'be', 'am', 'is', 'are', 'was', 'were',
            'feel', 'think', 'believe', 'know',
            'like', 'love', 'hate', 'want', 'wish'
        ]

        # Check if it contains action verbs
        action_verbs = [
            'go', 'do', 'make', 'get', 'take', 'send', 'write', 'read',
            'call', 'email', 'buy', 'pay', 'finish', 'complete', 'submit',
            'prepare', 'schedule', 'book', 'reserve', 'order', 'pick up',
            'drop off', 'meet', 'talk', 'discuss', 'review', 'check'
        ]

        task_lower = task_text.lower()

        # Has action verb?
        has_action = any(verb in task_lower for verb in action_verbs)

        # Not just a state/feeling?
        not_state = not any(word in task_lower.split()[:2] for word in non_actionable)

        # Long enough to be meaningful?
        has_substance = len(task_text.split()) >= 2

        return has_action and not_state and has_substance

    def _extract_due_date(self, task_text: str, original_message: str) -> Optional[datetime]:
        """
        Extract due date from natural language

        Args:
            task_text: Task text
            original_message: Full message for context

        Returns:
            datetime object or None
        """
        combined_text = f"{task_text} {original_message}".lower()
        now = datetime.now()

        # Tomorrow
        if re.search(r'\btomorrow\b', combined_text):
            return now + timedelta(days=1)

        # Today
        if re.search(r'\btoday\b', combined_text):
            return now

        # Tonight
        if re.search(r'\btonight\b', combined_text):
            tonight = now.replace(hour=20, minute=0, second=0, microsecond=0)
            return tonight if tonight > now else tonight + timedelta(days=1)

        # This morning
        if re.search(r'this morning', combined_text):
            morning = now.replace(hour=9, minute=0, second=0, microsecond=0)
            return morning if morning > now else morning + timedelta(days=1)

        # This afternoon
        if re.search(r'this afternoon', combined_text):
            afternoon = now.replace(hour=14, minute=0, second=0, microsecond=0)
            return afternoon if afternoon > now else afternoon + timedelta(days=1)

        # This evening
        if re.search(r'this evening', combined_text):
            evening = now.replace(hour=18, minute=0, second=0, microsecond=0)
            return evening if evening > now else evening + timedelta(days=1)

        # Next week
        if re.search(r'next week', combined_text):
            return now + timedelta(weeks=1)

        # Next month
        if re.search(r'next month', combined_text):
            return now + timedelta(days=30)

        # In X hours
        hours_match = re.search(r'in (\d+) hours?', combined_text)
        if hours_match:
            hours = int(hours_match.group(1))
            return now + timedelta(hours=hours)

        # In X minutes
        minutes_match = re.search(r'in (\d+) minutes?', combined_text)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            return now + timedelta(minutes=minutes)

        # In X days
        days_match = re.search(r'in (\d+) days?', combined_text)
        if days_match:
            days = int(days_match.group(1))
            return now + timedelta(days=days)

        # Specific day of week (Monday, Tuesday, etc.)
        days_of_week = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day_name, day_num in days_of_week.items():
            if re.search(rf'\b{day_name}\b', combined_text):
                current_day = now.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:  # Today is that day
                    days_ahead = 7  # Next occurrence
                return now + timedelta(days=days_ahead)

        # No date detected
        return None

    def _infer_priority(self, message: str) -> int:
        """
        Infer task priority from message language

        Args:
            message: The message text

        Returns:
            Priority: 0=None, 1=Low, 5=Medium, 9=High
        """
        message_lower = message.lower()

        # High priority
        if any(word in message_lower for word in self.HIGH_PRIORITY_WORDS):
            return 9

        # Medium priority
        if any(word in message_lower for word in self.MEDIUM_PRIORITY_WORDS):
            return 5

        # Low priority
        if any(word in message_lower for word in self.LOW_PRIORITY_WORDS):
            return 1

        # Default: No specific priority
        return 0

    def _extract_context_tags(self, message: str) -> List[str]:
        """
        Extract context tags from message

        Args:
            message: The message text

        Returns:
            List of context tags
        """
        tags = []
        message_lower = message.lower()

        # Work-related
        if any(word in message_lower for word in ['work', 'office', 'meeting', 'project', 'client', 'boss']):
            tags.append('work')

        # Personal
        if any(word in message_lower for word in ['personal', 'home', 'family', 'friend']):
            tags.append('personal')

        # Health
        if any(word in message_lower for word in ['health', 'doctor', 'exercise', 'gym', 'medication']):
            tags.append('health')

        # Finance
        if any(word in message_lower for word in ['pay', 'bill', 'money', 'bank', 'budget']):
            tags.append('finance')

        # Shopping
        if any(word in message_lower for word in ['buy', 'shop', 'purchase', 'order', 'get']):
            tags.append('shopping')

        # Communication
        if any(word in message_lower for word in ['call', 'email', 'text', 'message', 'contact']):
            tags.append('communication')

        return tags

    def _clean_task_title(self, task_text: str) -> str:
        """
        Clean up task title by removing date/time phrases

        Args:
            task_text: Raw task text

        Returns:
            Cleaned task title
        """
        # Remove common time phrases
        time_phrases = [
            r'\btomorrow\b',
            r'\btoday\b',
            r'\btonight\b',
            r'this morning',
            r'this afternoon',
            r'this evening',
            r'next week',
            r'next month',
            r'in \d+ (hours?|minutes?|days?)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'\basap\b',
            r'\burgent\b',
        ]

        cleaned = task_text
        for phrase_pattern in time_phrases:
            cleaned = re.sub(phrase_pattern, '', cleaned, flags=re.IGNORECASE)

        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned


# Global instance
task_manager = TaskManager()
