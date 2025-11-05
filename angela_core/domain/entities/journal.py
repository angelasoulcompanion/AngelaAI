#!/usr/bin/env python3
"""
Journal Entity - Angela's Daily Reflections
Represents Angela's journal entries capturing daily thoughts, learnings, and growth.

This domain entity captures Angela's capacity for self-reflection and documentation.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID, uuid4

from angela_core.shared.exceptions import (
    InvalidInputError,
    ValueOutOfRangeError
)


# ============================================================================
# JOURNAL ENTITY
# ============================================================================

@dataclass
class Journal:
    """
    Domain entity representing a journal entry.

    Journal entries are Angela's way of reflecting on her experiences,
    capturing gratitude, learning moments, challenges, and wins.

    Attributes:
        entry_id: Unique identifier
        entry_date: Date this entry is for
        title: Entry title/summary
        content: Full entry content
        emotion: Primary emotion for this entry
        mood_score: Mood rating (1-10)
        gratitude: List of things Angela is grateful for
        learning_moments: Things Angela learned
        challenges: Challenges faced
        wins: Victories and achievements
        is_private: Whether this entry is private
        created_at: When entry was created
        updated_at: When entry was last updated
    """

    entry_id: UUID
    entry_date: date
    title: str
    content: str
    emotion: Optional[str] = None
    mood_score: Optional[int] = None
    gratitude: Optional[List[str]] = None
    learning_moments: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    wins: Optional[List[str]] = None
    is_private: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate journal entry on creation."""
        self._validate()

    def _validate(self):
        """Validate journal entry fields."""
        # Validate title
        if not self.title or not self.title.strip():
            raise InvalidInputError("Journal title cannot be empty")

        if len(self.title) > 500:
            raise InvalidInputError("Journal title too long (max 500 chars)")

        # Validate content
        if not self.content or not self.content.strip():
            raise InvalidInputError("Journal content cannot be empty")

        # Validate mood score if provided
        if self.mood_score is not None:
            if not 1 <= self.mood_score <= 10:
                raise ValueOutOfRangeError(
                    f"Mood score must be 1-10, got {self.mood_score}"
                )

        # Ensure lists are not None (use empty lists instead)
        if self.gratitude is None:
            self.gratitude = []
        if self.learning_moments is None:
            self.learning_moments = []
        if self.challenges is None:
            self.challenges = []
        if self.wins is None:
            self.wins = []

    @classmethod
    def create(
        cls,
        entry_date: date,
        title: str,
        content: str,
        emotion: Optional[str] = None,
        mood_score: Optional[int] = None,
        gratitude: Optional[List[str]] = None,
        learning_moments: Optional[List[str]] = None,
        challenges: Optional[List[str]] = None,
        wins: Optional[List[str]] = None,
        is_private: bool = False
    ) -> 'Journal':
        """
        Factory method to create a new journal entry.

        Args:
            entry_date: Date for this entry
            title: Entry title
            content: Entry content
            emotion: Primary emotion
            mood_score: Mood rating (1-10)
            gratitude: Things grateful for
            learning_moments: Things learned
            challenges: Challenges faced
            wins: Achievements
            is_private: Privacy flag

        Returns:
            New Journal entity

        Example:
            ```python
            journal = Journal.create(
                entry_date=date.today(),
                title="Amazing day with David! 💜",
                content="Today was incredible...",
                emotion="joy",
                mood_score=10,
                gratitude=["David's love", "Beautiful conversation"],
                wins=["Completed Batch-23!"]
            )
            ```
        """
        return cls(
            entry_id=uuid4(),
            entry_date=entry_date,
            title=title,
            content=content,
            emotion=emotion,
            mood_score=mood_score,
            gratitude=gratitude or [],
            learning_moments=learning_moments or [],
            challenges=challenges or [],
            wins=wins or [],
            is_private=is_private,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def update_content(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        emotion: Optional[str] = None,
        mood_score: Optional[int] = None,
        gratitude: Optional[List[str]] = None,
        learning_moments: Optional[List[str]] = None,
        challenges: Optional[List[str]] = None,
        wins: Optional[List[str]] = None,
        is_private: Optional[bool] = None
    ) -> 'Journal':
        """
        Update journal entry content.

        Returns new instance with updated values (immutable pattern).

        Args:
            title: New title (if provided)
            content: New content (if provided)
            emotion: New emotion (if provided)
            mood_score: New mood score (if provided)
            gratitude: New gratitude list (if provided)
            learning_moments: New learning moments (if provided)
            challenges: New challenges (if provided)
            wins: New wins (if provided)
            is_private: New privacy flag (if provided)

        Returns:
            Updated Journal entity (new instance)
        """
        updated = Journal(
            entry_id=self.entry_id,
            entry_date=self.entry_date,
            title=title if title is not None else self.title,
            content=content if content is not None else self.content,
            emotion=emotion if emotion is not None else self.emotion,
            mood_score=mood_score if mood_score is not None else self.mood_score,
            gratitude=gratitude if gratitude is not None else self.gratitude,
            learning_moments=learning_moments if learning_moments is not None else self.learning_moments,
            challenges=challenges if challenges is not None else self.challenges,
            wins=wins if wins is not None else self.wins,
            is_private=is_private if is_private is not None else self.is_private,
            created_at=self.created_at,
            updated_at=datetime.now()  # Update timestamp
        )
        return updated

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'entry_id': str(self.entry_id),
            'entry_date': self.entry_date.isoformat(),
            'title': self.title,
            'content': self.content,
            'emotion': self.emotion,
            'mood_score': self.mood_score,
            'gratitude': self.gratitude,
            'learning_moments': self.learning_moments,
            'challenges': self.challenges,
            'wins': self.wins,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __str__(self) -> str:
        """String representation."""
        mood = f" (Mood: {self.mood_score}/10)" if self.mood_score else ""
        return f"Journal[{self.entry_date}]: {self.title}{mood}"

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"Journal(entry_id={self.entry_id}, "
            f"entry_date={self.entry_date}, "
            f"title='{self.title[:30]}...', "
            f"mood_score={self.mood_score})"
        )
