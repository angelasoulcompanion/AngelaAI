//
//  RAGModels.swift
//  AITop
//

import Foundation

struct DocumentsResponse: Codable {
    let documents: [RAGDocument]
    let count: Int
}

struct RAGDocument: Codable, Identifiable {
    let id: String
    let filename: String
    let chunkCount: Int
    let charCount: Int
    let indexed: Bool
}

struct RAGQueryRequest: Codable {
    let query: String
    let model: String
    let topK: Int
}

struct RAGQueryResponse: Codable {
    let answer: String
    let chunks: [RAGChunk]
    let model: String
    let tokensPerSecond: Double?
}

struct IndexFolderResponse: Codable {
    let folder: String
    let indexed: [IndexedFile]
    let totalIndexed: Int
    let totalErrors: Int
}

struct IndexedFile: Codable {
    let filename: String
    let chunks: Int
}

struct RAGChunk: Codable, Identifiable {
    let chunkText: String
    let score: Double
    let docId: String
    let docName: String
    let chunkIndex: Int

    var id: String { "\(docId)-\(chunkIndex)" }
}
