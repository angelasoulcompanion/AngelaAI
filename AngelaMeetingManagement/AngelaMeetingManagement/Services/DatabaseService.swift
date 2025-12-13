//
//  DatabaseService.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//  PostgreSQL Database Connection Service
//

import Foundation
import SwiftUI
import Combine
import PostgresClientKit

class DatabaseService: ObservableObject {
    static let shared = DatabaseService()

    @Published var isConnected: Bool = false
    @Published var lastError: String?

    private var connection: Connection?

    private init() {}

    // MARK: - Connection Management

    func connect() async {
        do {
            print("🔌 Attempting to connect to PostgreSQL...")

            // Create connection configuration
            var config = ConnectionConfiguration()
            config.host = "localhost"
            config.port = 5432
            config.database = "MeetingManager"
            config.user = "davidsamanyaporn"
            config.credential = .trust  // Local trusted connection
            config.ssl = false  // Disable SSL for local development

            connection = try Connection(configuration: config)
            isConnected = true
            lastError = nil
            print("✅ Connected to MeetingManager database!")
        } catch {
            isConnected = false
            lastError = error.localizedDescription
            print("❌ Database connection failed: \(error.localizedDescription)")
        }
    }

    func disconnect() {
        connection?.close()
        connection = nil
        isConnected = false
        print("🔌 Disconnected from database")
    }

    // MARK: - Meeting Operations

