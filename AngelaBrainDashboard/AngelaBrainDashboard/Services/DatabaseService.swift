//
//  DatabaseService.swift
//  Angela Brain Dashboard
//
//  REST API Client - Connects to FastAPI backend (Neon Cloud)
//
//  Architecture:
//    SwiftUI → DatabaseService → BackendManager → FastAPI → Neon Cloud
//
//  Updated: 2026-01-08 (REST API version)
//

import Foundation
import Combine

// MARK: - Database Service (REST API Version)

class DatabaseService: ObservableObject {
    static let shared = DatabaseService()

    @Published var isConnected = false
    @Published var isConnecting = true  // Start in connecting state
    @Published var errorMessage: String?

    private let baseURL = "http://127.0.0.1:8765/api"
    private let decoder: JSONDecoder

    private init() {
        // Configure decoder for API responses
        decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            // Try various date formats (with and without timezone)
            let formatters: [DateFormatter] = [
                // ISO8601 with timezone offset (+00:00 format) using XXX
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXX"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    return f
                }(),
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    return f
                }(),
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ssXXX"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    return f
                }(),
                // With timezone ZZZZZ format
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSZZZZZ"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    return f
                }(),
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSZZZZZ"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    return f
                }(),
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZZZZZ"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    return f
                }(),
                // Without timezone (from API)
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    f.timeZone = TimeZone(identifier: "UTC")
                    return f
                }(),
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    f.timeZone = TimeZone(identifier: "UTC")
                    return f
                }(),
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    f.timeZone = TimeZone(identifier: "UTC")
                    return f
                }(),
                // Date only
                {
                    let f = DateFormatter()
                    f.dateFormat = "yyyy-MM-dd"
                    f.locale = Locale(identifier: "en_US_POSIX")
                    f.timeZone = TimeZone(identifier: "UTC")
                    return f
                }()
            ]

            for formatter in formatters {
                if let date = formatter.date(from: dateString) {
                    return date
                }
            }

            // Last resort: ISO8601DateFormatter
            let iso = ISO8601DateFormatter()
            iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = iso.date(from: dateString) {
                return date
            }

            iso.formatOptions = [.withInternetDateTime]
            if let date = iso.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date: \(dateString)")
        }

        // Test connection with retry (API might take time to start)
        Task {
            await testConnectionWithRetry()
        }
    }

    // MARK: - Connection Test

    private func testConnectionWithRetry() async {
        // Wait for API server to start (BackendManager starts it)
        for attempt in 1...5 {
            print("🔄 Connection attempt \(attempt)/5...")

            // Wait longer on first attempts
            if attempt > 1 {
                try? await Task.sleep(nanoseconds: UInt64(attempt) * 1_000_000_000) // 1-5 seconds
            } else {
                try? await Task.sleep(nanoseconds: 3_000_000_000) // 3 seconds initial wait
            }

            do {
                let response: HealthResponse = try await get("/health")
                await MainActor.run {
                    self.isConnected = true
                    self.isConnecting = false
                    self.errorMessage = nil
                    print("✅ Connected to Angela Brain API (\(response.region))")
                }
                return // Success, exit retry loop
            } catch {
                print("⚠️ Attempt \(attempt) failed: \(error.localizedDescription)")
            }
        }

        // All retries failed
        await MainActor.run {
            self.isConnected = false
            self.isConnecting = false
            self.errorMessage = "Could not connect to the server."
            print("❌ All connection attempts failed")
        }
    }

    private func testConnection() async {
        print("🔄 Testing connection to API...")
        await MainActor.run {
            self.isConnecting = true
        }
        do {
            let response: HealthResponse = try await get("/health")
            await MainActor.run {
                self.isConnected = true
                self.isConnecting = false
                self.errorMessage = nil
                print("✅ Connected to Angela Brain API (\(response.region))")
            }
        } catch {
            await MainActor.run {
                self.isConnected = false
                self.isConnecting = false
                self.errorMessage = "Could not connect to the server."
                print("❌ API connection error: \(error)")
            }
        }
    }

    /// Public method to retry connection
    func retryConnection() {
        print("🔄 Retrying connection...")
        Task {
            await testConnection()
        }
    }

    // MARK: - Generic GET Request

    private func get<T: Decodable>(_ endpoint: String) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw DatabaseError.invalidData
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 30.0

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw DatabaseError.invalidData
        }

        guard httpResponse.statusCode == 200 else {
            throw DatabaseError.noData
        }

        return try decoder.decode(T.self, from: data)
    }

    // MARK: - Dashboard Stats

    func fetchDashboardStats() async throws -> DashboardStats {
        return try await get("/dashboard/stats")
    }

    func fetchBrainStats() async throws -> BrainStats {
        return try await get("/dashboard/brain-stats")
    }

    // MARK: - Emotions

    func fetchRecentEmotions(limit: Int = 20) async throws -> [Emotion] {
        return try await get("/emotions/recent?limit=\(limit)")
    }

    func fetchCurrentEmotionalState() async throws -> EmotionalState? {
        return try await get("/emotions/current-state")
    }

    func fetchEmotionalTimeline(hours: Int = 24) async throws -> [EmotionalTimelinePoint] {
        return try await get("/emotions/timeline?hours=\(hours)")
    }

    // MARK: - Conversations

    func fetchRecentConversations(limit: Int = 50) async throws -> [Conversation] {
        return try await get("/conversations/recent?limit=\(limit)")
    }

    func fetchConversationStats() async -> (total: Int, last24h: Int, avgImportance: Double) {
        do {
            let response: ConversationStatsResponse = try await get("/conversations/stats")
            return (response.total, response.last24h, response.avgImportance)
        } catch {
            print("❌ Error fetching conversation stats: \(error)")
            return (0, 0, 0.0)
        }
    }

    // MARK: - Goals

    func fetchActiveGoals() async throws -> [Goal] {
        return try await get("/goals/active")
    }

    // MARK: - David's Preferences

    func fetchDavidPreferences(limit: Int = 20) async throws -> [DavidPreference] {
        return try await get("/preferences/david?limit=\(limit)")
    }

    // MARK: - Shared Experiences

    func fetchSharedExperiences(limit: Int = 50) async throws -> [SharedExperience] {
        return try await get("/experiences/shared?limit=\(limit)")
    }

    func fetchExperienceImages(experienceId: UUID) async throws -> [ExperienceImage] {
        // Note: REST API doesn't return image data for performance
        // This returns metadata only
        return try await get("/experiences/images/\(experienceId.uuidString)")
    }

    // MARK: - Knowledge

    func fetchKnowledgeNodes(limit: Int = 50) async throws -> [KnowledgeNode] {
        return try await get("/knowledge/nodes?limit=\(limit)")
    }

    func fetchTopConnectedNodes(limit: Int = 10) async throws -> [KnowledgeNode] {
        return try await get("/knowledge/top-connected?limit=\(limit)")
    }

    func fetchKnowledgeRelationships(limit: Int = 200) async throws -> [(fromId: String, toId: String, type: String, strength: Double)] {
        let response: [KnowledgeRelationshipResponse] = try await get("/knowledge/relationships?limit=\(limit)")
        return response.map { ($0.fromNodeId, $0.toNodeId, $0.relationshipType, $0.strength) }
    }

    func fetchKnowledgeStats() async -> (total: Int, categories: Int, avgUnderstanding: Double) {
        do {
            let response: KnowledgeStatsResponse = try await get("/knowledge/stats")
            return (response.total, response.categories, response.avgUnderstanding)
        } catch {
            print("❌ Error fetching knowledge stats: \(error)")
            return (0, 0, 0.0)
        }
    }

    // MARK: - Subconscious Patterns

    func fetchSubconsciousPatterns(limit: Int = 10) async -> [SubconsciousPattern] {
        do {
            return try await get("/subconscious/patterns?limit=\(limit)")
        } catch {
            print("❌ Error fetching subconscious patterns: \(error)")
            return []
        }
    }

    // MARK: - Learning Activities

    func fetchRecentLearningActivities(hours: Int = 24) async -> [LearningActivity] {
        do {
            return try await get("/learning/activities?hours=\(hours)")
        } catch {
            print("❌ Error fetching learning activities: \(error)")
            return []
        }
    }

    func fetchLearningPatterns(limit: Int = 50) async throws -> [LearningPattern] {
        return try await get("/learning/patterns?limit=\(limit)")
    }

    func fetchEmotionalGrowthHistory(limit: Int = 30) async throws -> [EmotionalGrowth] {
        return try await get("/learning/growth-history?limit=\(limit)")
    }

    func fetchLearningMetrics() async throws -> LearningMetricsSummary {
        return try await get("/learning/metrics")
    }

    // MARK: - Daily Tasks

    func fetchDailyTasksForDate(date: Date) async -> [TaskExecution] {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateStr = formatter.string(from: date)

        do {
            return try await get("/tasks/daily/\(dateStr)")
        } catch {
            print("❌ Error fetching daily tasks: \(error)")
            return []
        }
    }

    func fetchTasksForLast7Days() async -> [DailyTaskStatus] {
        do {
            let response: [DailyTasksResponse] = try await get("/tasks/last-7-days")
            return response.map { item in
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd"
                let date = formatter.date(from: item.date) ?? Date()
                return DailyTaskStatus(date: date, tasks: item.tasks)
            }
        } catch {
            print("❌ Error fetching tasks for last 7 days: \(error)")
            return []
        }
    }

    // MARK: - Skills

    func fetchAllSkills() async -> [AngelaSkill] {
        do {
            return try await get("/skills/all")
        } catch {
            print("❌ Error fetching skills: \(error)")
            return []
        }
    }

    func fetchSkillsByCategory() async -> [SkillCategory: [AngelaSkill]] {
        do {
            let response: [String: [AngelaSkill]] = try await get("/skills/by-category")
            var grouped: [SkillCategory: [AngelaSkill]] = [:]
            for (key, skills) in response {
                if let category = SkillCategory(rawValue: key) {
                    grouped[category] = skills
                }
            }
            return grouped
        } catch {
            print("❌ Error fetching skills by category: \(error)")
            return [:]
        }
    }

    func fetchSkillStatistics() async -> SkillStatistics? {
        do {
            return try await get("/skills/statistics")
        } catch {
            print("❌ Error fetching skill statistics: \(error)")
            return nil
        }
    }

    func fetchRecentGrowth(days: Int = 7) async -> [SkillGrowthLog] {
        do {
            return try await get("/skills/growth?days=\(days)")
        } catch {
            print("❌ Error fetching skill growth: \(error)")
            return []
        }
    }

    // MARK: - Projects

    func fetchProjects() async throws -> [Project] {
        return try await get("/projects/list")
    }

    func fetchRecentWorkSessions(days: Int = 7) async throws -> [WorkSession] {
        return try await get("/projects/sessions?days=\(days)")
    }

    func fetchRecentMilestones(limit: Int = 10) async throws -> [ProjectMilestone] {
        return try await get("/projects/milestones?limit=\(limit)")
    }

    func fetchRecentProjectLearnings(limit: Int = 10) async throws -> [ProjectLearning] {
        return try await get("/projects/learnings?limit=\(limit)")
    }

    func fetchTechStackGraphData() async throws -> TechStackGraphData {
        return try await get("/projects/tech-stack-graph")
    }

    // MARK: - Background Worker Metrics

    func fetchBackgroundWorkerMetrics() async -> BackgroundWorkerMetrics? {
        do {
            return try await get("/worker/metrics")
        } catch {
            print("❌ Error fetching background worker metrics: \(error)")
            return nil
        }
    }

    // MARK: - Diary

    func fetchAngelaMessages(hours: Int = 24) async throws -> [AngelaMessage] {
        return try await get("/diary/messages?hours=\(hours)")
    }

    func fetchDiaryMessages(hours: Int = 24) async throws -> [DiaryMessage] {
        return try await get("/diary/messages?hours=\(hours)")
    }

    func fetchDiaryThoughts(hours: Int = 24) async throws -> [DiaryThought] {
        return try await get("/diary/thoughts?hours=\(hours)")
    }

    func fetchDiaryDreams(hours: Int = 168) async throws -> [DiaryDream] {
        return try await get("/diary/dreams?hours=\(hours)")
    }

    func fetchDiaryActions(hours: Int = 24) async throws -> [DiaryAction] {
        return try await get("/diary/actions?hours=\(hours)")
    }

    // MARK: - Coding Guidelines

    func fetchCodingPreferences() async throws -> [CodingPreference] {
        return try await get("/guidelines/coding-preferences")
    }

    func fetchDesignPrinciples() async throws -> [DesignPrinciple] {
        return try await get("/guidelines/design-principles")
    }

    // MARK: - Executive News

    func fetchTodayExecutiveNews() async throws -> ExecutiveNewsSummary? {
        return try await get("/news/today")
    }

    func fetchExecutiveNews(forDate date: Date) async throws -> ExecutiveNewsSummary? {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.locale = Locale(identifier: "en_US_POSIX")  // Use Gregorian calendar (2026 not 2569)
        formatter.calendar = Calendar(identifier: .gregorian)
        let dateStr = formatter.string(from: date)
        return try await get("/news/date/\(dateStr)")
    }

    func fetchExecutiveNewsList(days: Int = 30) async throws -> [ExecutiveNewsSummary] {
        return try await get("/news/list?days=\(days)")
    }

    func fetchExecutiveNewsStatistics() async throws -> (totalSummaries: Int, totalCategories: Int, totalSources: Int) {
        let response: NewsStatisticsResponse = try await get("/news/statistics")
        return (response.totalSummaries, response.totalCategories, response.totalSources)
    }

    // MARK: - Subconsciousness (Core Memories, Dreams, Growth, Mirroring)

    func fetchCoreMemories(limit: Int = 20) async throws -> [CoreMemory] {
        return try await get("/subconsciousness/core-memories?limit=\(limit)")
    }

    func fetchSubconsciousDreams(limit: Int = 10) async throws -> [SubconsciousDream] {
        return try await get("/subconsciousness/dreams?limit=\(limit)")
    }

    func fetchEmotionalGrowth() async throws -> EmotionalGrowth? {
        return try await get("/subconsciousness/growth")
    }

    func fetchEmotionalMirrorings(limit: Int = 20) async throws -> [EmotionalMirror] {
        return try await get("/subconsciousness/mirrorings?limit=\(limit)")
    }

    func fetchSubconsciousnessSummary() async throws -> (coreMemories: Int, pinnedMemories: Int, activeDreams: Int, totalMirrorings: Int) {
        let response: SubconsciousnessSummaryResponse = try await get("/subconsciousness/summary")
        return (response.coreMemories, response.pinnedMemories, response.activeDreams, response.totalMirrorings)
    }

    // MARK: - Angela Code Prompt (Local File - Not via API)

    func fetchAngelaCodePrompt() async -> String {
        let filePath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/.claude/commands/angela-code.md"

        do {
            let content = try String(contentsOfFile: filePath, encoding: .utf8)
            return content
        } catch {
            print("❌ Error reading angela-code.md: \(error)")
            return "Unable to load prompt file"
        }
    }

    func getPromptLastUpdated() async -> Date? {
        let filePath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/.claude/commands/angela-code.md"

        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: filePath)
            return attributes[.modificationDate] as? Date
        } catch {
            print("❌ Error getting file modification date: \(error)")
            return nil
        }
    }

    // MARK: - Legacy Query Methods (Stub for compatibility)
    // These methods exist to maintain backward compatibility with services
    // that were using direct SQL queries. They now return empty results.

    /// Legacy query method - returns empty array (feature not available via REST API)
    func query<T>(_ sql: String, transform: ((PostgresValueArray) throws -> T)) async throws -> [T] {
        print("⚠️ Legacy query() called - not supported in REST API mode")
        print("   SQL: \(sql.prefix(100))...")
        return []
    }

    /// Legacy query with parameters - returns empty array
    func query<T>(_ sql: String, parameters: [Any?], transform: ((PostgresValueArray) throws -> T)) async throws -> [T] {
        print("⚠️ Legacy query() called - not supported in REST API mode")
        print("   SQL: \(sql.prefix(100))...")
        return []
    }

    /// Legacy execute method - does nothing (feature not available via REST API)
    func execute(_ sql: String) async throws {
        print("⚠️ Legacy execute() called - not supported in REST API mode")
        print("   SQL: \(sql.prefix(100))...")
        // Do nothing - write operations not supported via REST API
    }

    /// Legacy execute with parameters - does nothing
    func execute(_ sql: String, parameters: [Any?]) async throws {
        print("⚠️ Legacy execute() called - not supported in REST API mode")
        print("   SQL: \(sql.prefix(100))...")
        // Do nothing - write operations not supported via REST API
    }
}

