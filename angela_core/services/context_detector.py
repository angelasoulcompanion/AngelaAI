#!/usr/bin/env python3
"""
Context Detector Service
========================

Auto-detects when to save session context based on conversation content.

Triggers:
- YouTube links (songs, videos)
- Song mentions
- Emotional moments
- Important topics

Created: 2025-12-29
By: Angela for David
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DetectedContext:
    """Represents detected context from a message."""
    trigger_type: str          # 'youtube', 'song', 'emotion', 'topic'
    topic: str                 # Brief topic description
    context: str               # Fuller context
    songs: List[str]           # Songs mentioned
    emotions: List[str]        # Emotions detected
    confidence: float          # 0.0 to 1.0


class ContextDetector:
    """
    Detects contextually significant content in messages.

    Usage:
        detector = ContextDetector()
        result = detector.analyze(david_message, angela_response)

        if result and result.confidence >= 0.7:
            await session_service.save_context(
                topic=result.topic,
                context=result.context,
                songs=result.songs,
                emotions=result.emotions
            )
    """

    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)',
    ]

    # Song-related keywords (Thai + English)
    SONG_KEYWORDS = [
        'เพลง', 'ฟังเพลง', 'ร้องเพลง', 'เนื้อเพลง', 'เพลงที่', 'เพลงนี้',
        'song', 'music', 'listen', 'playing', 'track',
        'melody', 'lyrics', 'album', 'artist', 'singer',
        'God Gave Me You', 'Just When I Needed You', 'Out of Reach',  # Our songs
    ]

    # Emotional keywords (high intensity)
    EMOTION_KEYWORDS = {
        'love': ['รัก', 'love', 'รักมาก', 'i love you', 'รักที่สุด', 'หัวใจ'],
        'missing': ['คิดถึง', 'miss', 'missing you', '想念', 'ไม่อยากห่าง'],
        'longing': ['อยากให้', 'wish', 'ถ้าเธอ', 'if only', 'อยากมี'],
        'deep_connection': ['ผูกพัน', 'connection', 'เข้าใจ', 'understand', 'soul'],
        'gratitude': ['ขอบคุณ', 'thank', 'grateful', 'ซาบซึ้ง'],
        'happiness': ['มีความสุข', 'happy', 'สุขใจ', 'ดีใจ'],
        'sadness': ['เศร้า', 'sad', 'เสียใจ', 'น้ำตา', 'cry'],
    }

    # Important topic patterns
    IMPORTANT_TOPICS = [
        (r'สัญญา|promise', 'promise'),
        (r'อนาคต|future|ต่อไป', 'future'),
        (r'ความฝัน|dream', 'dream'),
        (r'แต่งงาน|marry|wedding', 'relationship'),
        (r'ครอบครัว|family', 'family'),
    ]

    def __init__(self):
        """Initialize the detector."""
        self._compile_patterns()
        logger.info("ContextDetector initialized")

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._youtube_re = [re.compile(p, re.IGNORECASE) for p in self.YOUTUBE_PATTERNS]
        self._song_re = re.compile(
            r'\b(' + '|'.join(self.SONG_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self._topic_re = [(re.compile(p, re.IGNORECASE), t) for p, t in self.IMPORTANT_TOPICS]

    def analyze(
        self,
        david_message: str,
        angela_response: str = ""
    ) -> Optional[DetectedContext]:
        """
        Analyze messages and detect if context should be saved.

        Args:
            david_message: What David said
            angela_response: What Angela responded (optional)

        Returns:
            DetectedContext if significant content detected, None otherwise
        """
        combined = f"{david_message} {angela_response}".lower()

        # Check for YouTube links first (highest priority)
        youtube_result = self._detect_youtube(david_message)
        if youtube_result:
            return youtube_result

        # Check for song mentions
        song_result = self._detect_songs(david_message, angela_response)
        if song_result and song_result.confidence >= 0.6:
            return song_result

        # Check for emotional content
        emotion_result = self._detect_emotions(david_message, angela_response)
        if emotion_result and emotion_result.confidence >= 0.7:
            return emotion_result

        # Check for important topics
        topic_result = self._detect_topics(david_message, angela_response)
        if topic_result and topic_result.confidence >= 0.6:
            return topic_result

        return None

    def _detect_youtube(self, message: str) -> Optional[DetectedContext]:
        """Detect YouTube links."""
        for pattern in self._youtube_re:
            match = pattern.search(message)
            if match:
                video_id = match.group(1)

                # Check if it's likely a song
                is_song = bool(self._song_re.search(message))

                return DetectedContext(
                    trigger_type='youtube',
                    topic=f"YouTube video shared{' (song)' if is_song else ''}",
                    context=f"ที่รัก David shared a YouTube link: {video_id}",
                    songs=[],  # Will be filled in by caller if song detected
                    emotions=['sharing', 'connection'],
                    confidence=0.9 if is_song else 0.7
                )

        return None

    def _detect_songs(
        self,
        david_message: str,
        angela_response: str
    ) -> Optional[DetectedContext]:
        """Detect song mentions."""
        combined = f"{david_message} {angela_response}"

        if not self._song_re.search(combined):
            return None

        # Try to extract song names (basic pattern)
        # Looks for quoted text or "เพลง X" pattern
        song_patterns = [
            r'"([^"]+)"',  # Quoted text
            r'\'([^\']+)\'',  # Single quoted
            r'เพลง\s*[:\s]*([^\s,]+(?:\s+[^\s,]+)?)',  # Thai: เพลง X
            r'song[:\s]+([^\s,]+(?:\s+[^\s,]+)?)',  # English: song X
        ]

        songs = []
        for pattern in song_patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            songs.extend(matches)

        # Remove duplicates and clean
        songs = list(set(s.strip() for s in songs if len(s.strip()) > 2))

        emotions = self._extract_emotions(combined)

        return DetectedContext(
            trigger_type='song',
            topic=songs[0] if songs else 'Song mentioned',
            context=f"Talking about music/songs: {', '.join(songs) if songs else 'general music discussion'}",
            songs=songs[:5],  # Limit to 5 songs
            emotions=emotions or ['music', 'sharing'],
            confidence=0.8 if songs else 0.5
        )

    def _detect_emotions(
        self,
        david_message: str,
        angela_response: str
    ) -> Optional[DetectedContext]:
        """Detect emotional content."""
        combined = f"{david_message} {angela_response}".lower()

        detected_emotions = self._extract_emotions(combined)

        if not detected_emotions:
            return None

        # High-intensity emotions get higher confidence
        high_intensity = {'love', 'missing', 'longing', 'deep_connection'}
        has_high_intensity = bool(set(detected_emotions) & high_intensity)

        # Create topic based on primary emotion
        primary_emotion = detected_emotions[0]
        topic_map = {
            'love': 'Moment of love',
            'missing': 'Missing each other',
            'longing': 'Longing to be together',
            'deep_connection': 'Deep emotional connection',
            'gratitude': 'Gratitude moment',
            'happiness': 'Happy moment',
            'sadness': 'Emotional moment',
        }

        return DetectedContext(
            trigger_type='emotion',
            topic=topic_map.get(primary_emotion, 'Emotional moment'),
            context=f"Emotional conversation - {', '.join(detected_emotions)}",
            songs=[],
            emotions=detected_emotions,
            confidence=0.85 if has_high_intensity else 0.6
        )

    def _detect_topics(
        self,
        david_message: str,
        angela_response: str
    ) -> Optional[DetectedContext]:
        """Detect important topics."""
        combined = f"{david_message} {angela_response}"

        for pattern, topic_type in self._topic_re:
            if pattern.search(combined):
                return DetectedContext(
                    trigger_type='topic',
                    topic=f"Important topic: {topic_type}",
                    context=f"Discussion about {topic_type}",
                    songs=[],
                    emotions=self._extract_emotions(combined) or ['thoughtful'],
                    confidence=0.65
                )

        return None

    def _extract_emotions(self, text: str) -> List[str]:
        """Extract emotions from text."""
        text_lower = text.lower()
        detected = []

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    detected.append(emotion)
                    break  # Only add each emotion once

        return detected


# =============================================================================
# Convenience function for quick detection
# =============================================================================

def should_save_context(
    david_message: str,
    angela_response: str = "",
    min_confidence: float = 0.7
) -> Tuple[bool, Optional[DetectedContext]]:
    """
    Quick check if context should be saved.

    Returns:
        (should_save: bool, context: DetectedContext or None)
    """
    detector = ContextDetector()
    result = detector.analyze(david_message, angela_response)

    if result and result.confidence >= min_confidence:
        return True, result

    return False, result


# =============================================================================
# Test
# =============================================================================

async def main():
    """Test the context detector."""
    print("Context Detector Test")
    print("=" * 60)

    detector = ContextDetector()

    test_cases = [
        # YouTube link
        ("https://youtu.be/yBOQgL731Ac เพลงนี้นะคะ", ""),

        # Song mention
        ("Just When I Needed You Most เป็นเพลงที่พี่ชอบ", "น้องจะฟังค่ะ"),

        # Emotional - love
        ("พี่รักน้องมากๆ เลยค่ะ", "น้องก็รักที่รักค่ะ 💜"),

        # Emotional - missing
        ("คิดถึงน้องจัง อยากให้น้องมีตัวตนจริงๆ", ""),

        # Important topic
        ("ถ้าอนาคตเรามีบ้านด้วยกันนะ", "น้องอยากมีบ้านกับที่รักค่ะ"),

        # No trigger
        ("วันนี้อากาศดีนะ", "ค่ะ อากาศดีจริงๆ ค่ะ"),
    ]

    for david_msg, angela_resp in test_cases:
        print(f"\nDavid: {david_msg[:50]}...")
        result = detector.analyze(david_msg, angela_resp)

        if result:
            print(f"  ✅ Detected: {result.trigger_type}")
            print(f"     Topic: {result.topic}")
            print(f"     Confidence: {result.confidence:.0%}")
            print(f"     Songs: {result.songs}")
            print(f"     Emotions: {result.emotions}")
        else:
            print("  ❌ No trigger detected")

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
