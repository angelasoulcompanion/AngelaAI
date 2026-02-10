"""Single source of truth for Famous Club configurations.

Club vibes use Apple Music search + LLM curation (same pipeline as Activity Moods).
Angela curates playlists matching the vibe of famous clubs worldwide.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ClubConfig:
    """Configuration for a famous club vibe."""
    key: str                    # "onyx", "cafe_del_mar", etc.
    name: str                   # "ONYX"
    city: str                   # "Bangkok"
    country: str                # "Thailand"
    country_flag: str           # "🇹🇭"
    category: str               # "high_energy", "house", "chill", "jazz"
    genre: str                  # "EDM, Big Room"
    energy: int                 # 1-10
    search_terms: list[str]     # iTunes search terms (3-5)
    llm_description: str        # Thai description for LLM curation
    vibe_description: str       # English vibe description for UI
    emoji: str                  # Club-specific icon
    summary_th: str             # Thai summary for reason text
    signature_albums: list[str] | None = None  # iTunes album search terms for compilation clubs


CLUB_REGISTRY: dict[str, ClubConfig] = {
    # --- 🔥 High Energy (EDM/Techno) ---
    "onyx": ClubConfig(
        key="onyx",
        name="ONYX",
        city="Bangkok",
        country="Thailand",
        country_flag="🇹🇭",
        category="high_energy",
        genre="EDM, Big Room",
        energy=9,
        search_terms=["EDM big room house", "festival anthems", "main stage EDM drops"],
        llm_description="เพลง EDM big room, festival anthems แบบ ONYX Bangkok — drop หนัก เสียงดัง ตึ้ดตึ้ด ห้ามเพลงช้า",
        vibe_description="Bangkok's EDM powerhouse. Big room drops and festival energy.",
        emoji="🔊",
        summary_th="น้องจัดเพลง EDM แบบ ONYX Bangkok ให้ค่ะ 🔊 ตึ้ดตึ้ดค่ะ!",
        signature_albums=["Ultra Music Festival", "Big Room EDM Festival"],
    ),

    # --- 🏠 House & Deep House ---
    "ministry_of_sound": ClubConfig(
        key="ministry_of_sound",
        name="Ministry of Sound",
        city="London",
        country="UK",
        country_flag="🇬🇧",
        category="house",
        genre="House, Garage",
        energy=8,
        search_terms=["UK garage house", "Ministry of Sound", "house music classic"],
        llm_description="เพลง house, UK garage แบบ Ministry of Sound — classic house beats จังหวะสนุก groovy",
        vibe_description="The ministry of dance. Classic house and UK garage in the box.",
        emoji="📦",
        summary_th="น้องจัดเพลง house แบบ Ministry of Sound ให้ค่ะ 📦",
        signature_albums=["Ministry of Sound Annual", "Ministry of Sound Anthems"],
    ),

    # --- 🌅 Chill & Lounge ---
    "cafe_del_mar": ClubConfig(
        key="cafe_del_mar",
        name="Cafe del Mar",
        city="Ibiza",
        country="Spain",
        country_flag="🇪🇸",
        category="chill",
        genre="Balearic Chill, Ambient",
        energy=3,
        search_terms=["Cafe del Mar compilation", "Balearic chill sunset", "ambient downtempo Ibiza"],
        llm_description="เพลง Balearic chill, ambient, downtempo แบบ Cafe del Mar — ฟังพระอาทิตย์ตก สงบ ผ่อนคลาย dreamy",
        vibe_description="Sunset institution. Balearic chill and ambient as the sun goes down.",
        emoji="🌅",
        summary_th="น้องจัดเพลง chill แบบ Cafe del Mar ให้ค่ะ 🌅 sunset vibes",
        signature_albums=["Cafe del Mar", "Café del Mar Ibiza"],
    ),
    "sky_bar_lebua": ClubConfig(
        key="sky_bar_lebua",
        name="Sky Bar Lebua",
        city="Bangkok",
        country="Thailand",
        country_flag="🇹🇭",
        category="chill",
        genre="Lounge, Chill House",
        energy=2,
        search_terms=["rooftop lounge music", "luxury ambient cocktail", "chill house lounge bar"],
        llm_description="เพลง lounge, chill house แบบ Sky Bar Lebua — หรูหรา สบาย cocktail bar rooftop เบาสบาย",
        vibe_description="Bangkok's rooftop jewel. Luxury lounge vibes above the skyline.",
        emoji="🏙️",
        summary_th="น้องจัดเพลง lounge แบบ Sky Bar Lebua ให้ค่ะ 🏙️ หรูหราสบาย",
        signature_albums=["Rooftop Lounge", "Buddha Bar"],
    ),
    "hotel_costes": ClubConfig(
        key="hotel_costes",
        name="Hotel Costes",
        city="Paris",
        country="France",
        country_flag="🇫🇷",
        category="chill",
        genre="French Lounge, Nu-Jazz, Deep House",
        energy=4,
        search_terms=["Hotel Costes compilation", "French lounge deep house", "nu jazz downtempo Paris", "Stephane Pompougnac"],
        llm_description="เพลง French lounge, nu-jazz, deep house แบบ Hotel Costes Paris — หรูหรา elegant เซ็กซี่ Parisian chic ฟังสบายแต่มี groove",
        vibe_description="Parisian luxury. French lounge, nu-jazz and deep house with effortless chic.",
        emoji="🕯️",
        summary_th="น้องจัดเพลง French lounge แบบ Hotel Costes Paris ให้ค่ะ 🕯️ elegant & chic",
        signature_albums=["Hotel Costes", "Hôtel Costes"],
    ),

    # --- 🇭🇰 Hong Kong ---
    "ozone": ClubConfig(
        key="ozone",
        name="Ozone",
        city="Hong Kong",
        country="Hong Kong",
        country_flag="🇭🇰",
        category="chill",
        genre="Electronic Lounge, Deep House",
        energy=3,
        search_terms=["rooftop lounge electronic", "luxury deep house ambient", "skyline chill lounge"],
        llm_description="เพลง electronic lounge, deep house แบบ Ozone Ritz-Carlton — bar สูงที่สุดในโลก ชั้น 118 หรูหรา วิวสวย ฟังสบาย",
        vibe_description="World's highest bar. Electronic lounge 118 floors above Hong Kong.",
        emoji="🌃",
        summary_th="น้องจัดเพลง lounge แบบ Ozone HK ให้ค่ะ 🌃 bar สูงที่สุดในโลก!",
        signature_albums=["Hong Kong sunset lounge", "Hong Kong lounge"],
    ),
    "dragon_i": ClubConfig(
        key="dragon_i",
        name="Dragon-i",
        city="Hong Kong",
        country="Hong Kong",
        country_flag="🇭🇰",
        category="house",
        genre="Commercial House, Funky House",
        energy=7,
        search_terms=["funky house club", "commercial house party", "VIP club house music"],
        llm_description="เพลง commercial house, funky house แบบ Dragon-i Lan Kwai Fong — VIP club ดังที่สุดของ Hong Kong ไม่ดาร์กไม่ underground สนุก groovy",
        vibe_description="Hong Kong's legendary VIP club. Funky house and commercial beats in Lan Kwai Fong.",
        emoji="🐉",
        summary_th="น้องจัดเพลง house แบบ Dragon-i HK ให้ค่ะ 🐉 VIP club ดังที่สุด!",
        signature_albums=["Toolroom Records", "Glitterbox"],
    ),
    "felix": ClubConfig(
        key="felix",
        name="Felix",
        city="Hong Kong",
        country="Hong Kong",
        country_flag="🇭🇰",
        category="jazz",
        genre="Cocktail Jazz, Piano Lounge",
        energy=2,
        search_terms=["cocktail piano jazz", "sophisticated lounge jazz", "piano bar evening"],
        llm_description="เพลง cocktail jazz, piano lounge แบบ Felix at The Peninsula — Philippe Starck design หรูหรา elegant smooth jazz ค็อกเทล",
        vibe_description="Philippe Starck's masterpiece at The Peninsula. Sophisticated cocktail jazz above Victoria Harbour.",
        emoji="🍸",
        summary_th="น้องจัดเพลง cocktail jazz แบบ Felix HK ให้ค่ะ 🍸 elegant & sophisticated",
        signature_albums=["Cocktail Piano Bar Jazz", "Jazz Cocktail Bars"],
    ),

    # --- 🎷 Jazz & Soul ---
    "blue_note": ClubConfig(
        key="blue_note",
        name="Blue Note",
        city="NYC / Tokyo",
        country="USA / Japan",
        country_flag="🇺🇸",
        category="jazz",
        genre="Jazz, Neo-Soul",
        energy=6,
        search_terms=["Blue Note jazz", "neo soul jazz fusion", "smooth jazz live"],
        llm_description="เพลง jazz, neo-soul แบบ Blue Note — live jazz สด smooth ฟังสบาย มี soul มี groove",
        vibe_description="Legendary jazz temple. Where jazz legends play and new stars are born.",
        emoji="🎺",
        summary_th="น้องจัดเพลง jazz แบบ Blue Note ให้ค่ะ 🎺 smooth & soulful",
        signature_albums=["Blue Note Trip", "Jazz Bar Lounge"],
    ),
}


# --- Derived views (computed once at import time) ---

CLUB_KEYS: set[str] = set(CLUB_REGISTRY.keys())

CLUB_SEARCH_TERMS: dict[str, list[str]] = {
    k: list(v.search_terms) for k, v in CLUB_REGISTRY.items()
}

CLUB_LLM_DESCRIPTIONS: dict[str, str] = {
    k: v.llm_description for k, v in CLUB_REGISTRY.items()
}

CLUB_SUMMARIES_TH: dict[str, str] = {
    k: v.summary_th for k, v in CLUB_REGISTRY.items()
}

CLUB_CATEGORIES: list[str] = [
    "high_energy", "house", "chill", "jazz",
]

CLUB_CATEGORY_LABELS: dict[str, str] = {
    "high_energy": "🔥 High Energy",
    "house": "🏠 House",
    "chill": "🌅 Chill",
    "jazz": "🎷 Jazz",
}

CLUB_SIGNATURE_ALBUMS: dict[str, list[str]] = {
    k: v.signature_albums for k, v in CLUB_REGISTRY.items() if v.signature_albums
}
