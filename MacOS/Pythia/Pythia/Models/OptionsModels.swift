//
//  OptionsModels.swift
//  Pythia — Options pricing models (Phase 3)
//

import Foundation

struct OptionPriceResponse: Codable {
    let optionType: String
    let spot: Double
    let strike: Double
    let timeToExpiry: Double
    let price: Double
    let intrinsicValue: Double
    let timeValue: Double
    let greeks: OptionGreeks

    enum CodingKeys: String, CodingKey {
        case optionType = "option_type"
        case spot, strike
        case timeToExpiry = "time_to_expiry"
        case price
        case intrinsicValue = "intrinsic_value"
        case timeValue = "time_value"
        case greeks
    }
}

struct OptionGreeks: Codable {
    let delta: Double
    let gamma: Double
    let theta: Double
    let vega: Double
    let rho: Double
}

struct ImpliedVolResponse: Codable {
    let impliedVolatility: Double?
    let marketPrice: Double
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case impliedVolatility = "implied_volatility"
        case marketPrice = "market_price"
        case success, message
    }
}

// MARK: - Option Analysis (Asset Picker + AI Suggestion)

struct OptionAnalysisResponse: Codable {
    let success: Bool
    let symbol: String
    let spot: Double
    let historicalVol: Double
    let quote: AnalysisQuote
    let strike: Double
    let timeToExpiry: Double
    let riskFreeRate: Double
    let call: OptionSide
    let put: OptionSide
    let suggestion: OptionSuggestion
    let bsModel: BSModel?

    enum CodingKeys: String, CodingKey {
        case success, symbol, spot
        case historicalVol = "historical_vol"
        case quote, strike
        case timeToExpiry = "time_to_expiry"
        case riskFreeRate = "risk_free_rate"
        case call, put, suggestion
        case bsModel = "bs_model"
    }
}

struct BSModel: Codable {
    let d1: Double
    let d2: Double
    let nD1: Double
    let nD2: Double
    let nNegD1: Double
    let nNegD2: Double
    let discountFactor: Double
    let forwardPrice: Double

    enum CodingKeys: String, CodingKey {
        case d1, d2
        case nD1 = "n_d1"
        case nD2 = "n_d2"
        case nNegD1 = "n_neg_d1"
        case nNegD2 = "n_neg_d2"
        case discountFactor = "discount_factor"
        case forwardPrice = "forward_price"
    }
}

struct AnalysisQuote: Codable {
    let currentPrice: Double
    let changePercent: Double
    let name: String

    enum CodingKeys: String, CodingKey {
        case currentPrice = "current_price"
        case changePercent = "change_percent"
        case name
    }
}

struct OptionSide: Codable {
    let price: Double
    let intrinsicValue: Double
    let timeValue: Double
    let greeks: OptionGreeks

    enum CodingKeys: String, CodingKey {
        case price
        case intrinsicValue = "intrinsic_value"
        case timeValue = "time_value"
        case greeks
    }
}

struct OptionSuggestion: Codable {
    let direction: String       // "call", "put", "neutral"
    let confidence: String      // "high", "medium", "low"
    let score: Int
    let signals: [TechSignal]
    let summary: String
    let contract: RecommendedContract?
}

struct RecommendedContract: Codable {
    let type: String            // "call", "put", "straddle"
    let strike: Double
    let expiryYears: Double
    let premium: Double
    let breakeven: Double
    let profitTarget: Double
    let maxLoss: Double
    let riskReward: Double

    enum CodingKeys: String, CodingKey {
        case type, strike
        case expiryYears = "expiry_years"
        case premium, breakeven
        case profitTarget = "profit_target"
        case maxLoss = "max_loss"
        case riskReward = "risk_reward"
    }
}

struct TechSignal: Codable, Identifiable {
    let name: String
    let value: AnyCodableValue
    let detail: String
    let signal: String          // "bullish", "bearish", "neutral"

    var id: String { name }
}

/// Handles mixed JSON types (String or Number) for signal values
enum AnyCodableValue: Codable {
    case string(String)
    case double(Double)

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let d = try? container.decode(Double.self) {
            self = .double(d)
        } else if let s = try? container.decode(String.self) {
            self = .string(s)
        } else {
            self = .string("")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let s): try container.encode(s)
        case .double(let d): try container.encode(d)
        }
    }

    var displayString: String {
        switch self {
        case .string(let s): return s
        case .double(let d): return String(format: "%.1f", d)
        }
    }
}

