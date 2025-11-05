#!/usr/bin/env python3
"""
Memory Service DTOs (Data Transfer Objects)

Request/Response models for Memory Repository and Services.
Clean Architecture boundary between Application and Domain layers.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class MemoryPhaseDTO(str, Enum):
    """
    Memory consolidation phases for DTOs.

    Maps to domain MemoryPhase enum but used at application boundary.
    """
    EPISODIC = "episodic"
    COMPRESSED_1 = "compressed_1"
    COMPRESSED_2 = "compressed_2"
    SEMANTIC = "semantic"
    PATTERN = "pattern"
    INTUITIVE = "intuitive"
    FORGOTTEN = "forgotten"


class MemorySortBy(str, Enum):
    """Sort options for memory queries."""
    CREATED_AT = "created_at"
    IMPORTANCE = "importance"
    MEMORY_STRENGTH = "memory_strength"
    ACCESS_COUNT = "access_count"
    LAST_ACCESSED = "last_accessed"


# ============================================================================
# REQUEST DTOs
# ============================================================================

@dataclass
class MemoryQueryRequest:
    """
    Request for querying memories.

    Supports filtering by phase, importance, strength, and vector similarity.
    """
    # Query (optional - can query all memories)
    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None

    # Filters
    memory_phase: Optional[MemoryPhaseDTO] = None
    min_importance: Optional[float] = None
    max_importance: Optional[float] = None
    min_strength: Optional[float] = None
    max_strength: Optional[float] = None

    # Vector search (if query_embedding provided)
    similarity_threshold: float = 0.7
    top_k: int = 10

    # Pagination
    limit: int = 50
    offset: int = 0

    # Sorting
    sort_by: MemorySortBy = MemorySortBy.CREATED_AT
    ascending: bool = False  # Default: newest/highest first


@dataclass
class MemoryCreateRequest:
    """
    Request for creating a new memory.

    Used at application boundary to create memories from external input.
    """
    # Required
    content: str
    importance: float

    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_phase: MemoryPhaseDTO = MemoryPhaseDTO.EPISODIC
    embedding: Optional[List[float]] = None
    source_event_id: Optional[UUID] = None
    token_count: Optional[int] = None


# ============================================================================
# RESPONSE DTOs
# ============================================================================

@dataclass
class MemoryResult:
    """
    Single memory result from query.

    Represents one memory with all relevant metadata and scores.
    """
    # Identity
    memory_id: UUID

    # Content
    content: str

    # Metadata
    importance: float
    memory_phase: MemoryPhaseDTO
    memory_strength: float
    half_life_days: float
    access_count: int
    token_count: int

    # Timestamps
    created_at: datetime
    last_accessed: Optional[datetime] = None
    last_decayed: Optional[datetime] = None

    # Optional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    promoted_from: Optional[MemoryPhaseDTO] = None
    source_event_id: Optional[UUID] = None

    # Similarity score (if from vector search)
    similarity_score: Optional[float] = None

    def is_strong(self) -> bool:
        """Check if memory is strong (>= 0.7)."""
        return self.memory_strength >= 0.7

    def is_important(self) -> bool:
        """Check if memory is important (>= 0.7)."""
        return self.importance >= 0.7

    def is_forgotten(self) -> bool:
        """Check if memory is forgotten."""
        return self.memory_phase == MemoryPhaseDTO.FORGOTTEN


@dataclass
class MemoryQueryResponse:
    """
    Response from memory query.

    Contains list of memories and metadata about the query.
    """
    # Results
    memories: List[MemoryResult]

    # Metadata
    total_found: int
    query_text: Optional[str] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)

    # Timing
    query_timestamp: datetime = field(default_factory=datetime.now)

    # Statistics (optional)
    avg_importance: Optional[float] = None
    avg_strength: Optional[float] = None
    phase_distribution: Dict[str, int] = field(default_factory=dict)

    def get_strong_memories(self) -> List[MemoryResult]:
        """Get only strong memories (strength >= 0.7)."""
        return [m for m in self.memories if m.is_strong()]

    def get_important_memories(self) -> List[MemoryResult]:
        """Get only important memories (importance >= 0.7)."""
        return [m for m in self.memories if m.is_important()]


@dataclass
class MemoryStatsResponse:
    """
    Statistics about Angela's memories.

    Used for dashboards, monitoring, and analytics.
    """
    # Counts by phase
    phase_counts: Dict[str, int]

    # Overall stats
    total_memories: int
    strong_memories: int  # strength >= 0.7
    weak_memories: int    # strength < 0.3
    forgotten_memories: int

    # Averages
    avg_importance: float
    avg_strength: float
    avg_access_count: float

    # Recent activity
    memories_created_today: int
    memories_accessed_today: int

    # Top memories
    most_important: List[MemoryResult] = field(default_factory=list)
    most_accessed: List[MemoryResult] = field(default_factory=list)
    recently_created: List[MemoryResult] = field(default_factory=list)

    # Timestamp
    generated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# CONVERSION HELPERS
# ============================================================================

def memory_entity_to_result(memory: Any) -> MemoryResult:
    """
    Convert Memory entity to MemoryResult DTO.

    Args:
        memory: Memory entity from domain layer

    Returns:
        MemoryResult DTO for application layer
    """
    return MemoryResult(
        memory_id=memory.id,
        content=memory.content,
        importance=memory.importance,
        memory_phase=MemoryPhaseDTO(memory.memory_phase.value),
        memory_strength=memory.memory_strength,
        half_life_days=memory.half_life_days,
        access_count=memory.access_count,
        token_count=memory.token_count,
        created_at=memory.created_at,
        last_accessed=memory.last_accessed,
        last_decayed=memory.last_decayed,
        metadata=memory.metadata,
        promoted_from=MemoryPhaseDTO(memory.promoted_from.value) if memory.promoted_from else None,
        source_event_id=memory.source_event_id,
        similarity_score=None  # Set separately if from vector search
    )


# ============================================================================
# SUMMARY
# ============================================================================

"""
Memory DTOs Summary:
====================

Request DTOs (2):
- MemoryQueryRequest: Query memories with filters and pagination
- MemoryCreateRequest: Create new memory from external input

Response DTOs (3):
- MemoryResult: Single memory with all metadata
- MemoryQueryResponse: Multiple memories with query metadata
- MemoryStatsResponse: Statistics and analytics

Enums (2):
- MemoryPhaseDTO: Memory consolidation phases
- MemorySortBy: Sort options for queries

Helpers (1):
- memory_entity_to_result(): Convert entity to DTO

Total: ~240 lines

Design Principles:
✅ Clean separation between layers
✅ Rich metadata for monitoring
✅ Filtering and pagination support
✅ Statistics for dashboards
✅ Type safety with enums
✅ Helper methods for common queries
✅ Conversion helpers for entity mapping
"""
