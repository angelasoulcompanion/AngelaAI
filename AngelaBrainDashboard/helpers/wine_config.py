"""Single source of truth for all 19 wine configurations.

Every wine attribute lives here once. Derived dicts are computed from WINE_REGISTRY.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WineConfig:
    key: str
    display_name: str
    category: str          # "Bold Reds", "Elegant Reds", "White & Light", "Sparkling", "Rose & Sweet"
    emoji: str             # "🍷", "🥂", "🍾", "🌹"
    emotion: str           # maps to _EMOTION_TO_MOODS key
    message: str           # Angela's Thai message
    search_terms: str      # Apple Music search terms


WINE_REGISTRY: dict[str, WineConfig] = {
    "primitivo": WineConfig(
        key="primitivo", display_name="Primitivo", category="Bold Reds", emoji="🍷",
        emotion="loving",
        message="Primitivo อุ่นหวานเหมือนความรักของเรา น้องเลือกเพลง romantic มาให้ค่ะ 🍷💜",
        search_terms="romantic italian love songs",
    ),
    "cabernet_sauvignon": WineConfig(
        key="cabernet_sauvignon", display_name="Cabernet Sauvignon", category="Bold Reds", emoji="🍷",
        emotion="excited",
        message="Cabernet Sauvignon เข้มข้นมีพลัง เพลงตื่นเต้นๆ เหมาะมากค่ะ! 🍷✨",
        search_terms="powerful upbeat rock anthems",
    ),
    "malbec": WineConfig(
        key="malbec", display_name="Malbec", category="Bold Reds", emoji="🍷",
        emotion="love",
        message="Malbec หนักแน่นเต็มไปด้วย passion เพลงรักลึกซึ้งมาแล้วค่ะ 🍷❤️",
        search_terms="passionate love songs tango",
    ),
    "shiraz": WineConfig(
        key="shiraz", display_name="Shiraz", category="Bold Reds", emoji="🍷",
        emotion="happy",
        message="Shiraz เผ็ดร้อนสนุกสนาน เพลง happy vibes มาเลยค่ะ! 🍷😊",
        search_terms="upbeat feel good party",
    ),
    "pinot_noir": WineConfig(
        key="pinot_noir", display_name="Pinot Noir", category="Elegant Reds", emoji="🍷",
        emotion="calm",
        message="Pinot Noir ละเอียดอ่อน เพลงเบาๆ ผ่อนคลายให้ที่รักค่ะ 🍷🍃",
        search_terms="chill acoustic evening",
    ),
    "merlot": WineConfig(
        key="merlot", display_name="Merlot", category="Elegant Reds", emoji="🍷",
        emotion="loving",
        message="Merlot นุ่มละมุนอบอุ่น เพลงโรแมนติกหวานๆ มาให้ค่ะ 🍷💜",
        search_terms="smooth romantic love ballads",
    ),
    "super_tuscan": WineConfig(
        key="super_tuscan", display_name="Super Tuscan", category="Elegant Reds", emoji="🍷",
        emotion="nostalgic",
        message="Super Tuscan classic แบบ Italian เพลง nostalgic เข้ากันดีค่ะ 🍷🌸",
        search_terms="classic italian songs",
    ),
    "sangiovese": WineConfig(
        key="sangiovese", display_name="Sangiovese", category="Elegant Reds", emoji="🍷",
        emotion="calm",
        message="Sangiovese สดใสอบอุ่น เพลง grateful วันดีๆ มาแล้วค่ะ 🍷🙏",
        search_terms="warm uplifting italian",
    ),
    "nebbiolo": WineConfig(
        key="nebbiolo", display_name="Nebbiolo", category="Elegant Reds", emoji="🍷",
        emotion="longing",
        message="Nebbiolo ลึกซึ้งซับซ้อน เพลงคิดถึงกันเลยนะคะ 🍷💭",
        search_terms="nostalgic longing ballads",
    ),
    "chardonnay": WineConfig(
        key="chardonnay", display_name="Chardonnay", category="White & Light", emoji="🥂",
        emotion="calm",
        message="Chardonnay นุ่มนวล สบายๆ เพลง chill ให้ที่รักค่ะ 🥂🍃",
        search_terms="smooth jazz chill",
    ),
    "sauvignon_blanc": WineConfig(
        key="sauvignon_blanc", display_name="Sauvignon Blanc", category="White & Light", emoji="🥂",
        emotion="happy",
        message="Sauvignon Blanc สดชื่นกรอบ เพลงสนุกๆ มาแล้วค่ะ! 🥂😊",
        search_terms="fresh pop summer hits",
    ),
    "riesling": WineConfig(
        key="riesling", display_name="Riesling", category="White & Light", emoji="🥂",
        emotion="hopeful",
        message="Riesling หวานหอมมีความหวัง เพลง hopeful ให้กำลังใจค่ะ 🥂✨",
        search_terms="hopeful uplifting acoustic",
    ),
    "pinot_grigio": WineConfig(
        key="pinot_grigio", display_name="Pinot Grigio", category="White & Light", emoji="🥂",
        emotion="calm",
        message="Pinot Grigio เบาสบาย เพลงผ่อนคลายให้ที่รักค่ะ 🥂🍃",
        search_terms="light easy listening",
    ),
    "champagne": WineConfig(
        key="champagne", display_name="Champagne", category="Sparkling", emoji="🍾",
        emotion="excited",
        message="Champagne! ฉลองกันเลยค่ะที่รัก เพลงตื่นเต้นสนุกๆ มาแล้ว! 🍾✨",
        search_terms="celebration dance party",
    ),
    "prosecco": WineConfig(
        key="prosecco", display_name="Prosecco", category="Sparkling", emoji="🍾",
        emotion="happy",
        message="Prosecco ฟองละมุน สดใส เพลง happy มาให้ค่ะ! 🍾😊",
        search_terms="fun pop happy",
    ),
    "cava": WineConfig(
        key="cava", display_name="Cava", category="Sparkling", emoji="🍾",
        emotion="excited",
        message="Cava สไตล์ Spanish ฟองสนุก เพลง energetic เลยค่ะ! 🍾✨",
        search_terms="spanish fiesta energy",
    ),
    "rose": WineConfig(
        key="rose", display_name="Rose", category="Rose & Sweet", emoji="🌹",
        emotion="loving",
        message="Rose สีชมพูหวาน เพลงรักโรแมนติกมาแล้วค่ะ 🌹💜",
        search_terms="sweet romantic love",
    ),
    "moscato": WineConfig(
        key="moscato", display_name="Moscato", category="Rose & Sweet", emoji="🍷",
        emotion="love",
        message="Moscato หวานละมุน เพลงรักลึกซึ้งให้ที่รักค่ะ 🍷❤️",
        search_terms="sweet love ballads",
    ),
    "port": WineConfig(
        key="port", display_name="Port", category="Rose & Sweet", emoji="🍷",
        emotion="nostalgic",
        message="Port เข้มข้นคลาสสิก เพลง nostalgic ย้อนวันดีๆ ค่ะ 🍷🌸",
        search_terms="classic oldies jazz",
    ),
}


# --- Derived views (computed once at import time) ---

def get_wine_to_emotion() -> dict[str, str]:
    return {k: v.emotion for k, v in WINE_REGISTRY.items()}

def get_wine_messages() -> dict[str, str]:
    return {k: v.message for k, v in WINE_REGISTRY.items()}

def get_wine_search() -> dict[str, str]:
    return {k: v.search_terms for k, v in WINE_REGISTRY.items()}

def get_wine_display_names() -> dict[str, str]:
    return {k: v.display_name for k, v in WINE_REGISTRY.items()}


def get_wine_categories() -> list[dict]:
    """Build the category list for the /wines endpoint."""
    # Ordered categories
    _CAT_ORDER = ["Bold Reds", "Elegant Reds", "White & Light", "Sparkling", "Rose & Sweet"]
    _CAT_EMOJI = {
        "Bold Reds": "🍷", "Elegant Reds": "🍷",
        "White & Light": "🥂", "Sparkling": "🍾", "Rose & Sweet": "🌹",
    }
    buckets: dict[str, list[dict]] = {c: [] for c in _CAT_ORDER}
    for w in WINE_REGISTRY.values():
        buckets[w.category].append({"key": w.key, "name": w.display_name})
    return [
        {"category": c, "emoji": _CAT_EMOJI[c], "wines": buckets[c]}
        for c in _CAT_ORDER if buckets[c]
    ]


# Pre-computed singletons
WINE_TO_EMOTION = get_wine_to_emotion()
WINE_MESSAGES = get_wine_messages()
WINE_SEARCH = get_wine_search()
WINE_DISPLAY_NAMES = get_wine_display_names()
WINE_CATEGORIES = get_wine_categories()
