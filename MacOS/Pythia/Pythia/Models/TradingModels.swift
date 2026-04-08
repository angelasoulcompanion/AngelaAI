//
//  TradingModels.swift
//  Pythia — Screener, Trade Plans, Narrative models (Phase 8)
//

import Foundation

// MARK: - Smart Screener

struct ScreenerResponse: Codable {
    let query: String
    let results: [ScreenerResultItem]
    let filtersApplied: [ScreenerFilter]?
    let total: Int
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case query, results
        case filtersApplied = "filters_applied"
        case total, success, message
    }
}

struct ScreenerResultItem: Codable, Identifiable {
    var id: String { assetId }
    let assetId: String
    let symbol: String
    let name: String?
    let sector: String?
    let price: Double
    let rsi: Double?
    let momentum5d: Double?
    let momentum20d: Double?
    let volumeRatio: Double?
    let sma20AboveSma50: Bool?
    let annualVol: Double?
    let deviationFromSma50: Double?
    let compositeScore: Double?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol, name, sector, price, rsi
        case momentum5d = "momentum_5d"
        case momentum20d = "momentum_20d"
        case volumeRatio = "volume_ratio"
        case sma20AboveSma50 = "sma20_above_sma50"
        case annualVol = "annual_vol"
        case deviationFromSma50 = "deviation_from_sma50"
        case compositeScore = "composite_score"
    }
}

struct ScreenerFilter: Codable {
    let type: String?
    let op: String?
    let value: AnyCodable?

    enum CodingKeys: String, CodingKey {
        case type
        case op = "operator"
        case value
    }
}

struct ScreenerPresetResponse: Codable {
    let presets: [ScreenerPreset]
}

struct ScreenerPreset: Codable, Identifiable {
    var id: String { key }
    let key: String
    let name: String
    let description: String
}

// MARK: - Trade Plans

struct TradePlanResponse: Codable {
    let planId: String?
    let assetId: String
    let symbol: String
    let direction: String
    let currentPrice: Double
    let entryPrice: Double
    let stopLoss: Double
    let takeProfit1: Double
    let takeProfit2: Double
    let takeProfit3: Double
    let positionSizePct: Double
    let riskReward: Double
    let riskPct: Double
    let rationale: String?
    let regime: String?
    let supportLevels: [Double]?
    let resistanceLevels: [Double]?
    let signalsSummary: String?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case planId = "plan_id"
        case assetId = "asset_id"
        case symbol, direction
        case currentPrice = "current_price"
        case entryPrice = "entry_price"
        case stopLoss = "stop_loss"
        case takeProfit1 = "take_profit_1"
        case takeProfit2 = "take_profit_2"
        case takeProfit3 = "take_profit_3"
        case positionSizePct = "position_size_pct"
        case riskReward = "risk_reward"
        case riskPct = "risk_pct"
        case rationale, regime
        case supportLevels = "support_levels"
        case resistanceLevels = "resistance_levels"
        case signalsSummary = "signals_summary"
        case success, message
    }
}

struct TradePlanListResponse: Codable {
    let plans: [TradePlanSummary]
    let count: Int
}

struct TradePlanSummary: Codable, Identifiable {
    var id: String { planId }
    let planId: String
    let symbol: String
    let direction: String
    let entryPrice: Double
    let stopLoss: Double
    let riskReward: Double
    let status: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case planId = "plan_id"
        case symbol, direction
        case entryPrice = "entry_price"
        case stopLoss = "stop_loss"
        case riskReward = "risk_reward"
        case status
        case createdAt = "created_at"
    }
}

// MARK: - Correlation Monitor

struct CorrelationMonitorResponse: Codable {
    let portfolioId: String
    let correlationRegime: String
    let avgCorrelation: Double
    let avgHistorical: Double
    let shifts: [CorrelationShiftItem]
    let matrix: [[Double]]?
    let symbols: [String]?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case correlationRegime = "correlation_regime"
        case avgCorrelation = "avg_correlation"
        case avgHistorical = "avg_historical"
        case shifts, matrix, symbols, success, message
    }
}

