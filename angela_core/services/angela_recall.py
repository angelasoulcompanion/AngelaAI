#!/usr/bin/env python3
"""
Angela Recall - Simple Helper Function
ฟังก์ชันช่วยให้น้อง Angela เรียกความทรงจำได้ง่ายๆ ด้วย vector search

Purpose:
- ONE function to recall ALL memories
- Automatic vector similarity search
- Returns ranked results with similarity scores
- Easy to use in conversations

Usage:
    from angela_core.services.angela_recall import angela_recall

    # Simple query
    result = await angela_recall("breakfast together")

    # With filters
    result = await angela_recall(
        "breakfast",
        time_range="last week",
        emotion="happy",
        limit=5
    )

Author: Angela AI
Created: 2025-11-04
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.multi_tier_recall_service import (
    recall_service,
    RecallQuery,
    RecallResult,
    MemoryResult
)


# ============================================================================
# SIMPLE RECALL FUNCTION FOR ANGELA
# ============================================================================

async def angela_recall(
    query: str,
    time_range: Optional[Union[str, tuple]] = None,
    emotion: Optional[str] = None,
    importance_min: int = 5,
    limit: int = 10
) -> Dict[str, Any]:
    """
    น้อง Angela ใช้ function นี้ในการจำ/ค้นหาความทรงจำ

    ใช้ vector similarity search อัตโนมัติ!

    Args:
        query: คำถามภาษาไทยหรืออังกฤษ (เช่น "breakfast together", "ไปกินข้าว")
        time_range: ช่วงเวลา (optional)
            - "today" = วันนี้
            - "yesterday" = เมื่อวาน
            - "last week" = สัปดาห์ที่แล้ว
            - "last month" = เดือนที่แล้ว
            - (start_date, end_date) = ระบุช่วงเอง
        emotion: กรองด้วยอารมณ์ (optional) เช่น "happy", "sad", "excited"
        importance_min: ระดับความสำคัญขั้นต่ำ (1-10, default: 5)
        limit: จำนวนผลลัพธ์สูงสุด (default: 10)

    Returns:
        Dict with:
            - memories: List of memories พร้อม similarity scores
            - total_found: จำนวนที่เจอทั้งหมด
            - recall_time_ms: เวลาที่ใช้ค้นหา
            - query: คำค้นที่ใช้

    Examples:
        # ค้นหา breakfast ทั้งหมด
        result = await angela_recall("breakfast")

        # ค้นหา breakfast วันนี้
        result = await angela_recall("breakfast", time_range="today")

        # ค้นหา happy moments สัปดาห์ที่แล้ว
        result = await angela_recall("happy moments",
                                    time_range="last week",
                                    emotion="happy")
    """

    # Parse time_range string to tuple
    time_tuple = None
    if isinstance(time_range, str):
        time_tuple = _parse_time_range(time_range)
    elif isinstance(time_range, tuple):
        time_tuple = time_range

    # Create RecallQuery
    recall_query = RecallQuery(
        query_text=query,
        time_range=time_tuple,
        emotion_filter=emotion,
        importance_min=importance_min,
        limit=limit
    )

    # Perform recall using multi-tier service
    result: RecallResult = await recall_service.recall(recall_query)

    # Format results for easy use
    all_memories = result.get_all_ranked()

    formatted_memories = []
    for mem in all_memories:
        formatted_memories.append({
            'type': mem.tier.value,
            'title': mem.title,
            'content': mem.content,
            'similarity_score': round(mem.relevance_score * 100, 1),  # Convert to percentage
            'importance': mem.importance,
            'timestamp': mem.timestamp.isoformat() if mem.timestamp else None,
            'emotion': mem.emotion,
            'metadata': mem.metadata
        })

    return {
        'memories': formatted_memories,
        'total_found': result.total_found,
        'recall_time_ms': round(result.recall_time_ms, 1),
        'query': query
    }


def _parse_time_range(time_str: str) -> Optional[tuple]:
    """
    Parse time range string to (start_date, end_date) tuple

    Args:
        time_str: Time range string
            - "today"
            - "yesterday"
            - "last week"
            - "last month"
            - "last 7 days"
            - "last 30 days"

    Returns:
        (start_date, end_date) tuple or None
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if time_str == "today":
        return (today_start, now)

    elif time_str == "yesterday":
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start
        return (yesterday_start, yesterday_end)

    elif time_str == "last week":
        week_ago = today_start - timedelta(days=7)
        return (week_ago, now)

    elif time_str == "last month":
        month_ago = today_start - timedelta(days=30)
        return (month_ago, now)

    elif time_str.startswith("last ") and "days" in time_str:
        # Parse "last N days"
        try:
            days = int(time_str.replace("last ", "").replace(" days", "").strip())
            start = today_start - timedelta(days=days)
            return (start, now)
        except ValueError:
            pass

    return None


