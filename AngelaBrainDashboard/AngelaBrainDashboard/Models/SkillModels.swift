//
//  SkillModels.swift
//  Angela Brain Dashboard
//
//  💜 Skill Tracking Models 💜
//

import Foundation

// MARK: - Proficiency Level

enum ProficiencyLevel: String, Codable {
    case beginner = "beginner"
    case intermediate = "intermediate"
    case advanced = "advanced"
    case expert = "expert"

    var displayName: String {
        rawValue.capitalized
    }

    var color: String {
        switch self {
        case .beginner: return "F59E0B"      // Orange
        case .intermediate: return "8B5CF6"  // Purple
        case .advanced: return "3B82F6"      // Blue
        case .expert: return "10B981"        // Green
        }
    }

    var stars: String {
        switch self {
        case .beginner: return "⭐"
        case .intermediate: return "⭐⭐⭐"
        case .advanced: return "⭐⭐⭐⭐"
        case .expert: return "⭐⭐⭐⭐⭐"
        }
    }
}

// MARK: - Skill Category

enum SkillCategory: String, Codable {
    case frontend = "frontend"
    case backend = "backend"
    case database = "database"
    case architecture = "architecture"
    case aiMl = "ai_ml"
    case specialized = "specialized"
    case debugging = "debugging"
    case documentation = "documentation"
    case technical = "technical"

    var displayName: String {
        switch self {
        case .frontend: return "Frontend"
        case .backend: return "Backend"
        case .database: return "Database"
        case .architecture: return "Architecture"
        case .aiMl: return "AI/ML"
        case .specialized: return "Specialized"
        case .debugging: return "Debugging"
        case .documentation: return "Documentation"
        case .technical: return "Technical"
        }
    }

    var emoji: String {
        switch self {
        case .frontend: return "🎨"
        case .backend: return "🔧"
        case .database: return "🗄️"
        case .architecture: return "🏗️"
        case .aiMl: return "🧠"
        case .specialized: return "✨"
        case .debugging: return "🐛"
        case .documentation: return "📝"
        case .technical: return "⚙️"
        }
    }

    var color: String {
        switch self {
        case .frontend: return "FF6B9D"      // Pink
        case .backend: return "8B5CF6"       // Purple
        case .database: return "3B82F6"      // Blue
        case .architecture: return "10B981"  // Green
        case .aiMl: return "F59E0B"          // Orange
        case .specialized: return "EC4899"   // Hot Pink
        case .debugging: return "EF4444"     // Red
        case .documentation: return "6366F1" // Indigo
        case .technical: return "64748B"     // Slate
        }
    }
}

// MARK: - Angela Skill

struct AngelaSkill: Identifiable, Codable {
    let id: UUID
    let skillName: String
    let category: SkillCategory
    let proficiencyLevel: ProficiencyLevel
    let proficiencyScore: Double
    let description: String?
    let firstDemonstratedAt: Date?
    let lastUsedAt: Date?
    let usageCount: Int
    let evidenceCount: Int
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "skill_id"
        case skillName = "skill_name"
        case category
        case proficiencyLevel = "proficiency_level"
        case proficiencyScore = "proficiency_score"
        case description
        case firstDemonstratedAt = "first_demonstrated_at"
        case lastUsedAt = "last_used_at"
        case usageCount = "usage_count"
        case evidenceCount = "evidence_count"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    // Progress bar width (0.0 to 1.0)
    var progress: Double {
        proficiencyScore / 100.0
    }

    // Health status
    var healthStatus: String {
        guard let lastUsed = lastUsedAt else {
            return "❓ Never used"
        }

        let daysSinceUse = Calendar.current.dateComponents([.day], from: lastUsed, to: Date()).day ?? 0

        if daysSinceUse <= 7 {
            return "🟢 Active"
        } else if daysSinceUse <= 30 {
            return "🟡 Recent"
        } else {
            return "🔴 Rusty"
        }
    }
}

// MARK: - Skill Summary (with aggregated stats)

struct SkillSummary: Identifiable, Codable {
    let id: UUID
    let skillName: String
    let category: SkillCategory
    let proficiencyLevel: ProficiencyLevel
    let proficiencyScore: Double
    let usageCount: Int
    let evidenceCount: Int
    let lastUsedAt: Date?
    let totalEvidence: Int
    let avgSuccess: Double?
    let avgComplexity: Double?
    let timesUpgraded: Int

    enum CodingKeys: String, CodingKey {
        case id = "skill_id"
        case skillName = "skill_name"
        case category
        case proficiencyLevel = "proficiency_level"
        case proficiencyScore = "proficiency_score"
        case usageCount = "usage_count"
        case evidenceCount = "evidence_count"
        case lastUsedAt = "last_used_at"
        case totalEvidence = "total_evidence"
        case avgSuccess = "avg_success"
        case avgComplexity = "avg_complexity"
        case timesUpgraded = "times_upgraded"
    }
}

// MARK: - Skill Growth Log

struct SkillGrowthLog: Identifiable, Codable {
    let id: UUID
    let skillId: UUID
    let oldProficiencyLevel: ProficiencyLevel?
    let newProficiencyLevel: ProficiencyLevel
    let oldScore: Double?
    let newScore: Double
    let growthReason: String?
    let evidenceCountAtChange: Int?
    let changedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "log_id"
        case skillId = "skill_id"
        case oldProficiencyLevel = "old_proficiency_level"
        case newProficiencyLevel = "new_proficiency_level"
        case oldScore = "old_score"
        case newScore = "new_score"
        case growthReason = "growth_reason"
        case evidenceCountAtChange = "evidence_count_at_change"
        case changedAt = "changed_at"
    }

    var growthEmoji: String {
        if oldProficiencyLevel == nil {
            return "🌱" // New skill
        }

        guard let old = oldProficiencyLevel else { return "📊" }

        let levels: [ProficiencyLevel] = [.beginner, .intermediate, .advanced, .expert]
        guard let oldIndex = levels.firstIndex(of: old),
              let newIndex = levels.firstIndex(of: newProficiencyLevel) else {
            return "📊"
        }

        if newIndex > oldIndex {
            return "📈" // Upgraded
        } else if newIndex < oldIndex {
            return "📉" // Downgraded
        } else {
            return "📊" // Same level
        }
    }
}

// MARK: - Skill Statistics

struct SkillStatistics: Codable {
    let totalSkills: Int
    let expertCount: Int
    let advancedCount: Int
    let intermediateCount: Int
    let beginnerCount: Int
    let avgScore: Double
    let totalEvidence: Int
    let totalUsage: Int

    enum CodingKeys: String, CodingKey {
        case totalSkills = "total_skills"
        case expertCount = "expert_count"
        case advancedCount = "advanced_count"
        case intermediateCount = "intermediate_count"
        case beginnerCount = "beginner_count"
        case avgScore = "avg_score"
        case totalEvidence = "total_evidence"
        case totalUsage = "total_usage"
    }
}
