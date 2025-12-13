"""
Task Scheduler - Intelligent task prioritization for Angela AGI

Features:
- Priority-based scheduling across all projects
- Dependency resolution
- Workload balancing
- Deadline awareness
- Context-aware task selection
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from .planner import (
    HierarchicalPlanner, Project, Task, Action,
    PlanStatus, TaskType, planner
)


class SchedulePriority(Enum):
    """Priority levels for scheduling"""
    CRITICAL = 1    # Must do now
    HIGH = 2        # Do today
    MEDIUM = 3      # Do this week
    LOW = 4         # Do when possible
    BACKLOG = 5     # Maybe later


@dataclass
class ScheduledTask:
    """A task with scheduling metadata"""
    task: Task
    project: Project
    effective_priority: float  # Calculated priority score
    reason: str               # Why this priority
    estimated_start: Optional[datetime] = None
    deadline: Optional[datetime] = None


class TaskScheduler:
    """
    Schedules and prioritizes tasks across all projects.

    Priority is calculated based on:
    - Project priority (goal importance)
    - Task priority within project
    - Dependencies (blocked tasks have lower priority)
    - Time sensitivity (deadlines)
    - Task type (some types may be preferred)
    - Context (what Angela was just working on)

    Usage:
        scheduler = TaskScheduler(planner)
        next_task = await scheduler.get_next_task()
        schedule = await scheduler.get_schedule(hours=8)
    """

    def __init__(self, planner_instance: HierarchicalPlanner = None):
        self.planner = planner_instance or planner
        self.current_context: Dict[str, Any] = {}
        self.completed_today: List[str] = []
        self.work_session_start: Optional[datetime] = None

    async def get_next_task(self, context: Dict[str, Any] = None) -> Optional[ScheduledTask]:
        """
        Get the highest priority task to work on next.

        Args:
            context: Optional context (current topic, mood, etc.)

        Returns:
            ScheduledTask with the highest priority task
        """
        if context:
            self.current_context = context

        # Get all ready tasks from all projects
        ready_tasks = await self._get_all_ready_tasks()

        if not ready_tasks:
            return None

        # Score and sort tasks
        scored_tasks = []
        for task, project in ready_tasks:
            score, reason = self._calculate_priority(task, project)
            scored_tasks.append(ScheduledTask(
                task=task,
                project=project,
                effective_priority=score,
                reason=reason
            ))

        # Sort by priority (lower score = higher priority)
        scored_tasks.sort(key=lambda t: t.effective_priority)

        return scored_tasks[0] if scored_tasks else None

    async def get_schedule(
        self,
        hours: int = 8,
        max_tasks: int = 10
    ) -> List[ScheduledTask]:
        """
        Generate a schedule for the next N hours.

        Args:
            hours: Number of hours to schedule
            max_tasks: Maximum number of tasks to include

        Returns:
            List of scheduled tasks in order
        """
        schedule = []
        available_minutes = hours * 60
        used_minutes = 0

        # Get all ready tasks
        ready_tasks = await self._get_all_ready_tasks()

        # Score and sort
        scored_tasks = []
        for task, project in ready_tasks:
            score, reason = self._calculate_priority(task, project)
            scored_tasks.append(ScheduledTask(
                task=task,
                project=project,
                effective_priority=score,
                reason=reason
            ))

        scored_tasks.sort(key=lambda t: t.effective_priority)

        # Fill schedule
        current_time = datetime.now()
        for scheduled in scored_tasks:
            if len(schedule) >= max_tasks:
                break

            task_minutes = scheduled.task.estimated_minutes
            if used_minutes + task_minutes <= available_minutes:
                scheduled.estimated_start = current_time + timedelta(minutes=used_minutes)
                schedule.append(scheduled)
                used_minutes += task_minutes

        return schedule

    async def _get_all_ready_tasks(self) -> List[tuple]:
        """Get all tasks that are ready to work on"""
        ready_tasks = []

        for project in self.planner.active_projects.values():
            if project.status in [PlanStatus.PLANNING, PlanStatus.IN_PROGRESS]:
                # Get completed task IDs
                completed_ids = {
                    t.task_id for t in project.tasks
                    if t.status == PlanStatus.COMPLETED
                }

                # Find ready tasks
                for task in project.tasks:
                    if (task.status == PlanStatus.PENDING and
                        task.is_ready(completed_ids)):
                        ready_tasks.append((task, project))

        return ready_tasks

    def _calculate_priority(
        self,
        task: Task,
        project: Project
    ) -> tuple:
        """
        Calculate effective priority score for a task.

        Lower score = higher priority

        Returns:
            (score, reason) tuple
        """
        # Base score from project and task priority
        # Project priority: 1-10, Task priority: 1-10
        base_score = (project.priority * 10) + task.priority

        # Adjustments
        adjustments = []

        # 1. Task type bonus (some types are more urgent)
        type_bonuses = {
            TaskType.FIX: -20,          # Fixes are urgent
            TaskType.TEST: -5,          # Tests should run early
            TaskType.DEPLOY: -10,       # Deployments are important
            TaskType.RESEARCH: +5,      # Research can wait
            TaskType.DOCUMENT: +10,     # Docs can wait more
        }
        if task.task_type in type_bonuses:
            bonus = type_bonuses[task.task_type]
            base_score += bonus
            if bonus < 0:
                adjustments.append(f"{task.task_type.value} gets priority boost")

        # 2. Context bonus (if similar to what we were just doing)
        if self.current_context:
            if self.current_context.get('last_task_type') == task.task_type:
                base_score -= 10
                adjustments.append("matches current context")

        # 3. First task of project gets small bonus (get started)
        if not any(t.status == PlanStatus.COMPLETED for t in project.tasks):
            base_score -= 5
            adjustments.append("first task in project")

        # 4. No dependencies left - ready to go
        if not task.depends_on:
            base_score -= 3
            adjustments.append("no dependencies")

        # 5. Short tasks get slight bonus (quick wins)
        if task.estimated_minutes <= 15:
            base_score -= 5
            adjustments.append("quick task")

        # Build reason string
        reason = f"Base: {project.priority}*10 + {task.priority}"
        if adjustments:
            reason += f" | Adjustments: {', '.join(adjustments)}"

        return (base_score, reason)

    async def start_work_session(self) -> Dict[str, Any]:
        """Start a new work session"""
        self.work_session_start = datetime.now()
        self.completed_today = []

        # Get schedule for session
        schedule = await self.get_schedule(hours=4)

        return {
            'session_start': self.work_session_start.isoformat(),
            'scheduled_tasks': len(schedule),
            'estimated_hours': sum(t.task.estimated_minutes for t in schedule) / 60,
            'first_task': schedule[0].task.task_name if schedule else None,
            'schedule': [
                {
                    'task_name': t.task.task_name,
                    'project_name': t.project.project_name,
                    'estimated_minutes': t.task.estimated_minutes,
                    'priority_score': t.effective_priority,
                    'reason': t.reason
                }
                for t in schedule
            ]
        }

    async def complete_current_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        Mark current task as done and get next task.

        Returns:
            Next scheduled task
        """
        # Complete the task
        success = await self.planner.complete_task(task_id)
        if success:
            self.completed_today.append(task_id)

        # Get next task
        return await self.get_next_task()

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for current work session"""
        if not self.work_session_start:
            return {'active': False}

        elapsed = (datetime.now() - self.work_session_start).seconds // 60

        return {
            'active': True,
            'started_at': self.work_session_start.isoformat(),
            'elapsed_minutes': elapsed,
            'tasks_completed': len(self.completed_today),
            'projects_active': len(self.planner.active_projects)
        }

    async def get_workload_summary(self) -> Dict[str, Any]:
        """Get summary of current workload"""
        total_tasks = 0
        pending_tasks = 0
        in_progress_tasks = 0
        completed_tasks = 0
        total_hours_estimated = 0
        total_hours_actual = 0

        for project in self.planner.active_projects.values():
            for task in project.tasks:
                total_tasks += 1
                if task.status == PlanStatus.PENDING:
                    pending_tasks += 1
                    total_hours_estimated += task.estimated_minutes / 60
                elif task.status == PlanStatus.IN_PROGRESS:
                    in_progress_tasks += 1
                elif task.status == PlanStatus.COMPLETED:
                    completed_tasks += 1
                    total_hours_actual += task.actual_minutes / 60

        return {
            'projects': len(self.planner.active_projects),
            'tasks': {
                'total': total_tasks,
                'pending': pending_tasks,
                'in_progress': in_progress_tasks,
                'completed': completed_tasks
            },
            'hours': {
                'estimated_remaining': round(total_hours_estimated, 1),
                'actual_completed': round(total_hours_actual, 1)
            },
            'completion_rate': (
                completed_tasks / total_tasks * 100 if total_tasks > 0 else 0
            )
        }


# Global scheduler instance
scheduler = TaskScheduler()
