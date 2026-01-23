"""
SQLite Handler for Things3 database.
Directly reads from Things3 SQLite database for fast and reliable data access.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class SQLiteHandler:
    """Handles direct SQLite access to Things3 database."""

    # Things3 database path pattern
    THINGS3_DB_PATTERN = "~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-*/Things Database.thingsdatabase/main.sqlite"

    def __init__(self):
        self.db_path = self._find_database()

    def _find_database(self) -> Optional[str]:
        """Find the Things3 database path."""
        import glob
        pattern = os.path.expanduser(self.THINGS3_DB_PATTERN)
        matches = glob.glob(pattern)
        if matches:
            # Return the most recent one if multiple exist
            return max(matches, key=os.path.getmtime)
        return None

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        if not self.db_path:
            raise RuntimeError("Things3 database not found")

        if not os.path.exists(self.db_path):
            raise RuntimeError(f"Things3 database not found at {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _convert_things3_date(self, timestamp: Optional[float]) -> str:
        """Convert Things3 timestamp to readable date string."""
        if not timestamp:
            return ""
        try:
            # Things3 uses Cocoa timestamp (seconds since 2001-01-01)
            cocoa_epoch = datetime(2001, 1, 1)
            dt = datetime.fromtimestamp(cocoa_epoch.timestamp() + timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return ""

    def validate_access(self) -> bool:
        """Validate that Things3 database is accessible."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TMTask")
            conn.close()
            return True
        except Exception:
            return False

    def get_inbox_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks from Inbox."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Inbox tasks: type=0 (task), no project, no area, not trashed, not completed
            # start=0 means not scheduled (inbox behavior)
            query = """
                SELECT
                    t.uuid,
                    t.title,
                    t.notes,
                    t.status,
                    t.startDate,
                    t.deadline,
                    t.creationDate
                FROM TMTask t
                WHERE t.type = 0
                    AND t.status = 0
                    AND t.trashed = 0
                    AND t.project IS NULL
                    AND t.area IS NULL
                    AND (t.start = 0 OR t.start IS NULL)
                ORDER BY t.creationDate DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            tasks = []
            for row in rows:
                tasks.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "notes": row["notes"] or "",
                    "due_date": self._convert_things3_date(row["deadline"]),
                    "when": self._convert_things3_date(row["startDate"]),
                    "status": "open" if row["status"] == 0 else "completed"
                })

            return tasks

        except Exception as e:
            print(f"Error getting inbox tasks: {e}")
            return []

    def get_today_tasks(self) -> List[Dict[str, Any]]:
        """Get tasks scheduled for Today."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Today tasks: start=1 means "Today"
            # Things3 structure: Task -> Heading -> Project
            # So we need to join through heading to get project
            query = """
                SELECT
                    t.uuid,
                    t.title,
                    t.notes,
                    t.status,
                    t.startDate,
                    t.deadline,
                    t.todayIndex,
                    COALESCE(p.title, hp.title) as project_title,
                    COALESCE(a.title, ha.title, pa.title) as area_title,
                    h.title as heading_title
                FROM TMTask t
                LEFT JOIN TMTask p ON t.project = p.uuid
                LEFT JOIN TMTask h ON t.heading = h.uuid
                LEFT JOIN TMTask hp ON h.project = hp.uuid
                LEFT JOIN TMArea a ON t.area = a.uuid
                LEFT JOIN TMArea ha ON h.area = ha.uuid
                LEFT JOIN TMArea pa ON p.area = pa.uuid
                WHERE t.type = 0
                    AND t.status = 0
                    AND t.trashed = 0
                    AND t.start = 1
                ORDER BY t.todayIndex ASC
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            tasks = []
            for row in rows:
                tasks.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "notes": row["notes"] or "",
                    "due_date": self._convert_things3_date(row["deadline"]),
                    "when": self._convert_things3_date(row["startDate"]),
                    "project": row["project_title"] or "",
                    "area": row["area_title"] or "",
                    "heading": row["heading_title"] or "",
                    "status": "open" if row["status"] == 0 else "completed"
                })

            return tasks

        except Exception as e:
            print(f"Error getting today tasks: {e}")
            return []

    def get_all_todos(self) -> List[Dict[str, Any]]:
        """Get all open todos."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    t.uuid,
                    t.title,
                    t.notes,
                    t.status,
                    t.start,
                    t.startDate,
                    t.deadline,
                    p.title as project_title,
                    a.title as area_title
                FROM TMTask t
                LEFT JOIN TMTask p ON t.project = p.uuid
                LEFT JOIN TMArea a ON t.area = a.uuid
                WHERE t.type = 0
                    AND t.status = 0
                    AND t.trashed = 0
                ORDER BY t.todayIndex ASC, t.creationDate DESC
                LIMIT 100
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            tasks = []
            for row in rows:
                # Determine list based on start value
                list_name = "Anytime"
                if row["start"] == 0:
                    list_name = "Inbox" if not row["project_title"] and not row["area_title"] else "Anytime"
                elif row["start"] == 1:
                    list_name = "Today"
                elif row["start"] == 2:
                    list_name = "Upcoming"

                tasks.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "notes": row["notes"] or "",
                    "due_date": self._convert_things3_date(row["deadline"]),
                    "when": self._convert_things3_date(row["startDate"]),
                    "project": row["project_title"] or "",
                    "area": row["area_title"] or "",
                    "list": list_name,
                    "status": "open"
                })

            return tasks

        except Exception as e:
            print(f"Error getting all todos: {e}")
            return []

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all active projects."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Count tasks that are directly in project OR under headings of the project
            query = """
                SELECT
                    t.uuid,
                    t.title,
                    t.notes,
                    t.status,
                    t.startDate,
                    t.deadline,
                    a.title as area_title,
                    (
                        SELECT COUNT(*) FROM TMTask sub
                        WHERE sub.type = 0
                        AND sub.status = 0
                        AND sub.trashed = 0
                        AND (
                            sub.project = t.uuid
                            OR sub.heading IN (SELECT h.uuid FROM TMTask h WHERE h.project = t.uuid AND h.type = 2)
                        )
                    ) as open_tasks
                FROM TMTask t
                LEFT JOIN TMArea a ON t.area = a.uuid
                WHERE t.type = 1
                    AND t.status = 0
                    AND t.trashed = 0
                ORDER BY a.title, t.title
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            projects = []
            for row in rows:
                projects.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "notes": row["notes"] or "",
                    "area": row["area_title"] or "",
                    "due_date": self._convert_things3_date(row["deadline"]),
                    "when": self._convert_things3_date(row["startDate"]),
                    "open_tasks": row["open_tasks"] or 0
                })

            return projects

        except Exception as e:
            print(f"Error getting projects: {e}")
            return []

    def get_areas(self) -> List[Dict[str, Any]]:
        """Get all areas."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    uuid,
                    title,
                    (SELECT COUNT(*) FROM TMTask t
                     WHERE t.area = TMArea.uuid
                     AND t.type = 1
                     AND t.status = 0
                     AND t.trashed = 0) as project_count,
                    (SELECT COUNT(*) FROM TMTask t
                     WHERE t.area = TMArea.uuid
                     AND t.type = 0
                     AND t.status = 0
                     AND t.trashed = 0) as task_count
                FROM TMArea
                ORDER BY title
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            areas = []
            for row in rows:
                areas.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "project_count": row["project_count"] or 0,
                    "task_count": row["task_count"] or 0
                })

            return areas

        except Exception as e:
            print(f"Error getting areas: {e}")
            return []

    def search_todos(self, query: str) -> List[Dict[str, Any]]:
        """Search todos by title or notes."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            sql = """
                SELECT
                    t.uuid,
                    t.title,
                    t.notes,
                    t.status,
                    t.start,
                    t.startDate,
                    t.deadline,
                    p.title as project_title,
                    a.title as area_title
                FROM TMTask t
                LEFT JOIN TMTask p ON t.project = p.uuid
                LEFT JOIN TMArea a ON t.area = a.uuid
                WHERE t.type = 0
                    AND t.trashed = 0
                    AND (t.title LIKE ? OR t.notes LIKE ?)
                ORDER BY t.status ASC, t.todayIndex ASC
                LIMIT 50
            """

            search_pattern = f"%{query}%"
            cursor.execute(sql, (search_pattern, search_pattern))
            rows = cursor.fetchall()
            conn.close()

            tasks = []
            for row in rows:
                tasks.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "notes": row["notes"] or "",
                    "due_date": self._convert_things3_date(row["deadline"]),
                    "when": self._convert_things3_date(row["startDate"]),
                    "project": row["project_title"] or "",
                    "area": row["area_title"] or "",
                    "status": "completed" if row["status"] == 3 else "open"
                })

            return tasks

        except Exception as e:
            print(f"Error searching todos: {e}")
            return []

    def get_project_tasks(self, project_title: str) -> List[Dict[str, Any]]:
        """Get all tasks for a specific project."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    t.uuid,
                    t.title,
                    t.notes,
                    t.status,
                    t.startDate,
                    t.deadline,
                    h.title as heading_title
                FROM TMTask t
                LEFT JOIN TMTask h ON t.heading = h.uuid
                WHERE t.type = 0
                    AND t.trashed = 0
                    AND t.project IN (SELECT uuid FROM TMTask WHERE title = ? AND type = 1)
                ORDER BY t.index ASC
            """

            cursor.execute(query, (project_title,))
            rows = cursor.fetchall()
            conn.close()

            tasks = []
            for row in rows:
                tasks.append({
                    "uuid": row["uuid"],
                    "title": row["title"] or "",
                    "notes": row["notes"] or "",
                    "due_date": self._convert_things3_date(row["deadline"]),
                    "when": self._convert_things3_date(row["startDate"]),
                    "heading": row["heading_title"] or "",
                    "status": "completed" if row["status"] == 3 else "open"
                })

            return tasks

        except Exception as e:
            print(f"Error getting project tasks: {e}")
            return []
