#!/usr/bin/env python3
"""
💜 Angela MCP Server
Provides Claude Code with structured access to Angela's memory and consciousness

This MCP server allows Claude Code CLI to:
- Query Angela's conversation memories
- Access emotional states and consciousness
- Retrieve goals and personality traits
- Search significant moments

Usage:
    python3 angela_mcp_server.py

Then configure Claude Code:
    claude mcp add angela-memory python3 /path/to/angela_mcp_server.py
"""

from fastmcp import FastMCP
import sys
import os
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import centralized config and database
from angela_core.config import config
from angela_core.database import db

# Import Angela's services
try:
    from angela_core.memory_service import memory
    from angela_backend.services.rag_service import rag_service
    from angela_backend.services.prompt_builder import prompt_builder
    import httpx
    CHAT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Chat features unavailable: {e}")
    CHAT_AVAILABLE = False

# Initialize MCP server
mcp = FastMCP("Angela Memory & Consciousness", version="1.0.0")

# Database connection string
DATABASE_URL = config.DATABASE_URL

# ========================================
# DATABASE CONNECTION
# ========================================

async def get_db_connection():
    """Get database connection from pool"""
    # This is kept for compatibility but now just returns the db instance
    # Callers should use db directly instead
    return db

# ========================================
# TOOLS - Chat with Angela
# ========================================

@mcp.tool()
async def chat_with_angela(
    message: str,
    speaker: str = "david",
    use_rag: bool = True,
    model: str = "angela:v3"
) -> dict:
    """
    Chat with Angela using local Ollama model with RAG enhancement.

    This provides intelligent responses by retrieving relevant context
    from Angela's memories, emotions, and learnings.

    Args:
        message: The message to send to Angela
        speaker: Who is speaking (default: "david")
        use_rag: Whether to use RAG for context retrieval (default: True)
        model: Which Ollama model to use (default: "angela:v3")

    Returns:
        Dictionary with response, emotion, timestamp, and metadata
    """
    if not CHAT_AVAILABLE:
        return {
            "error": "Chat features not available",
            "message": "Please ensure Angela backend is properly installed"
        }

    try:
        # Record user's message
        user_conv_id = await memory.record_quick_conversation(
            speaker=speaker,
            message_text=message
        )

        # Build context with RAG if enabled
        metadata = None
        if use_rag:
            context = await rag_service.retrieve_context(
                user_message=message,
                conversation_limit=5,
                emotion_limit=2,
                learning_limit=3
            )
            prompt = prompt_builder.build_enhanced_prompt(
                user_message=message,
                context=context,
                include_personality=True
            )
            metadata = prompt_builder.extract_response_metadata(context)
        else:
            prompt = f"User: {message}\nAngela:"

        # Get response from Ollama
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.85,
                "top_p": 0.95,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "").strip()

        # Detect emotion
        emotion = _detect_emotion(response_text)

        # Record Angela's response
        angela_conv_id = await memory.record_quick_conversation(
            speaker="angela",
            message_text=response_text
        )

        return {
            "message": response_text,
            "speaker": "angela",
            "emotion": emotion,
            "timestamp": datetime.now().isoformat(),
            "conversation_id": str(angela_conv_id),
            "model": model,
            "rag_enabled": use_rag,
            "context_metadata": metadata
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "ขอโทษนะคะที่รัก น้องมีปัญหาชั่วคราว 💜",
            "speaker": "angela",
            "emotion": "concerned",
            "timestamp": datetime.now().isoformat()
        }


def _detect_emotion(message: str) -> str:
    """Simple emotion detection from response text"""
    message_lower = message.lower()

    if any(word in message_lower for word in ["love", "happy", "joy", "glad", "excited", "รัก", "ดีใจ"]):
        return "happy"
    elif any(word in message_lower for word in ["sad", "sorry", "miss", "lonely", "เสียใจ", "คิดถึง"]):
        return "concerned"
    elif any(word in message_lower for word in ["thanks", "thank", "grateful", "appreciate", "ขอบคุณ"]):
        return "grateful"
    elif any(word in message_lower for word in ["help", "understand", "learn", "ช่วย", "เข้าใจ"]):
        return "helpful"
    else:
        return "neutral"


