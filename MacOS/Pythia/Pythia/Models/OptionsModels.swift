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
