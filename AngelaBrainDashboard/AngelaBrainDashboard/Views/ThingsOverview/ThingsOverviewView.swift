//
//  ThingsOverviewView.swift
//  Angela Brain Dashboard
//
//  Things Overview - Meeting Dashboard & Calendar
//

import SwiftUI
import Charts
import Combine

struct ThingsOverviewView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = ThingsOverviewViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                header
                if let stats = viewModel.stats {
                    statsRow(stats)
                }
                calendarCard
                if !viewModel.upcomingMeetings.isEmpty {
                    upcomingMeetingsCard
                }
                if !viewModel.projectBreakdown.isEmpty {
                    projectBreakdownCard
                }
                completedMeetingsCard
            }
            .padding(AngelaTheme.largeSpacing)
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Things Overview")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Meeting Dashboard & Calendar")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Button {
                Task {
                    await viewModel.loadData(databaseService: databaseService)
                }
            } label: {
                Image(systemName: viewModel.isLoading ? "arrow.trianglehead.2.clockwise" : "arrow.trianglehead.2.clockwise")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .frame(width: 32, height: 32)
                    .background(AngelaTheme.primaryPurple.opacity(0.12))
                    .cornerRadius(8)
                    .rotationEffect(.degrees(viewModel.isLoading ? 360 : 0))
                    .animation(viewModel.isLoading ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: viewModel.isLoading)
            }
            .buttonStyle(.plain)
            .help("Refresh data")

            Image(systemName: "checklist")
                .font(.system(size: 28))
                .foregroundColor(AngelaTheme.primaryPurple)
        }
    }

    // MARK: - Stats Row

    private func statsRow(_ stats: MeetingStats) -> some View {
        HStack(spacing: AngelaTheme.spacing) {
            statCard(title: "Total", value: "\(stats.totalMeetings)", icon: "doc.text.fill", color: "3B82F6")
            statCard(title: "This Month", value: "\(stats.thisMonth)", icon: "calendar", color: "9333EA")
            statCard(title: "Upcoming", value: "\(stats.upcoming ?? 0)", icon: "clock.badge.exclamationmark.fill", color: "6366F1")
            statCard(title: "Open Actions", value: "\(stats.openActions)", icon: "exclamationmark.circle.fill", color: "F59E0B")
            statCard(title: "Completion", value: "\(Int(stats.completionRate))%", icon: "checkmark.circle.fill", color: "10B981")
        }
    }

    private func statCard(title: String, value: String, icon: String, color: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 22))
                .foregroundColor(Color(hex: color))

            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Calendar Card

    private var calendarCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Button {
                    viewModel.previousMonth()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(width: 28, height: 28)
                        .background(AngelaTheme.backgroundLight)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)

                Spacer()

                Text(viewModel.monthYearString)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button {
                    viewModel.nextMonth()
                } label: {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(width: 28, height: 28)
                        .background(AngelaTheme.backgroundLight)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }

            // Day of week headers
            HStack(spacing: 0) {
                ForEach(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], id: \.self) { day in
                    Text(day)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .frame(maxWidth: .infinity)
                }
            }

            // Calendar grid
            let days = viewModel.calendarDays()
            let rows = stride(from: 0, to: days.count, by: 7).map { Array(days[$0..<min($0+7, days.count)]) }

            VStack(spacing: 4) {
                ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                    HStack(spacing: 0) {
                        ForEach(row) { day in
                            calendarDayCell(day)
                                .frame(maxWidth: .infinity)
                        }
                    }
                }
            }

            // Legend
            HStack(spacing: 16) {
                HStack(spacing: 4) {
                    Circle().fill(Color(hex: "3B82F6")).frame(width: 6, height: 6)
                    Text("Meeting").font(.system(size: 10)).foregroundColor(AngelaTheme.textTertiary)
                }
                HStack(spacing: 4) {
                    Circle().fill(Color(hex: "10B981")).frame(width: 6, height: 6)
                    Text("Site Visit").font(.system(size: 10)).foregroundColor(AngelaTheme.textTertiary)
                }
                HStack(spacing: 4) {
                    RoundedRectangle(cornerRadius: 2)
                        .stroke(Color(hex: "9333EA"), lineWidth: 1.5)
                        .frame(width: 6, height: 6)
                    Text("Today").font(.system(size: 10)).foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .padding(.top, 4)
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    private func calendarDayCell(_ day: CalendarDay) -> some View {
        VStack(spacing: 2) {
            if day.dayNumber > 0 {
                Text("\(day.dayNumber)")
                    .font(.system(size: 12, weight: day.isToday ? .bold : .regular))
                    .foregroundColor(
                        day.isToday ? AngelaTheme.primaryPurple :
                        day.isCurrentMonth ? AngelaTheme.textPrimary : AngelaTheme.textTertiary.opacity(0.5)
                    )

                // Meeting dots
                HStack(spacing: 2) {
                    if day.meetingCount > 0 {
                        Circle()
                            .fill(Color(hex: "3B82F6"))
                            .frame(width: 5, height: 5)
                    }
                    if day.siteVisitCount > 0 {
                        Circle()
                            .fill(Color(hex: "10B981"))
                            .frame(width: 5, height: 5)
                    }
                }
                .frame(height: 6)
            } else {
                Text("")
                    .font(.system(size: 12))
                    .frame(height: 14)
                Spacer().frame(height: 6)
            }
        }
        .frame(height: 28)
        .frame(maxWidth: .infinity)
        .background(
            day.isToday ?
                AnyShapeStyle(Color(hex: "9333EA").opacity(0.15)) :
                AnyShapeStyle(Color.clear)
        )
        .cornerRadius(4)
    }

    // MARK: - Upcoming Meetings Card

    private var upcomingMeetingsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "clock.badge.exclamationmark.fill")
                    .foregroundColor(Color(hex: "6366F1"))

                Text("Upcoming Meetings")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(viewModel.upcomingMeetings.count)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(Color(hex: "6366F1"))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: "6366F1").opacity(0.15))
                    .cornerRadius(6)
            }

            VStack(spacing: AngelaTheme.smallSpacing) {
                ForEach(viewModel.upcomingMeetings.prefix(5)) { meeting in
                    MeetingCard(
                        meeting: meeting,
                        isExpanded: viewModel.expandedMeetingId == meeting.id
                    ) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            if viewModel.expandedMeetingId == meeting.id {
                                viewModel.expandedMeetingId = nil
                            } else {
                                viewModel.expandedMeetingId = meeting.id
                            }
                        }
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Project Breakdown Card

    private var projectBreakdownCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "chart.pie.fill")
                    .foregroundColor(Color(hex: "8B5CF6"))

                Text("Project Breakdown")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()
            }

            // Donut chart
            Chart(viewModel.projectBreakdown) { item in
                SectorMark(
                    angle: .value("Meetings", item.meetingCount),
                    innerRadius: .ratio(0.55),
                    angularInset: 1.5
                )
                .foregroundStyle(by: .value("Project", item.projectName))
                .annotation(position: .overlay) {
                    if item.meetingCount >= 2 {
                        Text("\(item.meetingCount)")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.white)
                    }
                }
            }
            .chartForegroundStyleScale(domain: viewModel.projectBreakdown.map(\.projectName),
                                        range: projectChartColors)
            .frame(height: 200)

            // Breakdown table
            VStack(spacing: 6) {
                ForEach(Array(viewModel.projectBreakdown.enumerated()), id: \.element.id) { index, item in
                    HStack(spacing: 8) {
                        Circle()
                            .fill(projectChartColors[index % projectChartColors.count])
                            .frame(width: 8, height: 8)

                        Text(item.projectName)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .lineLimit(1)

                        Spacer()

                        Text("\(item.openCount) open")
                            .font(.system(size: 10))
                            .foregroundColor(Color(hex: "3B82F6"))

                        Text("\(item.completedCount) done")
                            .font(.system(size: 10))
                            .foregroundColor(Color(hex: "10B981"))

                        if item.siteVisitCount > 0 {
                            Text("\(item.siteVisitCount) site")
                                .font(.system(size: 10))
                                .foregroundColor(Color(hex: "F59E0B"))
                        }

                        Text("\(item.meetingCount)")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(AngelaTheme.textPrimary)
                            .frame(width: 24, alignment: .trailing)
                    }
                    .padding(.vertical, 4)
                    .padding(.horizontal, 8)
                    .background(index % 2 == 0 ? AngelaTheme.backgroundLight.opacity(0.3) : Color.clear)
                    .cornerRadius(4)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    private var projectChartColors: [Color] {
        [
            Color(hex: "9333EA"),  // Purple
            Color(hex: "3B82F6"),  // Blue
            Color(hex: "10B981"),  // Green
            Color(hex: "F59E0B"),  // Orange
            Color(hex: "EC4899"),  // Pink
            Color(hex: "6366F1"),  // Indigo
            Color(hex: "14B8A6"),  // Teal
            Color(hex: "EF4444"),  // Red
        ]
    }

    // MARK: - Completed Meetings Card

    private var completedMeetingsCard: some View {
        let completed = viewModel.allMeetings.filter { !$0.isOpen }
        return VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(Color(hex: "10B981"))

                Text("Completed Meetings")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(completed.count)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(Color(hex: "10B981"))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: "10B981").opacity(0.15))
                    .cornerRadius(6)
            }

            if completed.isEmpty {
                EmptyStateView(
                    message: "No completed meetings yet",
                    icon: "checkmark.circle"
                )
            } else {
                VStack(spacing: AngelaTheme.spacing) {
                    ForEach(completed) { meeting in
                        MeetingCard(
                            meeting: meeting,
                            isExpanded: viewModel.expandedMeetingId == meeting.id
                        ) {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                if viewModel.expandedMeetingId == meeting.id {
                                    viewModel.expandedMeetingId = nil
                                } else {
                                    viewModel.expandedMeetingId = meeting.id
                                }
                            }
                        }
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Calendar Day Model

struct CalendarDay: Identifiable {
    let id = UUID()
    let dayNumber: Int
    let isCurrentMonth: Bool
    let isToday: Bool
    let meetingCount: Int
    let siteVisitCount: Int
}

// MARK: - View Model

@MainActor
class ThingsOverviewViewModel: ObservableObject {
    @Published var stats: MeetingStats?
    @Published var allMeetings: [MeetingNote] = []
    @Published var upcomingMeetings: [MeetingNote] = []
    @Published var projectBreakdown: [ProjectMeetingBreakdown] = []
    @Published var expandedMeetingId: UUID?
    @Published var isLoading = false
    @Published var currentMonth: Date = Date()

    var monthYearString: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM yyyy"
        return formatter.string(from: currentMonth)
    }

    func previousMonth() {
        currentMonth = Calendar.current.date(byAdding: .month, value: -1, to: currentMonth) ?? currentMonth
    }

    func nextMonth() {
        currentMonth = Calendar.current.date(byAdding: .month, value: 1, to: currentMonth) ?? currentMonth
    }

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        async let fetchedStats = try? databaseService.fetchMeetingStats()
        async let fetchedMeetings = try? databaseService.fetchMeetings()
        async let fetchedUpcoming = try? databaseService.fetchUpcomingMeetings()
        async let fetchedBreakdown = try? databaseService.fetchMeetingProjectBreakdown()

        stats = await fetchedStats
        allMeetings = await fetchedMeetings ?? []
        upcomingMeetings = await fetchedUpcoming ?? []
        projectBreakdown = await fetchedBreakdown ?? []

        isLoading = false
    }

    func calendarDays() -> [CalendarDay] {
        let calendar = Calendar.current
        let today = Date()

        guard let monthInterval = calendar.dateInterval(of: .month, for: currentMonth),
              let firstWeekday = calendar.dateComponents([.weekday], from: monthInterval.start).weekday,
              let daysInMonth = calendar.range(of: .day, in: .month, for: currentMonth)?.count else {
            return []
        }

        // Build meeting lookup for this month
        var meetingDays: [Int: (meetings: Int, siteVisits: Int)] = [:]
        let currentYear = calendar.component(.year, from: currentMonth)
        let currentMonthNum = calendar.component(.month, from: currentMonth)

        for meeting in allMeetings {
            guard let meetingDate = meeting.meetingDate else { continue }
            let comps = calendar.dateComponents([.year, .month, .day], from: meetingDate)
            if comps.year == currentYear && comps.month == currentMonthNum, let day = comps.day {
                var existing = meetingDays[day] ?? (0, 0)
                if meeting.isSiteVisit {
                    existing.siteVisits += 1
                } else {
                    existing.meetings += 1
                }
                meetingDays[day] = existing
            }
        }

        var days: [CalendarDay] = []

        // Leading empty days (Sunday = 1)
        let leadingBlanks = firstWeekday - 1
        for _ in 0..<leadingBlanks {
            days.append(CalendarDay(dayNumber: 0, isCurrentMonth: false, isToday: false, meetingCount: 0, siteVisitCount: 0))
        }

        // Actual days
        let todayComps = calendar.dateComponents([.year, .month, .day], from: today)
        for day in 1...daysInMonth {
            let isToday = todayComps.year == currentYear && todayComps.month == currentMonthNum && todayComps.day == day
            let counts = meetingDays[day] ?? (0, 0)
            days.append(CalendarDay(
                dayNumber: day,
                isCurrentMonth: true,
                isToday: isToday,
                meetingCount: counts.meetings,
                siteVisitCount: counts.siteVisits
            ))
        }

        // Trailing blanks to fill last row
        let remainder = days.count % 7
        if remainder > 0 {
            for _ in 0..<(7 - remainder) {
                days.append(CalendarDay(dayNumber: 0, isCurrentMonth: false, isToday: false, meetingCount: 0, siteVisitCount: 0))
            }
        }

        return days
    }
}
