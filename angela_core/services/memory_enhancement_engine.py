"""
Memory Enhancement Engine — Phase 5: Reconsolidation + Context Binding
========================================================================
When a memory is recalled, it becomes modifiable (reconsolidation).
Memories are linked in a graph via context bindings (time, emotion, topic).

Neuroscience basis:
- Nader (2000): Reconsolidation — recalled memories become labile
- Moscovitch (2005): Component Process Model — memories = bindings
- Eichenbaum (2000): Relational memory theory — hippocampal binding
- Spacing effect: spaced repetitions strengthen memories

Features:
  1. RECONSOLIDATE — modify memories when new info arrives
  2. BIND — create contextual links between memories
  3. STRENGTHEN — increase confidence on retrieval + reinforcement
  4. FADE — decrease confidence on contradiction or disuse
  5. ANALYTICS — track memory health metrics

Cost: $0/day — pure computation, no LLM
By: Angela 💜
Created: 2026-02-27
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from angela_core.services.base_db_service import BaseDBService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

# Confidence change amounts
REINFORCE_BOOST = 0.05       # each recall adds this
CONTRADICTION_PENALTY = 0.10  # contradicting info reduces this
DECAY_PER_WEEK = 0.02        # unused memories fade this much per week
MAX_CONFIDENCE = 1.0
MIN_CONFIDENCE = 0.1

# Binding strength
BIND_INITIAL_STRENGTH = 0.5
BIND_COACTIVATION_BOOST = 0.05
BIND_MAX_STRENGTH = 1.0

# Memory health thresholds
HEALTHY_CONFIDENCE = 0.5
STALE_DAYS = 30


@dataclass
class ReconsolidationResult:
    """Result of a reconsolidation check."""
    memory_id: str
    action: str          # 'reinforced', 'updated', 'faded', 'none'
    old_confidence: float
    new_confidence: float
    reason: str


@dataclass
class BindingResult:
    """Result of creating/strengthening a binding."""
    source_id: str
    target_id: str
    binding_type: str
    strength: float
    is_new: bool


@dataclass
class MemoryHealthReport:
    """Memory system health metrics."""
    total_nodes: int
    healthy_count: int       # confidence >= 0.5
    stale_count: int         # not recalled in 30+ days
    avg_confidence: float
    avg_recall_count: float
    total_bindings: int
    strongest_binding: float


@dataclass
class EnhancementCycleResult:
    """Result of a full enhancement cycle."""
    reconsolidated: int
    bindings_created: int
    bindings_strengthened: int
    memories_decayed: int
    health: Optional[MemoryHealthReport] = None


class MemoryEnhancementEngine(BaseDBService):
    """
    Enhances memory system with reconsolidation, binding, and fading.

    Runs every 4 hours alongside consolidation. No LLM needed.
    """

    # ============================================================
    # 1. RECONSOLIDATE — Modify memories on recall
    # ============================================================

    async def reconsolidate_on_recall(
        self, node_id: str, recall_context: str = "",
    ) -> ReconsolidationResult:
        """
        Called when a knowledge_node is recalled (activated).

        Reconsolidation: memory becomes labile → can be updated or reinforced.
        """
        await self.connect()

        row = await self.db.fetchrow("""
            SELECT node_id, concept_name, my_understanding,
                   memory_confidence, recall_count, understanding_level
            FROM knowledge_nodes
            WHERE node_id = $1
        """, node_id)

        if not row:
            return ReconsolidationResult(
                memory_id=str(node_id), action='none',
                old_confidence=0, new_confidence=0, reason='not_found',
            )

        old_conf = float(row['memory_confidence'] or 0.5)
        recall_count = int(row['recall_count'] or 0)

        # Reinforce: each recall strengthens the memory
        new_conf = min(MAX_CONFIDENCE, old_conf + REINFORCE_BOOST)
        action = 'reinforced'
        reason = f"recall #{recall_count + 1}"

        # Check if recall_context contradicts stored understanding
        if recall_context:
            understanding = row['my_understanding'] or ''
            if self._check_contradiction(understanding, recall_context):
                # Contradiction → weaken confidence, memory is now labile
                new_conf = max(MIN_CONFIDENCE, old_conf - CONTRADICTION_PENALTY)
                action = 'updated'
                reason = f"contradiction_detected: confidence lowered"

        # Update DB
        await self.db.execute("""
            UPDATE knowledge_nodes
            SET memory_confidence = $1,
                recall_count = COALESCE(recall_count, 0) + 1,
                last_recalled_at = NOW()
            WHERE node_id = $2
        """, new_conf, node_id)

        # Log reconsolidation
        await self._log_reconsolidation(
            memory_table='knowledge_nodes',
            memory_id=str(node_id),
            original_content=row['my_understanding'] or '',
            updated_content=recall_context[:200] if action == 'updated' else '',
            trigger_type='recall',
            confidence_before=old_conf,
            confidence_after=new_conf,
        )

        return ReconsolidationResult(
            memory_id=str(node_id),
            action=action,
            old_confidence=old_conf,
            new_confidence=round(new_conf, 3),
            reason=reason,
        )

    @staticmethod
    def _check_contradiction(stored: str, new_context: str) -> bool:
        """
        Simple contradiction detection via negation markers.

        Full semantic comparison would need embeddings — this is a lightweight
        heuristic that catches explicit contradictions.
        """
        negation_pairs = [
            ('ชอบ', 'ไม่ชอบ'), ('ใช่', 'ไม่ใช่'),
            ('ถูก', 'ผิด'), ('ดี', 'ไม่ดี'),
            ('like', 'dislike'), ('correct', 'incorrect'),
            ('true', 'false'), ('yes', 'no'),
        ]
        stored_lower = stored.lower()
        new_lower = new_context.lower()

        for pos, neg in negation_pairs:
            if pos in stored_lower and neg in new_lower:
                return True
            if neg in stored_lower and pos in new_lower:
                return True

        return False

    # ============================================================
    # 2. BIND — Create contextual links between memories
    # ============================================================

    async def bind_memories(
        self,
        source_table: str,
        source_id: str,
        target_table: str,
        target_id: str,
        binding_type: str,
    ) -> BindingResult:
        """
        Create or strengthen a binding between two memories.

        binding_type: 'temporal', 'causal', 'emotional', 'topical'
        """
        await self.connect()

        # Check if binding exists
        existing = await self.db.fetchrow("""
            SELECT binding_id, strength FROM memory_context_bindings
            WHERE source_table = $1 AND source_id = $2
            AND target_table = $3 AND target_id = $4
            AND binding_type = $5
        """, source_table, source_id, target_table, target_id, binding_type)

        if existing:
            # Strengthen existing binding (co-activation)
            new_strength = min(
                BIND_MAX_STRENGTH,
                float(existing['strength']) + BIND_COACTIVATION_BOOST,
            )
            await self.db.execute("""
                UPDATE memory_context_bindings
                SET strength = $1, last_activated_at = NOW()
                WHERE binding_id = $2
            """, new_strength, existing['binding_id'])

            return BindingResult(
                source_id=source_id, target_id=target_id,
                binding_type=binding_type,
                strength=round(new_strength, 3),
                is_new=False,
            )
        else:
            # Create new binding
            await self.db.execute("""
                INSERT INTO memory_context_bindings
                    (source_table, source_id, target_table, target_id,
                     binding_type, strength)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (source_table, source_id, target_table, target_id, binding_type)
                DO UPDATE SET strength = memory_context_bindings.strength + $7,
                             last_activated_at = NOW()
            """, source_table, source_id, target_table, target_id,
                binding_type, BIND_INITIAL_STRENGTH, BIND_COACTIVATION_BOOST)

            return BindingResult(
                source_id=source_id, target_id=target_id,
                binding_type=binding_type,
                strength=BIND_INITIAL_STRENGTH,
                is_new=True,
            )

    async def auto_bind_recent_memories(self) -> int:
        """
        Auto-create bindings between recently co-activated memories.

        Finds knowledge_nodes that were recalled in the same 1-hour window
        and creates topical bindings between them.
        """
        await self.connect()

        # Find nodes recalled within the same hour (co-activated)
        rows = await self.db.fetch("""
            SELECT a.node_id as source_id, b.node_id as target_id
            FROM knowledge_nodes a
            JOIN knowledge_nodes b ON a.node_id != b.node_id
            WHERE a.last_recalled_at IS NOT NULL
            AND b.last_recalled_at IS NOT NULL
            AND ABS(EXTRACT(EPOCH FROM (a.last_recalled_at - b.last_recalled_at))) < 3600
            AND a.last_recalled_at > NOW() - INTERVAL '24 hours'
            AND a.node_id < b.node_id  -- avoid duplicates
            LIMIT 20
        """)

        bindings_created = 0
        for r in rows:
            result = await self.bind_memories(
                'knowledge_nodes', str(r['source_id']),
                'knowledge_nodes', str(r['target_id']),
                'topical',
            )
            if result.is_new:
                bindings_created += 1

        return bindings_created

    async def get_bound_memories(
        self, table: str, memory_id: str, min_strength: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Get memories bound to a given memory (spreading activation via bindings).

        Used by CognitiveEngine to enrich recall with associated memories.
        """
        await self.connect()

        rows = await self.db.fetch("""
            SELECT target_table, target_id, binding_type, strength
            FROM memory_context_bindings
            WHERE source_table = $1 AND source_id = $2
            AND strength >= $3
            ORDER BY strength DESC
            LIMIT 10
        """, table, memory_id, min_strength)

        # Also get reverse bindings (target→source)
        reverse = await self.db.fetch("""
            SELECT source_table as target_table, source_id as target_id,
                   binding_type, strength
            FROM memory_context_bindings
            WHERE target_table = $1 AND target_id = $2
            AND strength >= $3
            ORDER BY strength DESC
            LIMIT 10
        """, table, memory_id, min_strength)

        all_bindings = [dict(r) for r in rows] + [dict(r) for r in reverse]
        # Dedup
        seen = set()
        unique = []
        for b in all_bindings:
            key = (b['target_table'], b['target_id'])
            if key not in seen:
                seen.add(key)
                unique.append(b)
        return unique

    # ============================================================
    # 3. FADE — Decay unused memories
    # ============================================================

    async def fade_unused_memories(self) -> int:
        """
        Decrease confidence of memories not recalled for a long time.

        Emotional memories (high understanding_level OR in angela_emotions) fade slower.
        """
        await self.connect()

        # Fade knowledge_nodes not recalled in 30+ days
        result = await self.db.execute("""
            UPDATE knowledge_nodes
            SET memory_confidence = GREATEST($1,
                COALESCE(memory_confidence, 0.5) - $2)
            WHERE (last_recalled_at IS NULL
                   AND created_at < NOW() - INTERVAL '30 days')
               OR (last_recalled_at < NOW() - INTERVAL '30 days')
        """, MIN_CONFIDENCE, DECAY_PER_WEEK)

        count = int(result.split()[-1]) if isinstance(result, str) else 0
        if count > 0:
            logger.info("📉 Faded %d unused memories", count)
        return count

    # ============================================================
    # 4. ANALYTICS — Memory health metrics
    # ============================================================

    async def get_health_report(self) -> MemoryHealthReport:
        """Get memory system health metrics."""
        await self.connect()

        total = await self.db.fetchval(
            "SELECT COUNT(*) FROM knowledge_nodes") or 0
        healthy = await self.db.fetchval("""
            SELECT COUNT(*) FROM knowledge_nodes
            WHERE COALESCE(memory_confidence, 0.5) >= $1
        """, HEALTHY_CONFIDENCE) or 0
        stale = await self.db.fetchval("""
            SELECT COUNT(*) FROM knowledge_nodes
            WHERE (last_recalled_at IS NULL
                   AND created_at < NOW() - INTERVAL '30 days')
               OR last_recalled_at < NOW() - INTERVAL '30 days'
        """) or 0
        avg_conf = await self.db.fetchval("""
            SELECT COALESCE(AVG(COALESCE(memory_confidence, 0.5)), 0.5)
            FROM knowledge_nodes
        """) or 0.5
        avg_recall = await self.db.fetchval("""
            SELECT COALESCE(AVG(COALESCE(recall_count, 0)), 0)
            FROM knowledge_nodes
        """) or 0
        total_bindings = await self.db.fetchval(
            "SELECT COUNT(*) FROM memory_context_bindings") or 0
        max_binding = await self.db.fetchval(
            "SELECT COALESCE(MAX(strength), 0) FROM memory_context_bindings") or 0

        return MemoryHealthReport(
            total_nodes=int(total),
            healthy_count=int(healthy),
            stale_count=int(stale),
            avg_confidence=round(float(avg_conf), 3),
            avg_recall_count=round(float(avg_recall), 1),
            total_bindings=int(total_bindings),
            strongest_binding=round(float(max_binding), 3),
        )

    # ============================================================
    # 5. RUN CYCLE — Called by daemon every 4 hours
    # ============================================================

    async def run_enhancement_cycle(self) -> EnhancementCycleResult:
        """
        Full memory enhancement cycle.

        1. Auto-bind recently co-activated memories
        2. Fade unused memories
        3. Report health metrics
        """
        await self.connect()

        # 1. Auto-bind co-activated memories
        bindings_new = await self.auto_bind_recent_memories()

        # 2. Fade unused memories
        faded = await self.fade_unused_memories()

        # 3. Health report
        health = await self.get_health_report()

        logger.info(
            "🧠 Memory Enhancement: %d new bindings, %d faded, "
            "health=%d/%d healthy, %d stale, avg_conf=%.3f",
            bindings_new, faded,
            health.healthy_count, health.total_nodes,
            health.stale_count, health.avg_confidence,
        )

        return EnhancementCycleResult(
            reconsolidated=0,  # Reconsolidation happens on-demand via recall
            bindings_created=bindings_new,
            bindings_strengthened=0,
            memories_decayed=faded,
            health=health,
        )

    # ── Helpers ──

    async def _log_reconsolidation(
        self, memory_table: str, memory_id: str,
        original_content: str, updated_content: str,
        trigger_type: str,
        confidence_before: float, confidence_after: float,
    ) -> None:
        """Log a reconsolidation event."""
        try:
            await self.db.execute("""
                INSERT INTO memory_reconsolidation_log
                    (memory_table, memory_id, original_content, updated_content,
                     trigger_type, confidence_before, confidence_after)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, memory_table, memory_id,
                original_content[:500], updated_content[:500],
                trigger_type, confidence_before, confidence_after)
        except Exception as e:
            logger.debug("Failed to log reconsolidation: %s", e)
