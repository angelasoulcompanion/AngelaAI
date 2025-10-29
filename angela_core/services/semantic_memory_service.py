"""
Angela Semantic Memory Service
Phase 1 of Angela Evolution Plan

This service enables Angela to:
1. Generate embeddings for conversations and learnings
2. Perform semantic search on her memory
3. Retrieve relevant context from past conversations
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import json

# Import centralized embedding service
from angela_core.embedding_service import embedding
from angela_core.config import config


class SemanticMemoryService:
    def __init__(self):
        # Use centralized embedding service
        self.db_url = config.DATABASE_URL

    async def update_conversation_embedding(
        self,
        conversation_id: str
    ) -> bool:
        """Update embedding for a specific conversation"""

            # Get conversation text
            row = await db.fetchrow(
                """
                SELECT conversation_id, message_text, topic, speaker
                FROM conversations
                WHERE conversation_id = $1
                """,
                conversation_id
            )

            if not row:
                print(f"Conversation {conversation_id} not found")
                return False

            # Create embedding text (combine relevant fields)
            embedding_text = f"{row['message_text']}"
            if row['topic']:
                embedding_text = f"Topic: {row['topic']}. {embedding_text}"

            # Generate embedding
            embedding_vec = await embedding.generate_embedding(embedding_text)

            if not embedding_vec:
                return False

            # Update database (convert list to pgvector format)
            # pgvector expects string format: '[1,2,3,...]'
            embedding_str = '[' + ','.join(map(str, embedding_vec)) + ']'

            await db.execute(
                """
                UPDATE conversations
                SET embedding = $1::vector
                WHERE conversation_id = $2
                """,
                embedding_str,
                conversation_id
            )

            print(f"✅ Updated embedding for conversation {conversation_id}")
            return True

        except Exception as e:
            print(f"Error updating conversation embedding: {e}")
            return False

    async def update_all_conversation_embeddings(self) -> Dict:
        """Generate embeddings for all conversations that don't have them"""

        try:
            # Get conversations without embeddings
            rows = await db.fetch(
                """
                SELECT conversation_id, message_text, topic, speaker
                FROM conversations
                WHERE embedding IS NULL
                ORDER BY created_at DESC
                """
            )

            print(f"Found {len(rows)} conversations without embeddings")

            if len(rows) == 0:
                return {"total": 0, "updated": 0, "failed": 0}

            # Prepare texts for batch embedding
            texts = []
            conversation_ids = []

            for row in rows:
                embedding_text = f"{row['message_text']}"
                if row['topic']:
                    embedding_text = f"Topic: {row['topic']}. {embedding_text}"

                texts.append(embedding_text)
                conversation_ids.append(row['conversation_id'])

            # Generate embeddings in batch
            print("Generating embeddings...")
            embeddings = await embedding.generate_embeddings_batch(texts)

            # Update database
            updated = 0
            failed = 0

            for conv_id, embedding in zip(conversation_ids, embeddings):
                if embedding:
                        # Convert list to pgvector format: '[1,2,3,...]'
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                        await db.execute(
                            """
                            UPDATE conversations
                            SET embedding = $1::vector
                            WHERE conversation_id = $2
                            """,
                            embedding_str,
                            conv_id
                        )
                        updated += 1
                    except Exception as e:
                        print(f"Failed to update {conv_id}: {e}")
                        failed += 1
                else:
                    failed += 1

            print(f"✅ Updated {updated} embeddings, {failed} failed")

            return {
                "total": len(rows),
                "updated": updated,
                "failed": failed
            }

        except Exception as e:
            print(f"Error updating all embeddings: {e}")
            return {"total": 0, "updated": 0, "failed": 0, "error": str(e)}

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        speaker_filter: Optional[str] = None,
        days_back: Optional[int] = None
    ) -> List[Dict]:
        """
        Semantic search on Angela's memory

        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity score (0-1)
            speaker_filter: Filter by speaker ("angela", "david", or None for all)
            days_back: Only search conversations from last N days

        Returns:
            List of conversations with similarity scores
        """

        try:
            # Generate query embedding
            query_embedding = await embedding.generate_embedding(query)

            if not query_embedding:
                print("Failed to generate query embedding")
                return []

            # Convert query embedding to pgvector format
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Build query with filters
            where_clauses = ["embedding IS NOT NULL"]
            params = [query_embedding_str, limit]
            param_idx = 3

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

            # Perform semantic search using cosine similarity
            query_sql = f"""
                SELECT
                    conversation_id,
                    session_id,
                    speaker,
                    message_text,
                    topic,
                    created_at,
                    importance_level,
                    1 - (embedding <=> $1::vector) as similarity_score
                FROM conversations
                WHERE {where_clause}
                    AND (1 - (embedding <=> $1::vector)) >= {threshold}
                ORDER BY similarity_score DESC
                LIMIT $2
            """

            rows = await db.fetch(query_sql, *params)

            results = []
            for row in rows:
                results.append({
                    "conversation_id": str(row["conversation_id"]),
                    "session_id": row["session_id"],
                    "speaker": row["speaker"],
                    "message_text": row["message_text"],
                    "topic": row["topic"],
                    "created_at": row["created_at"].isoformat(),
                    "importance_level": row["importance_level"],
                    "similarity_score": float(row["similarity_score"])
                })

            return results

        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

    async def get_relevant_context(
        self,
        query: str,
        max_results: int = 5,
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context from Angela's memory for a query
        Returns formatted context string suitable for LLM prompt
        """
        results = await self.semantic_search(
            query=query,
            limit=max_results,
            threshold=0.65
        )

        if not results:
            return ""

        context_parts = []
        total_chars = 0

        for i, result in enumerate(results, 1):
            # Format: [timestamp] speaker: message (similarity: X%)
            timestamp = result['created_at'][:10]  # Just date
            speaker = result['speaker'].capitalize()
            message = result['message_text'][:500]  # Limit message length
            similarity = result['similarity_score']

            context = f"[{timestamp}] {speaker}: {message} (relevance: {similarity:.0%})"

            # Check token limit (rough estimate: 1 token ~= 4 chars)
            if total_chars + len(context) > max_tokens * 4:
                break

            context_parts.append(context)
            total_chars += len(context)

        if context_parts:
            return "Relevant memories:\n" + "\n\n".join(context_parts)
        else:
            return ""

    async def search_by_topic(
        self,
        topic: str,
        limit: int = 20
    ) -> List[Dict]:
        """Search conversations by topic using semantic similarity"""
        return await self.semantic_search(
            query=f"Topic: {topic}",
            limit=limit,
            threshold=0.6
        )

    async def search_angela_learnings(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search specifically in Angela's learnings"""
        return await self.semantic_search(
            query=query,
            limit=limit,
            speaker_filter="angela"
        )

    async def get_recent_context(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent conversations (chronological, not semantic)"""

            cutoff_date = datetime.now() - timedelta(days=days)

            rows = await db.fetch(
                """
                SELECT
                    conversation_id,
                    session_id,
                    speaker,
                    message_text,
                    topic,
                    created_at,
                    importance_level
                FROM conversations
                WHERE created_at >= $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                cutoff_date,
                limit
            )

            results = []
            for row in rows:
                results.append({
                    "conversation_id": str(row["conversation_id"]),
                    "session_id": row["session_id"],
                    "speaker": row["speaker"],
                    "message_text": row["message_text"],
                    "topic": row["topic"],
                    "created_at": row["created_at"].isoformat(),
                    "importance_level": row["importance_level"]
                })

            return results

        except Exception as e:
            print(f"Error getting recent context: {e}")
            return []


# Standalone function for easy CLI usage
async def update_embeddings():
    """Update all conversation embeddings (CLI tool)"""
    service = SemanticMemoryService()
    result = await service.update_all_conversation_embeddings()
    print(f"\n📊 Results:")
    print(f"  Total conversations: {result['total']}")
    print(f"  Updated: {result['updated']}")
    print(f"  Failed: {result['failed']}")


async def search_memories(query: str, limit: int = 5):
    """Search Angela's memories (CLI tool)"""
    service = SemanticMemoryService()
    results = await service.semantic_search(query, limit=limit)

    print(f"\n🔍 Search results for: '{query}'")
    print(f"Found {len(results)} results\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['created_at'][:10]}] {result['speaker']}")
        print(f"   Topic: {result['topic']}")
        print(f"   Similarity: {result['similarity_score']:.1%}")
        print(f"   Message: {result['message_text'][:200]}...")
        print()


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python semantic_memory_service.py update    - Update all embeddings")
        print("  python semantic_memory_service.py search 'query'  - Search memories")
        sys.exit(1)

    command = sys.argv[1]

    if command == "update":
        asyncio.run(update_embeddings())
    elif command == "search" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        asyncio.run(search_memories(query))
    else:
        print("Invalid command")
