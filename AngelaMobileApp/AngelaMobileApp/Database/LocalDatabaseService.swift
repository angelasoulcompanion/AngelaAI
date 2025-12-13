//
//  LocalDatabaseService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-07.
//  Local SQLite database service for on-device data storage
//

import Foundation
import SQLite3

/// Local SQLite database service for Angela Mobile App
/// Handles Thai dictionary and other on-device data
class LocalDatabaseService {

    // MARK: - Singleton
    static let shared = LocalDatabaseService()

    // MARK: - Properties
    private var db: OpaquePointer?
    private let dbPath: String

    // MARK: - Initialization

    private init() {
        // Get database path in Documents directory
        let fileManager = FileManager.default
        let documentsURL = fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        dbPath = documentsURL.appendingPathComponent("angela.db").path

        print("💾 [LocalDatabase] Database path: \(dbPath)")

        // Open or create database
        openDatabase()

        // Initialize schema
        initializeSchema()
    }

    deinit {
        closeDatabase()
    }

    // MARK: - Database Management

    /// Open database connection
    private func openDatabase() {
        if sqlite3_open(dbPath, &db) == SQLITE_OK {
            print("✅ [LocalDatabase] Database opened successfully")
        } else {
            print("❌ [LocalDatabase] Failed to open database")
        }
    }

    /// Close database connection
    private func closeDatabase() {
        if sqlite3_close(db) == SQLITE_OK {
            print("✅ [LocalDatabase] Database closed successfully")
        } else {
            print("❌ [LocalDatabase] Failed to close database")
        }
    }

    /// Initialize database schema
    private func initializeSchema() {
        // Create tables
        createThaiWordsTable()
        createSpellingCorrectionsTable()
        createCorrectionHistoryTable()
        createMetadataTable()

        // Populate initial data if empty
        populateInitialData()
    }

    // MARK: - Schema Creation

    private func createThaiWordsTable() {
        let createTableSQL = """
        CREATE TABLE IF NOT EXISTS thai_words (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            word_type TEXT,
            category TEXT,
            frequency INTEGER DEFAULT 0,
            is_common INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        executeSQL(createTableSQL, name: "thai_words table")

        // Create index
        let createIndexSQL = "CREATE INDEX IF NOT EXISTS idx_thai_words_word ON thai_words(word);"
        executeSQL(createIndexSQL, name: "thai_words index")
    }

    private func createSpellingCorrectionsTable() {
        let createTableSQL = """
        CREATE TABLE IF NOT EXISTS spelling_corrections (
            correction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            incorrect_word TEXT NOT NULL,
            correct_word TEXT NOT NULL,
            correction_count INTEGER DEFAULT 0,
            confidence REAL DEFAULT 1.0,
            source TEXT DEFAULT 'manual',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used_at DATETIME,
            UNIQUE(incorrect_word, correct_word)
        );
        """

        executeSQL(createTableSQL, name: "spelling_corrections table")

        // Create index
        let createIndexSQL = "CREATE INDEX IF NOT EXISTS idx_spelling_corrections_incorrect ON spelling_corrections(incorrect_word);"
        executeSQL(createIndexSQL, name: "spelling_corrections index")
    }

    private func createCorrectionHistoryTable() {
        let createTableSQL = """
        CREATE TABLE IF NOT EXISTS correction_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            corrected_text TEXT NOT NULL,
            correction_type TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        executeSQL(createTableSQL, name: "correction_history table")
    }

