//
//  RAGModels.swift
//  AITop
//
//  Read-only stats for Angela's domain RAG knowledge bases (rag_* on Supabase).
//

import Foundation

struct AngelaRAGStats: Codable {
    let embedModel: String
    let embedDims: Int
    let totalChunks: Int
    let totalDomains: Int
    let totalSources: Int
    let totalTokens: Int
    let totalEmbedded: Int
    let lastUpdated: String?
    let domains: [RAGDomain]
}

struct RAGDomain: Codable, Identifiable {
    let key: String
    let table: String
    let label: String
    let chunks: Int
    let embedded: Int
    let sources: Int
    let tokens: Int
    let updatedAt: String?
    let languages: [RAGLanguage]
    let topSources: [RAGTopSource]

    var id: String { key }
}

struct RAGLanguage: Codable, Identifiable {
    let language: String
    let count: Int

    var id: String { language }
}

struct RAGTopSource: Codable, Identifiable {
    let source: String
    let count: Int

    var id: String { source }
}
