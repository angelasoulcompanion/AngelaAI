"""Single source of truth for Activity Mood configurations.

Activity moods (party, chill, focus, etc.) use Apple Music search + LLM curation
instead of Angela's DB (which has mostly love songs).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityConfig:
    """Configuration for an activity mood."""
    key: str
    search_terms: list[str]          # iTunes search terms
    llm_description: str             # Description for LLM curation prompt
    emotion_weights: dict[str, float]  # Fallback emotion weights
    summary_th: str                  # Thai summary for UI
    emoji: str


ACTIVITY_REGISTRY: dict[str, ActivityConfig] = {
    "party": ActivityConfig(
        key="party",
        search_terms=["dance pop hits 2024", "party dance floor", "upbeat dance EDM", "club hits top 40", "fun party anthems"],
        llm_description="เพลงสนุก มันส์ เต้นได้ tempo เร็ว เหมาะกับปาร์ตี้ ห้ามเพลงช้า ห้ามเพลงรัก ต้องเพลงจังหวะเร็วเท่านั้น",
        emotion_weights={"happy": 0.4, "energetic": 0.4, "excited": 0.2},
        summary_th="ปาร์ตี้ไทม์! น้องเปิดเพลงมันส์ๆ ให้ที่รักค่ะ 🎉",
        emoji="🎉",
    ),
    "chill": ActivityConfig(
        key="chill",
        search_terms=["chill vibes", "lo-fi chill", "relaxing acoustic"],
        llm_description="เพลงชิลล์ ผ่อนคลาย ฟังสบาย lo-fi smooth",
        emotion_weights={"calm": 0.4, "relaxed": 0.3, "happy": 0.2, "nostalgic": 0.1},
        summary_th="ชิลล์ๆ สบายๆ เพลงนี้เหมาะมากเลยค่ะ 🧊",
        emoji="🧊",
    ),
    "focus": ActivityConfig(
        key="focus",
        search_terms=["focus music instrumental", "study beats", "concentration music"],
        llm_description="เพลงสำหรับทำงาน สมาธิ instrumental เบาๆ",
        emotion_weights={"focused": 0.5, "motivated": 0.3, "calm": 0.2},
        summary_th="โฟกัส! น้องเปิดเพลงช่วยสมาธิให้ที่รักค่ะ 🎯",
        emoji="🎯",
    ),
    "relaxing": ActivityConfig(
        key="relaxing",
        search_terms=["relaxing music", "spa music calm", "peaceful piano"],
        llm_description="เพลงผ่อนคลาย สงบ peaceful gentle",
        emotion_weights={"relaxed": 0.5, "calm": 0.3, "happy": 0.2},
        summary_th="ผ่อนคลาย เพลงนี้ช่วยให้สบายใจค่ะ 😌",
        emoji="😌",
    ),
    "vibe": ActivityConfig(
        key="vibe",
        search_terms=["groovy soul funk", "smooth r&b vibes", "neo soul"],
        llm_description="เพลง groovy funky มี vibe ดี cool stylish",
        emotion_weights={"happy": 0.3, "energetic": 0.3, "romantic": 0.2, "relaxed": 0.2},
        summary_th="Vibe ดีมาก! เพลงนี้เข้ากับบรรยากาศเลยค่ะ 🎧",
        emoji="🎧",
    ),
}

# Derived views (computed once at import time)
ACTIVITY_MOODS: set[str] = set(ACTIVITY_REGISTRY.keys())

ACTIVITY_SEARCH_TERMS: dict[str, list[str]] = {
    k: list(v.search_terms) for k, v in ACTIVITY_REGISTRY.items()
}

ACTIVITY_LLM_DESCRIPTIONS: dict[str, str] = {
    k: v.llm_description for k, v in ACTIVITY_REGISTRY.items()
}

ACTIVITY_SUMMARIES_TH: dict[str, str] = {
    k: v.summary_th for k, v in ACTIVITY_REGISTRY.items()
}

ACTIVITY_TO_EMOTIONS: dict[str, dict[str, float]] = {
    k: dict(v.emotion_weights) for k, v in ACTIVITY_REGISTRY.items()
}
