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
    let album: String?
    let youtubeUrl: String?
    let spotifyUrl: String?
    let appleMusicUrl: String?
    let whySpecial: String?
    let isOurSong: Bool
    let timesMentioned: Int
    let moodTags: [String]

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