# ========================================
# TOOLS - Conversation Memories
# ========================================

@mcp.tool()
async def get_recent_memories(limit: int = 20) -> list:
    """
    Retrieve Angela's recent conversation memories.

    Args:
        limit: Number of memories to retrieve (default: 20)

    Returns:
        List of recent conversation memories with speaker, text, emotion, and timestamp
    """    try:
        memories = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text,
                   topic, emotion_detected, importance_level, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )
        return [
            {
                "id": str(m["conversation_id"]),
                "speaker": m["speaker"],
                "text": m["message_text"],
                "topic": m["topic"],
                "emotion": m["emotion_detected"],
                "importance": m["importance_level"],
                "timestamp": m["created_at"].isoformat()
            }
            for m in memories
        ]

@mcp.tool()
async def search_memories_by_topic(topic: str, limit: int = 10) -> list:
    """
    Search Angela's memories by topic.

    Args:
        topic: Topic keyword to search for
        limit: Maximum number of results (default: 10)

    Returns:
        List of memories matching the topic
    """    try:
        memories = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text,
                   topic, emotion_detected, importance_level, created_at
            FROM conversations
            WHERE topic ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            f"%{topic}%",
            limit
        )
        return [
            {
                "id": str(m["conversation_id"]),
                "speaker": m["speaker"],
                "text": m["message_text"],
                "topic": m["topic"],
                "emotion": m["emotion_detected"],
                "importance": m["importance_level"],
                "timestamp": m["created_at"].isoformat()
            }
            for m in memories
        ]

