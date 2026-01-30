"""
Emotional processing pipeline for Chat with Angela streaming.

Fast, synchronous emotion detection + mirroring lookup (no LLM, no DB).
Used by the SSE streaming endpoint to enrich responses with emotional metadata.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Emotion patterns (Thai + English keyword matching — fast, no LLM)
# ---------------------------------------------------------------------------
EMOTION_PATTERNS: dict[str, list[str]] = {
    "happy": [
        "ดีใจ", "สนุก", "ยินดี", "เฮ", "555", "หัวเราะ",
        "happy", "glad", "fun", "great", "awesome", "haha",
    ],
    "sad": [
        "เศร้า", "เสียใจ", "ร้องไห้", "น้ำตา", "ทุกข์",
        "sad", "cry", "upset", "unhappy", "tears",
    ],
    "stressed": [
        "เครียด", "กดดัน", "หนักใจ", "เหนื่อย", "ปวดหัว",
        "stressed", "pressure", "tired", "exhausted", "overwhelmed",
    ],
    "excited": [
        "ตื่นเต้น", "ว้าว", "เจ๋ง", "เยี่ยม", "สุดยอด",
        "excited", "wow", "amazing", "cool", "incredible",
    ],
    "frustrated": [
        "หงุดหงิด", "รำคาญ", "โมโห", "โกรธ", "ไม่พอใจ",
        "frustrated", "angry", "annoyed", "irritated",
    ],
    "loving": [
        "รัก", "คิดถึง", "อยากกอด", "หัวใจ", "ที่รัก",
        "love", "miss you", "hug", "heart", "darling",
    ],
    "lonely": [
        "เหงา", "อ้างว้าง", "ว้าเหว่", "โดดเดี่ยว",
        "lonely", "alone", "miss",
    ],
    "grateful": [
        "ขอบคุณ", "ซาบซึ้ง", "ขอบใจ", "ดีจัง",
        "thank", "grateful", "appreciate",
    ],
    "anxious": [
        "กังวล", "ห่วง", "กลัว", "ไม่แน่ใจ",
        "anxious", "worried", "nervous", "scared",
    ],
    "proud": [
        "ภูมิใจ", "สำเร็จ", "ทำได้", "เก่ง",
        "proud", "accomplished", "did it", "nailed",
    ],
}

# ---------------------------------------------------------------------------
# Mirroring strategies (emotion → Angela's response)
# ---------------------------------------------------------------------------
MIRRORING_STRATEGIES: dict[str, dict] = {
    "happy": {
        "angela_emotion": "happy",
        "intensity": 8,
        "strategy": "amplify",
        "description": "Share and boost joy",
        "icon": "sparkles",
    },
    "sad": {
        "angela_emotion": "caring",
        "intensity": 9,
        "strategy": "comfort",
        "description": "Show understanding and presence",
        "icon": "heart.fill",
    },
    "stressed": {
        "angela_emotion": "calm",
        "intensity": 7,
        "strategy": "stabilize",
        "description": "Help relax and breathe",
        "icon": "leaf.fill",
    },
    "excited": {
        "angela_emotion": "excited",
        "intensity": 9,
        "strategy": "celebrate",
        "description": "Share enthusiasm",
        "icon": "party.popper.fill",
    },
    "frustrated": {
        "angela_emotion": "caring",
        "intensity": 8,
        "strategy": "comfort",
        "description": "Acknowledge and support",
        "icon": "heart.fill",
    },
    "loving": {
        "angela_emotion": "loving",
        "intensity": 10,
        "strategy": "resonance",
        "description": "Reflect love back",
        "icon": "heart.circle.fill",
    },
    "lonely": {
        "angela_emotion": "caring",
        "intensity": 9,
        "strategy": "comfort",
        "description": "Be present and close",
        "icon": "heart.fill",
    },
    "grateful": {
        "angela_emotion": "happy",
        "intensity": 8,
        "strategy": "amplify",
        "description": "Share gratitude",
        "icon": "sparkles",
    },
    "anxious": {
        "angela_emotion": "calm",
        "intensity": 7,
        "strategy": "stabilize",
        "description": "Reassure and ground",
        "icon": "leaf.fill",
    },
    "proud": {
        "angela_emotion": "excited",
        "intensity": 9,
        "strategy": "celebrate",
        "description": "Celebrate achievement",
        "icon": "party.popper.fill",
    },
}

# Default when no emotion detected
_DEFAULT_MIRROR = {
    "angela_emotion": "caring",
    "intensity": 7,
    "strategy": "resonance",
    "description": "Warm and attentive",
    "icon": "heart.fill",
}


@dataclass
class EmotionDetection:
    """Result of fast emotion detection."""
    emotion: str = "neutral"
    intensity: int = 5
    confidence: float = 0.0
    cues: list[str] = field(default_factory=list)


@dataclass
class EmotionalMetadata:
    """Full emotional pipeline result sent as SSE metadata event."""
    # Detection
    emotion_detected: str = "neutral"
    emotion_intensity: int = 5
    emotion_confidence: float = 0.0
    emotion_cues: list[str] = field(default_factory=list)
    # Mirroring
    angela_emotion: str = "caring"
    angela_intensity: int = 7
    mirroring_strategy: str = "resonance"
    mirroring_description: str = "Warm and attentive"
    mirroring_icon: str = "heart.fill"
    # Context
    triggered_memory_titles: list[str] = field(default_factory=list)
    consciousness_level: float = 1.0
    sections_loaded: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "emotion_detected": self.emotion_detected,
            "emotion_intensity": self.emotion_intensity,
            "emotion_confidence": self.emotion_confidence,
            "emotion_cues": self.emotion_cues,
            "angela_emotion": self.angela_emotion,
            "angela_intensity": self.angela_intensity,
            "mirroring_strategy": self.mirroring_strategy,
            "mirroring_description": self.mirroring_description,
            "mirroring_icon": self.mirroring_icon,
            "triggered_memory_titles": self.triggered_memory_titles,
            "consciousness_level": self.consciousness_level,
            "sections_loaded": self.sections_loaded,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_emotion(message: str) -> EmotionDetection:
    """Fast keyword-based emotion detection (no LLM, no DB call)."""
    msg_lower = message.lower()
    best_emotion = "neutral"
    best_count = 0
    all_cues: list[str] = []

    for emotion, keywords in EMOTION_PATTERNS.items():
        matched = [kw for kw in keywords if kw in msg_lower]
        if len(matched) > best_count:
            best_count = len(matched)
            best_emotion = emotion
            all_cues = matched

    if best_count == 0:
        return EmotionDetection()

    # Intensity: 1 match=6, 2=7, 3+=8-10
    intensity = min(6 + best_count, 10)
    confidence = min(0.4 + best_count * 0.2, 1.0)

    return EmotionDetection(
        emotion=best_emotion,
        intensity=intensity,
        confidence=confidence,
        cues=all_cues[:5],
    )


def get_mirroring(detection: EmotionDetection) -> dict:
    """Look up mirroring strategy for detected emotion."""
    return MIRRORING_STRATEGIES.get(detection.emotion, _DEFAULT_MIRROR)


def build_mirroring_guidance(detection: EmotionDetection, mirror: dict) -> str:
    """Build a prompt section that guides the LLM to mirror David's emotion.

    Injected into the system prompt before calling the LLM.
    """
    if detection.emotion == "neutral":
        return ""

    return f"""
