"""Training example repository interface for Angela AI."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from abc import abstractmethod

from .base import IRepository


class ITrainingExampleRepository(IRepository):
    """
    Extended interface for training example queries.

    Handles training examples for fine-tuning Angela's model.
    Examples include real conversations, synthetic data, and paraphrases.

    Part of: Self-Learning System (Phase 5+)
    """

    @abstractmethod
    async def save_batch(
        self,
        examples: List[Any]
    ) -> List[UUID]:
        """
        Save multiple training examples efficiently.

        Args:
            examples: List of TrainingExample entities

        Returns:
            List of created example UUIDs
        """
        ...

    @abstractmethod
    async def get_high_quality(
        self,
        min_score: float = 7.0,
        source_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get high-quality training examples.

        Args:
            min_score: Minimum quality score (0.0-10.0)
            source_type: Optional source type filter
            limit: Maximum number of results

        Returns:
            List of high-quality TrainingExample entities
        """
        ...

    @abstractmethod
    async def get_by_source_type(
        self,
        source_type: str,
        min_quality: float = 0.0,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get examples by source type.

        Args:
            source_type: Source type (real_conversation, synthetic, paraphrased, augmented)
            min_quality: Minimum quality score
            limit: Maximum number of results

        Returns:
            List of TrainingExample entities from source
        """
        ...

    @abstractmethod
    async def get_unused_examples(
        self,
        min_quality: float = 7.0,
        limit: int = 1000
    ) -> List[Any]:
        """
        Get examples not yet used in training.

        Args:
            min_quality: Minimum quality score
            limit: Maximum number of results

        Returns:
            List of unused high-quality TrainingExample entities
        """
        ...

    @abstractmethod
    async def mark_as_used(
        self,
        example_ids: List[UUID],
        training_date: datetime
    ) -> int:
        """
        Mark examples as used in training.

        Args:
            example_ids: List of example UUIDs
            training_date: Date of training

        Returns:
            Number of examples marked
        """
        ...

    @abstractmethod
    async def export_to_jsonl(
        self,
        output_path: str,
        min_quality: float = 7.0,
        source_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> int:
        """
        Export training examples to JSONL file for fine-tuning.

        Args:
            output_path: File path to write JSONL
            min_quality: Minimum quality threshold
            source_types: Optional list of source types to include
            limit: Optional limit on number of examples

        Returns:
            Number of examples exported
        """
        ...

    @abstractmethod
    async def find_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        min_quality: float = 7.0
    ) -> List[tuple[Any, float]]:
        """
        Find similar training examples using vector search.

        Args:
            embedding: Query embedding (768 dimensions)
            top_k: Number of results
            min_quality: Minimum quality score

        Returns:
            List of (TrainingExample, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def count_by_source_type(self, source_type: str) -> int:
        """
        Count examples by source type.

        Args:
            source_type: Source type

        Returns:
            Number of examples from source
        """
        ...

    @abstractmethod
    async def get_quality_statistics(self) -> Dict[str, Any]:
        """
        Get quality statistics for all examples.

        Returns:
            Dictionary with:
            - total_examples: Total count
            - by_source_type: Dict mapping source to count
            - by_quality_level: Dict mapping quality level to count
            - average_quality: Average quality score
            - high_quality_count: Count with score >= 7.0
            - used_in_training: Count of used examples
        """
        ...
