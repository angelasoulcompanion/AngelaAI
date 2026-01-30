//
//  ProjectModels.swift
//  Angela Brain Dashboard
//
//  Project, WorkSession, ProjectMilestone, ProjectLearning, ProjectDecision
//

import Foundation

// MARK: - Project

struct Project: Identifiable, Codable {
    let id: UUID
    let projectCode: String
    let projectName: String
    let description: String?
    let projectType: String           // "client", "personal", "learning", "maintenance"
    let category: String?
    let status: String                // "planning", "active", "paused", "completed", "archived"
    let priority: Int                 // 1-5 (1=highest)
    let repositoryUrl: String?
    let workingDirectory: String?
    let clientName: String?
    let davidRole: String?
    let angelaRole: String?
    let startedAt: Date?
    let targetCompletion: Date?
    let completedAt: Date?
    let totalSessions: Int
    let totalHours: Double
    let tags: [String]
    let createdAt: Date
    let updatedAt: Date
    let lastSessionDate: Date?

    enum CodingKeys: String, CodingKey {
        case id = "project_id"
        case projectCode = "project_code"
        case projectName = "project_name"
        case description
        case projectType = "project_type"
        case category
        case status
        case priority
        case repositoryUrl = "repository_url"
        case workingDirectory = "working_directory"
        case clientName = "client_name"
        case davidRole = "david_role"
        case angelaRole = "angela_role"
        case startedAt = "started_at"
        case targetCompletion = "target_completion"
        case completedAt = "completed_at"
        case totalSessions = "total_sessions"
        case totalHours = "total_hours"
        case tags
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case lastSessionDate = "last_session_date"
    }

    var isActive: Bool {
        status == "active"
    }

    var isCompleted: Bool {
        status == "completed"
    }

    var typeIcon: String {
        switch projectType {
        case "personal": return "brain.head.profile"
        case "client": return "briefcase.fill"
        case "learning": return "book.fill"
        case "maintenance": return "wrench.fill"
        case "Our Future": return "star.fill"
        default: return "folder.fill"
        }
    }

    var typeColor: String {
        switch projectType {
        case "client": return "3B82F6"      // Blue
        case "personal": return "9333EA"    // Purple
        case "learning": return "10B981"    // Green
        case "maintenance": return "F59E0B" // Orange
        case "Our Future": return "EC4899"  // Pink - Our Future together 💜
        default: return "6B7280"            // Gray
        }
    }
}

// MARK: - Work Session

struct WorkSession: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionNumber: Int
    let sessionDate: Date
    let startedAt: Date
    let endedAt: Date?
    let durationMinutes: Int?
    let sessionGoal: String?
    let davidRequests: String?
    let summary: String?
    let accomplishments: [String]
    let blockers: [String]
    let nextSteps: [String]
    let mood: String?                 // "productive", "challenging", "smooth", "learning", "debugging", "creative"
    let productivityScore: Double?    // 1-10
    let projectName: String?          // Joined from angela_projects

    enum CodingKeys: String, CodingKey {
        case id = "session_id"
        case projectId = "project_id"
        case sessionNumber = "session_number"
        case sessionDate = "session_date"
        case startedAt = "started_at"
        case endedAt = "ended_at"
        case durationMinutes = "duration_minutes"
        case sessionGoal = "session_goal"
        case davidRequests = "david_requests"
        case summary
        case accomplishments
        case blockers
        case nextSteps = "next_steps"
        case mood
        case productivityScore = "productivity_score"
        case projectName = "project_name"
    }

    var formattedDuration: String {
        guard let mins = durationMinutes else { return "N/A" }
        if mins < 60 {
            return "\(mins) min"
        } else {
            let hours = mins / 60
            let remainingMins = mins % 60
            return "\(hours)h \(remainingMins)m"
        }
    }

    var moodIcon: String {
        switch mood {
        case "productive": return "bolt.fill"
        case "learning": return "book.fill"
        case "debugging": return "ant.fill"
        case "challenging": return "exclamationmark.triangle.fill"
        case "smooth": return "sparkles"
        case "creative": return "paintbrush.fill"
        default: return "clock.fill"
        }
    }

    var moodColor: String {
        switch mood {
        case "productive": return "10B981"
        case "learning": return "3B82F6"
        case "debugging": return "F59E0B"
        case "challenging": return "EF4444"
        case "smooth": return "9333EA"
        case "creative": return "EC4899"
        default: return "6B7280"
        }
    }
}

