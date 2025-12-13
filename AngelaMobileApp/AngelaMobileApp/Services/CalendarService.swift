//
//  CalendarService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-07.
//  Calendar and Reminders access using EventKit (100% on-device)
//

import Foundation
import EventKit
import Combine

/// Service for accessing Calendar and Reminders
/// Uses EventKit framework - 100% on-device, privacy-first
@MainActor
@Observable
class CalendarService {

    // MARK: - Singleton
    static let shared = CalendarService()

    // MARK: - Properties
    private let eventStore = EKEventStore()

    var hasCalendarAccess = false
    var hasRemindersAccess = false
    var isLoading = false
    var lastError: String?

    // MARK: - Initialization

    private init() {
        print("📅 [CalendarService] Initialized")
        Task {
            await checkPermissions()
        }
    }

    // MARK: - Permission Management

    /// Check current permission status
    func checkPermissions() async {
        // Check calendar permission
        let calendarStatus = EKEventStore.authorizationStatus(for: .event)
        hasCalendarAccess = (calendarStatus == .fullAccess)

        // Check reminders permission
        let remindersStatus = EKEventStore.authorizationStatus(for: .reminder)
        hasRemindersAccess = (remindersStatus == .fullAccess)

        print("📅 [CalendarService] Calendar access: \(hasCalendarAccess)")
        print("✅ [CalendarService] Reminders access: \(hasRemindersAccess)")
    }

