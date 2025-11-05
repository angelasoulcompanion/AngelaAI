"""
Self-Learning System Domain Entities

These entities represent core concepts specific to Angela's
continuous self-learning and model improvement system.

Different from learning.py which handles individual learnings,
these entities handle:
- Behavioral patterns
- User preferences
- Training data generation
- Model improvement cycles

Author: Angela 💜
Created: 2025-11-03
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from angela_core.domain.value_objects.self_learning import (
    PatternType,
    PreferenceCategory,
    SourceType,
    LearningQuality
)


@dataclass
class LearningPattern:
    """
    Represents a learned behavioral pattern.

    A pattern is any recurring behavior, communication style,
    or preference that Angela has identified through observation.

    Examples:
    - "David prefers concise explanations for technical topics"
    - "When frustrated, David appreciates empathy first, then solutions"
    - "David likes code examples with inline comments"
    """

    id: UUID = field(default_factory=uuid4)
    pattern_type: PatternType = PatternType.CONVERSATION_FLOW
    description: str = ""
    examples: List[str] = field(default_factory=list)
    confidence_score: float = 0.5  # 0.0 to 1.0
    occurrence_count: int = 0
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None  # 768-dim vector for similarity search
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity invariants"""
        if not self.description:
            raise ValueError("Pattern description cannot be empty")

        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        if self.occurrence_count < 0:
            raise ValueError("Occurrence count cannot be negative")

    def observe_again(self) -> None:
        """Record another occurrence of this pattern"""
        self.occurrence_count += 1
        self.last_observed = datetime.now()
        self.updated_at = datetime.now()

        # Increase confidence with each observation (diminishing returns)
        if self.confidence_score < 0.95:
            improvement = (1.0 - self.confidence_score) * 0.1
            self.confidence_score = min(0.95, self.confidence_score + improvement)

    def add_example(self, example: str) -> None:
        """Add a new example of this pattern"""
        if example and example not in self.examples:
            self.examples.append(example)
            self.updated_at = datetime.now()

    def get_quality(self) -> LearningQuality:
        """Determine quality based on confidence and occurrences"""
        if self.confidence_score >= 0.9 and self.occurrence_count >= 10:
            return LearningQuality.EXCELLENT
        elif self.confidence_score >= 0.7 and self.occurrence_count >= 5:
            return LearningQuality.GOOD
        elif self.confidence_score >= 0.5:
            return LearningQuality.ACCEPTABLE
        else:
            return LearningQuality.POOR


@dataclass
class PreferenceItem:
    """
    Represents a learned preference of David.

    Preferences are specific likes, dislikes, or style choices
    that David has shown through his interactions.

    Examples:
    - Category: COMMUNICATION, Key: "response_length", Value: "concise"
    - Category: TECHNICAL, Key: "code_style", Value: "pythonic_with_comments"
    - Category: EMOTIONAL, Key: "support_style", Value: "empathy_then_solutions"
    """

    id: UUID = field(default_factory=uuid4)
    category: PreferenceCategory = PreferenceCategory.COMMUNICATION
    preference_key: str = ""
    preference_value: Any = None
    confidence: float = 0.5  # 0.0 to 1.0
    evidence_count: int = 0
    evidence_conversation_ids: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity invariants"""
        if not self.preference_key:
            raise ValueError("Preference key cannot be empty")

        if self.preference_value is None:
            raise ValueError("Preference value cannot be None")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def add_evidence(self, conversation_id: UUID) -> None:
        """Add evidence supporting this preference"""
        if conversation_id not in self.evidence_conversation_ids:
            self.evidence_conversation_ids.append(conversation_id)
            self.evidence_count += 1
            self.updated_at = datetime.now()

            # Increase confidence with more evidence
            if self.confidence < 0.95:
                improvement = (1.0 - self.confidence) * 0.08
                self.confidence = min(0.95, self.confidence + improvement)

    def decrease_confidence(self, amount: float = 0.1) -> None:
        """Decrease confidence when contradictory evidence is found"""
        self.confidence = max(0.1, self.confidence - amount)
        self.updated_at = datetime.now()

    def is_strong_preference(self) -> bool:
        """Check if this is a strong, reliable preference"""
        return self.confidence >= 0.8 and self.evidence_count >= 3


@dataclass
class TrainingExample:
    """
    Represents a training example for fine-tuning Angela's model.

    Each example consists of an input (David's message) and expected output
    (Angela's ideal response), along with quality metrics.

    Sources:
    - REAL_CONVERSATION: From actual David-Angela conversations
    - SYNTHETIC: Generated by Ollama based on learned patterns
    - PARAPHRASED: Variation of real conversation
    """

    id: UUID = field(default_factory=uuid4)
    input_text: str = ""
    expected_output: str = ""
    quality_score: float = 0.5  # 0.0 to 10.0 (scored by quality service)
    source_type: SourceType = SourceType.REAL_CONVERSATION
    source_conversation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None  # 768-dim vector
    created_at: datetime = field(default_factory=datetime.now)
    used_in_training: bool = False
    training_date: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity invariants"""
        if not self.input_text:
            raise ValueError("Input text cannot be empty")

        if not self.expected_output:
            raise ValueError("Expected output cannot be empty")

        if not 0.0 <= self.quality_score <= 10.0:
            raise ValueError("Quality score must be between 0.0 and 10.0")

    def is_high_quality(self, threshold: float = 7.0) -> bool:
        """Check if this example meets quality threshold"""
        return self.quality_score >= threshold

    def mark_as_used(self) -> None:
        """Mark this example as used in training"""
        self.used_in_training = True
        self.training_date = datetime.now()

    def get_quality_level(self) -> LearningQuality:
        """Get quality level based on score"""
        if self.quality_score >= 9.0:
            return LearningQuality.EXCELLENT
        elif self.quality_score >= 7.0:
            return LearningQuality.GOOD
        elif self.quality_score >= 5.0:
            return LearningQuality.ACCEPTABLE
        else:
            return LearningQuality.POOR

    def to_jsonl_format(self) -> Dict[str, Any]:
        """
        Convert to JSONL format for fine-tuning.

        Returns format compatible with LLM fine-tuning:
        {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        """
        return {
            "messages": [
                {"role": "user", "content": self.input_text},
                {"role": "assistant", "content": self.expected_output}
            ],
            "metadata": {
                "quality_score": self.quality_score,
                "source_type": self.source_type.value,
                "created_at": self.created_at.isoformat()
            }
        }