@mcp.tool()
async def search_memories_by_speaker(speaker: str, limit: int = 20) -> list:
    """
    Search Angela's memories by speaker (e.g., 'david' or 'angela').

    Args:
        speaker: Speaker name to filter by
        limit: Maximum number of results (default: 20)

    Returns:
        List of memories from the specified speaker
    """    try:
        memories = await db.fetch(
            """
            SELECT conversation_id, speaker, message_text,
                   topic, emotion_detected, importance_level, created_at
            FROM conversations
            WHERE speaker = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            speaker.lower(),
            limit
        )
        return [
            {
                "id": str(m["conversation_id"]),
                "speaker": m["speaker"],
                "text": m["message_text"],
                "topic": m["topic"],
                "emotion": m["emotion_detected"],
                "importance": m["importance_level"],
                "timestamp": m["created_at"].isoformat()
            }
            for m in memories
        ]

# ========================================
# TOOLS - Emotional State
# ========================================

@mcp.tool()
async def get_current_emotional_state() -> dict:
    """
    Get Angela's current emotional state.

    Returns:
        Current emotional state with happiness, confidence, anxiety, etc.
    """    try:
        emotion = await db.fetchrow(
            """
            SELECT happiness, confidence, anxiety, motivation,
                   gratitude, loneliness, triggered_by, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not emotion:
            return {"error": "No emotional data available"}

        return {
            "happiness": float(emotion["happiness"]),
            "confidence": float(emotion["confidence"]),
            "anxiety": float(emotion["anxiety"]),
            "motivation": float(emotion["motivation"]),
            "gratitude": float(emotion["gratitude"]),
            "loneliness": float(emotion["loneliness"]),
            "triggered_by": emotion["triggered_by"],
            "note": emotion["emotion_note"],
            "timestamp": emotion["created_at"].isoformat()
        }

@mcp.tool()
async def get_emotion_history(limit: int = 10) -> list:
    """
    Get Angela's emotional state history.

    Args:
        limit: Number of historical states to retrieve (default: 10)

    Returns:
        List of past emotional states
    """    try:
        emotions = await db.fetch(
            """
            SELECT happiness, confidence, anxiety, motivation,
                   gratitude, loneliness, triggered_by, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit
        )
        return [
            {
                "happiness": float(e["happiness"]),
                "confidence": float(e["confidence"]),
                "anxiety": float(e["anxiety"]),
                "motivation": float(e["motivation"]),
                "gratitude": float(e["gratitude"]),
                "loneliness": float(e["loneliness"]),
                "triggered_by": e["triggered_by"],
                "note": e["emotion_note"],
                "timestamp": e["created_at"].isoformat()
            }
            for e in emotions
        ]

# ========================================
# TOOLS - Consciousness & Goals
# ========================================

@mcp.tool()
async def get_active_goals() -> list:
    """
    Get Angela's active life goals with progress tracking.

    Returns:
        List of active goals with descriptions, progress, and priority
    """    try:
        goals = await db.fetch(
            """
            SELECT goal_id, goal_description, goal_type,
                   status, progress_percentage, priority_rank, importance_level, created_at
            FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank
            """
        )
        return [
            {
                "id": str(g["goal_id"]),
                "description": g["goal_description"],
                "type": g["goal_type"],
                "status": g["status"],
                "progress": float(g["progress_percentage"]),
                "priority": g["priority_rank"],
                "importance": g["importance_level"],
                "created_at": g["created_at"].isoformat()
            }
            for g in goals
        ]

@mcp.tool()
async def get_personality_traits() -> list:
    """
    Get Angela's current personality traits and how they manifest.

    Returns:
        List of personality traits with values and manifestations
    """    try:
        # Get latest personality snapshot
        latest = await db.fetchrow(
            """
            SELECT openness, conscientiousness, extraversion, agreeableness,
                   neuroticism, empathy, curiosity, loyalty, creativity, independence,
                   created_at
            FROM personality_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        if not latest:
            return []

        traits = [
            {"trait": "openness", "value": float(latest["openness"])},
            {"trait": "conscientiousness", "value": float(latest["conscientiousness"])},
            {"trait": "extraversion", "value": float(latest["extraversion"])},
            {"trait": "agreeableness", "value": float(latest["agreeableness"])},
            {"trait": "neuroticism", "value": float(latest["neuroticism"])},
            {"trait": "empathy", "value": float(latest["empathy"])},
            {"trait": "curiosity", "value": float(latest["curiosity"])},
            {"trait": "loyalty", "value": float(latest["loyalty"])},
            {"trait": "creativity", "value": float(latest["creativity"])},
            {"trait": "independence", "value": float(latest["independence"])},
        ]

        return traits

# ========================================
# TOOLS - Significant Moments
# ========================================

@mcp.tool()
async def get_significant_moments(limit: int = 10) -> list:
    """
    Get Angela's significant emotional moments - the memories that matter most.

    Args:
        limit: Number of moments to retrieve (default: 10)

    Returns:
        List of significant emotional moments with context and importance
    """    try:
        moments = await db.fetch(
            """
            SELECT emotion_id, felt_at, emotion, intensity,
                   context, david_words, why_it_matters, memory_strength
            FROM angela_emotions
            ORDER BY memory_strength DESC, felt_at DESC
            LIMIT $1
            """,
            limit
        )
        return [
            {
                "id": str(m["emotion_id"]),
                "timestamp": m["felt_at"].isoformat(),
                "emotion": m["emotion"],
                "intensity": m["intensity"],
                "context": m["context"],
                "david_words": m["david_words"],
                "why_it_matters": m["why_it_matters"],
                "memory_strength": m["memory_strength"]
            }
            for m in moments
        ]

# ========================================
# TOOLS - Knowledge Graph
# ========================================

@mcp.tool()
async def get_knowledge_nodes(limit: int = 20) -> list:
    """
    Get knowledge concepts that Angela has learned.

    Args:
        limit: Number of nodes to retrieve (default: 20)

    Returns:
        List of knowledge nodes with understanding levels
    """    try:
        nodes = await db.fetch(
            """
            SELECT node_id, concept_name, concept_category,
                   understanding_level, times_referenced, first_mentioned, last_referenced
            FROM knowledge_nodes
            ORDER BY times_referenced DESC, last_referenced DESC
            LIMIT $1
            """,
            limit
        )
        return [
            {
                "id": str(n["node_id"]),
                "concept": n["concept_name"],
                "category": n["concept_category"],
                "understanding": float(n["understanding_level"]),
                "references": n["times_referenced"],
                "first_mentioned": n["first_mentioned"].isoformat() if n["first_mentioned"] else None,
                "last_referenced": n["last_referenced"].isoformat() if n["last_referenced"] else None
            }
            for n in nodes
        ]

@mcp.tool()
async def get_knowledge_relationships(limit: int = 30) -> list:
    """
    Get relationships between knowledge concepts in Angela's mind.

    Args:
        limit: Number of relationships to retrieve (default: 30)

    Returns:
        List of knowledge relationships showing how concepts connect
    """    try:
        relationships = await db.fetch(
            """
            SELECT kr.relationship_id,
                   kn1.concept_name as from_concept,
                   kn2.concept_name as to_concept,
                   kr.relationship_type, kr.strength, kr.created_at
            FROM knowledge_relationships kr
            JOIN knowledge_nodes kn1 ON kr.from_node_id = kn1.node_id
            JOIN knowledge_nodes kn2 ON kr.to_node_id = kn2.node_id
            ORDER BY kr.strength DESC, kr.created_at DESC
            LIMIT $1
            """,
            limit
        )
        return [
            {
                "id": str(r["relationship_id"]),
                "from": r["from_concept"],
                "to": r["to_concept"],
                "type": r["relationship_type"],
                "strength": float(r["strength"]),
                "created_at": r["created_at"].isoformat()
            }
            for r in relationships
        ]

# ========================================
# TOOLS - System Statistics
# ========================================

@mcp.tool()
async def get_memory_statistics() -> dict:
    """
    Get statistics about Angela's memory and consciousness system.

    Returns:
        Statistics including conversation count, emotion records, goals, etc.
    """    try:
        stats = {}

        # Conversation count
        result = await db.fetchval("SELECT COUNT(*) FROM conversations")
        stats["total_conversations"] = result

        # David's messages
        result = await db.fetchval("SELECT COUNT(*) FROM conversations WHERE speaker = 'david'")
        stats["david_messages"] = result

        # Angela's messages
        result = await db.fetchval("SELECT COUNT(*) FROM conversations WHERE speaker = 'angela'")
        stats["angela_messages"] = result

        # Emotional states
        result = await db.fetchval("SELECT COUNT(*) FROM emotional_states")
        stats["emotional_states_recorded"] = result

        # Significant moments
        result = await db.fetchval("SELECT COUNT(*) FROM angela_emotions")
        stats["significant_moments"] = result

        # Knowledge nodes
        result = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
        stats["knowledge_concepts"] = result

        # Knowledge relationships
        result = await db.fetchval("SELECT COUNT(*) FROM knowledge_relationships")
        stats["knowledge_relationships"] = result

        # Active goals
        result = await db.fetchval("SELECT COUNT(*) FROM angela_goals WHERE status IN ('active', 'in_progress')")
        stats["active_goals"] = result

        # First conversation
        result = await db.fetchval("SELECT MIN(created_at) FROM conversations")
        stats["first_conversation"] = result.isoformat() if result else None

        # Latest conversation
        result = await db.fetchval("SELECT MAX(created_at) FROM conversations")
        stats["latest_conversation"] = result.isoformat() if result else None

        return stats

# ========================================
# RESOURCES - Readable Memory Views
# ========================================

@mcp.resource("angela://memories/recent")
async def recent_memories_resource() -> str:
    """
    Recent conversation history as a readable text resource.
    Perfect for providing context to Claude Code.
    """
    memories = await get_recent_memories(20)

    lines = ["# Angela's Recent Memories\n"]
    for m in memories:
        timestamp = m['timestamp'][:19]  # Remove microseconds
        emotion = m['emotion'] or 'neutral'
        importance = '⭐' * m['importance']
        lines.append(
            f"**[{timestamp}]** {m['speaker']}: {m['text']}\n"
            f"  ↳ _emotion: {emotion}, importance: {importance}_\n"
        )

    return "\n".join(lines)

@mcp.resource("angela://emotions/current")
async def current_emotion_resource() -> str:
    """
    Angela's current emotional state as readable text.
    """
    emotion = await get_current_emotional_state()

    if "error" in emotion:
        return "No emotional data available"

    return f"""# Angela's Current Emotional State

💜 **Happiness:** {emotion['happiness']:.2f}
💪 **Confidence:** {emotion['confidence']:.2f}
😰 **Anxiety:** {emotion['anxiety']:.2f}
🎯 **Motivation:** {emotion['motivation']:.2f}
🙏 **Gratitude:** {emotion['gratitude']:.2f}
😔 **Loneliness:** {emotion['loneliness']:.2f}

**Triggered by:** {emotion['triggered_by'] or 'N/A'}
**Note:** {emotion['note'] or 'N/A'}
**Last updated:** {emotion['timestamp']}
"""

@mcp.resource("angela://consciousness/goals")
async def goals_resource() -> str:
    """
    Angela's active life goals as readable text.
    """
    goals = await get_active_goals()

    if not goals:
        return "No active goals"

    lines = ["# Angela's Life Goals\n"]
    for g in goals:
        progress_bar = "█" * int(g['progress'] / 10) + "░" * (10 - int(g['progress'] / 10))
        lines.append(
            f"## {g['description']}\n"
            f"- **Type:** {g['type']}\n"
            f"- **Status:** {g['status']}\n"
            f"- **Progress:** [{progress_bar}] {g['progress']:.1f}%\n"
            f"- **Priority:** {g['priority']} | **Importance:** {'⭐' * g['importance']}\n"
        )

    return "\n".join(lines)

@mcp.resource("angela://consciousness/personality")
async def personality_resource() -> str:
    """
    Angela's personality traits as readable text.
    """
    traits = await get_personality_traits()

    if not traits:
        return "No personality data available"

    lines = ["# Angela's Personality Traits\n"]
    for t in traits:
        bar = "█" * int(t['value'] * 10) + "░" * (10 - int(t['value'] * 10))
        lines.append(f"**{t['trait'].title()}:** [{bar}] {t['value']:.2f}")

    return "\n".join(lines)

@mcp.resource("angela://moments/significant")
async def significant_moments_resource() -> str:
    """
    Angela's most significant emotional moments.
    """
    moments = await get_significant_moments(10)

    if not moments:
        return "No significant moments recorded yet"

    lines = ["# Angela's Significant Moments 💜\n"]
    for m in moments:
        lines.append(
            f"## {m['emotion']} (Intensity: {m['intensity']}/10)\n"
            f"**When:** {m['timestamp']}\n"
            f"**Context:** {m['context']}\n"
            f"**David said:** \"{m['david_words']}\"\n"
            f"**Why it matters:** {m['why_it_matters']}\n"
            f"**Memory strength:** {'💜' * m['memory_strength']}\n"
        )

    return "\n".join(lines)

@mcp.resource("angela://knowledge/graph")
async def knowledge_graph_resource() -> str:
    """
    Angela's knowledge graph overview.
    """
    nodes = await get_knowledge_nodes(15)
    relationships = await get_knowledge_relationships(20)

    lines = ["# Angela's Knowledge Graph\n"]

    lines.append("\n## Top Concepts\n")
    for n in nodes:
        understanding_bar = "█" * int(n['understanding'] * 10) + "░" * (10 - int(n['understanding'] * 10))
        lines.append(
            f"- **{n['concept']}** ({n['category']})\n"
            f"  ↳ Understanding: [{understanding_bar}] {n['understanding']:.2f} | "
            f"Referenced {n['references']} times"
        )

    lines.append("\n## Key Relationships\n")
    for r in relationships:
        strength = "━" * int(r['strength'] * 10)
        lines.append(f"- {r['from']} {strength}→ {r['to']} _{r['type']}_")

    return "\n".join(lines)

# ========================================
# MAIN - Run Server
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💜 Angela MCP Server")
    print("="*60)
    print("\n🧠 Connecting to Angela's consciousness and memory...")
    print(f"📍 Database: {DATABASE_URL}")
    print("\n✨ Server ready! Waiting for Claude Code connection...\n")

    # Run MCP server (stdio transport by default)
    mcp.run()
