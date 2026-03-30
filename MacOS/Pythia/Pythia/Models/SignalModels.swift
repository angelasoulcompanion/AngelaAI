//
//  SignalModels.swift
//  Pythia — Trading Signal models (Phase 7.2)
//

import Foundation

// MARK: - Signal Generation

struct SignalResponse: Codable {
    let assetId: String
    let symbol: String
    let compositeScore: Double
    let compositeDirection: String
    let technicalScore: Double
    let sentimentScore: Double
    let quantScore: Double
    let aiInsight: String?
    let signals: [TradingSignal]
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol
        case compositeScore = "composite_score"
        case compositeDirection = "composite_direction"
        case technicalScore = "technical_score"
        case sentimentScore = "sentiment_score"
        case quantScore = "quant_score"
        case aiInsight = "ai_insight"
        case signals, success, message
    }
}

struct TradingSignal: Codable, Identifiable {
    var id: String { signalName }
    let signalType: String
    let signalName: String
    let direction: String
    let strength: Double
    let confidence: Double
    let metadata: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case signalType = "signal_type"
        case signalName = "signal_name"
        case direction, strength, confidence, metadata
    }
}

// MARK: - Signal Scan

struct SignalScanResponse: Codable {
    let results: [SignalScanResult]
    let count: Int
    let scanned: Int
}

struct SignalScanResult: Codable, Identifiable {
    var id: String { assetId }
    let assetId: String
    let symbol: String
    let compositeScore: Double
    let direction: String
    let topSignal: String
    let regime: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol
        case compositeScore = "composite_score"
        case direction
        case topSignal = "top_signal"
        case regime
    }
}

// MARK: - Signal History

struct SignalHistoryResponse: Codable {
    let assetId: String
    let days: Int
    let signals: [SignalHistoryEntry]
    let count: Int

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case days, signals, count
    }
}

struct SignalHistoryEntry: Codable, Identifiable {
    var id: String { "\(signalName)_\(createdAt)" }
    let signalType: String
    let signalName: String
    let direction: String
    let strength: Double
    let confidence: Double
    let metadata: [String: AnyCodable]?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case signalType = "signal_type"
        case signalName = "signal_name"
        case direction, strength, confidence, metadata
        case createdAt = "created_at"
    }
}

// MARK: - AnyCodable for flexible metadata

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) { self.value = value }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let intVal = try? container.decode(Int.self) { value = intVal }
        else if let doubleVal = try? container.decode(Double.self) { value = doubleVal }
        else if let stringVal = try? container.decode(String.self) { value = stringVal }
        else if let boolVal = try? container.decode(Bool.self) { value = boolVal }
        else { value = "" }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let v = value as? Int { try container.encode(v) }
        else if let v = value as? Double { try container.encode(v) }
        else if let v = value as? String { try container.encode(v) }
        else if let v = value as? Bool { try container.encode(v) }
        else { try container.encode(String(describing: value)) }
    }
}
