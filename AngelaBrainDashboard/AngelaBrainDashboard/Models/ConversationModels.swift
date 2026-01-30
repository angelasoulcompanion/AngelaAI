//
//  ConversationModels.swift
//  Angela Brain Dashboard
//
//  Conversation model
//

import Foundation

// MARK: - Conversation

struct Conversation: Identifiable, Codable {
    let id: UUID
    let speaker: String              // "david" or "angela"
    let messageText: String
    let topic: String?
    let emotionDetected: String?
    let importanceLevel: Int
    let createdAt: Date
    let modelUsed: String?           // "gemini-2.5-flash" or "scb10x/typhoon2.5-qwen3-4b"

    enum CodingKeys: String, CodingKey {
        case id = "conversation_id"
        case speaker
        case messageText = "message_text"
        case topic
        case emotionDetected = "emotion_detected"
        case importanceLevel = "importance_level"
        case createdAt = "created_at"
        case modelUsed = "model_used"
    }

    var isDavid: Bool {
        speaker.lowercased() == "david"
    }

    var isAngela: Bool {
        speaker.lowercased() == "angela"
    }

    var preview: String {
        String(messageText.prefix(100))
    }
}
