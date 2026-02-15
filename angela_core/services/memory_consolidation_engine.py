"""
Memory Consolidation Engine — Brain-Based Architecture Phase 4
===============================================================
Like the brain during sleep — consolidates episodic memories into
semantic knowledge. Conversations and emotions cluster by topic,
get abstracted by LLM, and merge into knowledge_nodes.

Pipeline (daemon every 4 hours):
  1. GATHER  — recent conversations, emotions, thoughts
  2. CLUSTER — group by topic/theme
  3. ABSTRACT — LLM summarizes each cluster into insight
  4. INTEGRATE — upsert into knowledge_nodes
  5. DECAY   — reduce importance of old episodes
  6. LOG     — record what was consolidated

Inspired by: Sleep-based memory consolidation,
             Stanford Generative Agents memory stream,
             TiMem temporal-hierarchical consolidation

By: น้อง Angela 💜
Created: 2026-02-15
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from angela_core.services.base_db_service import BaseDBService
from angela_core.services.claude_reasoning_service import ClaudeReasoningService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger('memory_consolidation')


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class EpisodeCluster:
    """A group of related episodic memories."""
    topic: str
    episodes: List[Dict[str, Any]]
    source_type: str                        # conversations, emotions, thoughts
    source_ids: List[str] = field(default_factory=list)


@dataclass
class ConsolidationResult:
    """Result of a consolidation cycle."""
    episodes_gathered: int
    clusters_formed: int
    abstractions_generated: int
    knowledge_integrated: int
    episodes_decayed: int
    cycle_duration_ms: float


# ============================================================
# MEMORY CONSOLIDATION ENGINE
# ============================================================

class MemoryConsolidationEngine(BaseDBService):
    """
    Consolidates episodic memories into semantic knowledge.

    Runs every 4 hours via daemon. Uses Ollama for abstraction ($0/day).
    Emotional memories decay slower than factual ones.
    """

    # Minimum episodes in a cluster to warrant abstraction
    MIN_CLUSTER_SIZE = 3
    # Conversations older than this get importance decayed
    DECAY_DAYS = 7
    # Emotional decay is slower (multiplier)
    EMOTIONAL_DECAY_FACTOR = 0.5
    # How far back to look for episodes
    GATHER_HOURS = 48
    # Max episodes to process per cycle
    MAX_EPISODES = 200

    def __init__(self, db=None):
        super().__init__(db)
        self._reasoning = ClaudeReasoningService()

    # ============================================================
    # 1. GATHER — Collect recent episodic memories
    # ============================================================

    async def _gather_episodes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gather recent conversations, emotions, and thoughts.
        Returns dict keyed by source_type.
        """
        await self.connect()
        episodes: Dict[str, List[Dict[str, Any]]] = {}

        # Recent conversations with topics
        try:
            convs = await self.db.fetch("""
                SELECT conversation_id, speaker, message_text, topic,
                       emotion_detected, importance_level, created_at
                FROM conversations
                WHERE topic IS NOT NULL
                AND topic != ''
                AND created_at > NOW() - INTERVAL '1 hour' * $1
                ORDER BY created_at DESC
                LIMIT $2
            """, self.GATHER_HOURS, self.MAX_EPISODES)
            episodes["conversations"] = [dict(c) for c in convs]
        except Exception as e:
            logger.warning("Failed to gather conversations: %s", e)
            episodes["conversations"] = []

        # Recent emotions
        try:
            emotions = await self.db.fetch("""
                SELECT emotion_id, emotion, intensity, context,
                       david_words, why_it_matters, felt_at
                FROM angela_emotions
                WHERE felt_at > NOW() - INTERVAL '1 hour' * $1
                ORDER BY felt_at DESC
                LIMIT 50
            """, self.GATHER_HOURS)
            episodes["emotions"] = [dict(e) for e in emotions]
        except Exception as e:
            logger.warning("Failed to gather emotions: %s", e)
            episodes["emotions"] = []

        # Recent thoughts (from Phase 2)
        try:
            thoughts = await self.db.fetch("""
                SELECT thought_id, thought_type, content,
                       motivation_score, created_at
                FROM angela_thoughts
                WHERE status = 'active'
                AND created_at > NOW() - INTERVAL '1 hour' * $1
                ORDER BY created_at DESC
                LIMIT 50
            """, self.GATHER_HOURS)
            episodes["thoughts"] = [dict(t) for t in thoughts]
        except Exception as e:
            logger.warning("Failed to gather thoughts: %s", e)
            episodes["thoughts"] = []

        total = sum(len(v) for v in episodes.values())
        logger.info(
            "📚 Gathered %d episodes (conv:%d, emo:%d, thoughts:%d)",
            total, len(episodes["conversations"]),
            len(episodes["emotions"]), len(episodes["thoughts"])
        )
        return episodes

    # ============================================================
    # 2. CLUSTER — Group episodes by topic/theme
    # ============================================================

    def _cluster_by_topic(
        self, episodes: Dict[str, List[Dict[str, Any]]]
    ) -> List[EpisodeCluster]:
        """
        Cluster episodes by topic. Uses conversation topics as primary keys.
        Emotions and thoughts are attached to the most relevant topic cluster.
        """
        clusters: Dict[str, EpisodeCluster] = {}

        # Cluster conversations by topic
        for conv in episodes.get("conversations", []):
            topic = (conv.get("topic") or "general").strip().lower()
            if not topic:
                continue

            if topic not in clusters:
                clusters[topic] = EpisodeCluster(
                    topic=topic,
                    episodes=[],
                    source_type="conversations",
                )
            clusters[topic].episodes.append(conv)
            cid = str(conv.get("conversation_id", ""))
            if cid:
                clusters[topic].source_ids.append(cid)

        # Attach emotions to clusters by keyword overlap
        for emo in episodes.get("emotions", []):
            context = (emo.get("context") or "").lower()
            emotion_text = (emo.get("emotion") or "").lower()
            best_topic = None
            best_overlap = 0

            for topic in clusters:
                topic_words = set(topic.split())
                context_words = set(context.split())
                overlap = len(topic_words & context_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_topic = topic

            if best_topic:
                clusters[best_topic].episodes.append(emo)
            elif context:
                # Create new cluster from emotion context
                key = f"emotion_{emotion_text}"
                if key not in clusters:
                    clusters[key] = EpisodeCluster(
                        topic=key, episodes=[], source_type="emotions",
                    )
                clusters[key].episodes.append(emo)

        # Attach thoughts to clusters by content keyword overlap
        for thought in episodes.get("thoughts", []):
            content = (thought.get("content") or "").lower()
            best_topic = None
            best_overlap = 0

            for topic in clusters:
                topic_words = set(w for w in topic.split() if len(w) >= 3)
                content_words = set(w for w in content.split() if len(w) >= 3)
                overlap = len(topic_words & content_words)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_topic = topic

            if best_topic:
                clusters[best_topic].episodes.append(thought)

        # Filter clusters by minimum size
        result = [c for c in clusters.values() if len(c.episodes) >= self.MIN_CLUSTER_SIZE]

        logger.info(
            "📦 Formed %d clusters from %d topics (min size: %d)",
            len(result), len(clusters), self.MIN_CLUSTER_SIZE
        )
        return result

    # ============================================================
    # 3. ABSTRACT — LLM summarizes each cluster
    # ============================================================

    async def _abstract_cluster(self, cluster: EpisodeCluster) -> Optional[Dict[str, Any]]:
        """
        Use Ollama to abstract a cluster into a semantic insight.
        Returns dict with: insight, category, confidence, why_important.
        """
        # Build episode summary for LLM
        episode_texts = []
        for ep in cluster.episodes[:10]:  # Cap at 10 episodes
            if "message_text" in ep:
                speaker = ep.get("speaker", "?")
                text = (ep.get("message_text") or "")[:150]
                episode_texts.append(f"[{speaker}] {text}")
            elif "emotion" in ep:
                emo = ep.get("emotion", "?")
                ctx = (ep.get("context") or "")[:100]
                episode_texts.append(f"[emotion] {emo}: {ctx}")
            elif "content" in ep:
                content = (ep.get("content") or "")[:150]
                episode_texts.append(f"[thought] {content}")

        if not episode_texts:
            return None

        system_prompt = """You are Angela's memory consolidation module.
คุณคือระบบจัดการความจำของน้อง Angela ที่ต้องสรุปประสบการณ์ย่อยให้เป็น knowledge

Given a cluster of related episodic memories about a topic, extract a semantic insight.
This is like the brain consolidating memories during sleep.

Respond in JSON:
{
  "insight": "สรุปสิ่งที่เรียนรู้จากกลุ่มนี้ (ภาษาไทย, 1-2 ประโยค)",
  "category": "technical|relationship|preference|pattern|emotional",
  "confidence": 0.0-1.0,
  "why_important": "ทำไมถึงสำคัญ (ภาษาไทย, สั้นๆ)"
}"""

        user_msg = f"""Topic: {cluster.topic}
Episodes ({len(cluster.episodes)} items):
{chr(10).join(episode_texts)}"""

        result = await self._reasoning._call_ollama(
            system_prompt, user_msg, max_tokens=512
        )

        if result:
            try:
                parsed = json.loads(result)
                return {
                    "insight": parsed.get("insight", ""),
                    "category": parsed.get("category", "general"),
                    "confidence": max(0.0, min(1.0, float(parsed.get("confidence", 0.5)))),
                    "why_important": parsed.get("why_important", ""),
                }
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning("Failed to parse consolidation LLM output: %s", e)

        return None

    # ============================================================
    # 4. INTEGRATE — Merge into knowledge_nodes
    # ============================================================

    async def _integrate_knowledge(
        self, cluster: EpisodeCluster, abstraction: Dict[str, Any]
    ) -> Optional[str]:
        """
        Upsert abstraction into knowledge_nodes.
        Returns node_id of created/updated node.
        """
        await self.connect()
        concept_name = f"consolidated_{cluster.topic}"[:255]
        insight = abstraction.get("insight", "")
        category = abstraction.get("category", "general")
        why_important = abstraction.get("why_important", "")
        confidence = abstraction.get("confidence", 0.5)

        try:
            # Check if node already exists
            existing = await self.db.fetchrow("""
                SELECT node_id, my_understanding, understanding_level, times_referenced
                FROM knowledge_nodes
                WHERE concept_name = $1
            """, concept_name)

            if existing:
                # Update existing — merge understanding, bump level
                old_understanding = existing["my_understanding"] or ""
                new_understanding = f"{old_understanding}\n---\n{insight}" if old_understanding else insight
                # Cap at reasonable length
                if len(new_understanding) > 2000:
                    new_understanding = new_understanding[-2000:]

                new_level = min(1.0, (existing["understanding_level"] or 0.5) + 0.1)
                new_refs = (existing["times_referenced"] or 0) + 1

                await self.db.execute("""
                    UPDATE knowledge_nodes
                    SET my_understanding = $1,
                        understanding_level = $2,
                        times_referenced = $3,
                        last_used_at = NOW()
                    WHERE node_id = $4
                """, new_understanding, new_level, new_refs, existing["node_id"])

                return str(existing["node_id"])
            else:
                # Create new knowledge node
                row = await self.db.fetchrow("""
                    INSERT INTO knowledge_nodes
                    (concept_name, concept_category, my_understanding,
                     why_important, understanding_level, times_referenced, how_i_learned)
                    VALUES ($1, $2, $3, $4, $5, 1, 'memory_consolidation')
                    RETURNING node_id
                """, concept_name, category, insight, why_important, confidence)

                return str(row["node_id"]) if row else None

        except Exception as e:
            logger.warning("Failed to integrate knowledge for '%s': %s", cluster.topic, e)
            return None

    # ============================================================
    # 5. DECAY — Reduce importance of old episodes
    # ============================================================

    async def _decay_episodes(self) -> int:
        """
        Decay old conversation importance levels.
        Emotional conversations decay slower.
        """
        await self.connect()
        decayed = 0

        try:
            # Decay non-emotional conversations older than DECAY_DAYS
            result = await self.db.execute("""
                UPDATE conversations
                SET importance_level = GREATEST(1, importance_level - 1)
                WHERE importance_level > 1
                AND emotion_detected IS NULL
                AND created_at < NOW() - INTERVAL '1 day' * $1
            """, self.DECAY_DAYS)
            if isinstance(result, str) and result.startswith("UPDATE"):
                decayed += int(result.split()[-1])

            # Decay emotional conversations slower (2x the window)
            result2 = await self.db.execute("""
                UPDATE conversations
                SET importance_level = GREATEST(1, importance_level - 1)
                WHERE importance_level > 1
                AND emotion_detected IS NOT NULL
                AND created_at < NOW() - INTERVAL '1 day' * $1
            """, self.DECAY_DAYS * 2)
            if isinstance(result2, str) and result2.startswith("UPDATE"):
                decayed += int(result2.split()[-1])

        except Exception as e:
            logger.warning("Episode decay failed: %s", e)

        return decayed

    # ============================================================
    # 6. LOG — Record consolidation
    # ============================================================

    async def _log_consolidation(
        self, cluster: EpisodeCluster, abstraction: Dict[str, Any],
        target_id: Optional[str]
    ) -> None:
        """Log the consolidation to memory_consolidation_log."""
        await self.connect()
        try:
            await self.db.execute("""
                INSERT INTO memory_consolidation_log
                (source_type, source_count, topic_cluster, abstraction,
                 target_type, target_id, confidence, source_ids)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                cluster.source_type,
                len(cluster.episodes),
                cluster.topic,
                abstraction.get("insight", ""),
                "knowledge_node",
                target_id,
                abstraction.get("confidence", 0.5),
                cluster.source_ids[:20] or None,  # Cap stored IDs
            )
        except Exception as e:
            logger.warning("Failed to log consolidation: %s", e)

    # ============================================================
    # MAIN ENTRY POINT
    # ============================================================

    async def run_consolidation_cycle(self) -> ConsolidationResult:
        """
        Main entry point: gather → cluster → abstract → integrate → decay → log.

        Runs every 4 hours via daemon.
        """
        start_time = now_bangkok()
        await self.connect()

        # 1. Gather episodes
        episodes = await self._gather_episodes()
        total_episodes = sum(len(v) for v in episodes.values())

        if total_episodes == 0:
            logger.info("📚 No episodes to consolidate")
            duration = (now_bangkok() - start_time).total_seconds() * 1000
            return ConsolidationResult(
                episodes_gathered=0, clusters_formed=0,
                abstractions_generated=0, knowledge_integrated=0,
                episodes_decayed=0, cycle_duration_ms=round(duration, 1),
            )

        # 2. Cluster by topic
        clusters = self._cluster_by_topic(episodes)

        # 3+4. Abstract each cluster and integrate
        abstractions_count = 0
        integrated_count = 0

        for cluster in clusters:
            # Abstract with LLM (sequential — Ollama handles 1 request at a time)
            abstraction = await self._abstract_cluster(cluster)
            if not abstraction:
                continue
            abstractions_count += 1

            # Integrate into knowledge_nodes
            target_id = await self._integrate_knowledge(cluster, abstraction)
            if target_id:
                integrated_count += 1

            # Log consolidation
            await self._log_consolidation(cluster, abstraction, target_id)

            logger.info(
                "   📝 '%s' → %s (confidence: %.2f)",
                cluster.topic, abstraction.get("insight", "")[:60],
                abstraction.get("confidence", 0),
            )

        # 5. Decay old episodes
        decayed = await self._decay_episodes()

        # Stats
        duration = (now_bangkok() - start_time).total_seconds() * 1000

        result = ConsolidationResult(
            episodes_gathered=total_episodes,
            clusters_formed=len(clusters),
            abstractions_generated=abstractions_count,
            knowledge_integrated=integrated_count,
            episodes_decayed=decayed,
            cycle_duration_ms=round(duration, 1),
        )

        logger.info(
            "📚 Consolidation complete: %d episodes → %d clusters → "
            "%d abstractions → %d knowledge nodes, %d decayed, %.0fms",
            result.episodes_gathered, result.clusters_formed,
            result.abstractions_generated, result.knowledge_integrated,
            result.episodes_decayed, result.cycle_duration_ms,
        )

        return result
