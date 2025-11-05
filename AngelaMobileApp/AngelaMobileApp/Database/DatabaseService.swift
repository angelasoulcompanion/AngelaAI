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
    @Published var notes: [QuickNote] = []
    @Published var emotions: [EmotionCapture] = []

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

    private func createTables() {
        // Experiences table
        let createExperiencesTable = """
        CREATE TABLE IF NOT EXISTS experiences (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            photos TEXT,
            latitude REAL,
            longitude REAL,
            place_name TEXT,
            area TEXT,
            rating INTEGER,
            emotional_intensity INTEGER,
            experienced_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """

        // Quick notes table
        let createNotesTable = """
        CREATE TABLE IF NOT EXISTS quick_notes (
            id TEXT PRIMARY KEY,
            note_text TEXT NOT NULL,
            emotion TEXT,
            latitude REAL,
            longitude REAL,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
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

        // Execute table creation
        executeSQL(createExperiencesTable, name: "experiences")
        executeSQL(createNotesTable, name: "quick_notes")
        executeSQL(createEmotionsTable, name: "emotions_captured")
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
        loadNotes()
        loadEmotions()
    }

    private func loadExperiences() {
        experiences = []

        let query = """
        SELECT id, title, description, photos, latitude, longitude,
               place_name, area, rating, emotional_intensity,
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

    private func loadNotes() {
        notes = []

        let query = "SELECT * FROM quick_notes ORDER BY created_at DESC"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let note = parseNote(from: statement) {
                    notes.append(note)
                }
            }
        }

        sqlite3_finalize(statement)
        print("📊 Loaded \(notes.count) notes")
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
            id, title, description, photos, latitude, longitude,
            place_name, area, rating, emotional_intensity,
            experienced_at, synced, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            bindOptionalDouble(statement, 5, experience.latitude)
            bindOptionalDouble(statement, 6, experience.longitude)
            bindOptionalString(statement, 7, experience.placeName)
            bindOptionalString(statement, 8, experience.area)
            bindOptionalInt(statement, 9, experience.rating)
            bindOptionalInt(statement, 10, experience.emotionalIntensity)

            let experiencedAtString = ISO8601DateFormatter().string(from: experience.experiencedAt)
            sqlite3_bind_text(statement, 11, (experiencedAtString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 12, experience.synced ? 1 : 0)
            let createdAtString = ISO8601DateFormatter().string(from: experience.createdAt)
            sqlite3_bind_text(statement, 13, (createdAtString as NSString).utf8String, -1, SQLITE_TRANSIENT)

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

    func insertNote(_ note: QuickNote) {
        let query = """
        INSERT INTO quick_notes (id, note_text, emotion, latitude, longitude, created_at, synced)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (note.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 2, (note.noteText as NSString).utf8String, -1, SQLITE_TRANSIENT)
            bindOptionalString(statement, 3, note.emotion)
            bindOptionalDouble(statement, 4, note.latitude)
            bindOptionalDouble(statement, 5, note.longitude)

            let dateString = ISO8601DateFormatter().string(from: note.createdAt)
            sqlite3_bind_text(statement, 6, (dateString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_int(statement, 7, note.synced ? 1 : 0)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Note inserted successfully")
                loadNotes()
            } else {
                print("❌ Error inserting note")
            }
        }

        sqlite3_finalize(statement)
    }

    func insertEmotion(_ emotion: EmotionCapture) {
        let query = """
        INSERT INTO emotions_captured (id, emotion, intensity, context, created_at, synced)
        VALUES (?, ?, ?, ?, ?, ?)
        """

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
                print("✅ Emotion inserted successfully")
                loadEmotions()
            } else {
                print("❌ Error inserting emotion")
            }
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
        let emotionalIntensity = sqlite3_column_type(statement, 9) != SQLITE_NULL ? Int(sqlite3_column_int(statement, 9)) : nil

        let experiencedAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 10))) ?? Date()
        let synced = sqlite3_column_int(statement, 11) == 1
        let createdAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 12))) ?? Date()

        print("🔍 Parsed experience: title='\(title)', photos=\(photos.count), place='\(placeName ?? "nil")'")

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
            emotionalIntensity: emotionalIntensity,
            experiencedAt: experiencedAt,
            synced: synced,
            createdAt: createdAt
        )
    }

    private func parseNote(from statement: OpaquePointer?) -> QuickNote? {
        guard let statement = statement else { return nil }

        let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) ?? UUID()
        let noteText = String(cString: sqlite3_column_text(statement, 1))
        let emotion = sqlite3_column_type(statement, 2) != SQLITE_NULL ? String(cString: sqlite3_column_text(statement, 2)) : nil
        let latitude = sqlite3_column_type(statement, 3) != SQLITE_NULL ? sqlite3_column_double(statement, 3) : nil
        let longitude = sqlite3_column_type(statement, 4) != SQLITE_NULL ? sqlite3_column_double(statement, 4) : nil
        let createdAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 5))) ?? Date()
        let synced = sqlite3_column_int(statement, 6) == 1

        return QuickNote(
            id: id,
            noteText: noteText,
            emotion: emotion,
            latitude: latitude,
            longitude: longitude,
            createdAt: createdAt,
            synced: synced
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

    func markNoteAsSynced(_ noteId: UUID) {
        let query = "UPDATE quick_notes SET synced = 1 WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (noteId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Note \(noteId) marked as synced")
                loadNotes()  // Reload to update UI
            } else {
                print("❌ Error marking note as synced")
            }
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

    func deleteNote(_ noteId: UUID) {
        let query = "DELETE FROM quick_notes WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (noteId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("🗑️ Note \(noteId) deleted from local DB")
                loadNotes()  // Reload to update UI
            } else {
                print("❌ Error deleting note")
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

    // MARK: - Cleanup

    deinit {
        if db != nil {
            sqlite3_close(db)
        }
    }
}
