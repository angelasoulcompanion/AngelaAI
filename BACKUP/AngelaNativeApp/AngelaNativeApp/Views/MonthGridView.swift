//
//  MonthGridView.swift
//  AngelaNativeApp
//
//  Calendar Month Grid View - Similar to macOS Calendar app
//

import SwiftUI
import EventKit
import Combine

struct MonthGridView: View {
    @StateObject private var viewModel = MonthGridViewModel()
    let events: [CalendarEvent]

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 1), count: 7)
    private let weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    var body: some View {
        VStack(spacing: 0) {
            // Month navigation header
            monthHeader

            Divider()

            // Weekday headers
            weekdayHeader

            Divider()

            // Calendar grid
            ScrollView {
                LazyVGrid(columns: columns, spacing: 1) {
                    ForEach(viewModel.daysInMonth, id: \.self) { date in
                        DayCell(
                            date: date,
                            isCurrentMonth: viewModel.isInCurrentMonth(date),
                            isToday: viewModel.isToday(date),
                            events: viewModel.eventsForDate(date, allEvents: events)
                        )
                    }
                }
                .background(Color.gray.opacity(0.2))
            }
        }
        .onAppear {
            viewModel.generateCalendar()
        }
    }

    // MARK: - Month Header

    private var monthHeader: some View {
        HStack {
            Text(viewModel.currentMonthYear)
                .font(.title2)
                .fontWeight(.bold)

            Spacer()

            HStack(spacing: 8) {
                Button(action: { viewModel.previousMonth() }) {
                    Image(systemName: "chevron.left")
                        .foregroundColor(.blue)
                }
                .buttonStyle(.plain)

                Button("Today") {
                    viewModel.goToToday()
                }
                .buttonStyle(.bordered)

                Button(action: { viewModel.nextMonth() }) {
                    Image(systemName: "chevron.right")
                        .foregroundColor(.blue)
                }
                .buttonStyle(.plain)
            }
        }
        .padding()
    }

    // MARK: - Weekday Header

    private var weekdayHeader: some View {
        LazyVGrid(columns: columns, spacing: 1) {
            ForEach(weekdays, id: \.self) { day in
                Text(day)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(Color(.controlBackgroundColor))
            }
        }
    }
}

// MARK: - Day Cell

struct DayCell: View {
    let date: Date
    let isCurrentMonth: Bool
    let isToday: Bool
    let events: [CalendarEvent]

    private var dayNumber: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "d"
        return formatter.string(from: date)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            // Day number
            HStack {
                if isToday {
                    Text(dayNumber)
                        .font(.caption)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                        .frame(width: 20, height: 20)
                        .background(Circle().fill(Color.red))
                } else {
                    Text(dayNumber)
                        .font(.caption)
                        .fontWeight(isCurrentMonth ? .medium : .regular)
                        .foregroundColor(isCurrentMonth ? .primary : .secondary)
                }
                Spacer()
            }

            // Events (max 3 visible)
            ForEach(events.prefix(3)) { event in
                EventBar(event: event)
            }

            if events.count > 3 {
                Text("+\(events.count - 3) more")
                    .font(.system(size: 9))
                    .foregroundColor(.secondary)
                    .padding(.leading, 2)
            }

            Spacer()
        }
        .padding(4)
        .frame(height: 80)
        .background(isCurrentMonth ? Color(.controlBackgroundColor) : Color(.controlBackgroundColor).opacity(0.5))
    }
}

// MARK: - Event Bar

struct EventBar: View {
    let event: CalendarEvent

    var body: some View {
        HStack(spacing: 2) {
            Circle()
                .fill(eventColor)
                .frame(width: 4, height: 4)

            Text(extractTime(from: event.start))
                .font(.system(size: 9))
                .foregroundColor(.white)

            Text(event.title)
                .font(.system(size: 9))
                .foregroundColor(.white)
                .lineLimit(1)
        }
        .padding(.horizontal, 4)
        .padding(.vertical, 2)
        .background(
            RoundedRectangle(cornerRadius: 3)
                .fill(eventColor)
        )
    }

    private var eventColor: Color {
        // Use different colors for different event types
        let colors: [Color] = [.blue, .orange, .green, .purple, .pink, .teal]
        let hash = abs(event.title.hashValue)
        return colors[hash % colors.count]
    }

    private func extractTime(from dateString: String) -> String {
        // Parse ISO8601 format: "yyyy-MM-dd HH:mm:ss"
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        guard let date = formatter.date(from: dateString) else {
            return ""
        }

        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm"
        return timeFormatter.string(from: date)
    }
}

// MARK: - View Model

@MainActor
class MonthGridViewModel: ObservableObject {
    @Published var currentDate = Date()
    @Published var daysInMonth: [Date] = []

    var currentMonthYear: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM yyyy"
        return formatter.string(from: currentDate)
    }

    func generateCalendar() {
        daysInMonth = getDaysInMonth(for: currentDate)
    }

    func previousMonth() {
        if let newDate = Calendar.current.date(byAdding: .month, value: -1, to: currentDate) {
            currentDate = newDate
            generateCalendar()
        }
    }

    func nextMonth() {
        if let newDate = Calendar.current.date(byAdding: .month, value: 1, to: currentDate) {
            currentDate = newDate
            generateCalendar()
        }
    }

    func goToToday() {
        currentDate = Date()
        generateCalendar()
    }

    func isInCurrentMonth(_ date: Date) -> Bool {
        Calendar.current.isDate(date, equalTo: currentDate, toGranularity: .month)
    }

    func isToday(_ date: Date) -> Bool {
        Calendar.current.isDateInToday(date)
    }

    func eventsForDate(_ date: Date, allEvents: [CalendarEvent]) -> [CalendarEvent] {
        let calendar = Calendar.current

        // Use ISO8601 formatter matching CalendarService
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        return allEvents.filter { event in
            if let eventDate = formatter.date(from: event.start) {
                return calendar.isDate(eventDate, inSameDayAs: date)
            }
            return false
        }
    }

    private func getDaysInMonth(for date: Date) -> [Date] {
        let calendar = Calendar.current

        // Get first day of month
        guard let firstOfMonth = calendar.date(from: calendar.dateComponents([.year, .month], from: date)) else {
            return []
        }

        // Get first day to show (previous month days)
        let firstWeekday = calendar.component(.weekday, from: firstOfMonth)
        let daysFromPreviousMonth = (firstWeekday + 5) % 7 // Adjust for Monday start

        guard let startDate = calendar.date(byAdding: .day, value: -daysFromPreviousMonth, to: firstOfMonth) else {
            return []
        }

        // Generate 42 days (6 weeks)
        var days: [Date] = []
        for i in 0..<42 {
            if let day = calendar.date(byAdding: .day, value: i, to: startDate) {
                days.append(day)
            }
        }

        return days
    }
}

// MARK: - Preview

#Preview {
    MonthGridView(events: [])
        .frame(width: 800, height: 600)
}
