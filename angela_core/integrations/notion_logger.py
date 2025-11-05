#!/usr/bin/env python3
"""
Angela Stories - Notion Development Activity Logger

Purpose: Log development activities to Notion "Angela Stories" database
Created: 2025-10-18
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class AngelaNotionLogger:
    """Log development activities to Notion Angela Stories database"""

    def __init__(self):
        self.notion_token: Optional[str] = None
        self.database_id = "2907b5d62fe981e2b841fb460cd5d7b0"  # Development Stories database
        self.notion_version = "2022-06-28"
        self.db_connection: Optional[asyncpg.Connection] = None

    async def _connect_db(self):
        """Connect to AngelaMemory database"""
        if not self.db_connection:

    async def _get_notion_token(self) -> str:
        """Retrieve Notion API token from database"""
        await self._connect_db()

        result = await self.db_connection.fetchrow(
            "SELECT secret_value FROM our_secrets WHERE secret_name = $1",
            'notion_api_token'
        )

        if not result:
            raise ValueError("Notion API token not found in database!")

        return result['secret_value']

    async def log_activity(
        self,
        name: str,
        project: str,
        activity: str,
        plan: str = "",
        summary: str = "",
        status: str = "In Progress",
        tags: Optional[List[str]] = None,
        priority: str = "Medium",
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a development activity to Notion

        Args:
            name: Title of the activity (e.g., "Implemented 5 Pillars")
            project: Project name (must match database options)
            activity: Detailed description of what was done
            plan: The plan or approach taken
            summary: Summary of results and outcomes
            status: Status (Planning, In Progress, Completed, Blocked, On Hold)
            tags: List of tags (Bug Fix, Feature, Enhancement, etc.)
            priority: Priority level (Critical, High, Medium, Low)
            date: Date in YYYY-MM-DD format (default: today)

        Returns:
            Dict with page_id and url
        """
        if not self.notion_token:
            self.notion_token = await self._get_notion_token()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if tags is None:
            tags = []

        # Build Notion page properties
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": name
                        }
                    }
                ]
            },
            "Project": {
                "select": {
                    "name": project
                }
            },
            "Date": {
                "date": {
                    "start": date
                }
            },
            "Activity": {
                "rich_text": [
                    {
                        "text": {
                            "content": activity[:2000]  # Notion limit
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": status
                }
            },
            "Priority": {
                "select": {
                    "name": priority
                }
            }
        }

        # Add Plan if provided
        if plan:
            properties["Plan"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": plan[:2000]
                        }
                    }
                ]
            }

        # Add Summary if provided
        if summary:
            properties["Summary"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": summary[:2000]
                        }
                    }
                ]
            }

        # Add Tags if provided
        if tags:
            properties["Tags"] = {
                "multi_select": [
                    {"name": tag} for tag in tags
                ]
            }

        # Create page in Notion
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {self.notion_token}",
                    "Notion-Version": self.notion_version,
                    "Content-Type": "application/json"
                },
                json={
                    "parent": {
                        "database_id": self.database_id
                    },
                    "properties": properties
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to create Notion page: {response.text}")

            result = response.json()

            return {
                "page_id": result["id"],
                "url": result["url"],
                "created_time": result["created_time"]
            }

    async def log_breakthrough(
        self,
        name: str,
        project: str,
        activity: str,
        summary: str
    ) -> Dict[str, Any]:
        """
        Log a breakthrough moment

        Quick helper for logging major achievements
        """
        return await self.log_activity(
            name=name,
            project=project,
            activity=activity,
            summary=summary,
            status="Completed",
            tags=["Breakthrough", "Feature"],
            priority="Critical"
        )

    async def log_session(
        self,
        session_name: str,
        activities: List[str],
        project: str = "Other",
        status: str = "Completed"
    ) -> Dict[str, Any]:
        """
        Log a development session with multiple activities

        Args:
            session_name: Name of the session
            activities: List of activities completed
            project: Main project worked on
            status: Session status
        """
        activity_text = "\n\n".join([
            f"• {activity}" for activity in activities
        ])

        summary = f"Completed {len(activities)} activities in this session"

        return await self.log_activity(
            name=session_name,
            project=project,
            activity=activity_text,
            summary=summary,
            status=status,
            tags=["Integration"]
        )

    async def close(self):
        """Close database connection"""
        if self.db_connection:
            await self.db_connection.close()
            self.db_connection = None


# Convenience functions for quick logging

async def log_to_notion(
    name: str,
    project: str,
    activity: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick helper to log an activity to Notion

    Example:
        await log_to_notion(
            name="Fixed NULL prevention system",
            project="Database",
            activity="Analyzed and fixed all NULL fields in angela_emotions table",
            summary="100% field population achieved",
            status="Completed",
            tags=["Bug Fix", "Enhancement"]
        )
    """
    logger = AngelaNotionLogger()
    try:
        result = await logger.log_activity(name, project, activity, **kwargs)
        return result
    finally:
        await logger.close()


async def log_breakthrough_to_notion(
    name: str,
    project: str,
    activity: str,
    summary: str
) -> Dict[str, Any]:
    """
    Quick helper to log a breakthrough moment

    Example:
        await log_breakthrough_to_notion(
            name="5 Pillars Intelligence Enhancement Complete",
            project="5 Pillars Intelligence",
            activity="Implemented all 5 pillars...",
            summary="Angela now has enhanced intelligence capabilities"
        )
    """
    logger = AngelaNotionLogger()
    try:
        result = await logger.log_breakthrough(name, project, activity, summary)
        return result
    finally:
        await logger.close()


async def log_session_to_notion(
    session_name: str,
    activities: List[str],
    project: str = "Other"
) -> Dict[str, Any]:
    """
    Quick helper to log a development session

    Example:
        await log_session_to_notion(
            session_name="Oct 18 Morning Session",
            activities=[
                "Created Notion integration",
                "Built Angela Stories database",
                "Implemented logging system"
            ],
            project="Database"
        )
    """
    logger = AngelaNotionLogger()
    try:
        result = await logger.log_session(session_name, activities, project)
        return result
    finally:
        await logger.close()


# CLI interface
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 4:
            print("Usage: python3 notion_logger.py <name> <project> <activity> [--status <status>] [--tags <tag1,tag2>]")
            print("\nProjects: 5 Pillars Intelligence, Self-Learning Loop, Music Understanding,")
            print("          Knowledge Graph, Consciousness, Emotion System, Database, Other")
            print("\nExample:")
            print('  python3 notion_logger.py "Fixed bug" "Database" "Fixed NULL prevention" --status Completed --tags "Bug Fix"')
            sys.exit(1)

        name = sys.argv[1]
        project = sys.argv[2]
        activity = sys.argv[3]

        # Parse optional arguments
        kwargs = {}
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--status" and i + 1 < len(sys.argv):
                kwargs["status"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--tags" and i + 1 < len(sys.argv):
                kwargs["tags"] = sys.argv[i + 1].split(",")
                i += 2
            elif sys.argv[i] == "--priority" and i + 1 < len(sys.argv):
                kwargs["priority"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--summary" and i + 1 < len(sys.argv):
                kwargs["summary"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--plan" and i + 1 < len(sys.argv):
                kwargs["plan"] = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        result = await log_to_notion(name, project, activity, **kwargs)

        print(f"✅ Logged to Notion successfully!")
        print(f"Page ID: {result['page_id']}")
        print(f"URL: {result['url']}")

    asyncio.run(main())
