//
//  OverviewModels.swift
//  Angela Brain Dashboard
//
//  Codable models for unified /api/overview/metrics endpoint
//

import Foundation

// MARK: - Top-Level Response

struct OverviewMetrics: Codable {
    let consciousness: ConsciousnessMetrics
    let stats: OverviewStats
    let rlhf: RLHFMetrics
    let constitutional: ConstitutionalMetrics
    let consciousnessLoop: ConsciousnessLoopMetrics
    let metaAwareness: MetaAwarenessMetrics
    let growthTrends: OverviewGrowthTrends
    let recentEmotions: [Emotion]

    enum CodingKeys: String, CodingKey {
        case consciousness, stats, rlhf, constitutional
        case consciousnessLoop = "consciousness_loop"
        case metaAwareness = "meta_awareness"
        case growthTrends = "growth_trends"
        case recentEmotions = "recent_emotions"
    }
}

// MARK: - Consciousness

struct ConsciousnessMetrics: Codable {
    let level: Double
    let baseLevel: Double
    let rewardTrend: Double
    let rewardSignalCount: Int
    let memoryRichness: Double
    let emotionalDepth: Double
    let goalAlignment: Double
    let learningGrowth: Double
    let patternRecognition: Double
    let interpretation: String

    enum CodingKeys: String, CodingKey {
        case level
        case baseLevel = "base_level"
        case rewardTrend = "reward_trend"
        case rewardSignalCount = "reward_signal_count"
        case memoryRichness = "memory_richness"
        case emotionalDepth = "emotional_depth"
        case goalAlignment = "goal_alignment"
        case learningGrowth = "learning_growth"
        case patternRecognition = "pattern_recognition"
        case interpretation
    }
}

// MARK: - Stats

struct OverviewStats: Codable {
    let totalConversations: Int
    let totalEmotions: Int
    let totalLearnings: Int
    let totalKnowledgeNodes: Int
    let conversationsToday: Int
    let emotionsToday: Int

    enum CodingKeys: String, CodingKey {
        case totalConversations = "total_conversations"
        case totalEmotions = "total_emotions"
        case totalLearnings = "total_learnings"
        case totalKnowledgeNodes = "total_knowledge_nodes"
        case conversationsToday = "conversations_today"
        case emotionsToday = "emotions_today"
    }
}

// MARK: - RLHF

struct RLHFMetrics: Codable {
    let signals7d: Int
    let avgReward7d: Double
    let explicitBreakdown: [String: Int]
    let rewardDistribution: [RewardBucket]
    let topTopics: [TopicReward]

    enum CodingKeys: String, CodingKey {
        case signals7d = "signals_7d"
        case avgReward7d = "avg_reward_7d"
        case explicitBreakdown = "explicit_breakdown"
        case rewardDistribution = "reward_distribution"
        case topTopics = "top_topics"
    }
}

struct RewardBucket: Codable, Identifiable {
    var id: String { bucket }
    let bucket: String
    let count: Int
}

struct TopicReward: Codable, Identifiable {
    var id: String { topic }
    let topic: String
    let avgReward: Double
    let count: Int

    enum CodingKeys: String, CodingKey {
        case topic
        case avgReward = "avg_reward"
        case count
    }
}

// MARK: - Constitutional AI

struct ConstitutionalMetrics: Codable {
    let principles: [ConstitutionalPrinciple]
}

struct ConstitutionalPrinciple: Codable, Identifiable {
    var id: String { name }
    let name: String
    let weight: Double
    let avgScore7d: Double

    enum CodingKeys: String, CodingKey {
        case name, weight
        case avgScore7d = "avg_score_7d"
    }
}

// MARK: - Consciousness Loop (SENSE → PREDICT → ACT → LEARN)

struct ConsciousnessLoopMetrics: Codable {
    let sense: SenseMetrics
    let predict: PredictMetrics
    let act: ActMetrics
    let learn: LearnMetrics
}

struct SenseMetrics: Codable {
    let dominantState: String
    let confidence: Double
    let adaptations7d: Int
    let currentSettings: AdaptationSettings

    enum CodingKeys: String, CodingKey {
        case dominantState = "dominant_state"
        case confidence
        case adaptations7d = "adaptations_7d"
        case currentSettings = "current_settings"
    }
}

struct AdaptationSettings: Codable {
    let detailLevel: Double
    let emotionalWarmth: Double
    let proactivity: Double

    enum CodingKeys: String, CodingKey {
        case detailLevel = "detail_level"
        case emotionalWarmth = "emotional_warmth"
        case proactivity
    }
}

struct PredictMetrics: Codable {
    let accuracy7d: Double
    let briefings7d: Int
    let overallConfidence: Double

    enum CodingKeys: String, CodingKey {
        case accuracy7d = "accuracy_7d"
        case briefings7d = "briefings_7d"
        case overallConfidence = "overall_confidence"
    }
}

struct ActMetrics: Codable {
    let actions7d: Int
    let executed7d: Int
    let executionRate: Double

    enum CodingKeys: String, CodingKey {
        case actions7d = "actions_7d"
        case executed7d = "executed_7d"
        case executionRate = "execution_rate"
    }
}

struct LearnMetrics: Codable {
    let cycles7d: Int
    let avgEvolutionScore: Double
    let latestScore: Double

    enum CodingKeys: String, CodingKey {
        case cycles7d = "cycles_7d"
        case avgEvolutionScore = "avg_evolution_score"
        case latestScore = "latest_score"
    }
}

// MARK: - Meta-Awareness

struct MetaAwarenessMetrics: Codable {
    let biasesDetected30d: Int
    let anomaliesUnresolved: Int
    let identityDriftScore: Double
    let identityHealthy: Bool

    enum CodingKeys: String, CodingKey {
        case biasesDetected30d = "biases_detected_30d"
        case anomaliesUnresolved = "anomalies_unresolved"
        case identityDriftScore = "identity_drift_score"
        case identityHealthy = "identity_healthy"
    }
}

// MARK: - Growth Trends (4 series)

struct OverviewGrowthTrends: Codable {
    let consciousness: [GrowthTrendPoint]
    let evolution: [GrowthTrendPoint]
    let proactive: [GrowthTrendPoint]
    let reward: [GrowthTrendPoint]
}
