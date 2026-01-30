//
//  MeetingModels.swift
//  Angela Brain Dashboard
//
//  MeetingNote, MeetingActionItem, MeetingStats,
//  ProjectMeetingBreakdown, MeetingCreateRequest,
//  MeetingCreateResponse, MeetingUpdateRequest
//

import Foundation

// MARK: - Meeting Notes Models

/// Meeting note synced from Things3
struct MeetingNote: Identifiable, Codable {
    let id: UUID
    let things3Uuid: String
    let title: String
    let meetingType: String           // "meeting" or "site_visit"
    let location: String?
    let meetingDate: Date?
    let timeRange: String?
    let attendees: [String]?
    let agenda: [String]?
    let keyPoints: [String]?
    let decisionsMade: [String]?
    let issuesRisks: [String]?
    let nextSteps: [String]?
    let personalNotes: String?
    let rawNotes: String?
    let projectName: String?
    let things3Status: String         // "open" or "completed"
    let morningNotes: String?
    let afternoonNotes: String?
    let siteObservations: String?
    let syncedAt: Date
    let createdAt: Date
    let updatedAt: Date
    let totalActions: Int?
    let completedActions: Int?

    enum CodingKeys: String, CodingKey {
        case id = "meeting_id"
        case things3Uuid = "things3_uuid"
        case title
        case meetingType = "meeting_type"
        case location
        case meetingDate = "meeting_date"
        case timeRange = "time_range"
        case attendees
        case agenda
        case keyPoints = "key_points"
        case decisionsMade = "decisions_made"
        case issuesRisks = "issues_risks"
        case nextSteps = "next_steps"
        case personalNotes = "personal_notes"
        case rawNotes = "raw_notes"
        case projectName = "project_name"
        case things3Status = "things3_status"
        case morningNotes = "morning_notes"
        case afternoonNotes = "afternoon_notes"
        case siteObservations = "site_observations"
        case syncedAt = "synced_at"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case totalActions = "total_actions"
        case completedActions = "completed_actions"
    }

    var isSiteVisit: Bool {
        meetingType == "site_visit"
    }

    var isOpen: Bool {
        things3Status == "open"
    }

    var typeIcon: String {
        isSiteVisit ? "building.2.fill" : "doc.text.fill"
    }

    var typeColor: String {
        isSiteVisit ? "10B981" : "3B82F6"    // Green for site visit, Blue for meeting
    }

    var actionCompletionRate: Double {
        guard let total = totalActions, total > 0,
              let completed = completedActions else { return 0 }
        return Double(completed) / Double(total) * 100
    }

    var attendeeCount: Int {
        attendees?.count ?? 0
    }

    var dateFormatted: String {
        guard let date = meetingDate else { return "No date" }
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM yyyy"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: date)
    }

    var hasKeyPoints: Bool {
        !(keyPoints?.isEmpty ?? true)
    }

    var hasDecisions: Bool {
        !(decisionsMade?.isEmpty ?? true)
    }
}

/// Action item from a meeting
struct MeetingActionItem: Identifiable, Codable {
    let id: UUID
    let meetingId: UUID
    let actionText: String
    let assignee: String?
    let dueDate: Date?
    let isCompleted: Bool
    let completedAt: Date?
    let priority: Int
    let createdAt: Date
    let meetingTitle: String?
    let meetingDate: Date?
    let projectName: String?

    enum CodingKeys: String, CodingKey {
        case id = "action_id"
        case meetingId = "meeting_id"
        case actionText = "action_text"
        case assignee
        case dueDate = "due_date"
        case isCompleted = "is_completed"
        case completedAt = "completed_at"
        case priority
        case createdAt = "created_at"
        case meetingTitle = "meeting_title"
        case meetingDate = "meeting_date"
        case projectName = "project_name"
    }

    var statusIcon: String {
        isCompleted ? "checkmark.circle.fill" : "circle"
    }

    var statusColor: String {
        isCompleted ? "10B981" : "F59E0B"    // Green if done, Orange if pending
    }

    var priorityLabel: String {
        switch priority {
        case 1...3: return "High"
        case 4...6: return "Medium"
        default: return "Low"
        }
    }

    var priorityColor: String {
        switch priority {
        case 1...3: return "EF4444"    // Red
        case 4...6: return "F59E0B"    // Orange
        default: return "6B7280"       // Gray
        }
    }
}

/// Meeting statistics summary
struct MeetingStats: Codable {
    let totalMeetings: Int
    let thisMonth: Int
    let upcoming: Int?
    let openActions: Int
    let totalActions: Int
    let completedActions: Int
    let completionRate: Double
    let siteVisits: Int

    enum CodingKeys: String, CodingKey {
        case totalMeetings = "total_meetings"
        case thisMonth = "this_month"
        case upcoming
        case openActions = "open_actions"
        case totalActions = "total_actions"
        case completedActions = "completed_actions"
        case completionRate = "completion_rate"
        case siteVisits = "site_visits"
    }
}

/// Project meeting breakdown for chart
struct ProjectMeetingBreakdown: Identifiable, Codable {
    var id: String { projectName }
    let projectName: String
    let meetingCount: Int
    let openCount: Int
    let completedCount: Int
    let siteVisitCount: Int

    enum CodingKeys: String, CodingKey {
        case projectName = "project_name"
        case meetingCount = "meeting_count"
        case openCount = "open_count"
        case completedCount = "completed_count"
        case siteVisitCount = "site_visit_count"
    }
}

// MARK: - Meeting Create

/// Request body for creating a new meeting
struct MeetingCreateRequest: Codable {
    let title: String
    let location: String
    let meetingDate: String           // YYYY-MM-DD
    let startTime: String             // HH:MM
    let endTime: String               // HH:MM
    let meetingType: String           // standard, site_visit, testing, bod
    let attendees: [String]?
    let projectName: String?

    enum CodingKeys: String, CodingKey {
        case title
        case location
        case meetingDate = "meeting_date"
        case startTime = "start_time"
        case endTime = "end_time"
        case meetingType = "meeting_type"
        case attendees
        case projectName = "project_name"
    }
}

/// Response from meeting creation
struct MeetingCreateResponse: Codable {
    let success: Bool
    let meetingId: String?
    let things3Title: String?
    let calendarCreated: Bool?
    let error: String?
    let deleted: Bool?

    enum CodingKeys: String, CodingKey {
        case success
        case meetingId = "meeting_id"
        case things3Title = "things3_title"
        case calendarCreated = "calendar_created"
        case error
        case deleted
    }
}

/// Request body for updating a meeting
struct MeetingUpdateRequest: Codable {
    var title: String?
    var location: String?
    var meetingDate: String?          // YYYY-MM-DD
    var startTime: String?            // HH:MM
    var endTime: String?              // HH:MM
    var meetingType: String?          // standard, site_visit, testing, bod
    var attendees: [String]?
    var projectName: String?
    var things3Status: String?        // open, completed
    var notes: String?                // raw meeting notes

    enum CodingKeys: String, CodingKey {
        case title
        case location
        case meetingDate = "meeting_date"
        case startTime = "start_time"
        case endTime = "end_time"
        case meetingType = "meeting_type"
        case attendees
        case projectName = "project_name"
        case things3Status = "things3_status"
        case notes
    }
}
