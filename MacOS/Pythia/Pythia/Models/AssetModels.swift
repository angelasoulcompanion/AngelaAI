//
//  AssetModels.swift
//  Pythia
//

import Foundation

struct Asset: Codable, Identifiable {
    let assetId: String
    let symbol: String
    let name: String
    let assetType: String
    let exchange: String?
    let currency: String?
    let sector: String?
    let industry: String?
    let country: String?
    let isActive: Bool?
    let createdAt: Date?

    var id: String { assetId }

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol, name
        case assetType = "asset_type"
        case exchange, currency, sector, industry, country
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

struct AssetCreateResponse: Codable {
    let assetId: String
    let symbol: String
    let name: String
    let assetType: String?
    let createdAt: Date?
    let status: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol, name
        case assetType = "asset_type"
        case createdAt = "created_at"
        case status
    }
}

struct HistoricalPrice: Codable, Identifiable {
    let priceId: String
    let date: Date
    let openPrice: Double?
    let highPrice: Double?
    let lowPrice: Double?
    let closePrice: Double
    let adjClose: Double?
    let volume: Int?

    var id: String { priceId }

    enum CodingKeys: String, CodingKey {
        case priceId = "price_id"
        case date
        case openPrice = "open_price"
        case highPrice = "high_price"
        case lowPrice = "low_price"
        case closePrice = "close_price"
        case adjClose = "adj_close"
        case volume
    }
}
