//
//  MPTModels.swift
//  Pythia — Modern Portfolio Theory models (Phase 2)
//

import Foundation

// MARK: - Optimization

struct OptimizationResponse: Codable {
    let portfolioId: String?
    let optimizationType: String
    let success: Bool
    let message: String?
    let weights: [String: Double]
    let expectedReturn: Double
    let volatility: Double
    let sharpeRatio: Double

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case optimizationType = "optimization_type"
        case success, message, weights
        case expectedReturn = "expected_return"
        case volatility
        case sharpeRatio = "sharpe_ratio"
    }
}

// MARK: - Efficient Frontier

struct EfficientFrontierResponse: Codable {
    let points: [FrontierPoint]
    let nAssets: Int?
    let riskFreeRate: Double?

    enum CodingKeys: String, CodingKey {
        case points
        case nAssets = "n_assets"
        case riskFreeRate = "risk_free_rate"
    }
}

struct FrontierPoint: Codable, Identifiable {
    let returnValue: Double
    let risk: Double
    let sharpeRatio: Double?
    let weights: [String: Double]?

    var id: Double { risk }

    enum CodingKeys: String, CodingKey {
        case returnValue = "return"
        case risk
        case sharpeRatio = "sharpe_ratio"
        case weights
    }
}

// MARK: - Correlation

struct CorrelationResponse: Codable {
    let symbols: [String]
    let correlationMatrix: [[Double]]
    let covarianceMatrix: [[Double]]
    let periodDays: Int?

    enum CodingKeys: String, CodingKey {
        case symbols
        case correlationMatrix = "correlation_matrix"
        case covarianceMatrix = "covariance_matrix"
        case periodDays = "period_days"
    }
}
