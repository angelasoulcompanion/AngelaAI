//
//  ChatService.swift
//  Angela Brain Dashboard
//
//  💜 Chat Service - SSE streaming + emotional mirroring 💜
//

import Foundation
import Combine

// MARK: - API Request / Response Models

private struct ChatAPIRequest: Encodable {
    let message: String
    let emotionalContext: [String: Double]?
    let model: String
    let imageData: String?
    let imageMimeType: String?

    enum CodingKeys: String, CodingKey {
        case message
        case emotionalContext = "emotional_context"
        case model
        case imageData = "image_data"
        case imageMimeType = "image_mime_type"
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
    let modelUsed: String?

    enum CodingKeys: String, CodingKey {
        case speaker
        case messageText = "message_text"
        case emotionDetected = "emotion_detected"
        case importanceLevel = "importance_level"
        case topic
        case modelUsed = "model_used"
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

// MARK: - Emotional Metadata (from SSE metadata event)

struct EmotionalMetadata: Codable {
    let emotionDetected: String
    let emotionIntensity: Int
    let emotionConfidence: Double
    let emotionCues: [String]
    let angelaEmotion: String
    let angelaIntensity: Int
    let mirroringStrategy: String
    let mirroringDescription: String
    let mirroringIcon: String
    let triggeredMemoryTitles: [String]
    let consciousnessLevel: Double
    let sectionsLoaded: [String]

    enum CodingKeys: String, CodingKey {
        case emotionDetected = "emotion_detected"
        case emotionIntensity = "emotion_intensity"
        case emotionConfidence = "emotion_confidence"
        case emotionCues = "emotion_cues"
        case angelaEmotion = "angela_emotion"
        case angelaIntensity = "angela_intensity"
        case mirroringStrategy = "mirroring_strategy"
        case mirroringDescription = "mirroring_description"
        case mirroringIcon = "mirroring_icon"
        case triggeredMemoryTitles = "triggered_memory_titles"
        case consciousnessLevel = "consciousness_level"
        case sectionsLoaded = "sections_loaded"
    }
}

// MARK: - Thinking Step

enum ThinkingStep: String {
    case loadingMemories = "loading_memories"
    case readingEmotion = "reading_emotion"
    case mirroring = "mirroring"
    case composing = "composing"
    case processingImage = "processing_image"

    var displayText: String {
        switch self {
        case .loadingMemories:  return "กำลังโหลดความทรงจำ..."
        case .readingEmotion:   return "กำลังอ่านอารมณ์ของที่รัก..."
        case .mirroring:        return "กำลัง mirror อารมณ์..."
        case .composing:        return "กำลังคิดคำตอบ..."
        case .processingImage:  return "กำลังดูรูปที่ที่รักส่งมา..."
        }
    }

    var icon: String {
        switch self {
        case .loadingMemories:  return "brain.head.profile"
        case .readingEmotion:   return "heart.text.square"
        case .mirroring:        return "arrow.triangle.2.circlepath"
        case .composing:        return "text.bubble"
        case .processingImage:  return "photo"
        }
    }
}

// MARK: - ChatService

class ChatService: ObservableObject {
    static let shared = ChatService()

    @Published var messages: [Conversation] = []
    @Published var currentEmotionalState: EmotionalState?
    @Published var isConnected = false
    @Published var isOnline = false

    // Streaming state
    @Published var streamingText: String = ""
    @Published var isStreaming = false
    @Published var currentThinkingStep: ThinkingStep? = nil
    @Published var lastEmotionalMetadata: EmotionalMetadata? = nil
    @Published var streamingModelName: String = ""

    // Learning state
    @Published var lastLearningCount: Int = 0
    @Published var lastLearningTopics: [String] = []
    @Published var isLearning: Bool = false

    // Image attachment (current session only)
    @Published var pendingImageData: Data? = nil
    @Published var pendingImageName: String? = nil
    var sentImageAttachments: [UUID: Data] = [:]  // messageID → image data (for display)

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
                let modelUsed = dict["model_used"] as? String

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
                    createdAt: createdAt,
                    modelUsed: modelUsed
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

    // MARK: - Send Message (non-streaming fallback)

