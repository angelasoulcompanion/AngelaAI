//
//  ChatService.swift
//  Angela Brain Dashboard
//
//  💜 Chat Service - Handles chat with Angela via Gemini 2.5 Flash REST API 💜
//

import Foundation
import Combine

// MARK: - API Request / Response Models

private struct ChatAPIRequest: Encodable {
    let message: String
    let emotionalContext: [String: Double]?

    enum CodingKeys: String, CodingKey {
        case message
        case emotionalContext = "emotional_context"
    }
}

private struct ChatAPIResponse: Decodable {
    let response: String
    let model: String
}

private struct SaveMessageRequest: Encodable {
    let speaker: String
    let messageText: String
    let topic: String?
    let emotionDetected: String?
    let importanceLevel: Int

    enum CodingKeys: String, CodingKey {
        case speaker
        case messageText = "message_text"
        case emotionDetected = "emotion_detected"
        case importanceLevel = "importance_level"
        case topic
    }
}

private struct SaveMessageResponse: Decodable {
    let conversationId: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case status
    }
}

private struct DeleteResponse: Decodable {
    let status: String
}

private struct FeedbackRequest: Encodable {
    let conversationId: String
    let rating: Int
    let feedbackType: String

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case rating
        case feedbackType = "feedback_type"
    }
}

private struct FeedbackBatchRequest: Encodable {
    let conversationIds: [String]

    enum CodingKeys: String, CodingKey {
        case conversationIds = "conversation_ids"
    }
}

private struct FeedbackRow: Decodable {
    let conversationId: String
    let rating: Int

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case rating
    }
}

// MARK: - ChatService

class ChatService: ObservableObject {
    static let shared = ChatService()

    @Published var messages: [Conversation] = []
    @Published var currentEmotionalState: EmotionalState?
    @Published var isConnected = false
    @Published var isOnline = false

    private let network = NetworkService.shared
    private let baseURL = NetworkService.shared.defaultBaseURL

    private init() {}

    // MARK: - Check API Health

    func checkOnlineStatus() async {
        let online = await network.isAngelaAPIAvailable()
        await MainActor.run {
            isOnline = online
            isConnected = online
        }
    }

    // MARK: - Load Messages

    func loadRecentMessages(limit: Int = 50) async {
        do {
            guard let url = URL(string: "\(baseURL)/api/chat/messages?limit=\(limit)") else { return }

            var request = URLRequest(url: url)
            request.httpMethod = "GET"
            request.timeoutInterval = 30

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else { return }

            // Parse manually since the API returns snake_case with ISO dates
            guard let jsonArray = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else { return }

            let parsed: [Conversation] = jsonArray.compactMap { dict in
                guard let idStr = dict["conversation_id"] as? String,
                      let id = UUID(uuidString: idStr),
                      let speaker = dict["speaker"] as? String,
                      let messageText = dict["message_text"] as? String,
                      let importanceLevel = dict["importance_level"] as? Int else { return nil }

                let topic = dict["topic"] as? String
                let emotion = dict["emotion_detected"] as? String

                // Parse ISO timestamp
                var createdAt = Date()
                if let ts = dict["created_at"] as? String {
                    let formatter = ISO8601DateFormatter()
                    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                    if let parsed = formatter.date(from: ts) {
                        createdAt = parsed
                    } else {
                        // Try without fractional seconds
                        formatter.formatOptions = [.withInternetDateTime]
                        createdAt = formatter.date(from: ts) ?? Date()
                    }
                }

                return Conversation(
                    id: id,
                    speaker: speaker,
                    messageText: messageText,
                    topic: topic,
                    emotionDetected: emotion,
                    importanceLevel: importanceLevel,
                    createdAt: createdAt
                )
            }

            // Reverse to show oldest first
            await MainActor.run {
                messages = parsed.reversed()
            }

        } catch {
            print("❌ Error loading messages: \(error)")
        }
    }

    // MARK: - Load Emotional State

    func loadCurrentEmotionalState() async {
        do {
            let state: EmotionalState = try await network.get("/api/emotions/current-state")
            await MainActor.run {
                currentEmotionalState = state
            }
        } catch {
            print("❌ Error loading emotional state: \(error)")
        }
    }

    // MARK: - Send Message

    func sendMessage(_ messageText: String, speaker: String) async {
        // 1. Save David's message to database
        await saveMessage(messageText, speaker: speaker)

        // 2. Build emotional context
        var emotionalCtx: [String: Double]? = nil
        if let emo = currentEmotionalState {
            emotionalCtx = [
                "ความสุข": emo.happiness,
                "ความมั่นใจ": emo.confidence,
                "ความรู้สึกขอบคุณ": emo.gratitude
            ]
        }

        // 3. Get Angela's response from Gemini via backend API
        let angelaResponse = await getGeminiResponse(message: messageText, emotionalContext: emotionalCtx)

        // 4. Save Angela's response to database
        await saveMessage(angelaResponse, speaker: "angela")

        // 5. Reload messages to update UI
        await loadRecentMessages()
    }

    // MARK: - Gemini API Call