// MARK: - Backtest

struct BacktestResponse: Codable {
    let strategyName: String
    let symbol: String
    let startDate: String
    let endDate: String
    let initialCapital: Double
    let finalValue: Double
    let totalReturn: Double
    let annualizedReturn: Double
    let maxDrawdown: Double
    let sharpeRatio: Double
    let nTrades: Int
    let winRate: Double
    let benchmarkReturn: Double
    let excessReturn: Double
    let equityCurve: [EquityPoint]
    let trades: [TradeRecord]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case strategyName = "strategy_name"
        case symbol
        case startDate = "start_date"
        case endDate = "end_date"
        case initialCapital = "initial_capital"
        case finalValue = "final_value"
        case totalReturn = "total_return"
        case annualizedReturn = "annualized_return"
        case maxDrawdown = "max_drawdown"
        case sharpeRatio = "sharpe_ratio"
        case nTrades = "n_trades"
        case winRate = "win_rate"
        case benchmarkReturn = "benchmark_return"
        case excessReturn = "excess_return"
        case equityCurve = "equity_curve"
        case trades
        case success, message
    }
}

struct EquityPoint: Codable, Identifiable {
    let date: String
    let value: Double

    var id: String { date }
}

struct TradeRecord: Codable, Identifiable {
    let date: String
    let type: String
    let price: Double
    let shares: Int
    let pnl: Double?

    var id: String { "\(date)-\(type)" }
}

// MARK: - Monte Carlo

struct MonteCarloResponse: Codable {
    let symbol: String
    let currentPrice: Double
    let nSimulations: Int
    let timeSteps: Int
    let statistics: MCStatistics
    let parameters: MCParameters
    let samplePaths: [[Double]]
    let percentileBands: [MCBand]
    let finalDistribution: [Double]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case symbol
        case currentPrice = "current_price"
        case nSimulations = "n_simulations"
        case timeSteps = "time_steps"
        case statistics, parameters
        case samplePaths = "sample_paths"
        case percentileBands = "percentile_bands"
        case finalDistribution = "final_distribution"
        case success, message
    }
}

struct MCStatistics: Codable {
    let meanFinalPrice: Double
    let medianFinalPrice: Double
    let stdFinalPrice: Double
    let percentile5: Double
    let percentile25: Double
    let percentile75: Double
    let percentile95: Double
    let probAboveCurrent: Double

    enum CodingKeys: String, CodingKey {
        case meanFinalPrice = "mean_final_price"
        case medianFinalPrice = "median_final_price"
        case stdFinalPrice = "std_final_price"
        case percentile5 = "percentile_5"
        case percentile25 = "percentile_25"
        case percentile75 = "percentile_75"
        case percentile95 = "percentile_95"
        case probAboveCurrent = "prob_above_current"
    }
}

struct MCParameters: Codable {
    let expectedReturn: Double
    let volatility: Double

    enum CodingKeys: String, CodingKey {
        case expectedReturn = "expected_return"
        case volatility
    }
}

struct MCBand: Codable, Identifiable {
    let step: Int
    let p5: Double
    let p25: Double
    let p50: Double
    let p75: Double
    let p95: Double

    var id: Int { step }
}

// MARK: - Statistics

struct StatisticsResponse: Codable {
    let symbol: String
    let nObservations: Int
    let descriptive: DescriptiveStats
    let percentiles: Percentiles
    let tests: [StatTest]
    let histogram: [HistBin]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case symbol
        case nObservations = "n_observations"
        case descriptive, percentiles, tests, histogram
        case success, message
    }
}

struct DescriptiveStats: Codable {
    let mean: Double
    let std: Double
    let median: Double
    let skewness: Double
    let kurtosis: Double
    let min: Double
    let max: Double
}

struct Percentiles: Codable {
    let p1: Double
    let p5: Double
    let p95: Double
    let p99: Double
}

struct StatTest: Codable, Identifiable {
    let testName: String
    let statistic: Double
    let pValue: Double
    let conclusion: String
    let significant: Bool

    var id: String { testName }

    enum CodingKeys: String, CodingKey {
        case testName = "test_name"
        case statistic
        case pValue = "p_value"
        case conclusion, significant
    }
}

struct HistBin: Codable, Identifiable {
    let binStart: Double
    let binEnd: Double
    let count: Int

    var id: Double { binStart }

    enum CodingKeys: String, CodingKey {
        case binStart = "bin_start"
        case binEnd = "bin_end"
        case count
    }
}