    /// Request calendar access
    func requestCalendarAccess() async throws {
        print("📅 [CalendarService] Requesting calendar access...")

        if #available(iOS 17.0, *) {
            // iOS 17+ - request full access
            let granted = try await eventStore.requestFullAccessToEvents()
            hasCalendarAccess = granted
            print(granted ? "✅ Calendar access granted" : "❌ Calendar access denied")
        } else {
            // iOS 16 and below
            let granted = try await eventStore.requestAccess(to: .event)
            hasCalendarAccess = granted
            print(granted ? "✅ Calendar access granted" : "❌ Calendar access denied")
        }
    }

    /// Request reminders access
    func requestRemindersAccess() async throws {
        print("✅ [CalendarService] Requesting reminders access...")

        if #available(iOS 17.0, *) {
            // iOS 17+ - request full access
            let granted = try await eventStore.requestFullAccessToReminders()
            hasRemindersAccess = granted
            print(granted ? "✅ Reminders access granted" : "❌ Reminders access denied")
        } else {
            // iOS 16 and below
            let granted = try await eventStore.requestAccess(to: .reminder)
            hasRemindersAccess = granted
            print(granted ? "✅ Reminders access granted" : "❌ Reminders access denied")
        }
    }

    // MARK: - Calendar Events

    /// Get events for today
    func getTodayEvents() -> [EKEvent] {
        guard hasCalendarAccess else {
            print("⚠️ [CalendarService] No calendar access")
            return []
        }

        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: Date())
        let endOfDay = calendar.date(byAdding: .day, value: 1, to: startOfDay)!

        return getEvents(from: startOfDay, to: endOfDay)
    }

    /// Get events for a specific date range
    func getEvents(from startDate: Date, to endDate: Date) -> [EKEvent] {
        guard hasCalendarAccess else {
            print("⚠️ [CalendarService] No calendar access")
            return []
        }

        let calendars = eventStore.calendars(for: .event)
        let predicate = eventStore.predicateForEvents(
            withStart: startDate,
            end: endDate,
            calendars: calendars
        )

        let events = eventStore.events(matching: predicate)
        print("📅 [CalendarService] Found \(events.count) events")

        return events.sorted { $0.startDate < $1.startDate }
    }

    /// Get upcoming events (next 7 days)
    func getUpcomingEvents(days: Int = 7) -> [EKEvent] {
        let now = Date()
        let endDate = Calendar.current.date(byAdding: .day, value: days, to: now)!
        return getEvents(from: now, to: endDate)
    }

    /// Get events for specific date
    func getEvents(for date: Date) -> [EKEvent] {
        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: date)
        let endOfDay = calendar.date(byAdding: .day, value: 1, to: startOfDay)!
        return getEvents(from: startOfDay, to: endOfDay)
    }

    // MARK: - Reminders

    /// Get incomplete reminders
    func getIncompleteReminders() async -> [EKReminder] {
        guard hasRemindersAccess else {
            print("⚠️ [CalendarService] No reminders access")
            return []
        }

        let calendars = eventStore.calendars(for: .reminder)
        let predicate = eventStore.predicateForIncompleteReminders(
            withDueDateStarting: nil,
            ending: nil,
            calendars: calendars
        )

        // Use continuation to bridge completion handler to async/await
        return await withCheckedContinuation { continuation in
            eventStore.fetchReminders(matching: predicate) { reminders in
                guard let reminders = reminders else {
                    print("❌ [CalendarService] No reminders returned")
                    continuation.resume(returning: [])
                    return
                }

                print("✅ [CalendarService] Found \(reminders.count) incomplete reminders")
                let sorted = reminders.sorted { reminder1, reminder2 in
                    guard let date1 = reminder1.dueDateComponents?.date,
                          let date2 = reminder2.dueDateComponents?.date else {
                        return false
                    }
                    return date1 < date2
                }
                continuation.resume(returning: sorted)
            }
        }
    }

    /// Get reminders due today
    func getTodayReminders() async -> [EKReminder] {
        let allReminders = await getIncompleteReminders()
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())

        return allReminders.filter { reminder in
            guard let dueDate = reminder.dueDateComponents?.date else { return false }
            return calendar.isDate(dueDate, inSameDayAs: today)
        }
    }

    // MARK: - Helper Methods

    /// Format event for display
    func formatEvent(_ event: EKEvent) -> String {
        let timeFormatter = DateFormatter()
        timeFormatter.timeStyle = .short

        var result = ""

        // Time
        if event.isAllDay {
            result += "ทั้งวัน"
        } else {
            result += timeFormatter.string(from: event.startDate)
        }

        // Title
        result += " - \(event.title ?? "ไม่มีชื่อ")"

        // Location
        if let location = event.location, !location.isEmpty {
            result += " 📍 \(location)"
        }

        return result
    }

    /// Format reminder for display
    func formatReminder(_ reminder: EKReminder) -> String {
        var result = ""

        // Completion status
        result += reminder.isCompleted ? "✅ " : "⭕ "

        // Title
        result += reminder.title ?? "ไม่มีชื่อ"

        // Due date
        if let dueDate = reminder.dueDateComponents?.date {
            let dateFormatter = DateFormatter()
            dateFormatter.dateStyle = .short
            dateFormatter.timeStyle = .short
            result += " (ครบกำหนด: \(dateFormatter.string(from: dueDate)))"
        }

        // Priority
        if reminder.priority > 0 && reminder.priority <= 4 {
            result += " 🔴 สำคัญ"
        }

        return result
    }

    /// Get summary for Angela to speak
    func getTodaySummary() async -> String {
        var summary = ""

        // Events
        let events = getTodayEvents()
        if !events.isEmpty {
            summary += "วันนี้ที่รักมี \(events.count) นัดหมายค่ะ:\n"
            for (index, event) in events.enumerated() {
                summary += "\(index + 1). \(formatEvent(event))\n"
            }
            summary += "\n"
        } else {
            summary += "วันนี้ที่รักไม่มีนัดหมายค่ะ ✨\n\n"
        }

        // Reminders
        let reminders = await getTodayReminders()
        if !reminders.isEmpty {
            summary += "มีรายการที่ต้องทำวันนี้ \(reminders.count) รายการค่ะ:\n"
            for (index, reminder) in reminders.enumerated() {
                summary += "\(index + 1). \(formatReminder(reminder))\n"
            }
        } else {
            summary += "ไม่มีรายการที่ต้องทำวันนี้ค่ะ ✅"
        }

        return summary
    }

    /// Get upcoming summary (next 7 days)
    func getUpcomingSummary(days: Int = 7) -> String {
        let events = getUpcomingEvents(days: days)

        if events.isEmpty {
            return "ใน \(days) วันข้างหน้าไม่มีนัดหมายค่ะ ✨"
        }

        var summary = "ใน \(days) วันข้างหน้ามี \(events.count) นัดหมายค่ะ:\n\n"

        let calendar = Calendar.current
        var currentDay: Date?

        for event in events {
            let eventDay = calendar.startOfDay(for: event.startDate)

            // Show date header if different day
            if currentDay != eventDay {
                currentDay = eventDay
                let dateFormatter = DateFormatter()
                dateFormatter.dateStyle = .medium
                summary += "\n📅 \(dateFormatter.string(from: eventDay))\n"
            }

            summary += "   • \(formatEvent(event))\n"
        }

        return summary
    }

    // MARK: - Statistics

    func getStats() -> [String: Any] {
        return [
            "has_calendar_access": hasCalendarAccess,
            "has_reminders_access": hasRemindersAccess,
            "today_events_count": getTodayEvents().count
        ]
    }
}

// MARK: - Event Extension

extension EKEvent {
    var displayText: String {
        CalendarService.shared.formatEvent(self)
    }
}

// MARK: - Reminder Extension

extension EKReminder {
    var displayText: String {
        CalendarService.shared.formatReminder(self)
    }
}