    func sendMessage(_ messageText: String, speaker: String, model: String = "gemini") async {
        // 1. Save David's message to database
        await saveMessage(messageText, speaker: speaker, modelUsed: nil)

        // 2. Build emotional context
        var emotionalCtx: [String: Double]? = nil
        if let emo = currentEmotionalState {
            emotionalCtx = [
                "ความสุข": emo.happiness,
                "ความมั่นใจ": emo.confidence,
                "ความรู้สึกขอบคุณ": emo.gratitude
            ]
        }

        // 3. Get Angela's response via backend API (Gemini or Typhoon)
        let (angelaResponse, actualModel) = await getResponse(message: messageText, emotionalContext: emotionalCtx, model: model)

        // 4. Save Angela's response to database (with model info)
        await saveMessage(angelaResponse, speaker: "angela", modelUsed: actualModel)

        // 5. Reload messages to update UI
        await loadRecentMessages()
    }

    // MARK: - Send Streaming Message (SSE)

    func sendStreamingMessage(_ messageText: String, model: String = "gemini", imageData: Data? = nil) async {
        // Reset streaming state
        let hasImage = imageData != nil
        await MainActor.run {
            streamingText = ""
            isStreaming = true
            currentThinkingStep = nil
            lastEmotionalMetadata = nil
            streamingModelName = ""
            lastLearningCount = 0
            lastLearningTopics = []
            isLearning = false
            pendingImageData = imageData
        }

        // 1. Save David's message first
        let savedText = hasImage ? (messageText.isEmpty ? "[sent an image]" : messageText) : messageText
        await saveMessage(savedText, speaker: "david", modelUsed: nil)

        // 2. Build request
        var emotionalCtx: [String: Double]? = nil
        if let emo = currentEmotionalState {
            emotionalCtx = [
                "ความสุข": emo.happiness,
                "ความมั่นใจ": emo.confidence,
                "ความรู้สึกขอบคุณ": emo.gratitude
            ]
        }

        guard let url = URL(string: "\(baseURL)/api/chat/stream") else {
            await MainActor.run { isStreaming = false }
            return
        }

        // Encode image to base64 if present
        var imageBase64: String? = nil
        var imageMime: String? = nil
        if let imgData = imageData {
            imageBase64 = imgData.base64EncodedString()
            imageMime = detectMimeType(from: imgData)
        }

        let body = ChatAPIRequest(
            message: messageText.isEmpty && hasImage ? "ที่รักส่งรูปมาให้ดูค่ะ" : messageText,
            emotionalContext: emotionalCtx,
            model: model,
            imageData: imageBase64,
            imageMimeType: imageMime
        )

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 120
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")

        do {
            request.httpBody = try JSONEncoder().encode(body)
        } catch {
            print("❌ Failed to encode request: \(error)")
            await MainActor.run { isStreaming = false }
            return
        }

        // 3. Stream SSE events
        //    NOTE: AsyncBytes.lines strips empty lines, so we cannot rely on
        //    empty-line separators for SSE event boundaries. Instead, we emit
        //    the event as soon as we have both an "event:" and a "data:" line.
        do {
            let (bytes, response) = try await URLSession.shared.bytes(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                print("❌ SSE: non-2xx or invalid response")
                await fallbackSendMessage(messageText, model: model)
                return
            }

            var currentEvent = ""

            for try await line in bytes.lines {
                if line.hasPrefix("event: ") {
                    currentEvent = String(line.dropFirst(7))
                } else if line.hasPrefix("data: ") {
                    let currentData = String(line.dropFirst(6))
                    // Process immediately — bytes.lines skips empty separators
                    if !currentEvent.isEmpty {
                        await processSSEEvent(event: currentEvent, data: currentData)
                    }
                    currentEvent = ""
                }
            }

        } catch {
            print("❌ SSE stream error: \(error)")
            await fallbackSendMessage(messageText, model: model)
            return
        }

        // 4. Save Angela's complete response to DB
        let finalText = await MainActor.run { streamingText }
        let modelName = await MainActor.run { streamingModelName }
        if !finalText.isEmpty {
            let emotionForSave = await MainActor.run { lastEmotionalMetadata?.angelaEmotion }
            await saveMessage(
                finalText,
                speaker: "angela",
                emotionDetected: emotionForSave,
                modelUsed: modelName.isEmpty ? model : modelName
            )
        }

        // 5. Finalize
        await MainActor.run {
            isStreaming = false
            currentThinkingStep = nil
            pendingImageData = nil
            pendingImageName = nil
        }

        // 6. Reload messages
        await loadRecentMessages()
    }

    // MARK: - MIME Type Detection

    private func detectMimeType(from data: Data) -> String {
        guard data.count >= 4 else { return "image/jpeg" }
        var header = [UInt8](repeating: 0, count: 4)
        data.copyBytes(to: &header, count: 4)

        if header[0] == 0x89 && header[1] == 0x50 { return "image/png" }
        if header[0] == 0x47 && header[1] == 0x49 { return "image/gif" }
        if header[0] == 0x52 && header[1] == 0x49 { return "image/webp" }
        return "image/jpeg"
    }

