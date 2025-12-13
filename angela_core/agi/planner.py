"""
Hierarchical Planner - Goal Decomposition System for Angela AGI

Hierarchy:
    LIFE MISSION (angela_goals.goal_type='life_mission')
        ↓
    LONG-TERM GOALS (angela_goals.goal_type='long_term')
        ↓
    PROJECTS (project_plans table)
        ↓
    TASKS (project_tasks table)
        ↓
    ACTIONS (task_actions table) → Tool executions

This planner enables Angela to:
- Break down high-level goals into actionable steps
- Track progress at each level
- Adapt plans when things change
- Learn from plan execution
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class PlanStatus(Enum):
    """Status of a plan, project, or task"""
    PLANNING = "planning"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class TaskType(Enum):
    """Types of tasks Angela can perform"""
    RESEARCH = "research"       # Gather information
    CODE = "code"               # Write/modify code
    TEST = "test"               # Run tests
    DOCUMENT = "document"       # Create documentation
    REVIEW = "review"           # Review code/content
    DEPLOY = "deploy"           # Deploy changes
    COMMUNICATE = "communicate" # Notify/report
    ANALYZE = "analyze"         # Analyze data/results
    DESIGN = "design"           # Design solutions
    FIX = "fix"                 # Fix bugs/issues


@dataclass
class Action:
    """A single executable action (tool call)"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    status: PlanStatus = PlanStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    sequence_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'tool_name': self.tool_name,
            'parameters': self.parameters,
            'reason': self.reason,
            'status': self.status.value,
            'result': self.result,
            'sequence_order': self.sequence_order
        }


