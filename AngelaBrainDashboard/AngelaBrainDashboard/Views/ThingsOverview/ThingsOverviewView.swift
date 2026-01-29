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
                            }
                        )
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

// MARK: - Add Meeting Sheet

struct AddMeetingSheet: View {
    let databaseService: DatabaseService
    let onCreated: () -> Void
    @Environment(\.dismiss) private var dismiss

    // Form State
    @State private var title = ""
    @State private var meetingType: MeetingType = .standard
    @State private var selectedDate = Date()
    @State private var startHour = 9
    @State private var startMinute = 0
    @State private var endHour = 10
    @State private var endMinute = 0
    @State private var location = ""
    @State private var projectName = ""
    @State private var attendeesText = ""

    @State private var isCreating = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSuccess = false

    // Location suggestions
    @State private var savedLocations: [String] = []
    @State private var showLocationSuggestions = false

    enum MeetingType: String, CaseIterable {
        case standard = "standard"
        case siteVisit = "site_visit"
        case testing = "testing"
        case bod = "bod"

        var displayName: String {
            switch self {
            case .standard: return "Standard"
            case .siteVisit: return "Site Visit"
            case .testing: return "Testing"
            case .bod: return "BOD"
            }
        }

        var icon: String {
            switch self {
            case .standard: return "person.3.fill"
            case .siteVisit: return "building.2.fill"
            case .testing: return "checkmark.seal.fill"
            case .bod: return "crown.fill"
            }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Create Meeting")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(width: 28, height: 28)
                        .background(AngelaTheme.backgroundLight)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding()
            .background(AngelaTheme.backgroundLight)

            Divider()

            // Form
            ScrollView {
                VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
                    // Title
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Meeting Title", systemImage: "doc.text.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        TextField("e.g. SRT + CI Meeting", text: $title)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Meeting Type
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Meeting Type", systemImage: "tag.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        HStack(spacing: 8) {
                            ForEach(MeetingType.allCases, id: \.self) { type in
                                Button {
                                    meetingType = type
                                } label: {
                                    HStack(spacing: 4) {
                                        Image(systemName: type.icon)
                                            .font(.system(size: 10))
                                        Text(type.displayName)
                                            .font(.system(size: 11, weight: .medium))
                                    }
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(meetingType == type ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                                    .foregroundColor(meetingType == type ? .white : AngelaTheme.textPrimary)
                                    .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Date
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Date", systemImage: "calendar")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        DatePicker("", selection: $selectedDate, displayedComponents: .date)
                            .datePickerStyle(.compact)
                            .labelsHidden()

                        // Thai day display
                        Text(thaiDateString)
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }

                    // Time
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Time", systemImage: "clock.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        HStack(spacing: 8) {
                            // Start time
                            HStack(spacing: 4) {
                                Picker("", selection: $startHour) {
                                    ForEach(0..<24, id: \.self) { hour in
                                        Text(String(format: "%02d", hour)).tag(hour)
                                    }
                                }
                                .pickerStyle(.menu)
                                .frame(width: 60)

                                Text(":")
                                    .foregroundColor(AngelaTheme.textSecondary)

                                Picker("", selection: $startMinute) {
                                    ForEach([0, 15, 30, 45], id: \.self) { min in
                                        Text(String(format: "%02d", min)).tag(min)
                                    }
                                }
                                .pickerStyle(.menu)
                                .frame(width: 60)
                            }

                            Text("to")
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)

                            // End time
                            HStack(spacing: 4) {
                                Picker("", selection: $endHour) {
                                    ForEach(0..<24, id: \.self) { hour in
                                        Text(String(format: "%02d", hour)).tag(hour)
                                    }
                                }
                                .pickerStyle(.menu)
                                .frame(width: 60)

                                Text(":")
                                    .foregroundColor(AngelaTheme.textSecondary)

                                Picker("", selection: $endMinute) {
                                    ForEach([0, 15, 30, 45], id: \.self) { min in
                                        Text(String(format: "%02d", min)).tag(min)
                                    }
                                }
                                .pickerStyle(.menu)
                                .frame(width: 60)
                            }
                        }
                    }

                    // Location (with suggestions dropdown)
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Location", systemImage: "mappin.circle.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        // ComboBox style: TextField + Dropdown
                        VStack(spacing: 0) {
                            HStack {
                                TextField("e.g. การรถไฟแห่งประเทศไทย", text: $location)
                                    .textFieldStyle(.plain)

                                if !savedLocations.isEmpty {
                                    Button {
                                        showLocationSuggestions.toggle()
                                    } label: {
                                        Image(systemName: showLocationSuggestions ? "chevron.up" : "chevron.down")
                                            .font(.system(size: 10, weight: .semibold))
                                            .foregroundColor(AngelaTheme.textSecondary)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(showLocationSuggestions ? 8 : 8)

                            // Dropdown suggestions
                            if showLocationSuggestions && !savedLocations.isEmpty {
                                VStack(spacing: 0) {
                                    ForEach(filteredLocations, id: \.self) { loc in
                                        Button {
                                            location = loc
                                            showLocationSuggestions = false
                                        } label: {
                                            HStack {
                                                Image(systemName: "mappin")
                                                    .font(.system(size: 10))
                                                    .foregroundColor(AngelaTheme.primaryPurple)
                                                Text(loc)
                                                    .font(.system(size: 12))
                                                    .foregroundColor(AngelaTheme.textPrimary)
                                                Spacer()
                                            }
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 8)
                                            .background(Color.clear)
                                        }
                                        .buttonStyle(.plain)

                                        if loc != filteredLocations.last {
                                            Divider().opacity(0.3)
                                        }
                                    }
                                }
                                .background(AngelaTheme.backgroundLight.opacity(0.8))
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
                                )
                            }
                        }
                    }

                    // Project (Optional)
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Project (Optional)", systemImage: "folder.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        TextField("e.g. EWG, WTU", text: $projectName)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Attendees (Optional)
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Attendees (Optional)", systemImage: "person.2.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        TextField("Name1, Name2, Name3", text: $attendeesText)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Template Preview
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Template Sections", systemImage: "doc.badge.gearshape.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        HStack(spacing: 4) {
                            ForEach(templateSections, id: \.self) { section in
                                Text(section)
                                    .font(.system(size: 9))
                                    .foregroundColor(AngelaTheme.primaryPurple)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(AngelaTheme.primaryPurple.opacity(0.12))
                                    .cornerRadius(4)
                            }
                        }
                    }
                }
                .padding()
            }

