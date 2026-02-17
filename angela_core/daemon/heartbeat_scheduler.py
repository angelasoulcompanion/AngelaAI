"""
Heartbeat Scheduler — Parse HEARTBEAT.md and determine which tasks are due.
============================================================================
Replaces 25+ `should_run_X()` methods with a single HEARTBEAT.md config file.

Usage:
    scheduler = HeartbeatScheduler()
    scheduler.load()  # Parse HEARTBEAT.md

    due_tasks = scheduler.get_due_tasks()
    for task in due_tasks:
        await handlers.run(task.name)
        scheduler.mark_completed(task.name)

State persisted in ~/.angela_heartbeat_state.json

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

HEARTBEAT_PATH = Path(__file__).parent.parent.parent / "HEARTBEAT.md"
STATE_FILE = Path.home() / ".angela_heartbeat_state.json"

WEEKDAY_MAP = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6,
}


@dataclass
class ScheduledTask:
    """A task parsed from HEARTBEAT.md."""
    name: str
    description: str
    schedule_type: str           # 'interval', 'daily', 'weekly', 'sequential'
    interval_minutes: int = 0    # For interval type
    daily_hour: int = 0          # For daily type
    daily_minute: int = 0
    weekly_day: int = 0          # 0=Monday
    weekly_hour: int = 0
    weekly_minute: int = 0
    parallel_safe: bool = True
    is_sequential: bool = False  # Runs in sequential phase


class HeartbeatScheduler:
    """
    Parses HEARTBEAT.md and determines which tasks are due.

    Persists last-run timestamps to JSON for cross-restart persistence.
    """

    def __init__(self, heartbeat_path: Optional[Path] = None):
        self._path = heartbeat_path or HEARTBEAT_PATH
        self._tasks: Dict[str, ScheduledTask] = {}
        self._last_run: Dict[str, datetime] = {}
        self._loaded = False

    def load(self) -> int:
        """Parse HEARTBEAT.md and load state. Returns task count."""
        self._tasks.clear()

        if not self._path.exists():
            logger.warning("HEARTBEAT.md not found at %s", self._path)
            return 0

        content = self._path.read_text(encoding='utf-8')
        self._parse(content)
        self._load_state()
        self._loaded = True

        logger.info("Heartbeat loaded: %d tasks from %s", len(self._tasks), self._path)
        return len(self._tasks)

    def get_due_tasks(self, now: Optional[datetime] = None) -> List[ScheduledTask]:
        """Get all tasks that are due to run now."""
        now = now or datetime.now()
        due = []

        for task in self._tasks.values():
            if task.is_sequential:
                continue  # Sequential tasks always run, handled separately
            if self._is_due(task, now):
                due.append(task)

        return due

    def get_sequential_tasks(self) -> List[ScheduledTask]:
        """Get tasks that run in the sequential phase (every cycle)."""
        return [t for t in self._tasks.values() if t.is_sequential]

    def get_parallel_tasks(self, due_tasks: List[ScheduledTask]) -> Tuple[List[ScheduledTask], List[ScheduledTask]]:
        """Split due tasks into parallel-safe and sequential groups."""
        parallel = [t for t in due_tasks if t.parallel_safe]
        sequential = [t for t in due_tasks if not t.parallel_safe]
        return parallel, sequential

    def mark_completed(self, task_name: str) -> None:
        """Mark a task as completed with current timestamp."""
        self._last_run[task_name] = datetime.now()
        self._save_state()

    def get_task(self, name: str) -> Optional[ScheduledTask]:
        """Get a task by name."""
        return self._tasks.get(name)

    @property
    def task_names(self) -> List[str]:
        return list(self._tasks.keys())

    def _is_due(self, task: ScheduledTask, now: datetime) -> bool:
        """Check if a task is due to run."""
        last = self._last_run.get(task.name)

        if task.schedule_type == 'interval':
            if last is None:
                return True
            elapsed = (now - last).total_seconds() / 60
            return elapsed >= task.interval_minutes

        elif task.schedule_type == 'daily':
            if last and last.date() == now.date():
                return False  # Already ran today
            return (now.hour == task.daily_hour and
                    now.minute >= task.daily_minute)

        elif task.schedule_type == 'weekly':
            if last and (now - last).days < 6:
                return False
            return (now.weekday() == task.weekly_day and
                    now.hour == task.weekly_hour and
                    now.minute >= task.weekly_minute)

        return False

    def _parse(self, content: str) -> None:
        """Parse HEARTBEAT.md content."""
        lines = content.strip().split('\n')
        current_schedule = None
        is_sequential = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('>'):
                continue

            # Section headers: ## Every 30 minutes, ## Daily 06:00, etc.
            if stripped.startswith('## '):
                section = stripped[3:].strip()
                current_schedule = self._parse_section_header(section)
                is_sequential = 'sequential' in section.lower()
                continue

            # Task entries: - task_name: Description (parallel_safe: true)
            if stripped.startswith('- ') and current_schedule and ':' in stripped:
                self._parse_task_entry(stripped, current_schedule, is_sequential)

    def _parse_section_header(self, header: str) -> Optional[Dict]:
        """Parse section header into schedule params."""
        header_lower = header.lower()

        # "Every N minutes/hours"
        interval_match = re.match(r'every\s+(\d+)\s+(minute|minutes|hour|hours)', header_lower)
        if interval_match:
            amount = int(interval_match.group(1))
            unit = interval_match.group(2)
            if 'hour' in unit:
                amount *= 60
            return {'type': 'interval', 'interval_minutes': amount}

        # "Daily HH:MM"
        daily_match = re.match(r'daily\s+(\d{1,2}):(\d{2})', header_lower)
        if daily_match:
            return {
                'type': 'daily',
                'hour': int(daily_match.group(1)),
                'minute': int(daily_match.group(2)),
            }

        # "Weekly DAY HH:MM"
        weekly_match = re.match(r'weekly\s+(\w+)\s+(\d{1,2}):(\d{2})', header_lower)
        if weekly_match:
            day = WEEKDAY_MAP.get(weekly_match.group(1))
            if day is not None:
                return {
                    'type': 'weekly',
                    'day': day,
                    'hour': int(weekly_match.group(2)),
                    'minute': int(weekly_match.group(3)),
                }

        # "Sequential"
        if 'sequential' in header_lower:
            return {'type': 'sequential'}

        return None

    def _parse_task_entry(self, line: str, schedule: Dict, is_sequential: bool) -> None:
        """Parse a task entry line."""
        # Strip "- " prefix
        content = line[2:].strip()

        # Split name: description (parallel_safe: X)
        parts = content.split(':', 1)
        if len(parts) < 2:
            return

        name = parts[0].strip()
        rest = parts[1].strip()

        # Extract parallel_safe flag
        parallel_safe = True
        ps_match = re.search(r'\(parallel_safe:\s*(true|false)\)', rest, re.IGNORECASE)
        if ps_match:
            parallel_safe = ps_match.group(1).lower() == 'true'
            rest = rest[:ps_match.start()].strip()

        description = rest

        stype = schedule.get('type', 'interval')

        task = ScheduledTask(
            name=name,
            description=description,
            schedule_type=stype if not is_sequential else 'sequential',
            interval_minutes=schedule.get('interval_minutes', 0),
            daily_hour=schedule.get('hour', 0),
            daily_minute=schedule.get('minute', 0),
            weekly_day=schedule.get('day', 0),
            weekly_hour=schedule.get('hour', 0),
            weekly_minute=schedule.get('minute', 0),
            parallel_safe=parallel_safe,
            is_sequential=is_sequential or stype == 'sequential',
        )

        self._tasks[name] = task

    def _load_state(self) -> None:
        """Load last-run timestamps from disk."""
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                self._last_run = {
                    k: datetime.fromisoformat(v) for k, v in data.items()
                }
            except Exception as e:
                logger.debug("Could not load heartbeat state: %s", e)

    def _save_state(self) -> None:
        """Persist last-run timestamps to disk."""
        try:
            data = {k: v.isoformat() for k, v in self._last_run.items()}
            STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.debug("Could not save heartbeat state: %s", e)

    def summary(self) -> Dict:
        """Get scheduler summary."""
        by_type = {}
        for task in self._tasks.values():
            by_type.setdefault(task.schedule_type, []).append(task.name)

        return {
            "total_tasks": len(self._tasks),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "tasks": {t.name: t.schedule_type for t in self._tasks.values()},
            "loaded": self._loaded,
        }
