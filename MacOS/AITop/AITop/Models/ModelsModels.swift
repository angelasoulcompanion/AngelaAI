//
//  ModelsModels.swift
//  AITop
//

import Foundation

struct ModelsResponse: Codable {
    let models: [OllamaModel]
    let count: Int
}

struct OllamaModel: Codable, Identifiable {
    let name: String
    let model: String
    let sizeBytes: Int64
    let sizeGb: Double
    let modifiedAt: String
    let digest: String
    let family: String
    let parameterSize: String
    let quantization: String

    var id: String { name }
}

struct HFSearchResponse: Codable {
    let models: [HFModel]
    let count: Int
}

struct HFModel: Codable, Identifiable {
    let id: String
    let author: String
    let downloads: Int
    let likes: Int
    let tags: [String]
    let pipelineTag: String
    let lastModified: String
}
