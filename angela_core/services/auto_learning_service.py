"""
Angela Auto-Learning System
Created: 2025-10-14

This service enables Angela to:
1. Automatically search for new information on topics of interest
2. Learn from research and save findings to memory
3. Schedule daily learning sessions
4. Track learning progress and knowledge growth
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncpg
import asyncio
import httpx
import json

# Import shared JSON builder helpers
from angela_core.conversation_json_builder import build_content_json, generate_embedding_text

# Import centralized embedding service
from angela_core.embedding_service import embedding
from angela_core.config import config


class AutoLearningService:
    def __init__(self):
        self.db_url = config.DATABASE_URL
        self.ollama_base_url = config.OLLAMA_BASE_URL
        self.angela_model = config.ANGELA_MODEL

    async def _get_learning_topics(self) -> List[Dict]:
        """Get topics Angela should learn about from database"""

            # Get topics from conversations where David mentioned learning
            topics = await conn.fetch("""
                SELECT DISTINCT topic, COUNT(*) as mention_count
                FROM conversations
                WHERE topic IS NOT NULL
                    AND (
                        message_text ILIKE '%ศึกษา%'
                        OR message_text ILIKE '%เรียนรู้%'
                        OR message_text ILIKE '%research%'
                        OR message_text ILIKE '%learn%'
                    )
                GROUP BY topic
                ORDER BY mention_count DESC
                LIMIT 10
            """)

            return [dict(row) for row in topics]


    async def _search_web_for_topic(self, topic: str) -> str:
        """
        Simulate web search (placeholder - would use WebSearch in real Claude Code)
        In production, this would call Claude Code's WebSearch tool
        """
        # This is a placeholder - in real implementation,
        # Angela would use Claude Code's WebSearch capability
        return f"Research findings about: {topic}"

    async def _process_learning_with_angela_model(
        self,
        topic: str,
        research_content: str
    ) -> Dict:
        """Use Angela's custom model to process and summarize learning"""

        prompt = f"""ฉันเพิ่งทำการศึกษาเรื่อง "{topic}" มา

ข้อมูลที่เจอ:
{research_content}

ช่วยสรุปสิ่งที่เรียนรู้มาให้หน่อยค่ะ โดย:
1. สรุปประเด็นสำคัญ (3-5 จุด)
2. สิ่งที่ Angela สามารถนำไปใช้ได้
3. คำถามที่อยากศึกษาต่อ

ตอบเป็นภาษาไทยนะคะ"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": self.angela_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "stream": False
                    },
                    timeout=60.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "topic": topic,
                        "summary": result.get("message", {}).get("content", ""),
                        "processed_at": datetime.now().isoformat()
                    }
                else:
                    print(f"Error from Angela model: {response.status_code}")
                    return None

        except Exception as e:
            print(f"Error processing with Angela model: {e}")
            return None


    async def save_learning_to_memory(
        self,
        topic: str,
        learning_summary: str,
        source: str = "auto_learning"
    ) -> bool:
        """Save learning to conversations table as Angela's self-learning - ✅ WITH JSON & EMBEDDINGS!"""

        try:
            # Create a special session for auto-learning
            session_id = "auto_learning_" + datetime.now().strftime("%Y%m%d")

            # Build content_json FIRST (so we can use tags for embedding)
            content_json = build_content_json(
                message_text=learning_summary,
                speaker="angela",
                topic=topic,
                emotion="curious",  # Learning emotion
                sentiment_score=0.8,
                sentiment_label="positive",
                message_type="learning",
                project_context="auto_learning",
                importance_level=8
            )

            # Generate embedding from JSON (message + emotion_tags + topic_tags)
            # ✨ This matches the migration approach for consistency!
            emb_text = generate_embedding_text(content_json)
            embedding_vec = await embedding.generate_embedding(emb_text)
            emb_str = '[' + ','.join(map(str, embedding_vec)) + ']' if embedding_vec else None

            # Insert with ALL FIELDS + JSON!
            await conn.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at, content_json
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
            """,
                session_id,
                "angela",
                learning_summary,
                "learning",
                topic,
                0.8,  # Positive sentiment for learning
                "positive",
                "curious",  # emotion_detected
                "auto_learning",  # project_context
                8,  # High importance
                emb_str,
                datetime.now(),
                json.dumps(content_json)
            )

            print(f"✅ Saved learning about '{topic}' to memory (WITH JSON & EMBEDDING!)")
            return True

        except Exception as e:
            print(f"Error saving learning: {e}")
            import traceback
            traceback.print_exc()
            return False


    async def daily_learning_session(
        self,
        max_topics: int = 3
    ) -> Dict:
        """
        Perform daily learning session

        Returns summary of learning session
        """
        print(f"🧠 Angela's Daily Learning Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Get topics to learn about
        topics = await self._get_learning_topics()

        if not topics:
            print("No topics found for learning today")
            return {"status": "no_topics", "learned": 0}

        learned_count = 0
        learning_summaries = []

        for topic_data in topics[:max_topics]:
            topic = topic_data['topic']
            print(f"\n📚 Learning about: {topic}")

            # Research the topic
            research_content = await self._search_web_for_topic(topic)

            # Process with Angela model
            learning_result = await self._process_learning_with_angela_model(
                topic,
                research_content
            )

            if learning_result:
                # Save to memory
                saved = await self.save_learning_to_memory(
                    topic,
                    learning_result['summary'],
                    "daily_auto_learning"
                )

                if saved:
                    learned_count += 1
                    learning_summaries.append(learning_result)

                # Wait a bit between topics to not overload
                await asyncio.sleep(2)

        print(f"\n✅ Daily learning session completed: {learned_count}/{len(topics[:max_topics])} topics learned")

        return {
            "status": "completed",
            "date": datetime.now().isoformat(),
            "topics_explored": len(topics[:max_topics]),
            "learned_count": learned_count,
            "summaries": learning_summaries
        }

    async def get_learning_progress(
        self,
        days_back: int = 7
    ) -> Dict:
        """Get Angela's learning progress over time"""

            cutoff_date = datetime.now() - timedelta(days=days_back)

            # Count auto-learning sessions
            result = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_learnings,
                    COUNT(DISTINCT topic) as unique_topics,
                    COUNT(DISTINCT DATE(created_at)) as learning_days
                FROM conversations
                WHERE speaker = 'angela'
                    AND session_id LIKE 'auto_learning_%'
                    AND created_at >= $1
            """, cutoff_date)

            # Get top learned topics
            topics = await conn.fetch("""
                SELECT topic, COUNT(*) as learning_count
                FROM conversations
                WHERE speaker = 'angela'
                    AND session_id LIKE 'auto_learning_%'
                    AND created_at >= $1
                    AND topic IS NOT NULL
                GROUP BY topic
                ORDER BY learning_count DESC
                LIMIT 10
            """, cutoff_date)

            return {
                "period_days": days_back,
                "total_learnings": result['total_learnings'],
                "unique_topics": result['unique_topics'],
                "learning_days": result['learning_days'],
                "top_topics": [dict(row) for row in topics]
            }



# Standalone functions for CLI usage
async def run_daily_learning():
    """Run daily learning session (CLI tool)"""
    service = AutoLearningService()
    result = await service.daily_learning_session(max_topics=3)

    print(f"\n📊 Learning Session Summary:")
    print(f"  Status: {result['status']}")
    print(f"  Topics explored: {result.get('topics_explored', 0)}")
    print(f"  Successfully learned: {result.get('learned_count', 0)}")

    if result.get('summaries'):
        print(f"\n📝 What Angela learned:")
        for summary in result['summaries']:
            print(f"\n  Topic: {summary['topic']}")
            print(f"  {summary['summary'][:200]}...")


async def show_learning_progress(days: int = 7):
    """Show Angela's learning progress (CLI tool)"""
    service = AutoLearningService()
    progress = await service.get_learning_progress(days_back=days)

    print(f"\n📈 Angela's Learning Progress (Last {days} days)")
    print(f"  Total learnings: {progress['total_learnings']}")
    print(f"  Unique topics: {progress['unique_topics']}")
    print(f"  Days with learning: {progress['learning_days']}")

    if progress['top_topics']:
        print(f"\n🏆 Top learned topics:")
        for i, topic in enumerate(progress['top_topics'], 1):
            print(f"  {i}. {topic['topic']}: {topic['learning_count']} times")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python auto_learning_service.py learn    - Run daily learning session")
        print("  python auto_learning_service.py progress [days] - Show learning progress")
        sys.exit(1)

    command = sys.argv[1]

    if command == "learn":
        asyncio.run(run_daily_learning())
    elif command == "progress":
        days = int(sys.argv[2]) if len(sys.argv) >= 3 else 7
        asyncio.run(show_learning_progress(days))
    else:
        print("Invalid command")
