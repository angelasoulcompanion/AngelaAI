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

struct WatchlistQuote: Codable, Identifiable {
    let symbol: String
    let name: String?
    let currentPrice: Double?
    let change: Double?
    let changePercent: Double?
    let sparkline: [Double]
    let currency: String?

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, name
        case currentPrice = "current_price"
        case change
        case changePercent = "change_percent"
        case sparkline, currency
    }
}

// MARK: - Financial Outlook

struct FinancialOutlookResponse: Codable {
    let symbol: String
    let name: String?
    let sector: String?
    let industry: String?
    // Analyst
    let recommendation: String?
    let recommendationMean: Double?
    let numberOfAnalysts: Int?
    let targetHigh: Double?
    let targetLow: Double?
    let targetMean: Double?
    let targetMedian: Double?
    // Valuation
    let peTrailing: Double?
    let peForward: Double?
    let pegRatio: Double?
    let priceToBook: Double?
    let priceToSales: Double?
    let evToEbitda: Double?
    // Profitability
    let profitMargin: Double?
    let operatingMargin: Double?
    let grossMargin: Double?
    let returnOnEquity: Double?
    let returnOnAssets: Double?
    // Growth
    let revenueGrowth: Double?
    let earningsGrowth: Double?
    let earningsQuarterlyGrowth: Double?
    // Financials
    let totalRevenue: Double?
    let ebitda: Double?
    let totalDebt: Double?
    let totalCash: Double?
    let debtToEquity: Double?
    let currentRatio: Double?
    // Dividends
    let dividendRate: Double?
    let dividendYield: Double?
    let payoutRatio: Double?
    let currency: String?

    enum CodingKeys: String, CodingKey {
        case symbol, name, sector, industry
        case recommendation
        case recommendationMean = "recommendation_mean"
        case numberOfAnalysts = "number_of_analysts"
        case targetHigh = "target_high"
        case targetLow = "target_low"
        case targetMean = "target_mean"
        case targetMedian = "target_median"
        case peTrailing = "pe_trailing"
        case peForward = "pe_forward"
        case pegRatio = "peg_ratio"
        case priceToBook = "price_to_book"
        case priceToSales = "price_to_sales"
        case evToEbitda = "ev_to_ebitda"
        case profitMargin = "profit_margin"
        case operatingMargin = "operating_margin"
        case grossMargin = "gross_margin"
        case returnOnEquity = "return_on_equity"
        case returnOnAssets = "return_on_assets"
        case revenueGrowth = "revenue_growth"
        case earningsGrowth = "earnings_growth"
        case earningsQuarterlyGrowth = "earnings_quarterly_growth"
        case totalRevenue = "total_revenue"
        case ebitda
        case totalDebt = "total_debt"
        case totalCash = "total_cash"
        case debtToEquity = "debt_to_equity"
        case currentRatio = "current_ratio"
        case dividendRate = "dividend_rate"
        case dividendYield = "dividend_yield"
        case payoutRatio = "payout_ratio"
        case currency
    }
}

// MARK: - Financial Statements

struct FinancialStatementsResponse: Codable {
    let symbol: String
    let period: String
    let incomeStatement: StatementData
    let balanceSheet: StatementData
    let cashFlow: StatementData

    enum CodingKeys: String, CodingKey {
        case symbol, period
        case incomeStatement = "income_statement"
        case balanceSheet = "balance_sheet"
        case cashFlow = "cash_flow"
    }
}

struct StatementData: Codable {
    let periods: [String]
    let items: [StatementItem]
}

struct StatementItem: Codable, Identifiable {
    let label: String
    let values: [Double?]

    var id: String { label }
}

// MARK: - Technical Analysis

struct TechnicalAnalysisResponse: Codable {
    let symbol: String
    let period: String
    let interval: String
    let dates: [String]
    let ohlcv: OHLCVData
    let macd: MACDData
    let rsi: RSIData
    let bollinger: BollingerData
    let sma: [String: [Double?]]
    let ema: [String: [Double?]]
}

struct OHLCVData: Codable {
    let open: [Double]
    let high: [Double]
    let low: [Double]
    let close: [Double]
    let volume: [Int]
}

struct MACDData: Codable {
    let params: MACDParams
    let macd: [Double?]
    let signal: [Double?]
    let histogram: [Double?]
}

struct MACDParams: Codable {
    let fast: Int
    let slow: Int
    let signal: Int
}

struct RSIData: Codable {
    let params: RSIParams
    let values: [Double?]
}

struct RSIParams: Codable {
    let period: Int
}

struct BollingerData: Codable {
    let params: BollingerParams
    let upper: [Double?]
    let middle: [Double?]
    let lower: [Double?]
}

struct BollingerParams: Codable {
    let period: Int
    let stdDev: Double

    enum CodingKeys: String, CodingKey {
        case period
        case stdDev = "std_dev"
    }
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

// MARK: - Watchlist CRUD Bodies

struct WatchlistCreateBody: Codable {
    let name: String
    let description: String?
}

struct WatchlistCreateResponse: Codable {
    let watchlistId: String
    let name: String
    let createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case watchlistId = "watchlist_id"
        case name
        case createdAt = "created_at"
    }
}

struct WatchlistItemAddBody: Codable {
    let assetId: String
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case notes
    }
}

struct WatchlistItemAddResponse: Codable {
    let itemId: String?
    let assetId: String?
    let status: String?

    enum CodingKeys: String, CodingKey {
        case itemId = "item_id"
        case assetId = "asset_id"
        case status
    }
}
