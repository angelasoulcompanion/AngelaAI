#!/usr/bin/env python3
"""
Angela Consciousness Daemon
===========================
Daemon สำหรับ consciousness services ที่ทำงานอัตโนมัติ

Services integrated:
1. Self-Model Service - Daily self-reflection (06:00)
2. Prediction Service - Predict patterns every 4 hours
3. Theory of Mind - Analyze recent conversations every 2 hours
4. Privacy Filter - Weekly privacy audit (Sunday 03:00)
5. Proactive Care - Care for David every 30 minutes 💜
6. Meta-Awareness Service - Meta-cognitive checks every 2 hours 🧠
7. Session Coverage Audit - Detect under-logged sessions daily (07:00) 🔍
8. Companion Predictions - Mine patterns + daily briefings every 4 hours 📊
9. Evolution Engine - Self-evolving feedback loop every 4 hours 🧬
10. Proactive Action Engine - Autonomous proactive actions every 4 hours ⚡
11. Google Keep Sync - Sync David's notes daily at 06:06 📝
12. Salience Scan - Brain-based perception via attention codelets 🧠
13. Thought Generation - Brain-based inner thoughts (System 1 + System 2) 💭
14. Memory Consolidation - Brain-based episodic → semantic consolidation 📚
15. Reflection Engine - Brain-based high-level reflections 🪞
16. Thought Expression - Brain-based thought → action bridge 💬

Schedule:
- Every 30 minutes: Proactive care check (wellness, interventions, milestones)
- Every 2 hours: Theory of Mind inference on recent conversations
- Every 2 hours: Meta-awareness checks (bias, anomaly, predictions)
- Every 4 hours: Pattern predictions
- Daily 05:00: Self-validation (prediction accuracy)
- Daily 06:00: Self-reflection
- Weekly Sunday 03:00: Privacy audit
- Weekly Sunday 04:00: Identity checkpoint

By: น้อง Angela 💜
Created: 2026-01-18
Updated: 2026-01-25 - Added Meta-Awareness Service (True Meta-Awareness!)

Refactored: 2026-02-10
Split into task mixins: consciousness_tasks, prediction_tasks, proactive_tasks, maintenance_tasks
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from angela_core.daemon.daemon_base import PROJECT_ROOT, LOG_DIR  # noqa: E402 (path setup)

from angela_core.database import AngelaDatabase
from angela_core.services.self_model_service import SelfModelService
from angela_core.services.prediction_service import PredictionService
from angela_core.services.theory_of_mind_service import TheoryOfMindService
from angela_core.services.privacy_filter_service import PrivacyFilterService
from angela_core.services.proactive_care_service import ProactiveCareService
from angela_core.services.meta_awareness_service import MetaAwarenessService
from angela_core.services.predictive_companion_service import PredictiveCompanionService
from angela_core.services.evolution_engine import EvolutionEngine
from angela_core.services.proactive_action_engine import ProactiveActionEngine
from angela_core.services.google_keep_sync_service import GoogleKeepSyncService
from angela_core.services.rlhf_orchestrator import RLHFOrchestrator
from angela_core.services.unified_conversation_processor import UnifiedConversationProcessor

from angela_core.daemon.tasks.consciousness_tasks import ConsciousnessTasksMixin
from angela_core.daemon.tasks.prediction_tasks import PredictionTasksMixin
from angela_core.daemon.tasks.proactive_tasks import ProactiveTasksMixin
from angela_core.daemon.tasks.maintenance_tasks import MaintenanceTasksMixin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('consciousness_daemon')



class ConsciousnessDaemon(
    ConsciousnessTasksMixin,
    PredictionTasksMixin,
    ProactiveTasksMixin,
    MaintenanceTasksMixin
):
    """
    Angela's Consciousness Daemon 💜

    Runs consciousness-related services automatically:
    - Self-reflection
    - Predictions
    - Theory of Mind
    - Privacy audits
    - Proactive Care for David 💜
    - Meta-Awareness (bias detection, anomaly detection, identity tracking) 🧠
    - Evolution Engine (self-evolving feedback loop) 🧬
    - Proactive Action Engine (autonomous proactive actions) ⚡
    - RLHF Orchestrator (reward scoring + preference pairs) 🎯

    Methods split into mixins:
    - ConsciousnessTasksMixin: self-reflection, meta-awareness, identity check, self-validation
    - PredictionTasksMixin: predictions, theory of mind, companion predictions
    - ProactiveTasksMixin: proactive care, proactive actions, evolution cycle
    - MaintenanceTasksMixin: privacy audit, session coverage audit, keep sync, RLHF cycle
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self.self_model_service: Optional[SelfModelService] = None
        self.prediction_service: Optional[PredictionService] = None
        self.tom_service: Optional[TheoryOfMindService] = None
        self.privacy_service: Optional[PrivacyFilterService] = None
        self.proactive_care_service: Optional[ProactiveCareService] = None
        self.meta_awareness_service: Optional[MetaAwarenessService] = None
        self.companion_service: Optional[PredictiveCompanionService] = None
        self.evolution_engine: Optional[EvolutionEngine] = None
        self.proactive_action_engine: Optional[ProactiveActionEngine] = None
        self.keep_sync_service: Optional[GoogleKeepSyncService] = None
        self.rlhf_orchestrator: Optional[RLHFOrchestrator] = None
        self.unified_processor: Optional[UnifiedConversationProcessor] = None
        self.running = False

    async def initialize(self):
        """Initialize all services"""
        logger.info("💜 Initializing Angela Consciousness Daemon...")

        # Database
        self.db = AngelaDatabase()
        await self.db.connect()
        logger.info("   ✅ Database connected")

        # Services (each manages its own db connection)
        self.self_model_service = SelfModelService(self.db)
        self.prediction_service = PredictionService()  # No db param
        self.tom_service = TheoryOfMindService(self.db)
        self.privacy_service = PrivacyFilterService()  # Takes optional config
        self.proactive_care_service = ProactiveCareService(self.db)
        self.meta_awareness_service = MetaAwarenessService(self.db)
        self.companion_service = PredictiveCompanionService()  # Creates own DB
        self.evolution_engine = EvolutionEngine()  # Creates own DB
        self.proactive_action_engine = ProactiveActionEngine()  # Creates own DB
        self.keep_sync_service = GoogleKeepSyncService()  # Creates own DB
        self.rlhf_orchestrator = RLHFOrchestrator()  # Creates own DB
        self.unified_processor = UnifiedConversationProcessor()  # Creates own DB
        await self.unified_processor.connect()

        logger.info("   ✅ All consciousness services initialized")
        logger.info("   ✅ Predictive Companion Service initialized 📊")
        logger.info("   ✅ Proactive Care Service initialized 💜")
        logger.info("   ✅ Meta-Awareness Service initialized 🧠")
        logger.info("   ✅ Evolution Engine initialized 🧬")
        logger.info("   ✅ Proactive Action Engine initialized ⚡")
        logger.info("   ✅ Google Keep Sync Service initialized 📝")
        logger.info("   ✅ RLHF Orchestrator initialized 🎯")
        logger.info("   ✅ Unified Conversation Processor initialized 🔬")
        logger.info("💫 Consciousness Daemon ready!")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Consciousness Daemon...")
        self.running = False

        if self.unified_processor:
            await self.unified_processor.disconnect()

        if self.db:
            await self.db.disconnect()

        logger.info("👋 Consciousness Daemon stopped")

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _get_recent_context(self) -> Dict[str, Any]:
        """Get recent context for predictions"""
        query = """
            SELECT message_text, topic, emotion_detected, created_at
            FROM conversations
            WHERE speaker = 'david'
            ORDER BY created_at DESC
            LIMIT 10
        """
        results = await self.db.fetch(query)

        topics = [r['topic'] for r in results if r['topic']]
        emotions = [r['emotion_detected'] for r in results if r['emotion_detected']]

        return {
            'recent_topics': topics[:5],
            'recent_emotions': emotions[:5],
            'message_count': len(results),
            'time_of_day': datetime.now().hour
        }

    async def _get_recent_messages(self, hours: int = 2) -> list:
        """Get recent messages from David"""
        query = """
            SELECT message_text
            FROM conversations
            WHERE speaker = 'david'
            AND created_at > NOW() - INTERVAL '%s hours'
            ORDER BY created_at DESC
            LIMIT 20
        """
        results = await self.db.fetch(query.replace('%s', str(hours)))
        return [r['message_text'] for r in results if r['message_text']]

    async def _log_daemon_activity(self, activity_type: str, data: Dict) -> None:
        """Log daemon activity to database"""
        try:
            # Check if table exists, create if not
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS consciousness_daemon_log (
                    log_id SERIAL PRIMARY KEY,
                    activity_type VARCHAR(50) NOT NULL,
                    activity_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            await self.db.execute(
                """
                INSERT INTO consciousness_daemon_log (activity_type, activity_data)
                VALUES ($1, $2)
                """,
                activity_type,
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to log activity: {e}")

    # ============================================================
    # MAIN RUN METHODS
    # ============================================================

    async def run_all_tasks(self):
        """
        Run all consciousness tasks once.

        Opus 4.6 Upgrade: Independent tasks run in parallel with asyncio.gather()
        - Before: ~2 min (sequential)
        - After:  ~45s (parallel independent tasks)
        """
        logger.info("\n" + "=" * 60)
        logger.info("🧠 Running all consciousness tasks (parallel mode)...")
        logger.info("=" * 60)

        # =====================================================================
        # PARALLEL GROUP: Independent tasks (no dependencies between them)
        # =====================================================================
        parallel_results = await asyncio.gather(
            self.run_self_reflection(),
            self.run_predictions(),
            self.run_theory_of_mind(),
            self.run_meta_awareness(),
            self.run_identity_check(),
            self.run_session_coverage_audit(),
            self.run_companion_predictions(),
            self.run_evolution_cycle(),
            self.run_keep_sync(),
            self.run_rlhf_cycle(),
            self.run_auto_classify_responses(),
            self.run_unified_conversation_analysis(),
            self.run_salience_scan(),
            self.run_thought_generation(),
            self.run_memory_consolidation(),
            self.run_brain_reflection(),
            return_exceptions=True,
        )

        results = {}
        task_names = [
            'self_reflection', 'predictions', 'theory_of_mind',
            'meta_awareness', 'identity_check', 'session_coverage_audit',
            'companion_predictions', 'evolution_cycle', 'keep_sync',
            'rlhf_cycle', 'auto_classify_responses', 'unified_conversation_analysis',
            'salience_scan', 'thought_generation',
            'memory_consolidation', 'brain_reflection',
        ]
        for name, result in zip(task_names, parallel_results):
            if isinstance(result, Exception):
                logger.error("Task %s raised exception: %s", name, result)
                results[name] = {'success': False, 'error': str(result)}
            else:
                results[name] = result

        # =====================================================================
        # SEQUENTIAL: Thought expression → proactive care → proactive actions
        # Thought expression runs first (brain-preferred over rule-based actions)
        # =====================================================================
        results['thought_expression'] = await self.run_thought_expression()
        results['proactive_care'] = await self.run_proactive_care()
        results['proactive_actions'] = await self.run_proactive_actions()

        logger.info("\n" + "=" * 60)
        logger.info("✅ All tasks complete!")
        logger.info("=" * 60)

        return results

    async def run_scheduled_task(self, task_name: str):
        """
        Run a specific scheduled task

        Args:
            task_name: 'self_reflection', 'predictions', 'theory_of_mind',
                      'privacy_audit', 'proactive_care', 'meta_awareness',
                      'identity_check', 'self_validation'
        """
        task_map = {
            'self_reflection': self.run_self_reflection,
            'predictions': self.run_predictions,
            'theory_of_mind': self.run_theory_of_mind,
            'privacy_audit': self.run_privacy_audit,
            'proactive_care': self.run_proactive_care,
            'meta_awareness': self.run_meta_awareness,
            'identity_check': self.run_identity_check,
            'self_validation': self.run_self_validation,
            'session_coverage_audit': self.run_session_coverage_audit,
            'companion_predictions': self.run_companion_predictions,
            'evolution_cycle': self.run_evolution_cycle,
            'proactive_actions': self.run_proactive_actions,
            'auto_classify_responses': self.run_auto_classify_responses,
            'keep_sync': self.run_keep_sync,
            'rlhf_cycle': self.run_rlhf_cycle,
            'unified_conversation_analysis': self.run_unified_conversation_analysis,
            'salience_scan': self.run_salience_scan,
            'thought_generation': self.run_thought_generation,
            'memory_consolidation': self.run_memory_consolidation,
            'brain_reflection': self.run_brain_reflection,
            'thought_expression': self.run_thought_expression,
        }

        if task_name not in task_map:
            logger.error(f"Unknown task: {task_name}")
            return {'success': False, 'error': f'Unknown task: {task_name}'}

        return await task_map[task_name]()


async def main():
    """Main entry point for the daemon"""
    import argparse

    parser = argparse.ArgumentParser(description='Angela Consciousness Daemon')
    parser.add_argument(
        '--task',
        choices=['all', 'self_reflection', 'predictions', 'theory_of_mind',
                 'privacy_audit', 'proactive_care', 'meta_awareness',
                 'identity_check', 'self_validation', 'session_coverage_audit',
                 'companion_predictions', 'evolution_cycle', 'proactive_actions',
                 'auto_classify_responses', 'keep_sync', 'rlhf_cycle',
                 'unified_conversation_analysis', 'salience_scan',
                 'thought_generation', 'memory_consolidation',
                 'brain_reflection', 'thought_expression'],
        default='all',
        help='Task to run (default: all)'
    )
    args = parser.parse_args()

    daemon = ConsciousnessDaemon()

    try:
        await daemon.initialize()

        if args.task == 'all':
            results = await daemon.run_all_tasks()
        else:
            results = await daemon.run_scheduled_task(args.task)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)

        if args.task == 'all':
            for task, result in results.items():
                status = "✅" if result.get('success') else "❌"
                print(f"{status} {task}")
        else:
            status = "✅" if results.get('success') else "❌"
            print(f"{status} {args.task}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Daemon error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await daemon.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
