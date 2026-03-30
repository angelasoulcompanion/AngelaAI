//
//  PatternModels.swift
//  Pythia — Chart Pattern Recognition models (Phase 8.5)
//

import Foundation

// MARK: - Pattern Detection

struct PatternResponse: Codable {
    let assetId: String
    let symbol: String
    let currentPrice: Double
    let patterns: [ChartPattern]
    let count: Int
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case assetId = "asset_id"
        case symbol
        case currentPrice = "current_price"
        case patterns, count, success, message
    }
}

struct ChartPattern: Codable, Identifiable {
    var id: String { "\(patternType)_\(startDate ?? "")" }
    let patternType: String
    let direction: String
    let confidence: Double
    let startDate: String?
    let endDate: String?
    let breakoutPrice: Double?
    let targetPrice: Double?
    let description: String?
    let keyLevels: [Double]?

    enum CodingKeys: String, CodingKey {
        case patternType = "pattern_type"
        case direction, confidence
        case startDate = "start_date"
        case endDate = "end_date"
        case breakoutPrice = "breakout_price"
        case targetPrice = "target_price"
        case description
        case keyLevels = "key_levels"
    }
}
