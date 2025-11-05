"""
Consolidate Memory Use Case

Business workflow for consolidating memories to next phase.
This use case orchestrates:
- Finding memories ready for consolidation
- Applying memory consolidation through phases
- Updating memory strength and half-life
- Persisting consolidated memories
- Publishing domain events

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from angela_core.application.use_cases.base_use_case import BaseUseCase, UseCaseResult
from angela_core.domain.entities.memory import Memory, MemoryPhase
from angela_core.domain.events import (
    MemoryConsolidated,
    MemoryStrengthened,
    MemoryDecayed,
    MemoryForgotten
)
from angela_core.domain.interfaces.repositories import IMemoryRepository


# ============================================================================
# INPUT/OUTPUT MODELS
# ============================================================================

@dataclass
class ConsolidateMemoryInput:
    """
    Input for consolidating memories.

    Attributes:
        memory_id: Specific memory to consolidate (optional)
        batch_consolidate: If True, consolidate all ready memories
        max_batch_size: Maximum memories to consolidate in batch
        apply_decay: Whether to apply decay before consolidation
        min_strength: Minimum strength threshold (skip if below)
    """
    memory_id: Optional[UUID] = None
    batch_consolidate: bool = False
    max_batch_size: int = 100
    apply_decay: bool = True
    min_strength: float = 0.1


@dataclass
class ConsolidateMemoryOutput:
    """
    Output after memory consolidation.

    Attributes:
        consolidated_count: Number of memories consolidated
        decayed_count: Number of memories decayed
        forgotten_count: Number of memories forgotten
        strengthened_count: Number of memories strengthened
        consolidated_memories: List of consolidated memory IDs
        events_published: Number of domain events published
    """
    consolidated_count: int = 0
    decayed_count: int = 0
    forgotten_count: int = 0
    strengthened_count: int = 0
    consolidated_memories: List[UUID] = None
    events_published: int = 0

    def __post_init__(self):
        if self.consolidated_memories is None:
            self.consolidated_memories = []


# ============================================================================
# USE CASE IMPLEMENTATION
# ============================================================================

class ConsolidateMemoryUseCase(BaseUseCase[ConsolidateMemoryInput, ConsolidateMemoryOutput]):
    """
    Use case for consolidating memories through consolidation phases.

    This use case handles the complete workflow of:
    1. Validating input
    2. Finding memories ready for consolidation
    3. Applying decay if requested
    4. Consolidating memories to next phase
    5. Persisting updated memories
    6. Publishing domain events

    Memory consolidation follows neuroscience-inspired phases:
    EPISODIC → COMPRESSED_1 → COMPRESSED_2 → SEMANTIC → PATTERN → INTUITIVE

    Dependencies:
        - IMemoryRepository: For persisting and querying memories

    Example:
        >>> # Consolidate single memory
        >>> input_data = ConsolidateMemoryInput(memory_id=some_uuid)
        >>> result = await use_case.execute(input_data)
        >>>
        >>> # Batch consolidate all ready memories
        >>> input_data = ConsolidateMemoryInput(
        ...     batch_consolidate=True,
        ...     max_batch_size=50
        ... )
        >>> result = await use_case.execute(input_data)
    """

    def __init__(self, memory_repo: IMemoryRepository):
        """
        Initialize use case with dependencies.

        Args:
            memory_repo: Repository for memory persistence
        """
        super().__init__()
        self.memory_repo = memory_repo

    # ========================================================================
    # VALIDATION
    # ========================================================================

    async def _validate(self, input_data: ConsolidateMemoryInput) -> List[str]:
        """
        Validate input before consolidating memories.

        Args:
            input_data: Input to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Must specify either memory_id or batch_consolidate
        if not input_data.memory_id and not input_data.batch_consolidate:
            errors.append("Must specify either memory_id or batch_consolidate=True")

        # Cannot specify both
        if input_data.memory_id and input_data.batch_consolidate:
            errors.append("Cannot specify both memory_id and batch_consolidate")

        # Batch size must be positive
        if input_data.max_batch_size <= 0:
            errors.append(f"max_batch_size must be positive, got {input_data.max_batch_size}")

        # Min strength must be 0.0-1.0
        if not (0.0 <= input_data.min_strength <= 1.0):
            errors.append(f"min_strength must be 0.0-1.0, got {input_data.min_strength}")

        return errors

    # ========================================================================
    # MAIN BUSINESS LOGIC
    # ========================================================================

    async def _execute_impl(self, input_data: ConsolidateMemoryInput) -> ConsolidateMemoryOutput:
        """
        Execute the memory consolidation workflow.

        Steps:
        1. Get memories to consolidate (single or batch)
        2. For each memory:
           a. Apply decay if requested
           b. Check if strength above threshold
           c. Consolidate to next phase
           d. Persist updated memory
           e. Publish domain event
        3. Return summary statistics

        Args:
            input_data: Validated input

        Returns:
            ConsolidateMemoryOutput with consolidation statistics

        Raises:
            RepositoryError: If database persistence fails
        """
        output = ConsolidateMemoryOutput()

        # Step 1: Get memories to consolidate
        memories = await self._get_memories_to_consolidate(input_data)

        if not memories:
            self.logger.info("No memories found to consolidate")
            return output

        self.logger.info(f"Processing {len(memories)} memories for consolidation")

        # Step 2: Process each memory
        for memory in memories:
            try:
                # Apply decay if requested
                if input_data.apply_decay:
                    memory = memory.apply_decay()
                    output.decayed_count += 1

                # Check if memory is forgotten
                if memory.memory_phase == MemoryPhase.FORGOTTEN:
                    await self._handle_forgotten_memory(memory)
                    output.forgotten_count += 1
                    continue

                # Check if strength above threshold
                if memory.memory_strength < input_data.min_strength:
                    self.logger.debug(
                        f"Skipping memory {memory.id}: strength {memory.memory_strength:.2f} "
                        f"below threshold {input_data.min_strength}"
                    )
                    continue

                # Consolidate to next phase
                consolidated = memory.consolidate_to_next_phase()

                if consolidated is None:
                    # Already at final phase
                    self.logger.debug(
                        f"Memory {memory.id} already at final phase: {memory.memory_phase.value}"
                    )
                    continue

                # Persist updated memory
                await self.memory_repo.update(consolidated.id, consolidated)
                output.consolidated_count += 1
                output.consolidated_memories.append(consolidated.id)

                # Publish domain event
                await self._publish_consolidation_event(memory, consolidated)
                output.events_published += 1

                self.logger.debug(
                    f"Consolidated memory {consolidated.id}: "
                    f"{memory.memory_phase.value} → {consolidated.memory_phase.value}"
                )

            except Exception as e:
                self.logger.error(f"Error processing memory {memory.id}: {e}")
                continue

        self.logger.info(
            f"✅ Consolidation complete: {output.consolidated_count} consolidated, "
            f"{output.decayed_count} decayed, {output.forgotten_count} forgotten"
        )

        return output

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_memories_to_consolidate(
        self,
        input_data: ConsolidateMemoryInput
    ) -> List[Memory]:
        """
        Get memories ready for consolidation.

        Args:
            input_data: Input specifying which memories to get

        Returns:
            List of Memory entities
        """
        if input_data.memory_id:
            # Single memory
            memory = await self.memory_repo.get_by_id(input_data.memory_id)
            return [memory] if memory else []

        else:
            # Batch: get all memories ready for consolidation
            memories = await self.memory_repo.get_ready_for_consolidation(
                limit=input_data.max_batch_size
            )
            return memories

    async def _handle_forgotten_memory(self, memory: Memory):
        """
        Handle memory that has been forgotten.

        Args:
            memory: Forgotten memory
        """
        # Update in database
        await self.memory_repo.update(memory.id, memory)

        # Publish forgotten event
        event = MemoryForgotten(
            entity_id=memory.id,
            final_strength=memory.memory_strength,
            days_since_created=(datetime.now() - memory.created_at).days,
            content_preview=memory.content[:100],
            timestamp=datetime.now()
        )

        self.logger.info(
            f"Memory forgotten: {memory.id} "
            f"(strength: {memory.memory_strength:.2f})"
        )

        # TODO: Integrate with event bus when ready

    async def _publish_consolidation_event(
        self,
        old_memory: Memory,
        new_memory: Memory
    ) -> bool:
        """
        Publish MemoryConsolidated domain event.

        Args:
            old_memory: Memory before consolidation
            new_memory: Memory after consolidation

        Returns:
            True if event published successfully
        """
        try:
            event = MemoryConsolidated(
                entity_id=new_memory.id,
                old_phase=old_memory.memory_phase.value,
                new_phase=new_memory.memory_phase.value,
                new_half_life_days=new_memory.half_life_days,
                timestamp=datetime.now()
            )

            # TODO: Integrate with event bus/publisher when ready
            # For now, just log the event
            self.logger.debug(
                f"Domain event created: MemoryConsolidated "
                f"({new_memory.id}, {old_memory.memory_phase.value} → {new_memory.memory_phase.value})"
            )

            return True

        except Exception as e:
            self.logger.warning(f"Failed to publish domain event: {e}")
            return False

    # ========================================================================
    # HOOKS
    # ========================================================================

    async def _before_execute(self, input_data: ConsolidateMemoryInput):
        """Log before execution starts."""
        if input_data.memory_id:
            self.logger.info(
                f"🧠 Consolidating single memory: {input_data.memory_id}"
            )
        else:
            self.logger.info(
                f"🧠 Batch consolidating memories "
                f"(max: {input_data.max_batch_size}, apply_decay: {input_data.apply_decay})"
            )

    async def _after_execute(
        self,
        input_data: ConsolidateMemoryInput,
        result: UseCaseResult[ConsolidateMemoryOutput]
    ):
        """Log after successful execution."""
        if result.success and result.data:
            self.logger.info(
                f"✅ Memory consolidation completed: "
                f"{result.data.consolidated_count} consolidated, "
                f"{result.data.decayed_count} decayed, "
                f"{result.data.forgotten_count} forgotten"
            )

    async def _on_success(
        self,
        input_data: ConsolidateMemoryInput,
        result: UseCaseResult[ConsolidateMemoryOutput]
    ):
        """Handle successful execution."""
        # Could trigger analytics, notifications, etc.
        pass

    async def _on_failure(
        self,
        input_data: ConsolidateMemoryInput,
        result: UseCaseResult
    ):
        """Handle failed execution."""
        self.logger.error(
            f"❌ Failed to consolidate memories: {result.error}"
        )
