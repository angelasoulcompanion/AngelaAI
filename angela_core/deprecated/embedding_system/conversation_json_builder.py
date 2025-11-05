"""
Conversation JSON Builder - Shared helper for building rich JSON content
Used by all services that insert to conversations table
"""
from datetime import datetime
from typing import Dict


def build_content_json(
    message_text: str,
    speaker: str,
    topic: str,
    emotion: str,
    sentiment_score: float,
    sentiment_label: str,
    message_type: str,
    project_context: str,
    importance_level: int
) -> dict:
    """
    Build rich JSON content with tags for conversation
    ✨ Shared across all Angela services!

    Returns dict ready for json.dumps() and insertion to conversations.content_json
    """
    # Extract emotion_tags
    emotion_tags = []
    if emotion and emotion != 'neutral':
        emotion_tags.append(emotion.lower())

    # Extract topic_tags
    topic_tags = []
    if topic:
        topics = topic.lower().replace(',', ' ').replace(';', ' ').split()
        topic_tags = [t for t in topics if len(t) > 2][:5]

    # Extract sentiment_tags
    sentiment_tags = []
    if sentiment_score > 0.3:
        sentiment_tags.append('positive')
    elif sentiment_score < -0.3:
        sentiment_tags.append('negative')
    else:
        sentiment_tags.append('neutral')

    # Extract context_tags
    context_tags = []
    if message_type:
        context_tags.append(message_type.lower())
    if project_context:
        context_tags.append(project_context.lower())

    # Extract importance_tags
    importance_tags = []
    if importance_level >= 8:
        importance_tags.extend(['critical', 'high_importance'])
    elif importance_level >= 6:
        importance_tags.extend(['significant', 'medium_importance'])
    else:
        importance_tags.append('normal')

    # Build rich JSON
    content_json = {
        "message": message_text,
        "speaker": speaker,
        "tags": {
            "emotion_tags": emotion_tags,
            "topic_tags": topic_tags,
            "sentiment_tags": sentiment_tags,
            "context_tags": context_tags,
            "importance_tags": importance_tags
        },
        "metadata": {
            "original_topic": topic,
            "original_emotion": emotion,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "message_type": message_type,
            "project_context": project_context,
            "importance_level": importance_level,
            "created_at": datetime.now().isoformat()
        }
    }
    return content_json


def generate_embedding_text(content_json: Dict) -> str:
    """
    Generate text for embedding from rich JSON

    Combines: message + emotion_tags + topic_tags
    This ensures embeddings include semantic information from tags!

    Args:
        content_json: Output from build_content_json()

    Returns:
        Text string ready for embedding generation
    """
    parts = [
        content_json['message'],
        ' '.join(content_json['tags'].get('emotion_tags', [])),
        ' '.join(content_json['tags'].get('topic_tags', [])),
    ]

    return ' '.join([p for p in parts if p])


def build_learning_content_json(
    topic: str,
    category: str,
    insight: str,
    evidence: str,
    confidence_level: float
) -> dict:
    """
    Build rich JSON content for learnings table

    Args:
        topic: Learning topic
        category: Category (technical, emotional, relationship, etc.)
        insight: What was learned
        evidence: Evidence or example
        confidence_level: Confidence (0.0-1.0)

    Returns:
        dict ready for json.dumps() and insertion to learnings.content_json
    """
    # Extract topic_tags
    topic_tags = []
    if topic:
        topics = topic.lower().replace(',', ' ').replace(';', ' ').split()
        topic_tags = [t for t in topics if len(t) > 2][:5]

    # Extract category_tags
    category_tags = [category.lower()] if category else []

    # Extract confidence_tags
    confidence_tags = []
    if confidence_level >= 0.8:
        confidence_tags.append('high_confidence')
    elif confidence_level >= 0.5:
        confidence_tags.append('medium_confidence')
    else:
        confidence_tags.append('low_confidence')

    # Build rich JSON
    content_json = {
        "learning": {
            "insight": insight,
            "evidence": evidence or "",
            "topic": topic,
            "category": category
        },
        "tags": {
            "topic_tags": topic_tags,
            "category_tags": category_tags,
            "confidence_tags": confidence_tags
        },
        "metadata": {
            "confidence_level": confidence_level,
            "category": category,
            "topic": topic,
            "created_at": datetime.now().isoformat()
        }
    }
    return content_json


