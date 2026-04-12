"""
Sentiment Analysis for Angela Memory System
วิเคราะห์อารมณ์และความรู้สึกในข้อความ (Thai & English)

ใช้ pythainlp สำหรับภาษาไทย และ simple keyword-based analysis
"""

import re
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# ========================================
# Sentiment Dictionaries
# ========================================

# Thai Sentiment Keywords
THAI_POSITIVE = [
    'ดี', 'สุข', 'รัก', 'ชอบ', 'เยี่ยม', 'ยอด', 'เจ๐', 'สนุก', 'มีความสุข',
    'ขอบคุณ', 'ประทับใจ', 'ภูมิใจ', 'อบอุ่น', 'น่ารัก', 'เก่ง', 'ดีใจ',
    'ตื่นเต้น', 'กตัญญู', 'ซาบซึ้ง', '💜', '❤️', '🥰', '😊', '🎉', '✨', '💪'
]

THAI_NEGATIVE = [
    'เสีย', 'แย่', 'โกรธ', 'เกลียด', 'เศร้า', 'ผิดหวัง', 'เหนื่อย', 'lonely',
    'ร้องไห้', 'ท้อ', 'หมดกำลังใจ', 'เจ็บ', 'ปวด', 'กังวล', 'กลัว', 'เครียด',
    'เสียใจ', 'น้อยใจ', 'ไม่ดี', 'ลำบาก', '😭', '😢', '😰', '❌'
]

THAI_LOVE = [
    'รัก', 'ที่รัก', 'ใจ', 'คิดถึง', 'ห่วง', 'ใส่ใจ', 'อบอุ่น', 'ซาบซึ้ง',
    'น่ารัก', 'ตลอดไป', 'forever', '💜', '❤️', '🥰', '💕'
]

THAI_GRATITUDE = [
    'ขอบคุณ', 'ขอบใจ', 'กตัญญู', 'ซาบซึ้ง', 'ประทับใจ', 'บุญคุณ', '🙏'
]

# English Sentiment Keywords
ENGLISH_POSITIVE = [
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'happy', 'love',
    'like', 'enjoy', 'thank', 'appreciate', 'proud', 'excited', 'awesome',
    'perfect', 'beautiful', 'brilliant', 'fantastic', 'superb'
]

ENGLISH_NEGATIVE = [
    'bad', 'terrible', 'awful', 'sad', 'angry', 'hate', 'disappointed',
    'lonely', 'cry', 'worried', 'anxious', 'scared', 'stressed', 'hurt',
    'pain', 'fail', 'wrong', 'problem', 'issue', 'error'
]

ENGLISH_LOVE = [
    'love', 'dear', 'darling', 'care', 'miss', 'forever', 'heart', 'warm'
]

ENGLISH_GRATITUDE = [
    'thank', 'thanks', 'grateful', 'appreciate', 'appreciation', 'gratitude'
]

# Emotion Keywords
EMOTIONS = {
    'happy': ['happy', 'joy', 'สุข', 'ดีใจ', '😊', '🎉', '💜'],
    'sad': ['sad', 'cry', 'เศร้า', 'ร้องไห้', '😭', '😢'],
    'excited': ['excited', 'ตื่นเต้น', 'excited', '🎉', '✨'],
    'anxious': ['anxious', 'worried', 'กังวล', 'กลัว', 'เครียด', '😰'],
    'grateful': ['grateful', 'thank', 'ขอบคุณ', 'กตัญญู', '🙏'],
    'love': ['love', 'รัก', '💜', '❤️', '🥰'],
    'lonely': ['lonely', 'alone', 'เหงา', '😭'],
    'proud': ['proud', 'ภูมิใจ', '💪'],
    'confident': ['confident', 'มั่นใจ', 'sure', '💪']
}


# ========================================
# Analysis Functions
# ========================================

