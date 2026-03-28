//
//  AngelaBrainModels.swift
//  AITop
//
//  Codable models for Angela Brain dashboard.
//

import Foundation

// MARK: - Summary

struct BrainSummary: Codable {
    let conversations: Int
    let knowledge: Int
    let learnings: Int
    let emotions: Int
    let projects: Int
    let totalHours: Double
}

// MARK: - Conversation Volume

struct DailyConversation: Codable, Identifiable {
    let day: String
    let count: Int
    let sessions: Int

    var id: String { day }
}

// MARK: - Categories

struct CategoryCount: Codable, Identifiable {
    let category: String
    let count: Int

    var id: String { category }
}

// MARK: - Projects

struct ProjectInfo: Codable, Identifiable {
    let projectCode: String
    let projectName: String
    let status: String
    let category: String
    let totalSessions: Int
    let totalHours: Double

    var id: String { projectCode }
}

// MARK: - Emotions

struct RecentEmotion: Codable, Identifiable {
    let emotion: String
    let intensity: Double
    let context: String
    let feltAt: String?

    var id: String { "\(emotion)-\(feltAt ?? UUID().uuidString)" }
}

// MARK: - Consciousness

struct ConsciousnessEvent: Codable, Identifiable {
    let signalType: String
    let signalValue: Double
    let details: String
    let createdAt: String?

    var id: String { "\(signalType)-\(createdAt ?? UUID().uuidString)" }
}

// MARK: - Top Knowledge

struct TopKnowledge: Codable, Identifiable {
    let conceptName: String
    let conceptCategory: String
    let understandingLevel: Double
    let timesReferenced: Int

    var id: String { conceptName }
}

// MARK: - Combined Response

struct AngelaBrainResponse: Codable {
    let summary: BrainSummary
    let conversationVolume: [DailyConversation]
    let knowledgeCategories: [CategoryCount]
    let learningCategories: [CategoryCount]
    let projects: [ProjectInfo]
    let recentEmotions: [RecentEmotion]
    let consciousness: [ConsciousnessEvent]
    let topKnowledge: [TopKnowledge]
}

// MARK: - Project Detail

struct ProjectDetail: Codable {
    let projectCode: String
    let projectName: String
    let description: String
    let projectType: String
    let category: String
    let status: String
    let priority: Int
    let repositoryUrl: String
    let workingDirectory: String
    let davidRole: String
    let angelaRole: String
    let startedAt: String?
    let targetCompletion: String?
    let totalSessions: Int
    let totalHours: Double
    let tags: [String]
}

struct WorkSession: Codable, Identifiable {
    let sessionNumber: Int
    let sessionDate: String?
    let startedAt: String?
    let endedAt: String?
    let durationMinutes: Int
    let summary: String
    let accomplishments: [String]
    let mood: String
    let productivityScore: Double
    let gitCommitsCount: Int

    var id: Int { sessionNumber }
}

struct GitCommit: Codable, Identifiable {
    let commitHash: String
    let commitMessage: String
    let filesChanged: Int
    let insertions: Int
    let deletions: Int
    let committedAt: String?

    var id: String { commitHash }
}

struct ProjectPattern: Codable, Identifiable {
    let patternName: String
    let patternType: String
    let description: String
    let usedCount: Int
    let filePath: String

    var id: String { patternName }
}

struct ProjectDetailResponse: Codable {
    let project: ProjectDetail
    let sessions: [WorkSession]
    let commits: [GitCommit]
    let patterns: [ProjectPattern]
}

// MARK: - Knowledge Graph

struct KnowledgeGraphResponse: Codable {
    let projects: [GraphProject]
    let categories: [GraphCategory]
    let edges: [GraphEdge]
    let typeBreakdown: [TypeCount]
    let techStack: [TechStackItem]?
}

struct TechStackItem: Codable, Identifiable {
    let name: String
    let techType: String
    let projects: [String]
    let projectCount: Int

    var id: String { name }
}

struct GraphProject: Codable, Identifiable {
    let id: String
    let code: String
    let name: String
    let description: String?
    let status: String?
    let projectType: String?
    let kbCount: Int
    let hours: Double
    let sessions: Int?
    let createdAt: String?
    let lastKnowledgeAt: String?
    let typeBreakdown: [String: Int]?
}

struct GraphCategory: Codable, Identifiable {
    let id: String
    let name: String
    let count: Int
    let projects: [String]
}

struct GraphEdge: Codable, Identifiable {
    let fromProject: String
    let toProject: String
    let sharedCount: Int
    let categories: [String]

    var id: String { "\(fromProject)-\(toProject)" }
}

struct TypeCount: Codable, Identifiable {
    let id: String
    let type: String
    let count: Int
}