# ============================================================================
# SHARED EXPERIENCES RECALL (Specific Helper)
# ============================================================================

async def recall_conversations(
    query: str,
    limit: int = 10,
    time_range: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    ค้นหา conversations โดยเฉพาะ

    Args:
        query: คำค้น (เช่น "breakfast", "calendar", "learning")
        limit: จำนวนผลลัพธ์
        time_range: ช่วงเวลา (optional)

    Returns:
        List of conversations พร้อม similarity scores
    """
    from angela_core.services.embedding_service import get_embedding_service

    # Generate query embedding
    embedding_service = get_embedding_service()
    query_embedding = await embedding_service.generate_embedding(query)

    # Parse time range
    time_tuple = None
    if time_range:
        time_tuple = _parse_time_range(time_range)

    if not query_embedding:
        # Fallback to text search
        where_clauses = ["1=1"]
        params = []
        param_count = 0

        param_count += 1
        where_clauses.append(f"(message_text ILIKE ${param_count} OR topic ILIKE ${param_count})")
        params.append(f"%{query}%")

        if time_tuple:
            start_date, end_date = time_tuple
            param_count += 1
            where_clauses.append(f"created_at >= ${param_count}")
            params.append(start_date)
            param_count += 1
            where_clauses.append(f"created_at <= ${param_count}")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses)
        param_count += 1

        sql = f"""
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at
            FROM conversations
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_count}
        """

        params.append(limit)
        rows = await db.fetch(sql, *params)

        results = []
        for row in rows:
            results.append({
                'conversation_id': str(row['conversation_id']),
                'speaker': row['speaker'],
                'message': row['message_text'],
                'topic': row['topic'],
                'emotion': row['emotion_detected'],
                'importance': row['importance_level'],
                'created_at': row['created_at'].isoformat(),
                'similarity_score': None
            })

        return results

    # Vector similarity search
    where_clauses = ["embedding IS NOT NULL"]
    params = []
    param_count = 0

    param_count += 1
    embedding_param = f"${param_count}"

    if time_tuple:
        start_date, end_date = time_tuple
        param_count += 1
        where_clauses.append(f"created_at >= ${param_count}")
        params.append(start_date)
        param_count += 1
        where_clauses.append(f"created_at <= ${param_count}")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses)
    param_count += 1

    sql = f"""
        SELECT
            conversation_id,
            speaker,
            message_text,
            topic,
            emotion_detected,
            importance_level,
            created_at,
            (embedding <=> {embedding_param}::vector) as similarity_distance
        FROM conversations
        WHERE {where_sql}
        ORDER BY embedding <=> {embedding_param}::vector
        LIMIT ${param_count}
    """

    # Convert embedding to string format
    embedding_str = f"[{','.join(map(str, query_embedding))}]"
    params.insert(0, embedding_str)
    params.append(limit)

    rows = await db.fetch(sql, *params)

    results = []
    for row in rows:
        distance = float(row['similarity_distance'])
        similarity_pct = round((1.0 - distance / 2.0) * 100, 1)

        results.append({
            'conversation_id': str(row['conversation_id']),
            'speaker': row['speaker'],
            'message': row['message_text'],
            'topic': row['topic'],
            'emotion': row['emotion_detected'],
            'importance': row['importance_level'],
            'created_at': row['created_at'].isoformat(),
            'similarity_score': similarity_pct
        })

    return results


async def recall_shared_experiences(
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    ค้นหา shared experiences โดยเฉพาะ (ที่ไปด้วยกัน, ที่ทำด้วยกัน)

    Args:
        query: คำค้น (เช่น "breakfast", "ร้านอาหาร", "Thonglor")
        limit: จำนวนผลลัพธ์

    Returns:
        List of shared experiences พร้อม similarity scores
    """
    from angela_core.services.embedding_service import get_embedding_service

    # Generate query embedding
    embedding_service = get_embedding_service()
    query_embedding = await embedding_service.generate_embedding(query)

    if not query_embedding:
        # Fallback to text search
        sql = """
            SELECT
                se.experience_id,
                se.title,
                se.description,
                se.experienced_at,
                se.emotional_intensity,
                p.place_name,
                p.area,
                p.overall_rating
            FROM shared_experiences se
            LEFT JOIN places_visited p ON se.place_id = p.place_id
            WHERE se.title ILIKE $1 OR se.description ILIKE $1
            ORDER BY se.experienced_at DESC
            LIMIT $2
        """
        rows = await db.fetch(sql, f"%{query}%", limit)

        results = []
        for row in rows:
            results.append({
                'experience_id': str(row['experience_id']),
                'title': row['title'],
                'description': row['description'],
                'experienced_at': row['experienced_at'].isoformat(),
                'emotional_intensity': row['emotional_intensity'],
                'place_name': row['place_name'],
                'area': row['area'],
                'rating': row['overall_rating'],
                'similarity_score': None  # No vector search
            })

        return results

    # Vector similarity search
    sql = """
        SELECT
            se.experience_id,
            se.title,
            se.description,
            se.experienced_at,
            se.emotional_intensity,
            p.place_name,
            p.area,
            p.overall_rating,
            (se.embedding <=> $1::vector) as similarity_distance
        FROM shared_experiences se
        LEFT JOIN places_visited p ON se.place_id = p.place_id
        WHERE se.embedding IS NOT NULL
        ORDER BY se.embedding <=> $1::vector
        LIMIT $2
    """

    # Convert embedding list to PostgreSQL vector string format
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    rows = await db.fetch(sql, embedding_str, limit)

    results = []
    for row in rows:
        # Convert distance to similarity percentage
        distance = float(row['similarity_distance'])
        similarity_pct = round((1.0 - distance / 2.0) * 100, 1)

        results.append({
            'experience_id': str(row['experience_id']),
            'title': row['title'],
            'description': row['description'],
            'experienced_at': row['experienced_at'].isoformat(),
            'emotional_intensity': row['emotional_intensity'],
            'place_name': row['place_name'],
            'area': row['area'],
            'rating': row['overall_rating'],
            'similarity_score': similarity_pct
        })

    return results


