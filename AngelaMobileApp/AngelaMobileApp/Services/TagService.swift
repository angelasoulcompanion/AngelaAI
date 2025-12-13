//
//  TagService.swift
//  Angela Mobile App
//
//  Tag management service for organizing experiences
//  Feature 4: Tags System
//

import Foundation
import SQLite3
import Combine

class TagService: ObservableObject {
    static let shared = TagService()

    @Published var availableTags: [Tag] = []

    private var db: OpaquePointer?
    private let SQLITE_TRANSIENT = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    private init() {
        // Use same database as DatabaseService
        let paths = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)
        let dbPath = paths[0].appendingPathComponent("angela_mobile.db").path

        if sqlite3_open(dbPath, &db) == SQLITE_OK {
            print("✅ TagService connected to database")
            loadTags()
        } else {
            print("❌ TagService failed to connect to database")
        }
    }

    // MARK: - Load Tags

    func loadTags() {
        availableTags = []

        let query = "SELECT id, name, color, created_at FROM tags ORDER BY name"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            while sqlite3_step(statement) == SQLITE_ROW {
                if let tag = parseTag(from: statement) {
                    availableTags.append(tag)
                }
            }
        }

        sqlite3_finalize(statement)
        print("📊 Loaded \(availableTags.count) tags")
    }

    private func parseTag(from statement: OpaquePointer?) -> Tag? {
        guard let statement = statement else { return nil }

        let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) ?? UUID()
        let name = String(cString: sqlite3_column_text(statement, 1))
        let color = sqlite3_column_type(statement, 2) != SQLITE_NULL
            ? String(cString: sqlite3_column_text(statement, 2))
            : "#9B7EBD"  // Default Angela purple
        let createdAt = ISO8601DateFormatter().date(from: String(cString: sqlite3_column_text(statement, 3))) ?? Date()

        return Tag(id: id, name: name, color: color, createdAt: createdAt)
    }

    // MARK: - Create Tag

    func createTag(name: String, color: String = "#9B7EBD") -> Tag? {
        // Check if tag already exists
        if availableTags.contains(where: { $0.name.lowercased() == name.lowercased() }) {
            print("⚠️ Tag '\(name)' already exists")
            return availableTags.first(where: { $0.name.lowercased() == name.lowercased() })
        }

        let tag = Tag(id: UUID(), name: name, color: color, createdAt: Date())

        let query = """
        INSERT INTO tags (id, name, color, created_at)
        VALUES (?, ?, ?, ?)
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (tag.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 2, (tag.name as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_bind_text(statement, 3, (tag.color as NSString).utf8String, -1, SQLITE_TRANSIENT)

            let dateString = ISO8601DateFormatter().string(from: tag.createdAt)
            sqlite3_bind_text(statement, 4, (dateString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("✅ Tag '\(name)' created")
                loadTags()
                return tag
            } else {
                print("❌ Failed to create tag")
            }
        }

        sqlite3_finalize(statement)
        return nil
    }

    // MARK: - Delete Tag

    func deleteTag(_ tagId: UUID) {
        let query = "DELETE FROM tags WHERE id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (tagId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            if sqlite3_step(statement) == SQLITE_DONE {
                print("🗑️ Tag deleted")
                loadTags()
            } else {
                print("❌ Failed to delete tag")
            }
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Link Tags to Experience

    func linkTagsToExperience(experienceId: UUID, tags: [Tag]) {
        // First, remove existing links
        removeAllTagsFromExperience(experienceId)

        // Then add new links
        for tag in tags {
            let query = """
            INSERT INTO experience_tags (experience_id, tag_id)
            VALUES (?, ?)
            """

            var statement: OpaquePointer?

            if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
                sqlite3_bind_text(statement, 1, (experienceId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
                sqlite3_bind_text(statement, 2, (tag.id.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

                if sqlite3_step(statement) == SQLITE_DONE {
                    print("✅ Tag '\(tag.name)' linked to experience")
                } else {
                    print("❌ Failed to link tag to experience")
                }
            }

            sqlite3_finalize(statement)
        }
    }

    private func removeAllTagsFromExperience(_ experienceId: UUID) {
        let query = "DELETE FROM experience_tags WHERE experience_id = ?"
        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (experienceId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)
            sqlite3_step(statement)
        }

        sqlite3_finalize(statement)
    }

    // MARK: - Get Tags for Experience

    func getTagsForExperience(_ experienceId: UUID) -> [Tag] {
        var tags: [Tag] = []

        let query = """
        SELECT t.id, t.name, t.color, t.created_at
        FROM tags t
        INNER JOIN experience_tags et ON t.id = et.tag_id
        WHERE et.experience_id = ?
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (experienceId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            while sqlite3_step(statement) == SQLITE_ROW {
                if let tag = parseTag(from: statement) {
                    tags.append(tag)
                }
            }
        }

        sqlite3_finalize(statement)
        return tags
    }

    // MARK: - Get Experiences for Tag

    func getExperiencesForTag(_ tagId: UUID) -> [UUID] {
        var experienceIds: [UUID] = []

        let query = """
        SELECT experience_id FROM experience_tags
        WHERE tag_id = ?
        """

        var statement: OpaquePointer?

        if sqlite3_prepare_v2(db, query, -1, &statement, nil) == SQLITE_OK {
            sqlite3_bind_text(statement, 1, (tagId.uuidString as NSString).utf8String, -1, SQLITE_TRANSIENT)

            while sqlite3_step(statement) == SQLITE_ROW {
                if let id = UUID(uuidString: String(cString: sqlite3_column_text(statement, 0))) {
                    experienceIds.append(id)
                }
            }
        }

        sqlite3_finalize(statement)
        return experienceIds
    }

    // MARK: - Predefined Tags

    func createPredefinedTags() {
        let predefined = [
            ("🍔 อาหาร", "#FF6B6B"),
            ("✈️ ท่องเที่ยว", "#4ECDC4"),
            ("💼 งาน", "#FFD93D"),
            ("❤️ ที่รัก", "#FF8C42"),
            ("👨‍👩‍👧‍👦 ครอบครัว", "#6BCB77"),
            ("🎉 งานเลี้ยง", "#C56CF0"),
            ("🏋️ ออกกำลังกาย", "#3498DB"),
            ("📚 เรียนรู้", "#E91E63"),
            ("🎨 ศิลปะ", "#9B7EBD")
        ]

        for (name, color) in predefined {
            _ = createTag(name: name, color: color)
        }
    }

    deinit {
        if db != nil {
            sqlite3_close(db)
        }
    }
}
