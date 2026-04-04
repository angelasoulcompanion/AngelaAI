//
//  StrategyModels.swift
//  Pythia — Strategy Builder models (Phase 7.6 + 7.7 + Strategy Builder)
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

// MARK: - Strategy Builder — Rule Types

enum EntryRuleType: String, CaseIterable, Identifiable {
    case sma_cross, rsi_threshold, momentum, breakout, volume_spike

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .sma_cross: return "SMA Crossover"
        case .rsi_threshold: return "RSI Threshold"
        case .momentum: return "Momentum"
        case .breakout: return "Breakout"
        case .volume_spike: return "Volume Spike"
        }
    }

    var icon: String {
        switch self {
        case .sma_cross: return "arrow.up.arrow.down"
        case .rsi_threshold: return "gauge.with.needle"
        case .momentum: return "bolt.fill"
        case .breakout: return "arrow.up.right"
        case .volume_spike: return "chart.bar.fill"
        }
    }

    var param1Label: String {
        switch self {
        case .sma_cross: return "Fast Period"
        case .rsi_threshold: return "RSI Period"
        case .momentum: return "Lookback"
        case .breakout: return "Lookback"
        case .volume_spike: return "Lookback"
        }
    }

    var param2Label: String? {
        switch self {
        case .sma_cross: return "Slow Period"
        case .rsi_threshold: return "Threshold"
        case .momentum: return "Threshold"
        case .breakout: return nil
        case .volume_spike: return "Vol Ratio"
        }
    }

    var defaultParam1: Double {
        switch self {
        case .sma_cross: return 20
        case .rsi_threshold: return 14
        case .momentum: return 20
        case .breakout: return 20
        case .volume_spike: return 20
        }
    }

    var defaultParam2: Double {
        switch self {
        case .sma_cross: return 50
        case .rsi_threshold: return 30
        case .momentum: return 0
        case .breakout: return 0
        case .volume_spike: return 2.0
        }
    }

    var description: String {
        switch self {
        case .sma_cross: return "Buy when fast SMA crosses above slow SMA"
        case .rsi_threshold: return "Buy when RSI drops below threshold (oversold)"
        case .momentum: return "Buy on positive momentum over lookback period"
        case .breakout: return "Buy on N-day high breakout"
        case .volume_spike: return "Confirm entry with volume spike ratio"
        }
    }
}

enum ExitRuleType: String, CaseIterable, Identifiable {
    case take_profit, stop_loss, trailing_stop, time_exit

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .take_profit: return "Take Profit"
        case .stop_loss: return "Stop Loss"
        case .trailing_stop: return "Trailing Stop"
        case .time_exit: return "Time Exit"
        }
    }

    var icon: String {
        switch self {
        case .take_profit: return "target"
        case .stop_loss: return "shield.fill"
        case .trailing_stop: return "arrow.uturn.down"
        case .time_exit: return "clock.fill"
        }
    }

    var valueLabel: String {
        switch self {
        case .take_profit: return "Profit %"
        case .stop_loss: return "Loss %"
        case .trailing_stop: return "Trail %"
        case .time_exit: return "Max Days"
        }
    }

    var defaultValue: Double {
        switch self {
        case .take_profit: return 0.15
        case .stop_loss: return 0.08
        case .trailing_stop: return 0.10
        case .time_exit: return 20
        }
    }

    var isPercentage: Bool {
        self != .time_exit
    }

    var description: String {
        switch self {
        case .take_profit: return "Exit at fixed profit target"
        case .stop_loss: return "Exit at fixed loss limit"
        case .trailing_stop: return "Trail stop below peak equity"
        case .time_exit: return "Exit after N holding days"
        }
    }
}

// MARK: - Strategy Builder — Rule Configs (for @State)

struct EntryRuleConfig: Identifiable {
    let id = UUID()
    var type: EntryRuleType
    var param1: Double
    var param2: Double

    init(type: EntryRuleType, param1: Double? = nil, param2: Double? = nil) {
        self.type = type
        self.param1 = param1 ?? type.defaultParam1
        self.param2 = param2 ?? type.defaultParam2
    }