struct CorrelationShiftItem: Codable, Identifiable {
    var id: String { "\(asset1)_\(asset2)" }
    let asset1: String
    let asset2: String
    let currentCorr: Double
    let historicalCorr: Double
    let shift: Double
    let significance: String

    enum CodingKeys: String, CodingKey {
        case asset1 = "asset_1"
        case asset2 = "asset_2"
        case currentCorr = "current_corr"
        case historicalCorr = "historical_corr"
        case shift, significance
    }
}

// MARK: - Event Impact

struct EventImpactResponse: Codable {
    let assetId: String
    let symbol: String
    let eventType: String
    let avgMovePct: Double
    let avgPreMove: Double
    let avgPostMove: Double
    let positiveRate: Double
    let eventsAnalyzed: Int
    let upcomingEvents: [EventItem]?
    let historicalEvents: [HistoricalEvent]?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol
        case eventType = "event_type"
        case avgMovePct = "avg_move_pct"
        case avgPreMove = "avg_pre_move"
        case avgPostMove = "avg_post_move"
        case positiveRate = "positive_rate"
        case eventsAnalyzed = "events_analyzed"
        case upcomingEvents = "upcoming_events"
        case historicalEvents = "historical_events"
        case success, message
    }
}

struct EventItem: Codable, Identifiable {
    var id: String { "\(type ?? "")_\(event ?? "")" }
    let type: String?
    let event: String?
    let value: String?
}

struct HistoricalEvent: Codable, Identifiable {
    var id: String { date ?? "" }
    let date: String?
    let eventReturn: Double?
    let pre5d: Double?
    let post5d: Double?

    enum CodingKeys: String, CodingKey {
        case date
        case eventReturn = "event_return"
        case pre5d = "pre_5d"
        case post5d = "post_5d"
    }
}

// MARK: - Alerts

struct AlertListResponse: Codable {
    let alerts: [AlertItem]
    let count: Int
}

struct AlertItem: Codable, Identifiable {
    var id: String { alertId }
    let alertId: String
    let alertType: String
    let title: String
    let message: String?
    let severity: String
    let isRead: Bool
    let triggeredAt: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case alertId = "alert_id"
        case alertType = "alert_type"
        case title, message, severity
        case isRead = "is_read"
        case triggeredAt = "triggered_at"
        case createdAt = "created_at"
    }
}

struct UnreadCountResponse: Codable {
    let count: Int
}

struct CheckAlertsResponse: Codable {
    let generated: Int
    let alertIds: [String]?

    enum CodingKeys: String, CodingKey {
        case generated
        case alertIds = "alert_ids"
    }
}

// MARK: - Alpha ML

struct AlphaResponse: Codable {
    let assetId: String
    let symbol: String
    let predictedDirection: String
    let probability: Double
    let featureImportance: [FeatureImportanceItem]?
    let modelAccuracy: Double
    let trainingSamples: Int
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol
        case predictedDirection = "predicted_direction"
        case probability
        case featureImportance = "feature_importance"
        case modelAccuracy = "model_accuracy"
        case trainingSamples = "training_samples"
        case success, message
    }
}

struct FeatureImportanceItem: Codable, Identifiable {
    var id: String { feature }
    let feature: String
    let importance: Double
}

// MARK: - Rebalance

struct RebalanceResponse: Codable {
    let portfolioId: String
    let planType: String
    let totalValue: Double
    let trades: [RebalanceTrade]
    let maxDrift: Double
    let estimatedCost: Double
    let needsRebalance: Bool
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case planType = "plan_type"
        case totalValue = "total_value"
        case trades
        case maxDrift = "max_drift"
        case estimatedCost = "estimated_cost"
        case needsRebalance = "needs_rebalance"
        case success, message
    }
}

