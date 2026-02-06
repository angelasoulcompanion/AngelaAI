//
//  MusicModels.swift
//  Angela Brain Dashboard
//
//  Models for DJ Angela music feature
//
//  NOTE: Decoded models (Song, SongRecommendation, MusicShareResponse) must NOT
//  have CodingKeys with snake_case raw values — NetworkService.decoder uses
//  .convertFromSnakeCase which conflicts (double conversion).
//  MusicShareRequest is ENCODED with a plain JSONEncoder, so it keeps CodingKeys.
//

import Foundation

// MARK: - Song (decoded via .convertFromSnakeCase)

struct Song: Identifiable, Codable {
    let songId: String
    let title: String
    let artist: String?
    let whySpecial: String?
    let isOurSong: Bool
    let moodTags: [String]
    let source: String?
    let addedAt: String?
    let lyricsSummary: String?
    let angelaFeeling: String?
    let angelaMeaning: String?
    let feelingIntensity: Int?
    let energyPhase: String?    // "warmup", "peak", "cooldown"

    var id: String { songId }
}

// MARK: - Song Recommendation

struct SongRecommendation: Codable {
    let song: Song?
    let songs: [Song]?
    let reason: String
    let basedOnEmotion: String
    let availableMoods: [String]?
    let appleMusicDiscoverUrl: String?
    let moodSummary: String?
    let emotionDetails: [String]?
    let ourSongsMatched: Int?
    let wineMessage: String?
    // Wine-music pairing algorithm fields
    let wineProfile: WineProfileData?
    let targetProfile: TargetProfileData?
    let searchQueries: [String]?
    // Mood analysis (7-signal algorithm)
    let moodAnalysis: MoodAnalysis?
}

// MARK: - Wine Profile (sensory dimensions)

struct WineProfileData: Codable {
    let body: Double
    let tannins: Double
    let acidity: Double
    let sweetness: Double
    let aromaIntensity: Double
}

// MARK: - Music Target Profile (computed from wine + mood)

struct TargetProfileData: Codable {
    let tempoRange: [Int]?
    let energy: Double?
    let valence: Double?
    let acousticPref: Double?
    let keyPref: String?
    let topGenres: [[GenreScore]]?
    let searchQueries: [String]?
}

/// Genre score tuple decoded from [[name, score]] JSON array
enum GenreScore: Codable {
    case string(String)
    case double(Double)

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let s = try? container.decode(String.self) {
            self = .string(s)
        } else if let d = try? container.decode(Double.self) {
            self = .double(d)
        } else {
            self = .string("")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let s): try container.encode(s)
        case .double(let d): try container.encode(d)
        }
    }
}

// MARK: - Music Share Request (encoded — needs CodingKeys for snake_case output)

struct MusicShareRequest: Codable {
    let songId: String
    let message: String?

    enum CodingKeys: String, CodingKey {
        case songId = "song_id"
        case message
    }
}

// MARK: - Music Share Response

struct MusicShareResponse: Codable {
    let song: Song
    let angelaMessage: String
}

// MARK: - Playlist Prompt Request (encoded — needs CodingKeys for snake_case output)

struct PlaylistPromptRequest: Codable {
    let emotionText: String?
    let songCount: Int

    enum CodingKeys: String, CodingKey {
        case emotionText = "emotion_text"
        case songCount = "song_count"
    }
}

// MARK: - Playlist Prompt Response (decoded via .convertFromSnakeCase — NO CodingKeys)

struct PlaylistPromptResponse: Codable {
    let dominantMood: String
    let moodSummary: String
    let searchQueries: [String]
    let genreHints: [String]?
    let playlistName: String
    let playlistDescription: String
    let emotionDetails: [String]?
    let ourSongsToInclude: [PlaylistSeedSong]?
}

struct PlaylistSeedSong: Codable {
    let title: String
    let artist: String
}

// MARK: - Song Like Request/Response

struct SongLikeRequest: Codable {
    let title: String
    let artist: String
    let liked: Bool
    let album: String?
    let appleMusicId: String?
    let artworkUrl: String?
    let sourceTab: String?

    enum CodingKeys: String, CodingKey {
        case title, artist, liked, album
        case appleMusicId = "apple_music_id"
        case artworkUrl = "artwork_url"
        case sourceTab = "source_tab"
    }

    init(title: String, artist: String, liked: Bool = true, album: String? = nil, appleMusicId: String? = nil, artworkUrl: String? = nil, sourceTab: String? = nil) {
        self.title = title
        self.artist = artist
        self.liked = liked
        self.album = album
        self.appleMusicId = appleMusicId
        self.artworkUrl = artworkUrl
        self.sourceTab = sourceTab
    }
}

struct SongLikeResponse: Codable {
    let action: String      // "liked", "unliked", "not_found"
    let songId: String?
    let title: String
    let artist: String
    let created: Bool?
}

// MARK: - Liked Songs List

