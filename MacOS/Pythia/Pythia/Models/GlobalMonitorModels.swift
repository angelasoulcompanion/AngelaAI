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

    enum CodingKeys: String, CodingKey {
        case success
        case fetchedAt = "fetched_at"
        case utcTime = "utc_time"
        case summary
        case pulseBar = "pulse_bar"
        case regions, heatmap, timeline
        case globalIndicators = "global_indicators"
    }
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

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, name, region, country, flag, exchange
        case isOpen = "is_open"
        case currentPrice = "current_price"
        case previousClose = "previous_close"
        case change
        case changePercent = "change_percent"
        case sparkline
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
