//
//  AngelaBackendService.swift
//  AngelaNativeApp
//
//  Angela Backend API Service
//  Connects to angela_backend FastAPI server with full Angela Memory
//

import Foundation
import Combine

// MARK: - Models

struct BackendChatRequest: Codable {
    let message: String
    let speaker: String
    let model: String
    let use_rag: Bool

    enum CodingKeys: String, CodingKey {
        case message
        case speaker
        case model
        case use_rag
    }
}

struct BackendChatResponse: Codable {
    let message: String
    let speaker: String
    let emotion: String
    let timestamp: String
    let conversation_id: String
    let model: String
    let rag_enabled: Bool
    let context_metadata: ContextMetadata?

    enum CodingKeys: String, CodingKey {
        case message
        case speaker
        case emotion
        case timestamp
        case conversation_id
        case model
        case rag_enabled
        case context_metadata
    }
}

struct ContextMetadata: Codable {
    let conversations_retrieved: Int?
    let emotions_retrieved: Int?
    let learnings_retrieved: Int?

    enum CodingKeys: String, CodingKey {
        case conversations_retrieved
        case emotions_retrieved
        case learnings_retrieved
    }
}

struct HealthCheckResponse: Codable {
    let status: String
    let service: String
    let version: String
    let message: String
}

// MARK: - Service

@MainActor
class AngelaBackendService: ObservableObject {
    static let shared = AngelaBackendService()

    private let baseURL = "http://localhost:8000"
    private let session: URLSession

    @Published var isConnected = false
    @Published var lastError: String?

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: config)

        // Check connection on init
        Task {
            await checkConnection()
        }
    }

    // MARK: - Health Check

    func checkConnection() async {
        do {
            guard let url = URL(string: "\(baseURL)/") else {
                throw ServiceError.invalidURL
            }

            let (data, response) = try await session.data(from: url)

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw ServiceError.serverError(statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0)
            }

            let health = try JSONDecoder().decode(HealthCheckResponse.self, from: data)
            print("✅ Connected to \(health.service) v\(health.version)")
            print("💜 \(health.message)")

            isConnected = true
            lastError = nil

        } catch {
            print("❌ Backend connection failed: \(error)")
            isConnected = false
            lastError = error.localizedDescription
        }
    }

    // MARK: - Chat with Angela (RAG-Enhanced)

    func chat(
        message: String,
        speaker: String = "david",
        model: String = "angela:v3",
        useRAG: Bool = true
    ) async throws -> BackendChatResponse {

        guard let url = URL(string: "\(baseURL)/api/ollama/chat") else {
            throw ServiceError.invalidURL
        }

        let request = BackendChatRequest(
            message: message,
            speaker: speaker,
            model: model,
            use_rag: useRAG
        )

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)

        print("💬 Sending to Angela Backend: \(message.prefix(50))...")
        print("📊 RAG enabled: \(useRAG), Model: \(model)")

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw ServiceError.invalidResponse
        }

        if httpResponse.statusCode != 200 {
            // Try to parse error message
            if let errorString = String(data: data, encoding: .utf8) {
                print("❌ Server error: \(errorString)")
            }
            throw ServiceError.serverError(statusCode: httpResponse.statusCode)
        }

        let chatResponse = try JSONDecoder().decode(BackendChatResponse.self, from: data)

        print("✅ Angela responded (emotion: \(chatResponse.emotion))")
        if let metadata = chatResponse.context_metadata {
            print("📊 RAG retrieved: \(metadata.conversations_retrieved ?? 0) conversations, \(metadata.emotions_retrieved ?? 0) emotions")
        }

        return chatResponse
    }

    // MARK: - List Available Models

    func listModels() async throws -> [String] {
        guard let url = URL(string: "\(baseURL)/api/ollama/models") else {
            throw ServiceError.invalidURL
        }

        let (data, _) = try await session.data(from: url)

        struct ModelsResponse: Codable {
            let models: [Model]
            let total: Int

            struct Model: Codable {
                let name: String
                let size: Int
                let modified: String
            }
        }

        let response = try JSONDecoder().decode(ModelsResponse.self, from: data)
        return response.models.map { $0.name }
    }

    // MARK: - Errors

    enum ServiceError: LocalizedError {
        case invalidURL
        case invalidResponse
        case serverError(statusCode: Int)
        case networkError(Error)

        var errorDescription: String? {
            switch self {
            case .invalidURL:
                return "Invalid API URL"
            case .invalidResponse:
                return "Invalid response from server"
            case .serverError(let code):
                return "Server error (status code: \(code))"
            case .networkError(let error):
                return "Network error: \(error.localizedDescription)"
            }
        }
    }
}
