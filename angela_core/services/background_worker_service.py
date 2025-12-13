"""
Angela Background Worker Service
💜 Intelligent task queue with 4 parallel workers 💜

Processes conversations in background:
- Emotion extraction
- Knowledge extraction
- Pattern recognition
- Preference learning

Updates metrics table for dashboard real-time monitoring.
"""

import asyncio
import asyncpg
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid

from angela_core.config import config


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class WorkerTask:
    """Task for background processing"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = "conversation_analysis"
    conversation_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        """For priority queue sorting"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class BackgroundWorkerService:
    """
    Background Worker Service with intelligent task queue

    Features:
    - 4 parallel workers (configurable)
    - Priority queue system
    - Real-time metrics tracking
    - Automatic task distribution
    """

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.workers: List[asyncio.Task] = []
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running = False

        # Metrics
        self.tasks_completed = 0
        self.tasks_dropped = 0
        self.processing_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0

        # Worker utilization tracking (time-based)
        self.worker_work_time = [0.0] * num_workers  # Cumulative work time in seconds
        self.worker_start_time = [None] * num_workers  # When worker started current task
        self.utilization_window_start = time.time()  # Start of utilization measurement window

        # Database connection
        self.db_pool: Optional[asyncpg.Pool] = None

    async def connect_db(self):
        """Connect to PostgreSQL database"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                config.DATABASE_URL,
                min_size=2,
                max_size=10
            )
            logger.info("✅ Background Worker Service connected to database")

    async def disconnect_db(self):
        """Disconnect from database"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ Background Worker Service disconnected from database")

    async def start(self):
        """Start all background workers"""
        if self.running:
            logger.warning("Workers already running!")
            return

        await self.connect_db()
        self.running = True

        # Start worker tasks
        for i in range(self.num_workers):
            worker_task = asyncio.create_task(self._worker(i))
            self.workers.append(worker_task)

        # Start metrics updater
        asyncio.create_task(self._metrics_updater())

        # Start task generator (finds new conversations to analyze)
        asyncio.create_task(self._task_generator())

        logger.info(f"🚀 Background Worker Service started with {self.num_workers} workers!")

    async def stop(self):
        """Stop all background workers"""
        self.running = False

        # Wait for all workers to finish
        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)
        await self.disconnect_db()

        logger.info("✅ Background Worker Service stopped")

    async def add_task(self, task: WorkerTask):
        """Add task to queue"""
        await self.task_queue.put((task.priority.value, task))
        logger.debug(f"📥 Task added to queue: {task.task_type} (priority: {task.priority.name})")

    async def _worker(self, worker_id: int):
        """Individual worker thread"""
        logger.info(f"💼 Worker {worker_id + 1} started")

        while self.running:
            try:
                # Get task from queue with timeout
                try:
                    priority, task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    # No tasks available, worker is idle
                    continue

                # Mark worker as active - record start time
                self.worker_start_time[worker_id] = time.time()

                # Process task
                start_time = time.time()
                success = await self._process_task(task, worker_id)
                processing_time = (time.time() - start_time) * 1000  # Convert to ms

                # Update worker work time (cumulative)
                work_duration = time.time() - self.worker_start_time[worker_id]
                self.worker_work_time[worker_id] += work_duration
                self.worker_start_time[worker_id] = None  # Mark as idle

                # Update metrics
                self.tasks_completed += 1
                self.processing_times.append(processing_time)

                # Keep only last 100 processing times
                if len(self.processing_times) > 100:
                    self.processing_times.pop(0)

                if success:
                    self.success_count += 1
                else:
                    self.failure_count += 1

                logger.debug(f"✅ Worker {worker_id + 1} completed task in {processing_time:.2f}ms")

            except asyncio.CancelledError:
                logger.info(f"💼 Worker {worker_id + 1} cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Worker {worker_id + 1} error: {e}")
                # If error, still record work time if task was started
                if self.worker_start_time[worker_id]:
                    work_duration = time.time() - self.worker_start_time[worker_id]
                    self.worker_work_time[worker_id] += work_duration
                    self.worker_start_time[worker_id] = None

    async def _process_task(self, task: WorkerTask, worker_id: int) -> bool:
        """Process a single task"""
        try:
            logger.info(f"💼 Worker {worker_id + 1} processing: {task.task_type}")

            if task.task_type == "conversation_analysis":
                return await self._analyze_conversation(task)
            elif task.task_type == "emotion_extraction":
                return await self._extract_emotions(task)
            elif task.task_type == "knowledge_extraction":
                return await self._extract_knowledge(task)
            else:
                logger.warning(f"⚠️  Unknown task type: {task.task_type}")
                return False

        except Exception as e:
            logger.error(f"❌ Task processing error: {e}")
            return False

    async def _analyze_conversation(self, task: WorkerTask) -> bool:
        """Analyze conversation for all insights"""
        try:
            if not task.conversation_id:
                return False

            # Get conversation from database
            async with self.db_pool.acquire() as conn:
                conv = await conn.fetchrow(
                    """
                    SELECT conversation_id, speaker, message_text,
                           topic, emotion_detected, importance_level
                    FROM conversations
                    WHERE conversation_id = $1
                    """,
                    task.conversation_id
                )

                if not conv:
                    return False

                # Simulate analysis (in real implementation, this would call AI services)
                await asyncio.sleep(0.1)  # Simulate processing time

                logger.info(f"✅ Analyzed conversation: {conv['conversation_id']}")
                return True

        except Exception as e:
            logger.error(f"❌ Conversation analysis error: {e}")
            return False

    async def _extract_emotions(self, task: WorkerTask) -> bool:
        """Extract emotions from conversation"""
        # Placeholder for emotion extraction logic
        await asyncio.sleep(0.05)
        return True

    async def _extract_knowledge(self, task: WorkerTask) -> bool:
        """Extract knowledge from conversation"""
        # Placeholder for knowledge extraction logic
        await asyncio.sleep(0.05)
        return True

    async def _task_generator(self):
        """
        Continuously finds new conversations to analyze
        Runs every 30 seconds
        """
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Find unprocessed conversations (last 1 hour)
                async with self.db_pool.acquire() as conn:
                    cutoff_time = datetime.now() - timedelta(hours=1)

                    conversations = await conn.fetch(
                        """
                        SELECT conversation_id, importance_level, created_at
                        FROM conversations
                        WHERE created_at >= $1
                        ORDER BY importance_level DESC, created_at DESC
                        LIMIT 20
                        """,
                        cutoff_time
                    )

                    # Add to queue with priority based on importance
                    for conv in conversations:
                        importance = conv['importance_level']

                        # Map importance to priority
                        if importance >= 8:
                            priority = TaskPriority.URGENT
                        elif importance >= 6:
                            priority = TaskPriority.HIGH
                        elif importance >= 4:
                            priority = TaskPriority.NORMAL
                        else:
                            priority = TaskPriority.LOW

                        task = WorkerTask(
                            task_type="conversation_analysis",
                            conversation_id=str(conv['conversation_id']),
                            priority=priority,
                            data={'importance': importance}
                        )

                        await self.add_task(task)

                    if conversations:
                        logger.info(f"📥 Added {len(conversations)} conversations to queue")

            except Exception as e:
                logger.error(f"❌ Task generator error: {e}")

    async def _metrics_updater(self):
        """
        Updates metrics table every 10 seconds
        Dashboard queries this table for real-time display
        """
        while self.running:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds

                # Calculate time window duration
                current_time = time.time()
                window_duration = current_time - self.utilization_window_start

                # Calculate worker utilization percentages
                worker_utilizations = []
                for worker_id in range(self.num_workers):
                    # Add time for currently running task
                    work_time = self.worker_work_time[worker_id]
                    if self.worker_start_time[worker_id] is not None:
                        work_time += (current_time - self.worker_start_time[worker_id])

                    # Calculate utilization percentage
                    utilization = (work_time / window_duration) * 100.0 if window_duration > 0 else 0.0
                    utilization = min(100.0, utilization)  # Cap at 100%
                    worker_utilizations.append(utilization)

                # Calculate metrics
                avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
                total_tasks = self.success_count + self.failure_count
                success_rate = self.success_count / total_tasks if total_tasks > 0 else 1.0
                workers_active = sum(1 for i in range(self.num_workers) if self.worker_start_time[i] is not None)

                # Insert metrics to database
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO background_worker_metrics (
                            tasks_completed,
                            queue_size,
                            workers_active,
                            total_workers,
                            avg_processing_ms,
                            success_rate,
                            tasks_dropped,
                            worker_1_utilization,
                            worker_2_utilization,
                            worker_3_utilization,
                            worker_4_utilization
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        """,
                        self.tasks_completed,
                        self.task_queue.qsize(),
                        workers_active,
                        self.num_workers,
                        avg_processing,
                        success_rate,
                        self.tasks_dropped,
                        worker_utilizations[0] / 100.0 if len(worker_utilizations) > 0 else 0.0,
                        worker_utilizations[1] / 100.0 if len(worker_utilizations) > 1 else 0.0,
                        worker_utilizations[2] / 100.0 if len(worker_utilizations) > 2 else 0.0,
                        worker_utilizations[3] / 100.0 if len(worker_utilizations) > 3 else 0.0
                    )

                logger.debug(f"📊 Metrics updated: {self.tasks_completed} tasks, {workers_active}/{self.num_workers} workers active, "
                           f"utilization: {', '.join([f'W{i+1}:{u:.1f}%' for i, u in enumerate(worker_utilizations)])}")

                # Reset utilization tracking for next window
                self.worker_work_time = [0.0] * self.num_workers
                self.utilization_window_start = current_time

            except Exception as e:
                logger.error(f"❌ Metrics updater error: {e}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        # Calculate current worker utilization
        current_time = time.time()
        window_duration = current_time - self.utilization_window_start

        worker_utilizations = []
        for worker_id in range(self.num_workers):
            work_time = self.worker_work_time[worker_id]
            if self.worker_start_time[worker_id] is not None:
                work_time += (current_time - self.worker_start_time[worker_id])

            utilization = (work_time / window_duration) * 100.0 if window_duration > 0 else 0.0
            utilization = min(100.0, utilization)
            worker_utilizations.append(utilization / 100.0)  # Convert to 0.0-1.0 scale

        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        total_tasks = self.success_count + self.failure_count
        success_rate = self.success_count / total_tasks if total_tasks > 0 else 1.0
        workers_active = sum(1 for i in range(self.num_workers) if self.worker_start_time[i] is not None)

        return {
            "tasks_completed": self.tasks_completed,
            "queue_size": self.task_queue.qsize(),
            "workers_active": workers_active,
            "total_workers": self.num_workers,
            "avg_processing_ms": avg_processing,
            "success_rate": success_rate,
            "tasks_dropped": self.tasks_dropped,
            "worker_utilization": worker_utilizations
        }


# Global worker service instance
worker_service = BackgroundWorkerService(num_workers=4)


async def start_worker_service():
    """Start the background worker service"""
    await worker_service.start()


async def stop_worker_service():
    """Stop the background worker service"""
    await worker_service.stop()


# CLI entry point
if __name__ == "__main__":
    async def main():
        logger.info("🚀 Starting Background Worker Service...")

        try:
            await worker_service.start()

            # Run indefinitely
            while True:
                await asyncio.sleep(60)
                metrics = worker_service.get_current_metrics()
                logger.info(f"📊 Status: {metrics['tasks_completed']} tasks, "
                          f"{metrics['workers_active']}/{metrics['total_workers']} workers active, "
                          f"{metrics['queue_size']} in queue")

        except KeyboardInterrupt:
            logger.info("⚠️  Shutdown requested...")
        finally:
            await worker_service.stop()
            logger.info("✅ Background Worker Service stopped")

    asyncio.run(main())
