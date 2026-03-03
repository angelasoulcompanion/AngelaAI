//
//  AIModels.swift
//  Pythia — AI feature models (Phase 4 + LLM Upgrade)
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
    let sessionId: String?
    let success: Bool
    let error: String?
    // Enhanced
    let llmAnalysis: String?
    let llmProvider: String?

    enum CodingKeys: String, CodingKey {
        case portfolio, analysis
        case holdingsCount = "holdings_count"
        case sectorsCount = "sectors_count"
        case diversificationScore = "diversification_score"
        case question
        case conversationId = "conversation_id"
        case sessionId = "session_id"
        case success, error
        case llmAnalysis = "llm_analysis"
        case llmProvider = "llm_provider"
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

struct ChatBubble: Identifiable {
    let id = UUID()
    let role: String  // "user" or "assistant"
    let content: String
    let timestamp: Date
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
    // Enhanced
    let narrative: String?
    let newsHeadlines: [NewsHeadline]?
    let technicalScore: Double?
    let newsScore: Double?
    let combinedScore: Double?
    let llmProvider: String?

    enum CodingKeys: String, CodingKey {
        case symbol, sentiment, score, signals
        case priceMomentum = "price_momentum"
        case volumeTrend = "volume_trend"
        case volatilityRegime = "volatility_regime"
        case success, message
        case narrative
        case newsHeadlines = "news_headlines"
        case technicalScore = "technical_score"
        case newsScore = "news_score"
        case combinedScore = "combined_score"
        case llmProvider = "llm_provider"
    }
}

struct SentimentSignal: Codable, Identifiable {
    let signal: String
    let impact: String
    let value: Double?

    var id: String { signal }
}

struct NewsHeadline: Codable, Identifiable {
    let title: String
    let publisher: String?
    let link: String?

    var id: String { title }
}

// MARK: - AI Forecast

struct AIForecastResponse: Codable {
    let symbol: String
    let method: String
    let currentPrice: Double
    let forecastDays: Int
    let trend: String
    let confidence: Double
    let confidenceLevel: String?
    let predictions: [PricePrediction]
    let historicalPrices: [HistoricalPricePoint]?
    let success: Bool
    let message: String?
    // Enhanced
    let interpretation: String?
    let riskFactors: [String]?
    let llmProvider: String?

    enum CodingKeys: String, CodingKey {
        case symbol, method
        case currentPrice = "current_price"
        case forecastDays = "forecast_days"
        case trend, confidence
        case confidenceLevel = "confidence_level"
        case predictions
        case historicalPrices = "historical_prices"
        case success, message
        case interpretation
        case riskFactors = "risk_factors"
        case llmProvider = "llm_provider"
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

struct HistoricalPricePoint: Codable, Identifiable {
    let date: String
    let price: Double

    var id: String { date }
}

// MARK: - AI Research

struct ResearchSearchResponse: Codable {
    let query: String
    let results: [ResearchDoc]
    let summary: String
    let sourcesCount: Int
    let success: Bool
    // Enhanced
    let searchMethod: String?
    let llmProvider: String?

    enum CodingKeys: String, CodingKey {
        case query, results, summary
        case sourcesCount = "sources_count"
        case success
        case searchMethod = "search_method"
        case llmProvider = "llm_provider"
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

struct ResearchAskResponse: Codable {
    let question: String
    let answer: String
    let sources: [ResearchSource]
    let llmProvider: String?
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case question, answer, sources
        case llmProvider = "llm_provider"
        case success, message
    }
}

struct ResearchSource: Codable, Identifiable {
    let title: String
    let sourceUrl: String?
    let sourceType: String?

    var id: String { title }

    enum CodingKeys: String, CodingKey {
        case title
        case sourceUrl = "source_url"
        case sourceType = "source_type"
    }
}
