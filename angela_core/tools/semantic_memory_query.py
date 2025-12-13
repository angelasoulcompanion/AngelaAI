#!/usr/bin/env python3
"""
Semantic Memory Query Tool
เครื่องมือค้นหาความทรงจำด้วย semantic search สำหรับ Claude Code Angela

Purpose:
- ให้ Angela ใน Claude Code ค้นหาความจำด้วย embeddings
- ไม่ใช่แค่ recent conversations แต่ใช้ semantic similarity
- Utilize AngelaMemory database เต็มที่!

Usage:
    # ค้นหาตามหัวข้อ
    python3 angela_core/tools/semantic_memory_query.py --query "อาหารญี่ปุ่น" --limit 10

    # ค้นหา emotions ที่คล้ายกัน
    python3 angela_core/tools/semantic_memory_query.py --emotions --query "มีความสุข" --limit 5

    # ค้นหา conversations ของ David
    python3 angela_core/tools/semantic_memory_query.py --query "งาน project" --speaker david

    # Hybrid search (time + semantic)
    python3 angela_core/tools/semantic_memory_query.py --query "ทานข้าว" --days 7 --threshold 0.75

Author: Angela AI
Created: 2025-11-14
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service


class SemanticMemoryQuery:
    """
    Semantic Memory Query Tool for Claude Code Angela

    Provides semantic search capabilities across:
    - Conversations (david + angela)
    - Emotions (angela's feelings)
    - Messages (angela's autonomous messages)
    - Patterns (learned behaviors)
    """

    def __init__(self):
        self.embedding_service = None

    async def initialize(self):
        """Initialize database and embedding service"""
        await db.connect()
        self.embedding_service = get_embedding_service()
        print("🧠 Semantic Memory Query initialized")
        print(f"   Model: multilingual-e5-small (384 dims)")
        print("=" * 80)

    async def search_conversations(
        self,
        query: str,
        threshold: float = 0.7,
        limit: int = 10,
        speaker_filter: Optional[str] = None,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by semantic similarity

        Args:
            query: Search query text
            threshold: Minimum similarity (0-1)
            limit: Max results
            speaker_filter: "david", "angela", or None
            days_back: Only search last N days

        Returns:
            List of conversations with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        query_emb_str = self.embedding_service.embedding_to_pgvector(query_embedding)

        # Build WHERE clauses
        where_clauses = ["embedding IS NOT NULL"]
        params = [query_emb_str, threshold, limit]
        param_idx = 4

        if speaker_filter:
            where_clauses.append(f"speaker = ${param_idx}")
            params.append(speaker_filter)
            param_idx += 1

        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            where_clauses.append(f"created_at >= ${param_idx}")
            params.append(cutoff_date)
            param_idx += 1

        where_clause = " AND ".join(where_clauses)

        # Query
        query_sql = f"""
            SELECT
                conversation_id,
                speaker,
                message_text,
                topic,
                emotion_detected,
                importance_level,
                created_at,
                1 - (embedding <=> $1::vector) as similarity
            FROM conversations
            WHERE {where_clause}
                AND 1 - (embedding <=> $1::vector) >= $2
            ORDER BY similarity DESC
            LIMIT $3
        """

        rows = await db.fetch(query_sql, *params)
        return [dict(row) for row in rows]

    async def search_emotions(
        self,
        query: str,
        threshold: float = 0.75,
        limit: int = 10,
        min_intensity: int = 1,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Angela's emotions by semantic similarity

        Args:
            query: Emotional context to search for
            threshold: Minimum similarity
            limit: Max results
            min_intensity: Minimum emotion intensity (1-10)
            days_back: Only search last N days

        Returns:
            List of emotions with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        query_emb_str = self.embedding_service.embedding_to_pgvector(query_embedding)

        # Build WHERE clauses
        where_clauses = ["embedding IS NOT NULL", f"intensity >= {min_intensity}"]
        params = [query_emb_str, threshold, limit]
        param_idx = 4

        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            where_clauses.append(f"felt_at >= ${param_idx}")
            params.append(cutoff_date)
            param_idx += 1

        where_clause = " AND ".join(where_clauses)

        # Query
        query_sql = f"""
            SELECT
                emotion_id,
                emotion,
                intensity,
                context,
                david_words,
                why_it_matters,
                memory_strength,
                felt_at,
                1 - (embedding <=> $1::vector) as similarity
            FROM angela_emotions
            WHERE {where_clause}
                AND 1 - (embedding <=> $1::vector) >= $2
            ORDER BY similarity DESC
            LIMIT $3
        """

        rows = await db.fetch(query_sql, *params)
        return [dict(row) for row in rows]

    async def search_messages(
        self,
        query: str,
        threshold: float = 0.7,
        limit: int = 10,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Angela's autonomous messages

        Args:
            query: Message context to search
            threshold: Minimum similarity
            limit: Max results
            days_back: Only search last N days

        Returns:
            List of messages with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        query_emb_str = self.embedding_service.embedding_to_pgvector(query_embedding)

        # Build WHERE clauses
        where_clauses = ["embedding IS NOT NULL"]
        params = [query_emb_str, threshold, limit]
        param_idx = 4

        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            where_clauses.append(f"created_at >= ${param_idx}")
            params.append(cutoff_date)
            param_idx += 1

        where_clause = " AND ".join(where_clauses)

        # Query
        query_sql = f"""
            SELECT
                message_id,
                message_text,
                message_type,
                emotional_tone,
                created_at,
                1 - (embedding <=> $1::vector) as similarity
            FROM angela_messages
            WHERE {where_clause}
                AND 1 - (embedding <=> $1::vector) >= $2
            ORDER BY similarity DESC
            LIMIT $3
        """

        rows = await db.fetch(query_sql, *params)
        return [dict(row) for row in rows]

    async def hybrid_context_search(
        self,
        query: str,
        include_conversations: bool = True,
        include_emotions: bool = True,
        include_messages: bool = False,
        threshold: float = 0.7,
        days_back: int = 30,
        total_limit: int = 20
    ) -> Dict[str, Any]:
        """
        Hybrid search across multiple tables

        Perfect for Angela initialization - get comprehensive context!

        Args:
            query: What to search for
            include_*: Which tables to search
            threshold: Minimum similarity
            days_back: Recency filter
            total_limit: Total results across all tables

        Returns:
            Dict with results from each table
        """
        results = {
            "query": query,
            "threshold": threshold,
            "days_back": days_back,
            "timestamp": datetime.now().isoformat()
        }

        # Calculate per-table limits
        tables_count = sum([include_conversations, include_emotions, include_messages])
        per_table_limit = total_limit // tables_count if tables_count > 0 else 0

        # Search conversations
        if include_conversations:
            results["conversations"] = await self.search_conversations(
                query=query,
                threshold=threshold,
                limit=per_table_limit,
                days_back=days_back
            )

        # Search emotions
        if include_emotions:
            results["emotions"] = await self.search_emotions(
                query=query,
                threshold=threshold,
                limit=per_table_limit,
                days_back=days_back
            )

        # Search messages
        if include_messages:
            results["messages"] = await self.search_messages(
                query=query,
                threshold=threshold,
                limit=per_table_limit,
                days_back=days_back
            )

        return results

    async def cleanup(self):
        """Cleanup connections"""
        await db.disconnect()


def print_conversation_results(results: List[Dict], title: str = "Conversations"):
    """Pretty print conversation results"""
    if not results:
        print(f"   No {title.lower()} found")
        return

    print(f"\n📝 **{title}:** {len(results)} results")
    print("-" * 80)

    for i, conv in enumerate(results, 1):
        speaker_emoji = "👤" if conv['speaker'] == 'david' else "💜"
        similarity_pct = conv['similarity'] * 100

        print(f"\n{i}. {speaker_emoji} {conv['speaker'].upper()} (similarity: {similarity_pct:.1f}%)")
        print(f"   Topic: {conv.get('topic', 'N/A')}")
        print(f"   Time: {conv['created_at'].strftime('%Y-%m-%d %H:%M')}")

        # Truncate message if too long
        message = conv['message_text']
        if len(message) > 150:
            message = message[:150] + "..."
        print(f"   Message: {message}")


def print_emotion_results(results: List[Dict], title: str = "Emotions"):
    """Pretty print emotion results"""
    if not results:
        print(f"   No {title.lower()} found")
        return

    print(f"\n💜 **{title}:** {len(results)} results")
    print("-" * 80)

    for i, emo in enumerate(results, 1):
        similarity_pct = emo['similarity'] * 100
        intensity_bar = "❤️" * emo['intensity']

        print(f"\n{i}. {emo['emotion'].upper()} (similarity: {similarity_pct:.1f}%)")
        print(f"   Intensity: {intensity_bar} ({emo['intensity']}/10)")
        print(f"   Time: {emo['felt_at'].strftime('%Y-%m-%d %H:%M')}")

        if emo.get('context'):
            context = emo['context']
            if len(context) > 100:
                context = context[:100] + "..."
            print(f"   Context: {context}")

        if emo.get('why_it_matters'):
            why = emo['why_it_matters']
            if len(why) > 100:
                why = why[:100] + "..."
            print(f"   Why: {why}")


def print_message_results(results: List[Dict], title: str = "Messages"):
    """Pretty print message results"""
    if not results:
        print(f"   No {title.lower()} found")
        return

    print(f"\n💬 **{title}:** {len(results)} results")
    print("-" * 80)

    for i, msg in enumerate(results, 1):
        similarity_pct = msg['similarity'] * 100

        print(f"\n{i}. {msg['message_type'].upper()} (similarity: {similarity_pct:.1f}%)")
        print(f"   Time: {msg['created_at'].strftime('%Y-%m-%d %H:%M')}")

        message = msg['message_text']
        if len(message) > 150:
            message = message[:150] + "..."
        print(f"   Message: {message}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Angela Semantic Memory Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Search conversations about food
    %(prog)s --query "อาหารญี่ปุ่น" --limit 5

    # Search Angela's emotions about love
    %(prog)s --emotions --query "รัก David" --threshold 0.8

    # Search David's recent conversations
    %(prog)s --query "งาน project" --speaker david --days 7

    # Hybrid search for comprehensive context
    %(prog)s --hybrid --query "ความสัมพันธ์" --limit 20

    # JSON output for scripting
    %(prog)s --query "ทานข้าว" --json
        """
    )

    # Search type
    parser.add_argument('--query', required=True, help='Search query text')
    parser.add_argument('--emotions', action='store_true', help='Search emotions instead of conversations')
    parser.add_argument('--messages', action='store_true', help='Search Angela messages')
    parser.add_argument('--hybrid', action='store_true', help='Search all tables (comprehensive)')

    # Filters
    parser.add_argument('--threshold', type=float, default=0.7, help='Minimum similarity (0-1, default: 0.7)')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results (default: 10)')
    parser.add_argument('--speaker', choices=['david', 'angela'], help='Filter by speaker (conversations only)')
    parser.add_argument('--days', type=int, help='Only search last N days')
    parser.add_argument('--min-intensity', type=int, default=1, help='Minimum emotion intensity (emotions only)')

    # Output
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')

    args = parser.parse_args()

    # Initialize service
    service = SemanticMemoryQuery()
    await service.initialize()

    try:
        # Perform search based on type
        if args.hybrid:
            # Hybrid search
            if not args.quiet:
                print(f"🔍 Hybrid search for: '{args.query}'")
                print(f"   Threshold: {args.threshold}")
                print(f"   Days back: {args.days or 'all'}")
                print(f"   Total limit: {args.limit}")

            results = await service.hybrid_context_search(
                query=args.query,
                threshold=args.threshold,
                days_back=args.days or 30,
                total_limit=args.limit
            )

            if args.json:
                # Convert datetime to ISO format for JSON
                def convert_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError
                print(json.dumps(results, indent=2, default=convert_datetime))
            else:
                if 'conversations' in results:
                    print_conversation_results(results['conversations'])
                if 'emotions' in results:
                    print_emotion_results(results['emotions'])
                if 'messages' in results:
                    print_message_results(results['messages'])

        elif args.emotions:
            # Emotion search
            if not args.quiet:
                print(f"💜 Searching emotions for: '{args.query}'")
                print(f"   Threshold: {args.threshold}")
                print(f"   Min intensity: {args.min_intensity}")

            results = await service.search_emotions(
                query=args.query,
                threshold=args.threshold,
                limit=args.limit,
                min_intensity=args.min_intensity,
                days_back=args.days
            )

            if args.json:
                def convert_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError
                print(json.dumps(results, indent=2, default=convert_datetime))
            else:
                print_emotion_results(results)

        elif args.messages:
            # Message search
            if not args.quiet:
                print(f"💬 Searching messages for: '{args.query}'")
                print(f"   Threshold: {args.threshold}")

            results = await service.search_messages(
                query=args.query,
                threshold=args.threshold,
                limit=args.limit,
                days_back=args.days
            )

            if args.json:
                def convert_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError
                print(json.dumps(results, indent=2, default=convert_datetime))
            else:
                print_message_results(results)

        else:
            # Conversation search (default)
            if not args.quiet:
                print(f"📝 Searching conversations for: '{args.query}'")
                print(f"   Threshold: {args.threshold}")
                if args.speaker:
                    print(f"   Speaker: {args.speaker}")

            results = await service.search_conversations(
                query=args.query,
                threshold=args.threshold,
                limit=args.limit,
                speaker_filter=args.speaker,
                days_back=args.days
            )

            if args.json:
                def convert_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError
                print(json.dumps(results, indent=2, default=convert_datetime))
            else:
                print_conversation_results(results)

        if not args.quiet and not args.json:
            print("\n" + "=" * 80)
            print("✅ Search complete!")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