// MARK: - Project Milestone

struct ProjectMilestone: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionId: UUID?
    let milestoneType: String         // "feature_complete", "bug_fixed", "release", "deployment", etc.
    let title: String
    let description: String?
    let significance: Int             // 1-10
    let achievedAt: Date
    let celebrationNote: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "milestone_id"
        case projectId = "project_id"
        case sessionId = "session_id"
        case milestoneType = "milestone_type"
        case title
        case description
        case significance
        case achievedAt = "achieved_at"
        case celebrationNote = "celebration_note"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch milestoneType {
        case "feature_complete": return "checkmark.seal.fill"
        case "bug_fixed": return "ant.fill"
        case "release": return "shippingbox.fill"
        case "deployment": return "cloud.fill"
        case "project_start": return "play.fill"
        case "project_complete": return "flag.fill"
        case "breakthrough": return "lightbulb.fill"
        case "decision": return "questionmark.circle.fill"
        default: return "star.fill"
        }
    }

    var typeColor: String {
        switch milestoneType {
        case "feature_complete": return "10B981"
        case "bug_fixed": return "F59E0B"
        case "release", "deployment": return "3B82F6"
        case "project_start", "project_complete": return "9333EA"
        case "breakthrough": return "FBBF24"
        default: return "6B7280"
        }
    }
}

// MARK: - Project Learning

struct ProjectLearning: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionId: UUID?
    let learningType: String          // "technical", "process", "tool", "pattern", "mistake", "best_practice"
    let category: String?
    let title: String
    let insight: String
    let context: String?
    let applicableTo: [String]
    let confidence: Double            // 0-1
    let learnedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "learning_id"
        case projectId = "project_id"
        case sessionId = "session_id"
        case learningType = "learning_type"
        case category
        case title
        case insight
        case context
        case applicableTo = "applicable_to"
        case confidence
        case learnedAt = "learned_at"
    }

    var typeIcon: String {
        switch learningType {
        case "technical": return "wrench.and.screwdriver.fill"
        case "process": return "flowchart.fill"
        case "tool": return "hammer.fill"
        case "pattern": return "square.grid.3x3.fill"
        case "mistake": return "exclamationmark.triangle.fill"
        case "best_practice": return "star.fill"
        default: return "lightbulb.fill"
        }
    }

    var typeColor: String {
        switch learningType {
        case "technical": return "9333EA"
        case "process": return "3B82F6"
        case "tool": return "6B7280"
        case "pattern": return "10B981"
        case "mistake": return "F59E0B"
        case "best_practice": return "FBBF24"
        default: return "EC4899"
        }
    }

    var confidencePercent: String {
        String(format: "%.0f%%", confidence * 100)
    }
}

// MARK: - Project Decision

struct ProjectDecision: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionId: UUID?
    let decisionType: String          // "architecture", "technology", "approach", etc.
    let title: String
    let context: String?
    let optionsConsidered: String?    // JSON string
    let decisionMade: String
    let reasoning: String?
    let decidedBy: String             // "david", "angela", "together"
    let outcome: String?              // "good", "neutral", "needs_revisit", "changed"
    let decidedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "decision_id"
        case projectId = "project_id"
        case sessionId = "session_id"
        case decisionType = "decision_type"
        case title
        case context
        case optionsConsidered = "options_considered"
        case decisionMade = "decision_made"
        case reasoning
        case decidedBy = "decided_by"
        case outcome
        case decidedAt = "decided_at"
    }
}
