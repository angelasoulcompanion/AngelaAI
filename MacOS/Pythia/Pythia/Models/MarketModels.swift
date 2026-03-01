//
//  MarketModels.swift
//  Pythia
//

import Foundation

struct StockQuote: Codable {
    let symbol: String
    let name: String?
    let currentPrice: Double?
    let previousClose: Double?
    let openPrice: Double?
    let dayHigh: Double?
    let dayLow: Double?
    let volume: Int?
    let marketCap: Double?
    let peRatio: Double?
    let forwardPe: Double?
    let dividendYield: Double?
    let fiftyTwoWeekHigh: Double?
    let fiftyTwoWeekLow: Double?
    let avgVolume: Int?
    let beta: Double?
    let exchange: String?
    let currency: String?
    let change: Double?
    let changePercent: Double?

    enum CodingKeys: String, CodingKey {
        case symbol, name
        case currentPrice = "current_price"
        case previousClose = "previous_close"
        case openPrice = "open_price"
        case dayHigh = "day_high"
        case dayLow = "day_low"
        case volume
        case marketCap = "market_cap"
        case peRatio = "pe_ratio"
        case forwardPe = "forward_pe"
        case dividendYield = "dividend_yield"
        case fiftyTwoWeekHigh = "fifty_two_week_high"
        case fiftyTwoWeekLow = "fifty_two_week_low"
        case avgVolume = "avg_volume"
        case beta, exchange, currency, change
        case changePercent = "change_percent"
    }
}

struct HistoryResponse: Codable {
    let symbol: String
    let period: String
    let interval: String
    let data: [HistoryBar]
}

struct HistoryBar: Codable, Identifiable {
    let date: String
    let open: Double
    let high: Double
    let low: Double
    let close: Double
    let volume: Int

    var id: String { date }
}

struct FetchPricesResponse: Codable {
    let symbol: String
    let recordsFetched: Int
    let recordsInserted: Int

    enum CodingKeys: String, CodingKey {
        case symbol
        case recordsFetched = "records_fetched"
        case recordsInserted = "records_inserted"
    }
}

struct Watchlist: Codable, Identifiable {
    let watchlistId: String
    let name: String
    let description: String?
    let itemCount: Int?
    let createdAt: Date?

    var id: String { watchlistId }

    enum CodingKeys: String, CodingKey {
        case watchlistId = "watchlist_id"
        case name, description
        case itemCount = "item_count"
        case createdAt = "created_at"
    }
}

struct WatchlistDetail: Codable {
    let watchlistId: String
    let name: String
    let description: String?
    let items: [WatchlistItem]

    enum CodingKeys: String, CodingKey {
        case watchlistId = "watchlist_id"
        case name, description, items
    }
}

struct WatchlistItem: Codable, Identifiable {
    let itemId: String
    let assetId: String
    let symbol: String
    let assetName: String?
    let assetType: String?
    let sector: String?
    let notes: String?
    let addedAt: Date?

    var id: String { itemId }

    enum CodingKeys: String, CodingKey {
        case itemId = "item_id"
        case assetId = "asset_id"
        case symbol
        case assetName = "asset_name"
        case assetType = "asset_type"
        case sector, notes
        case addedAt = "added_at"
    }
}
