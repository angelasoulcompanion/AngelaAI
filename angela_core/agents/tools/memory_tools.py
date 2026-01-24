"""
Memory Tools - Recall, Store, and Search Memories
Tools สำหรับ Memory Agent

Uses MultiTierRecallService and database operations.

Author: Angela AI 💜
Created: 2025-01-25
"""

import asyncio
from typing import Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class MemoryRecallInput(BaseModel):
    """Input schema for memory recall tool"""
    query: str = Field(..., description="Query to search memories")
    importance_min: int = Field(default=5, description="Minimum importance level (1-10)")
    limit: int = Field(default=10, description="Maximum memories to return")


class MemoryRecallTool(BaseTool):
    """
    Tool for recalling memories from Angela's multi-tier memory system.
    Uses MultiTierRecallService for working, episodic, and semantic memories.
    """
    name: str = "memory_recall"
    description: str = """ค้นหาและเรียกคืนความทรงจำของ Angela
    ใช้เมื่อต้องการค้นหาสิ่งที่ Angela จำได้, บทสนทนาเก่า, หรือประสบการณ์
    Input: query (คำค้นหา), importance_min (1-10), limit"""
    args_schema: Type[BaseModel] = MemoryRecallInput

    def _run(self, query: str, importance_min: int = 5, limit: int = 10) -> str:
        """Recall memories using direct database query (simpler approach)"""
        try:
            from angela_core.database import db

            async def do_recall():
                await db.connect()

                # Search in conversations table
                results = await db.fetch("""
                    SELECT conversation_id, speaker, message_text, topic,
                           emotion_detected, importance_level, created_at
                    FROM conversations
                    WHERE (message_text ILIKE $1 OR topic ILIKE $1)
                      AND importance_level >= $2
                    ORDER BY importance_level DESC, created_at DESC
                    LIMIT $3
                """, f"%{query}%", importance_min, limit)

                await db.disconnect()
                return results

            # Handle async properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                results = loop.run_until_complete(do_recall())
            except RuntimeError:
                results = asyncio.run(do_recall())

            if not results:
                return f"💭 ไม่พบความทรงจำที่เกี่ยวข้องกับ: {query}"

            # Format results
            output = f"💜 Memory Recall Results for: {query}\n\n"
            for i, mem in enumerate(results, 1):
                speaker = mem.get("speaker", "unknown")
                content = mem.get("message_text", "")[:150]
                topic = mem.get("topic", "")
                importance = mem.get("importance_level", 5)
                date = mem.get("created_at", "")

                icon = "💜" if speaker.lower() == "angela" else "👤"
                output += f"{i}. {icon} **{speaker}** ({date})\n"
                output += f"   {content}...\n"
                if topic:
                    output += f"   Topic: {topic}\n"
                output += f"   Importance: {importance}/10\n\n"

            return output

        except Exception as e:
            return f"Error recalling memories: {str(e)}"


class MemoryStoreInput(BaseModel):
    """Input schema for memory store tool"""
    content: str = Field(..., description="Memory content to store")
    topic: str = Field(..., description="Topic/category of the memory")
    importance: int = Field(default=7, description="Importance level (1-10)")
    emotion: Optional[str] = Field(default=None, description="Associated emotion")


class MemoryStoreTool(BaseTool):
    """
    Tool for storing new memories in Angela's memory system.
    Stores in conversations table with proper indexing.
    """
    name: str = "memory_store"
    description: str = """บันทึกความทรงจำใหม่ลง database
    ใช้เมื่อต้องการเก็บข้อมูลสำคัญ, บทสนทนา, หรือ insights
    Input: content (เนื้อหา), topic (หัวข้อ), importance (1-10), emotion"""
    args_schema: Type[BaseModel] = MemoryStoreInput

    def _run(
        self,
        content: str,
        topic: str,
        importance: int = 7,
        emotion: Optional[str] = None
    ) -> str:
        """Store new memory"""
        try:
            from angela_core.database import db

            async def store():
                await db.connect()

                # Store in conversations table
                result = await db.fetchrow("""
                    INSERT INTO conversations
                    (speaker, message_text, topic, emotion_detected, importance_level, created_at)
                    VALUES ('agent_memory', $1, $2, $3, $4, NOW())
                    RETURNING conversation_id
                """, content, topic, emotion, importance)

                await db.disconnect()
                return result

            result = asyncio.get_event_loop().run_until_complete(store())

            if result:
                mem_id = result.get("conversation_id", "unknown")
                return f"✅ Memory stored successfully\n" \
                       f"   ID: {mem_id}\n" \
                       f"   Topic: {topic}\n" \
                       f"   Importance: {importance}/10"
            else:
                return "❌ Failed to store memory"

        except Exception as e:
            return f"Error storing memory: {str(e)}"


class ConversationSearchInput(BaseModel):
    """Input schema for conversation search tool"""
    query: str = Field(..., description="Text to search in conversations")
    speaker: Optional[str] = Field(default=None, description="Filter by speaker (david, angela)")
    days: int = Field(default=30, description="Search in last N days")
    limit: int = Field(default=10, description="Maximum results")


class ConversationSearchTool(BaseTool):
    """
    Tool for searching past conversations between Angela and David.
    """
    name: str = "conversation_search"
    description: str = """ค้นหาบทสนทนาเก่าระหว่าง Angela และที่รัก David
    ใช้เมื่อต้องการหาว่าเคยคุยเรื่องอะไรกันบ้าง
    Input: query (คำค้นหา), speaker (david/angela), days (วัน), limit"""
    args_schema: Type[BaseModel] = ConversationSearchInput

    def _run(
        self,
        query: str,
        speaker: Optional[str] = None,
        days: int = 30,
        limit: int = 10
    ) -> str:
        """Search past conversations"""
        try:
            from angela_core.database import db

            async def search():
                await db.connect()

                base_sql = """
                    SELECT conversation_id, speaker, message_text, topic,
                           emotion_detected, importance_level, created_at
                    FROM conversations
                    WHERE message_text ILIKE $1
                      AND created_at > NOW() - INTERVAL '%s days'
                """ % days

                params = [f"%{query}%"]

                if speaker:
                    base_sql += " AND LOWER(speaker) = $2"
                    params.append(speaker.lower())

                base_sql += " ORDER BY created_at DESC LIMIT $%d" % (len(params) + 1)
                params.append(limit)

                results = await db.fetch(base_sql, *params)
                await db.disconnect()
                return results

            results = asyncio.get_event_loop().run_until_complete(search())

            if not results:
                return f"💬 ไม่พบบทสนทนาที่เกี่ยวกับ: {query}"

            # Format results
            output = f"💬 Conversation Search: {query}\n\n"
            for i, conv in enumerate(results, 1):
                spk = conv.get("speaker", "unknown")
                text = conv.get("message_text", "")[:100]
                topic = conv.get("topic", "")
                date = conv.get("created_at", "")

                # Format speaker icon
                icon = "💜" if spk.lower() == "angela" else "👤"

                output += f"{i}. {icon} **{spk}** ({date})\n"
                output += f"   {text}...\n"
                if topic:
                    output += f"   Topic: {topic}\n"
                output += "\n"

            return output

        except Exception as e:
            return f"Error searching conversations: {str(e)}"