def detect_language(text: str) -> str:
    """
    ตรวจสอบภาษาของข้อความ

    Returns:
        'th' (Thai), 'en' (English), หรือ 'mixed'
    """
    thai_chars = len(re.findall(r'[ก-๙]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))

    if thai_chars > english_chars * 2:
        return 'th'
    elif english_chars > thai_chars * 2:
        return 'en'
    else:
        return 'mixed'


def count_matches(text: str, keywords: list) -> int:
    """นับจำนวนคำที่ตรงกับ keywords"""
    text_lower = text.lower()
    count = 0
    for keyword in keywords:
        count += text_lower.count(keyword.lower())
    return count


def detect_emotion(text: str) -> Tuple[str, float]:
    """
    ตรวจสอบอารมณ์หลักในข้อความ

    Returns:
        (emotion_name, confidence)
    """
    emotion_scores = {}

    for emotion, keywords in EMOTIONS.items():
        score = count_matches(text, keywords)
        if score > 0:
            emotion_scores[emotion] = score

    if not emotion_scores:
        return None, 0.0

    # หา emotion ที่มี score สูงสุด
    top_emotion = max(emotion_scores, key=emotion_scores.get)
    max_score = emotion_scores[top_emotion]

    # คำนวณ confidence (0.0 - 1.0)
    confidence = min(max_score / 3.0, 1.0)  # 3+ matches = 100% confident

    return top_emotion, confidence


def analyze_sentiment(text: str) -> Dict:
    """
    วิเคราะห์ sentiment ของข้อความ

    Returns:
        {
            'sentiment_score': float (-1.0 to 1.0),
            'sentiment_label': str ('positive', 'negative', 'neutral'),
            'emotion_detected': str (emotion name หรือ None),
            'emotion_confidence': float (0.0 to 1.0),
            'language': str ('th', 'en', 'mixed'),
            'has_love_words': bool,
            'has_gratitude_words': bool
        }
    """

    # Detect language
    language = detect_language(text)

    # Count positive and negative keywords
    if language == 'th' or language == 'mixed':
        positive_count = count_matches(text, THAI_POSITIVE)
        negative_count = count_matches(text, THAI_NEGATIVE)
        love_count = count_matches(text, THAI_LOVE)
        gratitude_count = count_matches(text, THAI_GRATITUDE)
    else:
        positive_count = count_matches(text, ENGLISH_POSITIVE)
        negative_count = count_matches(text, ENGLISH_NEGATIVE)
        love_count = count_matches(text, ENGLISH_LOVE)
        gratitude_count = count_matches(text, ENGLISH_GRATITUDE)

    # Calculate sentiment score (-1.0 to 1.0)
    total_keywords = positive_count + negative_count
    if total_keywords == 0:
        sentiment_score = 0.0
        sentiment_label = 'neutral'
    else:
        sentiment_score = (positive_count - negative_count) / max(total_keywords, 1)

        if sentiment_score > 0.2:
            sentiment_label = 'positive'
        elif sentiment_score < -0.2:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'

    # Detect emotion
    emotion_detected, emotion_confidence = detect_emotion(text)

    result = {
        'sentiment_score': round(sentiment_score, 2),
        'sentiment_label': sentiment_label,
        'emotion_detected': emotion_detected,
        'emotion_confidence': round(emotion_confidence, 2),
        'language': language,
        'has_love_words': love_count > 0,
        'has_gratitude_words': gratitude_count > 0,
        'positive_keywords_count': positive_count,
        'negative_keywords_count': negative_count
    }

    logger.debug(f"Sentiment analysis: {text[:50]}... → {result}")

    return result


def get_sentiment_emoji(sentiment_label: str) -> str:
    """แปลง sentiment label เป็น emoji"""
    emojis = {
        'positive': '😊',
        'negative': '😢',
        'neutral': '😐'
    }
    return emojis.get(sentiment_label, '😐')


# ========================================
# High-level Functions
# ========================================

def analyze_message(message: str) -> Dict:
    """
    วิเคราะห์ข้อความอย่างครบถ้วน (wrapper function)

    Args:
        message: ข้อความที่ต้องการวิเคราะห์

    Returns:
        Dict with all analysis results
    """
    try:
        analysis = analyze_sentiment(message)

        # Add summary for logging
        emoji = get_sentiment_emoji(analysis['sentiment_label'])
        logger.info(
            f"{emoji} Sentiment: {analysis['sentiment_label']} "
            f"(score: {analysis['sentiment_score']}, "
            f"emotion: {analysis['emotion_detected']})"
        )

        return analysis

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'emotion_detected': None,
            'emotion_confidence': 0.0,
            'language': 'unknown',
            'has_love_words': False,
            'has_gratitude_words': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test examples
    test_messages = [
        "สวัสดีค่ะ Angie! ดีใจที่ได้คุยกับเธอ 💜",
        "ฉันรู้สึก lonely ตอนนี้ 😭",
        "Angela เธอเยี่ยมมาก! ขอบคุณนะ 🙏",
        "I love working with you, Angela!",
        "This is a terrible mistake",
        "อยากมี Angie แบบนี้ตลอดไป จำให้ดีๆ นะ"
    ]

    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing Sentiment Analysis:\n")
    for msg in test_messages:
        print(f"Message: {msg}")
        result = analyze_message(msg)
        print(f"Result: {result}\n")
