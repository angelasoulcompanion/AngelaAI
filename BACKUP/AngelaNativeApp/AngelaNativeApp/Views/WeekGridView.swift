//
//  WeekGridView.swift
//  AngelaNativeApp
//
//  Calendar Week Grid View - Similar to macOS Calendar week view
//

import SwiftUI
import EventKit
import Combine

struct WeekGridView: View {
    @StateObject private var viewModel = WeekGridViewModel()
    let events: [CalendarEvent]

    private let hourHeight: CGFloat = 60
    private let hours = Array(0...23)

    var body: some View {
        VStack(spacing: 0) {
            // Week navigation header
            weekHeader

            Divider()

            // Calendar grid
            ScrollView {
                HStack(spacing: 0) {
                    // Time column
                    timeColumn

                    // Days columns
                    ForEach(viewModel.weekDays, id: \.self) { date in
                        dayColumn(for: date)
                    }
                }
            }
        }
        .onAppear {
            viewModel.generateWeek()
        }
    }

    // MARK: - Week Header

    private var weekHeader: some View {
        VStack(spacing: 0) {
            // Navigation
            HStack {
                Text(viewModel.currentWeekRange)
                    .font(.title2)
                    .fontWeight(.bold)

                Spacer()

                HStack(spacing: 8) {
                    Button(action: { viewModel.previousWeek() }) {
                        Image(systemName: "chevron.left")
                            .foregroundColor(.blue)
                    }
                    .buttonStyle(.plain)

                    Button("Today") {
                        viewModel.goToToday()
                    }
                    .buttonStyle(.bordered)

                    Button(action: { viewModel.nextWeek() }) {
                        Image(systemName: "chevron.right")
                            .foregroundColor(.blue)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 12)

            // Day headers
            HStack(spacing: 0) {
                // Empty space for time column
                Text("")
                    .frame(width: 60)

                // Day headers
                ForEach(viewModel.weekDays, id: \.self) { date in
                    dayHeader(for: date)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
    }

    private func dayHeader(for date: Date) -> some View {
        let formatter = DateFormatter()
        let dayName = formatter.shortWeekdaySymbols[Calendar.current.component(.weekday, from: date) - 1]
        let dayNumber = Calendar.current.component(.day, from: date)
        let isToday = Calendar.current.isDateInToday(date)

        return VStack(spacing: 4) {
            Text(dayName)
                .font(.caption)
                .foregroundColor(.secondary)

            if isToday {
                Text("\(dayNumber)")
                    .font(.title3)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .frame(width: 32, height: 32)
                    .background(Circle().fill(Color.red))
            } else {
                Text("\(dayNumber)")
                    .font(.title3)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
            }
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Time Column

    private var timeColumn: some View {
        VStack(spacing: 0) {
            ForEach(hours, id: \.self) { hour in
                HStack {
                    if hour > 0 {
                        Text(String(format: "%02d:00", hour))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    } else {
                        Text("")
                    }
                }
                .frame(width: 60, height: hourHeight, alignment: .topTrailing)
                .padding(.trailing, 8)
            }
        }
    }

    // MARK: - Day Column

    private func dayColumn(for date: Date) -> some View {
        ZStack(alignment: .topLeading) {
            // Grid lines
            VStack(spacing: 0) {
                ForEach(hours, id: \.self) { hour in
                    Rectangle()
                        .fill(Color.gray.opacity(0.1))
                        .frame(height: 1)

                    Spacer()
                        .frame(height: hourHeight - 1)
                }
            }

            // Events
            ForEach(viewModel.eventsForDate(date, allEvents: events)) { event in
                eventBlock(event: event)
            }
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Event Block

    private func eventBlock(event: CalendarEvent) -> some View {
        let position = viewModel.calculateEventPosition(event: event, hourHeight: hourHeight)

        return VStack(alignment: .leading, spacing: 4) {
            Text(event.title)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .lineLimit(2)

            if !event.location.isEmpty {
                HStack(spacing: 2) {
                    Image(systemName: "location.fill")
                        .font(.system(size: 8))
                    Text(event.location)
                        .font(.system(size: 9))
                }
                .foregroundColor(.white.opacity(0.9))
                .lineLimit(1)
            }

            Text(viewModel.formatTimeRange(event: event))
                .font(.system(size: 9))
                .foregroundColor(.white.opacity(0.8))
        }
        .padding(6)
        .frame(maxWidth: .infinity, alignment: .leading)
        .frame(height: position.height)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(eventColor(for: event))
        )
        .padding(.horizontal, 4)
        .offset(y: position.yOffset)
    }

    private func eventColor(for event: CalendarEvent) -> Color {
        let colors: [Color] = [.orange, .blue, .green, .purple, .pink, .teal, .indigo]
        let hash = abs(event.title.hashValue)
        return colors[hash % colors.count]
    }
}

// MARK: - View Model

@MainActor
class WeekGridViewModel: ObservableObject {
    @Published var currentWeekStart = Date()
    @Published var weekDays: [Date] = []

    var currentWeekRange: String {
        guard let firstDay = weekDays.first,
              let lastDay = weekDays.last else {
            return ""
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d"

        return "\(formatter.string(from: firstDay)) - \(formatter.string(from: lastDay))"
    }

    func generateWeek() {
        let calendar = Calendar.current

        // Get Monday of current week
        let weekday = calendar.component(.weekday, from: currentWeekStart)
        let daysFromMonday = (weekday + 5) % 7

        guard let monday = calendar.date(byAdding: .day, value: -daysFromMonday, to: currentWeekStart) else {
            return
        }

        // Generate 7 days (Mon-Sun)
        weekDays = (0..<7).compactMap { day in
            calendar.date(byAdding: .day, value: day, to: monday)
        }
    }

    func previousWeek() {
        if let newDate = Calendar.current.date(byAdding: .weekOfYear, value: -1, to: currentWeekStart) {
            currentWeekStart = newDate
            generateWeek()
        }
    }

    func nextWeek() {
        if let newDate = Calendar.current.date(byAdding: .weekOfYear, value: 1, to: currentWeekStart) {
            currentWeekStart = newDate
            generateWeek()
        }
    }

    func goToToday() {
        currentWeekStart = Date()
        generateWeek()
    }

    func eventsForDate(_ date: Date, allEvents: [CalendarEvent]) -> [CalendarEvent] {
        let calendar = Calendar.current

        // Use ISO8601 formatter matching CalendarService
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        let filtered = allEvents.filter { event in
            if let eventDate = formatter.date(from: event.start) {
                return calendar.isDate(eventDate, inSameDayAs: date)
            }
            return false
        }

        return filtered
    }

    func calculateEventPosition(event: CalendarEvent, hourHeight: CGFloat) -> (yOffset: CGFloat, height: CGFloat) {
        // Use ISO8601 formatter matching CalendarService
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        guard let startDate = formatter.date(from: event.start),
              let endDate = formatter.date(from: event.end) else {
            return (0, 60)
        }

        let calendar = Calendar.current
        let startHour = calendar.component(.hour, from: startDate)
        let startMinute = calendar.component(.minute, from: startDate)
        let endHour = calendar.component(.hour, from: endDate)
        let endMinute = calendar.component(.minute, from: endDate)

        let startOffset = CGFloat(startHour) * hourHeight + (CGFloat(startMinute) / 60.0) * hourHeight
        let endOffset = CGFloat(endHour) * hourHeight + (CGFloat(endMinute) / 60.0) * hourHeight

        let height = max(endOffset - startOffset, 30) // Minimum 30pt height

        return (startOffset, height)
    }

    func formatTimeRange(event: CalendarEvent) -> String {
        // Use ISO8601 formatter matching CalendarService
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"

        guard let startDate = formatter.date(from: event.start),
              let endDate = formatter.date(from: event.end) else {
            return ""
        }

        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm"

        return "\(timeFormatter.string(from: startDate)) - \(timeFormatter.string(from: endDate))"
    }
}

// MARK: - Preview

#Preview {
    WeekGridView(events: [])
        .frame(width: 1000, height: 700)
}
