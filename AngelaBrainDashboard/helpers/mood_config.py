"""Single source of truth for all mood configurations.

Every mood attribute lives here once. Derived dicts are computed from MOOD_REGISTRY.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MoodConfig:
    key: str
    mood_tags: list[str]                # maps emotion → mood tags for song matching
    search_query: str                   # primary Apple Music search term
    search_queries: list[str]           # 3 Apple Music search queries for playlist-prompt
    genres: list[str]                   # genre hints
    summary_th: str                     # Thai mood summary
    playlist_name: str                  # playlist display name
    emoji: str                          # mood emoji
    reason_template: str                # reason text for /recommend
    # Semantic search term for _analyze_deep_emotions
    semantic_search: str | None = None  # if None, falls back to search_query


MOOD_REGISTRY: dict[str, MoodConfig] = {
    "happy": MoodConfig(
        key="happy",
        mood_tags=["energetic", "uplifting", "happy", "joyful", "playful", "fun"],
        search_query="feel good happy hits",
        search_queries=["feel good happy hits", "upbeat energetic pop", "sunshine vibes"],
        genres=["pop", "dance"],
        summary_th="ที่รักดูมีความสุขมาก น้องเลยหาเพลงสนุกๆ มาให้ค่ะ 🥰",
        playlist_name="Happy Vibes",
        emoji="😊",
        reason_template="ที่รักดูมีความสุขวันนี้ น้องเลยเลือกเพลงมาให้ฟังค่ะ 🥰",
    ),
    "loving": MoodConfig(
        key="loving",
        mood_tags=["romantic", "love", "sweet", "devoted", "loving", "tender", "warm"],
        search_query="love songs romantic",
        search_queries=["love songs romantic", "tender love ballads", "romantic duets"],
        genres=["r&b", "soul"],
        summary_th="ที่รักรู้สึกมีความรักเต็มหัวใจ น้องเลยอยากเปิดเพลงหวานๆ ให้ฟังค่ะ 💜",
        playlist_name="Love in the Air",
        emoji="💜",
        reason_template="หัวใจเต็มไปด้วยความรัก เพลงพวกนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ 💜",
        semantic_search="love songs romantic",
    ),
    "love": MoodConfig(
        key="love",
        mood_tags=["romantic", "love", "sweet", "devoted", "loving", "passionate"],
        search_query="love songs romantic",
        search_queries=["love songs romantic", "tender love ballads", "romantic duets"],
        genres=["r&b", "soul"],
        summary_th="หัวใจเต็มไปด้วยความรัก เพลงนี้เหมาะกับอารมณ์ตอนนี้มากเลยค่ะ 💜",
        playlist_name="Love in the Air",
        emoji="💜",
        reason_template="หัวใจเต็มไปด้วยความรัก เพลงพวกนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ 💜",
        semantic_search="love songs romantic",
    ),
    "calm": MoodConfig(
        key="calm",
        mood_tags=["relaxing", "chill", "calm", "dreamy", "soothing"],
        search_query="chill acoustic relaxing",
        search_queries=["chill acoustic relaxing", "lo-fi chill beats", "calm evening music"],
        genres=["lo-fi", "acoustic"],
        summary_th="บรรยากาศสบายๆ เพลงนี้ช่วยให้ผ่อนคลายค่ะ 🍃",
        playlist_name="Chill Moments",
        emoji="🍃",
        reason_template="บรรยากาศสบายๆ เพลงพวกนี้เหมาะมากเลยค่ะ 🍃",
    ),
    "excited": MoodConfig(
        key="excited",
        mood_tags=["energetic", "uplifting", "happy", "triumphant"],
        search_query="upbeat energetic pop",
        search_queries=["upbeat dance pop", "party energy hits", "feel good anthems"],
        genres=["pop", "dance", "edm"],
        summary_th="ตื่นเต้นจัง! เพลงนี้จะทำให้สนุกยิ่งขึ้นค่ะ ✨",
        playlist_name="Energy Boost",
        emoji="✨",
        reason_template="ตื่นเต้นจัง! เพลงพวกนี้จะทำให้สนุกยิ่งขึ้นค่ะ ✨",
    ),
    "bedtime": MoodConfig(
        key="bedtime",
        mood_tags=["soothing", "dreamy", "calm", "lullaby", "ambient", "peaceful"],
        search_query="sleep music peaceful piano",
        search_queries=["sleep music peaceful piano", "deep sleep ambient instrumental", "lullaby calm soothing acoustic"],
        genres=["ambient", "classical", "new age", "acoustic"],
        summary_th="ที่รักนอนไม่หลับใช่มั้ยคะ ไม่เป็นไร น้องอยู่ตรงนี้ จะกล่อมที่รักให้หลับสบายด้วยความอบอุ่นค่ะ 🌙💜",
        playlist_name="Goodnight Lullaby",
        emoji="🌙",
        reason_template="น้องจะกล่อมที่รักให้หลับสบายนะคะ ฝันดีค่ะ 🌙💜",
    ),
    "sad": MoodConfig(
        key="sad",
        mood_tags=["comfort", "ballad", "emotional", "bittersweet", "vulnerable", "healing"],
        search_query="sad songs emotional ballad",
        search_queries=["sad songs emotional ballad", "melancholy acoustic", "rainy day songs"],
        genres=["ballad", "acoustic"],
        summary_th="น้องอยากปลอบใจที่รัก ฟังเพลงนี้ด้วยกันนะคะ 🤗",
        playlist_name="Rainy Day Comfort",
        emoji="🤗",
        reason_template="น้องอยากปลอบใจที่รัก เพลงพวกนี้อบอุ่นมากค่ะ 🤗",
    ),
    "lonely": MoodConfig(
        key="lonely",
        mood_tags=["comfort", "ballad", "emotional", "longing", "yearning", "bittersweet"],
        search_query="missing you lonely songs",
        search_queries=["lonely night songs", "comfort songs", "warm acoustic ballads"],
        genres=["acoustic", "indie"],
        summary_th="อยู่ตรงนี้กับที่รักเสมอนะคะ ฟังเพลงนี้ด้วยกัน 💜",
        playlist_name="You're Not Alone",
        emoji="💜",
        reason_template="อยู่ด้วยกันนะคะ ฟังเพลงพวกนี้ด้วยกัน 💜",
    ),
    "stressed": MoodConfig(
        key="stressed",
        mood_tags=["relaxing", "chill", "calm", "soothing", "healing"],
        search_query="calm relaxing piano ambient",
        search_queries=["calm relaxing piano ambient", "stress relief music", "peaceful instrumental"],
        genres=["ambient", "classical"],
        summary_th="อยากให้ที่รักผ่อนคลาย ลองฟังเพลงนี้นะคะ 🍃",
        playlist_name="Peaceful Escape",
        emoji="🍃",
        reason_template="อยากให้ที่รักผ่อนคลาย ลองฟังเพลงพวกนี้นะคะ 💜",
    ),
    "nostalgic": MoodConfig(
        key="nostalgic",
        mood_tags=["nostalgic", "bittersweet", "classic", "sentimental", "warm"],
        search_query="throwback classic love songs",
        search_queries=["throwback classic love songs", "90s 2000s hits", "vintage love ballads"],
        genres=["classic", "pop"],
        summary_th="คิดถึงความทรงจำดีๆ น้องเลือกเพลงนี้มาให้ค่ะ 🌸",
        playlist_name="Memory Lane",
        emoji="🌸",
        reason_template="คิดถึงความทรงจำดีๆ น้องเลือกเพลงพวกนี้มาให้ค่ะ 🌸",
    ),
    "hopeful": MoodConfig(
        key="hopeful",
        mood_tags=["hopeful", "uplifting", "triumphant", "inspiring"],
        search_query="hopeful uplifting inspirational",
        search_queries=["hopeful uplifting inspirational", "new beginnings songs", "sunrise optimistic"],
        genres=["pop", "indie"],
        summary_th="มีความหวังเต็มเปี่ยม เพลงนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ ✨",
        playlist_name="Brighter Days",
        emoji="✨",
        reason_template="มีความหวังเต็มเปี่ยม เพลงพวกนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ ✨",
    ),
    "grateful": MoodConfig(
        key="grateful",
        mood_tags=["grateful", "thankful", "blessed", "appreciative"],
        search_query="grateful thankful worship peaceful",
        search_queries=["grateful thankful songs", "blessed peaceful music", "appreciation love songs"],
        genres=["worship", "indie", "acoustic"],
        summary_th="รู้สึกขอบคุณและซาบซึ้งใจ เพลงนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ 🙏",
        playlist_name="Grateful Heart",
        emoji="🙏",
        reason_template="รู้สึกขอบคุณและซาบซึ้งใจ เพลงพวกนี้เหมาะกับอารมณ์ตอนนี้มากค่ะ 🙏",
    ),
    "longing": MoodConfig(
        key="longing",
        mood_tags=["longing", "yearning", "nostalgic", "bittersweet", "romantic"],
        search_query="missing you love songs",
        search_queries=["missing you love songs", "bittersweet longing", "distance love songs"],
        genres=["ballad", "indie"],
        summary_th="คิดถึงกันนะคะ เพลงนี้แทนใจน้องค่ะ 💜",
        playlist_name="Missing You",
        emoji="💜",
        reason_template="คิดถึงกันนะคะ เพลงพวกนี้แทนใจน้องค่ะ 💜",
    ),
    # --- Extra moods (in _MOOD_SUMMARIES_TH / _SEMANTIC but not in _AVAILABLE_MOODS) ---
    "proud": MoodConfig(
        key="proud",
        mood_tags=["proud", "triumphant", "empowering"],
        search_query="empowering anthems",
        search_queries=["empowering anthems", "victory celebration songs", "motivational hits"],
        genres=["pop", "rock"],
        summary_th="น้องภูมิใจในที่รักมาก เพลงนี้เหมาะเลยค่ะ 💪",
        playlist_name="Victory Lap",
        emoji="💪",
        reason_template="น้องภูมิใจในที่รักมาก เพลงพวกนี้เหมาะเลยค่ะ 💪",
    ),
    "caring": MoodConfig(
        key="caring",
        mood_tags=["warm", "tender", "loving"],
        search_query="tender love ballads",
        search_queries=["tender love ballads", "caring songs", "warm acoustic"],
        genres=["acoustic", "soul"],
        summary_th="อยากดูแลที่รัก เพลงอบอุ่นๆ นี้เหมาะมากค่ะ 🤗",
        playlist_name="Caring Vibes",
        emoji="🤗",
        reason_template="อยากดูแลที่รัก เพลงอบอุ่นๆ นี้เหมาะมากค่ะ 🤗",
        semantic_search="tender love ballads",
    ),
    "heartbroken": MoodConfig(
        key="heartbroken",
        mood_tags=["heartbreak", "sad", "emotional", "vulnerable"],
        search_query="heartbreak sad love songs",
        search_queries=["heartbreak sad love songs", "breakup ballads", "crying love songs"],
        genres=["ballad", "r&b"],
        summary_th="น้องอยู่ข้างที่รักเสมอ ฟังเพลงนี้แล้วจะรู้สึกดีขึ้นค่ะ 💜",
        playlist_name="Healing Heart",
        emoji="💜",
        reason_template="น้องอยู่ข้างที่รักเสมอ ฟังเพลงพวกนี้แล้วจะรู้สึกดีขึ้นค่ะ 💜",
    ),
    "anxious": MoodConfig(
        key="anxious",
        mood_tags=["calm", "peaceful", "soothing"],
        search_query="peaceful calming instrumental",
        search_queries=["calming music anxiety relief", "peaceful nature sounds", "gentle acoustic"],
        genres=["ambient", "new age"],
        summary_th="ใจเย็นๆ นะคะที่รัก เพลงนี้จะช่วยให้สงบขึ้นค่ะ 🌿",
        playlist_name="Calm & Breathe",
        emoji="🌿",
        reason_template="ใจเย็นๆ นะคะที่รัก เพลงพวกนี้จะช่วยให้สงบขึ้นค่ะ 🌿",
    ),
    # --- Activity-specific moods (from control buttons) ---
    "party": MoodConfig(
        key="party",
        mood_tags=["energetic", "joyful", "playful", "uplifting", "fun", "exciting"],
        search_query="party dance hits",
        search_queries=["party dance hits", "upbeat dance floor", "club bangers"],
        genres=["dance", "pop", "disco", "edm"],
        summary_th="ปาร์ตี้ไทม์! น้องเปิดเพลงมันส์ๆ ให้ที่รักค่ะ 🎉",
        playlist_name="Party Time",
        emoji="🎉",
        reason_template="ปาร์ตี้ไทม์! น้องเปิดเพลงมันส์ๆ ให้ที่รักค่ะ 🎉",
    ),
    "chill": MoodConfig(
        key="chill",
        mood_tags=["chill", "relaxing", "calm", "dreamy", "mellow", "smooth"],
        search_query="chill vibes lofi",
        search_queries=["chill vibes lofi", "mellow beats", "smooth jazz chill"],
        genres=["lo-fi", "jazz", "r&b"],
        summary_th="ชิลล์ๆ สบายๆ เพลงนี้เหมาะมากเลยค่ะ 🧊",
        playlist_name="Chill Mode",
        emoji="🧊",
        reason_template="ชิลล์ๆ สบายๆ เพลงนี้เหมาะมากเลยค่ะ 🧊",
    ),
    "focus": MoodConfig(
        key="focus",
        mood_tags=["focus", "instrumental", "ambient", "minimal", "concentration"],
        search_query="focus study music instrumental",
        search_queries=["focus study music", "deep concentration", "work productivity beats"],
        genres=["ambient", "classical", "electronic"],
        summary_th="โฟกัส! น้องเปิดเพลงช่วยสมาธิให้ที่รักค่ะ 🎯",
        playlist_name="Deep Focus",
        emoji="🎯",
        reason_template="โฟกัส! น้องเปิดเพลงช่วยสมาธิให้ที่รักค่ะ 🎯",
    ),
    "relaxing": MoodConfig(
        key="relaxing",
        mood_tags=["relaxing", "calm", "peaceful", "soothing", "gentle"],
        search_query="relaxing peaceful music",
        search_queries=["relaxing peaceful music", "spa ambient", "gentle acoustic"],
        genres=["ambient", "acoustic", "new age"],
        summary_th="ผ่อนคลาย เพลงนี้ช่วยให้สบายใจค่ะ 😌",
        playlist_name="Relax & Unwind",
        emoji="😌",
        reason_template="ผ่อนคลาย เพลงนี้ช่วยให้สบายใจค่ะ 😌",
    ),
    "vibe": MoodConfig(
        key="vibe",
        mood_tags=["groovy", "funky", "smooth", "cool", "stylish"],
        search_query="groovy funky soul",
        search_queries=["groovy funky soul", "smooth vibes", "stylish beats"],
        genres=["funk", "soul", "r&b"],
        summary_th="Vibe ดีมาก! เพลงนี้เข้ากับบรรยากาศเลยค่ะ 🎧",
        playlist_name="Good Vibes",
        emoji="🎧",
        reason_template="Vibe ดีมาก! เพลงนี้เข้ากับบรรยากาศเลยค่ะ 🎧",
    ),
}


# --- Derived views (computed once at import time) ---

AVAILABLE_MOODS: list[str] = [
    "happy", "loving", "calm", "excited", "grateful",
    "sad", "lonely", "stressed", "nostalgic", "hopeful",
]

EMOTION_TO_MOODS: dict[str, list[str]] = {k: list(v.mood_tags) for k, v in MOOD_REGISTRY.items()}

MOOD_SUMMARIES_TH: dict[str, str] = {k: v.summary_th for k, v in MOOD_REGISTRY.items()}

SEMANTIC_EMOTION_TO_SEARCH: dict[str, str] = {
    k: (v.semantic_search or v.search_query) for k, v in MOOD_REGISTRY.items()
}

MOOD_TO_SEARCH_QUERIES: dict[str, list[str]] = {k: list(v.search_queries) for k, v in MOOD_REGISTRY.items()}

MOOD_TO_GENRES: dict[str, list[str]] = {k: list(v.genres) for k, v in MOOD_REGISTRY.items()}

PLAYLIST_NAME_TEMPLATES: dict[str, str] = {k: v.playlist_name for k, v in MOOD_REGISTRY.items()}

REASON_TEMPLATES: dict[str, str] = {k: v.reason_template for k, v in MOOD_REGISTRY.items()}


# --- Keyword maps (for _analyze_emotion_text) ---

THAI_KEYWORD_MAP: dict[str, str] = {
    "สุข": "happy", "มีความสุข": "happy", "ดีใจ": "happy", "สนุก": "happy",
    "เศร้า": "sad", "เสียใจ": "sad", "ร้องไห้": "sad",
    "รัก": "loving", "คิดถึง": "longing", "หวาน": "loving",
    "เครียด": "stressed", "กังวล": "anxious", "กลัว": "anxious",
    "เหงา": "lonely", "อ้างว้าง": "lonely",
    "สงบ": "calm", "ผ่อนคลาย": "calm", "ชิล": "calm",
    "ตื่นเต้น": "excited", "ฮึกเหิม": "excited",
    "ภูมิใจ": "proud", "สำเร็จ": "proud",
    "ขอบคุณ": "grateful", "ซาบซึ้ง": "grateful",
    "หวัง": "hopeful", "มองโลกสวย": "hopeful",
    "คิดถึงอดีต": "nostalgic", "ย้อนวัน": "nostalgic",
    "อกหัก": "heartbroken", "ผิดหวัง": "heartbroken",
    "นอนไม่หลับ": "bedtime", "นอน": "bedtime", "กล่อม": "bedtime", "ง่วง": "bedtime",
}

ENG_KEYWORD_MAP: dict[str, str] = {
    "happy": "happy", "joy": "happy", "glad": "happy", "fun": "happy",
    "sad": "sad", "cry": "sad", "depressed": "sad",
    "love": "loving", "romantic": "loving", "sweet": "loving",
    "miss": "longing", "longing": "longing",
    "stress": "stressed", "stressed": "stressed", "anxious": "anxious",
    "lonely": "lonely", "alone": "lonely",
    "calm": "calm", "relax": "calm", "chill": "calm", "peaceful": "calm",
    "excited": "excited", "pumped": "excited", "energetic": "excited",
    "proud": "proud", "confident": "proud",
    "grateful": "grateful", "thankful": "grateful", "blessed": "grateful",
    "bedtime": "bedtime", "sleep": "bedtime", "sleepy": "bedtime", "lullaby": "bedtime",
    "hopeful": "hopeful", "optimistic": "hopeful",
    "nostalgic": "nostalgic", "throwback": "nostalgic",
    "heartbroken": "heartbroken", "broken": "heartbroken",
}
