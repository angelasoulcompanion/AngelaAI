//
//  BrainStatusModels.swift
//  Angela Brain Dashboard
//
//  Codable models for /api/brain-status/metrics endpoint
//

import Foundation

// MARK: - Top-Level Response

struct BrainStatusMetrics: Codable {
    let stimuli: StimuliSummary
    let thoughts: ThoughtsSummary
    let expression: ExpressionSummary
    let reflections: ReflectionsSummary
    let migration: MigrationSummary
    let consolidation: ConsolidationSummary
}

// MARK: - Stimuli

struct StimuliSummary: Codable {
    let total24h: Int
    let total7d: Int
    let avgSalience: Double
    let highSalience: Int
    let byType: [StimuliTypeCount]
    let topSalient: [SalientStimulus]
    let salienceDims: [String: Double]

    enum CodingKeys: String, CodingKey {
        case total24h = "total_24h"
        case total7d = "total_7d"
        case avgSalience = "avg_salience"
        case highSalience = "high_salience"
        case byType = "by_type"
        case topSalient = "top_salient"
        case salienceDims = "salience_dims"
    }
}

struct StimuliTypeCount: Codable, Identifiable {
    var id: String { type }
    let type: String
    let count: Int
    let avgSalience: Double

    enum CodingKeys: String, CodingKey {
        case type, count
        case avgSalience = "avg_salience"
    }
}

struct SalientStimulus: Codable, Identifiable {
    let id: String
    let codeletType: String
    let stimulusType: String?
    let content: String
    let salienceScore: Double
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case codeletType = "codelet_type"
        case stimulusType = "stimulus_type"
        case content
        case salienceScore = "salience_score"
        case createdAt = "created_at"
    }
}

// MARK: - Thoughts

struct ThoughtsSummary: Codable {
    let total24h: Int
    let total7d: Int
    let system1: Int
    let system2: Int
    let avgMotivation: Double
    let highMotivation: Int
    let topThoughts: [TopThought]

    enum CodingKeys: String, CodingKey {
        case total24h = "total_24h"
        case total7d = "total_7d"
        case system1, system2
        case avgMotivation = "avg_motivation"
        case highMotivation = "high_motivation"
        case topThoughts = "top_thoughts"
    }
}

struct TopThought: Codable, Identifiable {
    let id: String
    let type: String
    let template: String?
    let content: String
    let motivation: Double
    let expressedVia: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, type, template, content, motivation
        case expressedVia = "expressed_via"
        case createdAt = "created_at"
    }
}

// MARK: - Expression

struct ExpressionSummary: Codable {
    let generated: Int
    let totalExpressed: Int
    let telegramCount: Int
    let chatCount: Int
    let suppressedCount: Int
    let suppressReasons: [String: Int]
    let effectivenessAvg: Double
    let davidResponses: DavidResponseCounts

    enum CodingKeys: String, CodingKey {
        case generated
        case totalExpressed = "total_expressed"
        case telegramCount = "telegram_count"
        case chatCount = "chat_count"
        case suppressedCount = "suppressed_count"
        case suppressReasons = "suppress_reasons"
        case effectivenessAvg = "effectiveness_avg"
        case davidResponses = "david_responses"
    }
}

struct DavidResponseCounts: Codable {
    let positive: Int
    let neutral: Int
    let negative: Int
}

// MARK: - Reflections

struct ReflectionsSummary: Codable {
    let total7d: Int
    let integratedCount: Int
    let byType: [String: Int]
    let recent: [RecentReflection]

    enum CodingKeys: String, CodingKey {
        case total7d = "total_7d"
        case integratedCount = "integrated_count"
        case byType = "by_type"
        case recent
    }
}

struct RecentReflection: Codable, Identifiable {
    let id: String
    let type: String
    let depth: Int?
    let content: String
    let status: String
    let importanceSum: Double
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, type, depth, content, status
        case importanceSum = "importance_sum"
        case createdAt = "created_at"
    }
}

// MARK: - Migration

struct MigrationSummary: Codable {
    let brainWins: Int
    let ruleWins: Int
    let ties: Int
    let totalComparisons: Int
    let readinessPct: Double
    let routing: [FeatureRouting]

    enum CodingKeys: String, CodingKey {
        case brainWins = "brain_wins"
        case ruleWins = "rule_wins"
        case ties
        case totalComparisons = "total_comparisons"
        case readinessPct = "readiness_pct"
        case routing
    }
}

struct FeatureRouting: Codable, Identifiable {
    var id: String { feature }
    let feature: String
    let mode: RoutingMode

    enum RoutingMode: Codable {
        case string(String)

        init(from decoder: Decoder) throws {
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)
            self = .string(value)
        }

        func encode(to encoder: Encoder) throws {
            var container = encoder.singleValueContainer()
            switch self {
            case .string(let value):
                try container.encode(value)
            }
        }

        var label: String {
            switch self {
            case .string(let s): return s
            }
        }
    }
}

// MARK: - Consolidation

struct ConsolidationSummary: Codable {
    let clusters7d: Int
    let episodesProcessed: Int
    let knowledgeCreated: Int
    let avgConfidence: Double
    let topTopics: [ConsolidationTopic]

    enum CodingKeys: String, CodingKey {
        case clusters7d = "clusters_7d"
        case episodesProcessed = "episodes_processed"
        case knowledgeCreated = "knowledge_created"
        case avgConfidence = "avg_confidence"
        case topTopics = "top_topics"
    }
}

struct ConsolidationTopic: Codable, Identifiable {
    var id: String { topic }
    let topic: String
    let count: Int
    let avgConfidence: Double

    enum CodingKeys: String, CodingKey {
        case topic, count
        case avgConfidence = "avg_confidence"
    }
}
