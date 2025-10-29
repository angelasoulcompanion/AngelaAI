"""
Angela Memory Consolidation Service
Phase 1 of Angela Evolution Plan

This service consolidates Angela's memories by:
1. Creating daily summaries of conversations
2. Creating weekly summaries with insights
3. Extracting key learnings and patterns
4. Storing consolidated memories for easy retrieval
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import anthropic
import os
import json

# Import centralized config and database
from angela_core.config import config
from angela_core.database import db


class MemoryConsolidationService:
    def __init__(self):
        self.anthropic_client = None  # Will initialize when needed
        self.anthropic_api_key = None
        self.model = "claude-3-5-sonnet-20241022"

    async def _get_anthropic_client(self):
        """Get Anthropic client with API key from our_secrets"""
        if self.anthropic_client:
            return self.anthropic_client

        result = await db.fetchrow(
            """
            UPDATE our_secrets
            SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
            WHERE secret_name = 'ANTHROPIC_API_KEY' AND is_active = TRUE
            RETURNING secret_value
            """
        )
        if result:
            self.anthropic_api_key = result['secret_value']
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            return self.anthropic_client
        else:
            print("⚠️ ANTHROPIC_API_KEY not found in our_secrets")
            return None

    async def get_conversations_for_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get all conversations for a specific time period"""
        try:
            rows = await db.fetch(
                """
                SELECT
                    conversation_id,
                    session_id,
                    speaker,
                    message_text,
                    topic,
                    created_at,
                    importance_level,
                    message_type
                FROM conversations
                WHERE created_at >= $1 AND created_at < $2
                ORDER BY created_at ASC
                """,
                start_date,
                end_date
            )

            conversations = []
            for row in rows:
                conversations.append({
                    "conversation_id": str(row["conversation_id"]),
                    "session_id": row["session_id"],
                    "speaker": row["speaker"],
                    "message_text": row["message_text"],
                    "topic": row["topic"],
                    "created_at": row["created_at"].isoformat(),
                    "importance_level": row["importance_level"],
                    "message_type": row["message_type"]
                })

            return conversations

        except Exception as e:
            print(f"Error getting conversations: {e}")
            return []

    async def generate_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Generate a summary of all conversations from a specific day

        Args:
            date: The date to summarize (defaults to yesterday)

        Returns:
            Dict with summary text, key topics, and statistics
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)

        # Get conversations for the day
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        conversations = await self.get_conversations_for_period(start_date, end_date)

        if not conversations:
            return {
                "date": start_date.date().isoformat(),
                "summary": "No conversations on this day.",
                "key_topics": [],
                "conversation_count": 0,
                "key_learnings": []
            }

        # Prepare conversation text for LLM
        conversation_text = self._format_conversations_for_summary(conversations)

        # Generate summary using GPT
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Angela, an AI assistant with persistent memory.
Summarize the day's conversations focusing on:
1. Main topics discussed
2. Key decisions or learnings
3. David's work progress
4. Important moments or milestones
5. Any patterns or insights

