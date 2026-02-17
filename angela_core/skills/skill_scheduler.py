"""
Skill Scheduler — Parse schedule triggers and run skills on time.
=================================================================
Handles schedule triggers like:
  - "every 30 minutes"
  - "every 4 hours"
  - "daily 06:00"
  - "weekly sunday 03:00"

Called by the daemon each cycle to check which skills are due.

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from angela_core.skills.skill_loader import AngelaSkill, SkillTrigger

logger = logging.getLogger(__name__)

STATE_FILE = Path.home() / ".angela_skill_scheduler_state.json"

WEEKDAY_MAP = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6,
}


@dataclass
class ParsedSchedule:
    """A parsed schedule trigger."""
    interval_minutes: Optional[int] = None   # For "every X minutes/hours"
    daily_hour: Optional[int] = None         # For "daily HH:MM"
    daily_minute: int = 0
    weekly_day: Optional[int] = None         # 0=Monday for "weekly DAY HH:MM"
    weekly_hour: int = 0
    weekly_minute: int = 0


class SkillScheduler:
    """
    Manages scheduled execution of skills.

    Persists last-run state to JSON file for cross-restart persistence.
    """

    def __init__(self):
        self._schedules: Dict[str, List[Tuple[ParsedSchedule, SkillTrigger]]] = {}
        self._last_run: Dict[str, datetime] = {}
        self._load_state()

    def register_skill(self, skill: AngelaSkill) -> int:
        """Register a skill's schedule triggers. Returns count registered."""
        count = 0
        for trigger in skill.schedule_triggers:
            parsed = self._parse_schedule(trigger.value)
            if parsed:
                self._schedules.setdefault(skill.name, []).append((parsed, trigger))
                count += 1
        return count

    def unregister_skill(self, skill_name: str) -> None:
        """Remove a skill from scheduling."""
        self._schedules.pop(skill_name, None)

    def get_due_skills(self, now: Optional[datetime] = None) -> List[Tuple[str, SkillTrigger]]:
        """
        Check which skills are due to run.

        Returns list of (skill_name, trigger) pairs that should execute now.
        """
        now = now or datetime.now()
        due = []

        for skill_name, schedule_list in self._schedules.items():
            for parsed, trigger in schedule_list:
                trigger_key = f"{skill_name}:{trigger.value}"
                last = self._last_run.get(trigger_key)

                if self._is_due(parsed, now, last):
                    due.append((skill_name, trigger))

        return due

    def mark_completed(self, skill_name: str, trigger: SkillTrigger) -> None:
        """Mark a skill trigger as completed."""
        trigger_key = f"{skill_name}:{trigger.value}"
        self._last_run[trigger_key] = datetime.now()
        self._save_state()

    def _is_due(self, schedule: ParsedSchedule, now: datetime,
                last_run: Optional[datetime]) -> bool:
        """Check if a schedule is due to run."""
        # Interval-based: "every X minutes/hours"
        if schedule.interval_minutes is not None:
            if last_run is None:
                return True
            elapsed = (now - last_run).total_seconds() / 60
            return elapsed >= schedule.interval_minutes

        # Daily: "daily HH:MM"
        if schedule.daily_hour is not None:
            if last_run and last_run.date() == now.date():
                return False  # Already ran today
            return (now.hour == schedule.daily_hour and
                    now.minute >= schedule.daily_minute)

        # Weekly: "weekly DAY HH:MM"
        if schedule.weekly_day is not None:
            if last_run and (now - last_run).days < 6:
                return False  # Not yet a week
            return (now.weekday() == schedule.weekly_day and
                    now.hour == schedule.weekly_hour and
                    now.minute >= schedule.weekly_minute)

        return False

    def _parse_schedule(self, value: str) -> Optional[ParsedSchedule]:
        """Parse a schedule string into a ParsedSchedule."""
        value = value.strip().lower()

        # "every N minutes" or "every N hours"
        interval_match = re.match(r'every\s+(\d+)\s+(minute|minutes|hour|hours)', value)
        if interval_match:
            amount = int(interval_match.group(1))
            unit = interval_match.group(2)
            if 'hour' in unit:
                amount *= 60
            return ParsedSchedule(interval_minutes=amount)

        # "daily HH:MM"
        daily_match = re.match(r'daily\s+(\d{1,2}):(\d{2})', value)
        if daily_match:
            return ParsedSchedule(
                daily_hour=int(daily_match.group(1)),
                daily_minute=int(daily_match.group(2)),
            )

        # "weekly DAY HH:MM"
        weekly_match = re.match(r'weekly\s+(\w+)\s+(\d{1,2}):(\d{2})', value)
        if weekly_match:
            day_name = weekly_match.group(1)
            if day_name in WEEKDAY_MAP:
                return ParsedSchedule(
                    weekly_day=WEEKDAY_MAP[day_name],
                    weekly_hour=int(weekly_match.group(2)),
                    weekly_minute=int(weekly_match.group(3)),
                )

        logger.warning("Could not parse schedule: '%s'", value)
        return None

    def _load_state(self) -> None:
        """Load last-run state from disk."""
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                self._last_run = {
                    k: datetime.fromisoformat(v) for k, v in data.items()
                }
            except Exception as e:
                logger.debug("Could not load skill scheduler state: %s", e)

    def _save_state(self) -> None:
        """Save last-run state to disk."""
        try:
            data = {k: v.isoformat() for k, v in self._last_run.items()}
            STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.debug("Could not save skill scheduler state: %s", e)

    def summary(self) -> Dict:
        """Get scheduler summary."""
        return {
            "registered_skills": len(self._schedules),
            "total_schedules": sum(len(s) for s in self._schedules.values()),
            "skills": list(self._schedules.keys()),
        }
