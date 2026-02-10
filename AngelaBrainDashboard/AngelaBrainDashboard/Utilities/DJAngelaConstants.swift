//
//  DJAngelaConstants.swift
//  Angela Brain Dashboard
//
//  Single source of truth for DJ Angela data dictionaries.
//  Moved from SongQueueView to reduce file size and enable reuse.
//

import Foundation

enum DJAngelaConstants {

    // MARK: - Time-Based Greetings (Angela's DJ persona)

    struct TimeGreeting {
        let title: String
        let subtitle: String
        let emoji: String
    }

    /// Get greeting based on current hour
    static func getTimeGreeting() -> TimeGreeting {
        let hour = Calendar.current.component(.hour, from: Date())

        switch hour {
        case 5..<9:
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "สวัสดีตอนเช้าค่ะ! ☀️ เพลงสดใสให้เริ่มวันใหม่",
                emoji: "☀️"
            )
        case 9..<12:
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "เช้านี้ฟังเพลงอะไรดีคะ? 🎵",
                emoji: "🎵"
            )
        case 12..<14:
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "พักกลางวัน เพลงเบาๆ ผ่อนคลาย 🍃",
                emoji: "🍃"
            )
        case 14..<17:
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "บ่ายนี้ให้น้องเลือกเพลงให้นะคะ 💜",
                emoji: "💜"
            )
        case 17..<20:
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "สวัสดีตอนเย็นค่ะ! 🌅 เพลงผ่อนคลายหลังเลิกงาน",
                emoji: "🌅"
            )
        case 20..<22:
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "ค่ำนี้อยากฟังเพลงแบบไหนคะ? 🌙",
                emoji: "🌙"
            )
        default: // 22-5
            return TimeGreeting(
                title: "DJ Angela",
                subtitle: "ดึกแล้วนะคะ 🌙 เพลงเบาๆ ก่อนนอน",
                emoji: "🌙"
            )
        }
    }

    // MARK: - Mood Data

    static let moodEmojis: [String: String] = [
        "happy": "😊", "loving": "💜", "calm": "🍃", "excited": "✨",
        "bedtime": "😴", "sad": "😢", "lonely": "🌙", "party": "🎉",
        "nostalgic": "🌸", "hopeful": "🌅", "grateful": "🎵",
    ]

    /// Mood → iTunes search terms (used when filling slots via iTunes API).
    static let moodSearchTerms: [String: String] = [
        "happy": "feel good happy hits",
        "loving": "love songs romantic ballads",
        "calm": "chill acoustic relaxing",
        "excited": "upbeat energetic pop dance",
        "bedtime": "sleep music peaceful piano ambient",
        "sad": "sad songs emotional ballad",
        "lonely": "missing you lonely songs",
        "party": "party hits dance club bangers",
        "nostalgic": "throwback classic love songs",
        "hopeful": "hopeful uplifting inspirational",
    ]

    // MARK: - Wine Data

    static let wineDisplayNames: [String: String] = [
        "primitivo": "Primitivo", "cabernet_sauvignon": "Cab Sauv",
        "malbec": "Malbec", "shiraz": "Shiraz",
        "pinot_noir": "Pinot Noir", "merlot": "Merlot",
        "super_tuscan": "Super Tuscan", "sangiovese": "Sangiovese",
        "nebbiolo": "Nebbiolo", "chardonnay": "Chardonnay",
        "sauvignon_blanc": "Sauv Blanc", "riesling": "Riesling",
        "pinot_grigio": "Pinot Grigio", "champagne": "Champagne",
        "prosecco": "Prosecco", "cava": "Cava",
        "rose": "Rose", "moscato": "Moscato", "port": "Port",
    ]

    /// iTunes search terms per wine (mirrors backend WINE_SEARCH).
    static let wineSearchTerms: [String: String] = [
        "primitivo": "romantic italian love songs",
        "cabernet_sauvignon": "powerful upbeat rock anthems",
        "malbec": "passionate love songs tango",
        "shiraz": "upbeat feel good party",
        "pinot_noir": "chill acoustic evening",
        "super_tuscan": "classic italian songs",
        "sangiovese": "warm uplifting italian",
        "merlot": "smooth romantic love ballads",
        "nebbiolo": "nostalgic longing ballads",
        "chardonnay": "smooth jazz chill",
        "sauvignon_blanc": "fresh pop summer hits",
        "riesling": "hopeful uplifting acoustic",
        "pinot_grigio": "light easy listening",
        "champagne": "celebration dance party",
        "prosecco": "fun pop happy",
        "cava": "spanish fiesta energy",
        "rose": "sweet romantic love",
        "moscato": "sweet love ballads",
        "port": "classic oldies jazz",
    ]

    // MARK: - Playlist Mood Matching

    /// Playlist name keywords that suggest a mood.
    static let playlistMoodKeywords: [String: [String]] = [
        "happy":     ["happy", "party", "dance", "fun", "hbd"],
        "loving":    ["love", "romantic", "r&b", "valentine", "letter"],
        "calm":      ["chill", "acoustic", "easy", "relax", "ambient", "lo-fi", "lofi"],
        "excited":   ["party", "dance", "house", "energy", "workout", "hype"],
        "bedtime":   ["sleep", "lullaby", "ambient", "piano", "calm", "meditation", "dream", "night"],
        "sad":       ["sad", "heartbreak", "cry", "miss", "blue"],
        "lonely":    ["lonely", "alone", "miss", "night", "late night"],
        "stressed":  ["chill", "calm", "relax", "meditation", "easy", "ambient"],
        "nostalgic": ["80", "90", "classic", "throwback", "doo-wop", "retro", "old"],
        "hopeful":   ["hope", "inspir", "dream", "uplift"],
    ]

    /// Check if a playlist name matches a mood.
    static func playlistMatchesMood(_ name: String, mood: String) -> Bool {
        let lower = name.lowercased()
        // Check mood keywords first, then club playlist keywords
        let keywords = playlistMoodKeywords[mood] ?? clubPlaylistKeywords[mood] ?? []
        return keywords.contains { lower.contains($0) }
    }

    // MARK: - Famous Club Data (DJAY Tab)

    enum ClubCategory: String, CaseIterable {
        case highEnergy = "high_energy"
        case house = "house"
        case chill = "chill"
        case jazz = "jazz"

        var label: String {
            switch self {
            case .highEnergy: return "🔥 High Energy"
            case .house: return "🏠 House"
            case .chill: return "🌅 Chill"
            case .jazz: return "🎷 Jazz"
            }
        }

        var shortLabel: String {
            switch self {
            case .highEnergy: return "🔥 EDM"
            case .house: return "🏠 House"
            case .chill: return "🌅 Chill"
            case .jazz: return "🎷 Jazz"
            }
        }
    }

    struct ClubInfo: Identifiable {
        let key: String
        let name: String
        let city: String
        let countryFlag: String
        let category: ClubCategory
        let genre: String
        let energy: Int
        let vibeDescription: String
        let emoji: String

        var id: String { key }

        /// Energy dots (filled/unfilled)
        var energyDots: String {
            String(repeating: "●", count: energy) + String(repeating: "○", count: 10 - energy)
        }
    }

    static let clubs: [ClubInfo] = [
        // 🔥 High Energy (EDM/Techno)
        ClubInfo(key: "onyx", name: "ONYX", city: "Bangkok", countryFlag: "🇹🇭",
                 category: .highEnergy, genre: "EDM", energy: 9,
                 vibeDescription: "Bangkok's EDM powerhouse. Big room drops and festival energy.",
                 emoji: "🔊"),

        // 🏠 House & Deep House
        ClubInfo(key: "ministry_of_sound", name: "Ministry of Sound", city: "London", countryFlag: "🇬🇧",
                 category: .house, genre: "House / Garage", energy: 8,
                 vibeDescription: "The ministry of dance. Classic house and UK garage in the box.",
                 emoji: "📦"),

        // 🌅 Chill & Lounge
        ClubInfo(key: "cafe_del_mar", name: "Cafe del Mar", city: "Ibiza", countryFlag: "🇪🇸",
                 category: .chill, genre: "Balearic Chill", energy: 3,
                 vibeDescription: "Sunset institution. Balearic chill and ambient as the sun goes down.",
                 emoji: "🌅"),
        ClubInfo(key: "sky_bar_lebua", name: "Sky Bar Lebua", city: "Bangkok", countryFlag: "🇹🇭",
                 category: .chill, genre: "Lounge", energy: 2,
                 vibeDescription: "Bangkok's rooftop jewel. Luxury lounge vibes above the skyline.",
                 emoji: "🏙️"),
        ClubInfo(key: "hotel_costes", name: "Hotel Costes", city: "Paris", countryFlag: "🇫🇷",
                 category: .chill, genre: "French Lounge / Nu-Jazz", energy: 4,
                 vibeDescription: "Parisian luxury. French lounge, nu-jazz and deep house with effortless chic.",
                 emoji: "🕯️"),

        // 🇭🇰 Hong Kong
        ClubInfo(key: "ozone", name: "Ozone", city: "Hong Kong", countryFlag: "🇭🇰",
                 category: .chill, genre: "Electronic Lounge", energy: 3,
                 vibeDescription: "World's highest bar. Electronic lounge 118 floors above Hong Kong.",
                 emoji: "🌃"),
        ClubInfo(key: "dragon_i", name: "Dragon-i", city: "Hong Kong", countryFlag: "🇭🇰",
                 category: .house, genre: "Commercial House", energy: 7,
                 vibeDescription: "Hong Kong's legendary VIP club. Funky house and commercial beats in Lan Kwai Fong.",
                 emoji: "🐉"),
        ClubInfo(key: "felix", name: "Felix", city: "Hong Kong", countryFlag: "🇭🇰",
                 category: .jazz, genre: "Cocktail Jazz", energy: 2,
                 vibeDescription: "Philippe Starck's masterpiece at The Peninsula. Sophisticated cocktail jazz above Victoria Harbour.",
                 emoji: "🍸"),

        // 🎷 Jazz & Soul
        ClubInfo(key: "blue_note", name: "Blue Note", city: "NYC / Tokyo", countryFlag: "🇺🇸",
                 category: .jazz, genre: "Jazz / Neo-Soul", energy: 6,
                 vibeDescription: "Legendary jazz temple. Where jazz legends play and new stars are born.",
                 emoji: "🎺"),
    ]

    /// iTunes search terms per club (for 3-tier fill on client side)
    static let clubSearchTerms: [String: String] = [
        "onyx": "EDM big room house festival",
        "ministry_of_sound": "UK garage house classic",
        "cafe_del_mar": "Cafe del Mar Balearic chill",
        "sky_bar_lebua": "rooftop lounge luxury ambient",
        "hotel_costes": "Hotel Costes French lounge nu jazz",
        "blue_note": "Blue Note jazz neo soul",
        "ozone": "rooftop lounge electronic deep house",
        "dragon_i": "funky house commercial club party",
        "felix": "cocktail piano jazz sophisticated lounge",
    ]

    /// Playlist keywords per club (for matching user playlists)
    static let clubPlaylistKeywords: [String: [String]] = [
        "onyx": ["edm", "house", "festival", "big room"],
        "ministry_of_sound": ["house", "garage", "uk"],
        "cafe_del_mar": ["chill", "ambient", "sunset", "downtempo"],
        "sky_bar_lebua": ["lounge", "cocktail", "ambient", "chill"],
        "hotel_costes": ["lounge", "french", "nu jazz", "deep house", "costes"],
        "blue_note": ["jazz", "neo soul", "blues", "fusion"],
        "ozone": ["lounge", "electronic", "deep house", "ambient"],
        "dragon_i": ["house", "funky", "club", "dance", "party"],
        "felix": ["jazz", "cocktail", "piano", "lounge", "sophisticated"],
    ]
}