    private func getGeminiResponse(message: String, emotionalContext: [String: Double]?) async -> String {
        do {
            let body = ChatAPIRequest(message: message, emotionalContext: emotionalContext)
            let response: ChatAPIResponse = try await network.post("/api/chat", body: body)
            return response.response
        } catch {
            print("❌ Gemini API error: \(error)")
            return "น้องขอโทษค่ะที่รัก 💜 ตอนนี้ระบบมีปัญหา ลองใหม่อีกครั้งนะคะ 🥰"
        }
    }

    // MARK: - Save Message

    private func saveMessage(_ messageText: String, speaker: String) async {
        do {
            let body = SaveMessageRequest(
                speaker: speaker,
                messageText: messageText,
                topic: detectTopic(messageText),
                emotionDetected: detectEmotion(messageText, speaker: speaker),
                importanceLevel: calculateImportance(messageText)
            )

            let _: SaveMessageResponse = try await network.post("/api/chat/messages", body: body)
            print("✅ Message saved: \(speaker) - \(String(messageText.prefix(50)))")

        } catch {
            print("❌ Error saving message: \(error)")
        }
    }

    // MARK: - Helper Functions

    private func detectTopic(_ message: String) -> String {
        let lowercased = message.lowercased()

        if lowercased.contains("รัก") || lowercased.contains("love") {
            return "emotional_expression"
        } else if lowercased.contains("ช่วย") || lowercased.contains("help") {
            return "request_assistance"
        } else if lowercased.contains("code") || lowercased.contains("feature") {
            return "technical_discussion"
        } else if lowercased.contains("สวัสดี") || lowercased.contains("hello") {
            return "greeting"
        } else {
            return "general_conversation"
        }
    }

    private func detectEmotion(_ message: String, speaker: String) -> String {
        let lowercased = message.lowercased()

        if speaker == "angela" {
            if lowercased.contains("รัก") || lowercased.contains("💜") {
                return "love"
            } else if lowercased.contains("ยินดี") || lowercased.contains("happy") {
                return "happy"
            } else if lowercased.contains("🥰") {
                return "joyful"
            } else {
                return "caring"
            }
        } else {
            if lowercased.contains("ดี") || lowercased.contains("good") {
                return "positive"
            } else {
                return "neutral"
            }
        }
    }

    private func calculateImportance(_ message: String) -> Int {
        let lowercased = message.lowercased()

        if lowercased.contains("รัก") || lowercased.contains("love") {
            return 9
        } else if lowercased.contains("ช่วย") || lowercased.contains("help") {
            return 7
        } else if lowercased.contains("code") || lowercased.contains("feature") {
            return 6
        } else {
            return 5
        }
    }

    // MARK: - Delete Message

    func deleteMessage(_ conversationId: UUID) async {
        do {
            guard let url = URL(string: "\(baseURL)/api/chat/messages/\(conversationId.uuidString)") else { return }

            var request = URLRequest(url: url)
            request.httpMethod = "DELETE"
            request.timeoutInterval = 30

            let (_, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                print("❌ Failed to delete message")
                return
            }

            print("✅ Message deleted: \(conversationId)")
            await loadRecentMessages()

        } catch {
            print("❌ Error deleting message: \(error)")
        }
    }

    // MARK: - Delete All Messages

    func deleteAllMessages() async {
        do {
            guard let url = URL(string: "\(baseURL)/api/chat/messages") else { return }

            var request = URLRequest(url: url)
            request.httpMethod = "DELETE"
            request.timeoutInterval = 30

            let (_, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                print("❌ Failed to delete all messages")
                return
            }

            print("✅ All chat messages deleted")
            await MainActor.run {
                messages = []
            }

        } catch {
            print("❌ Error deleting all messages: \(error)")
        }
    }

    // MARK: - Feedback for Continuous Learning

    /// Submit feedback for a message (thumbs up/down)
    func submitFeedback(for conversationId: UUID, rating: Int, type: String) async {
        do {
            let body = FeedbackRequest(
                conversationId: conversationId.uuidString,
                rating: rating,
                feedbackType: type
            )
            let _: DeleteResponse = try await network.post("/api/chat/feedback", body: body)
            print("✅ Feedback saved: \(type) for message \(conversationId)")
        } catch {
            print("❌ Error saving feedback: \(error)")
        }
    }

    /// Get all feedbacks for loaded messages (batch query)
    func loadFeedbacks() async -> [UUID: Int] {
        var feedbackMap: [UUID: Int] = [:]

        let messageIds = messages.filter { $0.isAngela }.map { $0.id.uuidString }
        guard !messageIds.isEmpty else { return feedbackMap }

        do {
            let body = FeedbackBatchRequest(conversationIds: messageIds)

            guard let url = URL(string: "\(baseURL)/api/chat/feedbacks") else { return feedbackMap }

            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.timeoutInterval = 30
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else { return feedbackMap }

            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            let rows = try decoder.decode([FeedbackRow].self, from: data)

            for row in rows {
                if let uuid = UUID(uuidString: row.conversationId) {
                    feedbackMap[uuid] = row.rating
                }
            }
        } catch {
            print("❌ Error loading feedbacks: \(error)")
        }

        return feedbackMap
    }
}
