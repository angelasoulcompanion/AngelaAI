//
//  FineTuneModels.swift
//  AITop — Fine-Tune Studio Models
//

import Foundation

// MARK: - Training Methods & Engines

enum TrainingMethodType: String, CaseIterable, Codable {
    case mlxLora = "mlx_lora"
    case mlxQlora = "mlx_qlora"
    case sft = "sft"
    case dpo = "dpo"
    case orpo = "orpo"

    var displayName: String {
        switch self {
        case .mlxLora: return "MLX LoRA"
        case .mlxQlora: return "MLX QLoRA"
        case .sft: return "SFT"
        case .dpo: return "DPO"
        case .orpo: return "ORPO"
        }
    }

    var engine: String {
        switch self {
        case .mlxLora, .mlxQlora, .dpo: return "mlx"
        case .sft, .orpo: return "transformers"
        }
    }

    var icon: String {
        switch self {
        case .mlxLora: return "cpu"
        case .mlxQlora: return "memorychip"
        case .sft: return "graduationcap"
        case .dpo: return "arrow.left.arrow.right"
        case .orpo: return "chart.bar"
        }
    }
}

// MARK: - Strategy Presets

struct StrategiesResponse: Codable {
    let strategies: [FineTuneStrategy]
}

struct FineTuneStrategy: Codable, Identifiable {
    let name: String
    let epochs: Int
    let learningRate: Double
    let loraRank: Int
    let batchSize: Int
    let description: String

    var id: String { name }
}

// MARK: - Training Methods API

struct MethodsResponse: Codable {
    let methods: [TrainingMethodInfo]
}

struct TrainingMethodInfo: Codable, Identifiable {
    let id: String
    let name: String
    let engine: String
    let available: Bool
    let description: String
    let defaults: [String: AnyCodable]?
}

// MARK: - Jobs

struct JobsResponse: Codable {
    let jobs: [FineTuneJob]
    let count: Int
}

struct FineTuneJob: Codable, Identifiable {
    let id: String
    let model: String
    let datasetPath: String
    let strategy: String
    let status: String
    let epochs: Int
    let learningRate: Double
    let loraRank: Int
    let batchSize: Int
    let currentEpoch: Int
    let currentStep: Int
    let totalSteps: Int
    let loss: Double
    let lossHistory: [LossPoint]
    let startedAt: Double
    let finishedAt: Double
    let outputDir: String
    let error: String
    let elapsedSeconds: Double?
    let etaSeconds: Double?
    // New Fine-Tune Studio fields
    let trainingMethod: String?
    let engine: String?
    let config: [String: AnyCodable]?
    let bestLoss: Double?
    let lrHistory: [LRPoint]?
    let memoryPeakGb: Double?
    let estimatedDurationS: Int?
    let estimatedMemoryGb: Double?
}

struct LossPoint: Codable {
    let step: Int
    let loss: Double
    let timestamp: Double
}

struct LRPoint: Codable {
    let step: Int
    let lr: Double
    let timestamp: Double
}

// MARK: - Create Job Request (expanded)

struct CreateJobRequest: Codable {
    let model: String
    let datasetPath: String
    let trainingMethod: String
    let engine: String?
    let strategy: String?
    let config: [String: AnyCodable]?
    let epochs: Int?
    let learningRate: Double?
    let loraRank: Int?
    let batchSize: Int?
}

// MARK: - Estimation

struct EstimateRequest: Codable {
    let model: String
    let datasetPath: String
    let trainingMethod: String
    let epochs: Int
    let batchSize: Int
    let gradAccumulation: Int
    let maxSeqLength: Int
}

struct EstimateResponse: Codable {
    let duration: DurationEstimate
    let memory: MemoryEstimate
}

struct DurationEstimate: Codable {
    let estimatedSeconds: Int
    let estimatedMinutes: Double
    let estimatedHours: Double
    let formatted: String
    let confidence: String
    let totalSteps: Int
    let modelSizeB: Double
    let basis: String
}

struct MemoryEstimate: Codable {
    let minimumGb: Double
    let recommendedGb: Double
    let modelMemoryGb: Double
    let totalRamGb: Double
    let fitsCurrentMachine: Bool
    let method: String
    let modelSizeB: Double
    let isQuantized: Bool
    let notes: String
}

// MARK: - Datasets

struct DatasetsResponse: Codable {
    let datasets: [DatasetFile]
}

