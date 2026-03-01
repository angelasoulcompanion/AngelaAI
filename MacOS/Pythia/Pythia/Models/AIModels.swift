//
//  AIModels.swift
//  Pythia — AI feature models (Phase 4)
//

import Foundation

// MARK: - AI Advisor

struct AIAdvisorResponse: Codable {
    let portfolio: String?
    let analysis: [String]
    let holdingsCount: Int?
    let sectorsCount: Int?
    let diversificationScore: Double?
    let question: String?
    let conversationId: String?
    let success: Bool
    let error: String?

    enum CodingKeys: String, CodingKey {
        case portfolio, analysis
        case holdingsCount = "holdings_count"
        case sectorsCount = "sectors_count"
        case diversificationScore = "diversification_score"
        case question
        case conversationId = "conversation_id"
        case success, error
    }
}

struct AIConversationMessage: Codable, Identifiable {
    let conversationId: String
    let type: String
    let content: String
    let createdAt: String?

    var id: String { conversationId }

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case type, content
        case createdAt = "created_at"
    }
}

// MARK: - AI Sentiment

struct AISentimentResponse: Codable {
    let symbol: String
    let sentiment: String
    let score: Double
    let signals: [SentimentSignal]
    let priceMomentum: Double
    let volumeTrend: Double
    let volatilityRegime: String
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case symbol, sentiment, score, signals
        case priceMomentum = "price_momentum"
        case volumeTrend = "volume_trend"
        case volatilityRegime = "volatility_regime"
        case success, message
    }
}

struct SentimentSignal: Codable, Identifiable {
    let signal: String
    let impact: String
    let value: Double?

    var id: String { signal }
}

// MARK: - AI Forecast

struct AIForecastResponse: Codable {
    let symbol: String
    let method: String
    let currentPrice: Double
    let forecastDays: Int
    let trend: String
    let confidence: Double
    let predictions: [PricePrediction]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case symbol, method
        case currentPrice = "current_price"
        case forecastDays = "forecast_days"
        case trend, confidence, predictions
        case success, message
    }
}

struct PricePrediction: Codable, Identifiable {
    let day: Int
    let price: Double
    let lower: Double
    let upper: Double
    let date: String?

    var id: Int { day }
}

// MARK: - AI Research

struct ResearchSearchResponse: Codable {
    let query: String
    let results: [ResearchDoc]
    let summary: String
    let sourcesCount: Int
    let success: Bool

    enum CodingKeys: String, CodingKey {
        case query, results, summary
        case sourcesCount = "sources_count"
        case success
    }
}

struct ResearchDoc: Codable, Identifiable {
    let documentId: String?
    let title: String
    let content: String?
    let sourceUrl: String?
    let sourceType: String?
    let createdAt: String?
    let tags: [String]?

    var id: String { documentId ?? title }

    enum CodingKeys: String, CodingKey {
        case documentId = "document_id"
        case title, content
        case sourceUrl = "source_url"
        case sourceType = "source_type"
        case createdAt = "created_at"
        case tags
    }
}
