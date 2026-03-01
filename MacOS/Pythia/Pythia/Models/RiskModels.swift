//
//  RiskModels.swift
//  Pythia — Risk management models (Phase 2)
//

import Foundation

// MARK: - VaR

struct VaRResponse: Codable {
    let portfolioId: String?
    let method: String
    let confidenceLevel: Double
    let holdingPeriod: Int
    let portfolioValue: Double
    let varValue: Double
    let varPercent: Double
    let cvarValue: Double
    let cvarPercent: Double
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case method
        case confidenceLevel = "confidence_level"
        case holdingPeriod = "holding_period"
        case portfolioValue = "portfolio_value"
        case varValue = "var_value"
        case varPercent = "var_percent"
        case cvarValue = "cvar_value"
        case cvarPercent = "cvar_percent"
        case success, message
    }
}

struct ComponentVaRResponse: Codable {
    let portfolioVarPct: Double?
    let components: [ComponentVaR]?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case portfolioVarPct = "portfolio_var_pct"
        case components, error
    }
}

struct ComponentVaR: Codable, Identifiable {
    let symbol: String
    let weight: Double
    let marginalVar: Double
    let componentVar: Double
    let pctContribution: Double

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, weight
        case marginalVar = "marginal_var"
        case componentVar = "component_var"
        case pctContribution = "pct_contribution"
    }
}

// MARK: - Stress Test

struct StressScenario: Codable, Identifiable {
    let key: String
    let name: String
    let description: String
    let defaultShock: Double

    var id: String { key }

    enum CodingKeys: String, CodingKey {
        case key, name, description
        case defaultShock = "default_shock"
    }
}

struct StressScenarioListResponse: Codable {
    let scenarios: [StressScenario]
}

struct StressTestResponse: Codable {
    let scenarioName: String
    let description: String
    let portfolioValueBefore: Double
    let portfolioValueAfter: Double
    let portfolioPnl: Double
    let portfolioPnlPct: Double
    let assetImpacts: [AssetImpact]
    let worstAsset: AssetImpact?
    let bestAsset: AssetImpact?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case scenarioName = "scenario_name"
        case description
        case portfolioValueBefore = "portfolio_value_before"
        case portfolioValueAfter = "portfolio_value_after"
        case portfolioPnl = "portfolio_pnl"
        case portfolioPnlPct = "portfolio_pnl_pct"
        case assetImpacts = "asset_impacts"
        case worstAsset = "worst_asset"
        case bestAsset = "best_asset"
        case success, message
    }
}

struct AssetImpact: Codable, Identifiable {
    let symbol: String
    let name: String?
    let sector: String?
    let marketValue: Double
    let shockPct: Double
    let pnl: Double
    let valueAfter: Double

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, name, sector
        case marketValue = "market_value"
        case shockPct = "shock_pct"
        case pnl
        case valueAfter = "value_after"
    }
}

struct StressTestAllResponse: Codable {
    let portfolioId: String?
    let scenarios: [StressTestSummary]

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case scenarios
    }
}

struct StressTestSummary: Codable, Identifiable {
    let scenarioName: String
    let portfolioPnl: Double
    let portfolioPnlPct: Double
    let worstAsset: AssetImpact?

    var id: String { scenarioName }

    enum CodingKeys: String, CodingKey {
        case scenarioName = "scenario_name"
        case portfolioPnl = "portfolio_pnl"
        case portfolioPnlPct = "portfolio_pnl_pct"
        case worstAsset = "worst_asset"
    }
}

// MARK: - Performance Metrics

struct PerformanceMetricsResponse: Codable {
    let portfolioId: String?
    let success: Bool
    let message: String?
    let returns: ReturnMetrics?
    let risk: RiskMetricsData?
    let ratios: RatioMetrics?
    let distribution: DistributionMetrics?
    let market: MarketMetrics?
    let meta: MetaMeta?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case success, message, returns, risk, ratios, distribution, market, meta
    }
}

struct ReturnMetrics: Codable {
    let totalReturn: Double
    let annualizedReturn: Double

    enum CodingKeys: String, CodingKey {
        case totalReturn = "total_return"
        case annualizedReturn = "annualized_return"
    }
}

struct RiskMetricsData: Codable {
    let volatility: Double
    let downsideDeviation: Double
    let maxDrawdown: Double
    let maxDrawdownDuration: Int
    let var95: Double
    let var99: Double
    let cvar95: Double

    enum CodingKeys: String, CodingKey {
        case volatility
        case downsideDeviation = "downside_deviation"
        case maxDrawdown = "max_drawdown"
        case maxDrawdownDuration = "max_drawdown_duration"
        case var95 = "var_95"
        case var99 = "var_99"
        case cvar95 = "cvar_95"
    }
}

struct RatioMetrics: Codable {
    let sharpeRatio: Double
    let sortinoRatio: Double
    let calmarRatio: Double
    let treynorRatio: Double
    let informationRatio: Double

    enum CodingKeys: String, CodingKey {
        case sharpeRatio = "sharpe_ratio"
        case sortinoRatio = "sortino_ratio"
        case calmarRatio = "calmar_ratio"
        case treynorRatio = "treynor_ratio"
        case informationRatio = "information_ratio"
    }
}

struct DistributionMetrics: Codable {
    let skewness: Double
    let excessKurtosis: Double

    enum CodingKeys: String, CodingKey {
        case skewness
        case excessKurtosis = "excess_kurtosis"
    }
}

struct MarketMetrics: Codable {
    let beta: Double
    let alpha: Double
    let rSquared: Double
    let trackingError: Double

    enum CodingKeys: String, CodingKey {
        case beta, alpha
        case rSquared = "r_squared"
        case trackingError = "tracking_error"
    }
}

struct MetaMeta: Codable {
    let nObservations: Int
    let periodDays: Int

    enum CodingKeys: String, CodingKey {
        case nObservations = "n_observations"
        case periodDays = "period_days"
    }
}

// MARK: - Drawdown

struct DrawdownResponse: Codable {
    let maxDrawdown: Double?
    let currentDrawdown: Double?
    let topDrawdowns: [DrawdownPeriod]?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case maxDrawdown = "max_drawdown"
        case currentDrawdown = "current_drawdown"
        case topDrawdowns = "top_drawdowns"
        case error
    }
}

struct DrawdownPeriod: Codable, Identifiable {
    let startDate: String
    let endDate: String
    let troughDate: String
    let drawdown: Double
    let durationDays: Int

    var id: String { "\(startDate)-\(endDate)" }

    enum CodingKeys: String, CodingKey {
        case startDate = "start_date"
        case endDate = "end_date"
        case troughDate = "trough_date"
        case drawdown
        case durationDays = "duration_days"
    }
}

// MARK: - Rolling Metrics

struct RollingMetricsResponse: Codable {
    let window: Int?
    let dates: [String]?
    let rollingVolatility: [Double]?
    let rollingSharpe: [Double]?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case window, dates
        case rollingVolatility = "rolling_volatility"
        case rollingSharpe = "rolling_sharpe"
        case error
    }
}
