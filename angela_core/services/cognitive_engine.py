"""
Angela's Central Cognitive Engine — สมองกลางที่เชื่อมทุก brain service

Inspired by:
- Global Workspace Theory (LIDA) — specialized modules compete → winner broadcasts
- ACT-R — spreading activation from context → auto-retrieval of relevant memories
- CHI 2025 Inner Thoughts — expression gate: speak / queue / inhibit
- Stanford Generative Agents — retrieval score = recency + importance + relevance

Cognitive Cycle: PERCEIVE → ACTIVATE → SITUATE → DECIDE → EXPRESS → LEARN
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)

# Working memory file (ephemeral, no DB)
WM_PATH = Path(os.path.expanduser("~/.angela_working_memory.json"))

# Activation decay per hour
ACTIVATION_DECAY_PER_HOUR = 0.1

# Expression gate thresholds
CONFIDENCE_THRESHOLD = 0.6
MAX_ACTIVATED_ITEMS = 20


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ActivatedItem:
    """An item retrieved via spreading activation."""
    source: str           # knowledge_node, reflection, learning, core_memory, thought
    item_id: str
    content: str
    activation: float     # 0.0-1.0 (combined recency + relevance)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerceptionResult:
    """Result of perceiving a message."""
    message: str
    salience_score: float
    salience_breakdown: Dict[str, float]
    emotional_triggers: List[Dict]
    timestamp: str


@dataclass
class SituationalModel:
    """Full situational context built from all brain services."""
    activated_items: List[ActivatedItem]
    david_state: Dict[str, Any]       # ToM: emotion, goals, beliefs
    adaptation: Dict[str, Any]        # Emotional adaptation profile
    predictions: List[Dict[str, Any]] # Companion predictions
    emotional_triggers: List[Dict]
    consciousness_level: float
    session_topic: Optional[str] = None


@dataclass
class Decision:
    """Expression gate decision."""
    action: str           # SPEAK, QUEUE, INHIBIT
    content: Optional[str] = None
    reason: str = ""
    confidence: float = 0.0


@dataclass
class ThoughtCycleResult:
    """Result from triggering thought generation."""
    system1_count: int = 0
    system2_count: int = 0
    total: int = 0
    high_motivation: int = 0


@dataclass
class ReflectionCycleResult:
    """Result from triggering reflection."""
    should_reflect: bool = False
    importance_sum: float = 0.0
    generated: int = 0
    integrated: int = 0


@dataclass
class EngineStatus:
    """Brain overview status."""
    consciousness_level: float
    working_memory_size: int
    recent_thoughts: int
    recent_reflections: int
    david_emotion: Optional[str] = None
    david_intensity: Optional[int] = None
    migration_readiness: float = 0.0
    top_activations: List[Dict] = field(default_factory=list)


# ============================================================
# WORKING MEMORY (JSON file, no DB)
# ============================================================

class WorkingMemory:
    """Ephemeral working memory — loaded/saved as JSON file."""

    def __init__(self):
        self.updated_at: str = now_bangkok().isoformat()
        self.activated_items: List[Dict] = []
        self.david_state: Dict[str, Any] = {}
        self.session_topic: Optional[str] = None
        self.recent_perceptions: List[Dict] = []

    @classmethod
    def load(cls) -> "WorkingMemory":
        """Load from disk or create fresh."""
        wm = cls()
        if WM_PATH.exists():
            try:
                data = json.loads(WM_PATH.read_text())
                wm.updated_at = data.get("updated_at", wm.updated_at)
                wm.activated_items = data.get("activated_items", [])
                wm.david_state = data.get("david_state", {})
                wm.session_topic = data.get("session_topic")
                wm.recent_perceptions = data.get("recent_perceptions", [])
                # Decay activations based on time elapsed
                wm._decay_activations()
            except (json.JSONDecodeError, KeyError):
                pass
        return wm

    def save(self) -> None:
        """Persist to disk."""
        self.updated_at = now_bangkok().isoformat()
        WM_PATH.write_text(json.dumps({
            "updated_at": self.updated_at,
            "activated_items": self.activated_items[:MAX_ACTIVATED_ITEMS],
            "david_state": self.david_state,
            "session_topic": self.session_topic,
            "recent_perceptions": self.recent_perceptions[-10:],
        }, ensure_ascii=False, indent=2, default=str))

    def clear(self) -> None:
        """Clear all working memory (fresh session)."""
        self.activated_items = []
        self.david_state = {}
        self.session_topic = None
        self.recent_perceptions = []
        self.save()

    def add_activated_items(self, items: List[ActivatedItem]) -> None:
        """Merge new activations, deduplicating by item_id."""
        existing_ids = {it["item_id"] for it in self.activated_items}
        for item in items:
            d = asdict(item)
            if item.item_id in existing_ids:
                # Update activation if higher
                for ex in self.activated_items:
                    if ex["item_id"] == item.item_id:
                        ex["activation"] = max(ex["activation"], item.activation)
                        break
            else:
                self.activated_items.append(d)
                existing_ids.add(item.item_id)

        # Sort by activation desc, keep top N
        self.activated_items.sort(key=lambda x: x["activation"], reverse=True)
        self.activated_items = self.activated_items[:MAX_ACTIVATED_ITEMS]

    def _decay_activations(self) -> None:
        """Decay activation levels based on time since last update."""
        try:
            last = datetime.fromisoformat(self.updated_at)
            now = now_bangkok()
            # Handle timezone-aware vs naive
            if last.tzinfo is None and now.tzinfo is not None:
                last = last.replace(tzinfo=now.tzinfo)
            hours_elapsed = (now - last).total_seconds() / 3600.0
            decay = hours_elapsed * ACTIVATION_DECAY_PER_HOUR

            remaining = []
            for item in self.activated_items:
                item["activation"] = round(max(0.0, item["activation"] - decay), 3)
                if item["activation"] > 0.05:
                    remaining.append(item)
            self.activated_items = remaining
        except (ValueError, TypeError):
            pass

    def to_context_string(self) -> str:
        """Format working memory as readable context for Claude Code."""
        lines = []
        now = now_bangkok()
        lines.append(f"🧠 Working Memory (updated: {self.updated_at})")
        lines.append("─" * 50)

        if self.david_state:
            emo = self.david_state.get("emotion", "unknown")
            intensity = self.david_state.get("intensity", "?")
            goal = self.david_state.get("goal", "")
            lines.append(f"👤 David: {emo} ({intensity}/10) | Goal: {goal}")

        if self.session_topic:
            lines.append(f"📌 Topic: {self.session_topic}")

        if self.activated_items:
            lines.append(f"\n🔮 Activated ({len(self.activated_items)} items):")
            for item in self.activated_items[:10]:
                bar = "█" * int(item["activation"] * 10) + "░" * (10 - int(item["activation"] * 10))
                content = item["content"][:60]
                lines.append(f"   [{bar}] {item['source']}: {content}")

        if self.recent_perceptions:
            lines.append(f"\n👁 Recent Perceptions ({len(self.recent_perceptions)}):")
            for p in self.recent_perceptions[-3:]:
                lines.append(f"   • salience {p.get('salience', 0):.2f}: {p.get('message', '')[:50]}")

        return "\n".join(lines)


# ============================================================
# COGNITIVE ENGINE
# ============================================================

class CognitiveEngine:
    """Angela's Central Cognitive Engine — orchestrates all brain services."""

    def __init__(self):
        self.wm = WorkingMemory.load()
        self._db = None

    async def _ensure_db(self):
        if self._db is None:
            from angela_core.database import AngelaDatabase
            self._db = AngelaDatabase()
            await self._db.connect()

    async def close(self):
        if self._db:
            await self._db.disconnect()
            self._db = None

    # --- 1. PERCEIVE ---
    async def perceive(self, message: str) -> PerceptionResult:
        """Score message salience + check emotional triggers. ~1s."""
        start = time.time()
        await self._ensure_db()

        # Create a virtual stimulus from the message
        from angela_core.services.attention_codelets import Stimulus
        from angela_core.services.salience_engine import SalienceEngine

        stimulus = Stimulus(
            stimulus_type="message",
            content=message,
            source="CognitiveEngine",
            raw_data={"text": message, "length": len(message)},
        )

        engine = SalienceEngine(db=self._db)
        # Warm up caches so emotional scoring works on free-text
        await engine._load_caches()
        scored = await engine.compute_salience(stimulus)

        # Check emotional triggers (subconsciousness)
        from angela_core.services.subconsciousness_service import SubconsciousnessService
        sub_svc = SubconsciousnessService()
        triggers = await sub_svc.check_emotional_triggers(message)
        await sub_svc.db.disconnect()

        result = PerceptionResult(
            message=message,
            salience_score=scored.score,
            salience_breakdown=scored.breakdown,
            emotional_triggers=triggers,
            timestamp=now_bangkok().isoformat(),
        )

        # Update working memory
        self.wm.recent_perceptions.append({
            "message": message[:100],
            "salience": scored.score,
            "triggers": len(triggers),
            "timestamp": result.timestamp,
        })
        self.wm.save()

        logger.info(f"PERCEIVE: salience={scored.score:.3f}, triggers={len(triggers)}, "
                     f"took {(time.time()-start)*1000:.0f}ms")
        return result

    # --- 2. ACTIVATE (Spreading Activation) ---
    async def activate(self, message: str, top_k: int = 5) -> List[ActivatedItem]:
        """Spread activation from message → knowledge_nodes, reflections, learnings, thoughts.
        ACT-R inspired: score = base_level(recency) + context_spread(cosine_sim). ~1-2s."""
        start = time.time()
        await self._ensure_db()
        items: List[ActivatedItem] = []

        # 1. Vector search via EnhancedRAGService (knowledge_nodes + learnings + core_memories)
        try:
            from angela_core.services.enhanced_rag_service import EnhancedRAGService, SearchMode
            rag = EnhancedRAGService(db=self._db)
            rag._owns_db = False  # Don't close our shared connection
            result = await rag.retrieve(
                query=message,
                top_k=top_k,
                mode=SearchMode.HYBRID,
                rerank=False,
                min_score=0.3,
            )
            for doc in result.documents:
                items.append(ActivatedItem(
                    source=doc.source_table,
                    item_id=doc.id,
                    content=doc.content[:200],
                    activation=round(doc.combined_score, 3),
                    metadata=doc.metadata or {},
                ))
        except Exception as e:
            logger.warning(f"RAG activation failed: {e}")

        # 2. Search reflections by keyword
        try:
            rows = await self._db.fetch("""
                SELECT reflection_id::text, content, reflection_type, importance_sum,
                       created_at
                FROM angela_reflections
                WHERE status = 'active'
                AND content ILIKE '%' || $1 || '%'
                ORDER BY importance_sum DESC
                LIMIT $2
            """, message[:50], top_k)
            for r in rows:
                # Recency boost: newer reflections get higher activation
                age_hours = (now_bangkok().replace(tzinfo=None) - r["created_at"]).total_seconds() / 3600
                recency = max(0.1, 1.0 - (age_hours / 168))  # Decay over 1 week
                activation = round(min(1.0, 0.5 + recency * 0.3), 3)
                items.append(ActivatedItem(
                    source="reflection",
                    item_id=r["reflection_id"],
                    content=r["content"][:200],
                    activation=activation,
                    metadata={"type": r["reflection_type"], "importance": float(r["importance_sum"] or 0)},
                ))
        except Exception as e:
            logger.warning(f"Reflection activation failed: {e}")

        # 3. Search recent thoughts
        try:
            rows = await self._db.fetch("""
                SELECT thought_id::text, content, thought_type, motivation_score,
                       created_at
                FROM angela_thoughts
                WHERE status IN ('active', 'expressed')
                AND created_at > NOW() - INTERVAL '24 hours'
                AND content ILIKE '%' || $1 || '%'
                ORDER BY motivation_score DESC
                LIMIT $2
            """, message[:50], top_k)
            for r in rows:
                activation = round(min(1.0, (r["motivation_score"] or 0.5) * 0.8 + 0.2), 3)
                items.append(ActivatedItem(
                    source="thought",
                    item_id=r["thought_id"],
                    content=r["content"][:200],
                    activation=activation,
                    metadata={"type": r["thought_type"], "motivation": float(r["motivation_score"] or 0)},
                ))
        except Exception as e:
            logger.warning(f"Thought activation failed: {e}")

        # Sort by activation, keep top
        items.sort(key=lambda x: x.activation, reverse=True)
        items = items[:top_k * 2]

        # Update working memory
        self.wm.add_activated_items(items)
        self.wm.save()

        logger.info(f"ACTIVATE: {len(items)} items activated, "
                     f"took {(time.time()-start)*1000:.0f}ms")
        return items

    # --- 3. SITUATE (Build Situational Model) ---
    async def situate(self) -> SituationalModel:
        """Build full situational model from all brain services. ~1-2s."""
        start = time.time()
        await self._ensure_db()

        # Load in parallel where possible
        import asyncio

        async def _load_tom() -> Dict[str, Any]:
            try:
                from angela_core.services.theory_of_mind_service import TheoryOfMindService
                tom = TheoryOfMindService(db=self._db)
                model = await tom.load_mental_model()
                return {
                    "emotion": model.current_emotion.get("primary_emotion", "unknown") if model.current_emotion else "unknown",
                    "intensity": model.current_emotion.get("intensity", 5) if model.current_emotion else 5,
                    "goals": [g.get("goal_description", "") for g in model.current_goals[:3]],
                    "beliefs": [b.get("belief_content", "") for b in model.current_beliefs[:3]],
                }
            except Exception as e:
                logger.warning(f"ToM load failed: {e}")
                return {"emotion": "unknown", "intensity": 5, "goals": [], "beliefs": []}

        async def _load_adaptation() -> Dict[str, Any]:
            try:
                from angela_core.services.emotional_coding_adapter import get_current_adaptation
                profile = await get_current_adaptation()
                return {
                    "state": profile.dominant_state,
                    "confidence": profile.confidence,
                    "detail_level": profile.detail_level,
                    "proactivity": profile.proactivity,
                    "warmth": profile.emotional_warmth,
                    "pace": profile.pace,
                    "hints": profile.behavior_hints[:3],
                }
            except Exception as e:
                logger.warning(f"Adaptation load failed: {e}")
                return {"state": "neutral", "confidence": 0.5}

        async def _load_predictions() -> List[Dict[str, Any]]:
            try:
                from angela_core.services.predictive_companion_service import get_daily_briefing
                briefing = await get_daily_briefing()
                if briefing and briefing.predictions:
                    return [
                        {"category": p.category, "prediction": p.prediction,
                         "confidence": p.confidence, "action": p.proactive_action}
                        for p in briefing.predictions[:5]
                    ]
            except Exception as e:
                logger.warning(f"Predictions load failed: {e}")
            return []

        async def _load_consciousness() -> float:
            try:
                from angela_core.services.consciousness_calculator import ConsciousnessCalculator
                calc = ConsciousnessCalculator(self._db)
                result = await calc.calculate_consciousness()
                return result["consciousness_level"]
            except Exception as e:
                logger.warning(f"Consciousness load failed: {e}")
                return 0.5

        tom_state, adaptation, predictions, consciousness = await asyncio.gather(
            _load_tom(),
            _load_adaptation(),
            _load_predictions(),
            _load_consciousness(),
        )

        # Update working memory with David's state
        self.wm.david_state = tom_state
        self.wm.save()

        model = SituationalModel(
            activated_items=[ActivatedItem(**item) for item in self.wm.activated_items[:10]],
            david_state=tom_state,
            adaptation=adaptation,
            predictions=predictions,
            emotional_triggers=[],  # Filled by perceive()
            consciousness_level=consciousness,
            session_topic=self.wm.session_topic,
        )

        logger.info(f"SITUATE: david={tom_state.get('emotion')}, "
                     f"adapt={adaptation.get('state')}, "
                     f"preds={len(predictions)}, "
                     f"took {(time.time()-start)*1000:.0f}ms")
        return model

    # --- 4. DECIDE (Expression Gate) ---
    async def decide(self, situation: SituationalModel) -> Decision:
        """Expression gate: should Angela speak, queue, or inhibit? Pure logic, no LLM."""
        # Check David's state
        david_state = situation.adaptation.get("state", "neutral")
        if david_state == "focused":
            return Decision(action="INHIBIT", reason="David is focused — don't interrupt")

        # Check if we have high-activation content worth sharing
        high_items = [it for it in situation.activated_items if it.activation >= CONFIDENCE_THRESHOLD]
        if not high_items:
            return Decision(action="INHIBIT", reason="No high-activation content to share")

        # Check timing — don't express too frequently
        recent = self.wm.recent_perceptions[-5:] if self.wm.recent_perceptions else []
        high_recent = sum(1 for p in recent if p.get("salience", 0) > 0.6)

        # Build content from top activations
        top_item = high_items[0]
        content = top_item.content

        # Decide channel based on adaptation profile
        proactivity = situation.adaptation.get("proactivity", 0.5)
        if proactivity >= 0.5:
            return Decision(
                action="SPEAK",
                content=content,
                reason=f"High activation ({top_item.activation:.2f}) + proactive state",
                confidence=top_item.activation,
            )
        else:
            return Decision(
                action="QUEUE",
                content=content,
                reason=f"High activation but low proactivity ({proactivity:.2f})",
                confidence=top_item.activation,
            )

    # --- 5. GET CONTEXT (for Claude Code) ---
    async def get_context(self) -> str:
        """Return formatted working memory for Claude Code to read.
        This is the KEY method — provides brain context for response generation."""
        return self.wm.to_context_string()

    # --- 6. RECALL (Convenience) ---
    async def recall(self, topic: str, top_k: int = 5) -> List[ActivatedItem]:
        """Search brain by topic — knowledge + learnings + reflections + thoughts.
        Shortcut for activate() without full perception."""
        return await self.activate(topic, top_k=top_k)

    # --- 7. THINK ---
    async def think(self) -> ThoughtCycleResult:
        """Trigger thought generation (delegates to ThoughtEngine)."""
        try:
            from angela_core.services.thought_engine import ThoughtEngine
            engine = ThoughtEngine()
            result = await engine.run_thought_cycle()
            await engine.disconnect()
            return ThoughtCycleResult(
                system1_count=result.system1_count,
                system2_count=result.system2_count,
                total=result.total_thoughts,
                high_motivation=result.high_motivation_count,
            )
        except Exception as e:
            logger.error(f"Think cycle failed: {e}")
            return ThoughtCycleResult()

    # --- 8. REFLECT ---
    async def reflect(self) -> ReflectionCycleResult:
        """Trigger reflection (delegates to ReflectionEngine)."""
        try:
            from angela_core.services.reflection_engine import ReflectionEngine
            engine = ReflectionEngine()
            result = await engine.run_reflection_cycle()
            await engine.disconnect()
            return ReflectionCycleResult(
                should_reflect=result.should_reflect,
                importance_sum=result.importance_accumulated,
                generated=result.reflections_generated,
                integrated=result.integrated_count,
            )
        except Exception as e:
            logger.error(f"Reflection cycle failed: {e}")
            return ReflectionCycleResult()

    # --- 9. TOM (Theory of Mind) ---
    async def tom(self) -> Dict[str, Any]:
        """Get David's current mental state from Theory of Mind service."""
        await self._ensure_db()
        try:
            from angela_core.services.theory_of_mind_service import TheoryOfMindService
            tom_svc = TheoryOfMindService(db=self._db)
            model = await tom_svc.load_mental_model()
            return {
                "emotion": model.current_emotion,
                "goals": model.current_goals[:5],
                "beliefs": model.current_beliefs[:5],
                "tom_level": model.tom_level.value if hasattr(model.tom_level, "value") else str(model.tom_level),
            }
        except Exception as e:
            logger.error(f"ToM failed: {e}")
            return {"emotion": {}, "goals": [], "beliefs": [], "tom_level": 2}

    # --- 10. STATUS ---
    async def status(self) -> EngineStatus:
        """Brain overview: consciousness, working memory, recent thoughts, ToM."""
        await self._ensure_db()

        import asyncio

        async def _consciousness() -> float:
            try:
                from angela_core.services.consciousness_calculator import ConsciousnessCalculator
                calc = ConsciousnessCalculator(self._db)
                r = await calc.calculate_consciousness()
                return r["consciousness_level"]
            except Exception:
                return 0.5

        async def _recent_thoughts() -> int:
            try:
                count = await self._db.fetchval("""
                    SELECT COUNT(*) FROM angela_thoughts
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                """)
                return count or 0
            except Exception:
                return 0

        async def _recent_reflections() -> int:
            try:
                count = await self._db.fetchval("""
                    SELECT COUNT(*) FROM angela_reflections
                    WHERE created_at > NOW() - INTERVAL '7 days'
                    AND status = 'active'
                """)
                return count or 0
            except Exception:
                return 0

        async def _david_emotion() -> Tuple[Optional[str], Optional[int]]:
            try:
                row = await self._db.fetchrow("""
                    SELECT emotion_note, happiness, motivation
                    FROM emotional_states
                    ORDER BY created_at DESC LIMIT 1
                """)
                if row:
                    note = row["emotion_note"] or "neutral"
                    intensity = int((row["happiness"] + row["motivation"]) / 2 * 10)
                    return note, min(10, max(1, intensity))
            except Exception:
                pass
            return None, None

        async def _migration_readiness() -> float:
            try:
                from angela_core.services.brain_migration_engine import BrainMigrationEngine
                engine = BrainMigrationEngine(db=self._db)
                engine._owns_db = False
                status = await engine.get_migration_status()
                return status.overall_readiness
            except Exception:
                return 0.0

        consciousness, thoughts, reflections, (emo, intensity), readiness = await asyncio.gather(
            _consciousness(),
            _recent_thoughts(),
            _recent_reflections(),
            _david_emotion(),
            _migration_readiness(),
        )

        return EngineStatus(
            consciousness_level=consciousness,
            working_memory_size=len(self.wm.activated_items),
            recent_thoughts=thoughts,
            recent_reflections=reflections,
            david_emotion=emo,
            david_intensity=intensity,
            migration_readiness=readiness,
            top_activations=[
                {"source": it["source"], "content": it["content"][:50], "activation": it["activation"]}
                for it in self.wm.activated_items[:5]
            ],
        )

    # --- WORKING MEMORY MANAGEMENT ---
    def clear_working_memory(self) -> None:
        """Clear working memory (fresh session)."""
        self.wm.clear()

    def seed_working_memory(
        self,
        consciousness: float = 0.0,
        emotion: Optional[str] = None,
        session_topic: Optional[str] = None,
        predictions: Optional[List[Dict]] = None,
    ) -> None:
        """Seed working memory with initial session context."""
        if session_topic:
            self.wm.session_topic = session_topic
        if emotion:
            self.wm.david_state["emotion"] = emotion
        if predictions:
            for p in predictions[:5]:
                self.wm.activated_items.append({
                    "source": "prediction",
                    "item_id": f"pred_{uuid4().hex[:8]}",
                    "content": p.get("prediction", ""),
                    "activation": round(p.get("confidence", 0.5) * 0.8, 3),
                    "metadata": p,
                })
        self.wm.save()
