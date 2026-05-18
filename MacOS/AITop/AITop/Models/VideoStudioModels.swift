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
    let audience: String?
    let persona: String?
    let notes: String?
    let segmentCount: Int?
    let completedCount: Int?

    // Hashable / Equatable are synthesized over ALL stored properties so that
    // SwiftUI ForEach diffing notices when a project's progress counters
    // change. (An id-only `==` would suppress the row re-render when the
    // sidebar badge needs to update from "3/5" to "4/5".)

    /// True when all known segments are marked done. Falls back to false
    /// while the count fields haven't been backfilled yet.
    var isFullyCompleted: Bool {
        guard let total = segmentCount, total > 0,
              let done = completedCount else { return false }
        return done >= total
    }
}

struct VideoProjectDetailEnvelope: Codable {
    let project: VideoProjectFull
    var segments: [VideoSegment]
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
    let persona: String?
    let notes: String?
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
    let completedAt: Date?
    let latestPrompt: VideoPromptVersion?

    // Hashable / Equatable synthesized over all properties — required for
    // SwiftUI to redraw a row when `completedAt` flips on toggle. An
    // id-only `==` would silently swallow the change.

    var pageRange: String { "\(startPage)–\(endPage)" }
    var isCompleted: Bool { completedAt != nil }

    /// Copy with a new completion timestamp — fields are `let`, so the toggle
    /// flow rebuilds the struct.
    func with(completedAt newValue: Date?) -> VideoSegment {
        VideoSegment(
            id: id,
            projectId: projectId,
            sequence: sequence,
            title: title,
            startPage: startPage,
            endPage: endPage,
            pageCount: pageCount,
            estMinutes: estMinutes,
            cognitiveLoad: cognitiveLoad,
            cutsMidSection: cutsMidSection,
            status: status,
            completedAt: newValue,
            latestPrompt: latestPrompt
        )
    }
}

struct VideoSegmentCompletionResponse: Codable {
    let id: String
    let projectId: String
    let completedAt: Date?
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

// MARK: - Project edit / delete

struct VideoProjectUpdateRequest: Codable {
    let title: String?
    let audience: String?
    let persona: String?
    let notes: String?
}

struct VideoProjectDeleteResponse: Codable {
    let deleted: Bool
    let pdfRemoved: Bool
    let pdfSha256: String
}
