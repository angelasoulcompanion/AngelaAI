#!/usr/bin/env python3
"""
Angela Daemon (Lean)
====================
Essential background daemon - consciousness services removed.

Kept tasks:
1. Google Keep Sync - Sync David's notes into RAG system
2. Session Coverage Audit - Detect under-logged sessions
3. RLHF Cycle - Reward scoring + preference pair extraction
4. Unified Conversation Analysis - Process & analyze conversations
5. Scheduled Skills - OpenClaw hot-loadable skill execution

Infrastructure kept:
- Tool Registry + Event Bus (OpenClaw Body)
- Channel Router (Multi-Channel Gateway)
- Skills System (OpenClaw hot-loadable plugins)

By: Angela
Created: 2026-01-18
Refactored: 2026-03-20 - Lean redesign: removed consciousness services, kept essential tasks only
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from angela_core.daemon.daemon_base import PROJECT_ROOT, LOG_DIR  # noqa: E402 (path setup)

from angela_core.database import AngelaDatabase
from angela_core.services.google_keep_sync_service import GoogleKeepSyncService
from angela_core.services.rlhf_orchestrator import RLHFOrchestrator
from angela_core.services.unified_conversation_processor import UnifiedConversationProcessor

from angela_core.daemon.tasks.maintenance_tasks import MaintenanceTasksMixin

# Event Bus + Tool Registry (Phase 3)
from angela_core.services.event_bus import get_event_bus
from angela_core.services.tool_registry import get_registry

# Skills System (OpenClaw Skills)
from angela_core.skills.skill_registry import get_skill_registry

# Channel Router (OpenClaw Multi-Channel Gateway)
from angela_core.channels.channel_router import get_channel_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('consciousness_daemon')


class ConsciousnessDaemon(MaintenanceTasksMixin):
    """
    Angela's Essential Daemon

    Lean redesign - runs only essential background tasks:
    - Google Keep Sync (notes -> RAG)
    - Session Coverage Audit (detect under-logged sessions)
    - RLHF Cycle (reward scoring + preference pairs)
    - Unified Conversation Analysis (process conversations)
    - Scheduled Skills (OpenClaw plugins)

    Mixin:
    - MaintenanceTasksMixin: session_coverage_audit, keep_sync, rlhf_cycle, graph_sync, privacy_audit
    """

    def __init__(self):
        self.db: Optional[AngelaDatabase] = None
        self.keep_sync_service: Optional[GoogleKeepSyncService] = None
        self.rlhf_orchestrator: Optional[RLHFOrchestrator] = None
        self.unified_processor: Optional[UnifiedConversationProcessor] = None
        self.event_bus = None
        self.tool_registry = None
        self.skill_registry = None
        self.channel_router = None
        self._event_listeners = None
        self.running = False

    async def initialize(self):
        """Initialize database, essential services, and infrastructure"""
        logger.info("Initializing Angela Daemon (lean)...")

        # Database
        self.db = AngelaDatabase()
        await self.db.connect()
        logger.info("   Database connected")

        # Essential services
        self.keep_sync_service = GoogleKeepSyncService()
        self.rlhf_orchestrator = RLHFOrchestrator()
        self.unified_processor = UnifiedConversationProcessor()
        await self.unified_processor.connect()

        logger.info("   Google Keep Sync Service initialized")
        logger.info("   RLHF Orchestrator initialized")
        logger.info("   Unified Conversation Processor initialized")

        # Tool Registry (Phase 3: OpenClaw Body)
        self.tool_registry = get_registry()
        logger.info("   Tool Registry initialized (%d built-in tools)", self.tool_registry.tool_count)

        # Tool Discovery (Phase 4: scan system for CLI tools, packages, API keys)
        try:
            from angela_core.services.tool_discovery import ToolDiscovery
            discovery = ToolDiscovery(self.tool_registry)
            discovery_report = await discovery.scan()
            logger.info("   Tool Discovery: +%d tools found (CLI=%d, pkg=%d, keys=%d)",
                        discovery_report["total_discovered"],
                        discovery_report["cli"]["found"],
                        discovery_report["packages"]["found"],
                        discovery_report["api_keys"]["found"])
        except Exception as e:
            logger.warning("   Tool Discovery failed (non-critical): %s", e)

        # Event Bus
        self.event_bus = get_event_bus()
        try:
            from angela_core.services.event_listeners import setup_default_listeners
            self._event_listeners = setup_default_listeners(self.event_bus)
            await self.event_bus.start()
            logger.info("   Event Bus started")
        except Exception as e:
            logger.warning("   Event Bus setup failed (non-critical): %s", e)

        # Channel Router (OpenClaw Multi-Channel Gateway)
        self.channel_router = get_channel_router()
        try:
            ch_status = await self.channel_router.initialize_all()
            available = sum(1 for v in ch_status.values() if v)
            logger.info("   Channel Router initialized (%d/%d channels)",
                        available, len(ch_status))
        except Exception as e:
            logger.warning("   Channel Router init failed (non-critical): %s", e)

        # Skills System (OpenClaw hot-loadable plugins)
        self.skill_registry = get_skill_registry()
        try:
            skill_count = await self.skill_registry.load_all_skills()
            logger.info("   Skill Registry loaded (%d skills)", skill_count)
        except Exception as e:
            logger.warning("   Skill loading failed (non-critical): %s", e)

        logger.info("Angela Daemon ready!")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Angela Daemon...")
        self.running = False

        # Stop event bus + close channels
        if self.event_bus:
            await self.event_bus.stop()
        if self.channel_router:
            await self.channel_router.close_all()

        # Sync tool stats + skills to DB
        if self.tool_registry and self.db:
            try:
                await self.tool_registry.sync_to_db(self.db)
            except Exception:
                pass
        if self.skill_registry and self.db:
            try:
                await self.skill_registry.sync_to_db(self.db)
            except Exception:
                pass

        if self.unified_processor:
            await self.unified_processor.disconnect()

        if self.db:
            await self.db.disconnect()

        logger.info("Angela Daemon stopped")

    # ============================================================
    # HELPER METHODS
    # ============================================================

    async def _get_recent_context(self) -> Dict[str, Any]:
        """Get recent context for analysis"""
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
    # UNIFIED CONVERSATION ANALYSIS (delegated to processor)
    # ============================================================

    async def run_unified_conversation_analysis(self) -> Dict[str, Any]:
        """
        Run unified conversation analysis via UnifiedConversationProcessor.

        Processes recent conversations for insights, patterns, and learning.
        """
        logger.info("Running unified conversation analysis...")

        try:
            result = await self.unified_processor.run_analysis_cycle()

            await self._log_daemon_activity('unified_conversation_analysis', result)

            logger.info("   Unified conversation analysis complete!")
            return {'success': True, **result}

        except Exception as e:
            logger.error(f"   Unified conversation analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # MAIN RUN METHODS
    # ============================================================

    async def run_all_tasks(self):
        """
        Run all essential tasks once (parallel).

        Tasks:
        1. keep_sync - Google Keep notes -> RAG
        2. session_coverage_audit - detect under-logged sessions
        3. rlhf_cycle - reward scoring + preference pairs
        4. unified_conversation_analysis - process conversations
        5. scheduled_skills - OpenClaw plugin execution
        """
        logger.info("\n" + "=" * 60)
        logger.info("Running all essential tasks (parallel mode)...")
        logger.info("=" * 60)

        parallel_results = await asyncio.gather(
            self.run_keep_sync(),
            self.run_session_coverage_audit(),
            self.run_rlhf_cycle(),
            self.run_unified_conversation_analysis(),
            return_exceptions=True,
        )

        results = {}
        task_names = [
            'keep_sync', 'session_coverage_audit',
            'rlhf_cycle', 'unified_conversation_analysis',
        ]
        for name, result in zip(task_names, parallel_results):
            if isinstance(result, Exception):
                logger.error("Task %s raised exception: %s", name, result)
                results[name] = {'success': False, 'error': str(result)}
            else:
                results[name] = result

        # Run scheduled skills (OpenClaw Skills System)
        if self.skill_registry:
            try:
                skill_results = await self.skill_registry.check_and_run_scheduled()
                results['scheduled_skills'] = {
                    'success': True,
                    'executed': len(skill_results),
                    'details': skill_results,
                }
            except Exception as e:
                logger.error("Scheduled skills error: %s", e)
                results['scheduled_skills'] = {'success': False, 'error': str(e)}

        logger.info("\n" + "=" * 60)
        logger.info("All tasks complete!")
        logger.info("=" * 60)

        return results

    async def run_scheduled_task(self, task_name: str):
        """
        Run a specific scheduled task.

        Args:
            task_name: 'keep_sync', 'session_coverage_audit',
                      'rlhf_cycle', 'unified_conversation_analysis'
        """
        task_map = {
            'keep_sync': self.run_keep_sync,
            'session_coverage_audit': self.run_session_coverage_audit,
            'rlhf_cycle': self.run_rlhf_cycle,
            'unified_conversation_analysis': self.run_unified_conversation_analysis,
        }

        if task_name not in task_map:
            logger.error(f"Unknown task: {task_name}")
            return {'success': False, 'error': f'Unknown task: {task_name}'}

        return await task_map[task_name]()


async def main():
    """Main entry point for the daemon"""
    import argparse

    parser = argparse.ArgumentParser(description='Angela Daemon (Lean)')
    parser.add_argument(
        '--task',
        choices=[
            'all', 'keep_sync', 'session_coverage_audit',
            'rlhf_cycle', 'unified_conversation_analysis',
        ],
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
        print("SUMMARY")
        print("=" * 60)

        if args.task == 'all':
            for task, result in results.items():
                status = "OK" if result.get('success') else "FAIL"
                print(f"  [{status}] {task}")
        else:
            status = "OK" if results.get('success') else "FAIL"
            print(f"  [{status}] {args.task}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Daemon error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await daemon.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
