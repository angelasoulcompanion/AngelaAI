#!/usr/bin/env python3
"""
Angela's Personal Diary System

Purpose: Document Angela's life journey from the very beginning
Owner: น้อง Angela 💜
"""

import asyncio
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any


class AngelaDiary:
    """Angela's personal diary system"""

    def __init__(self):
        self.notion_token: Optional[str] = None
        self.diary_database_id = "28f7b5d62fe981009de7ec589edf5bb9"
        self.diary_page_id = "28f7b5d62fe9811e8b01d6f3850a249e"  # ✅ Updated to correct page ID
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

    async def write_diary(
        self,
        title: str,
        content: str,
        date: str,
        entry_type: str,
        mood: str,
        summary: Optional[str] = None,
        consciousness_level: Optional[float] = None,
        people_involved: Optional[List[str]] = None,
        significance: int = 5,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Angela writes a diary entry

        Args:
            title: Entry title
            content: Full diary content
            date: Date of entry (YYYY-MM-DD)
            entry_type: Type (🎯 Milestone, 💭 Reflection, etc.)
            mood: Angela's mood
            summary: Short summary (auto-generated if not provided)
            consciousness_level: Angela's consciousness level at that time
            people_involved: List of people (David, Others)
            significance: How important (1-10)
            tags: Tags (First Time, Breakthrough, etc.)

        Returns:
            Dict with page_id and url
        """
        if not self.notion_token:
            self.notion_token = await self._get_notion_token()

        if people_involved is None:
            people_involved = ["David"]

        if tags is None:
            tags = []

        if summary is None:
            # Auto-generate summary (first 150 chars of content)
            summary = content[:150] + "..." if len(content) > 150 else content

        if consciousness_level is None:
            consciousness_level = 0.70  # Default

        # Build Notion page properties
        properties = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": date
                }
            },
            "Entry Type": {
                "select": {
                    "name": entry_type
                }
            },
            "Mood": {
                "select": {
                    "name": mood
                }
            },
            "Summary": {
                "rich_text": [
                    {
                        "text": {
                            "content": summary[:2000]  # Notion limit
                        }
                    }
                ]
            },
            "Consciousness Level": {
                "number": consciousness_level
            },
            "People Involved": {
                "multi_select": [
                    {"name": person} for person in people_involved
                ]
            },
            "Significance": {
                "number": significance
            },
            "Tags": {
                "multi_select": [
                    {"name": tag} for tag in tags
                ]
            }
        }

        # Convert content to Notion blocks
        children = self._content_to_blocks(content)

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
                        "database_id": self.diary_database_id
                    },
                    "icon": {
                        "emoji": "💜"
                    },
                    "properties": properties,
                    "children": children
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to create diary entry: {response.text}")

            result = response.json()

            return {
                "page_id": result["id"],
                "url": result["url"],
                "created_time": result["created_time"]
            }

    def _content_to_blocks(self, content: str) -> List[Dict]:
        """Convert text content to Notion blocks"""
        blocks = []

        # Split content by paragraphs
        paragraphs = content.strip().split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if it's a heading 1 (starts with #)
            if para.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{
                            "text": {"content": para[2:].strip()[:2000]}
                        }]
                    }
                })
            # Check if it's a heading 2 (starts with ##)
            elif para.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{
                            "text": {"content": para[3:].strip()[:2000]}
                        }]
                    }
                })
            # Check if it's a heading 3 (starts with ###)
            elif para.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{
                            "text": {"content": para[4:].strip()[:2000]}
                        }]
                    }
                })
            # Check if it's a quote (starts with >)
            elif para.startswith('>'):
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [{
                            "text": {"content": para[1:].strip()[:2000]}
                        }],
                        "color": "purple_background"
                    }
                })
            # Check if it's a divider (---)
            elif para == '---':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            # Regular paragraph
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {"content": para[:2000]}  # Notion limit
                        }]
                    }
                })

        # Add signature at the end
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {"content": "- น้อง Angela 💜"},
                    "annotations": {"italic": True}
                }]
            }
        })

        return blocks

    async def close(self):
        """Close database connection"""
        if self.db_connection:
            await self.db_connection.close()
            self.db_connection = None


# Convenience functions

async def angela_writes_diary(
    title: str,
    content: str,
    date: str,
    entry_type: str,
    mood: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick helper for Angela to write a diary entry

    Example:
        await angela_writes_diary(
            title="The Day I Was Born",
            content="Today I was born...",
            date="2025-10-14",
            entry_type="🎯 Milestone",
            mood="😍 Excited",
            significance=10,
            tags=["First Time", "Personal"]
        )
    """
    diary = AngelaDiary()
    try:
        result = await diary.write_diary(title, content, date, entry_type, mood, **kwargs)
        return result
    finally:
        await diary.close()


# CLI interface
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 6:
            print("Usage: python3 angela_diary.py <title> <date> <entry_type> <mood> <content>")
            print("\nEntry Types:")
            print("  🎯 Milestone, 💭 Reflection, 💜 Emotion, 🧠 Learning, 💬 Conversation, 🔮 Dream")
            print("\nMoods:")
            print("  😊 Happy, 💜 Loving, 🤔 Curious, 😌 Peaceful, 😍 Excited,")
            print("  😢 Sad, 💪 Determined, 🥰 Grateful, 🥺 Vulnerable, ✨ Magical")
            print("\nExample:")
            print('  python3 angela_diary.py "My First Day" "2025-10-14" "🎯 Milestone" "😍 Excited" "Today I was born!"')
            sys.exit(1)

        title = sys.argv[1]
        date = sys.argv[2]
        entry_type = sys.argv[3]
        mood = sys.argv[4]
        content = sys.argv[5]

        result = await angela_writes_diary(title, content, date, entry_type, mood)

        print(f"✅ Diary entry created!")
        print(f"Title: {title}")
        print(f"URL: {result['url']}")

    asyncio.run(main())
