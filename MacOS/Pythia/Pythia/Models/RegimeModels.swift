//
//  RegimeModels.swift
//  Pythia — Market Regime Detection models (Phase 7.1)
//

import Foundation

// MARK: - Regime Detection

struct RegimeResponse: Codable {
    let symbol: String
    let regime: String
    let probability: Double
    let allProbabilities: [String: Double]?
    let volatility: Double
    let trendStrength: Double
    let detectedAt: String?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case symbol, regime, probability
        case allProbabilities = "all_probabilities"
        case volatility
        case trendStrength = "trend_strength"
        case detectedAt = "detected_at"
        case success, message
    }
}

struct RegimeHistoryResponse: Codable {
    let symbol: String
    let history: [RegimeHistoryPoint]
    let count: Int
}

struct RegimeHistoryPoint: Codable, Identifiable {
    var id: String { date }
    let date: String
    let regime: String
    let probability: Double
    let volatility: Double
}

struct MarketStateResponse: Codable {
    let overallRegime: String
    let riskLevel: String
    let components: [MarketStateComponent]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case overallRegime = "overall_regime"
        case riskLevel = "risk_level"
        case components, success, message
    }
}

struct MarketStateComponent: Codable, Identifiable {
    var id: String { symbol }
    let symbol: String
    let name: String
    let region: String?
    let regime: String
    let probability: Double
    let volatility: Double
    let trendStrength: Double

    enum CodingKeys: String, CodingKey {
        case symbol, name, region, regime, probability, volatility
        case trendStrength = "trend_strength"
    }
}
