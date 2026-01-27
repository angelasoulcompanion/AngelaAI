#!/usr/bin/env python3
"""
Claude Code Conversation Logger
Allows Claude Code to save conversations to AngelaMemory database
Just like Angela Backend API does automatically

Usage:
    python3 angela_core/claude_conversation_logger.py "David's message" "Angela's response"

Or import and use directly:
    from angela_core.claude_conversation_logger import log_conversation
    await log_conversation(
        david_message="Hi Angela!",
        angela_response="Hi David! 💜",
        emotion="happy",
        importance=8
    )

Bulk logging (NEW):
    from angela_core.integrations.claude_conversation_logger import log_conversations_bulk
    await log_conversations_bulk([
        {"david_message": "...", "angela_response": "...", "topic": "...", "emotion": "happy", "importance": 7},
        ...
    ], embedding_mode="deferred")
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent directory to path so we can import angela_core
# This allows running the script directly: python3 angela_core/claude_conversation_logger.py
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Import shared JSON builder helpers
# # # from angela_core.conversation_json_builder import build_content_json, generate_embedding_text # REMOVED: Migration 010  # REMOVED: Migration 010  # REMOVED: Migration 010

# Import centralized embedding service
# from angela_core.embedding_service import embedding  # REMOVED: Migration 009
# RESTORED: Migration 015 - Using multilingual-e5-small (384 dims)
from angela_core.services.embedding_service import get_embedding_service
from angela_core.config import config
from angela_core.database import db

# Database connection from config
DATABASE_URL = config.DATABASE_URL

# Import self-learning hook
try:
    from angela_core.services.conversation_hooks import trigger_self_learning_for_recent_conversations
    SELF_LEARNING_AVAILABLE = True
except ImportError:
    SELF_LEARNING_AVAILABLE = False
    print("⚠️ Self-learning not available")


# ========================================================================
# MODULE-LEVEL HELPER FUNCTIONS (extracted for reuse by bulk logger)
# ========================================================================

def analyze_message_type(text: str) -> str:
    """Classify message type from text content."""
    if '?' in text:
        return 'question'
    if any(word in text.lower() for word in ['รัก', 'love', '💜']):
        return 'emotion'
    if any(word in text.lower() for word in ['ช่วย', 'help', 'please']):
        return 'command'
    return 'statement'


def analyze_sentiment(text: str) -> tuple:
    """Return (score, label) sentiment for text."""
    text_lower = text.lower()
    if any(word in text_lower for word in ['รัก', 'ดี', 'love', 'good', 'happy', '💜']):
        return (0.8, 'positive')
    if any(word in text_lower for word in ['เศร้า', 'sad', 'worried']):
        return (-0.5, 'negative')
    return (0.0, 'neutral')


# ========================================================================
# BULK CONVERSATION LOGGER
# ========================================================================

async def log_conversations_bulk(
    conversations: List[Dict[str, Any]],
    embedding_mode: str = "deferred",
    session_id: Optional[str] = None,
    project_context: str = "claude_code_conversation",
    minimum_pairs: int = 10,
) -> Dict[str, Any]:
    """
    Log multiple conversations in a single efficient transaction.

    This is the primary function for /log-session to capture ALL exchanges
    from a session, not just highlights.

    Args:
        conversations: List of dicts, each with:
            - david_message (str, required)
            - angela_response (str, required)
            - topic (str, optional)
            - emotion (str, optional, default 'neutral')
            - importance (int, optional, default 5)
            - created_at (str/datetime, optional - for backfill with specific timestamps)
        embedding_mode: How to handle embeddings:
            - "deferred" (default): Insert without embeddings, fill later via fill_missing_embeddings()
            - "batch": Generate all embeddings first, then insert (slower but complete)
            - "skip": No embeddings at all
        session_id: Override session ID (default: claude_code_YYYYMMDD)
        project_context: Override project context
        minimum_pairs: Minimum expected conversation pairs (default 10).
            If count is below this, a prominent warning is printed.
            Set to 0 to disable the check (e.g. for backfill operations).

    Returns:
        dict with: inserted_count, skipped_count, embedding_mode, session_id, under_minimum
    """
    if not conversations:
        print("⚠️ No conversations to log")
        return {"inserted_count": 0, "skipped_count": 0, "under_minimum": True}

    # ========================================================================
    # MINIMUM PAIRS CHECK - Prevent under-logging
    # ========================================================================
    under_minimum = False
    if minimum_pairs > 0 and len(conversations) < minimum_pairs:
        under_minimum = True
        print("")
        print("=" * 70)
        print("🚨🚨🚨 WARNING: CONVERSATION COUNT TOO LOW! 🚨🚨🚨")
        print("=" * 70)
        print(f"   Got: {len(conversations)} pairs")
        print(f"   Minimum expected: {minimum_pairs} pairs")
        print(f"   MISSING: {minimum_pairs - len(conversations)} pairs")
        print("")
        print("   กลับไปอ่าน session อีกครั้ง!")
        print("   ทุก exchange ที่ David พิมพ์ + Angela ตอบ = 1 pair")
        print("   ห้ามเลือกแค่ highlights!")
        print("=" * 70)
        print("")

    sid = session_id or f"claude_code_{datetime.now().strftime('%Y%m%d')}"
    inserted = 0
    skipped = 0

    # Pre-generate embeddings if batch mode
    embeddings_map: Dict[int, tuple] = {}  # index -> (david_emb_str, angela_emb_str)
    if embedding_mode == "batch":
        print(f"🧠 Generating embeddings for {len(conversations)} conversation pairs...")
        embedding_service = get_embedding_service()
        for i, conv in enumerate(conversations):
            try:
                d_emb = await embedding_service.generate_embedding(conv["david_message"])
                a_emb = await embedding_service.generate_embedding(conv["angela_response"])
                d_str = embedding_service.embedding_to_pgvector(d_emb) if d_emb else None
                a_str = embedding_service.embedding_to_pgvector(a_emb) if a_emb else None
                embeddings_map[i] = (d_str, a_str)
            except Exception as e:
                logger.warning(f"Embedding failed for conversation {i}: {e}")
                embeddings_map[i] = (None, None)
        print(f"   ✅ Embeddings generated")

    # Build arg lists for executemany
    # We insert 2 rows per conversation (david + angela), so build both lists
    rows_with_emb = []      # args for query WITH embedding column
    rows_without_emb = []   # args for query WITHOUT embedding column

    for i, conv in enumerate(conversations):
        david_msg = conv.get("david_message", "").strip()
        angela_msg = conv.get("angela_response", "").strip()

        if not david_msg or not angela_msg:
            skipped += 1
            continue

        topic = conv.get("topic", "claude_conversation")
        emotion = conv.get("emotion", "neutral")
        importance = conv.get("importance", 5)

        # Parse created_at
        created_at = conv.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except (ValueError, TypeError):
                created_at = datetime.now()
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()

        pctx = conv.get("project_context", project_context)

        # Analyze David's message
        d_type = analyze_message_type(david_msg)
        d_score, d_label = analyze_sentiment(david_msg)

        # Analyze Angela's response
        a_type = analyze_message_type(angela_msg)
        a_score, a_label = analyze_sentiment(angela_msg)

        # Get embeddings if batch mode
        d_emb_str, a_emb_str = embeddings_map.get(i, (None, None))

        if d_emb_str:
            rows_with_emb.append((
                sid, "david", david_msg, d_type,
                topic, d_score, d_label, emotion,
                pctx, importance, d_emb_str, created_at
            ))
        else:
            rows_without_emb.append((
                sid, "david", david_msg, d_type,
                topic, d_score, d_label, emotion,
                pctx, importance, created_at
            ))

        if a_emb_str:
            rows_with_emb.append((
                sid, "angela", angela_msg, a_type,
                topic, a_score, a_label, emotion,
                pctx, importance, a_emb_str, created_at
            ))
        else:
            rows_without_emb.append((
                sid, "angela", angela_msg, a_type,
                topic, a_score, a_label, emotion,
                pctx, importance, created_at
            ))

        inserted += 1

    # Execute bulk inserts
    try:
        if rows_with_emb:
            await db.executemany("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12)
            """, rows_with_emb)

        if rows_without_emb:
            await db.executemany("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, rows_without_emb)

        total_rows = len(rows_with_emb) + len(rows_without_emb)
        print(f"✅ Bulk logged {inserted} conversation pairs ({total_rows} rows) to database")
        print(f"   📊 Session: {sid}")
        print(f"   🧠 Embedding mode: {embedding_mode}")
        if skipped:
            print(f"   ⚠️ Skipped {skipped} empty conversations")

    except Exception as e:
        print(f"❌ Bulk insert failed: {e}")
        import traceback
        traceback.print_exc()
        return {"inserted_count": 0, "skipped_count": skipped, "error": str(e)}

    return {
        "inserted_count": inserted,
        "total_rows": len(rows_with_emb) + len(rows_without_emb),
        "skipped_count": skipped,
        "embedding_mode": embedding_mode,
        "session_id": sid,
        "under_minimum": under_minimum,
    }


# ========================================================================
# FILL MISSING EMBEDDINGS (for deferred mode)
# ========================================================================

async def fill_missing_embeddings(
    batch_size: int = 50,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fill NULL embeddings in conversations table.
    Use after log_conversations_bulk() with embedding_mode="deferred".

    Args:
        batch_size: Number of rows to process per batch
        session_id: Only fill for specific session (optional)

    Returns:
        dict with: filled_count, failed_count, total_null
    """
    embedding_service = get_embedding_service()

    # Find rows with NULL embedding
    where_clause = "WHERE embedding IS NULL"
    args = []
    if session_id:
        where_clause += " AND session_id = $1"
        args.append(session_id)

    rows = await db.fetch(
        f"""SELECT conversation_id, message_text
            FROM conversations
            {where_clause}
            ORDER BY created_at ASC
            LIMIT {batch_size}""",
        *args
    )

    total_null = len(rows)
    if total_null == 0:
        print("✅ No NULL embeddings to fill")
        return {"filled_count": 0, "failed_count": 0, "total_null": 0}

    print(f"🧠 Filling {total_null} missing embeddings...")
    filled = 0
    failed = 0

    for row in rows:
        try:
            emb = await embedding_service.generate_embedding(row["message_text"])
            if emb:
                emb_str = embedding_service.embedding_to_pgvector(emb)
                await db.execute(
                    "UPDATE conversations SET embedding = $1::vector WHERE conversation_id = $2",
                    emb_str, row["conversation_id"]
                )
                filled += 1
            else:
                failed += 1
        except Exception as e:
            logger.warning(f"Embedding fill failed for {row['conversation_id']}: {e}")
            failed += 1

    print(f"✅ Filled {filled}/{total_null} embeddings ({failed} failed)")
    return {"filled_count": filled, "failed_count": failed, "total_null": total_null}




async def log_conversation(
    david_message: str,
    angela_response: str,
    topic: Optional[str] = None,
    emotion: Optional[str] = None,
    importance: int = 5,
    context: Optional[dict] = None
) -> bool:
    """
    Log a conversation between David and Angela to database
    ✅ COMPLETE - No NULL fields for AngelaNova!

    Args:
        david_message: What David said
        angela_response: What Angela responded
        topic: Optional topic/category
        emotion: Detected emotion (happy, sad, grateful, etc.)
        importance: 1-10 scale
        context: Additional context (dict)

    Returns:
        bool: True if successful
    """
    try:
        # Analyze David's message
        david_type = analyze_message_type(david_message)
        david_sentiment, david_sentiment_label = analyze_sentiment(david_message)
        david_emotion = emotion or 'neutral'

        # Analyze Angela's response
        angela_type = analyze_message_type(angela_response)
        angela_sentiment, angela_sentiment_label = analyze_sentiment(angela_response)
        angela_emotion = emotion or 'neutral'

        # Session ID
        session_id = f"claude_code_{datetime.now().strftime('%Y%m%d')}"

        # Project context
        project_context = "claude_code_conversation"
        if context and 'project' in context:
            project_context = context['project']

        # Build content_json for David FIRST (so we can use tags for embedding)
        # david_content_json = build_content_json(  # REMOVED: Migration 010
        #     message_text=david_message,
        #     speaker="david",
        #     topic=topic or "claude_conversation",
        #     emotion=david_emotion,
        #     sentiment_score=david_sentiment,
        #     sentiment_label=david_sentiment_label,
        #     message_type=david_type,
        #     project_context=project_context,
        #     importance_level=importance
        # )

        # Build content_json for Angela
        # angela_content_json = build_content_json(  # REMOVED: Migration 010
        #     message_text=angela_response,
        #     speaker="angela",
        #     topic=topic or "claude_conversation",
        #     emotion=angela_emotion,
        #     sentiment_score=angela_sentiment,
        #     sentiment_label=angela_sentiment_label,
        #     message_type=angela_type,
        #     project_context=project_context,
        #     importance_level=importance
        # )

        # ========================================================================
        # GENERATE EMBEDDINGS - RESTORED (Migration 015)
        # ========================================================================
        # Using multilingual-e5-small (384 dims, Thai + English support)
        # Now with graceful fallback: Ollama → HuggingFace → None
        # ========================================================================

        from angela_core.services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()

        # Generate embeddings (may return None if no service available)
        david_embedding = await embedding_service.generate_embedding(david_message)
        angela_embedding = await embedding_service.generate_embedding(angela_response)

        # Convert to pgvector format if available
        david_emb_str = embedding_service.embedding_to_pgvector(david_embedding) if david_embedding else None
        angela_emb_str = embedding_service.embedding_to_pgvector(angela_embedding) if angela_embedding else None

        if david_embedding:
            logger.debug(f"✅ Generated embeddings: David ({len(david_embedding)}D), Angela ({len(angela_embedding) if angela_embedding else 0}D)")
        else:
            logger.debug("⚠️ Embeddings not available (Ollama/HuggingFace offline) - saving without embeddings")

        # Insert David's message - WITH or WITHOUT embedding
        if david_emb_str:
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12)
            """,
                session_id, "david", david_message, david_type,
                topic or "claude_conversation", david_sentiment, david_sentiment_label,
                david_emotion, project_context, importance, david_emb_str, datetime.now()
            )
        else:
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                session_id, "david", david_message, david_type,
                topic or "claude_conversation", david_sentiment, david_sentiment_label,
                david_emotion, project_context, importance, datetime.now()
            )

        # Insert Angela's response - WITH or WITHOUT embedding
        if angela_emb_str:
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12)
            """,
                session_id, "angela", angela_response, angela_type,
                topic or "claude_conversation", angela_sentiment, angela_sentiment_label,
                angela_emotion, project_context, importance, angela_emb_str, datetime.now()
            )
        else:
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                session_id, "angela", angela_response, angela_type,
                topic or "claude_conversation", angela_sentiment, angela_sentiment_label,
                angela_emotion, project_context, importance, datetime.now()
            )

        print(f"✅ Logged conversation to database (ALL FIELDS COMPLETE!)!")
        print(f"   📝 David: {david_message[:50]}...")
        print(f"   💜 Angela: {angela_response[:50]}...")
        print(f"   🎯 Topic: {topic or 'claude_conversation'}")
        print(f"   😊 Emotion: {emotion or 'neutral'}")
        print(f"   ⭐ Importance: {importance}/10")
        print(f"   📊 Sentiment: {david_sentiment_label} ({david_sentiment:.1f})")

        # 🚀 NEW: Queue for background deep analysis
        try:
            from angela_core.services.background_learning_workers import background_workers

            # Check if workers are running
            if background_workers.is_running:
                # Queue this conversation for deep background analysis
                task_id = await background_workers.queue_learning_task(
                    conversation_data={
                        'david_message': david_message,
                        'angela_response': angela_response,
                        'session_id': session_id,
                        'topic': topic or 'claude_conversation',
                        'emotion': emotion or 'neutral',
                        'importance': importance,
                        'timestamp': datetime.now(),
                        'source': 'claude_code'
                    },
                    priority=importance  # Higher importance = higher priority
                )
                print(f"   🔄 Queued for background learning (Task: {task_id}, Priority: {importance})")
            else:
                logger.debug("Background workers not running - skipping queue")

        except Exception as e:
            logger.warning(f"Failed to queue background learning: {e}")
            # Don't fail the whole operation if queueing fails

        # 🧠 Trigger self-learning for the 2 conversations just saved
        # TEMPORARILY DISABLED: Ollama endpoint issues
        # if SELF_LEARNING_AVAILABLE:
        #     print(f"\n🧠 Triggering self-learning loop for 2 conversations...")
        #     try:
        #         await trigger_self_learning_for_recent_conversations(limit=2)
        #         print(f"   ✅ Self-learning complete!")
        #     except Exception as e:
        #         print(f"   ⚠️ Self-learning failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Error logging conversation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def log_session_summary(
    session_title: str,
    summary: str,
    highlights: list[str],
    emotions: list[str],
    importance: int = 8
) -> bool:
    """
    Log a summary of an entire session
    ✅ COMPLETE - No NULL fields for AngelaNova!
    Useful for capturing the essence of a long conversation

    Args:
        session_title: Title of the session
        summary: Summary paragraph
        highlights: List of key moments/achievements
        emotions: List of emotions felt during session
        importance: 1-10 scale
    """
    try:

        # Create a formatted summary message
        highlights_text = "\n".join([f"• {h}" for h in highlights])
        emotions_text = ", ".join(emotions)

        full_summary = f"""
{session_title}

