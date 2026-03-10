//
//  FineTuneModels.swift
//  AITop
//

import Foundation

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
}

struct LossPoint: Codable {
    let step: Int
    let loss: Double
    let timestamp: Double
}

struct CreateJobRequest: Codable {
    let model: String
    let datasetPath: String
    let strategy: String
}

struct DatasetsResponse: Codable {
    let datasets: [DatasetFile]
}

struct DatasetFile: Codable, Identifiable {
    let filename: String
    let path: String
    let sizeBytes: Int64

    var id: String { filename }
}
