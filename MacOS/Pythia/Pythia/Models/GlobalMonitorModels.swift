//
//  GlobalMonitorModels.swift
//  Pythia
//

import Foundation

struct GlobalMonitorResponse: Codable {
    let success: Bool
    let fetchedAt: String
    let utcTime: String
    let summary: GlobalSummary
    let pulseBar: [PulseBarItem]
    let regions: [String: RegionData]
    let heatmap: [HeatmapItem]
    let timeline: [TimelineExchange]
    let globalIndicators: [IndexData]
    let headlines: [HeadlineItem]?
    // New sections
    let crossAsset: [CrossAssetItem]?
    let fxPairs: [FXPairItem]?
    let yieldCurve: YieldCurveData?
    let riskRegime: RiskRegimeData?
    let performanceRanking: [PerformanceRankItem]?
    let economicCalendar: [EconomicEvent]?

    enum CodingKeys: String, CodingKey {
        case success
        case fetchedAt = "fetched_at"
        case utcTime = "utc_time"
        case summary
        case pulseBar = "pulse_bar"
        case regions, heatmap, timeline
        case globalIndicators = "global_indicators"
        case headlines
        case crossAsset = "cross_asset"
        case fxPairs = "fx_pairs"
        case yieldCurve = "yield_curve"
        case riskRegime = "risk_regime"
        case performanceRanking = "performance_ranking"
        case economicCalendar = "economic_calendar"
    }
}

struct HeadlineItem: Codable, Identifiable {
    let title: String
    let source: String
    let published: String
    let url: String

    var id: String { title }
}

struct GlobalSummary: Codable {
    let marketsOpen: Int
    let marketsTotal: Int
    let vix: Double?
    let vixChange: Double?
    let dxy: Double?
    let dxyChange: Double?
    let sentiment: String
    let sentimentDetail: String

    enum CodingKeys: String, CodingKey {
        case marketsOpen = "markets_open"
        case marketsTotal = "markets_total"
        case vix
        case vixChange = "vix_change"
        case dxy
        case dxyChange = "dxy_change"
        case sentiment
        case sentimentDetail = "sentiment_detail"
    }
}

struct PulseBarItem: Codable, Identifiable {
    let exchange: String
    let isOpen: Bool
    var id: String { exchange }

    enum CodingKeys: String, CodingKey {
        case exchange
        case isOpen = "is_open"
    }
}

struct RegionData: Codable {
    let isOpen: Bool
    let openCount: Int
    let indices: [IndexData]

    enum CodingKeys: String, CodingKey {
        case isOpen = "is_open"
        case openCount = "open_count"
        case indices
    }
}

struct FuturesHint: Codable {
    let name: String
    let price: Double?
    let changePercent: Double?

    enum CodingKeys: String, CodingKey {
        case name, price
        case changePercent = "change_percent"
    }
}

struct IndexData: Codable, Identifiable {
    let symbol: String
    let name: String
    let region: String
    let country: String
    let flag: String
    let exchange: String
    let isOpen: Bool
    let currentPrice: Double?
    let previousClose: Double?
    let change: Double?
    let changePercent: Double?
    let sparkline: [Double]
    let futuresHint: FuturesHint?

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, name, region, country, flag, exchange
        case isOpen = "is_open"
        case currentPrice = "current_price"
        case previousClose = "previous_close"
        case change
        case changePercent = "change_percent"
        case sparkline
        case futuresHint = "futures_hint"
    }
}

struct HeatmapItem: Codable, Identifiable {
    let symbol: String
    let name: String
    let changePercent: Double?
    let flag: String

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, name
        case changePercent = "change_percent"
        case flag
    }
}

struct TimelineExchange: Codable, Identifiable {
    let name: String
    let utcOpen: Double
    let utcClose: Double

    var id: String { name }

    enum CodingKeys: String, CodingKey {
        case name
        case utcOpen = "utc_open"
        case utcClose = "utc_close"
    }
}

// MARK: - Cross-Asset

struct CrossAssetItem: Codable, Identifiable {
    let name: String
    let unit: String
    let price: Double?
    let changePercent: Double?

    var id: String { name }

    enum CodingKeys: String, CodingKey {
        case name, unit, price
        case changePercent = "change_percent"
    }
}

// MARK: - FX Pairs

struct FXPairItem: Codable, Identifiable {
    let name: String
    let rate: Double?
    let changePercent: Double?

    var id: String { name }

    enum CodingKeys: String, CodingKey {
        case name, rate
        case changePercent = "change_percent"
    }
}

// MARK: - Yield Curve

struct YieldCurveData: Codable {
    let t3m: Double?
    let t5y: Double?
    let t10y: Double?
    let t30y: Double?
    let spread10y3m: Double?
    let status: String

    enum CodingKeys: String, CodingKey {
        case t3m = "t_3m"
        case t5y = "t_5y"
        case t10y = "t_10y"
        case t30y = "t_30y"
        case spread10y3m = "spread_10y_3m"
        case status
    }
}

// MARK: - Risk Regime

struct RiskRegimeData: Codable {
    let regime: String
    let score: Int
    let vix: Double?
    let vix3m: Double?
    let vixTermStructure: String?
    let hygChange: Double?
    let creditRatio: Double?

    enum CodingKeys: String, CodingKey {
        case regime, score, vix
        case vix3m = "vix_3m"
        case vixTermStructure = "vix_term_structure"
        case hygChange = "hyg_change"
        case creditRatio = "credit_ratio"
    }
}

// MARK: - Performance Ranking

struct PerformanceRankItem: Codable, Identifiable {
    let name: String
    let flag: String
    let changePercent: Double?

    var id: String { name }

    enum CodingKeys: String, CodingKey {
        case name, flag
        case changePercent = "change_percent"
    }
}

// MARK: - Economic Calendar

struct EconomicEvent: Codable, Identifiable {
    let event: String
    let country: String
    let flag: String
    let datetime: String
    let impact: String
    let countdown: String

    var id: String { "\(event)_\(datetime)" }
}