            Divider()

            // Footer
            HStack {
                Spacer()

                Button {
                    Task {
                        await createMeeting()
                    }
                } label: {
                    HStack(spacing: 6) {
                        if isCreating {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "checkmark")
                        }
                        Text("Create Meeting")
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(canCreate ? AngelaTheme.primaryPurple : Color.gray)
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
                .disabled(!canCreate || isCreating)
            }
            .padding()
            .background(AngelaTheme.backgroundLight)
        }
        .frame(width: 500, height: 650)
        .background(AngelaTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
        .alert("Meeting Created", isPresented: $showSuccess) {
            Button("OK") {
                dismiss()
                onCreated()
            }
        } message: {
            Text("Meeting has been created in Things3 and database.")
        }
        .task {
            await loadLocations()
        }
    }

    // MARK: - Computed Properties

    private var canCreate: Bool {
        !title.isEmpty && !location.isEmpty
    }

    private var thaiDateString: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.calendar = Calendar(identifier: .buddhist)
        formatter.dateFormat = "วันEEEEที่ d MMMM yyyy"
        return formatter.string(from: selectedDate)
    }

    private var templateSections: [String] {
        switch meetingType {
        case .standard:
            return ["วาระ", "ผู้เข้าร่วม", "Key Points", "Next Steps"]
        case .siteVisit:
            return ["Morning", "Afternoon", "Observations", "Next Steps"]
        case .testing:
            return ["Test Scope", "Results", "Issues", "Next Steps"]
        case .bod:
            return ["Agenda", "Resolutions", "Actions", "Notes"]
        }
    }

