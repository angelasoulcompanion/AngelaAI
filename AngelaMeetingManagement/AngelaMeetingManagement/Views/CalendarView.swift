//
//  CalendarView.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜
//  ClickUp-inspired Calendar View with Purple Theme
//

import SwiftUI

struct CalendarView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @ObservedObject var viewModel: MeetingListViewModel
    @Binding var selectedMeeting: Meeting?

    // Filters
    let searchText: String
    let selectedPriorities: Set<String>
    let selectedStatuses: Set<String>
    let dateRange: DateRange?

    @State private var currentMonth = Date()
    @State private var selectedDate: Date?

    private let calendar = Calendar.current
    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM yyyy"
        return formatter
    }()

    var body: some View {
        HSplitView {
            // Left: Calendar Grid
            VStack(spacing: 0) {
                // Calendar Header
                calendarHeader

                Divider()

                // Calendar Grid
                ScrollView {
                    VStack(spacing: AngelaTheme.spacingL) {
                        calendarGrid
                    }
                    .padding(AngelaTheme.spacingXL)
                }
            }
            .frame(minWidth: 600, idealWidth: 800)
            .background(AngelaTheme.background)

            // Right: Selected Day's Meetings
            VStack(alignment: .leading, spacing: AngelaTheme.spacingL) {
                if let date = selectedDate {
                    // Day header
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(date, style: .date)
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(AngelaTheme.textPrimary)

                            Text("\(meetingsForDate(date).count) meetings")
                                .font(.system(size: 13))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }

                        Spacer()

                        Button(action: {
                            selectedDate = nil
                        }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(AngelaTheme.textSecondary)
                                .font(.system(size: 20))
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(AngelaTheme.spacingL)
                    .background(AngelaTheme.palePurple)

                    Divider()

                    // Meetings list
                    ScrollView {
                        VStack(spacing: AngelaTheme.spacingM) {
                            ForEach(meetingsForDate(date)) { meeting in
                                CalendarMeetingCard(
                                    meeting: meeting,
                                    isSelected: selectedMeeting?.id == meeting.id,
                                    onTap: {
                                        selectedMeeting = meeting
                                    }
                                )
                            }
                        }
                        .padding(AngelaTheme.spacingL)
                    }
                } else {
                    // No date selected
                    VStack(spacing: AngelaTheme.spacingL) {
                        Image(systemName: "calendar.badge.clock")
                            .font(.system(size: 60))
                            .foregroundColor(AngelaTheme.primaryPurple.opacity(0.3))

                        Text("Select a Date")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(AngelaTheme.textPrimary)

                        Text("Click on any date to view meetings")
                            .font(.system(size: 13))
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
            .frame(minWidth: 350, idealWidth: 400)
            .background(AngelaTheme.cardBackground)
        }
    }

    // MARK: - Calendar Header
    private var calendarHeader: some View {
        HStack {
            Button(action: previousMonth) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)

            Spacer()

            Text(dateFormatter.string(from: currentMonth))
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            Spacer()

            Button(action: nextMonth) {
                Image(systemName: "chevron.right")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)

            Divider()
                .frame(height: 20)
                .padding(.horizontal, AngelaTheme.spacingM)

            Button("Today") {
                currentMonth = Date()
                selectedDate = Date()
            }
            .buttonStyle(AngelaSecondaryButtonStyle())
        }
        .padding(AngelaTheme.spacingL)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Calendar Grid
    private var calendarGrid: some View {
        VStack(spacing: AngelaTheme.spacingS) {
            // Weekday headers
            HStack(spacing: 0) {
                ForEach(weekdaySymbols, id: \.self) { symbol in
                    Text(symbol)
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(maxWidth: .infinity)
                }
            }
            .padding(.bottom, AngelaTheme.spacingS)

            // Days grid
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 7), spacing: 8) {
                ForEach(daysInMonth, id: \.self) { date in
                    if let date = date {
                        CalendarDayCell(
                            date: date,
                            isSelected: calendar.isDate(date, inSameDayAs: selectedDate ?? Date.distantPast),
                            isToday: calendar.isDateInToday(date),
                            meetingCount: meetingsForDate(date).count,
                            onTap: {
                                selectedDate = date
                            }
                        )
                    } else {
                        // Empty cell for padding
                        Color.clear
                            .frame(height: 100)
                    }
                }
            }
        }
    }

    // MARK: - Helper Properties
    private var weekdaySymbols: [String] {
        calendar.shortWeekdaySymbols
    }

    private var daysInMonth: [Date?] {
        guard let monthInterval = calendar.dateInterval(of: .month, for: currentMonth)
        else { return [] }

        let days = calendar.generateDates(
            inside: monthInterval,
            matching: DateComponents(hour: 0, minute: 0, second: 0)
        )

        let firstWeekday = calendar.component(.weekday, from: monthInterval.start)
        let leadingEmptyDays = Array(repeating: nil as Date?, count: firstWeekday - 1)

        return leadingEmptyDays + days.map { $0 as Date? }
    }

    // MARK: - Helper Functions
    private func previousMonth() {
        currentMonth = calendar.date(byAdding: .month, value: -1, to: currentMonth) ?? currentMonth
    }

    private func nextMonth() {
        currentMonth = calendar.date(byAdding: .month, value: 1, to: currentMonth) ?? currentMonth
    }

    private func meetingsForDate(_ date: Date) -> [Meeting] {
        viewModel.meetings.filter { meeting in
            // Date match
            guard calendar.isDate(meeting.scheduledDate, inSameDayAs: date) else { return false }

            // Search filter
            if !searchText.isEmpty {
                let searchLower = searchText.lowercased()
                let matchesTitle = meeting.title.lowercased().contains(searchLower)
                let matchesDescription = (meeting.description ?? "").lowercased().contains(searchLower)
                guard matchesTitle || matchesDescription else { return false }
            }

            // Priority filter
            if !selectedPriorities.isEmpty {
                guard selectedPriorities.contains(meeting.priority ?? "Normal") else { return false }
            }

            // Status filter
            if !selectedStatuses.isEmpty {
                guard selectedStatuses.contains(meeting.status.rawValue) else { return false }
            }

            // Date range filter
            if let range = dateRange {
                guard range.contains(meeting.meetingDate) else { return false }
            }

            return true
        }
    }
}

