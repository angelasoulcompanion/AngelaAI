#!/usr/bin/env python3
"""
Embedding Validator Utility - DRY Compliant

Centralized embedding validation and sanitization logic to replace
3+ identical implementations across repositories.

Before (repeated in each repository):
    embedding = None
    if row.get('embedding') is not None:
        emb_list = list(row['embedding'])
        if len(emb_list) == 768:
            embedding = emb_list

After:
    embedding = EmbeddingValidator.validate(row.get('embedding'))

Created: 2026-01-12
DRY Savings: ~20 lines across 3+ repositories
"""

import json
import logging
from typing import Any, Optional, List, Union

logger = logging.getLogger(__name__)


class EmbeddingValidator:
    """
    Validate and sanitize embedding vectors.

    Handles various input formats:
    - None
    - List[float]
    - JSON string
    - PostgreSQL array (pgvector)
    - numpy array (if available)
    """

    # Default dimension for nomic-embed-text model
    DEFAULT_DIMENSION = 768

    # Common embedding dimensions
    VALID_DIMENSIONS = {
        384,   # MiniLM
        512,   # Some sentence transformers
        768,   # nomic-embed-text, BERT
        1024,  # Large models
        1536,  # OpenAI ada-002
        3072,  # OpenAI text-embedding-3-large
    }

    @classmethod
    def validate(
        cls,
        embedding_data: Any,
        expected_dim: int = DEFAULT_DIMENSION,
        strict: bool = False
    ) -> Optional[List[float]]:
        """
        Validate and sanitize an embedding vector.

        Args:
            embedding_data: Raw embedding data from database or API
            expected_dim: Expected dimension (default: 768 for nomic-embed-text)
            strict: If True, return None for wrong dimensions; if False, log warning

        Returns:
            Validated list of floats, or None if invalid

        Examples:
            >>> EmbeddingValidator.validate([0.1, 0.2, ..., 0.768])  # 768 floats
            [0.1, 0.2, ..., 0.768]

            >>> EmbeddingValidator.validate(None)
            None

            >>> EmbeddingValidator.validate('{"corrupt": "data"}')
            None
        """
        if embedding_data is None:
            return None

        try:
            # Handle JSON string
            if isinstance(embedding_data, str):
                try:
                    embedding_data = json.loads(embedding_data)
                except json.JSONDecodeError:
                    logger.debug("EmbeddingValidator: Invalid JSON string")
                    return None

            # Handle numpy array
            if hasattr(embedding_data, 'tolist'):
                embedding_data = embedding_data.tolist()

            # Convert to list
            if not isinstance(embedding_data, list):
                try:
                    embedding_data = list(embedding_data)
                except (TypeError, ValueError):
                    logger.debug("EmbeddingValidator: Cannot convert to list")
                    return None

            # Validate length
            if len(embedding_data) != expected_dim:
                if strict:
                    return None

                # Accept any valid dimension
                if len(embedding_data) not in cls.VALID_DIMENSIONS:
                    logger.warning(
                        f"EmbeddingValidator: Unexpected dimension {len(embedding_data)}, "
                        f"expected {expected_dim}"
                    )
                    return None

                # Log warning but accept
                logger.debug(
                    f"EmbeddingValidator: Dimension {len(embedding_data)} != "
                    f"expected {expected_dim}, but is valid"
                )

            # Ensure all values are floats
            return [float(x) for x in embedding_data]

        except (TypeError, ValueError) as e:
            logger.debug(f"EmbeddingValidator: Validation failed - {e}")
            return None

    @classmethod
    def is_valid(
        cls,
        embedding_data: Any,
        expected_dim: int = DEFAULT_DIMENSION
    ) -> bool:
        """
        Check if embedding data is valid without converting.

        Args:
            embedding_data: Raw embedding data
            expected_dim: Expected dimension

        Returns:
            True if valid, False otherwise
        """
        return cls.validate(embedding_data, expected_dim) is not None

    @classmethod
    def sanitize_for_db(
        cls,
        embedding: Optional[List[float]],
        as_string: bool = False
    ) -> Optional[Union[List[float], str]]:
        """
        Sanitize embedding for database storage.

        Args:
            embedding: Validated embedding list
            as_string: If True, return as JSON string for storage

        Returns:
            Sanitized embedding or None
        """
        if embedding is None:
            return None

        # Ensure it's a list of floats
        try:
            sanitized = [float(x) for x in embedding]
            if as_string:
                return json.dumps(sanitized)
            return sanitized
        except (TypeError, ValueError):
            return None

    @classmethod
    def get_dimension(cls, embedding_data: Any) -> Optional[int]:
        """
        Get the dimension of an embedding.

        Args:
            embedding_data: Raw embedding data

        Returns:
            Dimension as int, or None if invalid
        """
        validated = cls.validate(embedding_data, strict=False)
        if validated:
            return len(validated)
        return None


# Convenience aliases
validate_embedding = EmbeddingValidator.validate
is_valid_embedding = EmbeddingValidator.is_valid
sanitize_embedding = EmbeddingValidator.sanitize_for_db
