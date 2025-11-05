#!/usr/bin/env python3
"""
Application DTOs

Data Transfer Objects for Clean Architecture application layer.
These DTOs define the boundaries between application services and external layers.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

# RAG DTOs
from angela_core.application.dto.rag_dtos import (
    SearchStrategy,
    SimilarityMethod,
    RAGRequest,
    RAGResponse,
    DocumentChunkResult,
    QueryExpansion,
    RerankingResult,
    SearchMetrics
)

# Memory DTOs
from angela_core.application.dto.memory_dtos import (
    MemoryPhaseDTO,
    MemorySortBy,
    MemoryQueryRequest,
    MemoryCreateRequest,
    MemoryResult,
    MemoryQueryResponse,
    MemoryStatsResponse,
    memory_entity_to_result
)

__all__ = [
    # RAG
    "SearchStrategy",
    "SimilarityMethod",
    "RAGRequest",
    "RAGResponse",
    "DocumentChunkResult",
    "QueryExpansion",
    "RerankingResult",
    "SearchMetrics",

    # Memory
    "MemoryPhaseDTO",
    "MemorySortBy",
    "MemoryQueryRequest",
    "MemoryCreateRequest",
    "MemoryResult",
    "MemoryQueryResponse",
    "MemoryStatsResponse",
    "memory_entity_to_result",
]