    // MARK: - Process SSE Event

    @MainActor
    private func processSSEEvent(event: String, data: String) {
        guard let jsonData = data.data(using: .utf8) else { return }

        switch event {
        case "thinking":
            if let dict = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
               let step = dict["step"] as? String {
                currentThinkingStep = ThinkingStep(rawValue: step)
            }

        case "token":
            if let dict = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
               let text = dict["text"] as? String {
                // Clear thinking step once tokens start arriving
                if currentThinkingStep != nil {
                    currentThinkingStep = nil
                }
                streamingText += text
            }

        case "metadata":
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            if let metadata = try? decoder.decode(EmotionalMetadata.self, from: jsonData) {
                lastEmotionalMetadata = metadata
            }

        case "learning":
            if let dict = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any] {
                let count = dict["count"] as? Int ?? 0
                let topics = dict["topics"] as? [String] ?? []
                lastLearningCount = count
                lastLearningTopics = topics
                isLearning = true

                // Auto-dismiss after 8 seconds (give UI time to settle)
                DispatchQueue.main.asyncAfter(deadline: .now() + 8.0) { [weak self] in
                    self?.isLearning = false
                }
            }

        case "done":
            if let dict = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
               let model = dict["model"] as? String {
                streamingModelName = model
            }

        default:
            break
        }
    }

    // MARK: - Fallback (non-streaming)

    private func fallbackSendMessage(_ messageText: String, model: String) async {
        var emotionalCtx: [String: Double]? = nil
        if let emo = currentEmotionalState {
            emotionalCtx = [
                "ความสุข": emo.happiness,
                "ความมั่นใจ": emo.confidence,
                "ความรู้สึกขอบคุณ": emo.gratitude
            ]
        }

        let (angelaResponse, actualModel) = await getResponse(
            message: messageText, emotionalContext: emotionalCtx, model: model
        )

        await MainActor.run {
            streamingText = angelaResponse
            streamingModelName = actualModel
            isStreaming = false
            currentThinkingStep = nil
        }

        await saveMessage(angelaResponse, speaker: "angela", modelUsed: actualModel)
        await loadRecentMessages()
    }

    // MARK: - LLM API Call

    private func getResponse(message: String, emotionalContext: [String: Double]?, model: String) async -> (String, String) {
        do {
            let body = ChatAPIRequest(message: message, emotionalContext: emotionalContext, model: model, imageData: nil, imageMimeType: nil)
            let response: ChatAPIResponse = try await network.post("/api/chat", body: body)
            return (response.response, response.model)
        } catch {
            print("❌ LLM API error (\(model)): \(error)")
            return ("น้องขอโทษค่ะที่รัก 💜 ตอนนี้ระบบมีปัญหา ลองใหม่อีกครั้งนะคะ 🥰", model)
        }
    }

    // MARK: - Save Message

    private func saveMessage(
        _ messageText: String,
        speaker: String,
        emotionDetected: String? = nil,
        modelUsed: String? = nil
    ) async {
        do {
            let body = SaveMessageRequest(
                speaker: speaker,
                messageText: messageText,
                topic: detectTopic(messageText),
                emotionDetected: emotionDetected ?? detectEmotion(messageText, speaker: speaker),
                importanceLevel: calculateImportance(messageText),
                modelUsed: modelUsed
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

    // MARK: - Music (DJ Angela)

    func fetchFavoriteSongs(limit: Int = 20) async throws -> [Song] {
        return try await network.get("/api/music/favorites?limit=\(limit)")
    }

    func fetchOurSongs() async throws -> [Song] {
        return try await network.get("/api/music/our-songs")
    }

    func searchSongs(query: String) async throws -> [Song] {
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return try await network.get("/api/music/search?q=\(encoded)")
    }

    func getRecommendation(mood: String? = nil) async throws -> SongRecommendation {
        var path = "/api/music/recommend"
        if let mood {
            let encoded = mood.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? mood
            path += "?mood=\(encoded)"
        }
        return try await network.get(path)
    }

    func shareSong(songId: String, message: String? = nil) async throws -> MusicShareResponse {
        let body = MusicShareRequest(songId: songId, message: message)
        return try await network.post("/api/music/share", body: body)
    }

    func getPlaylistPrompt(emotionText: String?, songCount: Int = 15) async throws -> PlaylistPromptResponse {
        let body = PlaylistPromptRequest(emotionText: emotionText, songCount: songCount)
        return try await network.post("/api/music/playlist-prompt", body: body)
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
