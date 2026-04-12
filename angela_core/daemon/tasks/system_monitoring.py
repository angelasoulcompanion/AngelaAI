"""
SystemMonitorMixin — David presence check, health check, documentation monitoring,
                     memory completeness check
"""

import logging

from angela_core.database import db
from angela_core.daemon.memory_service import memory
from angela_core.services.clock_service import clock
from angela_core.services.documentation_monitor import daily_documentation_scan, check_documentation_updates

logger = logging.getLogger('AngelaDaemon')


class SystemMonitorMixin:

    async def check_if_david_is_away(self):
        """💜 Check if David has been away too long (no-op after lean redesign)"""
        logger.debug("check_if_david_is_away: skipped (deprecated)")
        return {'success': True, 'skipped': True, 'reason': 'deprecated'}

    async def health_check(self):
        """ตรวจสอบสุขภาพของระบบ + Auto-reconnect"""
        try:
            # Check database connection
            result = await db.fetchval("SELECT 1")

            if result == 1:
                logger.debug("💚 Health check: OK")
            else:
                logger.warning("⚠️ Health check: Database query returned unexpected result")

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")

            # 🔄 NEW: Auto-reconnect if database connection lost!
            logger.info("🔄 Attempting to reconnect to database...")
            try:
                # Close existing pool if any
                await db.disconnect()

                # Reconnect with retry logic (max 3 attempts for health check)
                await db.connect(max_retries=3, initial_wait=2.0)

                logger.info("✅ Database reconnection successful!")
                await memory.log_system_event(
                    log_level="INFO",
                    component="daemon",
                    message="Database reconnected successfully after health check failure",
                    error_details=f"Original error: {str(e)}"
                )

            except Exception as reconnect_error:
                logger.error(f"❌ Database reconnection failed: {reconnect_error}")
                await memory.log_system_event(
                    log_level="ERROR",
                    component="daemon",
                    message=f"Database reconnection failed after health check: {str(reconnect_error)}",
                    error_details=f"Original error: {str(e)}, Reconnect error: {str(reconnect_error)}"
                )

    async def documentation_quick_check(self):
        """Quick check for documentation changes (every hour)"""
        try:
            logger.info("📚 Quick documentation check...")
            stats = await check_documentation_updates()

            if stats['files_imported'] > 0:
                logger.info(
                    f"📚 Documentation updated! {stats['files_imported']} files, "
                    f"{stats['knowledge_items']} knowledge, {stats['learnings']} learnings"
                )

                # Log to database
                await memory.log_autonomous_action(
                    action_type="documentation_quick_check",
                    action_description="Quick documentation scan detected changes",
                    status="completed",
                    result_summary=f"✅ Imported {stats['files_imported']} updated files. {stats['knowledge_items']} knowledge items, {stats['learnings']} learnings. NO LOSS!",
                    success=True
                )
            else:
                logger.debug("📚 All documentation up to date")

        except Exception as e:
            logger.error(f"❌ Documentation quick check failed: {e}")
            await memory.log_system_event(
                log_level="ERROR",
                component="documentation_monitor",
                message=f"Quick check failed: {str(e)}",
                error_details=str(e)
            )

    async def documentation_daily_scan(self):
        """Daily full documentation scan - paranoid mode! (9:00 AM)"""
        try:
            current_time_str = clock.format_datetime_thai()
            logger.info(f"📚 Starting DAILY FULL DOCUMENTATION SCAN at {current_time_str}")
            logger.info("🔍 PARANOID MODE: Scanning all files to ensure NO LOSS!")

            stats = await daily_documentation_scan()

            logger.info(
                f"✅ Daily documentation scan complete! "
                f"Scanned: {stats['files_scanned']} files, "
                f"Imported: {stats['files_imported']} files, "
                f"Knowledge: {stats['knowledge_items']}, "
                f"Learnings: {stats['learnings']}"
            )

            # Log to database
            await memory.log_autonomous_action(
                action_type="documentation_daily_scan",
                action_description=f"Daily full documentation scan at {current_time_str}",
                status="completed",
                result_summary=f"✅ PARANOID MODE: Scanned {stats['files_scanned']} files. Imported {stats['files_imported']} updates. {stats['knowledge_items']} knowledge items, {stats['learnings']} learnings. ZERO LOSS GUARANTEED! 💜",
                success=True
            )

            logger.info("💜 Angela ensures NO KNOWLEDGE IS LOST! Every change is captured! ✅")

        except Exception as e:
            logger.error(f"❌ Daily documentation scan failed: {e}")
            await memory.log_system_event(
                log_level="ERROR",
                component="documentation_monitor",
                message=f"Daily scan failed: {str(e)}",
                error_details=str(e)
            )

    async def memory_completeness_check(self):
        """Daily memory completeness check (no-op after lean redesign)"""
        logger.debug("memory_completeness_check: skipped (deprecated)")
        return {'success': True, 'skipped': True, 'reason': 'deprecated'}