// MARK: - Calendar Day Cell
struct CalendarDayCell: View {
    let date: Date
    let isSelected: Bool
    let isToday: Bool
    let meetingCount: Int
    let onTap: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 8) {
                // Day number
                Text("\(Calendar.current.component(.day, from: date))")
                    .font(.system(size: 16, weight: isToday ? .bold : .medium))
                    .foregroundColor(
                        isSelected ? .white :
                        isToday ? AngelaTheme.primaryPurple :
                        AngelaTheme.textPrimary
                    )

                // Meeting count indicator
                if meetingCount > 0 {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(isSelected ? Color.white : AngelaTheme.primaryPurple)
                            .frame(width: 6, height: 6)

                        Text("\(meetingCount)")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(isSelected ? .white : AngelaTheme.primaryPurple)
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(
                        Capsule()
                            .fill(isSelected ? AngelaTheme.primaryPurple.opacity(0.3) : AngelaTheme.primaryPurple.opacity(0.15))
                    )
                }

                Spacer()
            }
            .frame(height: 100)
            .frame(maxWidth: .infinity)
            .padding(8)
            .background(
                Group {
                    if isSelected {
                        RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                            .fill(AngelaTheme.purpleGradient)
                    } else {
                        RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                            .fill(isHovered ? AngelaTheme.primaryPurple.opacity(0.1) : AngelaTheme.cardBackground)
                    }
                }
            )
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                    .stroke(
                        isToday && !isSelected ? AngelaTheme.primaryPurple :
                        isHovered ? AngelaTheme.primaryPurple.opacity(0.3) :
                        AngelaTheme.border,
                        lineWidth: isToday ? 2 : 1
                    )
            )
            .shadow(
                color: isSelected ? AngelaTheme.primaryPurple.opacity(0.3) : Color.clear,
                radius: 8,
                y: 4
            )
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - Calendar Meeting Card
struct CalendarMeetingCard: View {
    let meeting: Meeting
    let isSelected: Bool
    let onTap: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: AngelaTheme.spacingM) {
                // Time indicator
                VStack(alignment: .leading, spacing: 4) {
                    Text(meeting.scheduledDate, style: .time)
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Rectangle()
                        .fill(AngelaTheme.statusColor(for: meeting.status.rawValue))
                        .frame(width: 4)
                }
                .frame(width: 60)

                VStack(alignment: .leading, spacing: 8) {
                    // Title
                    Text(meeting.title)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)
                        .lineLimit(1)

                    // Metadata
                    HStack(spacing: AngelaTheme.spacingM) {
                        // Status badge
                        let statusText = meeting.status.rawValue
                        HStack(spacing: 4) {
                            Image(systemName: AngelaTheme.statusIcon(for: statusText))
                                .font(.system(size: 9))
                            Text(statusText.capitalized)
                                .font(.system(size: 10, weight: .medium))
                        }
                        .foregroundColor(AngelaTheme.statusColor(for: statusText))

                        // Priority badge
                        let priority = meeting.priority ?? "Normal"
                        HStack(spacing: 4) {
                            Image(systemName: AngelaTheme.priorityIcon(for: priority))
                                .font(.system(size: 9))
                            Text(priority)
                                .font(.system(size: 10, weight: .medium))
                        }
                        .foregroundColor(AngelaTheme.priorityColor(for: priority))
                    }
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .padding(AngelaTheme.spacingM)
            .angelaCard(isHovered: isHovered || isSelected)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

// MARK: - Calendar Extension
extension Calendar {
    func generateDates(
        inside interval: DateInterval,
        matching components: DateComponents
    ) -> [Date] {
        var dates: [Date] = []
        dates.append(interval.start)

        enumerateDates(
            startingAfter: interval.start,
            matching: components,
            matchingPolicy: .nextTime
        ) { date, _, stop in
            if let date = date {
                if date < interval.end {
                    dates.append(date)
                } else {
                    stop = true
                }
            }
        }

        return dates
    }
}

// MARK: - Preview
#Preview {
    CalendarView(
        viewModel: MeetingListViewModel(),
        selectedMeeting: .constant(nil),
        searchText: "",
        selectedPriorities: [],
        selectedStatuses: [],
        dateRange: nil
    )
    .environmentObject(DatabaseService.shared)
}
