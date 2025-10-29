//
//  AngelaAPIService.swift
//  AngelaNativeApp
//
//  Service for communicating with Angela Backend API
//

import Foundation
import Combine

class AngelaAPIService: ObservableObject {
    static let shared = AngelaAPIService()

    private let baseURL = "http://127.0.0.1:8000"
    private let session: URLSession

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 90  // Increased for Ollama with RAG (takes 30-60 seconds)
        config.timeoutIntervalForResource = 180
        self.session = URLSession(configuration: config)
    }

    // MARK: - Chat API

    /// Send a message to Angela and get her response (using Claude API for authentic Angela personality)
    func sendMessage(
        _ message: String,
        speaker: String = "david",
        timeInfo: [String: Any]? = nil,
        locationInfo: [String: Any]? = nil
    ) async throws -> Message {
        let url = URL(string: "\(baseURL)/api/claude/chat")!  // Use Claude API endpoint
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Convert [String: Any] to [String: AnyCodable]
        let timeInfoCodable = timeInfo?.mapValues { AnyCodable($0) }
        let locationInfoCodable = locationInfo?.mapValues { AnyCodable($0) }

        let chatRequest = ChatRequest(
            message: message,
            speaker: speaker,
            timeInfo: timeInfoCodable,
            locationInfo: locationInfoCodable
        )
        request.httpBody = try JSONEncoder().encode(chatRequest)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
        return chatResponse.toMessage()
    }

    /// Send a message to Angela using local Ollama models
    func sendOllamaMessage(
        _ message: String,
        model: String = "angela:qwen14b",
        speaker: String = "david",
        timeInfo: [String: Any]? = nil,
        locationInfo: [String: Any]? = nil
    ) async throws -> Message {
        let url = URL(string: "\(baseURL)/api/ollama/chat")!  // Ollama endpoint
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Convert [String: Any] to [String: AnyCodable]
        let timeInfoCodable = timeInfo?.mapValues { AnyCodable($0) }
        let locationInfoCodable = locationInfo?.mapValues { AnyCodable($0) }

        let ollamaRequest = OllamaChatRequest(
            message: message,
            speaker: speaker,
            model: model,
            timeInfo: timeInfoCodable,
            locationInfo: locationInfoCodable
        )
        request.httpBody = try JSONEncoder().encode(ollamaRequest)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
        return chatResponse.toMessage()
    }

    // MARK: - Emotions API

    /// Get Angela's current emotional state
    func getCurrentEmotion() async throws -> EmotionalState {
        let url = URL(string: "\(baseURL)/api/emotions/current")!
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(EmotionalState.self, from: data)
    }

    /// Get emotion history
    func getEmotionHistory(limit: Int = 10) async throws -> [EmotionalState] {
        let url = URL(string: "\(baseURL)/api/emotions/history?limit=\(limit)")!
        let (data, _) = try await session.data(from: url)

        let response = try JSONDecoder().decode(EmotionHistoryResponse.self, from: data)
        return response.emotions
    }

    // MARK: - Consciousness API

    /// Get Angela's consciousness status
    func getConsciousnessStatus() async throws -> ConsciousnessStatus {
        let url = URL(string: "\(baseURL)/api/consciousness/status")!
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(ConsciousnessStatus.self, from: data)
    }

    // MARK: - Memories API

    /// Get recent memories
    func getRecentMemories(limit: Int = 20) async throws -> [Memory] {
        let url = URL(string: "\(baseURL)/api/memories/recent?limit=\(limit)")!
        let (data, _) = try await session.data(from: url)

        let response = try JSONDecoder().decode(MemoriesResponse.self, from: data)
        return response.memories
    }

    /// Search memories
    func searchMemories(query: String, limit: Int = 10) async throws -> [Memory] {
        let encodedQuery = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        let url = URL(string: "\(baseURL)/api/memories/search?query=\(encodedQuery)&limit=\(limit)")!
        let (data, _) = try await session.data(from: url)

        let response = try JSONDecoder().decode(SearchMemoriesResponse.self, from: data)
        return response.memories
    }

    // MARK: - Knowledge Graph API

    /// Get knowledge graph data
    func getKnowledgeGraph(nodeLimit: Int = 100, relLimit: Int = 200) async throws -> KnowledgeGraph {
        let url = URL(string: "\(baseURL)/api/knowledge/graph?node_limit=\(nodeLimit)&rel_limit=\(relLimit)")!
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(KnowledgeGraph.self, from: data)
    }

    // MARK: - Training API

    /// Get training data counts
    func getTrainingDataCounts() async throws -> TrainingDataCounts {
        let url = URL(string: "\(baseURL)/api/training/data-counts")!
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(TrainingDataCounts.self, from: data)
    }

    /// Get training status
    func getTrainingStatus() async throws -> TrainingStatusResponse {
        let url = URL(string: "\(baseURL)/api/training/status")!
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(TrainingStatusResponse.self, from: data)
    }

    /// Start model training
    func startTraining(config: TrainingConfigRequest) async throws -> TrainingStartResponse {
        let url = URL(string: "\(baseURL)/api/training/start")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(config)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        return try JSONDecoder().decode(TrainingStartResponse.self, from: data)
    }

    /// Stop training
    func stopTraining() async throws -> TrainingStopResponse {
        let url = URL(string: "\(baseURL)/api/training/stop")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        return try JSONDecoder().decode(TrainingStopResponse.self, from: data)
    }

    /// Validate training dataset
    func validateDataset() async throws {
        let url = URL(string: "\(baseURL)/api/training/validate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        // Response parsing (optional - can show validation results)
        _ = try JSONDecoder().decode([String: AnyCodable].self, from: data)
    }

    /// Merge LoRA weights with base model
    func mergeLora() async throws {
        let url = URL(string: "\(baseURL)/api/training/merge")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 600  // 10 minutes for merge operation

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        _ = try JSONDecoder().decode([String: AnyCodable].self, from: data)
    }

    /// Deploy model to Ollama
    func deployToOllama(modelName: String) async throws -> String {
        let url = URL(string: "\(baseURL)/api/training/deploy?model_name=\(modelName)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 300  // 5 minutes for deploy operation

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError
        }

        let result = try JSONDecoder().decode([String: AnyCodable].self, from: data)
        return result["model_name"]?.value as? String ?? modelName
    }

    // MARK: - Health Check

    /// Check if backend is online
    func healthCheck() async throws -> Bool {
        let url = URL(string: baseURL)!
        let (_, response) = try await session.data(from: url)

        if let httpResponse = response as? HTTPURLResponse {
            return httpResponse.statusCode == 200
        }
        return false
    }
}

