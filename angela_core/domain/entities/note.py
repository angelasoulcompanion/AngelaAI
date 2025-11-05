#!/usr/bin/env python3
"""
Note Entity - Angela's Note-Taking System

Represents simple notes and quick captures without due dates or completion tracking.

Angela's note system helps David capture thoughts quickly:
- Quick capture of ideas and thoughts
- Simple organization by category
- Linking to conversations for context
- No pressure of deadlines or completion
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from angela_core.shared.exceptions import (
    InvalidInputError,
    ValueOutOfRangeError
)


# ============================================================================
# ENUMS & VALUE OBJECTS
# ============================================================================

class NoteCategory(str, Enum):
    """
    Note categories for organization.
    """
    IDEA = "idea"                      # New idea or inspiration
    THOUGHT = "thought"                # Random thought
    REMINDER = "reminder"              # Mental reminder (not time-sensitive)
    MEETING = "meeting"                # Meeting notes
    LEARNING = "learning"              # Learning notes
    PERSONAL = "personal"              # Personal notes
    WORK = "work"                      # Work-related notes
    REFERENCE = "reference"            # Reference material
    JOURNAL = "journal"                # Journal entry
    OTHER = "other"                    # Uncategorized


# ============================================================================
# NOTE ENTITY
# ============================================================================

@dataclass(frozen=False)
class Note:
    """
    Note entity - represents quick notes and thought captures for David.

    Handles simple note-taking without the complexity of tasks.
    Perfect for quick thoughts, ideas, and reference material.

    Invariants:
    - content cannot be empty
    - importance_level must be 1-10 (if provided)

    Business Rules:
    - Notes are lightweight - no completion tracking
    - Notes can be pinned for quick access
    - Notes can be linked to conversations for context
    - Notes can be organized by categories and tags
    """

    # Core content (required)
    content: str

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)

    # Title & Organization
    title: Optional[str] = None
    category: Optional[NoteCategory] = None
    tags: List[str] = field(default_factory=list)

    # Importance & Pinning
    importance_level: Optional[int] = None  # 1-10 scale (optional for notes)
    is_pinned: bool = False  # Pin for quick access

    # Source & Context
    conversation_id: Optional[UUID] = None
    david_words: Optional[str] = None  # David's original words (if from conversation)
    auto_created: bool = False  # Created automatically vs. explicitly

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate note after initialization."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """Validate all business rules."""
        # Content validation
        if not self.content or not self.content.strip():
            raise InvalidInputError("Note content cannot be empty")

        # Importance validation (if provided)
        if self.importance_level is not None:
            if not (1 <= self.importance_level <= 10):
                raise ValueOutOfRangeError(
                    "importance_level",
                    self.importance_level,
                    "Importance must be between 1 and 10"
                )

    # ========================================================================
    # CONTENT MANAGEMENT
    # ========================================================================

    def update_content(self, new_content: str) -> 'Note':
        """
        Update note content.

        Args:
            new_content: New content

        Returns:
            Updated Note

        Raises:
            InvalidInputError: If new content is empty
        """
        if not new_content or not new_content.strip():
            raise InvalidInputError("Note content cannot be empty")

        return replace(
            self,
            content=new_content,
            updated_at=datetime.now()
        )

    def append_content(self, additional_content: str) -> 'Note':
        """
        Append content to existing note.

        Args:
            additional_content: Content to append

        Returns:
            Updated Note with appended content
        """
        if not additional_content or not additional_content.strip():
            return self

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        updated_content = f"{self.content}\n\n[{timestamp}]\n{additional_content}"

        return replace(
            self,
            content=updated_content,
            updated_at=datetime.now()
        )

    def update_title(self, new_title: str) -> 'Note':
        """
        Update note title.

        Args:
            new_title: New title

        Returns:
            Updated Note with new title
        """
        return replace(
            self,
            title=new_title.strip() if new_title else None,
            updated_at=datetime.now()
        )

    # ========================================================================
    # ORGANIZATION
    # ========================================================================

    def pin(self) -> 'Note':
        """
        Pin note for quick access.

        Returns:
            Updated Note marked as pinned
        """
        if self.is_pinned:
            return self

        return replace(
            self,
            is_pinned=True,
            updated_at=datetime.now()
        )

    def unpin(self) -> 'Note':
        """
        Unpin note.

        Returns:
            Updated Note marked as unpinned
        """
        if not self.is_pinned:
            return self

        return replace(
            self,
            is_pinned=False,
            updated_at=datetime.now()
        )

    def add_tag(self, tag: str) -> 'Note':
        """
        Add tag to note.

        Args:
            tag: Tag to add

        Returns:
            Updated Note with new tag
        """
        if not tag or not tag.strip():
            return self

        tag = tag.strip().lower()

        if tag in self.tags:
            return self

        updated_tags = self.tags.copy()
        updated_tags.append(tag)

        return replace(
            self,
            tags=updated_tags,
            updated_at=datetime.now()
        )

    def remove_tag(self, tag: str) -> 'Note':
        """
        Remove tag from note.

        Args:
            tag: Tag to remove

        Returns:
            Updated Note without tag
        """
        tag = tag.strip().lower()

        if tag not in self.tags:
            return self

        updated_tags = [t for t in self.tags if t != tag]

        return replace(
            self,
            tags=updated_tags,
            updated_at=datetime.now()
        )

    def update_category(self, new_category: NoteCategory) -> 'Note':
        """
        Update note category.

        Args:
            new_category: New category

        Returns:
            Updated Note with new category
        """
        return replace(
            self,
            category=new_category,
            updated_at=datetime.now()
        )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_quick_note(
        cls,
        content: str,
        title: Optional[str] = None,
        category: Optional[NoteCategory] = None
    ) -> 'Note':
        """
        Create a quick note.

        Args:
            content: Note content
            title: Optional title
            category: Optional category

        Returns:
            New Note entity
        """
        return cls(
            content=content,
            title=title,
            category=category
        )

    @classmethod
    def create_idea(
        cls,
        content: str,
        title: Optional[str] = None,
        importance: int = 5
    ) -> 'Note':
        """
        Create an idea note.

        Args:
            content: Idea content
            title: Optional title
            importance: Importance level (1-10, default 5)

        Returns:
            New idea Note entity
        """
        return cls(
            content=content,
            title=title,
            category=NoteCategory.IDEA,
            importance_level=importance,
            is_pinned=importance >= 8  # Auto-pin important ideas
        )

    @classmethod
    def create_from_conversation(
        cls,
        content: str,
        conversation_id: UUID,
        david_words: str,
        title: Optional[str] = None,
        category: Optional[NoteCategory] = None
    ) -> 'Note':
        """
        Create note from conversation with David.

        Args:
            content: Note content (extracted/summarized)
            conversation_id: Source conversation ID
            david_words: David's original words
            title: Optional title
            category: Optional category

        Returns:
            New Note entity
        """
        return cls(
            content=content,
            title=title,
            category=category,
            conversation_id=conversation_id,
            david_words=david_words,
            auto_created=True
        )

    @classmethod
    def create_meeting_notes(
        cls,
        content: str,
        title: str,
        tags: Optional[List[str]] = None
    ) -> 'Note':
        """
        Create meeting notes.

        Args:
            content: Meeting notes content
            title: Meeting title
            tags: Optional tags (participants, topics, etc.)

        Returns:
            New meeting Note entity
        """
        return cls(
            content=content,
            title=title,
            category=NoteCategory.MEETING,
            tags=tags or [],
            importance_level=7  # Meetings are important
        )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_preview(self, length: int = 100) -> str:
        """
        Get preview of note content.

        Args:
            length: Maximum preview length (default 100)

        Returns:
            Preview string
        """
        if len(self.content) <= length:
            return self.content

        return self.content[:length].strip() + "..."

    def has_tag(self, tag: str) -> bool:
        """Check if note has specific tag."""
        return tag.strip().lower() in self.tags

    def word_count(self) -> int:
        """Get word count of note content."""
        return len(self.content.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)."""
        return {
            "note_id": str(self.id),
            "title": self.title,
            "content": self.content,
            "preview": self.get_preview(),
            "category": self.category.value if self.category else None,
            "tags": self.tags,
            "importance_level": self.importance_level,
            "is_pinned": self.is_pinned,
            "word_count": self.word_count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        pin = "📌 " if self.is_pinned else ""
        title_part = f"{self.title}: " if self.title else ""
        preview = self.get_preview(50)
        return f"{pin}{title_part}{preview}"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Note(id={self.id}, title='{self.title or 'Untitled'}', "
            f"category={self.category.value if self.category else None}, "
            f"pinned={self.is_pinned})"
        )


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'Note',
    'NoteCategory',
]
