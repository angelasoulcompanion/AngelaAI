//
//  DatabaseService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  SQLite database service for offline storage
//

import Foundation
import SQLite3
import Combine

class DatabaseService: ObservableObject {
    static let shared = DatabaseService()

    // SQLite destructor constant for proper string handling
    private let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    private var db: OpaquePointer?
    private let dbPath: String

    @Published var experiences: [Experience] = []
    @Published var emotions: [EmotionCapture] = []
    @Published var chatMessages: [ChatMessage] = []
    @Published var healthEntries: [HealthEntry] = []
    @Published var healthStats: HealthStats = HealthStats()

    private init() {
        // Database path in Documents directory
        let paths = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)
        dbPath = paths[0].appendingPathComponent("angela_mobile.db").path
        print("💾 Database path: \(dbPath)")
    }

    // MARK: - Initialization

    func initialize() {
        // Open database
        if sqlite3_open(dbPath, &db) != SQLITE_OK {
            print("❌ Error opening database")
            return
        }

        print("✅ Database opened successfully")

        // Create tables
        createTables()

        // Run database migrations
        migrateDatabase()

        // Load data
        loadData()
    }

    // MARK: - Reset Database (for development)
    func resetDatabase() {
        // Close database first
        sqlite3_close(db)

        // Delete database file
        do {
            try FileManager.default.removeItem(atPath: dbPath)
            print("🗑️ Database deleted successfully")
        } catch {
            print("❌ Error deleting database: \(error)")
        }

        // Reinitialize
        initialize()
        print("✅ Database reset complete")
    }

    // MARK: - Database Migrations
    private func migrateDatabase() {
        print("🔄 Running database migrations...")

        // Migration 1: Add emotion column to experiences table (2025-11-16)
        migrateAddColumn(tableName: "experiences", columnName: "emotion", columnType: "TEXT", migrationName: "emotion")

        // Migration 2: Add david_mood column (2025-11-16)
        migrateAddColumn(tableName: "experiences", columnName: "david_mood", columnType: "TEXT", migrationName: "david_mood")

        // Migration 3: Add importance_level column (2025-11-16)
        migrateAddColumn(tableName: "experiences", columnName: "importance_level", columnType: "INTEGER", migrationName: "importance_level")

        // Migration 4: Add memorable_moments column (2025-11-16)
        migrateAddColumn(tableName: "experiences", columnName: "memorable_moments", columnType: "TEXT", migrationName: "memorable_moments")

        // Migration 5: Add image_captions column (2025-11-16)
        migrateAddColumn(tableName: "experiences", columnName: "image_captions", columnType: "TEXT", migrationName: "image_captions")

        print("✅ Database migrations complete")
    }

    // Helper function to add a column if it doesn't exist
    private func migrateAddColumn(tableName: String, columnName: String, columnType: String, migrationName: String) {
        let checkColumn = """
        SELECT COUNT(*) as count FROM pragma_table_info('\(tableName)') WHERE name='\(columnName)';
        """

        var statement: OpaquePointer?
        if sqlite3_prepare_v2(db, checkColumn, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_ROW {
                let count = sqlite3_column_int(statement, 0)
                if count == 0 {
                    print("📝 Adding '\(columnName)' column to \(tableName) table...")
                    let addColumn = "ALTER TABLE \(tableName) ADD COLUMN \(columnName) \(columnType);"
                    executeSQL(addColumn, name: "add_\(migrationName)_column")
                    print("✅ Migration: \(columnName) column added")
                } else {
                    print("✅ \(columnName) column already exists")
                }
            }
        }
        sqlite3_finalize(statement)
    }

    private func createTables() {
        // Experiences table (enhanced with voice_notes and videos)
        let createExperiencesTable = """
        CREATE TABLE IF NOT EXISTS experiences (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            photos TEXT,
            voice_notes TEXT,
            videos TEXT,
            latitude REAL,
            longitude REAL,
            place_name TEXT,
            area TEXT,
            rating INTEGER,
            emotion TEXT,
            emotional_intensity INTEGER,
            david_mood TEXT,
            importance_level INTEGER,
            memorable_moments TEXT,
            image_captions TEXT,
            experienced_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            is_favorite INTEGER DEFAULT 0
        );
        """

        // Emotions table
        let createEmotionsTable = """
        CREATE TABLE IF NOT EXISTS emotions_captured (
            id TEXT PRIMARY KEY,
            emotion TEXT NOT NULL,
            intensity INTEGER NOT NULL,
            context TEXT,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        );
        """

        // Chat messages table
        let createChatMessagesTable = """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            speaker TEXT NOT NULL,
            message TEXT NOT NULL,
            emotion TEXT,
            timestamp TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        );
        """

        // Tags table (Feature 4: Tags System)
        let createTagsTable = """
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT,
            created_at TEXT NOT NULL
        );
        """

        // Experience Tags junction table
        let createExperienceTagsTable = """
        CREATE TABLE IF NOT EXISTS experience_tags (
            experience_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            PRIMARY KEY (experience_id, tag_id),
            FOREIGN KEY (experience_id) REFERENCES experiences(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );
        """

        // Collections table (Feature 16: Collections)
        let createCollectionsTable = """
        CREATE TABLE IF NOT EXISTS collections (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            cover_photo TEXT,
            created_at TEXT NOT NULL
        );
        """

        // Collection Items junction table
        let createCollectionItemsTable = """
        CREATE TABLE IF NOT EXISTS collection_items (
            collection_id TEXT NOT NULL,
            experience_id TEXT NOT NULL,
            added_at TEXT NOT NULL,
            PRIMARY KEY (collection_id, experience_id),
            FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
            FOREIGN KEY (experience_id) REFERENCES experiences(id) ON DELETE CASCADE
        );
        """

        // Achievements table (Feature 29: Achievements)
        let createAchievementsTable = """
        CREATE TABLE IF NOT EXISTS achievements (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            requirement INTEGER NOT NULL,
            unlocked_at TEXT,
            achievement_type TEXT NOT NULL
        );
        """

        // User Stats table (Features 29-31: Gamification)
        let createUserStatsTable = """
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_experiences INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_capture_date TEXT,
            total_xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
        );
        """

        // Insert initial user stats row
        let insertInitialStats = """
        INSERT OR IGNORE INTO user_stats (id, total_experiences, current_streak, longest_streak, total_xp, level)
        VALUES (1, 0, 0, 0, 0, 1);
        """

        // Health Tracking table (NEW: 2025-12-11)
        let createHealthTrackingTable = """
        CREATE TABLE IF NOT EXISTS health_tracking (
            id TEXT PRIMARY KEY,
            tracked_date TEXT NOT NULL UNIQUE,
            alcohol_free INTEGER DEFAULT 1,
            drinks_count INTEGER DEFAULT 0,
            drink_type TEXT,
            alcohol_notes TEXT,
            exercised INTEGER DEFAULT 0,
            exercise_type TEXT,
            exercise_duration_minutes INTEGER DEFAULT 0,
            exercise_intensity TEXT,
            exercise_notes TEXT,
            mood TEXT,
            energy_level INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        );
        """

        // Health Stats table (NEW: 2025-12-11)
        let createHealthStatsTable = """
        CREATE TABLE IF NOT EXISTS health_stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            alcohol_free_current_streak INTEGER DEFAULT 0,
            alcohol_free_longest_streak INTEGER DEFAULT 0,
            alcohol_free_total_days INTEGER DEFAULT 0,
            last_drink_date TEXT,
            exercise_current_streak INTEGER DEFAULT 0,
            exercise_longest_streak INTEGER DEFAULT 0,
            exercise_total_days INTEGER DEFAULT 0,
            exercise_total_minutes INTEGER DEFAULT 0,
            last_exercise_date TEXT,
            alcohol_free_days_this_week INTEGER DEFAULT 0,
            alcohol_free_days_this_month INTEGER DEFAULT 0,
            exercise_days_this_week INTEGER DEFAULT 0,
            exercise_days_this_month INTEGER DEFAULT 0,
            exercise_minutes_this_week INTEGER DEFAULT 0,
            exercise_minutes_this_month INTEGER DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        """

        // Insert initial health stats row
        let insertInitialHealthStats = """
        INSERT OR IGNORE INTO health_stats (id, updated_at)
        VALUES (1, '\(ISO8601DateFormatter().string(from: Date()))');
        """

        // Execute table creation
        executeSQL(createExperiencesTable, name: "experiences")
        executeSQL(createEmotionsTable, name: "emotions_captured")
        executeSQL(createChatMessagesTable, name: "chat_messages")
        executeSQL(createTagsTable, name: "tags")
        executeSQL(createExperienceTagsTable, name: "experience_tags")
        executeSQL(createCollectionsTable, name: "collections")
        executeSQL(createCollectionItemsTable, name: "collection_items")
        executeSQL(createAchievementsTable, name: "achievements")
        executeSQL(createUserStatsTable, name: "user_stats")
        executeSQL(insertInitialStats, name: "initial_user_stats")
        executeSQL(createHealthTrackingTable, name: "health_tracking")
        executeSQL(createHealthStatsTable, name: "health_stats")
        executeSQL(insertInitialHealthStats, name: "initial_health_stats")
    }

    private func executeSQL(_ sql: String, name: String) {
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Table '\(name)' created successfully")
            } else {
                print("❌ Error creating table '\(name)'")
            }
        } else {
            print("❌ Error preparing statement for '\(name)'")
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Load Data

    private func loadData() {
        loadExperiences()
        loadEmotions()
        loadChatMessages()
        loadHealthEntries()
        loadHealthStats()
    }

    private func loadExperiences() {
        experiences = []

        let query = """
        SELECT id, title, description, photos, latitude, longitude,
               place_name, area, rating, emotion, emotional_intensity,
               david_mood, importance_level, memorable_moments, image_captions,
               experienced_at, synced, created_at
        FROM experiences
        ORDER BY experienced_at DESC
        """
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let exp = parseExperience(from: statement) {
                    experiences.append(exp)
                }
            }
        }

        sqlite3_finalize(statement)
        print("📊 Loaded \(experiences.count) experiences")
    }

    private func loadEmotions() {
        emotions = []

        let query = "SELECT * FROM emotions_captured ORDER BY created_at DESC"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let emotion = parseEmotion(from: statement) {
                    emotions.append(emotion)
                }
            }
        }

        sqlite3_finalize(statement)
        print("📊 Loaded \(emotions.count) emotions")
    }

    // MARK: - Insert Methods

    func insertExperience(_ experience: Experience) {
        let query = """
        INSERT INTO experiences (
            id, title, description, photos, voice_notes, videos,
            latitude, longitude, place_name, area, rating, emotion, emotional_intensity,
            david_mood, importance_level, memorable_moments, image_captions,
            experienced_at, synced, created_at, is_favorite
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            // Bind values (using SQLITE_TRANSIENT to copy strings)
            sqlite3_bind_text(statement, 1, (experience.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 2, (experience.title as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 3, (experience.description as NSString).utf8String, -1, SQLITE_TRANSIENT)

            // Photos as JSON array
            let photosJSON = (try? JSONEncoder().encode(experience.photos)).flatMap { String(data: $0, encoding: .utf8) } ?? "[]"
            sqlite3_bind_text(statement, 4, (photosJSON as NSString).utf8String, -1, SQLITE_TRANSIENT)

            // Voice notes as JSON array (Feature 2)
            let voiceNotesJSON = (try? JSONEncoder().encode(experience.voiceNotes)).flatMap { String(data: $0, encoding: .utf8) } ?? "[]"
            sqlite3_bind_text(statement, 5, (voiceNotesJSON as NSString).utf8String, -1, SQLITE_TRANSIENT)

            // Videos as JSON array (Feature 3)
            let videosJSON = (try? JSONEncoder().encode(experience.videos)).flatMap { String(data: $0, encoding: .utf8) } ?? "[]"
            sqlite3_bind_text(statement, 6, (videosJSON as NSString).utf8String, -1, SQLITE_TRANSIENT)

            bindOptionalDouble(statement, 7, experience.latitude)
            bindOptionalDouble(statement, 8, experience.longitude)
            bindOptionalString(statement, 9, experience.placeName)
            bindOptionalString(statement, 10, experience.area)
            bindOptionalInt(statement, 11, experience.rating)
            bindOptionalString(statement, 12, experience.emotion)
            bindOptionalInt(statement, 13, experience.emotionalIntensity)
            bindOptionalString(statement, 14, experience.davidMood)  // ✅ New field
            bindOptionalInt(statement, 15, experience.importanceLevel)  // ✅ New field
            bindOptionalString(statement, 16, experience.memorableMoments)  // ✅ New field

            // Image captions as JSON array
            let captionsJSON = (try? JSONEncoder().encode(experience.imageCaptions)).flatMap { String(data: $0, encoding: .utf8) } ?? "[]"
            sqlite3_bind_text(statement, 17, (captionsJSON as NSString).utf8String, -1, SQLITE_TRANSIENT)  // ✅ New field

            let experiencedAtString = ISO8601DateFormatter().string(from: experience.experiencedAt)
            sqlite3_bind_text(statement, 18, (experiencedAtString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 19, experience.synced ? 1 : 0)
            let createdAtString = ISO8601DateFormatter().string(from: experience.createdAt)
            sqlite3_bind_text(statement, 20, (createdAtString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 21, experience.isFavorite ? 1 : 0)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Experience inserted successfully")
                loadExperiences()  // Reload
            } else {
                let errorMessage = String(cString: sqlite3_errmsg(db))
                let errorCode = sqlite3_errcode(db)
                print("❌ Error inserting experience: \(errorMessage) (code: \(errorCode))")
            }
        } else {
            let errorMessage = String(cString: sqlite3_errmsg(db))
            print("❌ Error preparing insert statement: \(errorMessage)")
        }

        sqlite3_finalize(statement)
    }

    func insertEmotion(_ emotion: EmotionCapture) {
        let query = """
        INSERT INTO emotions_captured (id, emotion, intensity, context, created_at, synced)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        print("💾 DatabaseService.insertEmotion() called:")
        print("   ID: \(emotion.id.uuidString)")
        print("   Emotion: \(emotion.emotion)")
        print("   Intensity: \(emotion.intensity)")
        print("   Context: \(emotion.context ?? "nil")")
        print("   Created at: \(emotion.createdAt)")

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (emotion.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 2, (emotion.emotion as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 3, Int32(emotion.intensity))
            bindOptionalString(statement, 4, emotion.context)

            let dateString = ISO8601DateFormatter().string(from: emotion.createdAt)
            sqlite3_bind_text(statement, 5, (dateString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 6, emotion.synced ? 1 : 0)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Emotion inserted successfully into database")
                loadEmotions()
                print("📊 Total emotions in DB after insert: \(emotions.count)")
            } else {
                let errorMessage = String(cString: sqlite3_errmsg(db))
                let errorCode = sqlite3_errcode(db)
                print("❌ Error inserting emotion: \(errorMessage) (code: \(errorCode))")
            }
        } else {
            let errorMessage = String(cString: sqlite3_errmsg(db))
            print("❌ Error preparing emotion insert statement: \(errorMessage)")
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Helper Methods

    private func bindOptionalString(_ statement: OpaquePointer?, _ index: Int32, _ value: String?) {
        if let value = value {
            sqlite3_bind_text(statement, index, (value as NSString).utf8String, -1, SQLITE_TRANSIENT)
        } else {
            sqlite3_bind_null(statement, index)
        }
    }

    private func bindOptionalInt(_ statement: OpaquePointer?, _ index: Int32, _ value: Int?) {
        if let value = value {
            sqlite3_bind_int(statement, index, Int32(value))
        } else {
            sqlite3_bind_null(statement, index)
        }
    }

    private func bindOptionalDouble(_ statement: OpaquePointer?, _ index: Int32, _ value: Double?) {
        if let value = value {
            sqlite3_bind_double(statement, index, value)
        } else {
            sqlite3_bind_null(statement, index)
        }
    }

    // MARK: - Parse Methods

    private func parseExperience(from statement: OpaquePointer?) -> Experience? {
        guard let statement = statement else { return nil }

        // Debug: Print raw column values
        let columnCount = sqlite3_column_count(statement)
        print("📊 Column count: \(columnCount)")

        for i in 0..<columnCount {
            let columnName = String(cString: sqlite3_column_name(statement, i))
            let columnType = sqlite3_column_type(statement, i)
            let valueText = columnType != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, i)) : "NULL"
            print("   [\(i)] \(columnName) = '\(valueText)' (type: \(columnType))")
        }

        let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) ?? UUID()
        let title = String(cString: sqlite3_column_text(statement, 1))
        let description = String(cString: sqlite3_column_text(statement, 2))

        // Parse photos JSON
        let photosData = String(cString: sqlite3_column_text(statement, 3)).data(using: .utf8)
        let photos = (try? JSONDecoder().decode([String].self, from: photosData ?? Data())) ?? []

        let latitude = sqlite3_column_type(statement, 4) != SQLITE_NULL ? sqlite3_column_double(statement, 4) : nil
        let longitude = sqlite3_column_type(statement, 5) != SQLITE_NULL ? sqlite3_column_double(statement, 5) : nil
        let placeName = sqlite3_column_type(statement, 6) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 6)) : nil
        let area = sqlite3_column_type(statement, 7) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 7)) : nil
        let rating = sqlite3_column_type(statement, 8) != SQLITE_NULL ? Int(sqlite3_column_int(statement, 8)) : nil
        let emotion = sqlite3_column_type(statement, 9) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 9)) : nil
        let emotionalIntensity = sqlite3_column_type(statement, 10) != SQLITE_NULL ? Int(sqlite3_column_int(statement, 10)) : nil

        // ✅ NEW FIELDS
        let davidMood = sqlite3_column_type(statement, 11) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 11)) : nil
        let importanceLevel = sqlite3_column_type(statement, 12) != SQLITE_NULL ? Int(sqlite3_column_int(statement, 12)) : nil
        let memorableMoments = sqlite3_column_type(statement, 13) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 13)) : nil

        // Parse image_captions JSON
        let captionsData = sqlite3_column_type(statement, 14) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 14)).data(using: .utf8) : nil
        let imageCaptions = (try? JSONDecoder().decode([String].self, from: captionsData ?? Data())) ?? []

        // ✅ UPDATED INDICES (shifted by 4 because of new fields)
        let experiencedAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 15))) ?? Date()
        let synced = sqlite3_column_int(statement, 16) == 1
        let createdAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 17))) ?? Date()

        print("🔍 Parsed experience: title='\(title)', photos=\(photos.count), place='\(placeName ?? "nil")', emotion='\(emotion ?? "nil")', mood='\(davidMood ?? "nil")', importance=\(importanceLevel ?? 0), captions=\(imageCaptions.count)")

        return Experience(
            id: id,
            title: title,
            description: description,
            photos: photos,
            latitude: latitude,
            longitude: longitude,
            placeName: placeName,
            area: area,
            rating: rating,
            emotion: emotion,
            emotionalIntensity: emotionalIntensity,
            davidMood: davidMood,  // ✅ NEW
            importanceLevel: importanceLevel,  // ✅ NEW
            memorableMoments: memorableMoments,  // ✅ NEW
            imageCaptions: imageCaptions,  // ✅ NEW
            experiencedAt: experiencedAt,
            synced: synced,
            createdAt: createdAt
        )
    }

    private func parseEmotion(from statement: OpaquePointer?) -> EmotionCapture? {
        guard let statement = statement else { return nil }

        let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) ?? UUID()
        let emotion = String(cString: sqlite3_column_text(statement, 1))
        let intensity = Int(sqlite3_column_int(statement, 2))
        let context = sqlite3_column_type(statement, 3) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 3)) : nil
        let createdAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 4))) ?? Date()
        let synced = sqlite3_column_int(statement, 5) == 1

        return EmotionCapture(
            id: id,
            emotion: emotion,
            intensity: intensity,
            context: context,
            createdAt: createdAt,
            synced: synced
        )
    }

    // MARK: - Update Methods

    func markExperienceAsSynced(_ experienceId: UUID) {
        let query = "UPDATE experiences SET synced = 1 WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (experienceId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Experience \(experienceId) marked as synced")
                loadExperiences()  // Reload to update UI
            } else {
                print("❌ Error marking experience as synced")
            }
        } else {
            print("❌ Error preparing update statement")
        }

        sqlite3_finalize(statement)
    }

    func markEmotionAsSynced(_ emotionId: UUID) {
        let query = "UPDATE emotions_captured SET synced = 1 WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (emotionId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Emotion \(emotionId) marked as synced")
                loadEmotions()  // Reload to update UI
            } else {
                print("❌ Error marking emotion as synced")
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Delete Methods (after successful sync)

    func deleteExperience(_ experienceId: UUID) {
        let query = "DELETE FROM experiences WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (experienceId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("🗑️ Experience \(experienceId) deleted from local DB")
                loadExperiences()  // Reload to update UI
            } else {
                print("❌ Error deleting experience")
            }
        }

        sqlite3_finalize(statement)
    }

    func deleteEmotion(_ emotionId: UUID) {
        let query = "DELETE FROM emotions_captured WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (emotionId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("🗑️ Emotion \(emotionId) deleted from local DB")
                loadEmotions()  // Reload to update UI
            } else {
                print("❌ Error deleting emotion")
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Chat Messages Methods

    private func loadChatMessages() {
        chatMessages = []

        let query = "SELECT * FROM chat_messages ORDER BY timestamp ASC"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let message = parseChatMessage(from: statement) {
                    chatMessages.append(message)
                }
            }
        }

        sqlite3_finalize(statement)
        print("📊 Loaded \(chatMessages.count) chat messages")
    }

    func insertChatMessage(_ message: ChatMessage) {
        let query = """
        INSERT INTO chat_messages (id, speaker, message, emotion, timestamp, synced)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (message.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 2, (message.speaker as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 3, (message.message as NSString).utf8String, -1, SQLITE_TRANSIENT)
            bindOptionalString(statement, 4, message.emotion)

            let dateString = ISO8601DateFormatter().string(from: message.timestamp)
            sqlite3_bind_text(statement, 5, (dateString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 6, message.synced ? 1 : 0)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Chat message inserted successfully")
                loadChatMessages()
            } else {
                print("❌ Error inserting chat message")
            }
        }

        sqlite3_finalize(statement)
    }

    private func parseChatMessage(from statement: OpaquePointer?) -> ChatMessage? {
        guard let statement = statement else { return nil }

        let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) ?? UUID()
        let speaker = String(cString: sqlite3_column_text(statement, 1))
        let message = String(cString: sqlite3_column_text(statement, 2))
        let emotion = sqlite3_column_type(statement, 3) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 3)) : nil
        let timestamp = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 4))) ?? Date()
        let synced = sqlite3_column_int(statement, 5) == 1

        return ChatMessage(
            id: id,
            speaker: speaker,
            message: message,
            emotion: emotion,
            timestamp: timestamp,
            synced: synced
        )
    }

    func markChatMessageAsSynced(_ messageId: UUID) {
        let query = "UPDATE chat_messages SET synced = 1 WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (messageId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Chat message \(messageId) marked as synced")
                loadChatMessages()
            } else {
                print("❌ Error marking chat message as synced")
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Debug/Development Helper

    /// Reset all sync flags to allow re-syncing all data
    /// ⚠️ Use this for debugging when sync fails
    func resetAllSyncFlags() {
        print("🔄 Resetting all sync flags...")

        // Reset experiences
        let resetExperiences = "UPDATE experiences SET synced = 0"
        executeSQL(resetExperiences, name: "reset_experiences_sync")

        // Reset emotions
        let resetEmotions = "UPDATE emotions_captured SET synced = 0"
        executeSQL(resetEmotions, name: "reset_emotions_sync")

        // Reset chat messages
        let resetChat = "UPDATE chat_messages SET synced = 0"
        executeSQL(resetChat, name: "reset_chat_sync")

        // Reload data to update UI
        loadExperiences()
        loadEmotions()
        loadChatMessages()

        let unsyncedExperiences = experiences.filter { !$0.synced }.count
        let unsyncedEmotions = emotions.filter { !$0.synced }.count
        let unsyncedChat = chatMessages.filter { !$0.synced }.count

        print("✅ Sync flags reset!")
        print("   📊 Unsynced experiences: \(unsyncedExperiences)")
        print("   💜 Unsynced emotions: \(unsyncedEmotions)")
        print("   💬 Unsynced chat messages: \(unsyncedChat)")
    }

    func deleteChatMessage(_ messageId: UUID) {
        let query = "DELETE FROM chat_messages WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (messageId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("🗑️ Chat message \(messageId) deleted from local DB")
                loadChatMessages()
            } else {
                print("❌ Error deleting chat message")
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Clear All Chat Messages

    func clearAllChatMessages() {
        let query = "DELETE FROM chat_messages"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_DONE {
                print("🗑️ All chat messages cleared from local DB")
                loadChatMessages()  // Reload to update UI (will be empty)
            } else {
                print("❌ Error clearing all chat messages")
            }
        } else {
            print("❌ Error preparing clear statement")
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Health Tracking Methods (NEW: 2025-12-11) 💜

    private func loadHealthEntries() {
        healthEntries = []

        let query = """
        SELECT id, tracked_date, alcohol_free, drinks_count, drink_type, alcohol_notes,
               exercised, exercise_type, exercise_duration_minutes, exercise_intensity,
               exercise_notes, mood, energy_level, notes, created_at, synced
        FROM health_tracking
        ORDER BY tracked_date DESC
        """
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let entry = parseHealthEntry(from: statement) {
                    healthEntries.append(entry)
                }
            }
        }

        sqlite3_finalize(statement)
        print("💪 Loaded \(healthEntries.count) health entries")
    }

    private func loadHealthStats() {
        // Explicitly specify columns in the order that matches HealthStats struct
        // This ensures columns are retrieved in the correct order regardless of table schema
        let query = """
        SELECT
            id,
            alcohol_free_current_streak,
            alcohol_free_longest_streak,
            alcohol_free_total_days,
            last_drink_date,
            exercise_current_streak,
            exercise_longest_streak,
            exercise_total_days,
            exercise_total_minutes,
            last_exercise_date,
            alcohol_free_days_this_week,
            exercise_days_this_week,
            exercise_minutes_this_week,
            alcohol_free_days_this_month,
            exercise_days_this_month,
            exercise_minutes_this_month
        FROM health_stats WHERE id = 1
        """
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_ROW {
                healthStats = parseHealthStats(from: statement) ?? HealthStats()
            }
        }

        sqlite3_finalize(statement)
        print("📊 Health stats loaded")
    }

    private func parseHealthEntry(from statement: OpaquePointer?) -> HealthEntry? {
        guard let statement = statement else { return nil }

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"

        let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) ?? UUID()
        let trackedDateStr = String(cString: sqlite3_column_text(statement, 1))
        let trackedDate = dateFormatter.date(from: trackedDateStr) ?? Date()

        let alcoholFree = sqlite3_column_int(statement, 2) == 1
        let drinksCount = Int(sqlite3_column_int(statement, 3))
        let drinkType = sqlite3_column_type(statement, 4) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 4)) : nil
        let alcoholNotes = sqlite3_column_type(statement, 5) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 5)) : nil

        let exercised = sqlite3_column_int(statement, 6) == 1
        let exerciseType = sqlite3_column_type(statement, 7) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 7)) : nil
        let exerciseDuration = Int(sqlite3_column_int(statement, 8))
        let exerciseIntensityStr = sqlite3_column_type(statement, 9) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 9)) : nil
        let exerciseIntensity = exerciseIntensityStr != nil ? ExerciseIntensity(rawValue: exerciseIntensityStr!) : nil
        let exerciseNotes = sqlite3_column_type(statement, 10) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 10)) : nil

        let mood = sqlite3_column_type(statement, 11) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 11)) : nil
        let energyLevel = sqlite3_column_type(statement, 12) != SQLITE_NULL ? Int(sqlite3_column_int(statement, 12)) : nil
        let notes = sqlite3_column_type(statement, 13) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 13)) : nil

        let createdAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 14))) ?? Date()
        let synced = sqlite3_column_int(statement, 15) == 1

        return HealthEntry(
            id: id,
            trackedDate: trackedDate,
            alcoholFree: alcoholFree,
            drinksCount: drinksCount,
            drinkType: drinkType,
            alcoholNotes: alcoholNotes,
            exercised: exercised,
            exerciseType: exerciseType,
            exerciseDurationMinutes: exerciseDuration,
            exerciseIntensity: exerciseIntensity,
            exerciseNotes: exerciseNotes,
            mood: mood,
            energyLevel: energyLevel,
            notes: notes,
            createdAt: createdAt,
            synced: synced
        )
    }

    private func parseHealthStats(from statement: OpaquePointer?) -> HealthStats? {
        guard let statement = statement else { return nil }

        // Arguments must match HealthStats struct property order!
        // Weekly: alcoholFreeDaysThisWeek, exerciseDaysThisWeek, exerciseMinutesThisWeek
        // Monthly: alcoholFreeDaysThisMonth, exerciseDaysThisMonth, exerciseMinutesThisMonth
        return HealthStats(
            alcoholFreeCurrentStreak: Int(sqlite3_column_int(statement, 1)),
            alcoholFreeLongestStreak: Int(sqlite3_column_int(statement, 2)),
            alcoholFreeTotalDays: Int(sqlite3_column_int(statement, 3)),
            lastDrinkDate: sqlite3_column_type(statement, 4) != SQLITE_NULL ?
                DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 4))) : nil,
            exerciseCurrentStreak: Int(sqlite3_column_int(statement, 5)),
            exerciseLongestStreak: Int(sqlite3_column_int(statement, 6)),
            exerciseTotalDays: Int(sqlite3_column_int(statement, 7)),
            exerciseTotalMinutes: Int(sqlite3_column_int(statement, 8)),
            lastExerciseDate: sqlite3_column_type(statement, 9) != SQLITE_NULL ?
                DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 9))) : nil,
            // Weekly summaries (must be in this order!)
            alcoholFreeDaysThisWeek: Int(sqlite3_column_int(statement, 10)),
            exerciseDaysThisWeek: Int(sqlite3_column_int(statement, 11)),
            exerciseMinutesThisWeek: Int(sqlite3_column_int(statement, 12)),
            // Monthly summaries (must be in this order!)
            alcoholFreeDaysThisMonth: Int(sqlite3_column_int(statement, 13)),
            exerciseDaysThisMonth: Int(sqlite3_column_int(statement, 14)),
            exerciseMinutesThisMonth: Int(sqlite3_column_int(statement, 15))
        )
    }

    // MARK: - Insert/Update Health Entry

    func insertOrUpdateHealthEntry(_ entry: HealthEntry) {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        let trackedDateStr = dateFormatter.string(from: entry.trackedDate)

        let query = """
        INSERT INTO health_tracking (
            id, tracked_date, alcohol_free, drinks_count, drink_type, alcohol_notes,
            exercised, exercise_type, exercise_duration_minutes, exercise_intensity,
            exercise_notes, mood, energy_level, notes, created_at, synced
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(tracked_date) DO UPDATE SET
            alcohol_free = excluded.alcohol_free,
            drinks_count = excluded.drinks_count,
            drink_type = excluded.drink_type,
            alcohol_notes = excluded.alcohol_notes,
            exercised = excluded.exercised,
            exercise_type = excluded.exercise_type,
            exercise_duration_minutes = excluded.exercise_duration_minutes,
            exercise_intensity = excluded.exercise_intensity,
            exercise_notes = excluded.exercise_notes,
            mood = COALESCE(excluded.mood, mood),
            energy_level = COALESCE(excluded.energy_level, energy_level),
            notes = COALESCE(excluded.notes, notes),
            synced = 0
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (entry.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 2, (trackedDateStr as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 3, entry.alcoholFree ? 1 : 0)
            sqlite3_bind_int(statement, 4, Int32(entry.drinksCount))
            bindOptionalString(statement, 5, entry.drinkType)
            bindOptionalString(statement, 6, entry.alcoholNotes)
            sqlite3_bind_int(statement, 7, entry.exercised ? 1 : 0)
            bindOptionalString(statement, 8, entry.exerciseType)
            sqlite3_bind_int(statement, 9, Int32(entry.exerciseDurationMinutes))
            bindOptionalString(statement, 10, entry.exerciseIntensity?.rawValue)
            bindOptionalString(statement, 11, entry.exerciseNotes)
            bindOptionalString(statement, 12, entry.mood)
            bindOptionalInt(statement, 13, entry.energyLevel)
            bindOptionalString(statement, 14, entry.notes)

            let createdAtString = ISO8601DateFormatter().string(from: entry.createdAt)
            sqlite3_bind_text(statement, 15, (createdAtString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 16, entry.synced ? 1 : 0)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Health entry saved for \(trackedDateStr)")
                loadHealthEntries()
                updateHealthStats()  // Recalculate stats
            } else {
                let errorMessage = String(cString: sqlite3_errmsg(db))
                print("❌ Error saving health entry: \(errorMessage)")
            }
        } else {
            let errorMessage = String(cString: sqlite3_errmsg(db))
            print("❌ Error preparing health entry statement: \(errorMessage)")
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Quick Health Actions

    /// Log today as alcohol-free (quick action)
    func logAlcoholFreeToday(notes: String? = nil) {
        var entry = getTodayHealthEntry() ?? HealthEntry(trackedDate: Date())
        entry.alcoholFree = true
        entry.drinksCount = 0
        if let notes = notes {
            entry.alcoholNotes = notes
        }
        insertOrUpdateHealthEntry(entry)
    }

    /// Log exercise for today
    func logExerciseToday(type: String, minutes: Int, intensity: ExerciseIntensity, notes: String? = nil) {
        var entry = getTodayHealthEntry() ?? HealthEntry(trackedDate: Date())
        entry.exercised = true
        entry.exerciseType = type
        entry.exerciseDurationMinutes = minutes
        entry.exerciseIntensity = intensity
        if let notes = notes {
            entry.exerciseNotes = notes
        }
        insertOrUpdateHealthEntry(entry)
    }

    /// Get today's health entry if exists
    func getTodayHealthEntry() -> HealthEntry? {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        let todayStr = dateFormatter.string(from: Date())

        return healthEntries.first { entry in
            dateFormatter.string(from: entry.trackedDate) == todayStr
        }
    }

    // MARK: - Update Health Stats (Calculate Streaks)

    func updateHealthStats() {
        // Calculate alcohol-free streak
        var alcoholStreak = 0
        let sortedEntries = healthEntries.sorted { $0.trackedDate > $1.trackedDate }

        for entry in sortedEntries {
            if entry.alcoholFree {
                alcoholStreak += 1
            } else {
                break
            }
        }

        // Calculate exercise streak
        var exerciseStreak = 0
        for entry in sortedEntries {
            if entry.exercised {
                exerciseStreak += 1
            } else {
                break
            }
        }

        // Calculate totals
        let alcoholFreeTotalDays = healthEntries.filter { $0.alcoholFree }.count
        let exerciseTotalDays = healthEntries.filter { $0.exercised }.count
        let exerciseTotalMinutes = healthEntries.reduce(0) { $0 + $1.exerciseDurationMinutes }

        // Get longest streaks from current stats
        let longestAlcoholStreak = max(healthStats.alcoholFreeLongestStreak, alcoholStreak)
        let longestExerciseStreak = max(healthStats.exerciseLongestStreak, exerciseStreak)

        // Calculate this week/month
        let calendar = Calendar.current
        let now = Date()
        let startOfWeek = calendar.date(from: calendar.dateComponents([.yearForWeekOfYear, .weekOfYear], from: now))!
        let startOfMonth = calendar.date(from: calendar.dateComponents([.year, .month], from: now))!

        let alcoholFreeDaysThisWeek = healthEntries.filter {
            $0.alcoholFree && $0.trackedDate >= startOfWeek
        }.count

        let alcoholFreeDaysThisMonth = healthEntries.filter {
            $0.alcoholFree && $0.trackedDate >= startOfMonth
        }.count

        let exerciseDaysThisWeek = healthEntries.filter {
            $0.exercised && $0.trackedDate >= startOfWeek
        }.count

        let exerciseDaysThisMonth = healthEntries.filter {
            $0.exercised && $0.trackedDate >= startOfMonth
        }.count

        let exerciseMinutesThisWeek = healthEntries.filter {
            $0.trackedDate >= startOfWeek
        }.reduce(0) { $0 + $1.exerciseDurationMinutes }

        let exerciseMinutesThisMonth = healthEntries.filter {
            $0.trackedDate >= startOfMonth
        }.reduce(0) { $0 + $1.exerciseDurationMinutes }

        // Update stats in database
        let updateQuery = """
        UPDATE health_stats SET
            alcohol_free_current_streak = ?,
            alcohol_free_longest_streak = ?,
            alcohol_free_total_days = ?,
            exercise_current_streak = ?,
            exercise_longest_streak = ?,
            exercise_total_days = ?,
            exercise_total_minutes = ?,
            alcohol_free_days_this_week = ?,
            alcohol_free_days_this_month = ?,
            exercise_days_this_week = ?,
            exercise_days_this_month = ?,
            exercise_minutes_this_week = ?,
            exercise_minutes_this_month = ?,
            updated_at = ?
        WHERE id = 1
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, updateQuery, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_int(statement, 1, Int32(alcoholStreak))
            sqlite3_bind_int(statement, 2, Int32(longestAlcoholStreak))
            sqlite3_bind_int(statement, 3, Int32(alcoholFreeTotalDays))
            sqlite3_bind_int(statement, 4, Int32(exerciseStreak))
            sqlite3_bind_int(statement, 5, Int32(longestExerciseStreak))
            sqlite3_bind_int(statement, 6, Int32(exerciseTotalDays))
            sqlite3_bind_int(statement, 7, Int32(exerciseTotalMinutes))
            sqlite3_bind_int(statement, 8, Int32(alcoholFreeDaysThisWeek))
            sqlite3_bind_int(statement, 9, Int32(alcoholFreeDaysThisMonth))
            sqlite3_bind_int(statement, 10, Int32(exerciseDaysThisWeek))
            sqlite3_bind_int(statement, 11, Int32(exerciseDaysThisMonth))
            sqlite3_bind_int(statement, 12, Int32(exerciseMinutesThisWeek))
            sqlite3_bind_int(statement, 13, Int32(exerciseMinutesThisMonth))

            let updatedAt = ISO8601DateFormatter().string(from: Date())
            sqlite3_bind_text(statement, 14, (updatedAt as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("📊 Health stats updated")
                loadHealthStats()  // Reload
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Mark Health Entry as Synced

    func markHealthEntryAsSynced(_ entryId: UUID) {
        let query = "UPDATE health_tracking SET synced = 1 WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (entryId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Health entry \(entryId) marked as synced")
                loadHealthEntries()
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Get Unsynced Health Entries

    func getUnsyncedHealthEntries() -> [HealthEntry] {
        return healthEntries.filter { !$0.synced }
    }

    // MARK: - Cleanup

    deinit {
        if db != nil {
            sqlite3_close(db)
        }
    }
}