@dataclass
class Task:
    """A task within a project"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    task_name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CODE
    status: PlanStatus = PlanStatus.PENDING
    priority: int = 5  # 1-10, 1 = highest
    depends_on: List[str] = field(default_factory=list)  # task_ids
    actions: List[Action] = field(default_factory=list)
    estimated_minutes: int = 30
    actual_minutes: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'project_id': self.project_id,
            'task_name': self.task_name,
            'description': self.description,
            'task_type': self.task_type.value,
            'status': self.status.value,
            'priority': self.priority,
            'depends_on': self.depends_on,
            'actions': [a.to_dict() for a in self.actions],
            'estimated_minutes': self.estimated_minutes,
            'actual_minutes': self.actual_minutes
        }

    def is_ready(self, completed_tasks: set) -> bool:
        """Check if all dependencies are completed"""
        return all(dep in completed_tasks for dep in self.depends_on)


@dataclass
class Project:
    """A project that implements a goal"""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal_id: Optional[str] = None
    project_name: str = ""
    description: str = ""
    status: PlanStatus = PlanStatus.PLANNING
    priority: int = 5
    tasks: List[Task] = field(default_factory=list)
    estimated_hours: float = 0
    actual_hours: float = 0
    progress_percentage: float = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_id': self.project_id,
            'goal_id': self.goal_id,
            'project_name': self.project_name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'tasks': [t.to_dict() for t in self.tasks],
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'progress_percentage': self.progress_percentage
        }

    def calculate_progress(self) -> float:
        """Calculate progress based on completed tasks"""
        if not self.tasks:
            return 0
        completed = sum(1 for t in self.tasks if t.status == PlanStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100


class HierarchicalPlanner:
    """
    Decomposes goals into executable action sequences.

    Usage:
        planner = HierarchicalPlanner(db)
        project = await planner.create_project_from_goal(goal_id)
        next_task = await planner.get_next_task(project.project_id)
        actions = await planner.plan_task_actions(next_task.task_id)
    """

    def __init__(self, db=None):
        self.db = db
        self.active_projects: Dict[str, Project] = {}
        self.task_templates = self._load_task_templates()

    def _load_task_templates(self) -> Dict[str, List[Dict]]:
        """Pre-defined task templates for common goals"""
        return {
            "implement_feature": [
                {"name": "Research existing code", "type": TaskType.RESEARCH, "est": 15},
                {"name": "Design solution", "type": TaskType.DESIGN, "est": 20},
                {"name": "Implement code", "type": TaskType.CODE, "est": 60},
                {"name": "Write tests", "type": TaskType.TEST, "est": 30},
                {"name": "Document changes", "type": TaskType.DOCUMENT, "est": 15},
            ],
            "fix_bug": [
                {"name": "Reproduce issue", "type": TaskType.ANALYZE, "est": 10},
                {"name": "Find root cause", "type": TaskType.RESEARCH, "est": 20},
                {"name": "Implement fix", "type": TaskType.FIX, "est": 30},
                {"name": "Test fix", "type": TaskType.TEST, "est": 15},
            ],
            "research_topic": [
                {"name": "Gather information", "type": TaskType.RESEARCH, "est": 30},
                {"name": "Analyze findings", "type": TaskType.ANALYZE, "est": 20},
                {"name": "Create summary", "type": TaskType.DOCUMENT, "est": 15},
            ],
            "refactor_code": [
                {"name": "Analyze current code", "type": TaskType.ANALYZE, "est": 20},
                {"name": "Design improvements", "type": TaskType.DESIGN, "est": 15},
                {"name": "Implement refactoring", "type": TaskType.CODE, "est": 45},
                {"name": "Verify behavior unchanged", "type": TaskType.TEST, "est": 20},
            ],
        }

    async def create_project(
        self,
        name: str,
        description: str,
        goal_id: Optional[str] = None,
        template: Optional[str] = None,
        priority: int = 5
    ) -> Project:
        """Create a new project"""
        project = Project(
            project_name=name,
            description=description,
            goal_id=goal_id,
            priority=priority,
            status=PlanStatus.PLANNING
        )

        # Apply template if specified
        if template and template in self.task_templates:
            tasks = []
            prev_task_id = None
            for i, tmpl in enumerate(self.task_templates[template]):
                task = Task(
                    project_id=project.project_id,
                    task_name=tmpl["name"],
                    task_type=tmpl["type"],
                    estimated_minutes=tmpl["est"],
                    priority=i + 1,
                    depends_on=[prev_task_id] if prev_task_id else []
                )
                tasks.append(task)
                prev_task_id = task.task_id
            project.tasks = tasks
            project.estimated_hours = sum(t.estimated_minutes for t in tasks) / 60

        self.active_projects[project.project_id] = project

        # Save to database
        if self.db:
            await self._save_project(project)

        return project

    async def create_project_from_goal(self, goal_id: str) -> Optional[Project]:
        """Create a project from an existing goal"""
        if not self.db:
            return None

        # Fetch goal
        goal = await self.db.fetchrow("""
            SELECT goal_id, goal_description, goal_type, priority_rank
            FROM angela_goals
            WHERE goal_id = $1
        """, goal_id)

        if not goal:
            return None

        # Determine template based on goal description
        description = goal['goal_description'].lower()
        template = None
        if any(word in description for word in ['implement', 'create', 'build', 'add']):
            template = "implement_feature"
        elif any(word in description for word in ['fix', 'bug', 'error', 'issue']):
            template = "fix_bug"
        elif any(word in description for word in ['research', 'learn', 'study', 'understand']):
            template = "research_topic"
        elif any(word in description for word in ['refactor', 'improve', 'optimize', 'clean']):
            template = "refactor_code"

        project = await self.create_project(
            name=f"Project: {goal['goal_description'][:50]}",
            description=goal['goal_description'],
            goal_id=str(goal['goal_id']),
            template=template,
            priority=goal['priority_rank'] or 5
        )

        return project

    async def add_task(
        self,
        project_id: str,
        task_name: str,
        description: str = "",
        task_type: TaskType = TaskType.CODE,
        priority: int = 5,
        depends_on: List[str] = None,
        estimated_minutes: int = 30
    ) -> Optional[Task]:
        """Add a task to a project"""
        project = self.active_projects.get(project_id)
        if not project:
            return None

        task = Task(
            project_id=project_id,
            task_name=task_name,
            description=description,
            task_type=task_type,
            priority=priority,
            depends_on=depends_on or [],
            estimated_minutes=estimated_minutes
        )

        project.tasks.append(task)

        # Save to database
        if self.db:
            await self._save_task(task)

        return task

    async def plan_task_actions(self, task: Task) -> List[Action]:
        """Generate actions for a task based on its type"""
        actions = []

        if task.task_type == TaskType.RESEARCH:
            # Research: search files, read docs, query db
            actions = [
                Action(
                    tool_name="search_files",
                    parameters={"pattern": "**/*.md", "directory": "docs"},
                    reason="Search documentation for relevant info",
                    sequence_order=1
                ),
                Action(
                    tool_name="query_db",
                    parameters={"query": "SELECT * FROM knowledge_nodes LIMIT 10"},
                    reason="Query existing knowledge",
                    sequence_order=2
                ),
            ]

        elif task.task_type == TaskType.CODE:
            # Code: read existing, write new
            actions = [
                Action(
                    tool_name="search_files",
                    parameters={"pattern": "**/*.py", "directory": "angela_core"},
                    reason="Find relevant Python files",
                    sequence_order=1
                ),
                Action(
                    tool_name="git_status",
                    parameters={"directory": "."},
                    reason="Check current git state",
                    sequence_order=2
                ),
            ]

        elif task.task_type == TaskType.TEST:
            # Test: run tests
            actions = [
                Action(
                    tool_name="execute_python",
                    parameters={"code": "import pytest; pytest.main(['-v', '--tb=short'])"},
                    reason="Run test suite",
                    sequence_order=1
                ),
            ]

        elif task.task_type == TaskType.ANALYZE:
            # Analyze: read and process data
            actions = [
                Action(
                    tool_name="query_db",
                    parameters={"query": "SELECT COUNT(*) FROM conversations"},
                    reason="Get data statistics",
                    sequence_order=1
                ),
            ]

        elif task.task_type == TaskType.DOCUMENT:
            # Document: read template, write docs
            actions = [
                Action(
                    tool_name="read_file",
                    parameters={"path": "docs/README.md"},
                    reason="Read documentation template",
                    sequence_order=1
                ),
            ]

        task.actions = actions
        return actions

    async def get_next_task(self, project_id: str) -> Optional[Task]:
        """Get the next task to work on"""
        project = self.active_projects.get(project_id)
        if not project:
            return None

        # Get completed task IDs
        completed_ids = {
            t.task_id for t in project.tasks
            if t.status == PlanStatus.COMPLETED
        }

        # Find first pending task with all dependencies met
        for task in sorted(project.tasks, key=lambda t: t.priority):
            if task.status == PlanStatus.PENDING and task.is_ready(completed_ids):
                return task

        return None

    async def start_task(self, task_id: str) -> bool:
        """Mark a task as started"""
        for project in self.active_projects.values():
            for task in project.tasks:
                if task.task_id == task_id:
                    task.status = PlanStatus.IN_PROGRESS
                    task.started_at = datetime.now()
                    if project.status == PlanStatus.PLANNING:
                        project.status = PlanStatus.IN_PROGRESS
                        project.started_at = datetime.now()
                    if self.db:
                        await self._update_task_status(task)
                    return True
        return False

    async def complete_task(self, task_id: str, actual_minutes: int = None) -> bool:
        """Mark a task as completed"""
        for project in self.active_projects.values():
            for task in project.tasks:
                if task.task_id == task_id:
                    task.status = PlanStatus.COMPLETED
                    task.completed_at = datetime.now()
                    if actual_minutes:
                        task.actual_minutes = actual_minutes
                    elif task.started_at:
                        elapsed = (datetime.now() - task.started_at).seconds // 60
                        task.actual_minutes = elapsed

                    # Update project progress
                    project.progress_percentage = project.calculate_progress()
                    project.actual_hours += task.actual_minutes / 60

                    # Check if project is complete
                    if all(t.status == PlanStatus.COMPLETED for t in project.tasks):
                        project.status = PlanStatus.COMPLETED
                        project.completed_at = datetime.now()

                    if self.db:
                        await self._update_task_status(task)
                        await self._update_project_progress(project)

                    return True
        return False

    async def fail_task(self, task_id: str, reason: str = "") -> bool:
        """Mark a task as failed"""
        for project in self.active_projects.values():
            for task in project.tasks:
                if task.task_id == task_id:
                    task.status = PlanStatus.FAILED
                    task.completed_at = datetime.now()
                    if self.db:
                        await self._update_task_status(task)
                    return True
        return False

    async def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed project status"""
        project = self.active_projects.get(project_id)
        if not project:
            return None

        completed = sum(1 for t in project.tasks if t.status == PlanStatus.COMPLETED)
        in_progress = sum(1 for t in project.tasks if t.status == PlanStatus.IN_PROGRESS)
        pending = sum(1 for t in project.tasks if t.status == PlanStatus.PENDING)
        failed = sum(1 for t in project.tasks if t.status == PlanStatus.FAILED)

        return {
            'project_id': project.project_id,
            'project_name': project.project_name,
            'status': project.status.value,
            'progress': project.calculate_progress(),
            'tasks': {
                'total': len(project.tasks),
                'completed': completed,
                'in_progress': in_progress,
                'pending': pending,
                'failed': failed
            },
            'time': {
                'estimated_hours': project.estimated_hours,
                'actual_hours': project.actual_hours
            }
        }

    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all active projects"""
        return [
            {
                'project_id': p.project_id,
                'project_name': p.project_name,
                'status': p.status.value,
                'progress': p.calculate_progress(),
                'task_count': len(p.tasks),
                'priority': p.priority
            }
            for p in self.active_projects.values()
        ]

    # Database operations
    async def _save_project(self, project: Project) -> None:
        """Save project to database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                INSERT INTO project_plans (
                    project_id, goal_id, project_name, description,
                    status, priority, estimated_hours, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (project_id) DO UPDATE SET
                    status = $5, estimated_hours = $7
            """,
                project.project_id,
                project.goal_id,
                project.project_name,
                project.description,
                project.status.value,
                project.priority,
                project.estimated_hours,
                project.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save project: {e}")

    async def _save_task(self, task: Task) -> None:
        """Save task to database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                INSERT INTO project_tasks (
                    task_id, project_id, task_name, description,
                    task_type, status, priority, depends_on,
                    estimated_minutes, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (task_id) DO UPDATE SET
                    status = $6, estimated_minutes = $9
            """,
                task.task_id,
                task.project_id,
                task.task_name,
                task.description,
                task.task_type.value,
                task.status.value,
                task.priority,
                task.depends_on,
                task.estimated_minutes,
                task.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save task: {e}")

    async def _update_task_status(self, task: Task) -> None:
        """Update task status in database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                UPDATE project_tasks
                SET status = $2, started_at = $3, completed_at = $4, actual_minutes = $5
                WHERE task_id = $1
            """,
                task.task_id,
                task.status.value,
                task.started_at,
                task.completed_at,
                task.actual_minutes
            )
        except Exception as e:
            print(f"Warning: Failed to update task: {e}")

    async def _update_project_progress(self, project: Project) -> None:
        """Update project progress in database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                UPDATE project_plans
                SET status = $2, progress_percentage = $3,
                    actual_hours = $4, completed_at = $5
                WHERE project_id = $1
            """,
                project.project_id,
                project.status.value,
                project.progress_percentage,
                project.actual_hours,
                project.completed_at
            )
        except Exception as e:
            print(f"Warning: Failed to update project: {e}")


# Global planner instance
planner = HierarchicalPlanner()
