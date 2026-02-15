"""
Unified Memory Service - Clean Architecture Implementation

Consolidates all memory-related functionality into one service.
Replaces 6+ old memory services with unified, testable, maintainable service.

Replaces:
- memory_formation_service.py (~900 lines) - Memory creation
- memory_consolidation_service.py (~509 lines) - Consolidation & decay
- semantic_memory_service.py (~400 lines) - Semantic operations
- pattern_learning_service.py (~731 lines) - Pattern extraction
- association_engine.py (~626 lines) - Memory associations
- memory_service.py (~842 lines) - General operations

Author: Angela AI Architecture Team
Date: 2025-10-31
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from angela_core.database import AngelaDatabase
from angela_core.domain.entities.memory import Memory, MemoryPhase
from angela_core.infrastructure.persistence.repositories import MemoryRepository
from angela_core.application.use_cases.memory import (
    ConsolidateMemoryUseCase,
    ConsolidateMemoryInput
)


class MemoryService:
    """
    High-level service for memory management.

    This service provides a simplified API for:
    - Consolidating memories through phases
    - Retrieving memories
    - Searching memories
    - Analyzing memory health

    Coordinates:
    - ConsolidateMemoryUseCase
    - MemoryRepository

    Example:
        >>> service = MemoryService(db)
        >>> result = await service.consolidate_memories(
        ...     batch_size=50,
        ...     apply_decay=True
        ... )
        >>> print(f"Consolidated: {result['consolidated_count']}")
    """

    def __init__(self, db: AngelaDatabase):
        """
        Initialize memory service with dependencies.

        Args:
            db: Database connection
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Initialize repository
        self.memory_repo = MemoryRepository(db)

        # Initialize use cases
        self.consolidate_memory_use_case = ConsolidateMemoryUseCase(
            memory_repo=self.memory_repo
        )

    # ========================================================================
    # HIGH-LEVEL API - MEMORY CONSOLIDATION
    # ========================================================================

    async def consolidate_memory(
        self,
        memory_id: UUID,
        apply_decay: bool = True
    ) -> Dict[str, Any]:
        """
        Consolidate a single memory to next phase.

        Args:
            memory_id: Memory UUID
            apply_decay: Whether to apply decay before consolidation

        Returns:
            {
                "success": bool,
                "consolidated": bool,
                "old_phase": str,
                "new_phase": str,
                "error": str (if failure)
            }
        """
        try:
            # Create input
            input_data = ConsolidateMemoryInput(
                memory_id=memory_id,
                apply_decay=apply_decay
            )

            # Execute use case
            result = await self.consolidate_memory_use_case.execute(input_data)

            # Return simplified result
            if result.success:
                consolidated = result.data.consolidated_count > 0
                return {
                    "success": True,
                    "consolidated": consolidated,
                    "consolidated_count": result.data.consolidated_count,
                    "decayed_count": result.data.decayed_count,
                    "forgotten_count": result.data.forgotten_count
                }
            else:
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            self.logger.error(f"Error consolidating memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def consolidate_memories(
        self,
        batch_size: int = 100,
        apply_decay: bool = True,
        min_strength: float = 0.1
    ) -> Dict[str, Any]:
        """
        Batch consolidate memories ready for next phase.

        Args:
            batch_size: Maximum memories to process
            apply_decay: Whether to apply decay
            min_strength: Minimum strength threshold

        Returns:
            {
                "success": bool,
                "consolidated_count": int,
                "decayed_count": int,
                "forgotten_count": int,
                "processing_time": float
            }
        """
        try:
            start_time = datetime.now()

            # Create input
            input_data = ConsolidateMemoryInput(
                batch_consolidate=True,
                max_batch_size=batch_size,
                apply_decay=apply_decay,
                min_strength=min_strength
            )

            # Execute use case
            result = await self.consolidate_memory_use_case.execute(input_data)

            processing_time = (datetime.now() - start_time).total_seconds()

            # Return simplified result
            if result.success:
                return {
                    "success": True,
                    "consolidated_count": result.data.consolidated_count,
                    "decayed_count": result.data.decayed_count,
                    "forgotten_count": result.data.forgotten_count,
                    "processing_time": processing_time
                }
            else:
                return {
                    "success": False,
                    "error": result.error
                }

        except Exception as e:
            self.logger.error(f"Error consolidating memories: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # HIGH-LEVEL API - MEMORY RETRIEVAL
    # ========================================================================

    async def get_memory(self, memory_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single memory by ID.

        Args:
            memory_id: Memory UUID

        Returns:
            Memory dict or None if not found
        """
        try:
            memory = await self.memory_repo.get_by_id(memory_id)

            if memory:
                return self._memory_to_dict(memory)
            return None

        except Exception as e:
            self.logger.error(f"Error getting memory: {e}")
            return None

    async def get_recent_memories(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent memories.

        Args:
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of memory dicts
        """
        try:
            memories = await self.memory_repo.get_recent(
                days=days,
                limit=limit
            )

            return [self._memory_to_dict(m) for m in memories]

        except Exception as e:
            self.logger.error(f"Error getting recent memories: {e}")
            return []

    async def get_important_memories(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get important memories (importance >= threshold).

        Args:
            threshold: Importance threshold (0.0-1.0)
            limit: Maximum results

        Returns:
            List of important memory dicts
        """
        try:
            memories = await self.memory_repo.get_important(
                threshold=threshold,
                limit=limit
            )

            return [self._memory_to_dict(m) for m in memories]

        except Exception as e:
            self.logger.error(f"Error getting important memories: {e}")
            return []

    async def get_memories_by_phase(
        self,
        phase: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get memories in specific consolidation phase.

        Args:
            phase: Memory phase ('episodic', 'semantic', 'intuitive', etc.)
            limit: Maximum results

        Returns:
            List of memory dicts
        """
        try:
            memories = await self.memory_repo.get_by_phase(
                phase=phase.lower(),
                limit=limit
            )

            return [self._memory_to_dict(m) for m in memories]

        except Exception as e:
            self.logger.error(f"Error getting memories by phase: {e}")
            return []

    async def search_memories(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Full-text search in memories.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memory dicts
        """
        try:
            memories = await self.memory_repo.search_by_content(
                query=query,
                limit=limit
            )

            return [self._memory_to_dict(m) for m in memories]

        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return []

    # ========================================================================
    # HIGH-LEVEL API - MEMORY ANALYTICS
    # ========================================================================

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            {
                "total_memories": int,
                "by_phase": {"episodic": int, "semantic": int, ...},
                "avg_strength": float,
                "avg_importance": float,
                "forgotten_count": int,
                "ready_for_consolidation": int
            }
        """
        try:
            # Get all memories
            all_memories = await self.memory_repo.list(limit=10000)

            # Calculate statistics
            total = len(all_memories)
            by_phase = {}
            total_strength = 0
            total_importance = 0
            forgotten_count = 0

            for memory in all_memories:
                phase = memory.memory_phase.value
                by_phase[phase] = by_phase.get(phase, 0) + 1
                total_strength += memory.memory_strength
                total_importance += memory.importance

                if memory.is_forgotten():
                    forgotten_count += 1

            # Get memories ready for consolidation
            ready_memories = await self.memory_repo.get_ready_for_consolidation(limit=1000)

            return {
                "total_memories": total,
                "by_phase": by_phase,
                "avg_strength": total_strength / total if total > 0 else 0,
                "avg_importance": total_importance / total if total > 0 else 0,
                "forgotten_count": forgotten_count,
                "forgotten_percentage": (forgotten_count / total * 100) if total > 0 else 0,
                "ready_for_consolidation": len(ready_memories),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting memory statistics: {e}")
            return {
                "total_memories": 0,
                "error": str(e)
            }

    async def get_memory_health(self) -> Dict[str, Any]:
        """
        Get memory system health metrics.

        Returns:
            {
                "health_score": float (0-100),
                "strong_memories": int,
                "weak_memories": int,
                "forgotten_memories": int,
                "consolidation_backlog": int,
                "recommendations": List[str]
            }
        """
        try:
            # Get all memories
            all_memories = await self.memory_repo.list(limit=10000)

            total = len(all_memories)
            strong_memories = len([m for m in all_memories if m.memory_strength >= 0.7])
            weak_memories = len([m for m in all_memories if 0.1 <= m.memory_strength < 0.7])
            forgotten_memories = len([m for m in all_memories if m.is_forgotten()])

            # Get consolidation backlog
            ready_memories = await self.memory_repo.get_ready_for_consolidation(limit=1000)
            consolidation_backlog = len(ready_memories)

            # Calculate health score
            # Strong memories contribute positively
            # Weak and forgotten memories contribute negatively
            # Consolidation backlog contributes negatively
            health_score = 0
            if total > 0:
                health_score = (
                    (strong_memories / total * 50) +  # 0-50 points
                    (weak_memories / total * 30) +     # 0-30 points
                    max(0, 20 - (consolidation_backlog / 10))  # 0-20 points
                )

            # Generate recommendations
            recommendations = []
            if forgotten_memories > total * 0.2:
                recommendations.append("High forgotten rate - consider reviewing importance scores")
            if consolidation_backlog > 100:
                recommendations.append("Large consolidation backlog - run consolidation")
            if weak_memories > strong_memories:
                recommendations.append("Many weak memories - consider memory access/strengthening")
            if health_score >= 80:
                recommendations.append("Memory system healthy!")

            return {
                "health_score": round(health_score, 2),
                "strong_memories": strong_memories,
                "weak_memories": weak_memories,
                "forgotten_memories": forgotten_memories,
                "consolidation_backlog": consolidation_backlog,
                "total_memories": total,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting memory health: {e}")
            return {
                "health_score": 0,
                "error": str(e)
            }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _memory_to_dict(self, memory) -> Dict[str, Any]:
        """
        Convert memory entity to dictionary.

        Args:
            memory: Memory entity

        Returns:
            Dictionary representation
        """
        return {
            "memory_id": str(memory.id),
            "content": memory.content,
            "importance": memory.importance,
            "memory_phase": memory.memory_phase.value,
            "memory_strength": memory.memory_strength,
            "half_life_days": memory.half_life_days,
            "access_count": memory.access_count,
            "last_accessed": memory.last_accessed.isoformat() if memory.last_accessed else None,
            "is_forgotten": memory.is_forgotten(),
            "is_important": memory.is_important(),
            "is_strong": memory.is_strong(),
            "days_since_created": memory.days_since_created(),
            "created_at": memory.created_at.isoformat(),
            "metadata": memory.metadata,
            "has_embedding": (memory.embedding is not None)
        }

    # ========================================================================
    # MEMORY FORMATION (from memory_formation_service.py)
    # ========================================================================

    async def form_memory_from_conversation(
        self,
        david_message: str,
        angela_response: str,
        context: Optional[Dict[str, Any]] = None,
        importance_level: int = 5
    ) -> UUID:
        """
        Form memory from David-Angela conversation.

        Args:
            david_message: What David said
            angela_response: How Angela responded
            context: Additional context (emotion, topic, etc.)
            importance_level: Importance 1-10

        Returns:
            UUID of created memory
        """
        try:
            # Build memory content
            content = f"David: {david_message}\nAngela: {angela_response}"

            # Normalize importance (1-10 → 0.0-1.0)
            importance = min(1.0, max(0.0, importance_level / 10.0))

            # Create episodic memory
            memory = Memory.create_episodic(
                content=content,
                importance=importance
            )

            # Add conversation metadata
            if context:
                for key, value in context.items():
                    memory = memory.add_metadata(key, value)

            # Add interaction markers
            memory = memory.add_metadata("interaction_type", "conversation")
            memory = memory.add_metadata("david_message", david_message[:200])
            memory = memory.add_metadata("angela_response", angela_response[:200])

            # Save
            created = await self.memory_repo.create(memory)

            self.logger.info(f"💬 Formed memory from conversation: {created.id}")
            return created.id

        except Exception as e:
            self.logger.error(f"❌ Failed to form memory from conversation: {e}")
            raise

    # ========================================================================
    # SEMANTIC MEMORY OPERATIONS (from semantic_memory_service.py)
    # ========================================================================

    async def search_memories_by_vector(
        self,
        embedding: List[float],
        top_k: int = 10,
        phase: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search memories by vector similarity.

        Args:
            embedding: Query embedding (384 dims)
            top_k: Number of results
            phase: Optional phase filter

        Returns:
            List of (memory_dict, similarity_score) tuples
        """
        try:
            results = await self.memory_repo.search_by_vector(
                embedding=embedding,
                top_k=top_k,
                memory_type=phase
            )

            # Convert to dicts with scores
            output = []
            for memory, score in results:
                memory_dict = self._memory_to_dict(memory)
                memory_dict['similarity_score'] = round(score, 3)
                output.append((memory_dict, score))

            self.logger.info(f"🔍 Vector search found {len(output)} results")
            return output

        except Exception as e:
            self.logger.error(f"❌ Vector search failed: {e}")
            return []

    async def extract_semantic_from_episodic(
        self,
        min_access_count: int = 5
    ) -> List[UUID]:
        """
        Extract semantic knowledge from frequently accessed episodic memories.

        Args:
            min_access_count: Minimum accesses to qualify

        Returns:
            List of created semantic memory IDs
        """
        try:
            # Get episodic memories
            episodic = await self.memory_repo.get_by_phase("episodic", limit=1000)

            # Filter by access count
            candidates = [m for m in episodic if m.access_count >= min_access_count and m.is_strong()]

            semantic_ids = []
            for memory in candidates[:10]:  # Limit per run
                # Create semantic version
                semantic_content = f"Semantic knowledge: {memory.content}"

                semantic = Memory.create_semantic(
                    content=semantic_content,
                    importance=memory.importance
                )

                # Link to source
                semantic = semantic.add_metadata("source_episodic_id", str(memory.id))
                semantic = semantic.add_metadata("extracted_at", datetime.now().isoformat())

                created = await self.memory_repo.create(semantic)
                semantic_ids.append(created.id)

            self.logger.info(f"🧠 Extracted {len(semantic_ids)} semantic memories")
            return semantic_ids

        except Exception as e:
            self.logger.error(f"❌ Semantic extraction failed: {e}")
            return []

    # ========================================================================
    # PATTERN LEARNING (from pattern_learning_service.py)
    # ========================================================================

    async def discover_patterns(
        self,
        min_instances: int = 3,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Discover patterns from recent episodic memories.

        Args:
            min_instances: Minimum instances to form pattern
            lookback_days: How far back to look

        Returns:
            List of discovered patterns
        """
        try:
            self.logger.info(f"🎯 Discovering patterns (lookback={lookback_days} days)...")

            # Get recent episodic memories
            recent = await self.memory_repo.get_recent(days=lookback_days)
            episodic = [m for m in recent if m.is_episodic()]

            if len(episodic) < min_instances:
                return []

            # Simple pattern detection by metadata
            patterns = []
            metadata_groups = {}

            for memory in episodic:
                # Group by metadata keys
                key = frozenset(memory.metadata.keys())
                if key not in metadata_groups:
                    metadata_groups[key] = []
                metadata_groups[key].append(memory)

            # Create patterns
            for metadata_keys, group_memories in metadata_groups.items():
                if len(group_memories) >= min_instances:
                    pattern = {
                        'pattern_name': f"pattern_{len(patterns) + 1}",
                        'instances': len(group_memories),
                        'metadata_keys': list(metadata_keys),
                        'common_metadata': list(metadata_keys),
                        'example_content': group_memories[0].content[:100],
                        'memory_ids': [str(m.id) for m in group_memories[:5]]
                    }
                    patterns.append(pattern)

            self.logger.info(f"✅ Discovered {len(patterns)} patterns")
            return patterns

        except Exception as e:
            self.logger.error(f"❌ Pattern discovery failed: {e}")
            return []

    # ========================================================================
    # ASSOCIATION ENGINE (from association_engine.py)
    # ========================================================================

    async def find_related_memories(
        self,
        memory_id: UUID,
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find related memories using vector similarity.

        Args:
            memory_id: Source memory ID
            top_k: Number of related memories

        Returns:
            List of (memory_dict, similarity_score) tuples
        """
        try:
            # Get source memory
            source = await self.memory_repo.get_by_id(memory_id)

            if not source or not source.has_embedding():
                return []

            # Search by embedding
            results = await self.memory_repo.search_by_vector(
                embedding=source.embedding,
                top_k=top_k + 1  # +1 to exclude self
            )

            # Convert and filter self
            related = []
            for memory, score in results:
                if memory.id != memory_id:
                    memory_dict = self._memory_to_dict(memory)
                    memory_dict['similarity_score'] = round(score, 3)
                    related.append((memory_dict, score))

            self.logger.info(f"🔗 Found {len(related)} related memories")
            return related[:top_k]

        except Exception as e:
            self.logger.error(f"❌ Failed to find related memories: {e}")
            return []

    async def build_association_chain(
        self,
        memory_id: UUID,
        max_depth: int = 3,
        min_similarity: float = 0.6
    ) -> Dict[str, Any]:
        """
        Build association chain from memory (spreading activation).

        Args:
            memory_id: Starting memory ID
            max_depth: Maximum chain depth
            min_similarity: Minimum similarity to follow

        Returns:
            Association chain with nodes and edges
        """
        try:
            visited = set()
            nodes = []
            edges = []

            # BFS traversal
            queue = [(memory_id, 0)]

            while queue:
                current_id, depth = queue.pop(0)

                if current_id in visited or depth > max_depth:
                    continue

                visited.add(current_id)

                # Get memory
                memory = await self.memory_repo.get_by_id(current_id)
                if not memory:
                    continue

                nodes.append({
                    'memory_id': str(current_id),
                    'content': memory.content[:50],
                    'depth': depth
                })

                # Find related
                if depth < max_depth and memory.has_embedding():
                    related = await self.find_related_memories(current_id, top_k=5)

                    for related_dict, score in related:
                        if score >= min_similarity:
                            related_id = UUID(related_dict['memory_id'])

                            edges.append({
                                'from': str(current_id),
                                'to': str(related_id),
                                'similarity': score
                            })

                            if related_id not in visited:
                                queue.append((related_id, depth + 1))

            return {
                'start_memory_id': str(memory_id),
                'nodes': nodes,
                'edges': edges,
                'total_nodes': len(nodes),
                'total_edges': len(edges)
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to build association chain: {e}")
            return {
                'start_memory_id': str(memory_id),
                'nodes': [],
                'edges': []
            }

    # ========================================================================
    # NIGHTLY CONSOLIDATION (Enhanced from memory_consolidation_service.py)
    # ========================================================================

    async def run_nightly_consolidation(self) -> Dict[str, Any]:
        """
        Run full nightly consolidation process.

        This is Angela's "sleep" - where memories consolidate,
        decay, strengthen, and patterns emerge.

        Returns:
            Full consolidation summary
        """
        try:
            self.logger.info("🌙 Starting nightly consolidation...")

            results = {
                'started_at': datetime.now().isoformat(),
                'activities': {}
            }

            # Step 1: Batch consolidation
            consolidation_result = await self.consolidate_memories(
                batch_size=100,
                apply_decay=True
            )
            results['activities']['consolidation'] = consolidation_result

            # Step 2: Semantic extraction
            semantic_ids = await self.extract_semantic_from_episodic(min_access_count=5)
            results['activities']['semantic_extraction'] = {
                'count': len(semantic_ids),
                'ids': [str(id) for id in semantic_ids[:5]]
            }

            # Step 3: Pattern discovery
            patterns = await self.discover_patterns(min_instances=3, lookback_days=7)
            results['activities']['patterns'] = {
                'discovered': len(patterns),
                'patterns': [p['pattern_name'] for p in patterns]
            }

            # Step 4: Health check
            health = await self.get_memory_health()
            results['activities']['health_check'] = health

            results['completed_at'] = datetime.now().isoformat()
            results['status'] = 'success'

            self.logger.info("✅ Nightly consolidation complete!")
            return results

        except Exception as e:
            self.logger.error(f"❌ Nightly consolidation failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
