//
//  DJAngelaConstants.swift
//  Angela Brain Dashboard
//
//  Single source of truth for DJ Angela data dictionaries.
//  Moved from SongQueueView to reduce file size and enable reuse.
//

import Foundation

enum DJAngelaConstants {

    // MARK: - Mood Data

    static let moodEmojis: [String: String] = [
        "happy": "😊", "loving": "💜", "calm": "🍃", "excited": "✨",
        "bedtime": "😴", "sad": "😢", "lonely": "🌙", "stressed": "😮‍💨",
        "nostalgic": "🌸", "hopeful": "🌅",
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
        "stressed": "calm relaxing piano ambient",
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
        let keywords = playlistMoodKeywords[mood] ?? []
        return keywords.contains { lower.contains($0) }
    }
}
