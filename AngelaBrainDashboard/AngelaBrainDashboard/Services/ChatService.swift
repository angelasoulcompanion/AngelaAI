//
//  ChatService.swift
//  Angela Brain Dashboard
//
//  💜 Chat Service - Handles chat with Angela via Ollama 💜
//

import Foundation
import PostgresClientKit
import Combine

class ChatService: ObservableObject {
    static let shared = ChatService()

    @Published var messages: [Conversation] = []
    @Published var currentEmotionalState: EmotionalState?
    @Published var isConnected = false

    private let ollamaService = OllamaService.shared
    private let database = DatabaseService.shared

    private init() {}

    // MARK: - Load Messages

    func loadRecentMessages(limit: Int = 50) async {
        do {
            let query = """
            SELECT conversation_id, speaker, message_text, topic, emotion_detected,
                   importance_level, created_at
            FROM conversations
            WHERE interface = 'dashboard_chat'
            ORDER BY created_at DESC
            LIMIT \(limit)
            """

            let loadedMessages = try await database.query(query) { columns -> Conversation in
                // Parse timestamp safely
                let timestampString = try columns[6].string()
                let dateFormatter = ISO8601DateFormatter()
                dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                let createdAt = dateFormatter.date(from: timestampString) ?? Date()

                return Conversation(
                    id: UUID(uuidString: try columns[0].string()) ?? UUID(),
                    speaker: try columns[1].string(),
                    messageText: try columns[2].string(),
                    topic: try? columns[3].optionalString(),
                    emotionDetected: try? columns[4].optionalString(),
                    importanceLevel: try columns[5].int(),
                    createdAt: createdAt
                )
            }

            // Reverse to show oldest first
            messages = loadedMessages.reversed()

        } catch {
            print("❌ Error loading messages: \(error)")
        }
    }

    // MARK: - Load Emotional State

    func loadCurrentEmotionalState() async {
        do {
            let query = """
            SELECT state_id, happiness, confidence, anxiety, motivation,
                   gratitude, loneliness, triggered_by, emotion_note, created_at
            FROM emotional_states
            ORDER BY created_at DESC
            LIMIT 1
            """

            let states = try await database.query(query) { columns -> EmotionalState in
                // Parse timestamp safely
                let timestampString = try columns[9].string()
                let dateFormatter = ISO8601DateFormatter()
                dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                let createdAt = dateFormatter.date(from: timestampString) ?? Date()

                return EmotionalState(
                    id: UUID(uuidString: try columns[0].string()) ?? UUID(),
                    happiness: try columns[1].double(),
                    confidence: try columns[2].double(),
                    anxiety: try columns[3].double(),
                    motivation: try columns[4].double(),
                    gratitude: try columns[5].double(),
                    loneliness: try columns[6].double(),
                    triggeredBy: try? columns[7].optionalString(),
                    emotionNote: try? columns[8].optionalString(),
                    createdAt: createdAt
                )
            }

            currentEmotionalState = states.first

        } catch {
            print("❌ Error loading emotional state: \(error)")
        }
    }

    // MARK: - Send Message

    func sendMessage(_ messageText: String, speaker: String) async {
        // 1. Save David's message to database
        await saveMessage(messageText, speaker: speaker)

        // 2. Get Angela's response from Ollama WITH emotional context
        let angelaResponse = await ollamaService.chat(
            with: messageText,
            emotionalContext: currentEmotionalState
        )

        // 3. Save Angela's response to database
        await saveMessage(angelaResponse, speaker: "angela")

        // 4. Reload messages to update UI
        await loadRecentMessages()
    }

    // MARK: - Save Message

