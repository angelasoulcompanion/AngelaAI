//
//  VideoStudioModels.swift
//  AITop
//
//  Codable models for the Angelora Video Studio tab.
//  Backend route prefix: /api/video-studio
//
//  After the 2026-05-04 redesign, AITop only does:
//    Upload PDF → analyze → generate prompts → copy to clipboard.
//  The NotebookLM submission/QA bridge has been removed.
//

import Foundation

// MARK: - Project list / detail

struct VideoProject: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let pdfSha256: String
    let originalFilename: String
    let byteSize: Int
    let totalPages: Int
    let totalEstimatedMinutes: Double
    let recommendedCount: Int
    let status: String
    let machine: String?
    let createdAt: Date

    func hash(into hasher: inout Hasher) { hasher.combine(id) }
    static func == (l: VideoProject, r: VideoProject) -> Bool { l.id == r.id }
}

struct VideoProjectDetailEnvelope: Codable {
    let project: VideoProjectFull
    let segments: [VideoSegment]
}

struct VideoProjectFull: Codable {
    let id: String
    let title: String
    let pdfSha256: String
    let originalFilename: String
    let byteSize: Int
    let totalPages: Int
    let totalEstimatedMinutes: Double
    let recommendedCount: Int
    let audience: String
    let alternatives: [VideoSplitAlternative]?
    let status: String
    let createdAt: Date
}

struct VideoSplitAlternative: Codable, Hashable {
    let count: Int
    let maxMinutes: Double
    let tradeoff: String
}

struct VideoSegment: Codable, Identifiable, Hashable {
    let id: String
    let projectId: String
    let sequence: Int
    let title: String?
    let startPage: Int
    let endPage: Int
    let pageCount: Int
    let estMinutes: Double
    let cognitiveLoad: Double
    let cutsMidSection: Bool
    let status: String           // pending | analyzed | prompt_ready
    let latestPrompt: VideoPromptVersion?

    func hash(into hasher: inout Hasher) { hasher.combine(id) }
    static func == (l: VideoSegment, r: VideoSegment) -> Bool { l.id == r.id }

    var pageRange: String { "\(startPage)–\(endPage)" }
}

struct VideoPromptVersion: Codable, Hashable {
    let templateName: String
    let notebooklmFormat: String
    let visualStyle: String
    let targetMinutes: Int
    let filledPrompt: String
    let version: Int
}

// MARK: - Requests / responses

struct VideoUploadResponse: Codable {
    let ok: Bool
    let projectId: String
    let pdfSha256: String
}

struct VideoProjectListEnvelope: Codable {
    let projects: [VideoProject]
}

struct VideoSegmentRegenerateRequest: Codable {
    let templateName: String?
    let audience: String?
    let personaName: String?
    let note: String?
}

struct VideoSegmentRegenerateResponse: Codable {
    let ok: Bool
    let version: Int
    let prompt: VideoPromptVersion
}
