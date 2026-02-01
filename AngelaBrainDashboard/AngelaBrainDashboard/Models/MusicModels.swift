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

    var id: String { songId }
}

// MARK: - Song Recommendation

struct SongRecommendation: Codable {
    let song: Song?
    let reason: String
    let basedOnEmotion: String
    let appleMusicDiscoverUrl: String?
    let moodSummary: String?
    let emotionDetails: [String]?
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

    /// Init from MusicKit.Song (Library, Playlists, Search results)
    init(from mkSong: MusicKit.Song) {
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
    }

    /// Init from Angela Song (Our Songs tab)
    init(from angelaSong: Song) {
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
    }

    /// Init from Angela Song enriched with MusicKit artwork
    init(from angelaSong: Song, artwork: URL?) {
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

    enum CodingKeys: String, CodingKey {
        case title, artist, album, activity
        case appleMusicId = "apple_music_id"
        case sourceTab = "source_tab"
        case durationSeconds = "duration_seconds"
        case listenedSeconds = "listened_seconds"
        case playStatus = "play_status"
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
    let playStatus: String

    enum CodingKeys: String, CodingKey {
        case listenedSeconds = "listened_seconds"
        case playStatus = "play_status"
    }
}

struct PlayLogUpdateResponse: Codable {
    let updated: Bool
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
