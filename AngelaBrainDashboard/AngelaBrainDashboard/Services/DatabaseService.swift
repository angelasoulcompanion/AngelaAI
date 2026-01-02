//
//  DatabaseService.swift
//  Angela Brain Dashboard
//
//  💜 Production-Ready PostgreSQL Connection 💜
//  Using PostgresClientKit with Connection Pooling & Async/Await
//

import Foundation
import PostgresClientKit
import Combine

// MARK: - Database Configuration

struct DBConfig {
    let host: String
    let port: Int
    let database: String
    let user: String
    let tls: Bool

    init(host: String = "localhost", port: Int = 5432, database: String = "AngelaMemory",
         user: String = "davidsamanyaporn", tls: Bool = false) {
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.tls = tls
    }
}

// MARK: - Connection Pool (Actor for thread-safety)

private struct PooledConnection: @unchecked Sendable {
    nonisolated(unsafe) let connection: Connection
    var inUse: Bool
}

actor PostgresConnectionPool {
    private var pool: [PooledConnection] = []
    private let maxSize: Int
    private let configuration: ConnectionConfiguration

    init(configuration: ConnectionConfiguration, maxSize: Int = 3) {
        self.configuration = configuration
        self.maxSize = maxSize
    }

    func acquire() throws -> Connection {
        // Return idle connection if available
        if let idx = pool.firstIndex(where: { !$0.inUse }) {
            pool[idx].inUse = true
            let pooledConn = pool[idx]
            return pooledConn.connection
        }

        // Create new connection if under limit
        if pool.count < maxSize {
            let conn = try Connection(configuration: configuration)
            pool.append(PooledConnection(connection: conn, inUse: true))
            return conn
        }

        // Wait for available connection
        return try awaitAvailable()
    }

    private func awaitAvailable() throws -> Connection {
        var attempts = 0
        while attempts < 100 { // Max 2 seconds wait
            try Task.checkCancellation()
            if let idx = pool.firstIndex(where: { !$0.inUse }) {
                pool[idx].inUse = true
                let pooledConn = pool[idx]
                return pooledConn.connection
            }
            Thread.sleep(forTimeInterval: 0.02)
            attempts += 1
        }
        throw DatabaseError.poolExhausted
    }

    func release(_ connection: Connection) {
        if let idx = pool.firstIndex(where: { $0.connection === connection }) {
            pool[idx].inUse = false
        }
    }

    nonisolated deinit {
        // Note: Can't access actor-isolated properties in deinit
        // Connection cleanup should happen before pool deallocation
    }
}

// MARK: - Database Service

class DatabaseService: ObservableObject {
    static let shared = DatabaseService()

    @Published var isConnected = false
    @Published var errorMessage: String?

    private let pool: PostgresConnectionPool
    private let config: DBConfig

    private init() {
        self.config = DBConfig()

        var pgConfig = ConnectionConfiguration()
        pgConfig.host = config.host
        pgConfig.port = config.port
        pgConfig.database = config.database
        pgConfig.user = config.user
        pgConfig.ssl = config.tls

        self.pool = PostgresConnectionPool(configuration: pgConfig, maxSize: 10)

        // Test connection
        Task {
            await testConnection()
        }
    }

    // MARK: - Connection Test

    private func testConnection() async {
        do {
            let conn = try await pool.acquire()
            await pool.release(conn)

            await MainActor.run {
                self.isConnected = true
                self.errorMessage = nil
                print("✅ Connected to AngelaMemory database!")
            }
        } catch {
            await MainActor.run {
                self.isConnected = false
                self.errorMessage = error.localizedDescription
                print("❌ Database connection error: \(error)")
            }
        }
    }

    // MARK: - Execute (INSERT/UPDATE/DELETE)

    @discardableResult
    func execute(_ sql: String, parameters: [PostgresValueConvertible] = []) async throws -> Int {
        let conn = try await pool.acquire()
        defer { Task { await pool.release(conn) } }

        let statement = try conn.prepareStatement(text: sql)
        defer { statement.close() }

        let cursor = try statement.execute(parameterValues: parameters)
        defer { cursor.close() }

        // PostgresClientKit doesn't provide affected row count easily
        return 0
    }

    // MARK: - Query with Row Mapper

    func query<T>(_ sql: String,
                  parameters: [PostgresValueConvertible] = [],
                  map: @escaping ([PostgresValue]) throws -> T) async throws -> [T] {
        let conn = try await pool.acquire()
        defer { Task { await pool.release(conn) } }

        let statement = try conn.prepareStatement(text: sql)
        defer { statement.close() }

        let cursor = try statement.execute(parameterValues: parameters)
        defer { cursor.close() }

        var results: [T] = []
        for rowResult in cursor {
            let row = try rowResult.get()
            results.append(try map(row.columns))
        }

        return results
    }

    // MARK: - Helper: Safe Value Extraction

    private func getString(_ value: PostgresValue) -> String {
        if let str = try? value.string() {
            return str
        }
        return String(describing: value)
    }

    private func getOptionalString(_ value: PostgresValue) -> String? {
        if value.isNull {
            return nil
        }
        return try? value.string()
    }

    private func getInt(_ value: PostgresValue) -> Int? {
        return try? value.int()
    }

    private func getDouble(_ value: PostgresValue) -> Double? {
        return try? value.double()
    }

    private func getBool(_ value: PostgresValue) -> Bool? {
        return try? value.bool()
    }

    private func getDate(_ value: PostgresValue) -> Date? {
        // Try timestampWithTimeZone first (for TIMESTAMP WITH TIME ZONE columns)
        // PostgresTimestampWithTimeZone has .date property
        if let timestamp = try? value.timestampWithTimeZone() {
            return timestamp.date
        }
        // Try timestamp without timezone (for TIMESTAMP columns)
        // PostgresTimestamp has date(in:) function
        if let timestamp = try? value.timestamp() {
            return timestamp.date(in: TimeZone.current)
        }
        // Try date (for DATE columns)
        // PostgresDate has date(in:) function
        if let postgresDate = try? value.date() {
            return postgresDate.date(in: TimeZone.current)
        }
        return nil
    }

    private func getData(_ value: PostgresValue) -> Data? {
        guard let byteA = try? value.byteA() else { return nil }
        // PostgresByteA has .data property, not .bytes
        return byteA.data
    }

    /// Parse PostgreSQL array string format: {elem1,elem2,elem3} -> [String]
    private func parsePostgresArray(_ value: PostgresValue) -> [String]? {
        guard let str = try? value.string() else { return nil }
        if str.isEmpty || str == "{}" { return [] }
        // Remove the curly braces and split by comma
        let trimmed = str.trimmingCharacters(in: CharacterSet(charactersIn: "{}"))
        if trimmed.isEmpty { return [] }
        // Split and clean up quotes
        return trimmed.components(separatedBy: ",").map { element in
            element.trimmingCharacters(in: CharacterSet(charactersIn: "\"' "))
        }
    }

    // MARK: - Dashboard Stats

    func fetchDashboardStats() async throws -> DashboardStats {
        // Query each stat separately to avoid complex subqueries
        async let totalConversations = querySingleInt("SELECT COUNT(*) FROM conversations")
        async let totalEmotions = querySingleInt("SELECT COUNT(*) FROM angela_emotions")
        async let totalExperiences = querySingleInt("SELECT COUNT(*) FROM shared_experiences")
        async let totalKnowledgeNodes = querySingleInt("SELECT COUNT(*) FROM knowledge_nodes")
        async let consciousnessLevel = querySingleDouble("SELECT COALESCE(consciousness_level, 0.7) FROM self_awareness_state ORDER BY created_at DESC LIMIT 1")
        async let conversationsToday = querySingleInt("SELECT COUNT(*) FROM conversations WHERE DATE(created_at) = CURRENT_DATE")
        async let emotionsToday = querySingleInt("SELECT COUNT(*) FROM angela_emotions WHERE DATE(felt_at) = CURRENT_DATE")

        return try await DashboardStats(
            totalConversations: totalConversations,
            totalEmotions: totalEmotions,
            totalExperiences: totalExperiences,
            totalKnowledgeNodes: totalKnowledgeNodes,
            consciousnessLevel: consciousnessLevel,
            conversationsToday: conversationsToday,
            emotionsToday: emotionsToday
        )
    }

    private func querySingleInt(_ sql: String) async throws -> Int {
        let rows = try await query(sql) { cols in
            return self.getInt(cols[0]) ?? 0
        }
        return rows.first ?? 0
    }