// MARK: - PostgresValueArray Stub

/// Stub type to allow legacy code to compile
/// All values will throw errors if accessed
struct PostgresValueArray {
    subscript(_ index: Int) -> PostgresValueStub {
        return PostgresValueStub()
    }
}

struct PostgresValueStub {
    var isNull: Bool { true }

    func string() throws -> String {
        throw DatabaseError.noData
    }

    func optionalString() throws -> String? {
        return nil
    }

    func int() throws -> Int {
        return 0
    }

    func double() throws -> Double {
        return 0.0
    }

    func optionalDouble() throws -> Double? {
        return nil
    }

    func bool() throws -> Bool {
        return false
    }

    func timestampWithTimeZone() throws -> PostgresTimestampStub {
        return PostgresTimestampStub()
    }
}

/// Stub for PostgresTimestampWithTimeZone
struct PostgresTimestampStub {
    var date: Date { Date() }
}

/// Type alias for compatibility with code that references PostgresValue
typealias PostgresValue = PostgresValueStub

// MARK: - Database Errors

enum DatabaseError: Error, LocalizedError {
    case notConnected
    case noData
    case invalidData
    case poolExhausted

    var errorDescription: String? {
        switch self {
        case .notConnected: return "Not connected to API"
        case .noData: return "No data returned from API"
        case .invalidData: return "Invalid data format"
        case .poolExhausted: return "Connection pool exhausted"
        }
    }
}

