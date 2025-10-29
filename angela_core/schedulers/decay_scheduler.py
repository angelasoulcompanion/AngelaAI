"""
Decay Scheduler - Automated Memory Compression

Runs periodically to:
1. Check memory strengths
2. Schedule decay operations
3. Process compression tasks
4. Track token savings

Runs every 6 hours by default.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict
import logging

from angela_core.services.decay_gradient_service import get_decay_service
from angela_core.database import get_db_connection


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DecayScheduler - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DecayScheduler:
    """
    Automated scheduler for memory decay and compression.

    Workflow:
    1. Scan long-term memories for decay candidates
    2. Calculate current memory strengths
    3. Schedule compression operations
    4. Process scheduled compressions in batches
    5. Log token savings and metrics
    """

    def __init__(self, interval_hours: int = 6, batch_size: int = 100):
        """
        Initialize scheduler.

        Args:
            interval_hours: How often to run (default: 6 hours)
            batch_size: How many memories to process per batch (default: 100)
        """
        self.interval_hours = interval_hours
        self.batch_size = batch_size
        self.decay_service = get_decay_service()
        self.running = False
        self.last_run = None
        self.stats = {
            'total_runs': 0,
            'total_memories_processed': 0,
            'total_tokens_saved': 0,
            'total_compressions': 0,
            'total_deletions': 0
        }

    async def start(self):
        """Start the scheduler loop."""
        self.running = True
        logger.info(f"Decay Scheduler started (interval: {self.interval_hours}h, batch: {self.batch_size})")

        while self.running:
            try:
                await self.run_decay_cycle()
                self.last_run = datetime.now()

                # Sleep until next cycle
                await asyncio.sleep(self.interval_hours * 3600)

            except Exception as e:
                logger.error(f"Error in decay cycle: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Decay Scheduler stopped")

    async def run_decay_cycle(self):
        """
        Run one complete decay cycle.

        Steps:
        1. Schedule memories for decay
        2. Process scheduled decay operations
        3. Update statistics
        4. Log results
        """
        cycle_start = datetime.now()
        logger.info("=== Starting Decay Cycle ===")

        try:
            # Step 1: Schedule decay operations
            logger.info(f"Scheduling decay batch (size: {self.batch_size})...")
            scheduled_ids = await self.decay_service.schedule_decay_batch(self.batch_size)
            logger.info(f"Scheduled {len(scheduled_ids)} memories for decay")

            # Step 2: Process scheduled operations
            logger.info("Processing decay schedule...")
            process_result = await self.decay_service.process_decay_schedule()

            # Step 3: Update statistics
            self.stats['total_runs'] += 1
            self.stats['total_memories_processed'] += process_result['processed']
            self.stats['total_tokens_saved'] += process_result['tokens_saved']
            self.stats['total_compressions'] += process_result['completed']

            # Step 4: Log results
            cycle_duration = (datetime.now() - cycle_start).total_seconds()

            logger.info(f"""
=== Decay Cycle Complete ===
Duration: {cycle_duration:.2f}s
Processed: {process_result['processed']} memories
Completed: {process_result['completed']} compressions
Failed: {process_result['failed']} errors
Tokens Saved: {process_result['tokens_saved']:,}
            """.strip())

            if process_result['errors']:
                logger.warning(f"Errors occurred: {len(process_result['errors'])}")
                for error in process_result['errors'][:5]:  # Log first 5 errors
                    logger.warning(f"  - Memory {error['memory_id']}: {error['error']}")

            # Update daily metrics
            await self._update_daily_metrics(process_result)

        except Exception as e:
            logger.error(f"Decay cycle failed: {e}", exc_info=True)

    async def _update_daily_metrics(self, process_result: Dict):
        """Update token_economics table with today's metrics."""
        async with get_db_connection() as conn:
            # Get current memory counts
            focus_count = await conn.fetchval("SELECT COUNT(*) FROM focus_memory WHERE archived = FALSE")
            fresh_count = await conn.fetchval("SELECT COUNT(*) FROM fresh_memory WHERE expired = FALSE")
            longterm_count = await conn.fetchval("SELECT COUNT(*) FROM long_term_memory")
            procedural_count = await conn.fetchval("SELECT COUNT(*) FROM procedural_memory")
            shock_count = await conn.fetchval("SELECT COUNT(*) FROM shock_memory")

            # Calculate average compression ratio
            avg_compression = await conn.fetchval("""
                SELECT AVG(compression_ratio)
                FROM decay_schedule
                WHERE status = 'completed' AND DATE(processed_at) = CURRENT_DATE
            """) or 1.0

            # Update today's economics
            await conn.execute("""
                INSERT INTO token_economics (
                    date,
                    focus_count, fresh_count, longterm_count,
                    procedural_count, shock_count,
                    compression_ratio, updated_at
                ) VALUES (CURRENT_DATE, $1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (date) DO UPDATE SET
                    focus_count = EXCLUDED.focus_count,
                    fresh_count = EXCLUDED.fresh_count,
                    longterm_count = EXCLUDED.longterm_count,
                    procedural_count = EXCLUDED.procedural_count,
                    shock_count = EXCLUDED.shock_count,
                    compression_ratio = EXCLUDED.compression_ratio,
                    updated_at = NOW()
            """,
                focus_count or 0,
                fresh_count or 0,
                longterm_count or 0,
                procedural_count or 0,
                shock_count or 0,
                avg_compression
            )

    async def get_status(self) -> Dict:
        """Get current scheduler status and statistics."""
        status = {
            'running': self.running,
            'interval_hours': self.interval_hours,
            'batch_size': self.batch_size,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': (
                (self.last_run + timedelta(hours=self.interval_hours)).isoformat()
                if self.last_run else 'Pending'
            ),
            'statistics': self.stats.copy()
        }

        # Get pending decay count
        async with get_db_connection() as conn:
            pending_count = await conn.fetchval("""
                SELECT COUNT(*) FROM decay_schedule WHERE status = 'pending'
            """)
            status['pending_operations'] = pending_count

            # Get today's token savings
            today_savings = await conn.fetchval("""
                SELECT tokens_saved_by_decay
                FROM token_economics
                WHERE date = CURRENT_DATE
            """) or 0
            status['today_tokens_saved'] = today_savings

        return status

    async def force_run_now(self):
        """Force immediate decay cycle (for testing/manual triggers)."""
        logger.info("Manual decay cycle triggered")
        await self.run_decay_cycle()


# Singleton instance
_scheduler = None

def get_decay_scheduler(interval_hours: int = 6, batch_size: int = 100) -> DecayScheduler:
    """Get singleton DecayScheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DecayScheduler(interval_hours, batch_size)
    return _scheduler


# Standalone run mode
if __name__ == "__main__":
    async def main():
        scheduler = get_decay_scheduler()

        try:
            logger.info("Starting Decay Scheduler (standalone mode)")
            logger.info("Press Ctrl+C to stop")
            await scheduler.start()
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            await scheduler.stop()

    asyncio.run(main())