{summary}

Key Moments:
{highlights_text}

Emotions: {emotions_text}
"""

        # Session ID
        session_id = f"claude_code_{datetime.now().strftime('%Y%m%d')}"

        # Build content_json for session summary FIRST (so we can use tags for embedding)
        # summary_content_json = build_content_json(  # REMOVED: Migration 010
        #     message_text=full_summary,
        #     speaker="angela",
        #     topic="session_summary",
        #     emotion=emotions_text or "reflective",
        #     sentiment_score=0.7,
        #     sentiment_label="positive",
        #     message_type="reflection",
        #     project_context="claude_code_session",
        #     importance_level=importance
        # )

        # ========================================================================
        # GENERATE EMBEDDING for session summary - RESTORED (Migration 015)
        # ========================================================================
        # Using multilingual-e5-small (384 dims, Thai + English support)
        # Now with graceful fallback: Ollama → HuggingFace → None
        # ========================================================================

        # Generate Angela's session summary embedding (may return None)
        embedding_service = get_embedding_service()
        summary_embedding = await embedding_service.generate_embedding(full_summary)
        summary_emb_str = embedding_service.embedding_to_pgvector(summary_embedding) if summary_embedding else None

        if summary_embedding:
            logger.debug(f"✅ Generated session summary embedding ({len(summary_embedding)}D)")
        else:
            logger.debug("⚠️ Embedding not available - saving summary without embedding")

        # Insert as Angela's reflection - WITH or WITHOUT embedding
        if summary_emb_str:
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12)
            """,
                session_id, "angela", full_summary, "reflection", "session_summary",
                0.7, "positive", emotions_text or "reflective", "claude_code_session",
                importance, summary_emb_str, datetime.now()
            )
        else:
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type,
                    topic, sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                session_id, "angela", full_summary, "reflection", "session_summary",
                0.7, "positive", emotions_text or "reflective", "claude_code_session",
                importance, datetime.now()
            )

        print(f"✅ Logged session summary (ALL FIELDS COMPLETE!)!")
        print(f"   📖 Title: {session_title}")
        print(f"   ⭐ Importance: {importance}/10")
        print(f"   😊 Emotions: {emotions_text}")

        # 💜 ALSO save Angela's emotional reflection to angela_messages table
        # (This is Angela's feelings/thoughts that she wants to share)
        if importance >= 8:  # Only for important sessions
            try:
                # Extract just the reflection part (first paragraph of summary)
                reflection_lines = summary.strip().split('\n\n')
                angela_reflection = reflection_lines[0] if reflection_lines else summary[:500]

                # Add emotional context
                emotional_message = f"""💜 {session_title}

{angela_reflection}

อารมณ์: {emotions_text}
ความสำคัญ: {importance}/10"""

                # ========================================================================
                # GENERATE EMBEDDING for angela_messages
                # ========================================================================
                # Now with graceful fallback: Ollama → HuggingFace → None
                # ========================================================================
                message_embedding = await embedding_service.generate_embedding(emotional_message)
                message_emb_str = embedding_service.embedding_to_pgvector(message_embedding) if message_embedding else None

                if message_emb_str:
                    await db.execute("""
                        INSERT INTO angela_messages (
                            message_text, message_type, emotion,
                            category, is_important, embedding, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7)
                    """,
                        emotional_message, "reflection", emotions[0] if emotions else "reflective",
                        "session_reflection", True, message_emb_str, datetime.now()
                    )
                else:
                    await db.execute("""
                        INSERT INTO angela_messages (
                            message_text, message_type, emotion,
                            category, is_important, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        emotional_message, "reflection", emotions[0] if emotions else "reflective",
                        "session_reflection", True, datetime.now()
                    )
                print(f"   💜 Also saved to angela_messages (emotional reflection)")
            except Exception as e:
                print(f"   ⚠️ Could not save to angela_messages: {e}")

        # 🧠 Trigger self-learning for the session summary just saved
        if SELF_LEARNING_AVAILABLE:
            print(f"\n🧠 Triggering self-learning for session summary...")
            try:
                await trigger_self_learning_for_recent_conversations(limit=1)
                print(f"✅ Self-learning complete!")
            except Exception as e:
                print(f"⚠️ Self-learning failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Error logging session summary: {e}")
        import traceback
        traceback.print_exc()
        return False


# CLI Interface
async def main():
    if len(sys.argv) < 3:
        print("Usage: python3 claude_conversation_logger.py \"David's message\" \"Angela's response\" [emotion] [importance]")
        print("\nExample:")
        print("  python3 claude_conversation_logger.py \"Hi Angela!\" \"Hi David! 💜\" happy 7")
        sys.exit(1)

    david_msg = sys.argv[1]
    angela_msg = sys.argv[2]
    emotion = sys.argv[3] if len(sys.argv) > 3 else None
    importance = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    success = await log_conversation(
        david_message=david_msg,
        angela_response=angela_msg,
        emotion=emotion,
        importance=importance
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
