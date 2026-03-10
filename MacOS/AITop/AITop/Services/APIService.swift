//
//  APIService.swift
//  AITop
//
//  Generic REST client for AI TOP backend.
//

import Foundation

enum APIError: LocalizedError {
    case httpError(Int, String)
    case decodingError(String)
    case networkError(String)

    var errorDescription: String? {
        switch self {
        case .httpError(let code, let msg): return "HTTP \(code): \(msg)"
        case .decodingError(let msg): return "Decoding: \(msg)"
        case .networkError(let msg): return "Network: \(msg)"
        }
    }
}

class APIService: ObservableObject {
    static let shared = APIService()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        d.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let str = try container.decode(String.self)
            // Try ISO8601 formats
            let formatters: [DateFormatter] = {
                let f1 = DateFormatter()
                f1.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSZ"
                let f2 = DateFormatter()
                f2.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
                let f3 = DateFormatter()
                f3.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
                return [f1, f2, f3]
            }()
            for fmt in formatters {
                if let date = fmt.date(from: str) { return date }
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date: \(str)")
        }
        return d
    }()

    private init() {}

    // MARK: - Generic Methods

    func get<T: Decodable>(_ path: String, timeout: TimeInterval = 30) async throws -> T {
        let url = URL(string: "\(APIConfig.apiBaseURL)\(path)")!
        var request = URLRequest(url: url)
        request.timeoutInterval = timeout

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResp = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid response")
        }
        guard httpResp.statusCode == 200 else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError(httpResp.statusCode, body)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError("\(error)")
        }
    }

    func post<T: Decodable, B: Encodable>(_ path: String, body: B, timeout: TimeInterval = 60) async throws -> T {
        let url = URL(string: "\(APIConfig.apiBaseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = timeout
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResp = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid response")
        }
        guard (200...299).contains(httpResp.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError(httpResp.statusCode, body)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError("\(error)")
        }
    }

    func delete(_ path: String) async throws {
        let url = URL(string: "\(APIConfig.apiBaseURL)\(path)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResp = response as? HTTPURLResponse else {
            throw APIError.networkError("Invalid response")
        }
        guard httpResp.statusCode == 200 else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError(httpResp.statusCode, body)
        }
    }

    // MARK: - Dashboard

    func getDashboard() async throws -> DashboardResponse {
        try await get("/dashboard")
    }

    func getHardwareStats() async throws -> HardwareStats {
        try await get("/dashboard/hardware")
    }

    // MARK: - Models

    func getModels() async throws -> ModelsResponse {
        try await get("/models")
    }

    func searchHuggingFace(query: String, task: String = "text-generation") async throws -> HFSearchResponse {
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return try await get("/models/search/hf?query=\(encoded)&task=\(task)")
    }

    // MARK: - Chat

    func chat(model: String, messages: [ChatMessage], system: String? = nil, temperature: Double = 0.7, maxTokens: Int = 2048) async throws -> ChatResponse {
        let body = ChatRequest(model: model, messages: messages, system: system, temperature: temperature, maxTokens: maxTokens, stream: false)
        return try await post("/chat", body: body, timeout: 120)
    }

    // MARK: - Fine-Tune

    func getStrategies() async throws -> StrategiesResponse {
        try await get("/finetune/strategies")
    }

    func getJobs() async throws -> JobsResponse {
        try await get("/finetune/jobs")
    }

    func getJobStatus(id: String) async throws -> FineTuneJob {
        try await get("/finetune/jobs/\(id)")
    }

    func createJob(model: String, datasetPath: String, strategy: String) async throws -> FineTuneJob {
        let body = CreateJobRequest(model: model, datasetPath: datasetPath, strategy: strategy)
        return try await post("/finetune/jobs", body: body)
    }

    func startJob(id: String) async throws -> FineTuneJob {
        struct Empty: Encodable {}
        return try await post("/finetune/jobs/\(id)/start", body: Empty(), timeout: 10)
    }

    // MARK: - RAG

    func getDocuments() async throws -> DocumentsResponse {
        try await get("/rag/documents")
    }

    func queryRAG(query: String, model: String, topK: Int = 5) async throws -> RAGQueryResponse {
        let body = RAGQueryRequest(query: query, model: model, topK: topK)
        return try await post("/rag/query", body: body, timeout: 120)
    }
}