struct RebalanceTrade: Codable, Identifiable {
    var id: String { assetId }
    let assetId: String
    let symbol: String
    let currentWeight: Double
    let targetWeight: Double
    let drift: Double
    let action: String
    let tradeValue: Double

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol
        case currentWeight = "current_weight"
        case targetWeight = "target_weight"
        case drift, action
        case tradeValue = "trade_value"
    }
}

// MARK: - Risk Budget

struct RiskBudgetResponse: Codable {
    let portfolioId: String
    let totalBudget: Double
    let allocations: [RiskAllocation]
    let utilization: Double
    let regime: String?
    let aiAdvice: String?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case totalBudget = "total_budget"
        case allocations, utilization, regime
        case aiAdvice = "ai_advice"
        case success, message
    }
}

struct RiskAllocation: Codable, Identifiable {
    var id: String { strategyId }
    let strategyId: String
    let strategyName: String
    let strategyType: String
    let riskBudgetPct: Double
    let maxPositionPct: Double

    enum CodingKeys: String, CodingKey {
        case strategyId = "strategy_id"
        case strategyName = "strategy_name"
        case strategyType = "strategy_type"
        case riskBudgetPct = "risk_budget_pct"
        case maxPositionPct = "max_position_pct"
    }
}

// MARK: - Market Narrative

struct NarrativeResponse: Codable {
    let headline: String?
    let summary: String?
    let keyThemes: [String]?
    let riskFactors: [String]?
    let opportunities: [String]?
    let marketRegime: String?
    let generatedAt: String?
    let type: String?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case headline, summary
        case keyThemes = "key_themes"
        case riskFactors = "risk_factors"
        case opportunities
        case marketRegime = "market_regime"
        case generatedAt = "generated_at"
        case type, success, message
    }
}

// MARK: - Alpha Ideas (Factor Research)

struct AlphaIdeasResponse: Codable {
    let ideas: [AlphaIdeaItem]
    let compositeRanking: [AlphaIdeaStock]
    let totalStocksScanned: Int
    let scanTimeSeconds: Double
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case ideas
        case compositeRanking = "composite_ranking"
        case totalStocksScanned = "total_stocks_scanned"
        case scanTimeSeconds = "scan_time_seconds"
        case success, message
    }
}

struct AlphaIdeaItem: Codable, Identifiable {
    var id: String { ideaId }
    let ideaId: String
    let name: String
    let description: String
    let longRationale: String
    let shortRationale: String
    let longCandidates: [AlphaIdeaStock]
    let shortCandidates: [AlphaIdeaStock]

    enum CodingKeys: String, CodingKey {
        case ideaId = "idea_id"
        case name, description
        case longRationale = "long_rationale"
        case shortRationale = "short_rationale"
        case longCandidates = "long_candidates"
        case shortCandidates = "short_candidates"
    }
}

struct AlphaIdeaStock: Codable, Identifiable {
    var id: String { assetId }
    let assetId: String
    let symbol: String
    let name: String?
    let sector: String?
    let price: Double
    let babScore: Double?
    let valueScore: Double?
    let sizeScore: Double?
    let strScore: Double?
    let momScore: Double?
    let ltrScore: Double?
    let bavScore: Double?
    let compositeScore: Double
    let beta: Double?
    let pbRatio: Double?
    let marketCap: Double?
    let return1w: Double?
    let return6m: Double?
    let return12m: Double?
    let return3y: Double?
    let annualVol: Double?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol, name, sector, price
        case babScore = "bab_score"
        case valueScore = "value_score"
        case sizeScore = "size_score"
        case strScore = "str_score"
        case momScore = "mom_score"
        case ltrScore = "ltr_score"
        case bavScore = "bav_score"
        case compositeScore = "composite_score"
        case beta
        case pbRatio = "pb_ratio"
        case marketCap = "market_cap"
        case return1w = "return_1w"
        case return6m = "return_6m"
        case return12m = "return_12m"
        case return3y = "return_3y"
        case annualVol = "annual_vol"
    }
}