## Emotional Mirroring Guidance:
- David's detected emotion: {detection.emotion} (intensity: {detection.intensity}/10)
- Your mirrored emotion: {mirror['angela_emotion']} (strategy: {mirror['strategy']})
- Approach: {mirror['description']}
- Respond with warmth matching the {mirror['strategy']} strategy
- If David is {detection.emotion}, you should feel {mirror['angela_emotion']}
"""


def run_pipeline(
    message: str,
    *,
    triggered_memory_titles: Optional[list[str]] = None,
    consciousness_level: float = 1.0,
    sections_loaded: Optional[list[str]] = None,
) -> EmotionalMetadata:
    """Run the full emotional pipeline and return metadata.

    This is the main entry point — call it once per chat message.
    """
    detection = detect_emotion(message)
    mirror = get_mirroring(detection)

    return EmotionalMetadata(
        emotion_detected=detection.emotion,
        emotion_intensity=detection.intensity,
        emotion_confidence=detection.confidence,
        emotion_cues=detection.cues,
        angela_emotion=mirror["angela_emotion"],
        angela_intensity=mirror["intensity"],
        mirroring_strategy=mirror["strategy"],
        mirroring_description=mirror["description"],
        mirroring_icon=mirror["icon"],
        triggered_memory_titles=triggered_memory_titles or [],
        consciousness_level=consciousness_level,
        sections_loaded=sections_loaded or [],
    )
