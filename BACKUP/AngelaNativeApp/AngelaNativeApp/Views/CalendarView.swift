//
//  CalendarView.swift
//  AngelaNativeApp
//
//  Calendar view showing David's schedule from macOS Calendar
//

import SwiftUI
import Combine

struct CalendarView: View {
    @StateObject private var viewModel = CalendarViewModel()

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            Divider()

            // Content
            if viewModel.isLoading {
                loadingView
            } else if let error = viewModel.errorMessage {
                errorView(error)
            } else {
                if viewModel.viewMode == .month {
                    MonthGridView(events: viewModel.events)
                } else if viewModel.viewMode == .week {
                    WeekGridView(events: viewModel.events)
                } else {
                    eventsListView
                }
            }
        }
        .task {
            await viewModel.loadTodayEvents()
        }
    }

    // MARK: - Header

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("📅 Calendar")
                    .font(.title2)
                    .fontWeight(.bold)

                HStack(spacing: 8) {
                    Text(viewModel.dateRange)
                        .font(.caption)
                        .foregroundColor(.secondary)

                    if viewModel.events.count > 0 {
                        Text("•")
                            .foregroundColor(.secondary)
                        Text("\(viewModel.events.count) event\(viewModel.events.count == 1 ? "" : "s")")
                            .font(.caption)
                            .foregroundColor(.blue)
                            .fontWeight(.medium)
                    }
                }
            }

            Spacer()

            // View mode picker
            Picker("View", selection: $viewModel.viewMode) {
                Text("Today").tag(CalendarViewMode.today)
                Text("Week").tag(CalendarViewMode.week)
                Text("Month").tag(CalendarViewMode.month)
            }
            .pickerStyle(.segmented)
            .frame(width: 200)

            Button(action: { Task { await viewModel.refresh() } }) {
                Image(systemName: "arrow.clockwise")
                    .foregroundColor(.blue)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isLoading)
        }
        .padding()
    }

    // MARK: - Events List

    private var eventsListView: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 16) {
                if viewModel.events.isEmpty {
                    emptyStateView
                } else {
                    ForEach(groupEventsByDate(), id: \.date) { group in
                        VStack(alignment: .leading, spacing: 12) {
                            // Date header (only for week/month view)
                            if viewModel.viewMode != .today {
                                Text(group.date)
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                                    .foregroundColor(.primary)
                                    .padding(.horizontal, 4)
                                    .padding(.top, 8)
                            }

                            ForEach(group.events) { event in
                                EventCard(event: event)
                            }
                        }
                    }
                }
            }
            .padding()
        }
    }

    private func groupEventsByDate() -> [(date: String, events: [CalendarEvent])] {
        let grouped = Dictionary(grouping: viewModel.events) { event -> String in
            // Extract date from event.start
            if let range = event.start.range(of: ",") {
                let dateStr = String(event.start[..<range.upperBound])
                return dateStr.trimmingCharacters(in: .whitespaces)
            }
            return "Today"
        }

        return grouped.map { (date: $0.key, events: $0.value) }
            .sorted { $0.date < $1.date }
    }

    // MARK: - Empty State

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "calendar")
                .font(.system(size: 60))
                .foregroundColor(.gray)

            Text("No Events")
                .font(.title3)
                .fontWeight(.medium)

            Text("You have no events scheduled for \(viewModel.viewMode.rawValue.lowercased())")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    // MARK: - Loading

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)

            Text("Loading events...")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Error

    private func errorView(_ error: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 50))
                .foregroundColor(.red)

            Text("Error")
                .font(.title3)
                .fontWeight(.medium)

            Text(error)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button("Retry") {
                Task { await viewModel.refresh() }
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}

// MARK: - Event Card

struct EventCard: View {
    let event: CalendarEvent

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Time indicator with colored accent
            VStack(spacing: 6) {
                Text(formatTime(event.start))
                    .font(.system(.caption, design: .rounded))
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(Color.blue)
                    )

                Image(systemName: "arrow.down")
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)

                Text(formatTime(event.end))
                    .font(.system(.caption, design: .rounded))
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
            }
            .frame(width: 70)

            // Event details
            VStack(alignment: .leading, spacing: 8) {
                Text(event.title)
                    .font(.headline)
                    .foregroundColor(.primary)

                if !event.location.isEmpty {
                    HStack(spacing: 6) {
                        Image(systemName: "location.fill")
                            .font(.caption2)
                            .foregroundColor(.green)
                        Text(event.location)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                if !event.notes.isEmpty {
                    HStack(spacing: 6) {
                        Image(systemName: "note.text")
                            .font(.caption2)
                            .foregroundColor(.orange)
                        Text(event.notes)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .lineLimit(3)
                    }
                }
            }

            Spacer()
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.controlBackgroundColor))
                .shadow(color: .black.opacity(0.05), radius: 4, x: 0, y: 2)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(Color.blue.opacity(0.2), lineWidth: 1)
        )
    }

    private func formatTime(_ timeString: String) -> String {
        // Parse time from format like "Thursday, October 17, 2025 at 2:00:00 PM"
        // Just extract the time part
        if let timeRange = timeString.range(of: "at ") {
            let time = String(timeString[timeRange.upperBound...])
            // Remove seconds
            let components = time.components(separatedBy: ":")
            if components.count >= 2 {
                return "\(components[0]):\(components[1])"
            }
            return time
        }
        return timeString
    }
}

// MARK: - View Model

enum CalendarViewMode: String {
    case today = "Today"
    case week = "Week"
    case month = "Month"
}

@MainActor
class CalendarViewModel: ObservableObject {
    @Published var events: [CalendarEvent] = []
    @Published var viewMode: CalendarViewMode = .today {
        didSet {
            Task { await refresh() }
        }
    }
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var dateRange: String = ""

    private let calendarService = CalendarService.shared

    func loadTodayEvents() async {
        await refresh()
    }

    func refresh() async {
        isLoading = true
        errorMessage = nil

        do {
            let response: CalendarEventsResponse

            switch viewMode {
            case .today:
                response = try await calendarService.getTodayEvents()
                dateRange = "Today - \(response.date)"

            case .week:
                // Get current week (Monday - Sunday)
                let calendar = Calendar.current
                let now = Date()
                let weekday = calendar.component(.weekday, from: now)
                let daysFromMonday = (weekday + 5) % 7

                guard let monday = calendar.date(byAdding: .day, value: -daysFromMonday, to: now),
                      let sunday = calendar.date(byAdding: .day, value: 6, to: monday) else {
                    throw CalendarError.notFound
                }

                response = try await calendarService.getEventsInRange(startDate: monday, endDate: sunday)
                dateRange = response.date

            case .month:
                // Get current month
                let calendar = Calendar.current
                let now = Date()
                guard let firstOfMonth = calendar.date(from: calendar.dateComponents([.year, .month], from: now)),
                      let lastOfMonth = calendar.date(byAdding: DateComponents(month: 1, day: -1), to: firstOfMonth) else {
                    throw CalendarError.notFound
                }

                response = try await calendarService.getEventsInRange(startDate: firstOfMonth, endDate: lastOfMonth)
                dateRange = "This month"
            }

            events = response.events

        } catch {
            errorMessage = error.localizedDescription
            print("❌ Failed to load events: \(error)")
        }

        isLoading = false
    }
}

// MARK: - Preview

#Preview {
    CalendarView()
        .frame(width: 600, height: 800)
}
