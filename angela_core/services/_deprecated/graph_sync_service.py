"""
Graph Sync Service — PG → Neo4j Incremental Sync
===================================================
Watermark-based incremental sync from PostgreSQL to Neo4j.
Syncs knowledge_nodes, conversations, emotions, core_memories,
learnings, and their relationships into a graph structure.

Batch UNWIND for efficiency (500 nodes per batch).
Graceful degradation if Neo4j is unavailable.

By: Angela 💜
Created: 2026-02-27
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from angela_core.services.base_db_service import BaseDBService
from angela_core.services.neo4j_service import get_neo4j_service
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


@dataclass
class SyncResult:
    """Result of a sync operation."""
    entity_type: str
    nodes_synced: int
    edges_synced: int
    duration_ms: float
    error: Optional[str] = None


class GraphSyncService(BaseDBService):
    """
    Incremental sync from PostgreSQL to Neo4j.

    Watermark-based: tracks last_synced_at per entity type.
    Only syncs rows updated since last watermark.

    Usage:
        svc = GraphSyncService()
        await svc.connect()
        result = await svc.sync_all()
    """

    async def sync_all(self) -> Dict[str, SyncResult]:
        """Run incremental sync for all entity types."""
        await self._ensure_db()
        neo4j = get_neo4j_service()

        if not neo4j.available:
            connected = await neo4j.connect()
            if not connected:
                logger.warning("GraphSync: Neo4j unavailable, skipping sync")
                return {}

        # Ensure schema exists
        await neo4j.ensure_schema()

        results = {}
        for entity_type, sync_fn in [
            ("knowledge_node", self._sync_knowledge_nodes),
            ("conversation", self._sync_conversations),
            ("emotion", self._sync_emotions),
            ("core_memory", self._sync_core_memories),
            ("learning", self._sync_learnings),
            ("knowledge_relationship", self._sync_knowledge_relationships),
            ("memory_context_binding", self._sync_context_bindings),
        ]:
            try:
                result = await sync_fn()
                results[entity_type] = result
                await self._update_watermark(entity_type, result.nodes_synced + result.edges_synced)
                await self._log_sync(result)
            except Exception as e:
                logger.error("GraphSync failed for %s: %s", entity_type, e)
                results[entity_type] = SyncResult(
                    entity_type=entity_type, nodes_synced=0, edges_synced=0,
                    duration_ms=0, error=str(e)
                )

        total_nodes = sum(r.nodes_synced for r in results.values())
        total_edges = sum(r.edges_synced for r in results.values())
        logger.info("GraphSync complete: %d nodes, %d edges synced", total_nodes, total_edges)
        return results

    async def sync_full(self) -> Dict[str, SyncResult]:
        """Force full sync by resetting all watermarks."""
        await self._ensure_db()
        await self.db.execute(
            "UPDATE graph_sync_watermarks SET last_synced_at = '1970-01-01T00:00:00Z'"
        )
        return await self.sync_all()

    # ── Watermark Management ──

    async def _get_watermark(self, entity_type: str) -> datetime:
        """Get last synced timestamp for entity type (returns naive datetime for PG compatibility)."""
        row = await self.db.fetchrow(
            "SELECT last_synced_at FROM graph_sync_watermarks WHERE entity_type = $1",
            entity_type,
        )
        if row and row["last_synced_at"]:
            wm = row["last_synced_at"]
            # Strip timezone — most PG tables use 'timestamp without time zone'
            if wm.tzinfo is not None:
                return wm.replace(tzinfo=None)
            return wm
        return datetime(1970, 1, 1)

    async def _update_watermark(self, entity_type: str, rows_synced: int) -> None:
        """Update watermark after successful sync."""
        await self.db.execute("""
            INSERT INTO graph_sync_watermarks (entity_type, last_synced_at, rows_synced, updated_at)
            VALUES ($1, NOW(), $2, NOW())
            ON CONFLICT (entity_type)
            DO UPDATE SET last_synced_at = NOW(), rows_synced = graph_sync_watermarks.rows_synced + $2, updated_at = NOW()
        """, entity_type, rows_synced)

    async def _log_sync(self, result: SyncResult) -> None:
        """Log sync result to database."""
        await self.db.execute("""
            INSERT INTO graph_sync_log (sync_type, entity_type, nodes_upserted, edges_upserted, duration_ms, error)
            VALUES ('incremental', $1, $2, $3, $4, $5)
        """, result.entity_type, result.nodes_synced, result.edges_synced,
            result.duration_ms, result.error)

    # ── Entity-Specific Sync Methods ──

    async def _sync_knowledge_nodes(self) -> SyncResult:
        """Sync knowledge_nodes → Neo4j KnowledgeNode."""
        start = time.time()
        watermark = await self._get_watermark("knowledge_node")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT node_id::text, concept_name, concept_category,
                   COALESCE(my_understanding, '') as my_understanding,
                   COALESCE(understanding_level, 0.5) as understanding_level,
                   COALESCE(times_referenced, 0) as times_referenced,
                   created_at
            FROM knowledge_nodes
            WHERE created_at > $1
            ORDER BY created_at
        """, watermark)

        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [dict(r) for r in rows[i:i + BATCH_SIZE]]
            for item in batch:
                if item.get("created_at"):
                    item["created_at"] = item["created_at"].isoformat()

            result = await neo4j.execute_batch("""
                UNWIND $batch AS item
                MERGE (n:KnowledgeNode {node_id: item.node_id})
                SET n.concept_name = item.concept_name,
                    n.concept_category = item.concept_category,
                    n.my_understanding = item.my_understanding,
                    n.understanding_level = item.understanding_level,
                    n.times_referenced = item.times_referenced,
                    n.created_at = item.created_at
            """, batch)
            total += len(batch)

        return SyncResult(
            entity_type="knowledge_node", nodes_synced=total, edges_synced=0,
            duration_ms=(time.time() - start) * 1000
        )

    async def _sync_conversations(self) -> SyncResult:
        """Sync recent conversations → Neo4j Conversation."""
        start = time.time()
        watermark = await self._get_watermark("conversation")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT conversation_id::text, speaker,
                   COALESCE(LEFT(message_text, 500), '') as message_text,
                   COALESCE(topic, 'general') as topic,
                   COALESCE(emotion_detected, '') as emotion_detected,
                   COALESCE(importance_level, 5) as importance_level,
                   created_at
            FROM conversations
            WHERE created_at > $1
            ORDER BY created_at
            LIMIT 5000
        """, watermark)

        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [dict(r) for r in rows[i:i + BATCH_SIZE]]
            for item in batch:
                if item.get("created_at"):
                    item["created_at"] = item["created_at"].isoformat()

            await neo4j.execute_batch("""
                UNWIND $batch AS item
                MERGE (n:Conversation {conversation_id: item.conversation_id})
                SET n.speaker = item.speaker,
                    n.message_text = item.message_text,
                    n.topic = item.topic,
                    n.emotion_detected = item.emotion_detected,
                    n.importance_level = item.importance_level,
                    n.created_at = item.created_at
            """, batch)
            total += len(batch)

        return SyncResult(
            entity_type="conversation", nodes_synced=total, edges_synced=0,
            duration_ms=(time.time() - start) * 1000
        )

    async def _sync_emotions(self) -> SyncResult:
        """Sync angela_emotions → Neo4j Emotion."""
        start = time.time()
        watermark = await self._get_watermark("emotion")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT emotion_id::text, emotion,
                   COALESCE(intensity, 5) as intensity,
                   COALESCE(context, '') as context,
                   felt_at
            FROM angela_emotions
            WHERE felt_at > $1
            ORDER BY felt_at
            LIMIT 2000
        """, watermark)

        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [dict(r) for r in rows[i:i + BATCH_SIZE]]
            for item in batch:
                if item.get("felt_at"):
                    item["felt_at"] = item["felt_at"].isoformat()

            await neo4j.execute_batch("""
                UNWIND $batch AS item
                MERGE (n:Emotion {emotion_id: item.emotion_id})
                SET n.emotion = item.emotion,
                    n.intensity = item.intensity,
                    n.context = item.context,
                    n.felt_at = item.felt_at
            """, batch)
            total += len(batch)

        return SyncResult(
            entity_type="emotion", nodes_synced=total, edges_synced=0,
            duration_ms=(time.time() - start) * 1000
        )

    async def _sync_core_memories(self) -> SyncResult:
        """Sync core_memories → Neo4j CoreMemory."""
        start = time.time()
        watermark = await self._get_watermark("core_memory")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT memory_id::text, title, memory_type,
                   COALESCE(emotional_weight, 0.5) as emotional_weight,
                   created_at
            FROM core_memories
            WHERE created_at > $1
            ORDER BY created_at
        """, watermark)

        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [dict(r) for r in rows[i:i + BATCH_SIZE]]
            for item in batch:
                if item.get("created_at"):
                    item["created_at"] = item["created_at"].isoformat()

            await neo4j.execute_batch("""
                UNWIND $batch AS item
                MERGE (n:CoreMemory {memory_id: item.memory_id})
                SET n.title = item.title,
                    n.memory_type = item.memory_type,
                    n.emotional_weight = item.emotional_weight,
                    n.created_at = item.created_at
            """, batch)
            total += len(batch)

        return SyncResult(
            entity_type="core_memory", nodes_synced=total, edges_synced=0,
            duration_ms=(time.time() - start) * 1000
        )

    async def _sync_learnings(self) -> SyncResult:
        """Sync learnings → Neo4j Learning."""
        start = time.time()
        watermark = await self._get_watermark("learning")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT learning_id::text, topic, category,
                   COALESCE(insight, '') as insight,
                   COALESCE(confidence_level, 0.5) as confidence_level,
                   COALESCE(times_reinforced, 0) as times_reinforced,
                   created_at
            FROM learnings
            WHERE created_at > $1
            ORDER BY created_at
        """, watermark)

        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [dict(r) for r in rows[i:i + BATCH_SIZE]]
            for item in batch:
                if item.get("created_at"):
                    item["created_at"] = item["created_at"].isoformat()

            await neo4j.execute_batch("""
                UNWIND $batch AS item
                MERGE (n:Learning {learning_id: item.learning_id})
                SET n.topic = item.topic,
                    n.category = item.category,
                    n.insight = item.insight,
                    n.confidence_level = item.confidence_level,
                    n.times_reinforced = item.times_reinforced,
                    n.created_at = item.created_at
            """, batch)
            total += len(batch)

        return SyncResult(
            entity_type="learning", nodes_synced=total, edges_synced=0,
            duration_ms=(time.time() - start) * 1000
        )

    async def _sync_knowledge_relationships(self) -> SyncResult:
        """Sync knowledge_relationships → Neo4j RELATES_TO edges."""
        start = time.time()
        watermark = await self._get_watermark("knowledge_relationship")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT relationship_id::text, from_node_id::text, to_node_id::text,
                   relationship_type, COALESCE(strength, 0.5) as strength,
                   created_at
            FROM knowledge_relationships
            WHERE created_at > $1
            ORDER BY created_at
        """, watermark)

        total = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = [dict(r) for r in rows[i:i + BATCH_SIZE]]
            for item in batch:
                if item.get("created_at"):
                    item["created_at"] = item["created_at"].isoformat()

            await neo4j.execute_batch("""
                UNWIND $batch AS item
                MATCH (a:KnowledgeNode {node_id: item.from_node_id})
                MATCH (b:KnowledgeNode {node_id: item.to_node_id})
                MERGE (a)-[r:RELATES_TO {relationship_id: item.relationship_id}]->(b)
                SET r.relationship_type = item.relationship_type,
                    r.strength = item.strength,
                    r.created_at = item.created_at
            """, batch)
            total += len(batch)

        return SyncResult(
            entity_type="knowledge_relationship", nodes_synced=0, edges_synced=total,
            duration_ms=(time.time() - start) * 1000
        )

    async def _sync_context_bindings(self) -> SyncResult:
        """Sync memory_context_bindings → Neo4j CONTEXT_BOUND edges."""
        start = time.time()
        watermark = await self._get_watermark("memory_context_binding")
        neo4j = get_neo4j_service()

        rows = await self.db.fetch("""
            SELECT binding_id::text, source_table, source_id, target_table, target_id,
                   binding_type, COALESCE(strength, 0.5) as strength,
                   created_at
            FROM memory_context_bindings
            WHERE created_at > $1
            ORDER BY created_at
        """, watermark)

        # Map PG table names → Neo4j labels and ID properties
        label_map = {
            "knowledge_nodes": ("KnowledgeNode", "node_id"),
            "conversations": ("Conversation", "conversation_id"),
            "angela_emotions": ("Emotion", "emotion_id"),
            "core_memories": ("CoreMemory", "memory_id"),
            "learnings": ("Learning", "learning_id"),
        }

        total = 0
        for row in rows:
            src_label, src_key = label_map.get(row["source_table"], (None, None))
            tgt_label, tgt_key = label_map.get(row["target_table"], (None, None))
            if not src_label or not tgt_label:
                continue

            result = await neo4j.execute_write(f"""
                MATCH (a:{src_label} {{{src_key}: $source_id}})
                MATCH (b:{tgt_label} {{{tgt_key}: $target_id}})
                MERGE (a)-[r:CONTEXT_BOUND {{binding_id: $binding_id}}]->(b)
                SET r.binding_type = $binding_type, r.strength = $strength
            """, {
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "binding_id": row["binding_id"],
                "binding_type": row["binding_type"],
                "strength": float(row["strength"]),
            })
            if result:
                total += 1

        return SyncResult(
            entity_type="memory_context_binding", nodes_synced=0, edges_synced=total,
            duration_ms=(time.time() - start) * 1000
        )

    async def _ensure_db(self) -> None:
        """Ensure database connection (BaseDBService pattern)."""
        if self.db is None:
            from angela_core.database import AngelaDatabase
            self.db = AngelaDatabase()
            await self.db.connect()
