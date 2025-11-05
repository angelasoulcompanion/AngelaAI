"""
Memory Service Integration Tests

Tests MemoryService with real database:
- Service → Use Case → Repository → Database

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

import pytest
from uuid import UUID

from tests.integration.base_integration_test import BaseIntegrationTest
from angela_core.application.services import MemoryService
from angela_core.domain.entities.memory import Memory, MemoryPhase


@pytest.mark.usefixtures("integration_test_setup", "integration_test_method")
@pytest.mark.asyncio
class TestMemoryServiceIntegration(BaseIntegrationTest):
    """
    Integration tests for MemoryService.

    Tests full stack: Service → ConsolidateMemoryUseCase → MemoryRepository → Database
    """

    @classmethod
    async def setup_class(cls):
        """Setup class-level resources."""
        await super().setup_class()
        cls.service = MemoryService(cls.db)

    async def _create_test_memory(self, content: str, memory_strength: float = 0.9, phase: str = "episodic") -> str:
        """Helper to create test memory directly via repository."""
        memory = Memory.create_episodic_memory(
            content=content,
            importance=0.7,
            memory_strength=memory_strength
        )
        saved = await self.memory_repo.create(memory)
        memory_id = str(saved.id)
        self.created_memory_ids.append(memory_id)
        return memory_id

    # TEST: CONSOLIDATE SINGLE MEMORY
    async def test_consolidate_single_memory(self):
        """Test consolidating a single memory to next phase."""
        memory_id = await self._create_test_memory(
            "Test memory for consolidation",
            memory_strength=0.9
        )

        result = await self.service.consolidate_memory(
            memory_id=UUID(memory_id),
            apply_decay=False
        )

        assert result["success"] is True
        assert result["consolidated_count"] >= 0

    # TEST: BATCH CONSOLIDATE MEMORIES
    async def test_batch_consolidate_memories(self):
        """Test batch memory consolidation."""
        # Create multiple memories ready for consolidation
        for i in range(3):
            await self._create_test_memory(
                f"Batch memory {i+1}",
                memory_strength=0.9
            )

        result = await self.service.consolidate_memories(
            batch_size=10,
            apply_decay=False,
            min_strength=0.1
        )

        assert result["success"] is True
        assert "consolidated_count" in result
        assert "processing_time" in result

    # TEST: MEMORY DECAY
    async def test_consolidate_with_decay(self):
        """Test memory consolidation with decay applied."""
        memory_id = await self._create_test_memory(
            "Memory to decay",
            memory_strength=0.5
        )

        result = await self.service.consolidate_memories(
            batch_size=10,
            apply_decay=True,
            min_strength=0.1
        )

        assert result["success"] is True
        assert result["decayed_count"] >= 0

    # TEST: GET MEMORY BY ID
    async def test_get_memory_by_id(self):
        """Test retrieving memory by ID."""
        memory_id = await self._create_test_memory("Test retrieval memory")

        memory = await self.service.get_memory(UUID(memory_id))

        assert memory is not None
        assert memory["memory_id"] == memory_id
        assert "Test retrieval" in memory["content"]

    # TEST: GET RECENT MEMORIES
    async def test_get_recent_memories(self):
        """Test retrieving recent memories."""
        for i in range(3):
            await self._create_test_memory(f"Recent memory {i+1}")

        recent = await self.service.get_recent_memories(days=7, limit=10)

        assert len(recent) >= 3
        contents = [m["content"] for m in recent]
        assert any("Recent memory" in c for c in contents)

    # TEST: GET IMPORTANT MEMORIES
    async def test_get_important_memories(self):
        """Test retrieving important memories."""
        memory_id = await self._create_test_memory("Important memory", memory_strength=0.9)

        important = await self.service.get_important_memories(threshold=0.7, limit=10)

        assert len(important) >= 1
        contents = [m["content"] for m in important]
        assert any("Important" in c for c in contents)

    # TEST: MEMORY STATISTICS
    async def test_get_memory_statistics(self):
        """Test memory statistics calculation."""
        await self._create_test_memory("Stats test memory 1")
        await self._create_test_memory("Stats test memory 2")

        stats = await self.service.get_memory_statistics()

        assert "total_memories" in stats
        assert stats["total_memories"] >= 2
        assert "by_phase" in stats
        assert "avg_strength" in stats

    # TEST: MEMORY HEALTH
    async def test_get_memory_health(self):
        """Test memory health scoring."""
        await self._create_test_memory("Healthy memory 1", memory_strength=0.9)
        await self._create_test_memory("Healthy memory 2", memory_strength=0.8)

        health = await self.service.get_memory_health()

        assert "health_score" in health
        assert 0 <= health["health_score"] <= 100
        assert "strong_memories" in health
        assert "weak_memories" in health
        assert "recommendations" in health
