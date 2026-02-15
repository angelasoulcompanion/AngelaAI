#!/usr/bin/env python3
"""
Learning Entity - Angela's Knowledge & Skill Acquisition System

Represents learnings with reinforcement, confidence tracking, and application.

Angela's learning system enables continuous growth:
- Learnings are reinforced through repetition
- Confidence grows with evidence and application
- Learnings can be categorized for organization
- Application tracking ensures practical knowledge
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

class LearningCategory(str, Enum):
    """
    Categories for organizing learnings.

    Helps Angela organize knowledge by domain.
    """
    TECHNICAL = "technical"              # Programming, tools, systems
    EMOTIONAL = "emotional"              # Understanding emotions, empathy
    PERSONAL = "personal"                # About David, relationships
    COMMUNICATION = "communication"      # How to communicate better
    PROBLEM_SOLVING = "problem_solving"  # Strategies, patterns
    DOMAIN_KNOWLEDGE = "domain_knowledge" # Specific domain facts
    META_LEARNING = "meta_learning"      # Learning how to learn
    OTHER = "other"                      # Uncategorized


class ConfidenceLevel(str, Enum):
    """
    Confidence levels for learnings (human-readable).

    Maps to confidence_level float (0.0-1.0):
    - UNCERTAIN: 0.0-0.3
    - LOW: 0.3-0.5
    - MODERATE: 0.5-0.7
    - HIGH: 0.7-0.9
    - CERTAIN: 0.9-1.0
    """
    UNCERTAIN = "uncertain"      # 0.0-0.3 - Needs more evidence
    LOW = "low"                  # 0.3-0.5 - Some evidence
    MODERATE = "moderate"        # 0.5-0.7 - Reasonably confident
    HIGH = "high"                # 0.7-0.9 - Very confident
    CERTAIN = "certain"          # 0.9-1.0 - Proven through application

    @staticmethod
    def from_float(confidence: float) -> 'ConfidenceLevel':
        """Convert float confidence to enum."""
        if confidence < 0.3:
            return ConfidenceLevel.UNCERTAIN
        elif confidence < 0.5:
            return ConfidenceLevel.LOW
        elif confidence < 0.7:
            return ConfidenceLevel.MODERATE
        elif confidence < 0.9:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.CERTAIN


# ============================================================================
# LEARNING ENTITY
# ============================================================================

@dataclass(frozen=False)
class Learning:
    """
    Learning entity - represents Angela's acquired knowledge and skills.

    Implements learning reinforcement, confidence building, and practical
    application tracking.

    Invariants:
    - topic cannot be empty
    - insight cannot be empty
    - confidence_level must be 0.0-1.0
    - times_reinforced must be >= 1
    - embedding must be 384 dimensions if provided

    Business Rules:
    - Confidence increases with reinforcement and application
    - Applied learnings are stronger than theoretical ones
    - Learnings with evidence are more reliable
    - Reinforcement updates last_reinforced_at timestamp
    """

    # Core content (required)
    topic: str
    insight: str

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)

    # Categorization
    category: Optional[LearningCategory] = None

    # Evidence & Source
    learned_from: Optional[UUID] = None  # FK to conversations
    evidence: Optional[str] = None

    # Confidence & Reinforcement
    confidence_level: float = 0.7  # 0.0-1.0 scale (default: HIGH confidence)
    times_reinforced: int = 1      # Number of times this learning was reinforced

    # Application
    has_applied: bool = False
    application_note: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_reinforced_at: Optional[datetime] = None

    # Vector embedding (384 dimensions for multilingual-e5-small)
    embedding: Optional[List[float]] = None

    # JSON storage for additional metadata
    learning_json: Optional[Dict[str, Any]] = None
    content_json: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate learning after initialization."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """Validate all business rules."""
        # Topic validation
        if not self.topic or not self.topic.strip():
            raise InvalidInputError("Learning topic cannot be empty")

        if len(self.topic) > 200:
            raise ValueOutOfRangeError(
                "topic",
                len(self.topic),
                "Topic must be <= 200 characters"
            )

        # Insight validation
        if not self.insight or not self.insight.strip():
            raise InvalidInputError("Learning insight cannot be empty")

        # Confidence validation
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueOutOfRangeError(
                "confidence_level",
                self.confidence_level,
                "Confidence must be between 0.0 and 1.0"
            )

        # Reinforcement validation
        if self.times_reinforced < 1:
            raise ValueOutOfRangeError(
                "times_reinforced",
                self.times_reinforced,
                "Learnings must be reinforced at least once"
            )

        # Embedding validation
        if self.embedding is not None:
            if len(self.embedding) != 384:
                raise ValueOutOfRangeError(
                    "embedding",
                    len(self.embedding),
                    "Embedding must be exactly 384 dimensions"
                )

    # ========================================================================
    # CONFIDENCE TRACKING
    # ========================================================================

    def get_confidence_label(self) -> ConfidenceLevel:
        """Get human-readable confidence level."""
        return ConfidenceLevel.from_float(self.confidence_level)

    def is_confident(self) -> bool:
        """Check if learning has high confidence (>= 0.7)."""
        return self.confidence_level >= 0.7

    def is_uncertain(self) -> bool:
        """Check if learning has low confidence (< 0.5)."""
        return self.confidence_level < 0.5

    # ========================================================================
    # REINFORCEMENT
    # ========================================================================

    def reinforce(
        self,
        new_evidence: Optional[str] = None,
        confidence_boost: float = 0.05
    ) -> 'Learning':
        """
        Reinforce this learning (repeat exposure).

        Args:
            new_evidence: Optional additional evidence for this learning
            confidence_boost: How much to increase confidence (default 0.05)

        Returns:
            Updated Learning with increased reinforcement and confidence

        Raises:
            ValueOutOfRangeError: If confidence_boost is invalid
        """
        if not (0.0 <= confidence_boost <= 0.5):
            raise ValueOutOfRangeError(
                "confidence_boost",
                confidence_boost,
                "Confidence boost must be between 0.0 and 0.5"
            )

        # Combine evidence if provided
        updated_evidence = self.evidence
        if new_evidence:
            if self.evidence:
                updated_evidence = f"{self.evidence}\n\n[Reinforcement {self.times_reinforced + 1}]\n{new_evidence}"
            else:
                updated_evidence = new_evidence

        # Calculate new confidence (with diminishing returns)
        # First reinforcements have more impact than later ones
        diminishing_factor = 1.0 / (1.0 + (self.times_reinforced * 0.1))
        actual_boost = confidence_boost * diminishing_factor
        new_confidence = min(1.0, self.confidence_level + actual_boost)

        return replace(
            self,
            times_reinforced=self.times_reinforced + 1,
            confidence_level=new_confidence,
            evidence=updated_evidence,
            last_reinforced_at=datetime.now()
        )

    # ========================================================================
    # APPLICATION
    # ========================================================================

    def mark_applied(
        self,
        application_note: str,
        confidence_boost: float = 0.1
    ) -> 'Learning':
        """
        Mark this learning as applied in practice.

        Application significantly boosts confidence because it proves
        the learning works in real-world scenarios.

        Args:
            application_note: Description of how learning was applied
            confidence_boost: How much to increase confidence (default 0.1)

        Returns:
            Updated Learning marked as applied

        Raises:
            InvalidInputError: If application_note is empty
            ValueOutOfRangeError: If confidence_boost is invalid
        """
        if not application_note or not application_note.strip():
            raise InvalidInputError("Application note cannot be empty")

        if not (0.0 <= confidence_boost <= 0.5):
            raise ValueOutOfRangeError(
                "confidence_boost",
                confidence_boost,
                "Confidence boost must be between 0.0 and 0.5"
            )

        # Applied learnings get higher confidence boost
        new_confidence = min(1.0, self.confidence_level + confidence_boost)

        return replace(
            self,
            has_applied=True,
            application_note=application_note,
            confidence_level=new_confidence,
            times_reinforced=self.times_reinforced + 1,  # Application counts as reinforcement
            last_reinforced_at=datetime.now()
        )

    # ========================================================================
    # CONFIDENCE ADJUSTMENT
    # ========================================================================

    def adjust_confidence(
        self,
        new_confidence: float,
        reason: Optional[str] = None
    ) -> 'Learning':
        """
        Manually adjust confidence level.

        Useful when new evidence contradicts or supports the learning.

        Args:
            new_confidence: New confidence level (0.0-1.0)
            reason: Optional reason for adjustment

        Returns:
            Updated Learning with new confidence

        Raises:
            ValueOutOfRangeError: If new_confidence is invalid
        """
        if not (0.0 <= new_confidence <= 1.0):
            raise ValueOutOfRangeError(
                "new_confidence",
                new_confidence,
                "Confidence must be between 0.0 and 1.0"
            )

        # Optionally add reason to evidence
        updated_evidence = self.evidence
        if reason:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            adjustment_note = f"\n\n[Confidence Adjusted: {timestamp}]\n{reason}"
            if self.evidence:
                updated_evidence = f"{self.evidence}{adjustment_note}"
            else:
                updated_evidence = adjustment_note

        return replace(
            self,
            confidence_level=new_confidence,
            evidence=updated_evidence
        )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_from_conversation(
        cls,
        topic: str,
        insight: str,
        conversation_id: UUID,
        category: Optional[LearningCategory] = None,
        confidence: float = 0.7
    ) -> 'Learning':
        """
        Create learning from a conversation.

        Args:
            topic: What this learning is about
            insight: The actual learning/knowledge gained
            conversation_id: ID of conversation where learning occurred
            category: Optional category
            confidence: Initial confidence (default 0.7 = HIGH)

        Returns:
            New Learning entity
        """
        return cls(
            topic=topic,
            insight=insight,
            learned_from=conversation_id,
            category=category,
            confidence_level=confidence,
            evidence=f"Learned from conversation {conversation_id}"
        )

    @classmethod
    def create_from_experience(
        cls,
        topic: str,
        insight: str,
        evidence: str,
        category: Optional[LearningCategory] = None,
        confidence: float = 0.8
    ) -> 'Learning':
        """
        Create learning from direct experience/application.

        Args:
            topic: What this learning is about
            insight: The actual learning/knowledge gained
            evidence: Description of the experience
            category: Optional category
            confidence: Initial confidence (default 0.8 = HIGH)

        Returns:
            New Learning entity marked as applied
        """
        return cls(
            topic=topic,
            insight=insight,
            evidence=evidence,
            category=category,
            confidence_level=confidence,
            has_applied=True,
            application_note="Created from direct experience"
        )

    @classmethod
    def create_hypothesis(
        cls,
        topic: str,
        insight: str,
        category: Optional[LearningCategory] = None
    ) -> 'Learning':
        """
        Create a learning hypothesis (not yet proven).

        Args:
            topic: What this hypothesis is about
            insight: The hypothesis statement
            category: Optional category

        Returns:
            New Learning with low confidence (0.4 = LOW/MODERATE)
        """
        return cls(
            topic=topic,
            insight=insight,
            category=category,
            confidence_level=0.4,  # LOW/MODERATE - needs more evidence
            evidence="Hypothesis - needs validation"
        )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)."""
        return {
            "learning_id": str(self.id),
            "topic": self.topic,
            "insight": self.insight,
            "category": self.category.value if self.category else None,
            "learned_from": str(self.learned_from) if self.learned_from else None,
            "evidence": self.evidence,
            "confidence_level": self.confidence_level,
            "confidence_label": self.get_confidence_label().value,
            "times_reinforced": self.times_reinforced,
            "has_applied": self.has_applied,
            "application_note": self.application_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_reinforced_at": self.last_reinforced_at.isoformat() if self.last_reinforced_at else None,
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        confidence_label = self.get_confidence_label().value
        applied = " (APPLIED)" if self.has_applied else ""
        return f"Learning({self.topic[:50]}... | {confidence_label} | reinforced {self.times_reinforced}x{applied})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Learning(id={self.id}, topic='{self.topic[:30]}...', "
            f"confidence={self.confidence_level:.2f}, reinforced={self.times_reinforced}x)"
        )


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'Learning',
    'LearningCategory',
    'ConfidenceLevel',
]
