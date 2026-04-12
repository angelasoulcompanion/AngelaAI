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
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(body)

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

    func getTrainingMethods() async throws -> MethodsResponse {
        try await get("/finetune/methods")
    }

    func getStrategies() async throws -> StrategiesResponse {
        try await get("/finetune/strategies")
    }

    func estimateTraining(model: String, datasetPath: String, method: String = "mlx_lora",
                          epochs: Int = 3, batchSize: Int = 2, gradAccumulation: Int = 4,
                          maxSeqLength: Int = 1024) async throws -> EstimateResponse {
        let body = EstimateRequest(model: model, datasetPath: datasetPath, trainingMethod: method,
                                   epochs: epochs, batchSize: batchSize, gradAccumulation: gradAccumulation,
                                   maxSeqLength: maxSeqLength)
        return try await post("/finetune/estimate", body: body)
    }

    func getJobs() async throws -> JobsResponse {
        try await get("/finetune/jobs")
    }

    func getJobStatus(id: String) async throws -> FineTuneJob {
        try await get("/finetune/jobs/\(id)")
    }

    func createJob(model: String, datasetPath: String, trainingMethod: String = "mlx_lora",
                   engine: String? = nil, strategy: String? = nil, config: [String: AnyCodable]? = nil,
                   epochs: Int? = nil, learningRate: Double? = nil,
                   loraRank: Int? = nil, batchSize: Int? = nil) async throws -> FineTuneJob {
        let body = CreateJobRequest(model: model, datasetPath: datasetPath, trainingMethod: trainingMethod,
                                    engine: engine, strategy: strategy, config: config,
                                    epochs: epochs, learningRate: learningRate,
                                    loraRank: loraRank, batchSize: batchSize)
        return try await post("/finetune/jobs", body: body)
    }

    func startJob(id: String) async throws -> FineTuneJob {
        struct Empty: Encodable {}
        return try await post("/finetune/jobs/\(id)/start", body: Empty(), timeout: 10)
    }

    func cancelJob(id: String) async throws {
        struct Empty: Encodable {}
        let _: [String: AnyCodable] = try await post("/finetune/jobs/\(id)/cancel", body: Empty())
    }

    // MARK: - Model Hub

    func searchHubModels(query: String, task: String = "text-generation", limit: Int = 20) async throws -> HubSearchResponse {
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return try await get("/models/hub/search?query=\(encoded)&task=\(task)&limit=\(limit)")
    }

    func getPopularModels() async throws -> PopularModelsResponse {
        try await get("/models/hub/popular")
    }

    func getHubModelInfo(modelId: String) async throws -> HubModel {
        let encoded = modelId.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? modelId
        return try await get("/models/hub/info/\(encoded)")
    }

    func downloadHubModel(hfModelId: String, name: String? = nil) async throws -> LocalModel {
        let body = DownloadRequest(hfModelId: hfModelId, name: name)
        return try await post("/models/hub/download", body: body, timeout: 600)
    }

    func importToOllama(adapterPath: String, baseModel: String, ollamaName: String) async throws -> [String: AnyCodable] {
        let body = ImportOllamaRequest(adapterPath: adapterPath, baseModel: baseModel, ollamaName: ollamaName)
        return try await post("/models/hub/import-ollama", body: body, timeout: 600)
    }

    func getLocalModels() async throws -> LocalModelsResponse {
        try await get("/models/local")
    }

    // MARK: - Dataset Management

    func validateDataset(id: String) async throws -> DatasetValidationResponse {
        struct Empty: Encodable {}
        return try await post("/finetune/datasets/\(id)/validate", body: Empty())
    }

    func previewDataset(id: String, limit: Int = 10) async throws -> DatasetPreviewResponse {
        try await get("/finetune/datasets/\(id)/preview?limit=\(limit)")
    }

    func getDatasetStats(id: String) async throws -> DatasetStatsResponse {
        try await get("/finetune/datasets/\(id)/stats")
    }

    func previewExportedFile(path: String, offset: Int = 0, limit: Int = 20) async throws -> ExportPreviewResponse {
        let encoded = path.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? path
        return try await get("/finetune/datasets/export/preview?path=\(encoded)&offset=\(offset)&limit=\(limit)")
    }

    func getExportBatches() async throws -> BatchesResponse {
        try await get("/finetune/batches")
    }

    func exportDataset(days: Int = 730, minQuality: Double = 4.0, maxExamples: Int = 10000,
                       includeKnowledge: Bool = true, includeCoreMemories: Bool = true) async throws -> ExportDatasetResponse {
        let body = ExportDatasetRequest(days: days, minQuality: minQuality, minImportance: 1,
                                        maxExamples: maxExamples, includeKnowledge: includeKnowledge,
                                        includeCoreMemories: includeCoreMemories)
        return try await post("/finetune/datasets/export", body: body, timeout: 120)
    }

    // MARK: - RAG

    func getDocuments() async throws -> DocumentsResponse {
        try await get("/rag/documents")
    }

    func queryRAG(query: String, model: String, topK: Int = 5) async throws -> RAGQueryResponse {
        let body = RAGQueryRequest(query: query, model: model, topK: topK)
        return try await post("/rag/query", body: body, timeout: 120)
    }

    func deleteRAGDocument(id: String) async throws {
        try await delete("/rag/documents/\(id)")
    }

    func indexRAGFolder(path: String) async throws -> IndexFolderResponse {
        struct Req: Encodable {
            let folder_path: String // snake_case to match Python
        }
        return try await post("/rag/documents/index-folder", body: Req(folder_path: path), timeout: 300)
    }

    // MARK: - Fine-Tune Datasets

    func getDatasets() async throws -> DatasetsResponse {
        try await get("/finetune/datasets")
    }

    func uploadDataset(fileURL: URL) async throws -> DatasetFile {
        let boundary = UUID().uuidString
        let fileData = try Data(contentsOf: fileURL)
        let filename = fileURL.lastPathComponent

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        let url = URL(string: "\(APIConfig.apiBaseURL)/finetune/datasets/upload")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        request.timeoutInterval = 60

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResp = response as? HTTPURLResponse, (200...299).contains(httpResp.statusCode) else {
            let msg = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError((response as? HTTPURLResponse)?.statusCode ?? 0, msg)
        }
        return try decoder.decode(DatasetFile.self, from: data)
    }
}