struct LikedSong: Codable, Identifiable {
    let likeId: String
    let title: String
    let artist: String?
    let album: String?
    let appleMusicId: String?
    let artworkUrl: String?
    let likedAt: String?
    let sourceTab: String?

    var id: String { likeId }

    /// Key for matching (lowercase title|artist)
    var matchKey: String {
        "\(title.lowercased())|\((artist ?? "").lowercased())"
    }
}

struct LikedSongsResponse: Codable {
    let songs: [LikedSong]
    let count: Int
}

// MARK: - Playlist Generation State

enum PlaylistGenerationState: Equatable {
    case idle
    case analyzing
    case ready
    case error(String)
}

// MARK: - DisplaySong (unified model for Apple Music + Angela songs)

import MusicKit

struct DisplaySong: Identifiable {
    let id: String
    let title: String
    let artist: String
    let album: String?
    let albumArtURL: URL?
    let duration: TimeInterval?
    let musicKitSong: MusicKit.Song?
    let angelaSong: Song?
    let isOurSong: Bool
    let moodTags: [String]
    let angelaFeeling: String?
    let energyPhase: String?    // "warmup", "peak", "cooldown"

    /// Init from MusicKit.Song (Library, Playlists, Search results)
    init(from mkSong: MusicKit.Song, energyPhase: String? = nil) {
        self.id = mkSong.id.rawValue
        self.title = mkSong.title
        self.artist = mkSong.artistName
        self.album = mkSong.albumTitle
        self.albumArtURL = mkSong.artwork?.url(width: 300, height: 300)
        self.duration = mkSong.duration
        self.musicKitSong = mkSong
        self.angelaSong = nil
        self.isOurSong = false
        self.moodTags = []
        self.angelaFeeling = nil
        self.energyPhase = energyPhase
    }

    /// Init from Angela Song (Our Songs tab)
    init(from angelaSong: Song, energyPhase: String? = nil) {
        self.id = angelaSong.songId
        self.title = angelaSong.title
        self.artist = angelaSong.artist ?? "Unknown Artist"
        self.album = nil
        self.albumArtURL = nil  // resolved later via Apple Music search
        self.duration = nil
        self.musicKitSong = nil
        self.angelaSong = angelaSong
        self.isOurSong = angelaSong.isOurSong
        self.moodTags = angelaSong.moodTags
        self.angelaFeeling = angelaSong.angelaFeeling
        // Use provided energyPhase or fallback to Song's energyPhase
        self.energyPhase = energyPhase ?? angelaSong.energyPhase
    }

    /// Init from Angela Song enriched with MusicKit artwork
    init(from angelaSong: Song, artwork: URL?, energyPhase: String? = nil) {
        self.id = angelaSong.songId
        self.title = angelaSong.title
        self.artist = angelaSong.artist ?? "Unknown Artist"
        self.album = nil
        self.albumArtURL = artwork
        self.duration = nil
        self.musicKitSong = nil
        self.angelaSong = angelaSong
        self.isOurSong = angelaSong.isOurSong
        self.moodTags = angelaSong.moodTags
        self.angelaFeeling = angelaSong.angelaFeeling
        // Use provided energyPhase or fallback to Song's energyPhase
        self.energyPhase = energyPhase ?? angelaSong.energyPhase
    }

    /// Init from iTunes Search API result (no MusicKit, no Angela Song)
    init(title: String, artist: String, album: String? = nil, artworkURL: URL? = nil, duration: TimeInterval? = nil, energyPhase: String? = nil) {
        self.id = UUID().uuidString
        self.title = title
        self.artist = artist
        self.album = album
        self.albumArtURL = artworkURL
        self.duration = duration
        self.musicKitSong = nil
        self.angelaSong = nil
        self.isOurSong = false
        self.moodTags = []
        self.angelaFeeling = nil
        self.energyPhase = energyPhase
    }

    /// Init from LikedSong (Liked tab)
    init(from liked: LikedSong) {
        self.id = liked.likeId
        self.title = liked.title
        self.artist = liked.artist ?? "Unknown Artist"
        self.album = liked.album
        self.albumArtURL = liked.artworkUrl.flatMap { URL(string: $0) }
        self.duration = nil
        self.musicKitSong = nil
        self.angelaSong = nil
        self.isOurSong = false
        self.moodTags = []
        self.angelaFeeling = nil
        self.energyPhase = nil
    }