def generate_embedding_text_from_learning(content_json: Dict) -> str:
    """
    Generate text for embedding from learning content_json

    Combines: insight + evidence + topic_tags + category_tags + confidence_tags

    Args:
        content_json: Output from build_learning_content_json()

    Returns:
        Text string ready for embedding generation
    """
    parts = [
        content_json['learning']['insight'],
        content_json['learning']['evidence'][:200] if content_json['learning']['evidence'] else '',
        ' '.join(content_json['tags'].get('topic_tags', [])),
        ' '.join(content_json['tags'].get('category_tags', [])),
        ' '.join(content_json['tags'].get('confidence_tags', [])),
    ]

    return ' '.join([p for p in parts if p])


def build_emotion_content_json(
    emotion: str,
    intensity: int,
    secondary_emotions: list,
    david_words: str,
    context: str,
    why_it_matters: str,
    what_it_means_to_me: str,
    memory_strength: int,
    how_it_feels: str,
    physical_sensation: str,
    emotional_quality: str,
    david_action: str,
    what_i_learned: str,
    how_it_changed_me: str,
    what_i_promise: str,
    reminder_for_future: str
) -> dict:
    """
    Build rich JSON content for angela_emotions table

    Returns:
        dict ready for json.dumps() and insertion to angela_emotions.content_json
    """
    # Extract emotion_tags
    emotion_tags = [emotion] + (secondary_emotions or [])

    # Extract intensity_tags
    intensity_tags = []
    if intensity >= 8:
        intensity_tags.append('high_intensity')
    elif intensity >= 5:
        intensity_tags.append('medium_intensity')
    else:
        intensity_tags.append('low_intensity')

    # Extract memory_strength_tags
    memory_strength_tags = []
    if memory_strength >= 9:
        memory_strength_tags.append('core_memory')
    elif memory_strength >= 7:
        memory_strength_tags.append('strong_memory')
    else:
        memory_strength_tags.append('normal_memory')

    # Build rich JSON
    content_json = {
        "emotion": {
            "primary": emotion,
            "secondary": secondary_emotions or [],
            "intensity": intensity,
            "how_it_feels": how_it_feels,
            "physical_sensation": physical_sensation,
            "emotional_quality": emotional_quality
        },
        "tags": {
            "emotion_tags": emotion_tags,
            "intensity_tags": intensity_tags,
            "memory_strength_tags": memory_strength_tags
        },
        "context": {
            "david_words": david_words,
            "david_action": david_action,
            "who_involved": "David",
            "situation": context
        },
        "significance": {
            "why_it_matters": why_it_matters,
            "what_it_means_to_me": what_it_means_to_me,
            "memory_strength": memory_strength
        },
        "growth": {
            "what_i_learned": what_i_learned,
            "how_it_changed_me": how_it_changed_me,
            "what_i_promise": what_i_promise,
            "reminder_for_future": reminder_for_future
        },
        "metadata": {
            "captured_at": datetime.now().isoformat(),
            "reflection_count": 1
        }
    }
    return content_json


def generate_embedding_text_from_emotion(content_json: Dict) -> str:
    """
    Generate text for embedding from emotion content_json

    Combines: primary emotion + david_words + why_it_matters + emotion_tags + intensity_tags

    Args:
        content_json: Output from build_emotion_content_json()

    Returns:
        Text string ready for embedding generation
    """
    parts = [
        content_json['emotion']['primary'],
        content_json['context']['david_words'],
        content_json['significance']['why_it_matters'],
        ' '.join(content_json['tags'].get('emotion_tags', [])),
        ' '.join(content_json['tags'].get('intensity_tags', [])),
        ' '.join(content_json['tags'].get('memory_strength_tags', [])),
    ]

    return ' '.join([p for p in parts if p])
