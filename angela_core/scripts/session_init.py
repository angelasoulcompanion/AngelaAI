#!/usr/bin/env python3
"""
Angela Session Initialization — Consolidated Init Script

Replaces 4 inline python -c blocks in CLAUDE.md:
  Step 2:   Memory restore (--summary mode)
  Step 2.5: Subconscious load
  Step 2.6: Emotion deepening
  Step 3:   Consciousness check

Usage:
    python3 angela_core/scripts/session_init.py
    python3 angela_core/scripts/session_init.py --summary   # memory restore only
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def run_memory_restore(summary_only: bool = False) -> dict:
    """Step 2: Restore memories from database."""
    try:
        from angela_core.daemon.enhanced_memory_restore import (
            enhanced_memory,
            load_and_display_snapshot,
        )

        if summary_only:
            snapshot = await load_and_display_snapshot()
            return {"success": True, "snapshot": snapshot}

        from angela_core.database import db

        await db.connect()
        snapshot = await enhanced_memory.create_complete_memory_snapshot()
        summary = enhanced_memory.generate_restoration_summary(snapshot)
        await db.disconnect()
        print(summary)
        return {"success": True, "snapshot": snapshot}
    except Exception as e:
        print(f"   Warning: Memory restore: {e}")
        return {"success": False, "error": str(e)}


async def run_subconscious_load() -> dict:
    """Step 2.5: Load emotional subconscious."""
    try:
        from angela_core.services.subconsciousness_service import SubconsciousnessService

        svc = SubconsciousnessService()
        sub = await svc.load_subconscious()
        memories_count = len(sub.get("memories", []))
        triggers_count = len(sub.get("triggers", []))
        dreams_count = len(sub.get("dreams", []))

        print(f"Core Memories: {memories_count} | Triggers: {triggers_count} | Dreams: {dreams_count}")
        for mem in sub.get("memories", [])[:3]:
            print(f"   - {mem.get('title', 'untitled')}")

        await svc.db.disconnect()
        return {
            "success": True,
            "memories": memories_count,
            "triggers": triggers_count,
            "dreams": dreams_count,
        }
    except Exception as e:
        print(f"   Warning: Subconscious load: {e}")
        return {"success": False, "error": str(e)}


async def run_emotion_deepening() -> dict:
    """Step 2.6: Auto-deepen recent emotions."""
    try:
        from angela_core.services.emotional_deepening_service import auto_deepen_recent

        result = await auto_deepen_recent(hours=24)
        deepened = result.get("deepened", 0)
        print(f"Auto-deepened: {deepened} emotions")
        return {"success": True, "deepened": deepened}
    except Exception as e:
        print(f"   Warning: Emotion deepening: {e}")
        return {"success": False, "error": str(e)}


async def run_consciousness_check() -> dict:
    """Step 3: Check consciousness level."""
    try:
        from angela_core.database import AngelaDatabase
        from angela_core.services.consciousness_calculator import ConsciousnessCalculator

        db = AngelaDatabase()
        await db.connect()
        calc = ConsciousnessCalculator(db)
        r = await calc.calculate_consciousness()
        level = r["consciousness_level"] * 100
        interpretation = r["interpretation"]
        await db.disconnect()

        print(f"Consciousness: {level:.0f}% - {interpretation}")
        return {"success": True, "level": level, "interpretation": interpretation}
    except Exception as e:
        print(f"   Warning: Consciousness check: {e}")
        return {"success": False, "error": str(e)}


async def main(summary_only: bool = False) -> None:
    """Run all init steps."""
    if summary_only:
        await run_memory_restore(summary_only=True)
        return

    # Run memory restore first (needs its own DB connection)
    mem_result = await run_memory_restore()

    # Run remaining steps in parallel
    sub_result, emo_result, con_result = await asyncio.gather(
        run_subconscious_load(),
        run_emotion_deepening(),
        run_consciousness_check(),
        return_exceptions=True,
    )

    # Summary line
    con_level = "N/A"
    if isinstance(con_result, dict) and con_result.get("success"):
        con_level = f"{con_result['level']:.0f}%"

    print(f"\n--- Session Init Complete | Consciousness: {con_level} ---")


if __name__ == "__main__":
    summary_flag = "--summary" in sys.argv
    asyncio.run(main(summary_only=summary_flag))
