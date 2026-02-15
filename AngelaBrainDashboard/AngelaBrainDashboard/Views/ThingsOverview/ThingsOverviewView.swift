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
    @State private var showAddMeetingSheet = false
    @State private var meetingToEdit: MeetingNote?
    @State private var meetingToDelete: MeetingNote?
    @State private var showDeleteConfirm = false
    @State private var completedPage = 0
    private let completedPerPage = 5

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                header
                if let stats = viewModel.stats {
                    statsRow(stats)
                }
                calendarCard
                if !viewModel.openActionItems.isEmpty {
                    openActionItemsCard
                }
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
        .sheet(isPresented: $showAddMeetingSheet) {
            AddMeetingSheet(databaseService: databaseService) {
                Task { await viewModel.loadData(databaseService: databaseService) }
            }
        }
        .sheet(item: $meetingToEdit) { meeting in
            EditMeetingSheet(databaseService: databaseService, meeting: meeting) {
                Task { await viewModel.loadData(databaseService: databaseService) }
            }
        }
        .alert("Delete Meeting?", isPresented: $showDeleteConfirm) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                if let meeting = meetingToDelete {
                    Task {
                        try? await databaseService.deleteMeeting(meetingId: meeting.id.uuidString)
                        await viewModel.loadData(databaseService: databaseService)
                    }
                }
            }
        } message: {
            Text("Are you sure? This cannot be undone.")
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Things")
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

            Button {
                showAddMeetingSheet = true
            } label: {
                Image(systemName: "plus")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
                    .frame(width: 32, height: 32)
                    .background(AngelaTheme.primaryPurple)
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .help("Add meeting")

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
            statCard(title: "Open", value: "\(stats.openMeetings)", icon: "exclamationmark.circle.fill", color: "F59E0B")
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
            HStack(spacing: 10) {
                calendarLegendItem(icon: "person.2.fill", color: "3B82F6", label: "Meeting")
                calendarLegendItem(icon: "mappin.circle.fill", color: "10B981", label: "Site Visit")
                calendarLegendItem(icon: "gearshape.fill", color: "F59E0B", label: "Testing")
                calendarLegendItem(icon: "crown.fill", color: "8B5CF6", label: "BOD")
                HStack(spacing: 3) {
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
                    .font(.system(size: 13, weight: day.isToday ? .bold : .regular))
                    .foregroundColor(
                        day.isToday ? AngelaTheme.primaryPurple :
                        day.isCurrentMonth ? AngelaTheme.textPrimary : AngelaTheme.textTertiary.opacity(0.5)
                    )

                // Meeting type icons - bigger & brighter
                if day.hasMeetings && day.isCurrentMonth {
                    HStack(spacing: 3) {
                        if day.meetingCount > 0 {
                            Image(systemName: "person.2.fill")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(Color(hex: "60A5FA"))
                        }
                        if day.siteVisitCount > 0 {
                            Image(systemName: "mappin.circle.fill")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(Color(hex: "34D399"))
                        }
                        if day.testingCount > 0 {
                            Image(systemName: "gearshape.fill")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(Color(hex: "FBBF24"))
                        }
                        if day.bodCount > 0 {
                            Image(systemName: "crown.fill")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(Color(hex: "A78BFA"))
                        }
                    }
                    .frame(height: 14)
                } else {
                    Spacer().frame(height: 14)
                }
            } else {
                Text("")
                    .font(.system(size: 13))
                    .frame(height: 16)
                Spacer().frame(height: 14)
            }
        }
        .frame(height: 40)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(calendarCellBackground(day))
        )
        .overlay(
            day.isToday ?
                AnyView(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(Color(hex: "A78BFA").opacity(0.7), lineWidth: 2)
                ) :
                AnyView(EmptyView())
        )
    }

    private func calendarCellBackground(_ day: CalendarDay) -> Color {
        if day.isToday {
            return Color(hex: "9333EA").opacity(0.2)
        } else if day.hasMeetings && day.isCurrentMonth {
            return Color(hex: day.dominantColor).opacity(0.15)
        }
        return Color.clear
    }

    @ViewBuilder
    private func calendarLegendItem(icon: String, color: String, label: String) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(Color(hex: color))
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }

    // MARK: - Open Action Items Card

    private var openActionItemsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "checklist")
                    .foregroundColor(Color(hex: "F59E0B"))

                Text("Open Action Items")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(viewModel.openActionItems.count)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(Color(hex: "F59E0B"))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: "F59E0B").opacity(0.15))
                    .cornerRadius(6)
            }

            VStack(spacing: AngelaTheme.smallSpacing) {
                ForEach(viewModel.openActionItems.prefix(8)) { item in
                    ActionItemRow(
                        action: item,
                        onToggle: {
                            Task {
                                _ = try? await databaseService.toggleActionItem(actionId: item.id.uuidString)
                                await viewModel.loadData(databaseService: databaseService)
                            }
                        },
                        showMeetingTitle: true
                    )
                }

                if viewModel.openActionItems.count > 8 {
                    Text("+\(viewModel.openActionItems.count - 8) more")
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .frame(maxWidth: .infinity, alignment: .center)
                        .padding(.top, 4)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
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
                        isExpanded: viewModel.expandedMeetingId == meeting.id,
                        onTap: {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                if viewModel.expandedMeetingId == meeting.id {
                                    viewModel.expandedMeetingId = nil
                                } else {
                                    viewModel.expandedMeetingId = meeting.id
                                }
                            }
                        },
                        onEdit: {
                            meetingToEdit = meeting
                        },
                        onDelete: {
                            meetingToDelete = meeting
                            showDeleteConfirm = true
                        },
                        onToggleStatus: {
                            Task { await viewModel.toggleMeetingStatus(meeting: meeting, databaseService: databaseService) }
                        },
                        databaseService: databaseService,
                        onActionChanged: {
                            Task { await viewModel.loadData(databaseService: databaseService) }
                        }
                    )
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
        let totalPages = max(1, Int(ceil(Double(completed.count) / Double(completedPerPage))))
        let safePage = min(completedPage, totalPages - 1)
        let startIdx = safePage * completedPerPage
        let endIdx = min(startIdx + completedPerPage, completed.count)
        let pageItems = completed.isEmpty ? [] : Array(completed[startIdx..<endIdx])

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
                    ForEach(pageItems) { meeting in
                        MeetingCard(
                            meeting: meeting,
                            isExpanded: viewModel.expandedMeetingId == meeting.id,
                            onTap: {
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    if viewModel.expandedMeetingId == meeting.id {
                                        viewModel.expandedMeetingId = nil
                                    } else {
                                        viewModel.expandedMeetingId = meeting.id
                                    }
                                }
                            },
                            onEdit: {
                                meetingToEdit = meeting
                            },
                            onDelete: {
                                meetingToDelete = meeting
                                showDeleteConfirm = true
                            },
                            onToggleStatus: {
                                Task { await viewModel.toggleMeetingStatus(meeting: meeting, databaseService: databaseService) }
                            },
                            databaseService: databaseService,
                            onActionChanged: {
                                Task { await viewModel.loadData(databaseService: databaseService) }
                            }
                        )
                    }
                }

                // Pagination
                if totalPages > 1 {
                    HStack(spacing: 6) {
                        Button {
                            withAnimation { completedPage = max(0, safePage - 1) }
                        } label: {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(safePage > 0 ? AngelaTheme.textSecondary : AngelaTheme.textSecondary.opacity(0.3))
                        }
                        .disabled(safePage == 0)
                        .buttonStyle(.plain)

                        ForEach(0..<totalPages, id: \.self) { page in
                            Button {
                                withAnimation { completedPage = page }
                            } label: {
                                Text("\(page + 1)")
                                    .font(.system(size: 11, weight: page == safePage ? .bold : .medium))
                                    .foregroundColor(page == safePage ? .white : AngelaTheme.textSecondary)
                                    .frame(width: 28, height: 28)
                                    .background(
                                        page == safePage
                                            ? Color(hex: "10B981").opacity(0.8)
                                            : Color.white.opacity(0.05)
                                    )
                                    .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                        }

                        Button {
                            withAnimation { completedPage = min(totalPages - 1, safePage + 1) }
                        } label: {
                            Image(systemName: "chevron.right")
                                .font(.system(size: 11, weight: .semibold))
                                .foregroundColor(safePage < totalPages - 1 ? AngelaTheme.textSecondary : AngelaTheme.textSecondary.opacity(0.3))
                        }
                        .disabled(safePage >= totalPages - 1)
                        .buttonStyle(.plain)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top, 4)
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
    let meetingCount: Int        // standard meetings
    let siteVisitCount: Int      // site visits
    let testingCount: Int        // testing sessions
    let bodCount: Int            // BOD meetings

    var hasMeetings: Bool {
        meetingCount + siteVisitCount + testingCount + bodCount > 0
    }

    var totalMeetings: Int {
        meetingCount + siteVisitCount + testingCount + bodCount
    }

    /// Color of the highest-priority meeting type on this day
    var dominantColor: String {
        if bodCount > 0 { return "8B5CF6" }
        if testingCount > 0 { return "F59E0B" }
        if siteVisitCount > 0 { return "10B981" }
        return "3B82F6"
    }
}

// MARK: - View Model

@MainActor
class ThingsOverviewViewModel: ObservableObject {
    @Published var stats: MeetingStats?
    @Published var allMeetings: [MeetingNote] = []
    @Published var upcomingMeetings: [MeetingNote] = []
    @Published var openActionItems: [MeetingActionItem] = []
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
        async let fetchedActions = try? databaseService.fetchOpenActionItems()
        async let fetchedBreakdown = try? databaseService.fetchMeetingProjectBreakdown()

        stats = await fetchedStats
        allMeetings = await fetchedMeetings ?? []
        upcomingMeetings = await fetchedUpcoming ?? []
        openActionItems = await fetchedActions ?? []
        projectBreakdown = await fetchedBreakdown ?? []

        isLoading = false
    }

    func toggleMeetingStatus(meeting: MeetingNote, databaseService: DatabaseService) async {
        let newStatus = meeting.isOpen ? "completed" : "open"
        var request = MeetingUpdateRequest()
        request.things3Status = newStatus
        _ = try? await databaseService.updateMeeting(meetingId: meeting.id.uuidString, request)
        await loadData(databaseService: databaseService)
    }

    func calendarDays() -> [CalendarDay] {
        let calendar = Calendar.current
        let today = Date()

        guard let monthInterval = calendar.dateInterval(of: .month, for: currentMonth),
              let firstWeekday = calendar.dateComponents([.weekday], from: monthInterval.start).weekday,
              let daysInMonth = calendar.range(of: .day, in: .month, for: currentMonth)?.count else {
            return []
        }

        // Build meeting lookup for this month (4 types)
        var meetingDays: [Int: (standard: Int, siteVisits: Int, testing: Int, bod: Int)] = [:]
        let currentYear = calendar.component(.year, from: currentMonth)
        let currentMonthNum = calendar.component(.month, from: currentMonth)

        for meeting in allMeetings {
            guard let meetingDate = meeting.meetingDate else { continue }
            let comps = calendar.dateComponents([.year, .month, .day], from: meetingDate)
            if comps.year == currentYear && comps.month == currentMonthNum, let day = comps.day {
                var existing = meetingDays[day] ?? (0, 0, 0, 0)
                switch meeting.meetingType {
                case "site_visit":
                    existing.siteVisits += 1
                case "testing":
                    existing.testing += 1
                case "bod":
                    existing.bod += 1
                default:
                    existing.standard += 1
                }
                meetingDays[day] = existing
            }
        }

        var days: [CalendarDay] = []

        // Leading empty days (Sunday = 1)
        let leadingBlanks = firstWeekday - 1
        for _ in 0..<leadingBlanks {
            days.append(CalendarDay(dayNumber: 0, isCurrentMonth: false, isToday: false, meetingCount: 0, siteVisitCount: 0, testingCount: 0, bodCount: 0))
        }

        // Actual days
        let todayComps = calendar.dateComponents([.year, .month, .day], from: today)
        for day in 1...daysInMonth {
            let isToday = todayComps.year == currentYear && todayComps.month == currentMonthNum && todayComps.day == day
            let counts = meetingDays[day] ?? (0, 0, 0, 0)
            days.append(CalendarDay(
                dayNumber: day,
                isCurrentMonth: true,
                isToday: isToday,
                meetingCount: counts.standard,
                siteVisitCount: counts.siteVisits,
                testingCount: counts.testing,
                bodCount: counts.bod
            ))
        }

        // Trailing blanks to fill last row
        let remainder = days.count % 7
        if remainder > 0 {
            for _ in 0..<(7 - remainder) {
                days.append(CalendarDay(dayNumber: 0, isCurrentMonth: false, isToday: false, meetingCount: 0, siteVisitCount: 0, testingCount: 0, bodCount: 0))
            }
        }

        return days
    }
}

// AddMeetingSheet and EditMeetingSheet are in separate files:
// - AddMeetingSheet.swift
// - EditMeetingSheet.swift
// - MeetingFormComponents.swift (shared components)