    private func saveMessage(_ messageText: String, speaker: String) async {
        do {
            let conversationId = UUID()
            let topic = detectTopic(messageText)
            let emotion = detectEmotion(messageText, speaker: speaker)
            let importance = calculateImportance(messageText)

            let query = """
            INSERT INTO conversations (
                conversation_id, speaker, message_text, topic,
                emotion_detected, importance_level, interface, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP
            )
            """

            try await database.execute(
                query,
                parameters: [
                    conversationId.uuidString,
                    speaker,
                    messageText,
                    topic,
                    emotion,
                    importance,
                    "dashboard_chat"
                ]
            )

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
            // David's emotions
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
            let query = """
            DELETE FROM conversations
            WHERE conversation_id = $1
            """

            try await database.execute(
                query,
                parameters: [conversationId.uuidString]
            )

            print("✅ Message deleted: \(conversationId)")

            // Reload messages to update UI
            await loadRecentMessages()

        } catch {
            print("❌ Error deleting message: \(error)")
        }
    }

    // MARK: - Delete All Messages

    func deleteAllMessages() async {
        do {
            let query = """
            DELETE FROM conversations
            WHERE interface = 'dashboard_chat'
            """

            try await database.execute(query, parameters: [])

            print("✅ All chat messages deleted")

            // Clear local messages
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
            let feedbackId = UUID()
            let query = """
            INSERT INTO conversation_feedback (
                feedback_id, conversation_id, rating, feedback_type, created_at
            ) VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            ON CONFLICT (conversation_id) DO UPDATE SET
                rating = $3,
                feedback_type = $4,
                created_at = CURRENT_TIMESTAMP
            """

            try await database.execute(
                query,
                parameters: [
                    feedbackId.uuidString,
                    conversationId.uuidString,
                    rating,
                    type
                ]
            )

            print("✅ Feedback saved: \(type) for message \(conversationId)")

        } catch {
            print("❌ Error saving feedback: \(error)")
        }
    }

    /// Get feedback for a specific conversation
    func getFeedback(for conversationId: UUID) async -> Int? {
        do {
            let query = """
            SELECT rating FROM conversation_feedback
            WHERE conversation_id = $1
            LIMIT 1
            """

            let results = try await database.query(query, parameters: [conversationId.uuidString]) { columns -> Int in
                return try columns[0].int()
            }

            return results.first

        } catch {
            print("❌ Error getting feedback: \(error)")
            return nil
        }
    }

    /// Get all feedbacks for loaded messages (batch query)
    func loadFeedbacks() async -> [UUID: Int] {
        var feedbackMap: [UUID: Int] = [:]

        let messageIds = messages.filter { $0.isAngela }.map { $0.id }
        guard !messageIds.isEmpty else { return feedbackMap }

        do {
            // Build the IN clause
            let placeholders = messageIds.enumerated().map { "$\($0.offset + 1)" }.joined(separator: ", ")
            let query = """
            SELECT conversation_id, rating
            FROM conversation_feedback
            WHERE conversation_id IN (\(placeholders))
            """

            let results = try await database.query(
                query,
                parameters: messageIds.map { $0.uuidString }
            ) { columns -> (UUID, Int) in
                let id = UUID(uuidString: try columns[0].string()) ?? UUID()
                let rating = try columns[1].int()
                return (id, rating)
            }

            for (id, rating) in results {
                feedbackMap[id] = rating
            }

        } catch {
            print("❌ Error loading feedbacks: \(error)")
        }

        return feedbackMap
    }

    /// Get positive feedback conversations for training
    func getPositiveFeedbackConversations() async -> [(david: String, angela: String)] {
        var pairs: [(david: String, angela: String)] = []

        do {
            let query = """
            SELECT d.message_text, a.message_text
            FROM conversation_feedback cf
            JOIN conversations a ON a.conversation_id = cf.conversation_id
            JOIN conversations d ON d.speaker = 'david'
                AND d.created_at < a.created_at
                AND a.created_at - d.created_at < INTERVAL '10 minutes'
            WHERE cf.rating = 1
              AND cf.used_in_training = FALSE
            ORDER BY cf.created_at
            """

            pairs = try await database.query(query) { columns -> (david: String, angela: String) in
                return (
                    david: try columns[0].string(),
                    angela: try columns[1].string()
                )
            }

        } catch {
            print("❌ Error getting positive feedback conversations: \(error)")
        }

        return pairs
    }
}