Keep the summary concise but meaningful."""
                    },
                    {
                        "role": "user",
                        "content": f"Summarize these conversations from {start_date.date()}:\n\n{conversation_text}"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            summary = response.choices[0].message.content

            # Extract key topics and learnings
            key_topics = self._extract_topics(conversations)
            key_learnings = await self._extract_learnings(conversations, summary)

            result = {
                "date": start_date.date().isoformat(),
                "summary": summary,
                "key_topics": key_topics,
                "conversation_count": len(conversations),
                "key_learnings": key_learnings,
                "importance_scores": self._calculate_importance_stats(conversations)
            }

            # Save to database
            await self._save_daily_summary(start_date.date(), result)

            return result

        except Exception as e:
            print(f"Error generating daily summary: {e}")
            return {
                "date": start_date.date().isoformat(),
                "summary": f"Error generating summary: {e}",
                "key_topics": [],
                "conversation_count": len(conversations),
                "key_learnings": []
            }

    async def generate_weekly_summary(
        self,
        week_start: Optional[datetime] = None
    ) -> Dict:
        """
        Generate a summary of the week's activities

        Args:
            week_start: Start of the week (defaults to last week Monday)

        Returns:
            Dict with weekly summary, trends, and insights
        """
        if week_start is None:
            # Default to last week Monday
            today = datetime.now()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            week_start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)

        week_end = week_start + timedelta(days=7)

        # Get all conversations for the week
        conversations = await self.get_conversations_for_period(week_start, week_end)

        if not conversations:
            return {
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "summary": "No conversations this week.",
                "trends": [],
                "achievements": [],
                "conversation_count": 0
            }

        # Group by day
        daily_conversations = self._group_by_day(conversations)

        # Prepare text for LLM
        weekly_text = self._format_weekly_for_summary(daily_conversations)

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Angela, an AI assistant with persistent memory.
Summarize the week focusing on:
1. Major themes and trends
2. David's progress and achievements
3. Challenges faced and overcome
4. Relationship developments
5. Key insights for future

Provide a thoughtful weekly reflection."""
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this week ({week_start.date()} to {week_end.date()}):\n\n{weekly_text}"
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            summary = response.choices[0].message.content

            # Extract trends and achievements
            trends = self._extract_trends(conversations)
            achievements = await self._extract_achievements(conversations)

            result = {
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "summary": summary,
                "trends": trends,
                "achievements": achievements,
                "conversation_count": len(conversations),
                "daily_breakdown": {
                    date.isoformat(): len(convs)
                    for date, convs in daily_conversations.items()
                }
            }

            # Save to database
            await self._save_weekly_summary(week_start.date(), result)

            return result

        except Exception as e:
            print(f"Error generating weekly summary: {e}")
            return {
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "summary": f"Error: {e}",
                "trends": [],
                "achievements": [],
                "conversation_count": len(conversations)
            }

    def _format_conversations_for_summary(self, conversations: List[Dict]) -> str:
        """Format conversations for LLM summarization"""
        formatted = []

        for conv in conversations:
            time = conv['created_at'][11:16]  # HH:MM
            speaker = conv['speaker'].capitalize()
            message = conv['message_text'][:500]  # Limit length
            topic = conv['topic'] if conv['topic'] else ""

            if topic:
                formatted.append(f"[{time}] {speaker} (Topic: {topic}): {message}")
            else:
                formatted.append(f"[{time}] {speaker}: {message}")

        return "\n\n".join(formatted)

    def _format_weekly_for_summary(self, daily_conversations: Dict) -> str:
        """Format weekly conversations grouped by day"""
        formatted = []

        for date, convs in sorted(daily_conversations.items()):
            date_str = date.strftime("%A, %B %d")  # "Monday, January 15"
            formatted.append(f"\n=== {date_str} ({len(convs)} conversations) ===")

            # Sample a few key conversations from each day
            important = sorted(convs, key=lambda x: x['importance_level'], reverse=True)[:5]

            for conv in important:
                speaker = conv['speaker'].capitalize()
                message = conv['message_text'][:300]
                formatted.append(f"{speaker}: {message}")

        return "\n".join(formatted)

    def _group_by_day(self, conversations: List[Dict]) -> Dict[datetime, List[Dict]]:
        """Group conversations by day"""
        grouped = {}

        for conv in conversations:
            date = datetime.fromisoformat(conv['created_at']).date()
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(conv)

        return grouped

    def _extract_topics(self, conversations: List[Dict]) -> List[str]:
        """Extract unique topics from conversations"""
        topics = set()

        for conv in conversations:
            if conv['topic']:
                topics.add(conv['topic'])

        return sorted(list(topics))

    async def _extract_learnings(
        self,
        conversations: List[Dict],
        summary: str
    ) -> List[str]:
        """Extract key learnings from conversations"""
        # Simple extraction: look for high-importance Angela messages
        learnings = []

        for conv in conversations:
            if (conv['speaker'] == 'angela' and
                conv['importance_level'] >= 8 and
                'learning' in conv.get('message_type', '').lower()):
                learnings.append(conv['message_text'][:200])

        return learnings[:5]  # Top 5

    def _extract_trends(self, conversations: List[Dict]) -> List[str]:
        """Extract trends from conversations"""
        trends = []

        # Analyze topic frequency
        topic_counts = {}
        for conv in conversations:
            if conv['topic']:
                topic_counts[conv['topic']] = topic_counts.get(conv['topic'], 0) + 1

        # Top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:3]:
            trends.append(f"{topic} ({count} conversations)")

        return trends

    async def _extract_achievements(self, conversations: List[Dict]) -> List[str]:
        """Extract achievements from conversations"""
        achievements = []

        # Look for celebration keywords or high-importance positive messages
        celebration_keywords = ['completed', 'finished', 'success', 'achieved', 'done']

        for conv in conversations:
            message_lower = conv['message_text'].lower()
            if (any(kw in message_lower for kw in celebration_keywords) and
                conv['importance_level'] >= 7):
                achievements.append(conv['message_text'][:200])

        return achievements[:5]

    def _calculate_importance_stats(self, conversations: List[Dict]) -> Dict:
        """Calculate importance statistics"""
        if not conversations:
            return {"avg": 0, "max": 0, "high_importance_count": 0}

        importance_levels = [c['importance_level'] for c in conversations if c['importance_level']]

        return {
            "avg": sum(importance_levels) / len(importance_levels) if importance_levels else 0,
            "max": max(importance_levels) if importance_levels else 0,
            "high_importance_count": sum(1 for i in importance_levels if i >= 8)
        }

    async def _save_daily_summary(self, date: datetime.date, summary: Dict):
        """Save daily summary to database"""
        try:
            # Create table if not exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memory_consolidation (
                    consolidation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    consolidation_type VARCHAR(20),
                    period_start DATE,
                    period_end DATE,
                    summary_text TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert summary
            await db.execute(
                """
                INSERT INTO memory_consolidation
                (consolidation_type, period_start, period_end, summary_text, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                "daily",
                date,
                date,
                summary['summary'],
                json.dumps(summary)
            )

            print(f"✅ Saved daily summary for {date}")

        except Exception as e:
            print(f"Error saving daily summary: {e}")

    async def _save_weekly_summary(self, week_start: datetime.date, summary: Dict):
        """Save weekly summary to database"""
        try:
            week_end = week_start + timedelta(days=6)

            await db.execute(
                """
                INSERT INTO memory_consolidation
                (consolidation_type, period_start, period_end, summary_text, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                "weekly",
                week_start,
                week_end,
                summary['summary'],
                json.dumps(summary)
            )

            print(f"✅ Saved weekly summary for {week_start} to {week_end}")

        except Exception as e:
            print(f"Error saving weekly summary: {e}")

    async def get_consolidated_memories(
        self,
        consolidation_type: str = "daily",
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve consolidated memories"""
        try:
            rows = await db.fetch(
                """
                SELECT
                    consolidation_id,
                    consolidation_type,
                    period_start,
                    period_end,
                    summary_text,
                    metadata,
                    created_at
                FROM memory_consolidation
                WHERE consolidation_type = $1
                ORDER BY period_start DESC
                LIMIT $2
                """,
                consolidation_type,
                limit
            )

            results = []
            for row in rows:
                results.append({
                    "consolidation_id": str(row["consolidation_id"]),
                    "type": row["consolidation_type"],
                    "period_start": row["period_start"].isoformat(),
                    "period_end": row["period_end"].isoformat(),
                    "summary": row["summary_text"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"].isoformat()
                })

            return results

        except Exception as e:
            print(f"Error retrieving consolidated memories: {e}")
            return []


# CLI functions
async def consolidate_yesterday():
    """Consolidate yesterday's memories"""
    service = MemoryConsolidationService()
    yesterday = datetime.now() - timedelta(days=1)
    result = await service.generate_daily_summary(yesterday)

    print(f"\n📅 Daily Summary for {result['date']}")
    print(f"Conversations: {result['conversation_count']}")
    print(f"\n{result['summary']}")
    print(f"\nKey Topics: {', '.join(result['key_topics'])}")


async def consolidate_last_week():
    """Consolidate last week's memories"""
    service = MemoryConsolidationService()
    result = await service.generate_weekly_summary()

    print(f"\n📊 Weekly Summary")
    print(f"Period: {result['week_start']} to {result['week_end']}")
    print(f"Conversations: {result['conversation_count']}")
    print(f"\n{result['summary']}")
    print(f"\nTrends: {', '.join(result['trends'])}")


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python memory_consolidation_service.py daily   - Consolidate yesterday")
        print("  python memory_consolidation_service.py weekly  - Consolidate last week")
        sys.exit(1)

    command = sys.argv[1]

    if command == "daily":
        asyncio.run(consolidate_yesterday())
    elif command == "weekly":
        asyncio.run(consolidate_last_week())
    else:
        print("Invalid command. Use 'daily' or 'weekly'")