struct DatasetFile: Codable, Identifiable {
    let filename: String
    let path: String
    let sizeBytes: Int64?
    let lines: Int?
    // New fields
    let id: String?
    let datasetType: String?
    let status: String?
    let totalExamples: Int?
    let isValidated: Bool?
}

struct DatasetPreviewResponse: Codable {
    let columns: [String]
    let rows: [[String: AnyCodable]]
    let totalRows: Int
    let showing: Int
    let format: String
    let datasetType: String
}

struct DatasetValidationResponse: Codable {
    let isValid: Bool
    let errors: [String]
    let warnings: [String]
    let totalExamples: Int
    let datasetType: String
    let statistics: [String: AnyCodable]?
}

struct DatasetStatsResponse: Codable {
    let totalExamples: Int
    let fileSizeBytes: Int
    let format: String
    let datasetType: String
    let columns: [String]
    let avgInputLength: Int
    let avgOutputLength: Int
    let maxInputLength: Int
    let maxOutputLength: Int
}

// MARK: - Model Hub

// HFSearchResponse and HFModel are defined in ModelsModels.swift

struct HubSearchResponse: Codable {
    let models: [HubModel]
    let count: Int
}

struct HubModel: Codable, Identifiable {
    let id: String
    let name: String
    let author: String?
    let downloads: Int?
    let likes: Int?
    let pipelineTag: String?
    let tags: [String]?
    let lastModified: String?
}

struct PopularModelsResponse: Codable {
    let models: [PopularModel]
}

struct PopularModel: Codable, Identifiable {
    let id: String
    let name: String
    let sizeB: Double
    let engine: String
    let recommended: Bool?
}

struct LocalModelsResponse: Codable {
    let models: [LocalModel]
    let count: Int
}

struct LocalModel: Codable, Identifiable {
    let id: String?
    let name: String
    let modelType: String
    let hfModelId: String?
    let filePath: String?
    let fileSizeMb: Double?
    let status: String?
    let parentModelId: String?
    let trainingJobId: String?
    let ollamaName: String?
}

struct DownloadRequest: Codable {
    let hfModelId: String
    let name: String?
}

struct ImportOllamaRequest: Codable {
    let adapterPath: String
    let baseModel: String
    let ollamaName: String
}

// MARK: - Export Batches (History)

struct BatchesResponse: Codable {
    let batches: [ExportBatch]
    let count: Int
}

struct ExportBatch: Codable, Identifiable {
    let id: String
    let batchName: String
    let exportType: String
    let status: String
    let outputPath: String?
    let previewPath: String?
    let totalPairs: Int
    let filteredOut: Int
    let avgQuality: Double?
    let fileSizeKb: Double?
    let sourceDistribution: [String: Int]?
    let machine: String?
    let createdAt: String?
    let usedInJobs: [String]?
}

// MARK: - Export Preview (in-app)

struct ExportPreviewResponse: Codable {
    let rows: [ExportPreviewRow]
    let total: Int
    let offset: Int
    let limit: Int
    let showing: Int
}

struct ExportPreviewRow: Codable, Identifiable {
    let messages: [ExportMessage]?
    let metadata: ExportMetadata?

    var id: String {
        let user = messages?.first(where: { $0.role == "user" })?.content ?? ""
        return String(user.prefix(50))
    }
}

struct ExportMessage: Codable {
    let role: String
    let content: String
}

struct ExportMetadata: Codable {
    let topic: String?
    let emotion: String?
    let qualityScore: Double?
    let importance: Int?
    let source: String?
    let emotionalWeight: Double?
}

// MARK: - Dataset Export

struct ExportDatasetRequest: Codable {
    let days: Int
    let minQuality: Double
    let minImportance: Int
    let maxExamples: Int
    let includeKnowledge: Bool
    let includeCoreMemories: Bool
}

struct ExportDatasetResponse: Codable {
    let outputPath: String
    let previewPath: String
    let totalPairs: Int
    let filteredOut: Int
    let avgQuality: Double
    let avgUserLength: Int
    let avgAngelaLength: Int
    let fileSizeKb: Double
    let exportTimeS: Double
    let topTopics: [TopicCount]?
    let qualityDistribution: [String: Int]?
    let sourceDistribution: [String: Int]?
}

struct TopicCount: Codable {
    let topic: String
    let count: Int
}

// MARK: - AnyCodable (flexible JSON values)

struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            value = NSNull()
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map(\.value)
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues(\.value)
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case is NSNull:
            try container.encodeNil()
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}
