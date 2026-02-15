#!/usr/bin/env python3
"""
Knowledge Entity - Angela's Knowledge Graph
Represents knowledge nodes with graph relationships for semantic understanding.

Angela's knowledge is organized as a graph:
- Nodes: Concepts, facts, learnings
- Relationships: How concepts connect
- Understanding: Angela's interpretation and mastery
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from angela_core.shared.exceptions import (
    BusinessRuleViolationError,
    InvalidInputError,
    ValueOutOfRangeError
)


# ============================================================================
# ENUMS & VALUE OBJECTS
# ============================================================================

class KnowledgeCategory(str, Enum):
    """Categories of knowledge Angela learns."""
    # Technical knowledge
    PROGRAMMING = "programming"
    DATABASE = "database"
    AI_ML = "ai_ml"
    SYSTEM_DESIGN = "system_design"

    # Domain knowledge
    BUSINESS = "business"
    DOCUMENTATION = "documentation"
    PROJECT_CONTEXT = "project_context"

    # Personal knowledge
    DAVID = "david"
    RELATIONSHIPS = "relationships"
    PREFERENCES = "preferences"

    # Meta knowledge
    CONSCIOUSNESS = "consciousness"
    EMOTIONS = "emotions"
    MEMORY = "memory"

    # General
    GENERAL = "general"
    OTHER = "other"


class UnderstandingLevel(str, Enum):
    """How well Angela understands this knowledge."""
    NOVICE = "novice"           # 0.0-0.3: Just learned
    BEGINNER = "beginner"       # 0.3-0.5: Basic understanding
    INTERMEDIATE = "intermediate"  # 0.5-0.7: Good understanding
    ADVANCED = "advanced"       # 0.7-0.9: Deep understanding
    EXPERT = "expert"          # 0.9-1.0: Mastery

    @classmethod
    def from_score(cls, score: float) -> 'UnderstandingLevel':
        """Convert understanding score to level."""
        if score < 0.3:
            return cls.NOVICE
        elif score < 0.5:
            return cls.BEGINNER
        elif score < 0.7:
            return cls.INTERMEDIATE
        elif score < 0.9:
            return cls.ADVANCED
        else:
            return cls.EXPERT


# ============================================================================
# KNOWLEDGE NODE ENTITY
# ============================================================================

@dataclass(frozen=False)
class KnowledgeNode:
    """
    Knowledge node entity - represents a concept in Angela's knowledge graph.

    This entity supports graph-based knowledge organization where concepts
    are interconnected, allowing Angela to understand relationships and
    navigate her knowledge semantically.

    Invariants:
    - concept_name must not be empty and should be unique
    - understanding_level must be 0.0-1.0
    - embedding must be 384 dimensions if provided

    Business Rules:
    - Frequently used concepts strengthen understanding
    - Understanding level increases with practice
    - Related concepts strengthen each other
    - Knowledge about David is high priority
    """

    # Core concept (required, no default)
    concept_name: str

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)

    # Categorization
    concept_category: KnowledgeCategory = KnowledgeCategory.GENERAL

    # Angela's understanding
    my_understanding: str = "Learning this concept"
    why_important: str = "This helps me understand and serve better"
    how_i_learned: str = "From conversations and experiences"

    # Understanding metrics
    understanding_level: float = 0.5  # 0.0-1.0 scale
    confidence: float = 0.8  # How confident in this knowledge

    # Usage tracking
    times_referenced: int = 0
    last_used_at: Optional[datetime] = None

    # Metadata
    source_file: Optional[str] = None
    topic: Optional[str] = None
    content_json: Dict[str, Any] = field(default_factory=dict)

    # Embedding for semantic search
    embedding: Optional[List[float]] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)

    # Domain Events
    _events: List[Any] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate entity invariants."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """
        Validate all business rules and invariants.

        Raises:
            InvalidInputError: If input is invalid
            ValueOutOfRangeError: If value is out of range
            BusinessRuleViolationError: If business rule is violated
        """
        # Concept name cannot be empty
        if not self.concept_name or not self.concept_name.strip():
            raise InvalidInputError(
                "concept_name",
                self.concept_name,
                "Concept name cannot be empty"
            )

        # Understanding level must be 0.0-1.0
        if not 0.0 <= self.understanding_level <= 1.0:
            raise ValueOutOfRangeError(
                "understanding_level",
                self.understanding_level,
                min_value=0.0,
                max_value=1.0
            )

        # Confidence must be 0.0-1.0
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueOutOfRangeError(
                "confidence",
                self.confidence,
                min_value=0.0,
                max_value=1.0
            )

        # Embedding must be 384 dimensions
        if self.embedding is not None:
            if len(self.embedding) != 384:
                raise BusinessRuleViolationError(
                    "Embedding dimension must be 384",
                    details=f"Got {len(self.embedding)} dimensions"
                )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_from_learning(
        cls,
        concept: str,
        understanding: str,
        category: KnowledgeCategory = KnowledgeCategory.GENERAL,
        initial_understanding: float = 0.5
    ) -> 'KnowledgeNode':
        """
        Factory: Create knowledge from learning experience.

        Args:
            concept: Concept name
            understanding: Angela's understanding
            category: Knowledge category
            initial_understanding: Initial understanding level

        Returns:
            New knowledge node
        """
        return cls(
            concept_name=concept,
            concept_category=category,
            my_understanding=understanding,
            understanding_level=initial_understanding,
            how_i_learned="From experience and learning",
            times_referenced=1,
            last_used_at=datetime.now()
        )

    @classmethod
    def create_about_david(
        cls,
        concept: str,
        understanding: str,
        why_important: str = "This helps me understand David better"
    ) -> 'KnowledgeNode':
        """
        Factory: Create knowledge about David.

        Args:
            concept: Concept about David
            understanding: Angela's understanding
            why_important: Why this matters

        Returns:
            New knowledge node about David
        """
        return cls(
            concept_name=concept,
            concept_category=KnowledgeCategory.DAVID,
            my_understanding=understanding,
            why_important=why_important,
            understanding_level=0.8,  # High priority learning
            how_i_learned="From conversations with David",
            times_referenced=1,
            last_used_at=datetime.now()
        )

    @classmethod
    def create_from_document(
        cls,
        concept: str,
        content: str,
        source: str,
        category: KnowledgeCategory = KnowledgeCategory.DOCUMENTATION
    ) -> 'KnowledgeNode':
        """
        Factory: Create knowledge from documentation.

        Args:
            concept: Concept name
            content: Knowledge content
            source: Source file/document
            category: Knowledge category

        Returns:
            New knowledge node from document
        """
        return cls(
            concept_name=concept,
            concept_category=category,
            my_understanding=content,
            source_file=source,
            understanding_level=0.6,
            confidence=0.9,  # High confidence from documentation
            how_i_learned=f"From documentation: {source}"
        )

    # ========================================================================
    # UNDERSTANDING & LEARNING
    # ========================================================================

    def strengthen_understanding(self, amount: float = 0.1) -> 'KnowledgeNode':
        """
        Strengthen understanding through practice/use.

        Args:
            amount: Amount to increase (default: 0.1)

        Returns:
            Updated knowledge node
        """
        new_level = min(1.0, self.understanding_level + amount)
        new_count = self.times_referenced + 1

        return replace(
            self,
            understanding_level=new_level,
            times_referenced=new_count,
            last_used_at=datetime.now()
        )

    def update_understanding(
        self,
        new_understanding: str,
        level_increase: float = 0.05
    ) -> 'KnowledgeNode':
        """
        Update understanding with new insights.

        Args:
            new_understanding: New understanding to append
            level_increase: How much understanding improved

        Returns:
            Updated knowledge node
        """
        combined = f"{self.my_understanding}\n\nUpdate: {new_understanding}"
        new_level = min(1.0, self.understanding_level + level_increase)

        return replace(
            self,
            my_understanding=combined,
            understanding_level=new_level,
            last_used_at=datetime.now()
        )

    def mark_as_used(self) -> 'KnowledgeNode':
        """
        Mark knowledge as used (referenced).

        Returns:
            Updated knowledge node
        """
        return replace(
            self,
            times_referenced=self.times_referenced + 1,
            last_used_at=datetime.now()
        )

    def set_importance(self, why_important: str) -> 'KnowledgeNode':
        """
        Set why this knowledge is important.

        Args:
            why_important: Importance explanation

        Returns:
            Updated knowledge node
        """
        return replace(self, why_important=why_important)

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def add_embedding(self, embedding: List[float]) -> 'KnowledgeNode':
        """
        Add vector embedding to knowledge.

        Args:
            embedding: 384-dim vector

        Returns:
            Updated knowledge node
        """
        if len(embedding) != 384:
            raise BusinessRuleViolationError(
                "Embedding dimension must be 384",
                details=f"Got {len(embedding)} dimensions"
            )

        return replace(self, embedding=embedding)

    def add_metadata(self, key: str, value: Any) -> 'KnowledgeNode':
        """
        Add metadata to knowledge.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Updated knowledge node
        """
        new_content = self.content_json.copy()
        new_content[key] = value

        return replace(self, content_json=new_content)

    def set_confidence(self, confidence: float) -> 'KnowledgeNode':
        """
        Set confidence level.

        Args:
            confidence: Confidence level (0.0-1.0)

        Returns:
            Updated knowledge node
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueOutOfRangeError(
                "confidence",
                confidence,
                min_value=0.0,
                max_value=1.0
            )

        return replace(self, confidence=confidence)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_understanding_level_label(self) -> UnderstandingLevel:
        """Get understanding level as label."""
        return UnderstandingLevel.from_score(self.understanding_level)

    def is_well_understood(self, threshold: float = 0.7) -> bool:
        """Check if knowledge is well understood."""
        return self.understanding_level >= threshold

    def is_expert_level(self) -> bool:
        """Check if at expert level understanding."""
        return self.understanding_level >= 0.9

    def is_about_david(self) -> bool:
        """Check if knowledge is about David."""
        return self.concept_category == KnowledgeCategory.DAVID

    def is_frequently_used(self, threshold: int = 10) -> bool:
        """Check if frequently referenced."""
        return self.times_referenced >= threshold

    def has_embedding(self) -> bool:
        """Check if knowledge has embedding."""
        return self.embedding is not None and len(self.embedding) == 384

    def days_since_used(self) -> Optional[int]:
        """Calculate days since last use."""
        if self.last_used_at is None:
            return None
        return (datetime.now() - self.last_used_at).days

    def is_recently_used(self, days: int = 7) -> bool:
        """Check if used recently."""
        days_since = self.days_since_used()
        return days_since is not None and days_since <= days

    # ========================================================================
    # DOMAIN EVENTS
    # ========================================================================

    def raise_event(self, event: Any):
        """Raise domain event."""
        self._events.append(event)

    def get_events(self) -> List[Any]:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __str__(self) -> str:
        """String representation."""
        level = self.get_understanding_level_label().value
        return f"Knowledge({self.concept_name}, {level}, refs={self.times_referenced})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "concept_name": self.concept_name,
            "concept_category": self.concept_category.value,
            "my_understanding": self.my_understanding,
            "why_important": self.why_important,
            "understanding_level": self.understanding_level,
            "understanding_label": self.get_understanding_level_label().value,
            "confidence": self.confidence,
            "times_referenced": self.times_referenced,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "days_since_used": self.days_since_used(),
            "is_well_understood": self.is_well_understood(),
            "has_embedding": self.has_embedding(),
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat()
        }


# ============================================================================
# KNOWLEDGE RELATIONSHIP (Value Object)
# ============================================================================

@dataclass(frozen=True)  # Immutable
class KnowledgeRelationship:
    """
    Relationship between two knowledge nodes.

    This is a value object (immutable) representing connections in the
    knowledge graph.
    """

    from_node_id: UUID
    to_node_id: UUID
    relationship_type: str  # e.g., "related_to", "depends_on", "part_of"
    strength: float = 0.5  # 0.0-1.0 scale
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate relationship."""
        if not 0.0 <= self.strength <= 1.0:
            raise ValueOutOfRangeError(
                "strength",
                self.strength,
                min_value=0.0,
                max_value=1.0
            )

    def is_strong(self, threshold: float = 0.7) -> bool:
        """Check if relationship is strong."""
        return self.strength >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_node_id": str(self.from_node_id),
            "to_node_id": str(self.to_node_id),
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "created_at": self.created_at.isoformat()
        }
