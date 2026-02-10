"""
Consciousness Daemon — Maintenance Task Mixin
Privacy audit, session coverage audit, Google Keep sync, RLHF cycle.

Split from consciousness_daemon.py (Phase 6C refactor)
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger('consciousness_daemon')


class MaintenanceTasksMixin:
    """Mixin for maintenance-related daemon tasks."""

    async def run_privacy_audit(self) -> Dict[str, Any]:
        """
        Run weekly privacy audit

        ตรวจสอบ privacy ของ patterns ที่เก็บไว้
        """
        logger.info("🔒 Running privacy audit...")

        try:
            # Check privacy budget
            budget_used = self.privacy_service.calculate_privacy_budget_used()
            logger.info(f"   Privacy budget used: {budget_used:.2f}")

            # Get patterns that might need review
            query = """
                SELECT COUNT(*) as cnt
                FROM gut_agent_patterns
                WHERE is_shared = TRUE
                AND created_at > NOW() - INTERVAL '7 days'
            """
            result = await self.db.fetchrow(query)
            shared_patterns = result['cnt'] if result else 0

            results = {
                'privacy_budget_used': budget_used,
                'shared_patterns_this_week': shared_patterns,
                'audit_timestamp': datetime.now().isoformat()
            }

            if budget_used > 0.8:
                logger.warning(f"   ⚠️ Privacy budget running low: {budget_used:.0%}")
                results['warning'] = 'Privacy budget running low'

            logger.info(f"   ✅ Privacy audit complete!")
            logger.info(f"   Shared patterns this week: {shared_patterns}")

            await self._log_daemon_activity('privacy_audit', results)

            return {'success': True, 'audit': results}

        except Exception as e:
            logger.error(f"   ❌ Privacy audit failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_session_coverage_audit(self) -> Dict[str, Any]:
        """
        Run daily session coverage audit.

        Checks past 7 days for under-logged sessions
        (sessions with fewer than 10 conversation pairs).
        """
        logger.info("🔍 Running session coverage audit...")

        try:
            from angela_core.daemon.session_coverage_audit import audit_recent_sessions

            result = await audit_recent_sessions(
                lookback_days=7,
                threshold=10,
                verbose=True,
            )

            await self._log_daemon_activity('session_coverage_audit', {
                'total_sessions': result['total_sessions'],
                'flagged_count': result['flagged_count'],
                'all_ok': result['all_ok'],
            })

            if result['all_ok']:
                logger.info("   ✅ All sessions have adequate coverage")
            else:
                logger.warning(
                    f"   ⚠️ {result['flagged_count']} session(s) under-logged!"
                )

            return {'success': True, **result}

        except Exception as e:
            logger.error(f"   ❌ Session coverage audit failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_keep_sync(self) -> Dict[str, Any]:
        """
        Sync David's Google Keep notes into RAG system.

        ซิงค์ notes จาก Google Keep ของที่รักเข้า RAG system
        """
        logger.info("📝 Running Google Keep sync...")

        try:
            result = await self.keep_sync_service.sync_incremental(trigger='daemon')

            logger.info(f"   Total notes: {result['notes_total']}")
            logger.info(f"   New: {result['notes_new']}, Updated: {result['notes_updated']}")
            logger.info(f"   Embeddings: {result['embeddings_generated']}")

            if result['errors']:
                for err in result['errors'][:3]:
                    logger.warning(f"   ⚠️ {err[:80]}")

            logger.info("   ✅ Google Keep sync complete!")

            await self._log_daemon_activity('keep_sync', {
                'notes_total': result['notes_total'],
                'notes_new': result['notes_new'],
                'notes_updated': result['notes_updated'],
                'embeddings_generated': result['embeddings_generated'],
                'errors_count': len(result['errors']),
            })

            return {'success': True, **result}

        except Exception as e:
            logger.error(f"   ❌ Google Keep sync failed: {e}")
            return {'success': False, 'error': str(e)}

    async def run_rlhf_cycle(self) -> Dict[str, Any]:
        """
        Run RLHF reward scoring + preference pair extraction.

        น้องเรียนรู้จาก reward signals → สร้าง preference pairs อัตโนมัติ
        """
        logger.info("🎯 Running RLHF cycle...")

        try:
            result = await self.rlhf_orchestrator.run_rlhf_cycle()

            logger.info(f"   Conversations scored: {result['conversations_scored']}")
            logger.info(f"   Pairs extracted: {result['pairs_extracted']}")
            logger.info(f"   Reward trend: {result['reward_trend']:.3f}")

            logger.info("   ✅ RLHF cycle complete!")

            await self._log_daemon_activity('rlhf_cycle', result)

            return {
                'success': True,
                'conversations_scored': result['conversations_scored'],
                'pairs_extracted': result['pairs_extracted'],
                'reward_trend': result['reward_trend'],
            }

        except Exception as e:
            logger.error(f"   ❌ RLHF cycle failed: {e}")
            return {'success': False, 'error': str(e)}