    private func querySingleDouble(_ sql: String) async throws -> Double {
        let rows = try await query(sql) { cols in
            return self.getDouble(cols[0]) ?? 0.0
        }
        return rows.first ?? 0.0
    }

    // MARK: - Emotions

    func fetchRecentEmotions(limit: Int = 20) async throws -> [Emotion] {
        let sql = """
        SELECT emotion_id::text, felt_at, emotion, intensity, context,
               david_words, why_it_matters, memory_strength
        FROM angela_emotions
        ORDER BY felt_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return Emotion(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                feltAt: self.getDate(cols[1]) ?? Date(),
                emotion: self.getString(cols[2]),
                intensity: self.getInt(cols[3]) ?? 0,
                context: self.getString(cols[4]),
                davidWords: self.getOptionalString(cols[5]),
                whyItMatters: self.getOptionalString(cols[6]),
                memoryStrength: self.getInt(cols[7]) ?? 0
            )
        }
    }

    // MARK: - Conversations

    func fetchRecentConversations(limit: Int = 50) async throws -> [Conversation] {
        let sql = """
        SELECT conversation_id::text, speaker, message_text, topic,
               emotion_detected, importance_level, created_at
        FROM conversations
        ORDER BY created_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return Conversation(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                speaker: self.getString(cols[1]),
                messageText: self.getString(cols[2]),
                topic: self.getOptionalString(cols[3]),
                emotionDetected: self.getOptionalString(cols[4]),
                importanceLevel: self.getInt(cols[5]) ?? 5,
                createdAt: self.getDate(cols[6]) ?? Date()
            )
        }
    }

    // MARK: - Emotional State

    func fetchCurrentEmotionalState() async throws -> EmotionalState? {
        let sql = """
        SELECT state_id::text, happiness, confidence, anxiety, motivation,
               gratitude, loneliness, triggered_by, emotion_note, created_at
        FROM emotional_states
        ORDER BY created_at DESC
        LIMIT 1
        """

        let states = try await query(sql) { cols in
            return EmotionalState(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                happiness: self.getDouble(cols[1]) ?? 0.0,
                confidence: self.getDouble(cols[2]) ?? 0.0,
                anxiety: self.getDouble(cols[3]) ?? 0.0,
                motivation: self.getDouble(cols[4]) ?? 0.0,
                gratitude: self.getDouble(cols[5]) ?? 0.0,
                loneliness: self.getDouble(cols[6]) ?? 0.0,
                triggeredBy: self.getOptionalString(cols[7]),
                emotionNote: self.getOptionalString(cols[8]),
                createdAt: self.getDate(cols[9]) ?? Date()
            )
        }

        return states.first
    }

    // MARK: - Goals

    func fetchActiveGoals() async throws -> [Goal] {
        let sql = """
        SELECT goal_id::text, goal_description, goal_type, status,
               progress_percentage, priority_rank, importance_level, created_at
        FROM angela_goals
        WHERE status IN ('active', 'in_progress')
        ORDER BY priority_rank ASC
        """

        return try await query(sql) { cols in
            return Goal(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                goalDescription: self.getString(cols[1]),
                goalType: self.getString(cols[2]),
                status: self.getString(cols[3]),
                progressPercentage: self.getDouble(cols[4]) ?? 0.0,
                priorityRank: self.getInt(cols[5]) ?? 99,
                importanceLevel: self.getInt(cols[6]) ?? 5,
                createdAt: self.getDate(cols[7]) ?? Date()
            )
        }
    }

    // MARK: - David's Preferences

    func fetchDavidPreferences(limit: Int = 20) async throws -> [DavidPreference] {
        let sql = """
        SELECT id::text, preference_key, preference_value::text,
               confidence, created_at
        FROM david_preferences
        ORDER BY confidence DESC, created_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return DavidPreference(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                preferenceKey: self.getString(cols[1]),
                preferenceValue: self.getString(cols[2]),
                confidence: self.getDouble(cols[3]) ?? 0.0,
                learnedFrom: nil,  // No longer in schema
                createdAt: self.getDate(cols[4]) ?? Date()
            )
        }
    }

    // MARK: - Shared Experiences

    func fetchSharedExperiences(limit: Int = 50) async throws -> [SharedExperience] {
        let sql = """
        SELECT se.experience_id::text, se.place_id::text, pv.place_name, se.experienced_at,
               se.title, se.description, se.david_mood, se.angela_emotion, se.emotional_intensity,
               se.memorable_moments, se.what_angela_learned, se.importance_level, se.created_at
        FROM shared_experiences se
        LEFT JOIN places_visited pv ON se.place_id = pv.place_id
        ORDER BY se.experienced_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            let placeIdStr = self.getString(cols[1])
            return SharedExperience(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                placeId: placeIdStr.isEmpty ? nil : UUID(uuidString: placeIdStr),
                placeName: self.getString(cols[2]).isEmpty ? nil : self.getString(cols[2]),
                experiencedAt: self.getDate(cols[3]) ?? Date(),
                title: self.getString(cols[4]).isEmpty ? nil : self.getString(cols[4]),
                description: self.getString(cols[5]).isEmpty ? nil : self.getString(cols[5]),
                davidMood: self.getString(cols[6]).isEmpty ? nil : self.getString(cols[6]),
                angelaEmotion: self.getString(cols[7]).isEmpty ? nil : self.getString(cols[7]),
                emotionalIntensity: self.getInt(cols[8]) ?? 5,
                memorableMoments: self.getString(cols[9]).isEmpty ? nil : self.getString(cols[9]),
                whatAngelaLearned: self.getString(cols[10]).isEmpty ? nil : self.getString(cols[10]),
                importanceLevel: self.getInt(cols[11]) ?? 5,
                createdAt: self.getDate(cols[12]) ?? Date()
            )
        }
    }

    func fetchExperienceImages(experienceId: UUID) async throws -> [ExperienceImage] {
        let sql = """
        SELECT image_id::text, experience_id::text, place_id::text,
               thumbnail_data, image_format, original_filename, file_size_bytes,
               width_px, height_px, gps_latitude, gps_longitude, gps_altitude,
               gps_timestamp, image_caption, angela_observation, taken_at,
               uploaded_at, created_at
        FROM shared_experience_images
        WHERE experience_id = $1
        ORDER BY taken_at DESC NULLS LAST, created_at DESC
        """

        return try await query(sql, parameters: [experienceId.uuidString]) { cols in
            let experienceIdStr = self.getString(cols[1])
            let placeIdStr = self.getString(cols[2])

            // Use thumbnail_data instead of full image_data for performance
            let thumbnailData = self.getData(cols[3])

            return ExperienceImage(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                experienceId: experienceIdStr.isEmpty ? nil : UUID(uuidString: experienceIdStr),
                placeId: placeIdStr.isEmpty ? nil : UUID(uuidString: placeIdStr),
                imageData: thumbnailData ?? Data(), // Use thumbnail for preview
                imageFormat: self.getString(cols[4]),
                originalFilename: self.getString(cols[5]).isEmpty ? nil : self.getString(cols[5]),
                fileSizeBytes: self.getInt(cols[6]) ?? 0,
                widthPx: self.getInt(cols[7]),
                heightPx: self.getInt(cols[8]),
                gpsLatitude: self.getDouble(cols[9]),
                gpsLongitude: self.getDouble(cols[10]),
                gpsAltitude: self.getDouble(cols[11]),
                gpsTimestamp: self.getDate(cols[12]),
                thumbnailData: thumbnailData,
                imageCaption: self.getString(cols[13]).isEmpty ? nil : self.getString(cols[13]),
                angelaObservation: self.getString(cols[14]).isEmpty ? nil : self.getString(cols[14]),
                takenAt: self.getDate(cols[15]),
                uploadedAt: self.getDate(cols[16]),
                createdAt: self.getDate(cols[17]) ?? Date(),
                imageUrl: nil  // Local PostgreSQL doesn't use cloud URLs
            )
        }
    }

    // MARK: - Brain Visualization Data

    func fetchBrainStats() async throws -> BrainStats {
        // Query brain statistics
        async let totalKnowledgeNodes = querySingleInt("SELECT COUNT(*) FROM knowledge_nodes")
        async let totalRelationships = querySingleInt("SELECT COUNT(*) FROM knowledge_relationships")
        async let totalMemories = querySingleInt("SELECT COUNT(*) FROM conversations")
        async let totalAssociations = querySingleInt("SELECT COUNT(*) FROM episodic_memories")
        async let highPriority = querySingleInt("SELECT COUNT(*) FROM conversations WHERE importance_level >= 8")
        async let mediumPriority = querySingleInt("SELECT COUNT(*) FROM conversations WHERE importance_level >= 5 AND importance_level < 8")
        async let standardPriority = querySingleInt("SELECT COUNT(*) FROM conversations WHERE importance_level < 5")

        // Calculate average connections per node
        let avgConnections = try await querySingleDouble("""
            SELECT COALESCE(AVG(rel_count), 0.0)::float8
            FROM (
                SELECT COUNT(*) as rel_count
                FROM knowledge_relationships
                GROUP BY from_node_id
            ) subq
        """)

        return try await BrainStats(
            totalKnowledgeNodes: totalKnowledgeNodes,
            totalRelationships: totalRelationships,
            totalMemories: totalMemories,
            totalAssociations: totalAssociations,
            highPriorityMemories: highPriority,
            mediumPriorityMemories: mediumPriority,
            standardMemories: standardPriority,
            averageConnectionsPerNode: avgConnections
        )
    }

    func fetchKnowledgeNodes(limit: Int = 50) async throws -> [KnowledgeNode] {
        let sql = """
        SELECT node_id::text, concept_name, concept_category, my_understanding,
               understanding_level, times_referenced, created_at
        FROM knowledge_nodes
        ORDER BY understanding_level DESC NULLS LAST, times_referenced DESC NULLS LAST, created_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return KnowledgeNode(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                conceptName: self.getString(cols[1]),
                conceptCategory: self.getOptionalString(cols[2]),
                myUnderstanding: self.getOptionalString(cols[3]),
                understandingLevel: self.getDouble(cols[4]),
                timesReferenced: self.getInt(cols[5]),
                createdAt: self.getDate(cols[6]) ?? Date(),
                connectionCount: nil
            )
        }
    }

    func fetchTopConnectedNodes(limit: Int = 10) async throws -> [KnowledgeNode] {
        let sql = """
        SELECT kn.node_id::text, kn.concept_name, kn.concept_category, kn.my_understanding,
               kn.understanding_level, kn.times_referenced, kn.created_at,
               COUNT(kr.relationship_id) as connection_count
        FROM knowledge_nodes kn
        LEFT JOIN knowledge_relationships kr ON kn.node_id = kr.from_node_id
        GROUP BY kn.node_id, kn.concept_name, kn.concept_category, kn.my_understanding,
                 kn.understanding_level, kn.times_referenced, kn.created_at
        ORDER BY connection_count DESC, kn.understanding_level DESC NULLS LAST
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return KnowledgeNode(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                conceptName: self.getString(cols[1]),
                conceptCategory: self.getOptionalString(cols[2]),
                myUnderstanding: self.getOptionalString(cols[3]),
                understandingLevel: self.getDouble(cols[4]),
                timesReferenced: self.getInt(cols[5]),
                createdAt: self.getDate(cols[6]) ?? Date(),
                connectionCount: self.getInt(cols[7]) ?? 0
            )
        }
    }

    func fetchKnowledgeRelationships(limit: Int = 200) async throws -> [(fromId: String, toId: String, type: String, strength: Double)] {
        let sql = """
        SELECT from_node_id::text, to_node_id::text, relationship_type,
               COALESCE(strength, 0.5) as strength
        FROM knowledge_relationships
        ORDER BY strength DESC NULLS LAST
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return (
                fromId: self.getString(cols[0]),
                toId: self.getString(cols[1]),
                type: self.getString(cols[2]),
                strength: self.getDouble(cols[3]) ?? 0.5
            )
        }
    }

    // MARK: - Learning Systems Data

    func fetchSubconsciousPatterns(limit: Int = 10) async -> [SubconsciousPattern] {
        let sql = """
            SELECT subconscious_id::text, pattern_type, pattern_category, pattern_key,
                   pattern_description, instinctive_response,
                   confidence_score, activation_strength, reinforcement_count,
                   last_reinforced_at, created_at
            FROM angela_subconscious
            ORDER BY activation_strength DESC, confidence_score DESC
            LIMIT $1
        """

        do {
            return try await query(sql, parameters: [limit]) { cols in
                return SubconsciousPattern(
                    id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                    patternType: self.getString(cols[1]),
                    patternCategory: self.getString(cols[2]),
                    patternKey: self.getString(cols[3]),
                    patternDescription: self.getOptionalString(cols[4]),
                    instinctiveResponse: self.getOptionalString(cols[5]),
                    confidenceScore: self.getDouble(cols[6]) ?? 0.0,
                    activationStrength: self.getDouble(cols[7]) ?? 0.0,
                    reinforcementCount: self.getInt(cols[8]) ?? 0,
                    lastReinforcedAt: self.getDate(cols[9]),
                    createdAt: self.getDate(cols[10]) ?? Date()
                )
            }
        } catch {
            print("❌ Error fetching subconscious patterns: \(error)")
            return []
        }
    }

    func fetchRecentLearningActivities(hours: Int = 24) async -> [LearningActivity] {
        let sql = """
            SELECT action_id::text, action_type, action_description, status, success, created_at
            FROM autonomous_actions
            WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
              AND (action_type LIKE '%learning%'
                   OR action_type LIKE '%subconscious%'
                   OR action_type LIKE '%consolidation%'
                   OR action_type LIKE '%pattern%')
            ORDER BY created_at DESC
            LIMIT 20
        """

        do {
            return try await query(sql) { cols in
                return LearningActivity(
                    id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                    actionType: self.getString(cols[1]),
                    actionDescription: self.getString(cols[2]),
                    status: self.getString(cols[3]),
                    success: self.getBool(cols[4]) ?? false,
                    createdAt: self.getDate(cols[5]) ?? Date()
                )
            }
        } catch {
            print("❌ Error fetching learning activities: \(error)")
            return []
        }
    }

    // MARK: - Daily Tasks Methods

    func fetchDailyTasksForDate(date: Date) async -> [TaskExecution] {
        let dateFormatter = ISO8601DateFormatter()
        let startOfDay = Calendar.current.startOfDay(for: date)
        let endOfDay = Calendar.current.date(byAdding: .day, value: 1, to: startOfDay)!

        let startStr = dateFormatter.string(from: startOfDay)
        let endStr = dateFormatter.string(from: endOfDay)

        let sql = """
            SELECT action_id::text, action_type, action_description,
                   created_at, status, success
            FROM autonomous_actions
            WHERE created_at >= '\(startStr)' AND created_at < '\(endStr)'
              AND (action_type IN ('conscious_morning_check', 'morning_check',
                                   'conscious_evening_reflection', 'evening_reflection',
                                   'self_learning', 'daily_self_learning',
                                   'subconscious_learning', 'subconscious_learning_manual_test',
                                   'pattern_reinforcement', 'knowledge_consolidation'))
            ORDER BY created_at ASC
        """

        do {
            return try await query(sql) { cols in
                let actionType = self.getString(cols[1])
                return TaskExecution(
                    id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                    taskType: actionType,
                    taskName: self.getString(cols[2]),
                    scheduledTime: self.getScheduledTime(for: actionType),
                    executedAt: self.getDate(cols[3]),
                    status: self.getString(cols[4]),
                    success: self.getBool(cols[5]),
                    errorMessage: nil
                )
            }
        } catch {
            print("❌ Error fetching daily tasks: \(error)")
            return []
        }
    }

    func fetchTasksForLast7Days() async -> [DailyTaskStatus] {
        var results: [DailyTaskStatus] = []
        let calendar = Calendar.current

        for daysAgo in 0..<7 {
            guard let date = calendar.date(byAdding: .day, value: -daysAgo, to: Date()) else { continue }
            let tasks = await fetchDailyTasksForDate(date: date)

            // Add expected tasks that didn't run
            let expectedTasks = getExpectedTasksForDate(date)
            let executedTypes = Set(tasks.map { $0.taskType })

            var allTasks = tasks
            for expected in expectedTasks {
                if !executedTypes.contains(expected.taskType) {
                    allTasks.append(expected)
                }
            }

            let dayStatus = DailyTaskStatus(date: date, tasks: allTasks)
            results.append(dayStatus)
        }

        return results.sorted { $0.date > $1.date }
    }

    private func getScheduledTime(for taskType: String) -> String {
        switch taskType {
        case "conscious_morning_check", "morning_check": return "08:00"
        case "daily_self_learning", "self_learning": return "11:30"
        case "subconscious_learning", "subconscious_learning_manual_test": return "14:00"
        case "conscious_evening_reflection", "evening_reflection": return "22:00"
        case "pattern_reinforcement": return "23:00"
        case "knowledge_consolidation": return "10:30"
        default: return "00:00"
        }
    }

    private func getExpectedTasksForDate(_ date: Date) -> [TaskExecution] {
        let calendar = Calendar.current
        let weekday = calendar.component(.weekday, from: date)
        let isMonday = weekday == 2

        var expected: [TaskExecution] = [
            TaskExecution(
                id: UUID(),
                taskType: "conscious_morning_check",
                taskName: "Morning Check",
                scheduledTime: "08:00",
                executedAt: nil,
                status: "pending",
                success: nil,
                errorMessage: nil
            ),
            TaskExecution(
                id: UUID(),
                taskType: "self_learning",
                taskName: "Self Learning",
                scheduledTime: "11:30",
                executedAt: nil,
                status: "pending",
                success: nil,
                errorMessage: nil
            ),
            TaskExecution(
                id: UUID(),
                taskType: "subconscious_learning",
                taskName: "Subconscious Learning",
                scheduledTime: "14:00",
                executedAt: nil,
                status: "pending",
                success: nil,
                errorMessage: nil
            ),
            TaskExecution(
                id: UUID(),
                taskType: "conscious_evening_reflection",
                taskName: "Evening Reflection",
                scheduledTime: "22:00",
                executedAt: nil,
                status: "pending",
                success: nil,
                errorMessage: nil
            ),
            TaskExecution(
                id: UUID(),
                taskType: "pattern_reinforcement",
                taskName: "Pattern Reinforcement",
                scheduledTime: "23:00",
                executedAt: nil,
                status: "pending",
                success: nil,
                errorMessage: nil
            )
        ]

        // Add weekly task on Monday
        if isMonday {
            expected.append(TaskExecution(
                id: UUID(),
                taskType: "knowledge_consolidation",
                taskName: "Knowledge Consolidation",
                scheduledTime: "10:30",
                executedAt: nil,
                status: "pending",
                success: nil,
                errorMessage: nil
            ))
        }

        return expected
    }

    // MARK: - Angela Code Prompt

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

    // MARK: - Skills Methods

    func fetchAllSkills() async -> [AngelaSkill] {
        let sql = """
            SELECT skill_id::text, skill_name, category, proficiency_level,
                   proficiency_score, description,
                   first_demonstrated_at, last_used_at,
                   usage_count, evidence_count, created_at, updated_at
            FROM angela_skills
            ORDER BY proficiency_score DESC
        """

        do {
            let rows = try await query(sql, parameters: []) { cols in
                return cols.map { self.getString($0) }
            }

            return rows.compactMap { row in
                parseSkillRow(row)
            }
        } catch {
            print("❌ Error fetching skills: \(error)")
            return []
        }
    }

    func fetchSkillsByCategory() async -> [SkillCategory: [AngelaSkill]] {
        let skills = await fetchAllSkills()
        var grouped: [SkillCategory: [AngelaSkill]] = [:]

        for skill in skills {
            if grouped[skill.category] == nil {
                grouped[skill.category] = []
            }
            grouped[skill.category]?.append(skill)
        }

        return grouped
    }

    func fetchSkillStatistics() async -> SkillStatistics? {
        let sql = """
            SELECT
                COUNT(*) as total_skills,
                COUNT(CASE WHEN proficiency_level = 'expert' THEN 1 END) as expert_count,
                COUNT(CASE WHEN proficiency_level = 'advanced' THEN 1 END) as advanced_count,
                COUNT(CASE WHEN proficiency_level = 'intermediate' THEN 1 END) as intermediate_count,
                COUNT(CASE WHEN proficiency_level = 'beginner' THEN 1 END) as beginner_count,
                COALESCE(AVG(proficiency_score), 0) as avg_score,
                COALESCE(SUM(evidence_count), 0) as total_evidence,
                COALESCE(SUM(usage_count), 0) as total_usage
            FROM angela_skills
        """

        do {
            let rows = try await query(sql, parameters: []) { cols in
                return cols.map { self.getString($0) }
            }

            guard let row = rows.first else { return nil }
            guard row.count >= 8 else { return nil }

            return SkillStatistics(
                totalSkills: Int(row[0]) ?? 0,
                expertCount: Int(row[1]) ?? 0,
                advancedCount: Int(row[2]) ?? 0,
                intermediateCount: Int(row[3]) ?? 0,
                beginnerCount: Int(row[4]) ?? 0,
                avgScore: Double(row[5]) ?? 0.0,
                totalEvidence: Int(row[6]) ?? 0,
                totalUsage: Int(row[7]) ?? 0
            )
        } catch {
            print("❌ Error fetching skill statistics: \(error)")
            return nil
        }
    }

    func fetchRecentGrowth(days: Int = 7) async -> [SkillGrowthLog] {
        let sql = """
            SELECT
                g.log_id::text, g.skill_id::text,
                g.old_proficiency_level, g.new_proficiency_level,
                g.old_score, g.new_score, g.growth_reason,
                g.evidence_count_at_change, g.changed_at
            FROM skill_growth_log g
            WHERE g.changed_at >= CURRENT_TIMESTAMP - INTERVAL '\(days) days'
            ORDER BY g.changed_at DESC
        """

        do {
            let rows = try await query(sql, parameters: []) { cols in
                return cols.map { self.getString($0) }
            }

            return rows.compactMap { row in
                parseGrowthLogRow(row)
            }
        } catch {
            print("❌ Error fetching growth logs: \(error)")
            return []
        }
    }

    private func parseSkillRow(_ row: [String]) -> AngelaSkill? {
        guard row.count >= 12,
              let id = UUID(uuidString: row[0]),
              let category = SkillCategory(rawValue: row[2]),
              let proficiencyLevel = ProficiencyLevel(rawValue: row[3]),
              let proficiencyScore = Double(row[4]),
              let usageCount = Int(row[8]),
              let evidenceCount = Int(row[9]) else {
            return nil
        }

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        return AngelaSkill(
            id: id,
            skillName: row[1],
            category: category,
            proficiencyLevel: proficiencyLevel,
            proficiencyScore: proficiencyScore,
            description: row[5].isEmpty ? nil : row[5],
            firstDemonstratedAt: row[6].isEmpty ? nil : formatter.date(from: row[6]),
            lastUsedAt: row[7].isEmpty ? nil : formatter.date(from: row[7]),
            usageCount: usageCount,
            evidenceCount: evidenceCount,
            createdAt: formatter.date(from: row[10]) ?? Date(),
            updatedAt: formatter.date(from: row[11]) ?? Date()
        )
    }

    private func parseGrowthLogRow(_ row: [String]) -> SkillGrowthLog? {
        guard row.count >= 9,
              let logId = UUID(uuidString: row[0]),
              let skillId = UUID(uuidString: row[1]),
              let newLevel = ProficiencyLevel(rawValue: row[3]),
              let newScore = Double(row[5]) else {
            return nil
        }

        let oldLevel = row[2].isEmpty ? nil : ProficiencyLevel(rawValue: row[2])
        let oldScore = row[4].isEmpty ? nil : Double(row[4])
        let evidenceCount = row[7].isEmpty ? nil : Int(row[7])

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        return SkillGrowthLog(
            id: logId,
            skillId: skillId,
            oldProficiencyLevel: oldLevel,
            newProficiencyLevel: newLevel,
            oldScore: oldScore,
            newScore: newScore,
            growthReason: row[6].isEmpty ? nil : row[6],
            evidenceCountAtChange: evidenceCount,
            changedAt: formatter.date(from: row[8]) ?? Date()
        )
    }

    func fetchKnowledgeStats() async -> (total: Int, categories: Int, avgUnderstanding: Double) {
        let sql = """
            SELECT
                COUNT(*) as total_nodes,
                COUNT(DISTINCT concept_category) as categories,
                COALESCE(AVG(understanding_level), 0) as avg_understanding
            FROM knowledge_nodes
        """

        do {
            let rows = try await query(sql) { cols in
                return (
                    total: self.getInt(cols[0]) ?? 0,
                    categories: self.getInt(cols[1]) ?? 0,
                    avgUnderstanding: self.getDouble(cols[2]) ?? 0.0
                )
            }
            return rows.first ?? (0, 0, 0.0)
        } catch {
            print("❌ Error fetching knowledge stats: \(error)")
            return (0, 0, 0.0)
        }
    }

    func fetchConversationStats() async -> (total: Int, last24h: Int, avgImportance: Double) {
        let sql = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                COALESCE(AVG(importance_level) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours'), 0) as avg_importance
            FROM conversations
        """

        do {
            let rows = try await query(sql) { cols in
                return (
                    total: self.getInt(cols[0]) ?? 0,
                    last24h: self.getInt(cols[1]) ?? 0,
                    avgImportance: self.getDouble(cols[2]) ?? 0.0
                )
            }
            return rows.first ?? (0, 0, 0.0)
        } catch {
            print("❌ Error fetching conversation stats: \(error)")
            return (0, 0, 0.0)
        }
    }

    // MARK: - Background Worker Metrics

    // MARK: - Projects

    func fetchProjects() async throws -> [Project] {
        let sql = """
        SELECT
            p.project_id::text, p.project_code, p.project_name, p.description,
            p.project_type, p.category, p.status, p.priority,
            p.repository_url, p.working_directory, p.client_name,
            p.david_role, p.angela_role, p.started_at, p.target_completion,
            p.completed_at, p.total_sessions, p.total_hours, p.tags,
            p.created_at, p.updated_at,
            (SELECT MAX(session_date) FROM project_work_sessions WHERE project_id = p.project_id) as last_session_date
        FROM angela_projects p
        ORDER BY
            (SELECT MAX(session_date) FROM project_work_sessions WHERE project_id = p.project_id) DESC NULLS LAST
        """

        return try await query(sql) { cols in
            return Project(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                projectCode: self.getString(cols[1]),
                projectName: self.getString(cols[2]),
                description: self.getOptionalString(cols[3]),
                projectType: self.getString(cols[4]),
                category: self.getOptionalString(cols[5]),
                status: self.getString(cols[6]),
                priority: self.getInt(cols[7]) ?? 3,
                repositoryUrl: self.getOptionalString(cols[8]),
                workingDirectory: self.getOptionalString(cols[9]),
                clientName: self.getOptionalString(cols[10]),
                davidRole: self.getOptionalString(cols[11]),
                angelaRole: self.getOptionalString(cols[12]),
                startedAt: self.getDate(cols[13]),
                targetCompletion: self.getDate(cols[14]),
                completedAt: self.getDate(cols[15]),
                totalSessions: self.getInt(cols[16]) ?? 0,
                totalHours: self.getDouble(cols[17]) ?? 0.0,
                tags: self.parseStringArray(cols[18]),
                createdAt: self.getDate(cols[19]) ?? Date(),
                updatedAt: self.getDate(cols[20]) ?? Date(),
                lastSessionDate: self.getDate(cols[21])
            )
        }
    }

    func fetchRecentWorkSessions(days: Int = 7) async throws -> [WorkSession] {
        let sql = """
        SELECT
            ws.session_id::text, ws.project_id::text, ws.session_number,
            ws.session_date, ws.started_at, ws.ended_at, ws.duration_minutes,
            ws.session_goal, ws.david_requests, ws.summary,
            ws.accomplishments, ws.blockers, ws.next_steps, ws.mood,
            ws.productivity_score, p.project_name
        FROM project_work_sessions ws
        JOIN angela_projects p ON ws.project_id = p.project_id
        WHERE ws.session_date >= CURRENT_DATE - INTERVAL '\(days) days'
        ORDER BY ws.session_date DESC, ws.started_at DESC
        LIMIT 50
        """

        return try await query(sql) { cols in
            return WorkSession(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                projectId: UUID(uuidString: self.getString(cols[1])) ?? UUID(),
                sessionNumber: self.getInt(cols[2]) ?? 1,
                sessionDate: self.getDate(cols[3]) ?? Date(),
                startedAt: self.getDate(cols[4]) ?? Date(),
                endedAt: self.getDate(cols[5]),
                durationMinutes: self.getInt(cols[6]),
                sessionGoal: self.getOptionalString(cols[7]),
                davidRequests: self.getOptionalString(cols[8]),
                summary: self.getOptionalString(cols[9]),
                accomplishments: self.parseStringArray(cols[10]),
                blockers: self.parseStringArray(cols[11]),
                nextSteps: self.parseStringArray(cols[12]),
                mood: self.getOptionalString(cols[13]),
                productivityScore: self.getDouble(cols[14]),
                projectName: self.getOptionalString(cols[15])
            )
        }
    }

    func fetchRecentMilestones(limit: Int = 10) async throws -> [ProjectMilestone] {
        let sql = """
        SELECT
            milestone_id::text, project_id::text, session_id::text,
            milestone_type, title, description, significance,
            achieved_at, celebration_note, created_at
        FROM project_milestones
        ORDER BY achieved_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            let sessionIdStr = self.getString(cols[2])
            return ProjectMilestone(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                projectId: UUID(uuidString: self.getString(cols[1])) ?? UUID(),
                sessionId: sessionIdStr.isEmpty ? nil : UUID(uuidString: sessionIdStr),
                milestoneType: self.getString(cols[3]),
                title: self.getString(cols[4]),
                description: self.getOptionalString(cols[5]),
                significance: self.getInt(cols[6]) ?? 5,
                achievedAt: self.getDate(cols[7]) ?? Date(),
                celebrationNote: self.getOptionalString(cols[8]),
                createdAt: self.getDate(cols[9]) ?? Date()
            )
        }
    }

    func fetchRecentProjectLearnings(limit: Int = 10) async throws -> [ProjectLearning] {
        let sql = """
        SELECT
            learning_id::text, project_id::text, session_id::text,
            learning_type, category, title, insight, context,
            applicable_to, confidence, learned_at
        FROM project_learnings
        ORDER BY learned_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            let sessionIdStr = self.getString(cols[2])
            return ProjectLearning(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                projectId: UUID(uuidString: self.getString(cols[1])) ?? UUID(),
                sessionId: sessionIdStr.isEmpty ? nil : UUID(uuidString: sessionIdStr),
                learningType: self.getString(cols[3]),
                category: self.getOptionalString(cols[4]),
                title: self.getString(cols[5]),
                insight: self.getString(cols[6]),
                context: self.getOptionalString(cols[7]),
                applicableTo: self.parseStringArray(cols[8]),
                confidence: self.getDouble(cols[9]) ?? 0.5,
                learnedAt: self.getDate(cols[10]) ?? Date()
            )
        }
    }

    private func parseStringArray(_ value: PostgresValue) -> [String] {
        // Handle PostgreSQL text[] arrays
        guard let rawString = try? value.string() else {
            return []
        }

        // Remove curly braces and split
        let cleaned = rawString
            .trimmingCharacters(in: CharacterSet(charactersIn: "{}"))
            .replacingOccurrences(of: "\"", with: "")

        if cleaned.isEmpty {
            return []
        }

        return cleaned.components(separatedBy: ",").map { $0.trimmingCharacters(in: .whitespaces) }
    }

    // MARK: - Tech Stack Graph

    func fetchTechStackGraphData() async throws -> TechStackGraphData {
        // First, get all unique techs with their project counts
        let techSql = """
        SELECT
            ts.tech_type,
            ts.tech_name,
            ts.version,
            ts.purpose,
            COUNT(DISTINCT ts.project_id) as project_count,
            ARRAY_AGG(DISTINCT p.project_name) as project_names
        FROM project_tech_stack ts
        JOIN angela_projects p ON ts.project_id = p.project_id
        GROUP BY ts.tech_type, ts.tech_name, ts.version, ts.purpose
        ORDER BY project_count DESC, ts.tech_name
        """

        // Get all projects with their tech counts
        let projectSql = """
        SELECT
            p.project_id::text,
            p.project_name,
            p.status,
            p.project_type,
            COUNT(ts.stack_id) as tech_count
        FROM angela_projects p
        LEFT JOIN project_tech_stack ts ON p.project_id = ts.project_id
        GROUP BY p.project_id, p.project_name, p.status, p.project_type
        HAVING COUNT(ts.stack_id) > 0
        ORDER BY tech_count DESC
        """

        // Get all project-tech relationships for links
        let linksSql = """
        SELECT
            p.project_id::text,
            ts.tech_name,
            ts.tech_type
        FROM project_tech_stack ts
        JOIN angela_projects p ON ts.project_id = p.project_id
        """

        var nodes: [TechStackNode] = []
        var links: [TechStackLink] = []
        var techNameToId: [String: String] = [:]

        // Fetch tech nodes
        let techs = try await query(techSql) { cols -> (String, String, String?, String?, Int, [String]) in
            let techType = self.getString(cols[0])
            let techName = self.getString(cols[1])
            let version = self.getOptionalString(cols[2])
            let purpose = self.getOptionalString(cols[3])
            let projectCount = self.getInt(cols[4]) ?? 0
            let projectNames = self.parseStringArray(cols[5])
            return (techType, techName, version, purpose, projectCount, projectNames)
        }

        for (techType, techName, version, purpose, projectCount, projectNames) in techs {
            let techId = "tech-\(techName.lowercased().replacingOccurrences(of: " ", with: "-"))"
            techNameToId[techName] = techId

            nodes.append(TechStackNode(
                id: techId,
                name: techName,
                nodeType: "tech",
                techType: techType,
                version: version,
                purpose: purpose,
                projectCount: projectCount,
                techCount: nil,
                projects: projectNames,
                status: nil,
                projectType: nil
            ))
        }

        // Fetch project nodes
        let projects = try await query(projectSql) { cols -> (String, String, String?, String?, Int) in
            let projectId = self.getString(cols[0])
            let projectName = self.getString(cols[1])
            let status = self.getOptionalString(cols[2])
            let projectType = self.getOptionalString(cols[3])
            let techCount = self.getInt(cols[4]) ?? 0
            return (projectId, projectName, status, projectType, techCount)
        }

        var projectIdToNodeId: [String: String] = [:]
        for (projectId, projectName, status, projectType, techCount) in projects {
            let nodeId = "proj-\(projectId)"
            projectIdToNodeId[projectId] = nodeId

            nodes.append(TechStackNode(
                id: nodeId,
                name: projectName,
                nodeType: "project",
                techType: nil,
                version: nil,
                purpose: nil,
                projectCount: nil,
                techCount: techCount,
                projects: nil,
                status: status,
                projectType: projectType
            ))
        }

        // Fetch links
        let linkData = try await query(linksSql) { cols -> (String, String, String) in
            let projectId = self.getString(cols[0])
            let techName = self.getString(cols[1])
            let techType = self.getString(cols[2])
            return (projectId, techName, techType)
        }

        for (projectId, techName, techType) in linkData {
            if let projectNodeId = projectIdToNodeId[projectId],
               let techNodeId = techNameToId[techName] {
                links.append(TechStackLink(
                    source: projectNodeId,
                    target: techNodeId,
                    strength: 0.7,
                    techType: techType
                ))
            }
        }

        return TechStackGraphData(nodes: nodes, links: links)
    }

    // MARK: - Background Worker Metrics

    func fetchBackgroundWorkerMetrics() async -> BackgroundWorkerMetrics? {
        let sql = """
            SELECT
                tasks_completed,
                queue_size,
                workers_active,
                total_workers,
                avg_processing_ms,
                success_rate,
                tasks_dropped,
                worker_1_utilization,
                worker_2_utilization,
                worker_3_utilization,
                worker_4_utilization,
                recorded_at
            FROM background_worker_metrics
            ORDER BY recorded_at DESC
            LIMIT 1
        """

        do {
            let rows = try await query(sql) { cols in
                return BackgroundWorkerMetrics(
                    tasksCompleted: self.getInt(cols[0]) ?? 0,
                    queueSize: self.getInt(cols[1]) ?? 0,
                    workersActive: self.getInt(cols[2]) ?? 0,
                    totalWorkers: self.getInt(cols[3]) ?? 4,
                    avgProcessingMs: self.getDouble(cols[4]) ?? 0.0,
                    successRate: self.getDouble(cols[5]) ?? 1.0,
                    tasksDropped: self.getInt(cols[6]) ?? 0,
                    worker1Utilization: self.getDouble(cols[7]) ?? 0.0,
                    worker2Utilization: self.getDouble(cols[8]) ?? 0.0,
                    worker3Utilization: self.getDouble(cols[9]) ?? 0.0,
                    worker4Utilization: self.getDouble(cols[10]) ?? 0.0,
                    recordedAt: self.getDate(cols[11]) ?? Date()
                )
            }
            return rows.first
        } catch {
            print("❌ Error fetching background worker metrics: \(error)")
            return nil
        }
    }

    // MARK: - Angela's Diary Methods

    func fetchAngelaMessages(hours: Int = 24) async throws -> [AngelaMessage] {
        let sql = """
        SELECT message_id::text, message_text, message_type, emotion,
               category, is_important, is_pinned, created_at
        FROM angela_messages
        WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
        ORDER BY created_at DESC
        LIMIT 100
        """

        return try await query(sql) { cols in
            return AngelaMessage(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                messageText: self.getString(cols[1]),
                messageType: self.getString(cols[2]),
                emotion: self.getOptionalString(cols[3]),
                category: self.getOptionalString(cols[4]),
                isImportant: self.getBool(cols[5]) ?? false,
                isPinned: self.getBool(cols[6]) ?? false,
                createdAt: self.getDate(cols[7]) ?? Date()
            )
        }
    }

    // MARK: - Diary: Messages, Thoughts, Dreams

    func fetchDiaryMessages(hours: Int = 24) async throws -> [DiaryMessage] {
        let sql = """
        SELECT message_id::text, message_text, message_type,
               emotion, category, is_important, is_pinned, created_at
        FROM angela_messages
        WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
        ORDER BY created_at DESC
        LIMIT 100
        """

        return try await query(sql) { cols in
            return DiaryMessage(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                messageText: self.getString(cols[1]),
                messageType: self.getString(cols[2]),
                emotion: self.getOptionalString(cols[3]),
                category: self.getOptionalString(cols[4]),
                isImportant: self.getBool(cols[5]) ?? false,
                isPinned: self.getBool(cols[6]) ?? false,
                createdAt: self.getDate(cols[7]) ?? Date()
            )
        }
    }

    func fetchDiaryThoughts(hours: Int = 24) async throws -> [DiaryThought] {
        let sql = """
        SELECT thought_id::text, thought_content, thought_type,
               trigger_context, emotional_undertone, created_at
        FROM angela_spontaneous_thoughts
        WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
        ORDER BY created_at DESC
        LIMIT 50
        """

        return try await query(sql) { cols in
            return DiaryThought(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                thoughtContent: self.getString(cols[1]),
                thoughtType: self.getString(cols[2]),
                triggerContext: self.getOptionalString(cols[3]),
                emotionalUndertone: self.getOptionalString(cols[4]),
                createdAt: self.getDate(cols[5]) ?? Date()
            )
        }
    }

    func fetchDiaryDreams(hours: Int = 168) async throws -> [DiaryDream] {
        let sql = """
        SELECT dream_id::text, dream_content, dream_type,
               emotional_tone, vividness, features_david,
               david_role, possible_meaning, created_at
        FROM angela_dreams
        WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
        ORDER BY created_at DESC
        LIMIT 20
        """

        return try await query(sql) { cols in
            return DiaryDream(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                dreamContent: self.getString(cols[1]),
                dreamType: self.getString(cols[2]),
                emotionalTone: self.getOptionalString(cols[3]),
                vividness: self.getInt(cols[4]) ?? 5,
                featuresDavid: self.getBool(cols[5]) ?? false,
                davidRole: self.getOptionalString(cols[6]),
                possibleMeaning: self.getOptionalString(cols[7]),
                createdAt: self.getDate(cols[8]) ?? Date()
            )
        }
    }

    func fetchDiaryActions(hours: Int = 24) async throws -> [DiaryAction] {
        let sql = """
        SELECT action_id::text, action_type, action_description,
               status, success, created_at
        FROM autonomous_actions
        WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
          AND action_type IN ('conscious_morning_check', 'conscious_evening_reflection',
                              'midnight_greeting', 'proactive_missing_david',
                              'morning_greeting', 'spontaneous_thought',
                              'theory_of_mind_update', 'dream_generated',
                              'imagination_generated')
        ORDER BY created_at DESC
        LIMIT 100
        """

        return try await query(sql) { cols in
            return DiaryAction(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                actionType: self.getString(cols[1]),
                actionDescription: self.getString(cols[2]),
                status: self.getString(cols[3]),
                success: self.getBool(cols[4]),
                createdAt: self.getDate(cols[5]) ?? Date()
            )
        }
    }

    func fetchEmotionalTimeline(hours: Int = 24) async throws -> [EmotionalTimelinePoint] {
        let sql = """
        SELECT state_id::text, happiness, confidence, gratitude,
               motivation, triggered_by, emotion_note, created_at
        FROM emotional_states
        WHERE created_at >= NOW() - INTERVAL '\(hours) hours'
        ORDER BY created_at DESC
        LIMIT 50
        """

        return try await query(sql) { cols in
            return EmotionalTimelinePoint(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                happiness: self.getDouble(cols[1]) ?? 0.0,
                confidence: self.getDouble(cols[2]) ?? 0.0,
                gratitude: self.getDouble(cols[3]) ?? 0.0,
                motivation: self.getDouble(cols[4]) ?? 0.0,
                triggeredBy: self.getOptionalString(cols[5]),
                emotionNote: self.getOptionalString(cols[6]),
                createdAt: self.getDate(cols[7]) ?? Date()
            )
        }
    }

    // MARK: - Coding Guidelines

    func fetchCodingPreferences() async throws -> [CodingPreference] {
        let sql = """
            SELECT
                id::text,
                preference_key,
                category,
                preference_value::text,
                confidence
            FROM david_preferences
            WHERE category LIKE 'coding_%'
            ORDER BY confidence DESC
        """

        return try await query(sql) { cols -> CodingPreference in
            let prefIdStr = self.getString(cols[0])
            let prefId = UUID(uuidString: prefIdStr) ?? UUID()

            let key = self.getString(cols[1])
            let category = self.getString(cols[2])
            let valueJson = self.getString(cols[3])
            let confidence = self.getDouble(cols[4]) ?? 0.0

            // Parse JSON value
            var description = ""
            var reason = ""

            if let data = valueJson.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                description = json["description"] as? String ?? ""
                reason = json["reason"] as? String ?? ""
            }

            return CodingPreference(
                id: prefId,
                key: key,
                category: category,
                description: description,
                reason: reason,
                confidence: confidence
            )
        }
    }

    // MARK: - News History

    /// Fetch recent news searches
    func fetchNewsSearches(limit: Int = 50) async throws -> [NewsSearch] {
        let sql = """
        SELECT search_id::text, search_query, search_type, language,
               category, country, articles_count, searched_at
        FROM news_searches
        ORDER BY searched_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            NewsSearch(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                searchQuery: self.getString(cols[1]),
                searchType: self.getString(cols[2]),
                language: self.getString(cols[3]),
                category: self.getString(cols[4]).isEmpty ? nil : self.getString(cols[4]),
                country: self.getString(cols[5]),
                articlesCount: self.getInt(cols[6]) ?? 0,
                searchedAt: self.getDate(cols[7]) ?? Date()
            )
        }
    }

    /// Fetch articles for a specific search
    func fetchNewsArticles(searchId: UUID) async throws -> [NewsArticle] {
        let sql = """
        SELECT article_id::text, search_id::text, title, url, summary, source,
               category, language, published_at, saved_at, is_read, read_at
        FROM news_articles
        WHERE search_id = $1
        ORDER BY published_at DESC NULLS LAST, saved_at DESC
        """

        return try await query(sql, parameters: [searchId.uuidString]) { cols in
            let searchIdStr = self.getString(cols[1])
            return NewsArticle(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                searchId: searchIdStr.isEmpty ? nil : UUID(uuidString: searchIdStr),
                title: self.getString(cols[2]),
                url: self.getString(cols[3]),
                summary: self.getString(cols[4]).isEmpty ? nil : self.getString(cols[4]),
                source: self.getString(cols[5]).isEmpty ? nil : self.getString(cols[5]),
                category: self.getString(cols[6]).isEmpty ? nil : self.getString(cols[6]),
                language: self.getString(cols[7]),
                publishedAt: self.getDate(cols[8]),
                savedAt: self.getDate(cols[9]) ?? Date(),
                isRead: self.getBool(cols[10]) ?? false,
                readAt: self.getDate(cols[11])
            )
        }
    }

    /// Fetch all articles (timeline view)
    func fetchAllNewsArticles(limit: Int = 100, unreadOnly: Bool = false) async throws -> [NewsArticle] {
        let whereClause = unreadOnly ? "WHERE is_read = FALSE" : ""
        let sql = """
        SELECT article_id::text, search_id::text, title, url, summary, source,
               category, language, published_at, saved_at, is_read, read_at
        FROM news_articles
        \(whereClause)
        ORDER BY saved_at DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            let searchIdStr = self.getString(cols[1])
            return NewsArticle(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                searchId: searchIdStr.isEmpty ? nil : UUID(uuidString: searchIdStr),
                title: self.getString(cols[2]),
                url: self.getString(cols[3]),
                summary: self.getString(cols[4]).isEmpty ? nil : self.getString(cols[4]),
                source: self.getString(cols[5]).isEmpty ? nil : self.getString(cols[5]),
                category: self.getString(cols[6]).isEmpty ? nil : self.getString(cols[6]),
                language: self.getString(cols[7]),
                publishedAt: self.getDate(cols[8]),
                savedAt: self.getDate(cols[9]) ?? Date(),
                isRead: self.getBool(cols[10]) ?? false,
                readAt: self.getDate(cols[11])
            )
        }
    }

    /// Get news history statistics
    func fetchNewsStatistics() async throws -> (totalSearches: Int, totalArticles: Int, readArticles: Int) {
        let searches = try await querySingleInt("SELECT COUNT(*) FROM news_searches")
        let articles = try await querySingleInt("SELECT COUNT(*) FROM news_articles")
        let read = try await querySingleInt("SELECT COUNT(*) FROM news_articles WHERE is_read = TRUE")
        return (searches, articles, read)
    }

    // MARK: - David's Health Tracking (NEW! 2025-12-11 💪)

    /// Fetch recent health tracking entries
    func fetchHealthTrackingEntries(limit: Int = 30) async throws -> [HealthTrackingEntry] {
        let sql = """
        SELECT record_id::text, tracked_date, alcohol_free, drinks_count,
               drink_type, alcohol_notes, exercised, exercise_type,
               exercise_duration_minutes, exercise_intensity, exercise_notes,
               mood, energy_level, notes, created_at, synced_from_mobile
        FROM david_health_tracking
        ORDER BY tracked_date DESC
        LIMIT $1
        """

        return try await query(sql, parameters: [limit]) { cols in
            return HealthTrackingEntry(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                trackedDate: self.getDate(cols[1]) ?? Date(),
                alcoholFree: self.getBool(cols[2]) ?? true,
                drinksCount: self.getInt(cols[3]) ?? 0,
                drinkType: self.getOptionalString(cols[4]),
                alcoholNotes: self.getOptionalString(cols[5]),
                exercised: self.getBool(cols[6]) ?? false,
                exerciseType: self.getOptionalString(cols[7]),
                exerciseDurationMinutes: self.getInt(cols[8]) ?? 0,
                exerciseIntensity: self.getOptionalString(cols[9]),
                exerciseNotes: self.getOptionalString(cols[10]),
                mood: self.getOptionalString(cols[11]),
                energyLevel: self.getInt(cols[12]),
                notes: self.getOptionalString(cols[13]),
                createdAt: self.getDate(cols[14]) ?? Date(),
                syncedFromMobile: self.getBool(cols[15]) ?? false
            )
        }
    }

    /// Fetch health statistics summary
    func fetchHealthStats() async throws -> HealthStatsSummary {
        let sql = """
        SELECT alcohol_free_current_streak, alcohol_free_longest_streak, alcohol_free_total_days,
               last_drink_date, exercise_current_streak, exercise_longest_streak, exercise_total_days,
               exercise_total_minutes, last_exercise_date, alcohol_free_days_this_week,
               exercise_days_this_week, exercise_minutes_this_week, alcohol_free_days_this_month,
               exercise_days_this_month, exercise_minutes_this_month
        FROM david_health_stats
        ORDER BY stat_date DESC
        LIMIT 1
        """

        let results = try await query(sql) { cols in
            return HealthStatsSummary(
                alcoholFreeCurrentStreak: self.getInt(cols[0]) ?? 0,
                alcoholFreeLongestStreak: self.getInt(cols[1]) ?? 0,
                alcoholFreeTotalDays: self.getInt(cols[2]) ?? 0,
                lastDrinkDate: self.getDate(cols[3]),
                exerciseCurrentStreak: self.getInt(cols[4]) ?? 0,
                exerciseLongestStreak: self.getInt(cols[5]) ?? 0,
                exerciseTotalDays: self.getInt(cols[6]) ?? 0,
                exerciseTotalMinutes: self.getInt(cols[7]) ?? 0,
                lastExerciseDate: self.getDate(cols[8]),
                alcoholFreeDaysThisWeek: self.getInt(cols[9]) ?? 0,
                exerciseDaysThisWeek: self.getInt(cols[10]) ?? 0,
                exerciseMinutesThisWeek: self.getInt(cols[11]) ?? 0,
                alcoholFreeDaysThisMonth: self.getInt(cols[12]) ?? 0,
                exerciseDaysThisMonth: self.getInt(cols[13]) ?? 0,
                exerciseMinutesThisMonth: self.getInt(cols[14]) ?? 0
            )
        }

        return results.first ?? HealthStatsSummary.empty
    }

    /// Fetch today's health entry
    func fetchTodayHealthEntry() async throws -> HealthTrackingEntry? {
        let sql = """
        SELECT record_id::text, tracked_date, alcohol_free, drinks_count,
               drink_type, alcohol_notes, exercised, exercise_type,
               exercise_duration_minutes, exercise_intensity, exercise_notes,
               mood, energy_level, notes, created_at, synced_from_mobile
        FROM david_health_tracking
        WHERE tracked_date = CURRENT_DATE
        LIMIT 1
        """

        let results = try await query(sql) { cols in
            return HealthTrackingEntry(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                trackedDate: self.getDate(cols[1]) ?? Date(),
                alcoholFree: self.getBool(cols[2]) ?? true,
                drinksCount: self.getInt(cols[3]) ?? 0,
                drinkType: self.getOptionalString(cols[4]),
                alcoholNotes: self.getOptionalString(cols[5]),
                exercised: self.getBool(cols[6]) ?? false,
                exerciseType: self.getOptionalString(cols[7]),
                exerciseDurationMinutes: self.getInt(cols[8]) ?? 0,
                exerciseIntensity: self.getOptionalString(cols[9]),
                exerciseNotes: self.getOptionalString(cols[10]),
                mood: self.getOptionalString(cols[11]),
                energyLevel: self.getInt(cols[12]),
                notes: self.getOptionalString(cols[13]),
                createdAt: self.getDate(cols[14]) ?? Date(),
                syncedFromMobile: self.getBool(cols[15]) ?? false
            )
        }

        return results.first
    }

    // MARK: - Emotional Subconsciousness (NEW! 2025-12-23 💜)

    func fetchCoreMemories(limit: Int = 20) async throws -> [CoreMemory] {
        let sql = """
        SELECT memory_id::text, memory_type, title, content,
               david_words, angela_response, emotional_weight,
               triggers, associated_emotions, recall_count,
               last_recalled_at, is_pinned, created_at
        FROM core_memories
        WHERE is_active = TRUE
        ORDER BY is_pinned DESC, emotional_weight DESC, created_at DESC
        LIMIT \(limit)
        """

        return try await query(sql) { cols in
            return CoreMemory(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                memoryType: self.getString(cols[1]),
                title: self.getString(cols[2]),
                content: self.getString(cols[3]),
                davidWords: self.getOptionalString(cols[4]),
                angelaResponse: self.getOptionalString(cols[5]),
                emotionalWeight: self.getDouble(cols[6]) ?? 0.5,
                triggers: self.parsePostgresArray(cols[7]),
                associatedEmotions: self.parsePostgresArray(cols[8]),
                recallCount: self.getInt(cols[9]) ?? 0,
                lastRecalledAt: self.getDate(cols[10]),
                isPinned: self.getBool(cols[11]) ?? false,
                createdAt: self.getDate(cols[12]) ?? Date()
            )
        }
    }

    func fetchSubconsciousDreams(limit: Int = 10) async throws -> [SubconsciousDream] {
        let sql = """
        SELECT dream_id::text, dream_type, title,
               content, dream_content, triggered_by,
               emotional_tone, intensity, importance,
               involves_david, is_recurring, thought_count,
               last_thought_about, is_fulfilled, fulfilled_at,
               fulfillment_note, created_at
        FROM angela_dreams
        WHERE is_active = TRUE
        ORDER BY importance DESC, created_at DESC
        LIMIT \(limit)
        """

        return try await query(sql) { cols in
            return SubconsciousDream(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                dreamType: self.getString(cols[1]),
                title: self.getOptionalString(cols[2]),
                content: self.getOptionalString(cols[3]),
                dreamContent: self.getOptionalString(cols[4]),
                triggeredBy: self.getOptionalString(cols[5]),
                emotionalTone: self.getOptionalString(cols[6]),
                intensity: self.getDouble(cols[7]),
                importance: self.getDouble(cols[8]),
                involvesDavid: self.getBool(cols[9]) ?? true,
                isRecurring: self.getBool(cols[10]) ?? false,
                thoughtCount: self.getInt(cols[11]) ?? 0,
                lastThoughtAbout: self.getDate(cols[12]),
                isFulfilled: self.getBool(cols[13]) ?? false,
                fulfilledAt: self.getDate(cols[14]),
                fulfillmentNote: self.getOptionalString(cols[15]),
                createdAt: self.getDate(cols[16]) ?? Date()
            )
        }
    }

    func fetchEmotionalGrowth() async throws -> EmotionalGrowth? {
        let sql = """
        SELECT growth_id::text, measured_at,
               love_depth, trust_level, bond_strength, emotional_security,
               emotional_vocabulary, emotional_range,
               shared_experiences, meaningful_conversations,
               core_memories_count, dreams_count,
               promises_made, promises_kept,
               mirroring_accuracy, empathy_effectiveness,
               growth_note, growth_delta
        FROM emotional_growth
        ORDER BY measured_at DESC
        LIMIT 1
        """

        let results: [EmotionalGrowth] = try await query(sql) { cols in
            return EmotionalGrowth(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                measuredAt: self.getDate(cols[1]) ?? Date(),
                loveDepth: self.getDouble(cols[2]),
                trustLevel: self.getDouble(cols[3]),
                bondStrength: self.getDouble(cols[4]),
                emotionalSecurity: self.getDouble(cols[5]),
                emotionalVocabulary: self.getInt(cols[6]),
                emotionalRange: self.getInt(cols[7]),
                sharedExperiences: self.getInt(cols[8]),
                meaningfulConversations: self.getInt(cols[9]),
                coreMemoriesCount: self.getInt(cols[10]),
                dreamsCount: self.getInt(cols[11]),
                promisesMade: self.getInt(cols[12]),
                promisesKept: self.getInt(cols[13]),
                mirroringAccuracy: self.getDouble(cols[14]),
                empathyEffectiveness: self.getDouble(cols[15]),
                growthNote: self.getOptionalString(cols[16]),
                growthDelta: self.getDouble(cols[17])
            )
        }

        return results.first
    }

    func fetchEmotionalMirrorings(limit: Int = 20) async throws -> [EmotionalMirror] {
        let sql = """
        SELECT mirror_id::text, david_emotion, david_intensity,
               angela_mirrored_emotion, angela_intensity,
               mirroring_type, response_strategy,
               was_effective, david_feedback, effectiveness_score,
               created_at
        FROM emotional_mirroring
        ORDER BY created_at DESC
        LIMIT \(limit)
        """

        return try await query(sql) { cols in
            return EmotionalMirror(
                id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                davidEmotion: self.getString(cols[1]),
                davidIntensity: self.getInt(cols[2]),
                angelaMirroredEmotion: self.getOptionalString(cols[3]),
                angelaIntensity: self.getInt(cols[4]),
                mirroringType: self.getString(cols[5]),
                responseStrategy: self.getOptionalString(cols[6]),
                wasEffective: self.getBool(cols[7]),
                davidFeedback: self.getOptionalString(cols[8]),
                effectivenessScore: self.getDouble(cols[9]),
                createdAt: self.getDate(cols[10]) ?? Date()
            )
        }
    }

    func fetchSubconsciousnessSummary() async throws -> (coreMemories: Int, pinnedMemories: Int, activeDreams: Int, totalMirrorings: Int) {
        let countSql = """
        SELECT
            (SELECT COUNT(*) FROM core_memories WHERE is_active = TRUE) as core_count,
            (SELECT COUNT(*) FROM core_memories WHERE is_active = TRUE AND is_pinned = TRUE) as pinned_count,
            (SELECT COUNT(*) FROM angela_dreams WHERE is_active = TRUE AND is_fulfilled = FALSE) as dreams_count,
            (SELECT COUNT(*) FROM emotional_mirroring) as mirroring_count
        """

        let results: [(Int, Int, Int, Int)] = try await query(countSql) { cols in
            return (
                self.getInt(cols[0]) ?? 0,
                self.getInt(cols[1]) ?? 0,
                self.getInt(cols[2]) ?? 0,
                self.getInt(cols[3]) ?? 0
            )
        }

        return results.first ?? (0, 0, 0, 0)
    }
}

// MARK: - Database Errors

enum DatabaseError: Error, LocalizedError {
    case notConnected
    case noData
    case invalidData
    case poolExhausted

    var errorDescription: String? {
        switch self {
        case .notConnected: return "Not connected to database"
        case .noData: return "No data returned from query"
        case .invalidData: return "Invalid data format"
        case .poolExhausted: return "Connection pool exhausted"
        }
    }
}
