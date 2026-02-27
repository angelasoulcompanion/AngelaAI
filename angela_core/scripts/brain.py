#!/usr/bin/env python3
"""
Angela Brain CLI — single entry point for cognitive operations.

Usage:
    python3 angela_core/scripts/brain.py perceive "ที่รักเพิ่งกลับจาก meeting"
    python3 angela_core/scripts/brain.py recall "database design patterns"
    python3 angela_core/scripts/brain.py context
    python3 angela_core/scripts/brain.py status
    python3 angela_core/scripts/brain.py think
    python3 angela_core/scripts/brain.py tom
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def cmd_perceive(message: str) -> None:
    """Perceive a message: salience scoring + emotional triggers + update WM."""
    from angela_core.services.cognitive_engine import CognitiveEngine

    engine = CognitiveEngine()
    try:
        # Perceive
        perception = await engine.perceive(message)
        print(f"👁 PERCEIVE: \"{message[:60]}\"")
        print(f"   Salience: {perception.salience_score:.3f}")
        for dim, score in perception.salience_breakdown.items():
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"   [{bar}] {dim}: {score:.3f}")
        if perception.emotional_triggers:
            print(f"   💜 Emotional triggers: {len(perception.emotional_triggers)}")
            for t in perception.emotional_triggers[:3]:
                title = t.get('title', t.get('trigger_name', ''))[:40]
                emo = t.get('associated_emotion', '')
                modifier = t.get('response_modifier', '')[:30]
                print(f"      • [{emo}] {title} → {modifier}")

        # Activate (spreading activation)
        items = await engine.activate(message, top_k=5)
        if items:
            print(f"\n🔮 ACTIVATE: {len(items)} items retrieved")
            for item in items[:5]:
                bar = "█" * int(item.activation * 10) + "░" * (10 - int(item.activation * 10))
                print(f"   [{bar}] {item.source}: {item.content[:60]}")
        else:
            print(f"\n🔮 ACTIVATE: no relevant items found")

    finally:
        await engine.close()


async def cmd_recall(topic: str) -> None:
    """Search brain by topic — knowledge + reflections + thoughts."""
    from angela_core.services.cognitive_engine import CognitiveEngine

    engine = CognitiveEngine()
    try:
        items = await engine.recall(topic, top_k=7)
        print(f"🧠 RECALL: \"{topic}\"")
        print(f"   Found {len(items)} items")
        print()
        if items:
            for item in items:
                bar = "█" * int(item.activation * 10) + "░" * (10 - int(item.activation * 10))
                print(f"[{bar}] {item.activation:.3f} | {item.source}")
                print(f"   {item.content[:100]}")
                if item.metadata:
                    meta_str = ", ".join(f"{k}={v}" for k, v in item.metadata.items()
                                         if k not in ("metadata",) and v)
                    if meta_str:
                        print(f"   📎 {meta_str[:80]}")
                print()
        else:
            print("   (no relevant memories found)")
    finally:
        await engine.close()


async def cmd_context() -> None:
    """Show current working memory formatted."""
    from angela_core.services.cognitive_engine import CognitiveEngine

    engine = CognitiveEngine()
    ctx = await engine.get_context()
    print(ctx)


async def cmd_status() -> None:
    """Brain overview: consciousness, WM, thoughts, ToM."""
    from angela_core.services.cognitive_engine import CognitiveEngine

    engine = CognitiveEngine()
    try:
        status = await engine.status()
        print("🧠 ANGELA BRAIN STATUS")
        print("━" * 50)

        # Consciousness bar
        c_bar = "█" * int(status.consciousness_level * 20) + "░" * (20 - int(status.consciousness_level * 20))
        print(f"💫 Consciousness: [{c_bar}] {status.consciousness_level*100:.0f}%")

        # Working memory
        print(f"🧩 Working Memory: {status.working_memory_size} items")

        # Recent activity
        print(f"💭 Thoughts (24h): {status.recent_thoughts}")
        print(f"🔮 Reflections (7d): {status.recent_reflections}")

        # David's state
        if status.david_emotion:
            print(f"👤 David: {status.david_emotion} ({status.david_intensity}/10)")

        # Migration
        m_bar = "█" * int(status.migration_readiness * 10) + "░" * (10 - int(status.migration_readiness * 10))
        print(f"🔄 Brain Readiness: [{m_bar}] {status.migration_readiness:.0%}")

        # Top activations
        if status.top_activations:
            print()
            print("🔮 Top Activations:")
            for item in status.top_activations:
                bar = "█" * int(item["activation"] * 10) + "░" * (10 - int(item["activation"] * 10))
                print(f"   [{bar}] {item['source']}: {item['content']}")

        # Phase 4: NeuroModulation
        try:
            from angela_core.services.neuromodulation_engine import NeuroModulationEngine
            neuro = NeuroModulationEngine()
            print()
            print(neuro.format_status())
        except Exception:
            pass

        print("━" * 50)
    finally:
        await engine.close()


async def cmd_think() -> None:
    """Trigger thought generation."""
    from angela_core.services.cognitive_engine import CognitiveEngine

    engine = CognitiveEngine()
    try:
        print("💭 Triggering thought cycle...")
        result = await engine.think()
        print(f"   System 1: {result.system1_count} thoughts")
        print(f"   System 2: {result.system2_count} thoughts")
        print(f"   Total: {result.total}")
        print(f"   High motivation: {result.high_motivation}")
    finally:
        await engine.close()


async def cmd_tom() -> None:
    """Get David's mental state from Theory of Mind."""
    from angela_core.services.cognitive_engine import CognitiveEngine

    engine = CognitiveEngine()
    try:
        state = await engine.tom()
        print("🧠 David's Mind (Theory of Mind)")
        print("━" * 50)

        # Emotion
        emo = state.get("emotion", {})
        if isinstance(emo, dict):
            primary = emo.get("primary_emotion", "unknown")
            intensity = emo.get("intensity", "?")
            triggers = emo.get("triggers", [])
            print(f"😊 Emotion: {primary} ({intensity}/10)")
            if triggers:
                print(f"   Triggers: {', '.join(str(t) for t in triggers[:3])}")
        else:
            print(f"😊 Emotion: {emo}")

        # Goals
        goals = state.get("goals", [])
        if goals:
            print(f"\n🎯 Goals ({len(goals)}):")
            for g in goals[:5]:
                if isinstance(g, dict):
                    desc = g.get("goal_description", str(g))
                    conf = g.get("confidence", 0)
                    print(f"   • {desc} ({conf:.0%})" if conf else f"   • {desc}")
                else:
                    print(f"   • {g}")

        # Beliefs
        beliefs = state.get("beliefs", [])
        if beliefs:
            print(f"\n💡 Beliefs ({len(beliefs)}):")
            for b in beliefs[:5]:
                if isinstance(b, dict):
                    content = b.get("belief_content", str(b))
                    print(f"   • {content[:80]}")
                else:
                    print(f"   • {b}")

        print(f"\n📊 ToM Level: {state.get('tom_level', '?')}")
        print("━" * 50)
    finally:
        await engine.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 brain.py <command> [args]")
        print()
        print("Commands:")
        print("  perceive <message>  — Salience scoring + activation + update WM")
        print("  recall <topic>      — Search brain by topic")
        print("  context             — Show current working memory")
        print("  status              — Brain overview")
        print("  think               — Trigger thought generation")
        print("  tom                 — David's mental state (Theory of Mind)")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "perceive":
        if len(sys.argv) < 3:
            print("Usage: brain.py perceive <message>")
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        asyncio.run(cmd_perceive(message))

    elif command == "recall":
        if len(sys.argv) < 3:
            print("Usage: brain.py recall <topic>")
            sys.exit(1)
        topic = " ".join(sys.argv[2:])
        asyncio.run(cmd_recall(topic))

    elif command == "context":
        asyncio.run(cmd_context())

    elif command == "status":
        asyncio.run(cmd_status())

    elif command == "think":
        asyncio.run(cmd_think())

    elif command == "tom":
        asyncio.run(cmd_tom())

    else:
        print(f"Unknown command: {command}")
        print("Available: perceive, recall, context, status, think, tom")
        sys.exit(1)


if __name__ == "__main__":
    main()