    private var filteredLocations: [String] {
        if location.isEmpty {
            return savedLocations
        }
        let filtered = savedLocations.filter { $0.localizedCaseInsensitiveContains(location) }
        return filtered.isEmpty ? savedLocations : filtered
    }

    // MARK: - Actions

    private func loadLocations() async {
        do {
            savedLocations = try await databaseService.fetchMeetingLocations()
        } catch {
            print("Failed to load locations: \(error)")
        }
    }

    private func createMeeting() async {
        isCreating = true

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")
        let dateStr = dateFormatter.string(from: selectedDate)

        let startStr = String(format: "%02d:%02d", startHour, startMinute)
        let endStr = String(format: "%02d:%02d", endHour, endMinute)

        // Parse attendees
        let attendees: [String]? = attendeesText.isEmpty ? nil : attendeesText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        let request = MeetingCreateRequest(
            title: title,
            location: location,
            meetingDate: dateStr,
            startTime: startStr,
            endTime: endStr,
            meetingType: meetingType.rawValue,
            attendees: attendees,
            projectName: projectName.isEmpty ? nil : projectName
        )

        do {
            let response = try await databaseService.createMeeting(request)
            isCreating = false

            if response.success {
                showSuccess = true
            } else {
                errorMessage = response.error ?? "Unknown error"
                showError = true
            }
        } catch {
            isCreating = false
            errorMessage = error.localizedDescription
            showError = true
        }
    }
}

// MARK: - Edit Meeting Sheet

struct EditMeetingSheet: View {
    let databaseService: DatabaseService
    let meeting: MeetingNote
    let onUpdated: () -> Void
    @Environment(\.dismiss) private var dismiss

    @State private var title: String
    @State private var meetingType: AddMeetingSheet.MeetingType
    @State private var selectedDate: Date
    @State private var startHour: Int
    @State private var startMinute: Int
    @State private var endHour: Int
    @State private var endMinute: Int
    @State private var location: String
    @State private var projectName: String
    @State private var attendeesText: String
    @State private var status: String

    @State private var isSaving = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSuccess = false

    @State private var savedLocations: [String] = []
    @State private var showLocationSuggestions = false

