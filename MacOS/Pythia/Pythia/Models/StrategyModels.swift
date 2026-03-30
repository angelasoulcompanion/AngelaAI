//
//  StrategyModels.swift
//  Pythia — Strategy Builder models (Phase 7.6 + 7.7)
//

import Foundation

// MARK: - Strategy CRUD

struct StrategyListResponse: Codable {
    let strategies: [StrategyItem]
    let count: Int
}

struct StrategyItem: Codable, Identifiable {
    var id: String { strategyId }
    let strategyId: String
    let name: String
    let description: String?
    let strategyType: String
    let isActive: Bool?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case strategyId = "strategy_id"
        case name, description
        case strategyType = "strategy_type"
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

struct PresetListResponse: Codable {
    let presets: [PresetItem]
}

struct PresetItem: Codable, Identifiable {
    var id: String { key }
    let key: String
    let name: String
    let type: String
    let description: String
}

struct CreateStrategyResponse: Codable {
    let strategyId: String?
    let name: String?
    let success: Bool

    enum CodingKeys: String, CodingKey {
        case strategyId = "strategy_id"
        case name, success
    }
}

// MARK: - Strategy Evaluation

struct StrategyEvalResponse: Codable {
    let strategyId: String
    let strategyName: String
    let totalReturn: Double
    let annualizedReturn: Double
    let sharpeRatio: Double
    let maxDrawdown: Double
    let winRate: Double
    let profitFactor: Double
    let totalTrades: Int
    let avgHoldingDays: Double
    let trades: [StrategyTrade]
    let equityCurve: [StrategyEquityPoint]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case strategyId = "strategy_id"
        case strategyName = "strategy_name"
        case totalReturn = "total_return"
        case annualizedReturn = "annualized_return"
        case sharpeRatio = "sharpe_ratio"
        case maxDrawdown = "max_drawdown"
        case winRate = "win_rate"
        case profitFactor = "profit_factor"
        case totalTrades = "total_trades"
        case avgHoldingDays = "avg_holding_days"
        case trades
        case equityCurve = "equity_curve"
        case success, message
    }
}

struct StrategyTrade: Codable, Identifiable {
    var id: String { "\(entryDate)_\(exitDate)" }
    let entryDate: String
    let exitDate: String
    let direction: String
    let entryPrice: Double
    let exitPrice: Double
    let pnlPct: Double
    let pnlValue: Double
    let holdingDays: Int
    let exitReason: String

    enum CodingKeys: String, CodingKey {
        case entryDate = "entry_date"
        case exitDate = "exit_date"
        case direction
        case entryPrice = "entry_price"
        case exitPrice = "exit_price"
        case pnlPct = "pnl_pct"
        case pnlValue = "pnl_value"
        case holdingDays = "holding_days"
        case exitReason = "exit_reason"
    }
}

struct StrategyEquityPoint: Codable, Identifiable {
    var id: String { date }
    let date: String
    let equity: Double
}
