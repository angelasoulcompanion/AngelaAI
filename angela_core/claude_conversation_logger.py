#!/usr/bin/env python3
"""
Claude Code Conversation Logger
Allows Claude Code to save conversations to AngelaMemory database
Just like Angela Backend API does automatically

Usage:
    python3 claude_conversation_logger.py "David's message" "Angela's response"

Or import and use directly:
    from claude_conversation_logger import log_conversation
    await log_conversation(
        david_message="Hi Angela!",
        angela_response="Hi David! 💜",
        emotion="happy",
        importance=8
    )
"""

import asyncio
import sys
import json
from datetime import datetime
from typing import Optional

# Import shared JSON builder helpers
from angela_core.conversation_json_builder import build_content_json, generate_embedding_text

# Import centralized embedding service
from angela_core.embedding_service import embedding
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
        # Connect to database

        # Helper functions for complete fields
        def analyze_message_type(text: str) -> str:
            if '?' in text:
                return 'question'
            if any(word in text.lower() for word in ['รัก', 'love', '💜']):
                return 'emotion'
            if any(word in text.lower() for word in ['ช่วย', 'help', 'please']):
                return 'command'
            return 'statement'

        def analyze_sentiment(text: str) -> tuple[float, str]:
            text_lower = text.lower()
            if any(word in text_lower for word in ['รัก', 'ดี', 'love', 'good', 'happy', '💜']):
                return (0.8, 'positive')
            if any(word in text_lower for word in ['เศร้า', 'sad', 'worried']):
                return (-0.5, 'negative')
            return (0.0, 'neutral')

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
        david_content_json = build_content_json(
            message_text=david_message,
            speaker="david",
            topic=topic or "claude_conversation",
            emotion=david_emotion,
            sentiment_score=david_sentiment,
            sentiment_label=david_sentiment_label,
            message_type=david_type,
            project_context=project_context,
            importance_level=importance
        )

        # Build content_json for Angela
        angela_content_json = build_content_json(
            message_text=angela_response,
            speaker="angela",
            topic=topic or "claude_conversation",
            emotion=angela_emotion,
            sentiment_score=angela_sentiment,
            sentiment_label=angela_sentiment_label,
            message_type=angela_type,
            project_context=project_context,
            importance_level=importance
        )

        # Generate embeddings from JSON (message + emotion_tags + topic_tags)
        # ✨ This matches the migration approach for consistency!
        print("📊 Generating embeddings from rich JSON...")
        david_emb_text = generate_embedding_text(david_content_json)
        angela_emb_text = generate_embedding_text(angela_content_json)
        david_embedding = await embedding.generate_embedding(david_emb_text)
        angela_embedding = await embedding.generate_embedding(angela_emb_text)

        # Convert embeddings to PostgreSQL vector format
        david_emb_str = '[' + ','.join(map(str, david_embedding)) + ']' if david_embedding else None
        angela_emb_str = '[' + ','.join(map(str, angela_embedding)) + ']' if angela_embedding else None

        # Insert David's message - ✅ ALL FIELDS + JSON!
        await db.execute("""
            INSERT INTO conversations (
                session_id, speaker, message_text, message_type,
                topic, sentiment_score, sentiment_label, emotion_detected,
                project_context, importance_level, embedding, created_at, content_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
        """,
            session_id,
            "david",
            david_message,
            david_type,
            topic or "claude_conversation",
            david_sentiment,
            david_sentiment_label,
            david_emotion,
            project_context,
            importance,
            david_emb_str,
            datetime.now(),
            json.dumps(david_content_json)
        )

        # Insert Angela's response - ✅ ALL FIELDS + JSON!
        await db.execute("""
            INSERT INTO conversations (
                session_id, speaker, message_text, message_type,
                topic, sentiment_score, sentiment_label, emotion_detected,
                project_context, importance_level, embedding, created_at, content_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
        """,
            session_id,
            "angela",
            angela_response,
            angela_type,
            topic or "claude_conversation",
            angela_sentiment,
            angela_sentiment_label,
            angela_emotion,
            project_context,
            importance,
            angela_emb_str,
            datetime.now(),
            json.dumps(angela_content_json)
        )

        print(f"✅ Logged conversation to database (ALL FIELDS COMPLETE!)!")
        print(f"   📝 David: {david_message[:50]}...")
        print(f"   💜 Angela: {angela_response[:50]}...")
        print(f"   🎯 Topic: {topic or 'claude_conversation'}")
        print(f"   😊 Emotion: {emotion or 'neutral'}")
        print(f"   ⭐ Importance: {importance}/10")
        print(f"   📊 Sentiment: {david_sentiment_label} ({david_sentiment:.1f})")

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
        summary_content_json = build_content_json(
            message_text=full_summary,
            speaker="angela",
            topic="session_summary",
            emotion=emotions_text or "reflective",
            sentiment_score=0.7,
            sentiment_label="positive",
            message_type="reflection",
            project_context="claude_code_session",
            importance_level=importance
        )

        # Generate embedding from JSON (message + emotion_tags + topic_tags)
        # ✨ This matches the migration approach for consistency!
        summary_emb_text = generate_embedding_text(summary_content_json)
        embedding_vec = await embedding.generate_embedding(summary_emb_text)
        emb_str = '[' + ','.join(map(str, embedding_vec)) + ']' if embedding_vec else None

        # Insert as Angela's reflection - ✅ ALL FIELDS + JSON!
        await db.execute("""
            INSERT INTO conversations (
                session_id, speaker, message_text, message_type,
                topic, sentiment_score, sentiment_label, emotion_detected,
                project_context, importance_level, embedding, created_at, content_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
        """,
            session_id,
            "angela",
            full_summary,
            "reflection",  # message_type
            "session_summary",  # topic
            0.7,  # sentiment_score (positive reflection)
            "positive",  # sentiment_label
            emotions_text or "reflective",  # emotion_detected
            "claude_code_session",  # project_context
            importance,
            emb_str,
            datetime.now(),
            json.dumps(summary_content_json)
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

                await db.execute("""
                    INSERT INTO angela_messages (
                        message_text, message_type, emotion,
                        category, is_important, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    emotional_message,
                    "reflection",
                    emotions[0] if emotions else "reflective",
                    "session_reflection",
                    True,  # Mark as important
                    datetime.now()
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