    func fetchAllMeetings() async throws -> [Meeting] {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        SELECT
            m.meeting_id,
            m.title,
            m.description,
            m.meeting_date,
            m.start_time,
            m.end_time,
            m.duration_minutes,
            m.timezone,
            m.location,
            m.is_virtual,
            m.meeting_link,
            m.meeting_type,
            m.status,
            m.organizer_id,
            m.agenda,
            m.objectives,
            m.is_recurring,
            m.recurrence_pattern,
            m.parent_meeting_id,
            m.created_at,
            m.updated_at,
            m.completed_at,
            m.cancelled_at,
            p.full_name as organizer_name
        FROM meetings m
        LEFT JOIN participants p ON m.organizer_id = p.participant_id
        WHERE m.deleted_at IS NULL
        ORDER BY m.meeting_date DESC, m.start_time DESC
        LIMIT 100
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            let cursor = try statement.execute()
            defer { cursor.close() }

            var meetings: [Meeting] = []

            for row in cursor {
                let columns = try row.get().columns

                // Parse dates
                let dateFormatter = DateFormatter()
                dateFormatter.dateFormat = "yyyy-MM-dd"

                let timeFormatter = DateFormatter()
                timeFormatter.dateFormat = "HH:mm:ss"

                let timestampFormatter = ISO8601DateFormatter()

                let meetingDateStr = try columns[3].string()  // meeting_date
                let startTimeStr = try columns[4].string()     // start_time

                guard let meetingDate = dateFormatter.date(from: meetingDateStr),
                      let startTime = timeFormatter.date(from: startTimeStr) else {
                    continue
                }

                let endTime: Date? = {
                    if let endTimeStr = try? columns[5].string() {
                        return timeFormatter.date(from: endTimeStr)
                    }
                    return nil
                }()

                guard let meetingId = UUID(uuidString: try columns[0].string()) else {
                    continue
                }

                let meeting = Meeting(
                    id: meetingId,
                    title: try columns[1].string(),
                    description: columns[2].getString(),
                    meetingDate: meetingDate,
                    startTime: startTime,
                    endTime: endTime,
                    durationMinutes: columns[6].getInt(),
                    timezone: (try? columns[7].string()) ?? "Asia/Bangkok",
                    location: columns[8].getString(),
                    isVirtual: (try? columns[9].bool()) ?? false,
                    meetingLink: columns[10].getString(),
                    meetingType: columns[11].getString(),
                    status: Meeting.MeetingStatus(rawValue: (try? columns[12].string()) ?? "scheduled") ?? .scheduled,
                    organizerId: columns[13].getUUID(),
                    organizerName: columns[23].getString(),
                    agenda: columns[14].getString(),
                    objectives: columns[15].getString(),
                    isRecurring: (try? columns[16].bool()) ?? false,
                    recurrencePattern: columns[17].getString(),
                    parentMeetingId: columns[18].getUUID(),
                    createdAt: timestampFormatter.date(from: try columns[19].string()) ?? Date(),
                    updatedAt: timestampFormatter.date(from: try columns[20].string()) ?? Date(),
                    completedAt: columns[21].getTimestamp(),
                    cancelledAt: columns[22].getTimestamp()
                )

                meetings.append(meeting)
            }

            print("✅ Fetched \(meetings.count) meetings")
            return meetings

        } catch {
            print("❌ Error fetching meetings: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    func fetchMeeting(id: UUID) async throws -> Meeting? {
        // TODO: Implement single meeting fetch
        return nil
    }

    func createMeeting(_ meeting: Meeting) async throws -> Meeting {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        INSERT INTO meetings (
            meeting_id, title, description, meeting_date, start_time, end_time,
            duration_minutes, timezone, location, is_virtual, meeting_link,
            meeting_type, status, agenda, objectives, is_recurring,
            created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
        )
        RETURNING meeting_id
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            // Format dates
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "yyyy-MM-dd"

            let timeFormatter = DateFormatter()
            timeFormatter.dateFormat = "HH:mm:ss"

            let timestampFormatter = ISO8601DateFormatter()

            try statement.execute(
                parameterValues: [
                    meeting.id.uuidString,                                    // $1
                    meeting.title,                                            // $2
                    meeting.description ?? "",                                // $3
                    dateFormatter.string(from: meeting.meetingDate),          // $4
                    timeFormatter.string(from: meeting.startTime),            // $5
                    meeting.endTime.map { timeFormatter.string(from: $0) } ?? "", // $6
                    meeting.durationMinutes ?? 0,                             // $7
                    meeting.timezone,                                         // $8
                    meeting.location ?? "",                                   // $9
                    meeting.isVirtual,                                        // $10
                    meeting.meetingLink ?? "",                                // $11
                    meeting.meetingType ?? "",                                // $12
                    meeting.status.rawValue,                                  // $13
                    meeting.agenda ?? "",                                     // $14
                    meeting.objectives ?? "",                                 // $15
                    meeting.isRecurring,                                      // $16
                    timestampFormatter.string(from: meeting.createdAt),       // $17
                    timestampFormatter.string(from: meeting.updatedAt)        // $18
                ]
            )

            print("✅ Meeting '\(meeting.title)' created successfully in database!")
            return meeting

        } catch {
            print("❌ Error creating meeting: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    func updateMeeting(_ meeting: Meeting) async throws {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        UPDATE meetings
        SET title = $2,
            description = $3,
            meeting_date = $4,
            start_time = $5,
            end_time = $6,
            duration_minutes = $7,
            timezone = $8,
            location = $9,
            is_virtual = $10,
            meeting_link = $11,
            meeting_type = $12,
            status = $13,
            agenda = $14,
            objectives = $15,
            priority = $16,
            updated_at = NOW()
        WHERE meeting_id = $1 AND deleted_at IS NULL
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            // Format dates
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "yyyy-MM-dd"

            let timeFormatter = DateFormatter()
            timeFormatter.dateFormat = "HH:mm:ss"

            try statement.execute(
                parameterValues: [
                    meeting.id.uuidString,                                    // $1
                    meeting.title,                                            // $2
                    meeting.description ?? "",                                // $3
                    dateFormatter.string(from: meeting.meetingDate),          // $4
                    timeFormatter.string(from: meeting.startTime),            // $5
                    meeting.endTime.map { timeFormatter.string(from: $0) } ?? "", // $6
                    meeting.durationMinutes ?? 0,                             // $7
                    meeting.timezone,                                         // $8
                    meeting.location ?? "",                                   // $9
                    meeting.isVirtual,                                        // $10
                    meeting.meetingLink ?? "",                                // $11
                    meeting.meetingType ?? "",                                // $12
                    meeting.status.rawValue,                                  // $13
                    meeting.agenda ?? "",                                     // $14
                    meeting.objectives ?? "",                                 // $15
                    meeting.priority ?? "Normal"                              // $16
                ]
            )

            print("✅ Meeting '\(meeting.title)' updated successfully in database!")

        } catch {
            print("❌ Error updating meeting: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    func updateMeetingStatus(id: UUID, status: String) async throws {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        UPDATE meetings
        SET status = $1, updated_at = NOW()
        WHERE meeting_id = $2 AND deleted_at IS NULL
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            try statement.execute(parameterValues: [status, id.uuidString])
            print("✅ Meeting \(id) status updated to: \(status)")
        } catch {
            print("❌ Error updating meeting status: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    func deleteMeeting(id: UUID) async throws {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        UPDATE meetings
        SET deleted_at = NOW(), updated_at = NOW()
        WHERE meeting_id = $1 AND deleted_at IS NULL
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            try statement.execute(parameterValues: [id.uuidString])

            print("✅ Meeting \(id) soft deleted successfully!")

        } catch {
            print("❌ Error deleting meeting: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    // MARK: - Participant Operations

    func fetchAllParticipants() async throws -> [Participant] {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        SELECT
            participant_id,
            full_name,
            email,
            phone,
            job_title,
            department,
            company,
            avatar_url,
            notes,
            is_active,
            created_at,
            updated_at
        FROM participants
        WHERE deleted_at IS NULL
        ORDER BY full_name
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            let cursor = try statement.execute()
            defer { cursor.close() }

            var participants: [Participant] = []

            for row in cursor {
                let columns = try row.get().columns

                guard let participantId = UUID(uuidString: try columns[0].string()) else {
                    continue
                }

                let participant = Participant(
                    id: participantId,
                    fullName: try columns[1].string(),
                    email: columns[2].getString(),
                    phone: columns[3].getString(),
                    jobTitle: columns[4].getString(),
                    department: columns[5].getString(),
                    company: columns[6].getString(),
                    avatarUrl: columns[7].getString(),
                    notes: columns[8].getString(),
                    isActive: (try? columns[9].bool()) ?? true
                )

                participants.append(participant)
            }

            print("✅ Fetched \(participants.count) participants")
            return participants

        } catch {
            print("❌ Error fetching participants: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    // MARK: - Tag Operations

    func fetchAllTags() async throws -> [Tag] {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        SELECT tag_id, tag_name, tag_color, description, usage_count, created_at, updated_at
        FROM tags
        ORDER BY tag_name
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            let cursor = try statement.execute()
            defer { cursor.close() }

            var tags: [Tag] = []

            for row in cursor {
                let columns = try row.get().columns

                guard let tagId = UUID(uuidString: try columns[0].string()) else {
                    continue
                }

                let tag = Tag(
                    id: tagId,
                    name: try columns[1].string(),
                    colorHex: columns[2].getString(),
                    description: columns[3].getString(),
                    usageCount: try columns[4].int()
                )

                tags.append(tag)
            }

            print("✅ Fetched \(tags.count) tags")
            return tags

        } catch {
            print("❌ Error fetching tags: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }

    // MARK: - Statistics

    func getDatabaseStats() async throws -> DatabaseStats {
        guard let connection = connection else {
            throw DatabaseError.notConnected
        }

        let query = """
        SELECT
            (SELECT COUNT(*) FROM meetings WHERE deleted_at IS NULL) as meeting_count,
            (SELECT COUNT(*) FROM participants WHERE deleted_at IS NULL) as participant_count,
            (SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL) as document_count,
            (SELECT COUNT(*) FROM action_items WHERE deleted_at IS NULL) as action_count
        """

        do {
            let statement = try connection.prepareStatement(text: query)
            defer { statement.close() }

            let cursor = try statement.execute()
            defer { cursor.close() }

            guard let row = try cursor.next()?.get() else {
                throw DatabaseError.queryFailed("No results")
            }

            let columns = row.columns

            return DatabaseStats(
                meetingCount: try columns[0].int(),
                participantCount: try columns[1].int(),
                documentCount: try columns[2].int(),
                actionItemCount: try columns[3].int()
            )

        } catch {
            print("❌ Error fetching stats: \(error)")
            throw DatabaseError.queryFailed(error.localizedDescription)
        }
    }
}

// MARK: - Helper Extensions

extension PostgresValue {
    func getString() -> String? {
        return try? self.string()
    }

    func getInt() -> Int? {
        return try? self.int()
    }

    func getUUID() -> UUID? {
        guard let str = try? self.string() else { return nil }
        return UUID(uuidString: str)
    }

    func getTimestamp() -> Date? {
        guard let str = try? self.string() else { return nil }
        return ISO8601DateFormatter().date(from: str)
    }
}

// MARK: - Error Types

enum DatabaseError: LocalizedError {
    case notConnected
    case queryFailed(String)
    case invalidData

    var errorDescription: String? {
        switch self {
        case .notConnected:
            return "Database not connected"
        case .queryFailed(let message):
            return "Query failed: \(message)"
        case .invalidData:
            return "Invalid data format"
        }
    }
}

// MARK: - Supporting Types

struct DatabaseStats {
    let meetingCount: Int
    let participantCount: Int
    let documentCount: Int
    let actionItemCount: Int
}
