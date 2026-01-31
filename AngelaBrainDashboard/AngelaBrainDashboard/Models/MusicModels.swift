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
