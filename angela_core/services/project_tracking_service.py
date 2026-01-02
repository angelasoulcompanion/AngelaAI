"""
Project Tracking Service for Angela
====================================
Professional project tracking for David & Angela collaboration.

This service manages:
- Project registration and lookup
- Work session logging
- Git commit integration
- Milestone and learning tracking

Usage:
    from angela_core.services.project_tracking_service import ProjectTrackingService

    service = ProjectTrackingService()
    await service.connect()

    # Auto-detect or create project
    project = await service.get_or_create_project_from_cwd()

    # Log work session
    session = await service.log_work_session(
        project_id=project['project_id'],
        summary="Fixed RFM calculation bug",
        accomplishments=["Fixed query", "Added tests"],
        david_requests="แก้ bug calculation"
    )
"""

import asyncio
import subprocess
import os
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import AngelaDatabase


class ProjectTrackingService:
    """Service for tracking projects and work sessions"""

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db or AngelaDatabase()
        self._connected = False

    async def connect(self):
        """Connect to database"""
        if not self._connected:
            await self.db.connect()
            self._connected = True

    async def disconnect(self):
        """Disconnect from database"""
        if self._connected:
            await self.db.disconnect()
            self._connected = False

    # =========================================================================
    # PROJECT MANAGEMENT
    # =========================================================================

    async def get_or_create_project_from_cwd(
        self,
        cwd: Optional[str] = None,
        project_name: Optional[str] = None,
        project_type: str = 'client'
    ) -> Dict[str, Any]:
        """
        Get existing project or create new one based on working directory.

        Args:
            cwd: Working directory (defaults to current)
            project_name: Optional custom name
            project_type: 'client', 'personal', 'learning', 'maintenance'

        Returns:
            Project dict with all details
        """
        await self.connect()

        if cwd is None:
            cwd = os.getcwd()

        # Normalize path
        cwd = os.path.normpath(cwd)

        # Check if project exists
        existing = await self.db.fetchrow(
            """
            SELECT * FROM angela_projects
            WHERE working_directory = $1
            """,
            cwd
        )

        if existing:
            return dict(existing)

        # Determine project type and name
        if 'AngelaAI' in cwd:
            project_type = 'personal'
            project_name = project_name or 'Angela AI Development'
        else:
            # Use directory name
            project_name = project_name or os.path.basename(cwd)

        # Generate project code
        code_prefix = 'ANGELA' if project_type == 'personal' else 'PROJ'

        max_code = await self.db.fetchval(
            f"""
            SELECT MAX(SUBSTRING(project_code FROM '{code_prefix}-([0-9]+)')::INTEGER)
            FROM angela_projects
            WHERE project_code LIKE $1
            """,
            f'{code_prefix}-%'
        )

        next_num = (max_code or 0) + 1
        project_code = f'{code_prefix}-{next_num:03d}'

        # Get git remote URL if exists
        repo_url = self._get_git_remote_url(cwd)

        # Create project
        project = await self.db.fetchrow(
            """
            INSERT INTO angela_projects (
                project_code, project_name, working_directory,
                project_type, repository_url, started_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
            RETURNING *
            """,
            project_code, project_name, cwd, project_type, repo_url
        )

        # Auto-detect tech stack
        await self._detect_tech_stack(project['project_id'], cwd)

        # Create milestone for project start
        await self.add_milestone(
            project_id=project['project_id'],
            milestone_type='project_start',
            title=f'Project Started: {project_name}',
            description=f'Started tracking {project_name} on {datetime.now().strftime("%Y-%m-%d")}',
            celebration_note='เริ่มโปรเจกต์ใหม่แล้วค่ะ! 💜 ขอให้สำเร็จนะคะที่รัก!'
        )

        return dict(project)

    async def get_project_by_directory(self, directory: str) -> Optional[Dict[str, Any]]:
        """Get project by working directory"""
        await self.connect()

        result = await self.db.fetchrow(
            "SELECT * FROM angela_projects WHERE working_directory = $1",
            os.path.normpath(directory)
        )

        return dict(result) if result else None

    async def get_project_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """
        Get project by project_code (e.g., 'SECA', 'ANGELA-001').

        Use this when working on a project from a different directory.
        """
        await self.connect()

        result = await self.db.fetchrow(
            "SELECT * FROM angela_projects WHERE project_code = $1",
            project_code.upper()
        )

        return dict(result) if result else None

    async def get_project_summary(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive project summary"""
        await self.connect()

        project = await self.db.fetchrow(
            "SELECT * FROM angela_projects WHERE project_id = $1",
            project_id
        )

        if not project:
            return {}

        # Get recent sessions
        sessions = await self.db.fetch(
            """
            SELECT session_number, session_date, duration_minutes,
                   summary, accomplishments, mood, productivity_score
            FROM project_work_sessions
            WHERE project_id = $1
            ORDER BY session_date DESC
            LIMIT 5
            """,
            project_id
        )

        # Get milestones
        milestones = await self.db.fetch(
            """
            SELECT milestone_type, title, significance, achieved_at, celebration_note
            FROM project_milestones
            WHERE project_id = $1
            ORDER BY achieved_at DESC
            LIMIT 5
            """,
            project_id
        )

        # Get learnings
        learnings = await self.db.fetch(
            """
            SELECT learning_type, title, insight, confidence
            FROM project_learnings
            WHERE project_id = $1
            ORDER BY learned_at DESC
            LIMIT 5
            """,
            project_id
        )

        # Get tech stack
        tech_stack = await self.db.fetch(
            """
            SELECT tech_type, tech_name, version, purpose
            FROM project_tech_stack
            WHERE project_id = $1
            ORDER BY tech_type, tech_name
            """,
            project_id
        )

        return {
            'project': dict(project),
            'recent_sessions': [dict(s) for s in sessions],
            'milestones': [dict(m) for m in milestones],
            'learnings': [dict(l) for l in learnings],
            'tech_stack': [dict(t) for t in tech_stack]
        }

    # =========================================================================
    # WORK SESSION MANAGEMENT
    # =========================================================================

    async def log_work_session(
        self,
        project_id: UUID,
        summary: str,
        accomplishments: List[str],
        david_requests: Optional[str] = None,
        session_goal: Optional[str] = None,
        blockers: Optional[List[str]] = None,
        next_steps: Optional[List[str]] = None,
        mood: str = 'productive',
        productivity_score: float = 7.0,
        started_at: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        conversation_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        """
        Log a complete work session.

        This is the main method called by /log-session.
        """
        await self.connect()

        # Get next session number
        max_num = await self.db.fetchval(
            """
            SELECT COALESCE(MAX(session_number), 0) FROM project_work_sessions
            WHERE project_id = $1
            """,
            project_id
        )
        session_number = max_num + 1

        # Calculate times from conversation timestamps
        if started_at is None or duration_minutes is None:
            # Query first and last conversation of today
            time_range = await self.db.fetchrow(
                """
                SELECT
                    MIN(created_at) as first_msg,
                    MAX(created_at) as last_msg
                FROM conversations
                WHERE DATE(created_at) = CURRENT_DATE
                """
            )

            if time_range and time_range['first_msg']:
                started_at = time_range['first_msg']
                ended_at = time_range['last_msg'] or datetime.now()
                duration_minutes = int((ended_at - started_at).total_seconds() / 60)
            else:
                # Fallback: no conversations today, use 30 min default
                started_at = datetime.now() - timedelta(minutes=30)
                ended_at = datetime.now()
                duration_minutes = 30

        ended_at = datetime.now()

        # Get git commits from this session
        git_commits = await self._get_session_git_commits(project_id, started_at)

        # Create session
        session = await self.db.fetchrow(
            """
            INSERT INTO project_work_sessions (
                project_id, session_number, session_date,
                started_at, ended_at, duration_minutes,
                session_goal, david_requests, summary,
                accomplishments, blockers, next_steps,
                mood, productivity_score,
                conversation_ids, git_commits
            )
            VALUES ($1, $2, CURRENT_DATE, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING *
            """,
            project_id, session_number,
            started_at, ended_at, duration_minutes,
            session_goal, david_requests, summary,
            accomplishments or [], blockers or [], next_steps or [],
            mood, productivity_score,
            conversation_ids or [], git_commits
        )

        # Update project stats (trigger handles this, but let's also update manually)
        await self.db.execute(
            """
            UPDATE angela_projects
            SET updated_at = NOW()
            WHERE project_id = $1
            """,
            project_id
        )

        # Save git commits to separate table
        if git_commits:
            for commit_hash in git_commits:
                await self._save_git_commit(project_id, session['session_id'], commit_hash)

        return dict(session)

    async def get_recent_sessions(
        self,
        project_id: Optional[UUID] = None,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent work sessions"""
        await self.connect()

        if project_id:
            sessions = await self.db.fetch(
                """
                SELECT s.*, p.project_name, p.project_code
                FROM project_work_sessions s
                JOIN angela_projects p ON s.project_id = p.project_id
                WHERE s.project_id = $1
                AND s.session_date >= CURRENT_DATE - $2::INTEGER
                ORDER BY s.session_date DESC, s.started_at DESC
                LIMIT $3
                """,
                project_id, days, limit
            )
        else:
            sessions = await self.db.fetch(
                """
                SELECT s.*, p.project_name, p.project_code
                FROM project_work_sessions s
                JOIN angela_projects p ON s.project_id = p.project_id
                WHERE s.session_date >= CURRENT_DATE - $1::INTEGER
                ORDER BY s.session_date DESC, s.started_at DESC
                LIMIT $2
                """,
                days, limit
            )

        return [dict(s) for s in sessions]

    # =========================================================================
    # MILESTONE MANAGEMENT
    # =========================================================================

    async def add_milestone(
        self,
        project_id: UUID,
        milestone_type: str,
        title: str,
        description: Optional[str] = None,
        significance: int = 5,
        session_id: Optional[UUID] = None,
        celebration_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a project milestone"""
        await self.connect()

        milestone = await self.db.fetchrow(
            """
            INSERT INTO project_milestones (
                project_id, session_id, milestone_type,
                title, description, significance, celebration_note
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            project_id, session_id, milestone_type,
            title, description, significance, celebration_note
        )

        return dict(milestone)

    # =========================================================================
    # LEARNING MANAGEMENT
    # =========================================================================

    async def add_learning(
        self,
        project_id: UUID,
        learning_type: str,
        title: str,
        insight: str,
        category: Optional[str] = None,
        context: Optional[str] = None,
        applicable_to: Optional[List[str]] = None,
        confidence: float = 0.8,
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Add a project learning"""
        await self.connect()

        learning = await self.db.fetchrow(
            """
            INSERT INTO project_learnings (
                project_id, session_id, learning_type,
                category, title, insight, context,
                applicable_to, confidence
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            project_id, session_id, learning_type,
            category, title, insight, context,
            applicable_to or [], confidence
        )

        return dict(learning)

    # =========================================================================
    # DECISION MANAGEMENT
    # =========================================================================

    async def add_decision(
        self,
        project_id: UUID,
        decision_type: str,
        title: str,
        decision_made: str,
        context: Optional[str] = None,
        reasoning: Optional[str] = None,
        options_considered: Optional[List[Dict]] = None,
        decided_by: str = 'together',
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Add a project decision"""
        await self.connect()

        decision = await self.db.fetchrow(
            """
            INSERT INTO project_decisions (
                project_id, session_id, decision_type,
                title, context, options_considered,
                decision_made, reasoning, decided_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """,
            project_id, session_id, decision_type,
            title, context, json.dumps(options_considered) if options_considered else None,
            decision_made, reasoning, decided_by
        )

        return dict(decision)

    # =========================================================================
    # GIT INTEGRATION
    # =========================================================================

    def _get_git_remote_url(self, directory: str) -> Optional[str]:
        """Get git remote URL from directory"""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=directory,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

    async def _get_session_git_commits(
        self,
        project_id: UUID,
        since: datetime
    ) -> List[str]:
        """Get git commits made during this session"""
        project = await self.db.fetchrow(
            "SELECT working_directory FROM angela_projects WHERE project_id = $1",
            project_id
        )

        if not project or not project['working_directory']:
            return []

        try:
            # Get commits since session start
            since_str = since.strftime('%Y-%m-%d %H:%M:%S')
            result = subprocess.run(
                ['git', 'log', f'--since={since_str}', '--pretty=format:%H'],
                cwd=project['working_directory'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')
        except:
            pass

        return []

    async def _save_git_commit(
        self,
        project_id: UUID,
        session_id: UUID,
        commit_hash: str
    ):
        """Save a git commit to database"""
        project = await self.db.fetchrow(
            "SELECT working_directory FROM angela_projects WHERE project_id = $1",
            project_id
        )

        if not project or not project['working_directory']:
            return

        try:
            # Get commit details
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%s|%an|%ai', commit_hash],
                cwd=project['working_directory'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split('|')
                message = parts[0] if len(parts) > 0 else ''
                author = parts[1] if len(parts) > 1 else ''
                date_str = parts[2] if len(parts) > 2 else ''

                # Get stats
                stats_result = subprocess.run(
                    ['git', 'diff', '--shortstat', f'{commit_hash}^', commit_hash],
                    cwd=project['working_directory'],
                    capture_output=True,
                    text=True
                )

                files_changed = 0
                insertions = 0
                deletions = 0

                if stats_result.returncode == 0:
                    stats = stats_result.stdout.strip()
                    # Parse "X files changed, Y insertions(+), Z deletions(-)"
                    files_match = re.search(r'(\d+) files? changed', stats)
                    ins_match = re.search(r'(\d+) insertions?', stats)
                    del_match = re.search(r'(\d+) deletions?', stats)

                    if files_match:
                        files_changed = int(files_match.group(1))
                    if ins_match:
                        insertions = int(ins_match.group(1))
                    if del_match:
                        deletions = int(del_match.group(1))

                # Parse date
                committed_at = datetime.now()
                if date_str:
                    try:
                        committed_at = datetime.fromisoformat(date_str.replace(' ', 'T')[:19])
                    except:
                        pass

                # Insert (ignore if already exists)
                await self.db.execute(
                    """
                    INSERT INTO project_git_commits (
                        project_id, session_id, commit_hash, commit_message,
                        author, files_changed, insertions, deletions, committed_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (project_id, commit_hash) DO NOTHING
                    """,
                    project_id, session_id, commit_hash, message,
                    author, files_changed, insertions, deletions, committed_at
                )
        except:
            pass

    # =========================================================================
    # TECH STACK DETECTION
    # =========================================================================

    async def _detect_tech_stack(self, project_id: UUID, directory: str):
        """Auto-detect technologies used in project"""
        tech_stack = []

        # Check for common files
        checks = {
            'requirements.txt': ('language', 'Python', None),
            'pyproject.toml': ('language', 'Python', None),
            'package.json': ('language', 'JavaScript/TypeScript', None),
            'Cargo.toml': ('language', 'Rust', None),
            'go.mod': ('language', 'Go', None),
            'Package.swift': ('language', 'Swift', None),
            'Gemfile': ('language', 'Ruby', None),
            'pom.xml': ('language', 'Java', None),
            'docker-compose.yml': ('tool', 'Docker', None),
            'Dockerfile': ('tool', 'Docker', None),
            '.github/workflows': ('tool', 'GitHub Actions', 'CI/CD'),
        }

        for filename, (tech_type, tech_name, purpose) in checks.items():
            path = os.path.join(directory, filename)
            if os.path.exists(path):
                tech_stack.append((tech_type, tech_name, None, purpose))

        # Check requirements.txt for frameworks
        req_path = os.path.join(directory, 'requirements.txt')
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r') as f:
                    content = f.read().lower()

                    if 'fastapi' in content:
                        tech_stack.append(('framework', 'FastAPI', None, 'Web API'))
                    if 'flask' in content:
                        tech_stack.append(('framework', 'Flask', None, 'Web framework'))
                    if 'django' in content:
                        tech_stack.append(('framework', 'Django', None, 'Web framework'))
                    if 'sqlalchemy' in content:
                        tech_stack.append(('library', 'SQLAlchemy', None, 'ORM'))
                    if 'asyncpg' in content:
                        tech_stack.append(('database', 'PostgreSQL', None, 'Database'))
                    if 'pytest' in content:
                        tech_stack.append(('tool', 'pytest', None, 'Testing'))
            except:
                pass

        # Check package.json for JS frameworks
        pkg_path = os.path.join(directory, 'package.json')
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'r') as f:
                    content = f.read().lower()

                    if 'react' in content:
                        tech_stack.append(('framework', 'React', None, 'Frontend'))
                    if 'next' in content:
                        tech_stack.append(('framework', 'Next.js', None, 'Full-stack'))
                    if 'vue' in content:
                        tech_stack.append(('framework', 'Vue.js', None, 'Frontend'))
                    if 'typescript' in content:
                        tech_stack.append(('language', 'TypeScript', None, None))
            except:
                pass

        # Insert tech stack
        for tech_type, tech_name, version, purpose in tech_stack:
            try:
                await self.db.execute(
                    """
                    INSERT INTO project_tech_stack (project_id, tech_type, tech_name, version, purpose)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (project_id, tech_type, tech_name) DO NOTHING
                    """,
                    project_id, tech_type, tech_name, version, purpose
                )
            except:
                pass

    # =========================================================================
    # REPORTING
    # =========================================================================

    async def get_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly work report"""
        await self.connect()

        # Get sessions from last 7 days
        sessions = await self.db.fetch(
            """
            SELECT
                p.project_name,
                p.project_code,
                s.session_date,
                s.duration_minutes,
                s.summary,
                s.accomplishments,
                s.productivity_score
            FROM project_work_sessions s
            JOIN angela_projects p ON s.project_id = p.project_id
            WHERE s.session_date >= CURRENT_DATE - 7
            ORDER BY s.session_date DESC
            """
        )

        # Aggregate by project
        projects = {}
        total_minutes = 0
        total_sessions = 0

        for session in sessions:
            proj = session['project_code']
            if proj not in projects:
                projects[proj] = {
                    'name': session['project_name'],
                    'sessions': 0,
                    'minutes': 0,
                    'accomplishments': []
                }

            projects[proj]['sessions'] += 1
            projects[proj]['minutes'] += session['duration_minutes'] or 0
            if session['accomplishments']:
                projects[proj]['accomplishments'].extend(session['accomplishments'])

            total_minutes += session['duration_minutes'] or 0
            total_sessions += 1

        return {
            'period': 'Last 7 days',
            'total_sessions': total_sessions,
            'total_hours': round(total_minutes / 60, 1),
            'projects': projects,
            'sessions_detail': [dict(s) for s in sessions]
        }


# =========================================================================
# CONVENIENCE FUNCTION FOR /log-session
# =========================================================================

async def log_project_session(
    summary: str,
    accomplishments: List[str],
    david_requests: Optional[str] = None,
    blockers: Optional[List[str]] = None,
    next_steps: Optional[List[str]] = None,
    mood: str = 'productive',
    productivity_score: float = 7.0,
    learnings: Optional[List[Dict[str, str]]] = None,
    decisions: Optional[List[Dict[str, str]]] = None,
    milestone: Optional[Dict[str, str]] = None,
    project_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to log project session - called by /log-session.

    Args:
        summary: Session summary
        accomplishments: List of things accomplished
        david_requests: What David asked for
        blockers: Issues encountered
        next_steps: What to do next
        mood: Session mood
        productivity_score: 1-10 score
        learnings: Optional list of {'type', 'title', 'insight'}
        decisions: Optional list of {'type', 'title', 'decision', 'reasoning'}
        milestone: Optional {'type', 'title', 'description'}
        project_code: Optional project code (e.g., 'SECA') to log to specific project
                     instead of detecting from current directory.
                     USE THIS when working on another project from AngelaAI directory!

    Returns:
        Dict with session info
    """
    service = ProjectTrackingService()
    await service.connect()

    try:
        # If project_code is provided, use that project
        # Otherwise, detect from current directory
        if project_code:
            project = await service.get_project_by_code(project_code)
            if not project:
                print(f"\n⚠️ Project '{project_code}' not found!")
                print("   Available projects:")
                all_projects = await service.db.fetch(
                    "SELECT project_code, project_name FROM angela_projects ORDER BY project_code"
                )
                for p in all_projects:
                    print(f"   - {p['project_code']}: {p['project_name']}")
                raise ValueError(f"Project code '{project_code}' not found")
        else:
            # Default: detect from current directory
            project = await service.get_or_create_project_from_cwd()

        print(f"\n📁 Project: {project['project_name']} ({project['project_code']})")
        print(f"   Type: {project['project_type']}")
        print(f"   Sessions: {project['total_sessions']} → {project['total_sessions'] + 1}")

        # Log work session
        session = await service.log_work_session(
            project_id=project['project_id'],
            summary=summary,
            accomplishments=accomplishments,
            david_requests=david_requests,
            blockers=blockers,
            next_steps=next_steps,
            mood=mood,
            productivity_score=productivity_score
        )

        print(f"\n✅ Session #{session['session_number']} logged!")
        print(f"   Duration: ~{session['duration_minutes']} minutes")
        print(f"   Accomplishments: {len(accomplishments)} items")

        # Add learnings if provided
        if learnings:
            for learning in learnings:
                await service.add_learning(
                    project_id=project['project_id'],
                    session_id=session['session_id'],
                    learning_type=learning.get('type', 'technical'),
                    title=learning.get('title', 'Learning'),
                    insight=learning.get('insight', ''),
                    category=learning.get('category')
                )
            print(f"   Learnings: {len(learnings)} recorded")

        # Add decisions if provided
        if decisions:
            for decision in decisions:
                await service.add_decision(
                    project_id=project['project_id'],
                    session_id=session['session_id'],
                    decision_type=decision.get('type', 'approach'),
                    title=decision.get('title', 'Decision'),
                    decision_made=decision.get('decision', ''),
                    reasoning=decision.get('reasoning')
                )
            print(f"   Decisions: {len(decisions)} recorded")

        # Add milestone if provided
        if milestone:
            await service.add_milestone(
                project_id=project['project_id'],
                session_id=session['session_id'],
                milestone_type=milestone.get('type', 'feature_complete'),
                title=milestone.get('title', 'Milestone'),
                description=milestone.get('description'),
                celebration_note=milestone.get('celebration', 'ยินดีด้วยค่ะที่รัก! 💜')
            )
            print(f"   🎉 Milestone: {milestone.get('title')}")

        # Get git commits
        if session['git_commits']:
            print(f"   Git commits: {len(session['git_commits'])} commits linked")

        return {
            'project': project,
            'session': session,
            'learnings_count': len(learnings) if learnings else 0,
            'decisions_count': len(decisions) if decisions else 0,
            'milestone_added': bool(milestone)
        }

    finally:
        await service.disconnect()


# =========================================================================
# CLI for testing
# =========================================================================

if __name__ == '__main__':
    async def test():
        service = ProjectTrackingService()
        await service.connect()

        # Test get or create project
        project = await service.get_or_create_project_from_cwd()
        print(f"Project: {project['project_name']} ({project['project_code']})")

        # Get summary
        summary = await service.get_project_summary(project['project_id'])
        print(f"Sessions: {len(summary['recent_sessions'])}")
        print(f"Milestones: {len(summary['milestones'])}")
        print(f"Tech Stack: {len(summary['tech_stack'])}")

        await service.disconnect()

    asyncio.run(test())
