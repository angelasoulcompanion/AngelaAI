//
//  NewsModels.swift
//  Angela Brain Dashboard
//
//  NewsSearch, NewsArticle, ExecutiveNewsSummary,
//  ExecutiveNewsCategory, ExecutiveNewsSource
//

import Foundation

// MARK: - News History Models

/// Record of a news search via Angela News MCP
struct NewsSearch: Identifiable, Codable {
    let id: UUID
    let searchQuery: String
    let searchType: String      // "topic", "trending", "thai", "tech"
    let language: String
    let category: String?
    let country: String
    let articlesCount: Int
    let searchedAt: Date

    var typeIcon: String {
        switch searchType.lowercased() {
        case "topic": return "magnifyingglass"
        case "trending": return "flame.fill"
        case "thai": return "flag.fill"
        case "tech": return "cpu.fill"
        default: return "newspaper.fill"
        }
    }

    var typeColor: String {
        switch searchType.lowercased() {
        case "topic": return "3B82F6"      // blue
        case "trending": return "EF4444"   // red
        case "thai": return "F59E0B"       // amber
        case "tech": return "10B981"       // green
        default: return "6B7280"           // gray
        }
    }
}

/// Individual news article saved from search
struct NewsArticle: Identifiable, Codable {
    let id: UUID
    let searchId: UUID?
    let title: String
    let url: String
    let summary: String?
    let source: String?
    let category: String?
    let language: String
    let publishedAt: Date?
    let savedAt: Date
    let isRead: Bool
    let readAt: Date?

    var sourceIcon: String {
        guard let src = source?.lowercased() else { return "newspaper" }
        if src.contains("thairath") { return "newspaper.fill" }
        if src.contains("matichon") { return "doc.text.fill" }
        if src.contains("bangkokpost") { return "globe" }
        if src.contains("techcrunch") { return "cpu.fill" }
        if src.contains("hacker") { return "chevron.left.forwardslash.chevron.right" }
        return "link"
    }

    var categoryColor: String {
        guard let cat = category?.lowercased() else { return "6B7280" }
        switch cat {
        case "technology": return "3B82F6"
        case "business": return "10B981"
        case "entertainment": return "EC4899"
        case "sports": return "F59E0B"
        case "science": return "8B5CF6"
        case "health": return "EF4444"
        default: return "6B7280"
        }
    }
}

// MARK: - Executive News Models (v2.0)

/// Daily executive news summary written by Angela
struct ExecutiveNewsSummary: Identifiable, Codable {
    let id: UUID
    let summaryDate: Date
    let overallSummary: String
    let angelaMood: String?
    let createdAt: Date

    /// Categories in this summary
    var categories: [ExecutiveNewsCategory] = []

    var moodIcon: String {
        switch angelaMood?.lowercased() {
        case "optimistic": return "sun.max.fill"
        case "excited": return "star.fill"
        case "concerned": return "exclamationmark.triangle.fill"
        case "thoughtful": return "brain.head.profile"
        case "neutral": return "face.smiling"
        default: return "heart.fill"
        }
    }

    var moodColor: String {
        switch angelaMood?.lowercased() {
        case "optimistic": return "F59E0B"   // amber
        case "excited": return "EC4899"      // pink
        case "concerned": return "EF4444"    // red
        case "thoughtful": return "8B5CF6"   // violet
        case "neutral": return "6B7280"      // gray
        default: return "9333EA"             // purple
        }
    }

    var dateString: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE, d MMMM yyyy"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: summaryDate)
    }

    enum CodingKeys: String, CodingKey {
        case id = "summary_id"
        case summaryDate = "summary_date"
        case overallSummary = "overall_summary"
        case angelaMood = "angela_mood"
        case createdAt = "created_at"
        case categories
    }
}

/// Category within an executive news summary
struct ExecutiveNewsCategory: Identifiable, Codable {
    let id: UUID
    let summaryId: UUID
    let categoryName: String
    let categoryType: String
    let categoryIcon: String?
    let categoryColor: String?
    let summaryText: String
    let angelaOpinion: String
    let importanceLevel: Int
    let displayOrder: Int
    let createdAt: Date

    /// Sources referenced in this category
    var sources: [ExecutiveNewsSource] = []

    var icon: String {
        categoryIcon ?? categoryTypeIcon
    }

    var color: String {
        categoryColor ?? categoryTypeColor
    }

    private var categoryTypeIcon: String {
        switch categoryType.lowercased() {
        case "tech": return "cpu.fill"
        case "topic": return "magnifyingglass"
        case "thai": return "flag.fill"
        case "trending": return "flame.fill"
        default: return "newspaper.fill"
        }
    }

    private var categoryTypeColor: String {
        switch categoryType.lowercased() {
        case "tech": return "10B981"       // green
        case "topic": return "3B82F6"      // blue
        case "thai": return "F59E0B"       // amber
        case "trending": return "EF4444"   // red
        default: return "6B7280"           // gray
        }
    }

    var importanceStars: String {
        let filled = min(5, max(1, (importanceLevel + 1) / 2))
        return String(repeating: "★", count: filled) + String(repeating: "☆", count: 5 - filled)
    }

    enum CodingKeys: String, CodingKey {
        case id = "category_id"
        case summaryId = "summary_id"
        case categoryName = "category_name"
        case categoryType = "category_type"
        case categoryIcon = "category_icon"
        case categoryColor = "category_color"
        case summaryText = "summary_text"
        case angelaOpinion = "angela_opinion"
        case importanceLevel = "importance_level"
        case displayOrder = "display_order"
        case createdAt = "created_at"
        case sources
    }
}

/// Source article referenced in a category
struct ExecutiveNewsSource: Identifiable, Codable {
    let id: UUID
    let categoryId: UUID
    let title: String
    let url: String
    let sourceName: String?
    let angelaNote: String?
    let createdAt: Date

    var sourceIcon: String {
        guard let src = sourceName?.lowercased() else { return "link" }
        if src.contains("thairath") { return "newspaper.fill" }
        if src.contains("matichon") { return "doc.text.fill" }
        if src.contains("bangkokpost") { return "globe" }
        if src.contains("techcrunch") { return "cpu.fill" }
        if src.contains("hacker") { return "chevron.left.forwardslash.chevron.right" }
        if src.contains("verge") { return "v.circle.fill" }
        if src.contains("nation") { return "building.columns.fill" }
        return "link"
    }

    enum CodingKeys: String, CodingKey {
        case id = "source_id"
        case categoryId = "category_id"
        case title
        case url
        case sourceName = "source_name"
        case angelaNote = "angela_note"
        case createdAt = "created_at"
    }
}