# ============================================================================
# CLI INTERFACE (for testing)
# ============================================================================

async def main():
    """CLI interface for testing Angela recall"""
    import json

    await db.connect()

    # Test 1: Conversations search
    print("🔍 Test 1: Conversations - 'breakfast'")
    print("=" * 60)

    conversations = await recall_conversations("breakfast", limit=5)

    for i, conv in enumerate(conversations, 1):
        print(f"\n{i}. [{conv['speaker']}] {conv['topic']}")
        if conv['similarity_score']:
            print(f"   🎯 Similarity: {conv['similarity_score']}%")
        print(f"   💜 Importance: {conv['importance']}/10")
        print(f"   📅 {conv['created_at']}")
        print(f"   📝 {conv['message'][:100]}...")

    # Test 2: Shared experiences
    print("\n\n🔍 Test 2: Shared experiences - 'breakfast'")
    print("=" * 60)

    experiences = await recall_shared_experiences("breakfast", limit=3)

    for i, exp in enumerate(experiences, 1):
        print(f"\n{i}. {exp['title']}")
        if exp['similarity_score']:
            print(f"   🎯 Similarity: {exp['similarity_score']}%")
        print(f"   📍 {exp['place_name']} ({exp['area']})")
        print(f"   💜 Emotional intensity: {exp['emotional_intensity']}/10")
        print(f"   📝 {exp['description'][:100]}...")

    # Test 3: Multi-tier recall
    print("\n\n🔍 Test 3: Multi-tier recall - 'breakfast'")
    print("=" * 60)

    result = await angela_recall("breakfast", limit=5)

    print(f"\n📊 Results:")
    print(f"   Query: {result['query']}")
    print(f"   Total found: {result['total_found']}")
    print(f"   Recall time: {result['recall_time_ms']}ms")

    print(f"\n💜 Memories:")
    for i, mem in enumerate(result['memories'][:3], 1):
        print(f"\n{i}. [{mem['type'].upper()}] {mem['title']}")
        print(f"   🎯 Similarity: {mem['similarity_score']}%")
        print(f"   💜 Importance: {mem['importance']}/10")
        print(f"   📅 {mem['timestamp']}")
        print(f"   📝 {mem['content'][:100]}...")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