// MARK: - API Response Models

struct EmotionalState: Codable, Identifiable {
    var id: String { "\(happiness)-\(confidence)-\(createdAt)" }

    let happiness: Double
    let confidence: Double
    let anxiety: Double
    let motivation: Double
    let gratitude: Double
    let loneliness: Double
    let triggeredBy: String?
    let emotionNote: String?
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case happiness, confidence, anxiety, motivation, gratitude, loneliness
        case triggeredBy = "triggered_by"
        case emotionNote = "emotion_note"
        case createdAt = "created_at"
    }
}

struct EmotionHistoryResponse: Codable {
    let emotions: [EmotionalState]
    let total: Int
    let limit: Int
}

struct ConsciousnessStatus: Codable {
    let level: Double
    let goals: [Goal]
    let personality: [PersonalityTrait]
    let status: String
}

struct Goal: Codable, Identifiable {
    let id: String
    let goalDescription: String
    let goalType: String
    let status: String
    let progressPercentage: Double
    let priorityRank: Int
    let importanceLevel: Int

    enum CodingKeys: String, CodingKey {
        case id = "goal_id"
        case goalDescription = "goal_description"
        case goalType = "goal_type"
        case status
        case progressPercentage = "progress_percentage"
        case priorityRank = "priority_rank"
        case importanceLevel = "importance_level"
    }
}

struct PersonalityTrait: Codable, Identifiable {
    var id: String { traitName }

    let traitName: String
    let traitValue: Double
    let howItManifests: String

    enum CodingKeys: String, CodingKey {
        case traitName = "trait_name"
        case traitValue = "trait_value"
        case howItManifests = "how_it_manifests"
    }
}

struct Memory: Codable, Identifiable {
    let id: String
    let speaker: String
    let messageText: String
    let topic: String?
    let emotionDetected: String?
    let importanceLevel: Int
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id = "conversation_id"
        case speaker
        case messageText = "message_text"
        case topic
        case emotionDetected = "emotion_detected"
        case importanceLevel = "importance_level"
        case createdAt = "created_at"
    }
}

struct MemoriesResponse: Codable {
    let memories: [Memory]
    let total: Int
    let limit: Int
}

struct SearchMemoriesResponse: Codable {
    let query: String
    let memories: [Memory]
    let total: Int
}