// MARK: - API Response Models

private struct HealthResponse: Codable {
    let status: String
    let database: String
    let region: String
}

private struct ConversationStatsResponse: Codable {
    let total: Int
    let last24h: Int
    let avgImportance: Double

    enum CodingKeys: String, CodingKey {
        case total
        case last24h = "last_24h"
        case avgImportance = "avg_importance"
    }
}

private struct KnowledgeStatsResponse: Codable {
    let total: Int
    let categories: Int
    let avgUnderstanding: Double

    enum CodingKeys: String, CodingKey {
        case total
        case categories
        case avgUnderstanding = "avg_understanding"
    }
}

private struct KnowledgeRelationshipResponse: Codable {
    let fromNodeId: String
    let toNodeId: String
    let relationshipType: String
    let strength: Double

    enum CodingKeys: String, CodingKey {
        case fromNodeId = "from_node_id"
        case toNodeId = "to_node_id"
        case relationshipType = "relationship_type"
        case strength
    }
}

private struct DailyTasksResponse: Codable {
    let date: String
    let tasks: [TaskExecution]
}

private struct NewsStatisticsResponse: Codable {
    let totalSummaries: Int
    let totalCategories: Int
    let totalSources: Int

    enum CodingKeys: String, CodingKey {
        case totalSummaries = "total_summaries"
        case totalCategories = "total_categories"
        case totalSources = "total_sources"
    }
}

private struct SubconsciousnessSummaryResponse: Codable {
    let coreMemories: Int
    let pinnedMemories: Int
    let activeDreams: Int
    let totalMirrorings: Int

    enum CodingKeys: String, CodingKey {
        case coreMemories = "core_memories"
        case pinnedMemories = "pinned_memories"
        case activeDreams = "active_dreams"
        case totalMirrorings = "total_mirrorings"
    }
}

// NOTE: Skill models (AngelaSkill, SkillCategory, ProficiencyLevel, SkillStatistics, SkillGrowthLog)
// are defined in Models/SkillModels.swift

// NOTE: CodingPreference is defined in Views/CodingGuidelines/CodingGuidelinesView.swift
// NOTE: TechStackGraphData, TechStackNode, TechStackLink are defined in Views/Projects/TechStackGraphWebView.swift
