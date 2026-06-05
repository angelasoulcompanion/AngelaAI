//
//  ProjectsModels.swift
//  AITop
//
//  Codable models for the Projects tracking page (detailed project tracker).
//  Mirrors routers/projects.py. Distinct type names avoid clashing with the
//  lighter project types in AngelaBrainModels.
//

import Foundation

// MARK: - Overview

struct ProjectsOverview: Codable {
    let totals: PortfolioTotals
    let projects: [ProjectCardInfo]
}

struct PortfolioTotals: Codable {
    let projects: Int
    let active: Int
    let sessions: Int
    let hours: Double
    let decisions: Int
    let activeGotchas: Int
    let commits: Int
    let weekSessions: Int
}

struct ProjectCardInfo: Codable, Identifiable, Hashable {
    let projectCode: String
    let projectName: String
    let status: String
    let priority: Int
    let totalSessions: Int
    let totalHours: Double
    let lastActive: String?
    let activeGotchas: Int
    let openThreads: Int
    let spark: [Double]
    let avgProductivity: Double

    var id: String { projectCode }
}

// MARK: - Detail

struct ProjectFullDetail: Codable {
    let project: ProjectMeta
    let kpis: ProjectKpis
    let threads: [String]
    let productivity: [ProductivityPoint]
    let sessions: [ProjectSession]
    let decisions: [ProjectDecision]
    let gotchas: [ProjectGotcha]
    let commits: [ProjectCommit]
    let milestones: [ProjectMilestone]
}

struct ProjectMeta: Codable {
    let projectCode: String
    let projectName: String
    let description: String
    let projectType: String
    let category: String
    let status: String
    let priority: Int
    let repositoryUrl: String
    let davidRole: String
    let angelaRole: String
    let startedAt: String?
    let targetCompletion: String?
    let totalSessions: Int
    let totalHours: Double
    let tags: [String]
}

struct ProjectKpis: Codable {
    let decisions: Int
    let mistakes: Int
    let activeGotchas: Int
    let commits: Int
    let milestones: Int
}

struct ProductivityPoint: Codable {
    let date: String?
    let score: Double
    let mood: String
}

struct ProjectSession: Codable, Identifiable {
    let sessionNumber: Int
    let sessionDate: String?
    let sessionGoal: String
    let summary: String
    let accomplishments: [String]
    let blockers: [String]
    let nextSteps: [String]
    let mood: String
    let productivityScore: Double
    let durationMinutes: Int
    let gitCommitsCount: Int

    var id: Int { sessionNumber }
}

struct ProjectDecision: Codable, Identifiable {
    let decisionTitle: String
    let category: String
    let decisionMade: String
    let status: String
    let decidedAt: String?

    var id: String { "\(decisionTitle)-\(decidedAt ?? "")" }
}

struct ProjectGotcha: Codable, Identifiable {
    let severity: String
    let title: String
    let howToPrevent: String
    let mistakeType: String
    let createdAt: String?

    var id: String { "\(title)-\(createdAt ?? "")" }
}

struct ProjectCommit: Codable, Identifiable {
    let commitHash: String
    let commitMessage: String
    let filesChanged: Int
    let insertions: Int
    let deletions: Int
    let committedAt: String?

    var id: String { commitHash }
}

struct ProjectMilestone: Codable, Identifiable {
    let title: String
    let milestoneType: String
    let description: String
    let significance: Int
    let celebrationNote: String
    let achievedAt: String?

    var id: String { "\(title)-\(achievedAt ?? "")" }
}
