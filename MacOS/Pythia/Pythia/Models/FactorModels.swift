//
//  FactorModels.swift
//  Pythia — Factor Models (Phase 7.3) + Position Sizing (Phase 7.5)
//

import Foundation

// MARK: - Factor Exposure

struct FactorResponse: Codable {
    let portfolioId: String?
    let model: String
    let alpha: Double
    let alphaTStat: Double
    let alphaPValue: Double
    let rSquared: Double
    let adjRSquared: Double?
    let exposures: [FactorExposure]
    let periodDays: Int?
    let aiInterpretation: String?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case model, alpha
        case alphaTStat = "alpha_t_stat"
        case alphaPValue = "alpha_p_value"
        case rSquared = "r_squared"
        case adjRSquared = "adj_r_squared"
        case exposures
        case periodDays = "period_days"
        case aiInterpretation = "ai_interpretation"
        case success, message
    }
}

struct FactorExposure: Codable, Identifiable {
    var id: String { factorName }
    let factorName: String
    let beta: Double
    let tStat: Double
    let pValue: Double

    enum CodingKeys: String, CodingKey {
        case factorName = "factor_name"
        case beta
        case tStat = "t_stat"
        case pValue = "p_value"
    }
}

struct AssetFactorResponse: Codable {
    let assetId: String
    let symbol: String
    let model: String
    let alpha: Double
    let alphaTStat: Double
    let rSquared: Double
    let exposures: [FactorExposure]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol, model, alpha
        case alphaTStat = "alpha_t_stat"
        case rSquared = "r_squared"
        case exposures, success, message
    }
}

// MARK: - Position Sizing

struct PositionSizeResponse: Codable {
    let assetId: String
    let symbol: String
    let method: String
    let positionSizePct: Double
    let positionSizeValue: Double
    let portfolioValue: Double
    let riskPerTrade: Double
    let details: [String: AnyCodable]?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol, method
        case positionSizePct = "position_size_pct"
        case positionSizeValue = "position_size_value"
        case portfolioValue = "portfolio_value"
        case riskPerTrade = "risk_per_trade"
        case details, success, message
    }
}
