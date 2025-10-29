//
//  CalendarService.swift
//  AngelaNativeApp
//
//  Native macOS Calendar integration using EventKit
//

import Foundation
import EventKit
import Combine

@MainActor
class CalendarService: ObservableObject {
    static let shared = CalendarService()

    private let eventStore = EKEventStore()
    @Published var hasAccess = false

    private init() {
        Task {
            await requestAccess()
        }
    }

    // MARK: - Access

    func requestAccess() async {
        print("🔍 Requesting calendar access...")

        // Use new API for macOS 14.0+
        let granted = await withCheckedContinuation { continuation in
            eventStore.requestFullAccessToEvents { granted, error in
                if let error = error {
                    print("❌ Calendar access error: \(error)")
                    print("❌ Error details: \(error.localizedDescription)")
                }
                print("📊 Access granted: \(granted)")
                continuation.resume(returning: granted)
            }
        }

        hasAccess = granted
        print(hasAccess ? "✅ Calendar access granted" : "❌ Calendar access denied")
    }

    // MARK: - Get Events

    func getTodayEvents() async throws -> CalendarEventsResponse {
        // Request access if not already granted
        if !hasAccess {
            await requestAccess()
        }

        guard hasAccess else {
            throw CalendarError.accessDenied
        }

        let calendar = Calendar.current
        let startOfDay = calendar.startOfDay(for: Date())
        let endOfDay = calendar.date(byAdding: .day, value: 1, to: startOfDay)!

        let predicate = eventStore.predicateForEvents(
            withStart: startOfDay,
            end: endOfDay,
            calendars: nil
        )

        let events = eventStore.events(matching: predicate)

        // Use ISO8601 formatter for consistent date parsing
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let calendarEvents = events.map { event in
            CalendarEvent(
                title: event.title ?? "Untitled",
                start: formatter.string(from: event.startDate),
                end: formatter.string(from: event.endDate),
                location: event.location ?? "",
                notes: event.notes ?? ""
            )
        }

        return CalendarEventsResponse(
            date: Date().formatted(date: .abbreviated, time: .omitted),
            events: calendarEvents,
            count: calendarEvents.count
        )
    }

    func getUpcomingEvents(days: Int = 7) async throws -> CalendarEventsResponse {
        // Request access if not already granted
        if !hasAccess {
            await requestAccess()
        }

        guard hasAccess else {
            throw CalendarError.accessDenied
        }

        let calendar = Calendar.current
        let startDate = Date()
        let endDate = calendar.date(byAdding: .day, value: days, to: startDate)!

        let predicate = eventStore.predicateForEvents(
            withStart: startDate,
            end: endDate,
            calendars: nil
        )

        let events = eventStore.events(matching: predicate)

        // Use ISO8601 formatter for consistent date parsing
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let calendarEvents = events.map { event in
            CalendarEvent(
                title: event.title ?? "Untitled",
                start: formatter.string(from: event.startDate),
                end: formatter.string(from: event.endDate),
                location: event.location ?? "",
                notes: event.notes ?? ""
            )
        }

        return CalendarEventsResponse(
            date: "Next \(days) days",
            events: calendarEvents,
            count: calendarEvents.count
        )
    }

    func getEventsInRange(startDate: Date, endDate: Date) async throws -> CalendarEventsResponse {
        // Request access if not already granted
        if !hasAccess {
            await requestAccess()
        }

        guard hasAccess else {
            throw CalendarError.accessDenied
        }

        let predicate = eventStore.predicateForEvents(
            withStart: startDate,
            end: endDate,
            calendars: nil
        )

        let events = eventStore.events(matching: predicate)

        // Use ISO8601 formatter for consistent date parsing
        let dateFormatter = DateFormatter()
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let calendarEvents = events.map { event in
            CalendarEvent(
                title: event.title ?? "Untitled",
                start: dateFormatter.string(from: event.startDate),
                end: dateFormatter.string(from: event.endDate),
                location: event.location ?? "",
                notes: event.notes ?? ""
            )
        }

        let rangeFormatter = DateFormatter()
        rangeFormatter.dateStyle = .medium

        return CalendarEventsResponse(
            date: "\(rangeFormatter.string(from: startDate)) - \(rangeFormatter.string(from: endDate))",
            events: calendarEvents,
            count: calendarEvents.count
        )
    }

    func searchEvents(query: String, days: Int = 30) async throws -> CalendarEventsResponse {
        // Request access if not already granted
        if !hasAccess {
            await requestAccess()
        }

        guard hasAccess else {
            throw CalendarError.accessDenied
        }

        let calendar = Calendar.current
        let startDate = Date()
        let endDate = calendar.date(byAdding: .day, value: days, to: startDate)!

        let predicate = eventStore.predicateForEvents(
            withStart: startDate,
            end: endDate,
            calendars: nil
        )

        let events = eventStore.events(matching: predicate)

        // Filter by query
        let filteredEvents = events.filter { event in
            let title = event.title ?? ""
            let location = event.location ?? ""
            let notes = event.notes ?? ""

            return title.localizedCaseInsensitiveContains(query) ||
                   location.localizedCaseInsensitiveContains(query) ||
                   notes.localizedCaseInsensitiveContains(query)
        }

        // Use ISO8601 formatter for consistent date parsing
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let calendarEvents = filteredEvents.map { event in
            CalendarEvent(
                title: event.title ?? "Untitled",
                start: formatter.string(from: event.startDate),
                end: formatter.string(from: event.endDate),
                location: event.location ?? "",
                notes: event.notes ?? ""
            )
        }

        return CalendarEventsResponse(
            date: "Search results",
            events: calendarEvents,
            count: calendarEvents.count
        )
    }

    func getCalendars() async throws -> [String] {
        guard hasAccess else {
            throw CalendarError.accessDenied
        }

        let calendars = eventStore.calendars(for: .event)
        return calendars.map { $0.title }
    }
}

// MARK: - Errors

enum CalendarError: Error, LocalizedError {
    case accessDenied
    case notFound

    var errorDescription: String? {
        switch self {
        case .accessDenied:
            return "Calendar access denied. Please grant access in System Settings."
        case .notFound:
            return "Calendar not found"
        }
    }
}
