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
    let consciousnessLoop: ConsciousnessLoopMetrics
    let growthTrends: OverviewGrowthTrends
    let recentEmotions: [Emotion]
    let aiMetrics: AIMetricsData?
    let aiMetricsTrend: [AIMetricsTrendPoint]?
    let judgeDimensions: JudgeDimensionsData?
    let abTests: ABTestsData?

    enum CodingKeys: String, CodingKey {
        case consciousness, stats, rlhf
        case consciousnessLoop = "consciousness_loop"
        case growthTrends = "growth_trends"
        case recentEmotions = "recent_emotions"
        case aiMetrics = "ai_metrics"
        case aiMetricsTrend = "ai_metrics_trend"
        case judgeDimensions = "judge_dimensions"
        case abTests = "ab_tests"
    }
}

// MARK: - AI Quality Metrics

struct AIMetricsData: Codable {
    let satisfaction: SatisfactionData
    let engagement: EngagementData
    let correctionRate: CorrectionRateData
    let memoryAccuracy: MemoryAccuracyData

    enum CodingKeys: String, CodingKey {
        case satisfaction, engagement
        case correctionRate = "correction_rate"
        case memoryAccuracy = "memory_accuracy"
    }
}

struct SatisfactionData: Codable {
    let rate: Double
    let praise: Int
    let corrections: Int
    let total: Int
}

struct EngagementData: Codable {
    let rate: Double
    let engaged: Int
    let total: Int
}

struct CorrectionRateData: Codable {
    let rate: Double
    let corrections: Int
    let total: Int
}

struct MemoryAccuracyData: Codable {
    let accuracy: Double
    let totalRefs: Int
    let corrected: Int

    enum CodingKeys: String, CodingKey {
        case accuracy
        case totalRefs = "total_refs"
        case corrected
    }
}

// MARK: - LLM Judge Dimensions

struct JudgeDimensionsData: Codable {
    let dimensions: [String: DimensionStats]
    let totalEvaluated: Int
    let avgScore: Double
    let stddev: Double
    let scoreRange: [Double]

    enum CodingKeys: String, CodingKey {
        case dimensions
        case totalEvaluated = "total_evaluated"
        case avgScore = "avg_score"
        case stddev
        case scoreRange = "score_range"
    }
}

struct DimensionStats: Codable {
    let avg: Double
    let min: Int
    let max: Int
    let count: Int
}

// MARK: - A/B Test Results

struct ABTestsData: Codable {
    let total: Int
    let originalWins: Int
    let alternativeWins: Int
    let avgStrength: Double
    let pairsGenerated: Int
    let recent: [ABTestSummary]

    enum CodingKeys: String, CodingKey {
        case total
        case originalWins = "original_wins"
        case alternativeWins = "alternative_wins"
        case avgStrength = "avg_strength"
        case pairsGenerated = "pairs_generated"
        case recent
    }
}

struct ABTestSummary: Codable, Identifiable {
    var id: String { "\(topic ?? "?")-\(originalScore)-\(alternativeScore)" }
    let winner: String
    let originalScore: Double
    let alternativeScore: Double
    let strength: Double
    let topic: String?
    let reasoning: String?

    enum CodingKeys: String, CodingKey {
        case winner
        case originalScore = "original_score"
        case alternativeScore = "alternative_score"
        case strength, topic, reasoning
    }
}

// MARK: - AI Metrics Weekly Trend

struct AIMetricsTrendPoint: Codable, Identifiable {
    var id: String { week }
    let week: String
    let satisfaction: Double
    let engagement: Double
    let correctionRate: Double
    let avgReward: Double
    let total: Int

    enum CodingKeys: String, CodingKey {
        case week, satisfaction, engagement, total
        case correctionRate = "correction_rate"
        case avgReward = "avg_reward"
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
    let totalKnowledgeNodes: Int
    let conversationsToday: Int
    let activeDays30d: Int
    let avgMsgsPerSession: Double

    enum CodingKeys: String, CodingKey {
        case totalConversations = "total_conversations"
        case totalKnowledgeNodes = "total_knowledge_nodes"
        case conversationsToday = "conversations_today"
        case activeDays30d = "active_days_30d"
        case avgMsgsPerSession = "avg_msgs_per_session"
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

// MARK: - Growth Trends (4 series)

struct OverviewGrowthTrends: Codable {
    let consciousness: [GrowthTrendPoint]
    let evolution: [GrowthTrendPoint]
    let proactive: [GrowthTrendPoint]
    let reward: [GrowthTrendPoint]
}