    private func createMetadataTable() {
        let createTableSQL = """
        CREATE TABLE IF NOT EXISTS db_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        executeSQL(createTableSQL, name: "db_metadata table")
    }

    // MARK: - Helper Methods

    /// Execute SQL statement
    private func executeSQL(_ sql: String, name: String) {
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, sql, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ [LocalDatabase] Created \(name)")
            } else {
                print("❌ [LocalDatabase] Failed to execute \(name)")
            }
        } else {
            let error = String(cString: sqlite3_errmsg(db))
            print("❌ [LocalDatabase] Failed to prepare \(name): \(error)")
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Thai Words Methods

    /// Check if a word exists in dictionary
    func isValidWord(_ word: String) -> Bool {
        let query = "SELECT word FROM thai_words WHERE word = ? LIMIT 1;"
        var statement: OpaquePointer?
        var exists = false

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (word as NSString).utf8String, -1, nil)

            if sqlite3_step(statement) == SQLITE_ROW {
                exists = true
            }
        }

        sqlite3_finalize(statement)
        return exists
    }

    /// Add a word to dictionary
    func addWord(_ word: String, type: String? = nil, category: String? = nil, isCommon: Bool = false) -> Bool {
        let insert = """
        INSERT OR IGNORE INTO thai_words (word, word_type, category, is_common)
        VALUES (?, ?, ?, ?);
        """

        var statement: OpaquePointer?
        var success = false

        if sqlite3_prepare_v2(db, insert, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (word as NSString).utf8String, -1, nil)
            sqlite3_bind_text(statement, 2, (type as NSString?)?.utf8String, -1, nil)
            sqlite3_bind_text(statement, 3, (category as NSString?)?.utf8String, -1, nil)
            sqlite3_bind_int(statement, 4, isCommon ? 1 : 0)

            if sqlite3_step(statement) == SQLITE_DONE {
                success = true
            }
        }

        sqlite3_finalize(statement)
        return success
    }

    /// Get all common words
    func getCommonWords() -> Set<String> {
        let query = "SELECT word FROM thai_words WHERE is_common = 1;"
        var statement: OpaquePointer?
        var words = Set<String>()

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let wordCString = sqlite3_column_text(statement, 0) {
                    let word = String(cString: wordCString)
                    words.insert(word)
                }
            }
        }

        sqlite3_finalize(statement)
        return words
    }

    // MARK: - Spelling Corrections Methods

    /// Get correction for a word
    func getCorrection(for word: String) -> String? {
        let query = """
        SELECT correct_word FROM spelling_corrections
        WHERE incorrect_word = ?
        ORDER BY confidence DESC
        LIMIT 1;
        """

        var statement: OpaquePointer?
        var correction: String?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (word as NSString).utf8String, -1, nil)

            if sqlite3_step(statement) == SQLITE_ROW {
                if let correctionCString = sqlite3_column_text(statement, 0) {
                    correction = String(cString: correctionCString)
                }
            }
        }

        sqlite3_finalize(statement)
        return correction
    }

    /// Get all spelling corrections
    func getAllCorrections() -> [String: String] {
        let query = "SELECT incorrect_word, correct_word FROM spelling_corrections;"
        var statement: OpaquePointer?
        var corrections: [String: String] = [:]

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let incorrectCString = sqlite3_column_text(statement, 0),
                   let correctCString = sqlite3_column_text(statement, 1) {
                    let incorrect = String(cString: incorrectCString)
                    let correct = String(cString: correctCString)
                    corrections[incorrect] = correct
                }
            }
        }

        sqlite3_finalize(statement)
        return corrections
    }

    /// Add a spelling correction
    func addCorrection(incorrect: String, correct: String, confidence: Double = 1.0) -> Bool {
        let insert = """
        INSERT OR REPLACE INTO spelling_corrections (incorrect_word, correct_word, confidence, source)
        VALUES (?, ?, ?, 'manual');
        """

        var statement: OpaquePointer?
        var success = false

        if sqlite3_prepare_v2(db, insert, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (incorrect as NSString).utf8String, -1, nil)
            sqlite3_bind_text(statement, 2, (correct as NSString).utf8String, -1, nil)
            sqlite3_bind_double(statement, 3, confidence)

            if sqlite3_step(statement) == SQLITE_DONE {
                success = true
            }
        }

        sqlite3_finalize(statement)
        return success
    }

    /// Track correction usage
    func trackCorrectionUsage(incorrect: String, correct: String) {
        let update = """
        UPDATE spelling_corrections
        SET correction_count = correction_count + 1,
            last_used_at = CURRENT_TIMESTAMP
        WHERE incorrect_word = ? AND correct_word = ?;
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, update, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (incorrect as NSString).utf8String, -1, nil)
            sqlite3_bind_text(statement, 2, (correct as NSString).utf8String, -1, nil)
            sqlite3_step(statement)
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Populate Initial Data

    /// Populate initial dictionary data using InitialDataImporter
    private func populateInitialData() {
        // Check if data already exists
        let countQuery = "SELECT COUNT(*) FROM thai_words;"
        var statement: OpaquePointer?
        var count = 0

        if sqlite3_prepare_v2(db, countQuery, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_ROW {
                count = Int(sqlite3_column_int(statement, 0))
            }
        }
        sqlite3_finalize(statement)

        // Only populate if empty
        if count == 0 {
            print("📝 [LocalDatabase] Database is empty, importing initial data...")
            // TODO: Fix InitialDataImporter crash
            // InitialDataImporter.shared.importInitialData()
            print("⚠️ [LocalDatabase] Initial data import disabled temporarily")
        } else {
            print("ℹ️ [LocalDatabase] Dictionary already has \(count) words")
        }
    }

    // MARK: - Statistics

    func getStats() -> [String: Any] {
        var stats: [String: Any] = [:]

        // Count words
        var statement: OpaquePointer?
        let wordCountQuery = "SELECT COUNT(*) FROM thai_words;"
        if sqlite3_prepare_v2(db, wordCountQuery, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_ROW {
                stats["total_words"] = Int(sqlite3_column_int(statement, 0))
            }
        }
        sqlite3_finalize(statement)

        // Count corrections
        let correctionCountQuery = "SELECT COUNT(*) FROM spelling_corrections;"
        if sqlite3_prepare_v2(db, correctionCountQuery, -1, &statement, nil) == SQLITE_OK {
            if sqlite3_step(statement) == SQLITE_ROW {
                stats["total_corrections"] = Int(sqlite3_column_int(statement, 0))
            }
        }
        sqlite3_finalize(statement)

        return stats
    }

}
