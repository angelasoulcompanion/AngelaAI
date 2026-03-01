//
//  DashboardModels.swift
//  Pythia
//

import Foundation

struct DashboardSummary: Codable {
    let portfolioCount: Int
    let totalPortfolioValue: Double
    let assetCount: Int
    let holdingCount: Int
    let recentTransactions: Int
    let priceDataPoints: Int
    let watchlistCount: Int

    enum CodingKeys: String, CodingKey {
        case portfolioCount = "portfolio_count"
        case totalPortfolioValue = "total_portfolio_value"
        case assetCount = "asset_count"
        case holdingCount = "holding_count"
        case recentTransactions = "recent_transactions"
        case priceDataPoints = "price_data_points"
        case watchlistCount = "watchlist_count"
    }
}

struct AssetTypeBreakdown: Codable, Identifiable {
    let assetType: String
    let count: Int
    let totalValue: Double
    let totalWeight: Double

    var id: String { assetType }

    enum CodingKeys: String, CodingKey {
        case assetType = "asset_type"
        case count
        case totalValue = "total_value"
        case totalWeight = "total_weight"
    }
}

struct AppSetting: Codable, Identifiable {
    let settingId: String
    let settingKey: String
    let settingValue: String?
    let valueType: String?
    let description: String?
    let category: String?

    var id: String { settingId }

    enum CodingKeys: String, CodingKey {
        case settingId = "setting_id"
        case settingKey = "setting_key"
        case settingValue = "setting_value"
        case valueType = "value_type"
        case description, category
    }
}
