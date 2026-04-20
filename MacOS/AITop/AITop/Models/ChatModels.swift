//
//  ChatModels.swift
//  AITop
//

import Foundation

struct ChatRequest: Codable {
    let model: String
    let messages: [ChatMessage]
    let system: String?
    let temperature: Double
    let maxTokens: Int
    let stream: Bool
    let ragEnabled: Bool  // false for clean model testing (no Angela memory injection)
}

struct ChatMessage: Codable, Identifiable {
    let role: String
    let content: String
    var model: String? = nil  // Local-only: which model produced this message (assistant) — not sent to backend

    var id: String { "\(role)-\(content.prefix(20))-\(UUID().uuidString.prefix(4))" }

    enum CodingKeys: String, CodingKey {
        case role, content  // `model` omitted on purpose so request payload stays clean
    }
}

struct ChatResponse: Codable {
    let content: String
    let model: String
    let totalDurationMs: Double
    let evalCount: Int
    let evalDurationMs: Double
    let tokensPerSecond: Double
}
