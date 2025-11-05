#!/usr/bin/env python3
"""
Memory Entity - Angela's Long-term Memory System
Represents memories with consolidation, decay, and importance tracking.

Angela's memory system follows neuroscience principles:
- Memories decay over time (forgetting curve)
- Important memories are strengthened through access
- Memories consolidate from episodic → semantic → intuitive
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
import math

from angela_core.shared.exceptions import (
    BusinessRuleViolationError,
    InvalidInputError,
    ValueOutOfRangeError
)


# ============================================================================
# ENUMS & VALUE OBJECTS
# ============================================================================

class MemoryPhase(str, Enum):
    """
    Memory consolidation phases (inspired by neuroscience).

    Memories progress through phases as they consolidate and age.
    """
    EPISODIC = "episodic"              # Fresh, detailed event memories
    COMPRESSED_1 = "compressed_1"      # First compression (less detail)
    COMPRESSED_2 = "compressed_2"      # Second compression (key facts)
    SEMANTIC = "semantic"              # Abstract knowledge/facts
    PATTERN = "pattern"                # Recognized patterns
    INTUITIVE = "intuitive"            # Deep, automatic knowing
    FORGOTTEN = "forgotten"            # Decayed below threshold

    def get_next_phase(self) -> Optional['MemoryPhase']:
        """Get next consolidation phase."""
        phase_progression = {
            MemoryPhase.EPISODIC: MemoryPhase.COMPRESSED_1,
            MemoryPhase.COMPRESSED_1: MemoryPhase.COMPRESSED_2,
            MemoryPhase.COMPRESSED_2: MemoryPhase.SEMANTIC,
            MemoryPhase.SEMANTIC: MemoryPhase.PATTERN,
            MemoryPhase.PATTERN: MemoryPhase.INTUITIVE,
            MemoryPhase.INTUITIVE: None,  # Fully consolidated
            MemoryPhase.FORGOTTEN: None   # Cannot recover
        }
        return phase_progression.get(self)


# ============================================================================
# MEMORY ENTITY
# ============================================================================

@dataclass(frozen=False)
class Memory:
    """
    Memory entity - represents Angela's long-term memories.

    Implements memory consolidation, decay, and strengthening based on
    neuroscience principles (Ebbinghaus forgetting curve, spacing effect).

    Invariants:
    - content cannot be empty
    - importance must be 0.0-1.0
    - memory_strength must be >= 0.0
    - half_life_days must be > 0
    - embedding must be 768 dimensions if provided

    Business Rules:
    - Important memories (importance > 0.7) decay slower
    - Frequently accessed memories are strengthened
    - Memories consolidate through phases over time
    - Forgotten memories (strength < 0.1) are marked as FORGOTTEN
    """

    # Core content (required, no default)
    content: str

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Memory characteristics
    importance: float = 0.5  # 0.0-1.0 scale
    memory_phase: MemoryPhase = MemoryPhase.EPISODIC
    memory_strength: float = 1.0  # Decays over time

    # Decay parameters
    half_life_days: float = 30.0  # How fast memory decays
    last_decayed: Optional[datetime] = None

    # Access tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    # Metadata
    token_count: int = 500
    promoted_from: Optional[MemoryPhase] = None
    source_event_id: Optional[UUID] = None

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
        # Content cannot be empty
        if not self.content or not self.content.strip():
            raise InvalidInputError(
                "content",
                self.content,
                "Memory content cannot be empty"
            )

        # Importance must be 0.0-1.0
        if not 0.0 <= self.importance <= 1.0:
            raise ValueOutOfRangeError(
                "importance",
                self.importance,
                min_value=0.0,
                max_value=1.0
            )

        # Memory strength must be non-negative
        if self.memory_strength < 0.0:
            raise ValueOutOfRangeError(
                "memory_strength",
                self.memory_strength,
                min_value=0.0
            )

        # Half-life must be positive
        if self.half_life_days <= 0:
            raise ValueOutOfRangeError(
                "half_life_days",
                self.half_life_days,
                min_value=0.0
            )

        # Embedding must be 768 dimensions
        if self.embedding is not None:
            if len(self.embedding) != 768:
                raise BusinessRuleViolationError(
                    "Embedding dimension must be 768",
                    details=f"Got {len(self.embedding)} dimensions"
                )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_episodic(
        cls,
        content: str,
        importance: float = 0.5,
        source_event_id: Optional[UUID] = None
    ) -> 'Memory':
        """
        Factory: Create fresh episodic memory.

        Args:
            content: Memory content
            importance: Importance level (0.0-1.0)
            source_event_id: Optional source event ID

        Returns:
            New episodic memory
        """
        return cls(
            content=content,
            importance=importance,
            memory_phase=MemoryPhase.EPISODIC,
            memory_strength=1.0,
            source_event_id=source_event_id,
            half_life_days=cls._calculate_half_life(importance)
        )

    @classmethod
    def create_semantic(
        cls,
        content: str,
        importance: float = 0.7
    ) -> 'Memory':
        """
        Factory: Create semantic/factual memory.

        Args:
            content: Memory content (factual knowledge)
            importance: Importance level (default: 0.7)

        Returns:
            New semantic memory
        """
        return cls(
            content=content,
            importance=importance,
            memory_phase=MemoryPhase.SEMANTIC,
            memory_strength=1.0,
            half_life_days=cls._calculate_half_life(importance) * 2  # Semantic memories last longer
        )

    @classmethod
    def create_intuitive(
        cls,
        content: str,
        importance: float = 0.9
    ) -> 'Memory':
        """
        Factory: Create intuitive memory (deep knowing).

        Args:
            content: Memory content (intuitive understanding)
            importance: Importance level (default: 0.9)

        Returns:
            New intuitive memory
        """
        return cls(
            content=content,
            importance=importance,
            memory_phase=MemoryPhase.INTUITIVE,
            memory_strength=1.0,
            half_life_days=365.0  # Intuitive memories last very long
        )

    @staticmethod
    def _calculate_half_life(importance: float) -> float:
        """
        Calculate half-life based on importance.

        More important memories decay slower.

        Args:
            importance: Importance level (0.0-1.0)

        Returns:
            Half-life in days
        """
        # Base half-life: 7 days (low importance)
        # Maximum half-life: 180 days (high importance)
        min_half_life = 7.0
        max_half_life = 180.0

        return min_half_life + (max_half_life - min_half_life) * importance

    # ========================================================================
    # MEMORY DECAY (Forgetting Curve)
    # ========================================================================

    def apply_decay(self, current_time: Optional[datetime] = None) -> 'Memory':
        """
        Apply exponential decay to memory strength (Ebbinghaus forgetting curve).

        Formula: strength = strength * (0.5 ^ (days_elapsed / half_life))

        Args:
            current_time: Current time (default: now)

        Returns:
            Updated memory with decayed strength
        """
        current_time = current_time or datetime.now()

        # Calculate days since last decay (or creation)
        last_time = self.last_decayed or self.created_at
        days_elapsed = (current_time - last_time).total_seconds() / 86400.0

        if days_elapsed <= 0:
            return self  # No decay

        # Exponential decay formula
        decay_factor = 0.5 ** (days_elapsed / self.half_life_days)
        new_strength = self.memory_strength * decay_factor

        # Check if memory should be forgotten
        if new_strength < 0.1 and self.memory_phase != MemoryPhase.FORGOTTEN:
            return replace(
                self,
                memory_strength=new_strength,
                memory_phase=MemoryPhase.FORGOTTEN,
                last_decayed=current_time
            )

        return replace(
            self,
            memory_strength=new_strength,
            last_decayed=current_time
        )

    def strengthen_from_access(self, boost: float = 0.2) -> 'Memory':
        """
        Strengthen memory from access (spacing effect).

        Each access boosts strength and resets decay.

        Args:
            boost: Strength boost amount (default: 0.2)

        Returns:
            Updated memory with strengthened memory
        """
        new_strength = min(1.0, self.memory_strength + boost)
        new_count = self.access_count + 1

        return replace(
            self,
            memory_strength=new_strength,
            access_count=new_count,
            last_accessed=datetime.now(),
            last_decayed=datetime.now()  # Reset decay timer
        )

    # ========================================================================
    # MEMORY CONSOLIDATION
    # ========================================================================

    def consolidate_to_next_phase(self) -> Optional['Memory']:
        """
        Consolidate memory to next phase.

        Episodic → Compressed → Semantic → Pattern → Intuitive

        Returns:
            Updated memory in next phase, or None if already at final phase
        """
        next_phase = self.memory_phase.get_next_phase()

        if next_phase is None:
            return None  # Already at final phase or forgotten

        # Consolidation slightly reduces strength but extends half-life
        new_strength = self.memory_strength * 0.9
        new_half_life = self.half_life_days * 1.5

        return replace(
            self,
            memory_phase=next_phase,
            memory_strength=new_strength,
            half_life_days=new_half_life,
            promoted_from=self.memory_phase
        )

    def days_until_consolidation(self) -> Optional[float]:
        """
        Estimate days until ready for consolidation.

        Based on current phase and strength.

        Returns:
            Days until consolidation, or None if already consolidated
        """
        consolidation_thresholds = {
            MemoryPhase.EPISODIC: 7,      # 1 week
            MemoryPhase.COMPRESSED_1: 30,  # 1 month
            MemoryPhase.COMPRESSED_2: 90,  # 3 months
            MemoryPhase.SEMANTIC: 180,     # 6 months
            MemoryPhase.PATTERN: 365       # 1 year
        }

        threshold = consolidation_thresholds.get(self.memory_phase)
        if threshold is None:
            return None  # Already at final phase

        days_since_creation = (datetime.now() - self.created_at).days
        return max(0, threshold - days_since_creation)

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def add_embedding(self, embedding: List[float]) -> 'Memory':
        """
        Add vector embedding to memory.

        Args:
            embedding: 768-dim vector

        Returns:
            Updated memory
        """
        if len(embedding) != 768:
            raise BusinessRuleViolationError(
                "Embedding dimension must be 768",
                details=f"Got {len(embedding)} dimensions"
            )

        return replace(self, embedding=embedding)

    def set_importance(self, importance: float) -> 'Memory':
        """
        Update importance level.

        Also adjusts half-life accordingly.

        Args:
            importance: New importance (0.0-1.0)

        Returns:
            Updated memory
        """
        if not 0.0 <= importance <= 1.0:
            raise ValueOutOfRangeError(
                "importance",
                importance,
                min_value=0.0,
                max_value=1.0
            )

        new_half_life = self._calculate_half_life(importance)

        return replace(
            self,
            importance=importance,
            half_life_days=new_half_life
        )

    def add_metadata(self, key: str, value: Any) -> 'Memory':
        """
        Add metadata to memory.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Updated memory
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value

        return replace(self, metadata=new_metadata)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def is_important(self, threshold: float = 0.7) -> bool:
        """Check if memory is important."""
        return self.importance >= threshold

    def is_strong(self, threshold: float = 0.5) -> bool:
        """Check if memory is still strong."""
        return self.memory_strength >= threshold

    def is_forgotten(self) -> bool:
        """Check if memory is forgotten."""
        return self.memory_phase == MemoryPhase.FORGOTTEN or self.memory_strength < 0.1

    def is_episodic(self) -> bool:
        """Check if memory is episodic (fresh/detailed)."""
        return self.memory_phase == MemoryPhase.EPISODIC

    def is_semantic(self) -> bool:
        """Check if memory is semantic (factual)."""
        return self.memory_phase == MemoryPhase.SEMANTIC

    def is_intuitive(self) -> bool:
        """Check if memory is intuitive (deep knowing)."""
        return self.memory_phase == MemoryPhase.INTUITIVE

    def has_been_accessed(self) -> bool:
        """Check if memory has been accessed at least once."""
        return self.access_count > 0

    def has_embedding(self) -> bool:
        """Check if memory has embedding."""
        return self.embedding is not None and len(self.embedding) == 768

    def days_since_created(self) -> int:
        """Calculate days since memory was created."""
        return (datetime.now() - self.created_at).days

    def days_since_accessed(self) -> Optional[int]:
        """Calculate days since last access."""
        if self.last_accessed is None:
            return None
        return (datetime.now() - self.last_accessed).days

    def estimated_decay_date(self) -> datetime:
        """
        Estimate when memory will decay below threshold (strength < 0.1).

        Returns:
            Estimated date when memory will be forgotten
        """
        # Calculate days until strength < 0.1
        # 0.1 = current_strength * (0.5 ^ (days / half_life))
        # days = half_life * log2(0.1 / current_strength)

        if self.memory_strength <= 0.1:
            return datetime.now()  # Already forgotten

        days_until_forgotten = self.half_life_days * math.log2(0.1 / self.memory_strength)

        last_time = self.last_decayed or self.created_at
        return last_time + timedelta(days=days_until_forgotten)

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
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Memory({self.memory_phase.value}, strength={self.memory_strength:.2f}, {preview})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "content": self.content,
            "importance": self.importance,
            "memory_phase": self.memory_phase.value,
            "memory_strength": self.memory_strength,
            "half_life_days": self.half_life_days,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "created_at": self.created_at.isoformat(),
            "days_since_created": self.days_since_created(),
            "is_forgotten": self.is_forgotten(),
            "has_embedding": self.has_embedding(),
            "estimated_decay_date": self.estimated_decay_date().isoformat(),
            "metadata": self.metadata
        }