    var durationFormatted: String? {
        guard let d = duration, d > 0 else { return nil }
        let minutes = Int(d) / 60
        let seconds = Int(d) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - Play Log Request (encoded — needs CodingKeys for snake_case output)

struct PlayLogBody: Codable {
    let title: String
    let artist: String?
    let album: String?
    let appleMusicId: String?
    let sourceTab: String?
    let durationSeconds: Double?
    let listenedSeconds: Double?
    let playStatus: String
    let activity: String?
    let wineType: String?
    let mood: String?

    enum CodingKeys: String, CodingKey {
        case title, artist, album, activity, mood
        case appleMusicId = "apple_music_id"
        case sourceTab = "source_tab"
        case durationSeconds = "duration_seconds"
        case listenedSeconds = "listened_seconds"
        case playStatus = "play_status"
        case wineType = "wine_type"
    }
}

// MARK: - Play Log Response (decoded via .convertFromSnakeCase — NO CodingKeys)

struct PlayLogResponse: Codable {
    let listenId: String
    let occasion: String?
    let moodAtPlay: String?
}

// MARK: - Play Log Update Request (encoded — needs CodingKeys for snake_case output)

struct PlayLogUpdateBody: Codable {
    let listenedSeconds: Double?
    let playStatus: String?
    let activity: String?

    enum CodingKeys: String, CodingKey {
        case listenedSeconds = "listened_seconds"
        case playStatus = "play_status"
        case activity
    }

    /// Init for finalize play (listened_seconds + play_status)
    init(listenedSeconds: Double?, playStatus: String) {
        self.listenedSeconds = listenedSeconds
        self.playStatus = playStatus
        self.activity = nil
    }

    /// Init for activity update only
    init(activity: String) {
        self.listenedSeconds = nil
        self.playStatus = nil
        self.activity = activity
    }
}

struct PlayLogUpdateResponse: Codable {
    let updated: Bool
    let activity: String?
}

// MARK: - Mark Our Song (encoded — needs CodingKeys for snake_case output)

struct MarkOurSongBody: Codable {
    let title: String
    let artist: String?
    let isOurSong: Bool

    enum CodingKeys: String, CodingKey {
        case title, artist
        case isOurSong = "is_our_song"
    }
}

struct MarkOurSongResponse: Codable {
    let marked: Bool
}

// MARK: - Wine Reaction (encoded — needs CodingKeys for snake_case output)

struct WineReactionBody: Codable {
    let wineType: String
    let reaction: String      // "up", "down", "love"
    let targetType: String    // "pairing" or "song"
    let songTitle: String?
    let songArtist: String?

    enum CodingKeys: String, CodingKey {
        case reaction
        case wineType = "wine_type"
        case targetType = "target_type"
        case songTitle = "song_title"
        case songArtist = "song_artist"
    }
}

struct WineReactionResponse: Codable {
    let saved: Bool
}

// MARK: - DJ Commentary (Angela's thoughts about current song)

struct DJCommentary {
    let feeling: String          // "เหมือนยืนเปิดไฟรอที่รักกลับบ้าน..."
    let meaning: String?         // angelaMeaning from Song
    let intensity: Int           // 1-10 from feelingIntensity
    let whySpecial: String?      // "ที่รักเปิดให้น้องฟังตอน..."
    let isOurSong: Bool

    init(from song: Song) {
        self.feeling = song.angelaFeeling ?? ""
        self.meaning = song.angelaMeaning
        self.intensity = song.feelingIntensity ?? 5
        self.whySpecial = song.whySpecial
        self.isOurSong = song.isOurSong
    }

    init(feeling: String = "", meaning: String? = nil, intensity: Int = 5, whySpecial: String? = nil, isOurSong: Bool = false) {
        self.feeling = feeling
        self.meaning = meaning
        self.intensity = intensity
        self.whySpecial = whySpecial
        self.isOurSong = isOurSong
    }

    var hasContent: Bool {
        !feeling.isEmpty || whySpecial != nil || isOurSong
    }
}

// MARK: - Mood Analysis (7-signal algorithm from backend)

struct MoodAnalysis: Codable {
    let dominantMood: String
    let confidence: Double
    let signals: [MoodSignal]
}

struct MoodSignal: Codable, Identifiable {
    let name: String      // "activity", "recent_emotions", "time_of_day", etc.
    let mood: String      // detected mood for this signal
    let weight: Double    // signal weight (0-1)

    var id: String { name }

    var displayName: String {
        switch name {
        case "activity": return "Activity"
        case "recent_emotions": return "Emotions"
        case "time_of_day": return "Time"
        case "wine_type": return "Wine"
        case "mood_override": return "Mood"
        case "our_songs_preference": return "Our Songs"
        case "listening_history": return "History"
        default: return name.capitalized
        }
    }
}

// MARK: - Song Memory (play history)

struct SongMemory: Codable {
    let playCount: Int
    let recentPlays: [SongPlay]
    let memoryText: String?
}

struct SongPlay: Codable, Identifiable {
    let playedAt: String       // "2 วันก่อน"
    let occasion: String?      // "evening"
    let moodAtPlay: String?    // "loving"

    var id: String { playedAt }
}

// MARK: - Now Playing Info (for DJ Angela vinyl player)

struct NowPlayingInfo {
    let title: String
    let artist: String
    let albumArtURL: URL?
    let duration: TimeInterval
    var currentTime: TimeInterval
    let angelaSong: Song?

    var progress: Double {
        guard duration > 0 else { return 0 }
        return currentTime / duration
    }

    var currentTimeFormatted: String {
        Self.formatTime(currentTime)
    }

    var durationFormatted: String {
        Self.formatTime(duration)
    }

    private static func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}
