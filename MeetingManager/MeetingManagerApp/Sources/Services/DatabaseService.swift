//
//  DatabaseService.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//  PostgreSQL Database Connection Service
//

import Foundation
import PostgresClientKit

@MainActor
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

                let meetingDateStr = try columns[2].string()
                let startTimeStr = try columns[3].string()

                guard let meetingDate = dateFormatter.date(from: meetingDateStr),
                      let startTime = timeFormatter.date(from: startTimeStr) else {
                    continue
                }

                let endTime: Date? = {
                    if let endTimeStr = try? columns[4].string() {
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
                    durationMinutes: columns[5].getInt(),
                    timezone: (try? columns[6].string()) ?? "Asia/Bangkok",
                    location: columns[7].getString(),
                    isVirtual: (try? columns[8].bool()) ?? false,
                    meetingLink: columns[9].getString(),
                    meetingType: columns[10].getString(),
                    status: Meeting.MeetingStatus(rawValue: (try? columns[11].string()) ?? "scheduled") ?? .scheduled,
                    organizerId: columns[12].getUUID(),
                    organizerName: columns[22].getString(),
                    agenda: columns[13].getString(),
                    objectives: columns[14].getString(),
                    isRecurring: (try? columns[15].bool()) ?? false,
                    recurrencePattern: columns[16].getString(),
                    parentMeetingId: columns[17].getUUID(),
                    createdAt: timestampFormatter.date(from: try columns[18].string()) ?? Date(),
                    updatedAt: timestampFormatter.date(from: try columns[19].string()) ?? Date(),
                    completedAt: columns[20].getTimestamp(),
                    cancelledAt: columns[21].getTimestamp()
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
        // TODO: Implement meeting creation
        return meeting
    }

    func updateMeeting(_ meeting: Meeting) async throws {
        // TODO: Implement meeting update
    }

    func deleteMeeting(id: UUID) async throws {
        // TODO: Implement soft delete
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
