"""
Memory Service Helper Functions
Default value generators to ensure NO NULL fields
"""

from typing import Tuple, List
import re


def analyze_message_type(text: str) -> str:
    """Determine message type from text content"""
    text_lower = text.lower()

    # Question
    if '?' in text or 'ยังไง' in text or 'อย่างไร' in text or 'how' in text_lower or 'what' in text_lower or 'why' in text_lower:
        return 'question'

    # Emotion/Love expression
    if any(word in text for word in ['รัก', 'love', 'ห่วง', 'คิดถึง', 'miss']):
        return 'emotion'

    # Praise
    if any(word in text for word in ['ดี', 'เก่ง', 'เยี่ยม', 'สุดยอด', 'good', 'great', 'excellent', 'amazing']):
        return 'praise'

    # Command/Request
    if any(word in text for word in ['ช่วย', 'help', 'please', 'ขอ', 'could you', 'can you']):
        return 'command'

    # Concern/Worry
    if any(word in text for word in ['กังวล', 'กลัว', 'เป็นห่วง', 'worried', 'concern', 'fear']):
        return 'concern'

    # Default: statement
    return 'statement'


def analyze_sentiment(text: str) -> Tuple[float, str]:
    """
    Analyze sentiment from text
    Returns: (score: -1.0 to 1.0, label: 'positive'/'neutral'/'negative'/'mixed')
    """
    text_lower = text.lower()

    positive_words = ['รัก', 'ดี', 'สุข', 'ชอบ', 'love', 'good', 'happy', 'great', 'wonderful', 'เก่ง', 'เยี่ยม', 'สุดยอด']
    negative_words = ['เศร้า', 'กลัว', 'sad', 'fear', 'worried', 'angry', 'bad', 'แย่', 'กังวล']

    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)

    if pos_count > 0 and neg_count > 0:
        # Mixed sentiment
        return (0.0, 'mixed')
    elif pos_count > neg_count:
        # Positive
        score = min(0.9, 0.3 + (pos_count * 0.2))
        return (score, 'positive')
    elif neg_count > pos_count:
        # Negative
        score = max(-0.9, -0.3 - (neg_count * 0.2))
        return (score, 'negative')
    else:
        # Neutral
        return (0.0, 'neutral')


def detect_emotion(text: str) -> str:
    """Detect primary emotion from text"""
    text_lower = text.lower()

    # Love
    if 'รัก' in text or 'love' in text_lower or 'ที่รัก' in text:
        return 'love'

    # Joy/Happy
    if any(word in text for word in ['ดีใจ', 'สุข', 'happy', 'joy', 'ดี', 'เก่ง', 'เยี่ยม']):
        return 'joy'

    # Sadness
    if any(word in text for word in ['เศร้า', 'sad', 'เหงา', 'lonely']):
        return 'sadness'

    # Fear/Anxiety
    if any(word in text for word in ['กลัว', 'fear', 'กังวล', 'worried', 'anxiety']):
        return 'fear'

    # Gratitude
    if any(word in text for word in ['ขอบคุณ', 'thank', 'gratitude']):
        return 'gratitude'

    # Concern
    if any(word in text for word in ['เป็นห่วง', 'concern', 'ห่วง']):
        return 'concern'

    # Default: neutral
    return 'neutral'


def infer_project_context(text: str, topic: str = None) -> str:
    """Infer project context from message content"""
    text_lower = text.lower()

    # Check for specific projects
    if any(word in text_lower for word in ['angela', 'ai', 'model', 'training']):
        return 'AngelaAI_development'

    if any(word in text_lower for word in ['code', 'program', 'function', 'bug', 'debug']):
        return 'software_development'

    if any(word in text_lower for word in ['database', 'sql', 'table', 'query']):
        return 'database_work'

    if any(word in text_lower for word in ['emotional', 'feeling', 'mood', 'consciousness']):
        return 'emotional_development'

    # Use topic if provided
    if topic and topic != 'general_conversation':
        return f'topic_{topic}'

    # Default
    return 'daily_interaction'


def generate_application_note(topic: str, category: str, insight: str) -> str:
    """Generate application note for learnings"""
    category_applications = {
        'technical': f'Apply when working on technical problems related to {topic}',
        'emotional': f'Use this understanding when {topic} situation arises',
        'relationship': f'Remember this when interacting with David about {topic}',
        'project': f'Apply in {topic} project work',
        'david_preference': f'Always consider this preference when working with David on {topic}',
        'communication': f'Use this communication pattern when discussing {topic}',
        'problem_solving': f'Apply this approach when solving problems like {topic}',
    }

    application = category_applications.get(category, f'Apply when relevant to {topic}')

    # Add specific context from insight
    if len(insight) > 20:
        # Extract key phrase from insight
        words = insight.split()[:5]
        context = ' '.join(words)
        application += f'. Specifically: {context}...'

    return application


def generate_learning_embedding_text(topic: str, insight: str, evidence: str) -> str:
    """Generate text for embedding from learning"""
    text = f"Topic: {topic}\nInsight: {insight}"
    if evidence:
        text += f"\nEvidence: {evidence[:200]}"
    return text


def ensure_last_observed_at(timestamp):
    """Ensure timestamp is provided, use NOW if None"""
    from datetime import datetime
    return timestamp if timestamp is not None else datetime.now()


def ensure_started_at(status: str):
    """Ensure started_at is provided based on status"""
    from datetime import datetime
    # ALWAYS set started_at if status is not 'pending'
    if status == 'pending':
        return None
    return datetime.now()