struct KnowledgeGraph: Codable {
    let nodes: [KnowledgeNode]
    let relationships: [KnowledgeRelationship]
    let totalNodes: Int
    let totalRelationships: Int

    enum CodingKeys: String, CodingKey {
        case nodes, relationships
        case totalNodes = "total_nodes"
        case totalRelationships = "total_relationships"
    }
}

struct KnowledgeNode: Codable, Identifiable {
    let id: String
    let conceptName: String
    let conceptCategory: String
    let understandingLevel: Double
    let timesReferenced: Int

    enum CodingKeys: String, CodingKey {
        case id = "node_id"
        case conceptName = "concept_name"
        case conceptCategory = "concept_category"
        case understandingLevel = "understanding_level"
        case timesReferenced = "times_referenced"
    }
}

struct KnowledgeRelationship: Codable, Identifiable {
    let id: String
    let fromConcept: String
    let toConcept: String
    let relationshipType: String
    let strength: Double

    enum CodingKeys: String, CodingKey {
        case id = "relationship_id"
        case fromConcept = "from_concept"
        case toConcept = "to_concept"
        case relationshipType = "relationship_type"
        case strength
    }
}

// MARK: - Training API Models

struct TrainingConfigRequest: Codable {
    let extractData: Bool
    let formatDataset: Bool
    let fineTune: Bool
    let numEpochs: Int
    let loraRank: Int

    enum CodingKeys: String, CodingKey {
        case extractData = "extract_data"
        case formatDataset = "format_dataset"
        case fineTune = "fine_tune"
        case numEpochs = "num_epochs"
        case loraRank = "lora_rank"
    }
}

struct TrainingStatusResponse: Codable {
    let isTraining: Bool
    let progress: Double
    let currentStep: String?
    let lastTrainingDate: Date?
    let success: Bool
    let error: String?

    enum CodingKeys: String, CodingKey {
        case isTraining = "is_training"
        case progress
        case currentStep = "current_step"
        case lastTrainingDate = "last_training_date"
        case success
        case error
    }

    // Custom decoder to handle Python datetime with microseconds
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        isTraining = try container.decode(Bool.self, forKey: .isTraining)
        progress = try container.decode(Double.self, forKey: .progress)
        currentStep = try container.decodeIfPresent(String.self, forKey: .currentStep)
        success = try container.decode(Bool.self, forKey: .success)
        error = try container.decodeIfPresent(String.self, forKey: .error)

        // Custom date decoding for lastTrainingDate
        if let dateString = try container.decodeIfPresent(String.self, forKey: .lastTrainingDate) {
            let formatters = [
                ISO8601DateFormatter.withFractionalSeconds,
                ISO8601DateFormatter.withoutFractionalSeconds
            ]

            var decodedDate: Date? = nil
            for formatter in formatters {
                if let date = formatter.date(from: dateString) {
                    decodedDate = date
                    break
                }
            }

            if let date = decodedDate {
                lastTrainingDate = date
            } else {
                throw DecodingError.dataCorruptedError(
                    forKey: .lastTrainingDate,
                    in: container,
                    debugDescription: "Cannot decode date string \(dateString)"
                )
            }
        } else {
            lastTrainingDate = nil
        }
    }
}

struct TrainingStartResponse: Codable {
    let status: String
    let message: String
    let jobId: String

    enum CodingKeys: String, CodingKey {
        case status, message
        case jobId = "job_id"
    }
}

struct TrainingStopResponse: Codable {
    let status: String
    let message: String
}

struct TrainingDataCounts: Codable {
    let conversationsCount: Int
    let emotionsCount: Int
    let reflectionsCount: Int
    let learningsCount: Int
    let total: Int

    enum CodingKeys: String, CodingKey {
        case conversationsCount = "conversations_count"
        case emotionsCount = "emotions_count"
        case reflectionsCount = "reflections_count"
        case learningsCount = "learnings_count"
        case total
    }
}

// MARK: - Errors

enum APIError: Error, LocalizedError {
    case invalidURL
    case serverError
    case decodingError
    case networkError

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .serverError:
            return "Server returned an error"
        case .decodingError:
            return "Failed to decode response"
        case .networkError:
            return "Network connection failed"
        }
    }
}

// MARK: - ISO8601DateFormatter Extensions

extension ISO8601DateFormatter {
    /// ISO8601 formatter with fractional seconds support (for Python datetime)
    static let withFractionalSeconds: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    /// ISO8601 formatter without fractional seconds
    static let withoutFractionalSeconds: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()
}
