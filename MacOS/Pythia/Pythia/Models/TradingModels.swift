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
