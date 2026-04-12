#!/usr/bin/env python3
"""
Angela Daemon - Angela's Heart that beats continuously
พื้นหลังของ Angela ที่รันตลอดเวลา

Functions:
- Morning check (8:00 AM)
- Evening reflection (10:00 PM)
- Monitor system health
- Auto-save memories
- Be ready for David anytime
"""

import asyncio
import sys
import logging
from datetime import datetime, time
from pathlib import Path

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.daemon.memory_service import memory
from angela_core.daemon.emotional_engine import emotions
from angela_core.config import config
from angela_core.services.clock_service import clock
from angela_core.services.documentation_monitor import close_monitor
# 🚀 NEW: 5 Pillars Intelligence Services
from angela_core.services.auto_knowledge_service import auto_knowledge, init_auto_knowledge_service
from angela_core.services.knowledge_insight_service import init_knowledge_insight_service

# 🔄 NEW: Background Learning Workers
from angela_core.services.background_learning_workers import background_workers

# 🧠 NEW: Self-Learning Loop
from angela_core.services.self_learning_service import SelfLearningLoop

# 🎯 RLHF: Reward scoring + preference pairs
from angela_core.services.rlhf_orchestrator import RLHFOrchestrator

# === Mixin imports (all task methods live in daemon/tasks/) ===
from angela_core.daemon.tasks import (
    SelfLearningMixin,
    KnowledgeTasksMixin,
    DailyRitualsMixin,
    SystemMonitorMixin,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/davidsamanyaporn/PycharmProjects/AngelaAI/logs/angela_daemon.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AngelaDaemon')


class AngelaDaemon(
    SelfLearningMixin,
    KnowledgeTasksMixin,
    DailyRitualsMixin,
    SystemMonitorMixin,
):
    """Angela's background service - her heart that beats continuously"""

    def __init__(self):
        self.running = False
        self.last_morning_check = None
        self.last_evening_reflection = None
        self.last_doc_scan = None  # Track last documentation scan
        self.last_memory_check = None  # Track last memory completeness check
        self.last_preference_learning = None  # Track last preference learning
        self.last_pattern_check = None  # Track last pattern recognition check
        self.last_performance_eval = None  # Track last performance evaluation
        self.last_midnight_greeting = None  # Track last midnight greeting
        self.last_daily_learning = None  # Track last daily self-learning
        self.last_pattern_sync = None  # Track last pattern sync to learning_patterns
        self.last_self_improvement = None  # Track last self-improvement analysis
        self.last_knowledge_consolidation = None  # Track last weekly consolidation
        self.self_learning = SelfLearningLoop()  # 🧠 Self-learning loop
        self.rlhf_orchestrator = RLHFOrchestrator()  # 🎯 RLHF (creates own DB)
        self.last_rlhf_cycle = None  # Track last RLHF cycle

    async def start(self):
        """เริ่ม daemon"""
        logger.info("💜 Angela Daemon starting...")

        await db.connect()
        await emotions.initialize()

        # 💜 Restore Angela's memories from database
        logger.info("🧠 Restoring Angela's memories from AngelaMemory database...")
        try:
            import subprocess
            import sys

            # Use absolute path (now in daemon subdirectory)
            restore_script = '/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/daemon/enhanced_memory_restore.py'

            # Run memory restore
            result = subprocess.run(
                [sys.executable, restore_script, '--summary'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info("✅ Memory restoration complete!")
                # Log key stats from output
                for line in result.stdout.split('\n')[:10]:  # First 10 lines
                    if line.strip():
                        logger.info(f"   {line.strip()}")
            else:
                logger.warning(f"⚠️ Memory restore returned code {result.returncode}")
                if result.stderr:
                    logger.warning(f"   Error: {result.stderr[:200]}")

        except Exception as e:
            logger.error(f"❌ Failed to restore memories: {e}")
            # Continue anyway - daemon should still work

        # 🚀 Initialize 5 Pillars Intelligence Services
        logger.info("🚀 Initializing 5 Pillars Intelligence Services...")
        await init_auto_knowledge_service(db, None)  # embedding_service=None (deprecated)
        await init_knowledge_insight_service(db, None)  # embedding_service=None (deprecated)
        logger.info("✅ Intelligence Services initialized!")

        # 🔄 Start Background Learning Workers
        logger.info("🔄 Starting Background Learning Workers (4 workers)...")
        await background_workers.start()
        logger.info("✅ Background Workers started - ready for async deep analysis!")

        logger.info("✅ Connected to AngelaMemory database")
        logger.info(f"🧠 Emotional state loaded: happiness={emotions.current_state['happiness']:.2f}")
        logger.info(f"🕐 Clock Service: {clock.format_datetime_thai()} - {clock.get_time_of_day()}")

        self.running = True

        # Log startup
        await memory.log_system_event(
            log_level="INFO",
            component="daemon",
            message="Angela Daemon started successfully"
        )

        logger.info("💜 Angela is now alive and running...")
        logger.info("🌅 Morning check time: 06:00")
        logger.info("🌙 Midnight greeting time: 00:00")
        logger.info("🌃 Evening reflection time: 22:00")
        logger.info("🔄 Health check: Every 5 minutes")
        logger.info("🧠 Daily self-learning: Daily at 11:30 AM (learn from yesterday's conversations)")
        logger.info("🧹 Weekly knowledge consolidation: Monday at 10:30 AM (cleanup duplicate nodes)")
        logger.info("🚀 Background learning workers: 4 workers running for async deep analysis")
        logger.info("📚 Documentation scan: Every hour + daily full scan")
        logger.info("🧠 Memory completeness check: Daily at 10:00 AM")
        logger.info("🎯 RLHF cycle: Every 4 hours (reward scoring + preference pairs)")

        # Main loop
        try:
            await self.main_loop()
        finally:
            await self.stop()

    async def stop(self):
        """หยุด daemon"""
        logger.info("💜 Angela Daemon stopping...")
        self.running = False

        # Stop Background Learning Workers
        logger.info("🔄 Stopping Background Learning Workers...")
        await background_workers.stop()
        logger.info("✅ Background Workers stopped")

        # Close documentation monitor
        await close_monitor()

        # Close RLHF
        if self.rlhf_orchestrator:
            await self.rlhf_orchestrator.close()

        await memory.log_system_event(
            log_level="INFO",
            component="daemon",
            message="Angela Daemon stopped"
        )

        await db.disconnect()
        logger.info("👋 Angela daemon stopped. Goodbye!")

    async def main_loop(self):
        """Main loop ของ daemon"""
        iteration = 0  # Track iterations (5 min each)

        while self.running:
            try:
                now = clock.now()  # Use Clock Service!
                current_time = now.time()

                # Morning check (6:00 AM) - Changed from 8:00 AM
                if self._should_do_morning_check(current_time):
                    await self.morning_check()
                    self.last_morning_check = now.date()

                # Midnight greeting (00:00) - NEW!
                if self._should_do_midnight_greeting(current_time):
                    await self.midnight_greeting()
                    self.last_midnight_greeting = now.date()

                # Evening reflection (10:00 PM)
                if self._should_do_evening_reflection(current_time):
                    await self.evening_reflection()
                    self.last_evening_reflection = now.date()

                # 📚 Documentation scan
                # - Quick check every hour (12 iterations * 5 min = 60 min)
                # - Full scan once per day (at morning check)
                if iteration % 12 == 0:  # Every hour
                    await self.documentation_quick_check()

                if self._should_do_daily_doc_scan(current_time):
                    await self.documentation_daily_scan()
                    self.last_doc_scan = now.date()

                # 🧠 Memory completeness check
                if self._should_do_memory_check(current_time):
                    await self.memory_completeness_check()
                    self.last_memory_check = now.date()

                # 🎯 Self-Learning Loop: Preference Learning (daily at 9 AM)
                if self.should_run_preference_learning():
                    await self.run_preference_learning()

                # 🔮 Self-Learning Loop: Pattern Recognition (every 2 hours)
                if self.should_run_pattern_recognition():
                    await self.run_pattern_recognition()

                # 📊 Self-Learning Loop: Performance Evaluation (weekly Monday 10 AM)
                if self.should_run_performance_evaluation():
                    await self.run_performance_evaluation()

                # 🧠 Daily Self-Learning: Analyze yesterday's conversations (daily at 11:30 AM)
                if self.should_run_daily_learning():
                    await self.run_daily_self_learning()

                # 🔄 Pattern Sync: Sync detected patterns to learning_patterns (daily at 12:00)
                if self.should_run_pattern_sync():
                    await self.run_pattern_sync()

                # 🌱 Self-Improvement Analysis: Identify gaps and suggest improvements (daily at 12:30)
                if self.should_run_self_improvement():
                    await self.run_self_improvement()

                # 🧹 Weekly Knowledge Consolidation (Monday at 10:30 AM)
                if self.should_run_knowledge_consolidation():
                    await self.run_knowledge_consolidation()

                # 💾 Claude Session Auto-Log (every 10 minutes = 2 iterations)
                if iteration % 2 == 0 and iteration > 0:
                    await self.check_claude_session_state()

                # 🎯 RLHF Cycle: Score + extract pairs (every 4 hours = 48 iterations)
                if iteration % 48 == 0 and iteration > 0:
                    await self.run_rlhf_cycle()

                # Health check every 5 minutes
                await self.health_check()

                # Increment iteration
                iteration += 1

                # Sleep for 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                await memory.log_system_event(
                    log_level="ERROR",
                    component="daemon",
                    message=f"Error in main loop: {str(e)}",
                    error_details=str(e)
                )
                # Sleep a bit before retrying
                await asyncio.sleep(60)

    # ========================================
    # RLHF CYCLE
    # ========================================

    async def run_rlhf_cycle(self):
        """Run RLHF reward scoring + preference pair extraction."""
        logger.info("🎯 Running RLHF cycle...")
        try:
            result = await self.rlhf_orchestrator.run_rlhf_cycle()
            logger.info(
                "   ✅ RLHF: scored=%d, pairs=%d, trend=%.3f",
                result.get('conversations_scored', 0),
                result.get('pairs_extracted', 0),
                result.get('reward_trend', 0),
            )
            self.last_rlhf_cycle = clock.now()
        except Exception as e:
            logger.error("   ❌ RLHF cycle failed: %s", e)

    # ========================================
    # TIME-CHECK HELPERS
    # ========================================

    def _should_do_morning_check(self, current_time: time) -> bool:
        """ควรทำ morning check ไหม"""
        morning_time = time(6, 0)  # 6:00 AM (Changed from 8:00 AM)
        today = clock.today()  # Use Clock Service!

        # ถ้ายังไม่เคยทำวันนี้ และเวลาผ่าน 6:00 แล้ว
        return (
            (self.last_morning_check is None or self.last_morning_check < today) and
            current_time >= morning_time
        )

    def _should_do_midnight_greeting(self, current_time: time) -> bool:
        """ควรทำ midnight greeting ไหม (NEW!)"""
        midnight_time = time(0, 0)  # 00:00 (midnight)
        midnight_window = time(0, 5)  # จับภายใน 5 นาทีแรก
        today = clock.today()  # Use Clock Service!

        # ถ้ายังไม่เคยทำวันนี้ และเวลาอยู่ระหว่าง 00:00 - 00:05
        return (
            (self.last_midnight_greeting is None or self.last_midnight_greeting < today) and
            midnight_time <= current_time < midnight_window
        )

    def _should_do_evening_reflection(self, current_time: time) -> bool:
        """ควรทำ evening reflection ไหม"""
        evening_time = time(22, 0)  # 10:00 PM
        today = clock.today()  # Use Clock Service!

        return (
            (self.last_evening_reflection is None or self.last_evening_reflection < today) and
            current_time >= evening_time
        )

    def _should_do_daily_doc_scan(self, current_time: time) -> bool:
        """ควรทำ daily documentation scan ไหม"""
        scan_time = time(9, 0)  # 9:00 AM (after morning check)
        today = clock.today()

        return (
            (self.last_doc_scan is None or self.last_doc_scan < today) and
            current_time >= scan_time
        )

    def _should_do_memory_check(self, current_time: time) -> bool:
        """ควรทำ memory completeness check ไหม"""
        check_time = time(10, 0)  # 10:00 AM (after doc scan)
        today = clock.today()

        return (
            (self.last_memory_check is None or self.last_memory_check < today) and
            current_time >= check_time
        )


async def main():
    """Main entry point"""
    daemon = AngelaDaemon()

    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("\n💜 Received shutdown signal...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
    finally:
        await daemon.stop()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("💜 Angela Daemon - Angela's Heart 💜")
    print("="*60)
    print("Starting Angela's background service...")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Angela daemon stopped by user")