    func toPayload() -> EntryRulePayload {
        switch type {
        case .sma_cross:
            return EntryRulePayload(type: type.rawValue, fastPeriod: Int(param1), slowPeriod: Int(param2), period: nil, threshold: nil, lookback: nil)
        case .rsi_threshold:
            return EntryRulePayload(type: type.rawValue, fastPeriod: nil, slowPeriod: nil, period: Int(param1), threshold: param2, lookback: nil)
        case .momentum:
            return EntryRulePayload(type: type.rawValue, fastPeriod: nil, slowPeriod: nil, period: nil, threshold: param2, lookback: Int(param1))
        case .breakout:
            return EntryRulePayload(type: type.rawValue, fastPeriod: nil, slowPeriod: nil, period: nil, threshold: nil, lookback: Int(param1))
        case .volume_spike:
            return EntryRulePayload(type: type.rawValue, fastPeriod: nil, slowPeriod: nil, period: nil, threshold: param2, lookback: Int(param1))
        }
    }

    static func fromPayload(_ p: EntryRulePayload) -> EntryRuleConfig {
        let t = EntryRuleType(rawValue: p.type) ?? .sma_cross
        switch t {
        case .sma_cross:
            return EntryRuleConfig(type: t, param1: Double(p.fastPeriod ?? 20), param2: Double(p.slowPeriod ?? 50))
        case .rsi_threshold:
            return EntryRuleConfig(type: t, param1: Double(p.period ?? 14), param2: p.threshold ?? 30)
        case .momentum:
            return EntryRuleConfig(type: t, param1: Double(p.lookback ?? 20), param2: p.threshold ?? 0)
        case .breakout:
            return EntryRuleConfig(type: t, param1: Double(p.lookback ?? 20))
        case .volume_spike:
            return EntryRuleConfig(type: t, param1: Double(p.lookback ?? 20), param2: p.threshold ?? 2.0)
        }
    }
}

struct ExitRuleConfig: Identifiable {
    let id = UUID()
    var type: ExitRuleType
    var value: Double

    init(type: ExitRuleType, value: Double? = nil) {
        self.type = type
        self.value = value ?? type.defaultValue
    }

    func toPayload() -> ExitRulePayload {
        switch type {
        case .time_exit:
            return ExitRulePayload(type: type.rawValue, value: nil, maxDays: Int(value))
        default:
            return ExitRulePayload(type: type.rawValue, value: value, maxDays: nil)
        }
    }

    static func fromPayload(_ p: ExitRulePayload) -> ExitRuleConfig {
        let t = ExitRuleType(rawValue: p.type) ?? .stop_loss
        switch t {
        case .time_exit:
            return ExitRuleConfig(type: t, value: Double(p.maxDays ?? 20))
        default:
            return ExitRuleConfig(type: t, value: p.value ?? t.defaultValue)
        }
    }
}

// MARK: - API Payloads

struct EntryRulePayload: Codable {
    let type: String
    let fastPeriod: Int?
    let slowPeriod: Int?
    let period: Int?
    let threshold: Double?
    let lookback: Int?

    enum CodingKeys: String, CodingKey {
        case type
        case fastPeriod = "fast_period"
        case slowPeriod = "slow_period"
        case period, threshold, lookback
    }
}

struct ExitRulePayload: Codable {
    let type: String
    let value: Double?
    let maxDays: Int?

    enum CodingKeys: String, CodingKey {
        case type, value
        case maxDays = "max_days"
    }
}

struct PositionSizingPayload: Codable {
    let method: String?
    let value: Double?
}

struct StrategyConfigPayload: Codable {
    let entryRules: [EntryRulePayload]?
    let exitRules: [ExitRulePayload]?
    let positionSizing: PositionSizingPayload?
    let transactionCostBps: Int?

    enum CodingKeys: String, CodingKey {
        case entryRules = "entry_rules"
        case exitRules = "exit_rules"
        case positionSizing = "position_sizing"
        case transactionCostBps = "transaction_cost_bps"
    }
}

struct StrategyCreateBody: Encodable {
    let name: String
    let strategyType: String
    let description: String
    let entryRules: [EntryRulePayload]
    let exitRules: [ExitRulePayload]
    let positionSizing: PositionSizingPayload
    let transactionCostBps: Int

    enum CodingKeys: String, CodingKey {
        case name
        case strategyType = "strategy_type"
        case description
        case entryRules = "entry_rules"
        case exitRules = "exit_rules"
        case positionSizing = "position_sizing"
        case transactionCostBps = "transaction_cost_bps"
    }
}

struct StrategyDetailResponse: Codable {
    let strategyId: String
    let name: String
    let description: String?
    let strategyType: String
    let config: StrategyConfigPayload
    let isActive: Bool?

    enum CodingKeys: String, CodingKey {
        case strategyId = "strategy_id"
        case name, description
        case strategyType = "strategy_type"
        case config
        case isActive = "is_active"
    }
}

struct StrategyEvalBody: Encodable {
    let assetId: String
    let initialCapital: Double?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case initialCapital = "initial_capital"
    }
}
