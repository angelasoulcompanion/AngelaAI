//
//  PortfolioModels.swift
//  Pythia
//

import Foundation

struct Portfolio: Codable, Identifiable, Hashable {
    static func == (lhs: Portfolio, rhs: Portfolio) -> Bool { lhs.portfolioId == rhs.portfolioId }
    func hash(into hasher: inout Hasher) { hasher.combine(portfolioId) }

    let portfolioId: String
    let name: String
    let description: String?
    let baseCurrency: String?
    let benchmarkSymbol: String?
    let riskFreeRate: Double?
    let initialCapital: Double?
    let inceptionDate: Date?
    let isActive: Bool?
    let createdAt: Date?
    let updatedAt: Date?
    let holdingCount: Int?
    let totalValue: Double?

    var id: String { portfolioId }

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case name, description
        case baseCurrency = "base_currency"
        case benchmarkSymbol = "benchmark_symbol"
        case riskFreeRate = "risk_free_rate"
        case initialCapital = "initial_capital"
        case inceptionDate = "inception_date"
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case holdingCount = "holding_count"
        case totalValue = "total_value"
    }
}

struct PortfolioDetail: Codable {
    let portfolioId: String
    let name: String
    let description: String?
    let baseCurrency: String?
    let benchmarkSymbol: String?
    let riskFreeRate: Double?
    let initialCapital: Double?
    let inceptionDate: Date?
    let holdings: [Holding]
    let totalValue: Double?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case name, description
        case baseCurrency = "base_currency"
        case benchmarkSymbol = "benchmark_symbol"
        case riskFreeRate = "risk_free_rate"
        case initialCapital = "initial_capital"
        case inceptionDate = "inception_date"
        case holdings
        case totalValue = "total_value"
    }
}

struct Holding: Codable, Identifiable {
    let holdingId: String
    let assetId: String
    let symbol: String
    let assetName: String?
    let assetType: String?
    let sector: String?
    let weight: Double
    let quantity: Double?
    let averageCost: Double?
    let marketValue: Double?
    let targetWeight: Double?
    let minWeight: Double?
    let maxWeight: Double?

    var id: String { holdingId }

    enum CodingKeys: String, CodingKey {
        case holdingId = "holding_id"
        case assetId = "asset_id"
        case symbol
        case assetName = "asset_name"
        case assetType = "asset_type"
        case sector, weight, quantity
        case averageCost = "average_cost"
        case marketValue = "market_value"
        case targetWeight = "target_weight"
        case minWeight = "min_weight"
        case maxWeight = "max_weight"
    }
}

struct Transaction: Codable, Identifiable {
    let transactionId: String
    let assetId: String
    let symbol: String
    let assetName: String?
    let transactionType: String
    let quantity: Double
    let price: Double
    let fees: Double?
    let taxes: Double?
    let totalAmount: Double
    let transactionDate: Date?
    let notes: String?
    let createdAt: Date?

    var id: String { transactionId }

    enum CodingKeys: String, CodingKey {
        case transactionId = "transaction_id"
        case assetId = "asset_id"
        case symbol
        case assetName = "asset_name"
        case transactionType = "transaction_type"
        case quantity, price, fees, taxes
        case totalAmount = "total_amount"
        case transactionDate = "transaction_date"
        case notes
        case createdAt = "created_at"
    }
}

// MARK: - Request/Response

struct PortfolioCreateRequest: Codable {
    let name: String
    let description: String?
    let baseCurrency: String
    let benchmarkSymbol: String
    let riskFreeRate: Double
    let initialCapital: Double?

    enum CodingKeys: String, CodingKey {
        case name, description
        case baseCurrency = "base_currency"
        case benchmarkSymbol = "benchmark_symbol"
        case riskFreeRate = "risk_free_rate"
        case initialCapital = "initial_capital"
    }
}

struct PortfolioCreateResponse: Codable {
    let portfolioId: String
    let name: String
    let createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case portfolioId = "portfolio_id"
        case name
        case createdAt = "created_at"
    }
}