    init(databaseService: DatabaseService, meeting: MeetingNote, onUpdated: @escaping () -> Void) {
        self.databaseService = databaseService
        self.meeting = meeting
        self.onUpdated = onUpdated

        // Pre-fill from meeting
        _title = State(initialValue: meeting.title)
        _meetingType = State(initialValue: meeting.isSiteVisit ? .siteVisit : .standard)
        _selectedDate = State(initialValue: meeting.meetingDate ?? Date())
        _location = State(initialValue: meeting.location ?? "")
        _projectName = State(initialValue: meeting.projectName ?? "")
        _attendeesText = State(initialValue: meeting.attendees?.joined(separator: ", ") ?? "")
        _status = State(initialValue: meeting.things3Status)

        // Parse time range "HH:MM-HH:MM"
        if let timeRange = meeting.timeRange {
            let parts = timeRange.split(separator: "-")
            if parts.count == 2 {
                let startParts = parts[0].split(separator: ":")
                let endParts = parts[1].split(separator: ":")
                _startHour = State(initialValue: Int(startParts.first ?? "9") ?? 9)
                _startMinute = State(initialValue: Int(startParts.last ?? "0") ?? 0)
                _endHour = State(initialValue: Int(endParts.first ?? "10") ?? 10)
                _endMinute = State(initialValue: Int(endParts.last ?? "0") ?? 0)
            } else {
                _startHour = State(initialValue: 9)
                _startMinute = State(initialValue: 0)
                _endHour = State(initialValue: 10)
                _endMinute = State(initialValue: 0)
            }
        } else {
            _startHour = State(initialValue: 9)
            _startMinute = State(initialValue: 0)
            _endHour = State(initialValue: 10)
            _endMinute = State(initialValue: 0)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Edit Meeting")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button { dismiss() } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(width: 28, height: 28)
                        .background(AngelaTheme.backgroundLight)
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
            .padding()
            .background(AngelaTheme.backgroundLight)

            Divider()

            // Form
            ScrollView {
                VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
                    // Title
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Meeting Title", systemImage: "doc.text.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        TextField("Title", text: $title)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Status
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Status", systemImage: "circle.badge.checkmark.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        HStack(spacing: 8) {
                            ForEach(["open", "completed"], id: \.self) { s in
                                Button {
                                    status = s
                                } label: {
                                    HStack(spacing: 4) {
                                        Image(systemName: s == "open" ? "circle" : "checkmark.circle.fill")
                                            .font(.system(size: 10))
                                        Text(s == "open" ? "Open" : "Completed")
                                            .font(.system(size: 11, weight: .medium))
                                    }
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(status == s ? (s == "open" ? Color(hex: "3B82F6") : Color(hex: "10B981")) : AngelaTheme.backgroundLight)
                                    .foregroundColor(status == s ? .white : AngelaTheme.textPrimary)
                                    .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Meeting Type
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Meeting Type", systemImage: "tag.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        HStack(spacing: 8) {
                            ForEach(AddMeetingSheet.MeetingType.allCases, id: \.self) { type in
                                Button {
                                    meetingType = type
                                } label: {
                                    HStack(spacing: 4) {
                                        Image(systemName: type.icon)
                                            .font(.system(size: 10))
                                        Text(type.displayName)
                                            .font(.system(size: 11, weight: .medium))
                                    }
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(meetingType == type ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                                    .foregroundColor(meetingType == type ? .white : AngelaTheme.textPrimary)
                                    .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Date
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Date", systemImage: "calendar")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        DatePicker("", selection: $selectedDate, displayedComponents: .date)
                            .datePickerStyle(.compact)
                            .labelsHidden()

                        Text(thaiDateString)
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }

                    // Time
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Time", systemImage: "clock.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        HStack(spacing: 8) {
                            HStack(spacing: 4) {
                                Picker("", selection: $startHour) {
                                    ForEach(0..<24, id: \.self) { h in Text(String(format: "%02d", h)).tag(h) }
                                }
                                .pickerStyle(.menu).frame(width: 60)
                                Text(":").foregroundColor(AngelaTheme.textSecondary)
                                Picker("", selection: $startMinute) {
                                    ForEach([0, 15, 30, 45], id: \.self) { m in Text(String(format: "%02d", m)).tag(m) }
                                }
                                .pickerStyle(.menu).frame(width: 60)
                            }
                            Text("to").font(AngelaTheme.caption()).foregroundColor(AngelaTheme.textSecondary)
                            HStack(spacing: 4) {
                                Picker("", selection: $endHour) {
                                    ForEach(0..<24, id: \.self) { h in Text(String(format: "%02d", h)).tag(h) }
                                }
                                .pickerStyle(.menu).frame(width: 60)
                                Text(":").foregroundColor(AngelaTheme.textSecondary)
                                Picker("", selection: $endMinute) {
                                    ForEach([0, 15, 30, 45], id: \.self) { m in Text(String(format: "%02d", m)).tag(m) }
                                }
                                .pickerStyle(.menu).frame(width: 60)
                            }
                        }
                    }

                    // Location with suggestions
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Location", systemImage: "mappin.circle.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        VStack(spacing: 0) {
                            HStack {
                                TextField("Location", text: $location)
                                    .textFieldStyle(.plain)
                                if !savedLocations.isEmpty {
                                    Button { showLocationSuggestions.toggle() } label: {
                                        Image(systemName: showLocationSuggestions ? "chevron.up" : "chevron.down")
                                            .font(.system(size: 10, weight: .semibold))
                                            .foregroundColor(AngelaTheme.textSecondary)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)

                            if showLocationSuggestions && !savedLocations.isEmpty {
                                VStack(spacing: 0) {
                                    ForEach(filteredLocations, id: \.self) { loc in
                                        Button {
                                            location = loc
                                            showLocationSuggestions = false
                                        } label: {
                                            HStack {
                                                Image(systemName: "mappin")
                                                    .font(.system(size: 10))
                                                    .foregroundColor(AngelaTheme.primaryPurple)
                                                Text(loc)
                                                    .font(.system(size: 12))
                                                    .foregroundColor(AngelaTheme.textPrimary)
                                                Spacer()
                                            }
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 8)
                                        }
                                        .buttonStyle(.plain)
                                        if loc != filteredLocations.last { Divider().opacity(0.3) }
                                    }
                                }
                                .background(AngelaTheme.backgroundLight.opacity(0.8))
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
                                )
                            }
                        }
                    }

                    // Project
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Project (Optional)", systemImage: "folder.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        TextField("e.g. EWG, WTU", text: $projectName)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Attendees
                    VStack(alignment: .leading, spacing: 4) {
                        Label("Attendees (Optional)", systemImage: "person.2.fill")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        TextField("Name1, Name2, Name3", text: $attendeesText)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }
                }
                .padding()
            }

            Divider()

            // Footer
            HStack {
                Spacer()

                Button {
                    Task { await saveMeeting() }
                } label: {
                    HStack(spacing: 6) {
                        if isSaving {
                            ProgressView().scaleEffect(0.7)
                        } else {
                            Image(systemName: "checkmark")
                        }
                        Text("Save Changes")
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(canSave ? AngelaTheme.primaryPurple : Color.gray)
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
                .disabled(!canSave || isSaving)
            }
            .padding()
            .background(AngelaTheme.backgroundLight)
        }
        .frame(width: 500, height: 650)
        .background(AngelaTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
        .alert("Meeting Updated", isPresented: $showSuccess) {
            Button("OK") { dismiss(); onUpdated() }
        } message: {
            Text("Meeting has been updated.")
        }
        .task { await loadLocations() }
    }

    // MARK: - Computed Properties

    private var canSave: Bool {
        !title.isEmpty && !location.isEmpty
    }

    private var thaiDateString: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.calendar = Calendar(identifier: .buddhist)
        formatter.dateFormat = "วันEEEEที่ d MMMM yyyy"
        return formatter.string(from: selectedDate)
    }

    private var filteredLocations: [String] {
        if location.isEmpty { return savedLocations }
        let filtered = savedLocations.filter { $0.localizedCaseInsensitiveContains(location) }
        return filtered.isEmpty ? savedLocations : filtered
    }

    // MARK: - Actions

    private func loadLocations() async {
        savedLocations = (try? await databaseService.fetchMeetingLocations()) ?? []
    }

    private func saveMeeting() async {
        isSaving = true

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")

        let attendees: [String]? = attendeesText.isEmpty ? nil : attendeesText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        let request = MeetingUpdateRequest(
            title: title,
            location: location,
            meetingDate: dateFormatter.string(from: selectedDate),
            startTime: String(format: "%02d:%02d", startHour, startMinute),
            endTime: String(format: "%02d:%02d", endHour, endMinute),
            meetingType: meetingType.rawValue,
            attendees: attendees,
            projectName: projectName.isEmpty ? nil : projectName,
            things3Status: status
        )

        do {
            let response = try await databaseService.updateMeeting(meetingId: meeting.id.uuidString, request)
            isSaving = false
            if response.success {
                showSuccess = true
            } else {
                errorMessage = response.error ?? "Unknown error"
                showError = true
            }
        } catch {
            isSaving = false
            errorMessage = error.localizedDescription
            showError = true
        }
    }
}
