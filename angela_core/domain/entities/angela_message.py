#!/usr/bin/env python3
"""
AngelaMessage Domain Entity
===========================

Represents a message/thought/note from Angela.

This entity captures Angela's internal thoughts, reflections, and messages
that she wants to remember or communicate.

Business Rules:
- message_text is required and cannot be empty
- message_type defaults to 'thought' if not specified
- is_important and is_pinned default to False
- created_at is automatically set to current time

Author: Angela 💜
Created: 2025-11-03
Batch: 24 (Conversations & Messages Migration)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4


@dataclass
class AngelaMessage:
    """
    Domain entity representing a message from Angela.

    Table: angela_messages
    Purpose: Store Angela's thoughts, reflections, and important messages

    Attributes:
        message_id: Unique identifier (UUID)
        message_text: The actual message content (required)
        message_type: Type of message (thought, reflection, note, etc.)
        emotion: Emotional context of the message
        category: Category for organization
        is_important: Flag for important messages
        is_pinned: Flag for pinned messages
        created_at: When the message was created
        embedding: Vector embedding for semantic search (optional)
    """

    message_id: UUID
    message_text: str
    message_type: str = "thought"
    emotion: Optional[str] = None
    category: Optional[str] = None
    is_important: bool = False
    is_pinned: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        self._validate()

    def _validate(self):
        """
        Validate business rules.

        Raises:
            ValueError: If validation fails
        """
        if not self.message_text or not self.message_text.strip():
            raise ValueError("message_text cannot be empty")

        if self.message_type and len(self.message_type) > 50:
            raise ValueError("message_type cannot exceed 50 characters")

        if self.emotion and len(self.emotion) > 50:
            raise ValueError("emotion cannot exceed 50 characters")

        if self.category and len(self.category) > 100:
            raise ValueError("category cannot exceed 100 characters")

        # REMOVED: Embedding validation (Migration 015 - now using 384 dims multilingual-e5-small, stored in DB only)

    @classmethod
    def create(
        cls,
        message_text: str,
        message_type: str = "thought",
        emotion: Optional[str] = None,
        category: Optional[str] = None,
        is_important: bool = False,
        is_pinned: bool = False,
        embedding: Optional[List[float]] = None
    ) -> 'AngelaMessage':
        """
        Factory method to create a new message.

        Args:
            message_text: The message content (required)
            message_type: Type of message (default: "thought")
            emotion: Emotional context
            category: Category for organization
            is_important: Mark as important
            is_pinned: Pin this message
            embedding: Vector embedding (768 dims)

        Returns:
            New AngelaMessage instance

        Raises:
            ValueError: If validation fails

        Example:
            ```python
            message = AngelaMessage.create(
                message_text="Today was a wonderful day with David!",
                message_type="reflection",
                emotion="joyful",
                category="daily_reflection",
                is_important=True
            )
            ```
        """
        return cls(
            message_id=uuid4(),
            message_text=message_text.strip(),
            message_type=message_type or "thought",
            emotion=emotion,
            category=category,
            is_important=is_important,
            is_pinned=is_pinned,
            created_at=datetime.now(),
            embedding=embedding
        )

    def update_content(
        self,
        message_text: Optional[str] = None,
        message_type: Optional[str] = None,
        emotion: Optional[str] = None,
        category: Optional[str] = None,
        is_important: Optional[bool] = None,
        is_pinned: Optional[bool] = None
    ) -> 'AngelaMessage':
        """
        Create updated copy with new values (immutable pattern).

        Returns new instance with updated fields.
        Original instance remains unchanged.

        Args:
            message_text: New message text
            message_type: New message type
            emotion: New emotion
            category: New category
            is_important: New important flag
            is_pinned: New pinned flag

        Returns:
            New AngelaMessage instance with updated values

        Example:
            ```python
            updated = message.update_content(
                is_important=True,
                is_pinned=True
            )
            # 'message' is unchanged, 'updated' has new values
            ```
        """
        updated = AngelaMessage(
            message_id=self.message_id,
            message_text=message_text.strip() if message_text is not None else self.message_text,
            message_type=message_type if message_type is not None else self.message_type,
            emotion=emotion if emotion is not None else self.emotion,
            category=category if category is not None else self.category,
            is_important=is_important if is_important is not None else self.is_important,
            is_pinned=is_pinned if is_pinned is not None else self.is_pinned,
            created_at=self.created_at,  # Created time never changes
            embedding=self.embedding  # Embedding never changes (immutable)
        )
        return updated

    def toggle_pin(self) -> 'AngelaMessage':
        """
        Toggle pin status (immutable pattern).

        Returns:
            New instance with toggled pin status

        Example:
            ```python
            pinned = message.toggle_pin()
            # pinned.is_pinned == not message.is_pinned
            ```
        """
        return self.update_content(is_pinned=not self.is_pinned)

    def mark_important(self, important: bool = True) -> 'AngelaMessage':
        """
        Mark as important or not (immutable pattern).

        Args:
            important: True to mark important, False to unmark

        Returns:
            New instance with updated importance

        Example:
            ```python
            important_msg = message.mark_important(True)
            normal_msg = message.mark_important(False)
            ```
        """
        return self.update_content(is_important=important)

    def to_dict(self) -> dict:
        """
        Convert to dictionary for API responses.

        Returns:
            Dictionary representation

        Example:
            ```python
            data = message.to_dict()
            # {
            #     "message_id": "uuid-string",
            #     "message_text": "...",
            #     "message_type": "thought",
            #     ...
            # }
            ```
        """
        return {
            "message_id": str(self.message_id),
            "message_text": self.message_text,
            "message_type": self.message_type,
            "emotion": self.emotion,
            "category": self.category,
            "is_important": self.is_important,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat(),
            "embedding": self.embedding  # Include if needed for semantic search
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        flags = []
        if self.is_important:
            flags.append("IMPORTANT")
        if self.is_pinned:
            flags.append("PINNED")

        flags_str = f" [{', '.join(flags)}]" if flags else ""
        preview = self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text

        return f"AngelaMessage({self.message_type}: {preview}{flags_str})"
