#!/usr/bin/env python3
"""
Pattern Entity - Domain Model for Response Patterns

Represents Angela's learned behavioral patterns for recognizing situations
and generating appropriate responses.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from angela_core.shared.exceptions import InvalidInputError, BusinessRuleViolationError


class ResponseType(str, Enum):
    """Types of responses Angela can give."""
    EMOTIONAL_SUPPORT = "emotional_support"
    FACTUAL_ANSWER = "factual_answer"
    SUGGESTION = "suggestion"
    ACKNOWLEDGMENT = "acknowledgment"
    QUESTION = "question"
    ENCOURAGEMENT = "encouragement"
    REMINDER = "reminder"
    APPRECIATION = "appreciation"
    CONCERN = "concern"
    CELEBRATION = "celebration"
    OTHER = "other"


class SituationType(str, Enum):
    """Types of situations Angela recognizes."""
    GREETING = "greeting"
    GOODBYE = "goodbye"
    QUESTION = "question"
    PROBLEM = "problem"
    ACHIEVEMENT = "achievement"
    CONCERN = "concern"
    PLANNING = "planning"
    LEARNING = "learning"
    EMOTIONAL = "emotional"
    CASUAL_CHAT = "casual_chat"
    REQUEST = "request"
    FEEDBACK = "feedback"
    OTHER = "other"


@dataclass(frozen=False)
class Pattern:
    """
    Rich domain entity for response patterns.

    Represents learned patterns for how Angela should respond
    to specific situations.

    Business Rules:
    - success_rate is calculated automatically from usage/success counts
    - Pattern must have a response template
    - Pattern must have a situation type
    - Confidence score must be 0.0-1.0
    """

    # Required fields
    situation_type: str
    response_template: str
    situation_embedding: Optional[List[float]] = None

    # Identity
    id: UUID = field(default_factory=uuid4)

    # Classification
    emotion_category: Optional[str] = None
    response_type: Optional[ResponseType] = None
    context_keywords: List[str] = field(default_factory=list)

    # Systems integration
    systems_used: Dict[str, Any] = field(default_factory=dict)

    # Usage metrics
    usage_count: int = 0
    success_count: int = 0
    avg_satisfaction: float = 0.0
    avg_response_time_ms: Optional[int] = None
    last_used_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate pattern after initialization."""
        if not self.situation_type or not self.situation_type.strip():
            raise InvalidInputError("Pattern must have a situation type")

        if not self.response_template or not self.response_template.strip():
            raise InvalidInputError("Pattern must have a response template")

        if self.usage_count < 0:
            raise InvalidInputError("Usage count cannot be negative")

        if self.success_count < 0:
            raise InvalidInputError("Success count cannot be negative")

        if self.success_count > self.usage_count:
            raise InvalidInputError("Success count cannot exceed usage count")

        if not (0.0 <= self.avg_satisfaction <= 1.0):
            raise InvalidInputError("Average satisfaction must be between 0.0 and 1.0")

    # ========================================================================
    # BUSINESS LOGIC - Pattern Effectiveness
    # ========================================================================

    def get_success_rate(self) -> float:
        """
        Calculate success rate (0.0-1.0).

        Returns:
            Success rate as decimal (0.0 = 0%, 1.0 = 100%)
        """
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    def is_effective(self, min_success_rate: float = 0.7) -> bool:
        """
        Check if pattern is effective based on success rate.

        Args:
            min_success_rate: Minimum success rate threshold (default 70%)

        Returns:
            True if pattern has sufficient usage and meets threshold
        """
        # Need minimum usage to be statistically significant
        if self.usage_count < 5:
            return False

        return self.get_success_rate() >= min_success_rate

    def is_popular(self, min_usage_count: int = 10) -> bool:
        """
        Check if pattern is frequently used.

        Args:
            min_usage_count: Minimum usage threshold

        Returns:
            True if pattern usage exceeds threshold
        """
        return self.usage_count >= min_usage_count

    def get_confidence_score(self) -> float:
        """
        Calculate overall confidence in this pattern.

        Combines success rate, usage count, and satisfaction.

        Returns:
            Confidence score 0.0-1.0
        """
        if self.usage_count == 0:
            return 0.0

        # Weight factors
        success_weight = 0.5
        usage_weight = 0.3
        satisfaction_weight = 0.2

        # Success rate (0.0-1.0)
        success_score = self.get_success_rate()

        # Usage score (logarithmic, caps at 100 uses = 1.0)
        usage_score = min(1.0, self.usage_count / 100.0)

        # Satisfaction score (already 0.0-1.0)
        satisfaction_score = self.avg_satisfaction

        confidence = (
            success_score * success_weight +
            usage_score * usage_weight +
            satisfaction_score * satisfaction_weight
        )

        return round(confidence, 3)

    # ========================================================================
    # BUSINESS LOGIC - Pattern Usage
    # ========================================================================

    def record_usage(
        self,
        success: bool,
        satisfaction: Optional[float] = None,
        response_time_ms: Optional[int] = None
    ) -> 'Pattern':
        """
        Record a usage of this pattern.

        Args:
            success: Whether the response was successful
            satisfaction: User satisfaction score (0.0-1.0)
            response_time_ms: Response generation time

        Returns:
            New Pattern instance with updated metrics
        """
        new_usage_count = self.usage_count + 1
        new_success_count = self.success_count + (1 if success else 0)

        # Update average satisfaction (running average)
        new_avg_satisfaction = self.avg_satisfaction
        if satisfaction is not None:
            if not (0.0 <= satisfaction <= 1.0):
                raise InvalidInputError("Satisfaction must be between 0.0 and 1.0")

            # Running average formula
            total = self.avg_satisfaction * self.usage_count + satisfaction
            new_avg_satisfaction = total / new_usage_count

        # Update average response time (running average)
        new_avg_response_time = self.avg_response_time_ms
        if response_time_ms is not None:
            if response_time_ms < 0:
                raise InvalidInputError("Response time cannot be negative")

            if self.avg_response_time_ms is None:
                new_avg_response_time = response_time_ms
            else:
                total = self.avg_response_time_ms * self.usage_count + response_time_ms
                new_avg_response_time = int(total / new_usage_count)

        return replace(
            self,
            usage_count=new_usage_count,
            success_count=new_success_count,
            avg_satisfaction=round(new_avg_satisfaction, 3),
            avg_response_time_ms=new_avg_response_time,
            last_used_at=datetime.now(),
            updated_at=datetime.now()
        )

    def add_keyword(self, keyword: str) -> 'Pattern':
        """
        Add a context keyword to the pattern.

        Args:
            keyword: Keyword to add

        Returns:
            New Pattern instance with updated keywords
        """
        if not keyword or not keyword.strip():
            return self

        keyword = keyword.strip().lower()

        if keyword in self.context_keywords:
            return self

        new_keywords = self.context_keywords.copy()
        new_keywords.append(keyword)

        return replace(
            self,
            context_keywords=new_keywords,
            updated_at=datetime.now()
        )

    def remove_keyword(self, keyword: str) -> 'Pattern':
        """
        Remove a context keyword from the pattern.

        Args:
            keyword: Keyword to remove

        Returns:
            New Pattern instance with updated keywords
        """
        if not keyword or keyword not in self.context_keywords:
            return self

        new_keywords = self.context_keywords.copy()
        new_keywords.remove(keyword)

        return replace(
            self,
            context_keywords=new_keywords,
            updated_at=datetime.now()
        )

    def update_response_template(self, new_template: str) -> 'Pattern':
        """
        Update the response template.

        Args:
            new_template: New response template

        Returns:
            New Pattern instance with updated template
        """
        if not new_template or not new_template.strip():
            raise InvalidInputError("Response template cannot be empty")

        if new_template == self.response_template:
            return self

        return replace(
            self,
            response_template=new_template,
            updated_at=datetime.now()
        )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_from_conversation(
        cls,
        situation_type: str,
        response_template: str,
        emotion_category: Optional[str] = None,
        context_keywords: Optional[List[str]] = None
    ) -> 'Pattern':
        """
        Create a new pattern from a conversation.

        Args:
            situation_type: Type of situation
            response_template: How Angela should respond
            emotion_category: Associated emotion
            context_keywords: Keywords for matching

        Returns:
            New Pattern instance
        """
        return cls(
            situation_type=situation_type,
            response_template=response_template,
            emotion_category=emotion_category,
            context_keywords=context_keywords or [],
            response_type=ResponseType.OTHER
        )

    @classmethod
    def create_greeting_pattern(
        cls,
        response_template: str,
        time_of_day: Optional[str] = None
    ) -> 'Pattern':
        """
        Create a greeting pattern.

        Args:
            response_template: Greeting template
            time_of_day: morning, afternoon, evening, night

        Returns:
            New Pattern instance
        """
        keywords = ["greeting", "hello", "hi", "สวัสดี"]
        if time_of_day:
            keywords.append(time_of_day)

        return cls(
            situation_type=SituationType.GREETING.value,
            response_template=response_template,
            response_type=ResponseType.ACKNOWLEDGMENT,
            context_keywords=keywords
        )

    @classmethod
    def create_support_pattern(
        cls,
        response_template: str,
        emotion_category: str,
        keywords: Optional[List[str]] = None
    ) -> 'Pattern':
        """
        Create an emotional support pattern.

        Args:
            response_template: Support response template
            emotion_category: Associated emotion
            keywords: Context keywords

        Returns:
            New Pattern instance
        """
        return cls(
            situation_type=SituationType.EMOTIONAL.value,
            response_template=response_template,
            emotion_category=emotion_category,
            response_type=ResponseType.EMOTIONAL_SUPPORT,
            context_keywords=keywords or []
        )
