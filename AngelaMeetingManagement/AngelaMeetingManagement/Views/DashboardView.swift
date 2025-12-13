//
//  DashboardView.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  ClickUp-inspired Dashboard with Analytics & Insights
//

import SwiftUI
import Charts

struct DashboardView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @ObservedObject var viewModel: MeetingListViewModel

    // Dashboard stats
    @State private var totalMeetings = 0
    @State private var scheduledMeetings = 0
    @State private var completedMeetings = 0
    @State private var inProgressMeetings = 0
    @State private var upcomingMeetings: [Meeting] = []
    @State private var recentMeetings: [Meeting] = []
    @State private var priorityBreakdown: [String: Int] = [:]
    @State private var statusBreakdown: [String: Int] = [:]

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.spacingXL) {
                // Page Header
                headerSection

                // Overview Cards Row
                overviewCardsRow

                // Charts Section
                HStack(alignment: .top, spacing: AngelaTheme.spacingL) {
                    // Status Distribution Chart
                    statusChartCard

                    // Priority Distribution Chart
                    priorityChartCard
                }

                // Upcoming & Recent Section
                HStack(alignment: .top, spacing: AngelaTheme.spacingL) {
                    // Upcoming Meetings
                    upcomingMeetingsCard

                    // Recent Activity
                    recentActivityCard
                }

                Spacer(minLength: AngelaTheme.spacingXL)
            }
            .padding(AngelaTheme.spacingXL)
        }
        .background(AngelaTheme.background)
        .task {
            await loadDashboardData()
        }
    }

    // MARK: - Header Section
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text("Dashboard")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Overview of your meetings and activities")
                    .font(.system(size: 15))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Refresh Button
            Button(action: {
                Task {
                    await loadDashboardData()
                }
            }) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                    Text("Refresh")
                }
            }
            .buttonStyle(AngelaSecondaryButtonStyle())
        }
    }

    // MARK: - Overview Cards Row
    private var overviewCardsRow: some View {
        HStack(spacing: AngelaTheme.spacingL) {
            StatCard(
                title: "Total Meetings",
                value: "\(totalMeetings)",
                icon: "calendar",
                color: AngelaTheme.primaryPurple,
                trend: nil
            )

            StatCard(
                title: "Scheduled",
                value: "\(scheduledMeetings)",
                icon: "clock",
                color: .blue,
                trend: nil
            )

            StatCard(
                title: "In Progress",
                value: "\(inProgressMeetings)",
                icon: "play.circle.fill",
                color: .orange,
                trend: nil
            )

            StatCard(
                title: "Completed",
                value: "\(completedMeetings)",
                icon: "checkmark.circle.fill",
                color: .green,
                trend: nil
            )
        }
    }

    // MARK: - Status Chart Card
    private var statusChartCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingL) {
            HStack {
                Image(systemName: "chart.pie.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 18))

                Text("Status Distribution")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()
            }

            if !statusBreakdown.isEmpty {
                Chart {
                    ForEach(Array(statusBreakdown.keys.sorted()), id: \.self) { status in
                        SectorMark(
                            angle: .value("Count", statusBreakdown[status] ?? 0),
                            innerRadius: .ratio(0.5),
                            angularInset: 2
                        )
                        .foregroundStyle(by: .value("Status", status.capitalized))
                        .annotation(position: .overlay) {
                            Text("\(statusBreakdown[status] ?? 0)")
                                .font(.system(size: 12, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                }
                .chartForegroundStyleScale([
                    "Scheduled": .blue,
                    "In Progress": .orange,
                    "Completed": .green,
                    "Cancelled": .red
                ])
                .frame(height: 220)

                // Legend
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(Array(statusBreakdown.keys.sorted()), id: \.self) { status in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(colorForStatus(status))
                                .frame(width: 12, height: 12)

                            Text(status.capitalized)
                                .font(.system(size: 13))
                                .foregroundColor(AngelaTheme.textPrimary)

                            Spacer()

                            Text("\(statusBreakdown[status] ?? 0)")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                    }
                }
            } else {
                emptyChartView
            }
        }
        .padding(AngelaTheme.spacingL)
        .frame(maxWidth: .infinity)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 8, y: 4)
    }

    // MARK: - Priority Chart Card
    private var priorityChartCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingL) {
            HStack {
                Image(systemName: "flag.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 18))

                Text("Priority Breakdown")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()
            }

            if !priorityBreakdown.isEmpty {
                Chart {
                    ForEach(Array(priorityBreakdown.keys.sorted()), id: \.self) { priority in
                        BarMark(
                            x: .value("Priority", priority),
                            y: .value("Count", priorityBreakdown[priority] ?? 0)
                        )
                        .foregroundStyle(AngelaTheme.priorityColor(for: priority))
                        .annotation(position: .top) {
                            Text("\(priorityBreakdown[priority] ?? 0)")
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                    }
                }
                .frame(height: 220)

                // Summary
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(Array(priorityBreakdown.keys.sorted()), id: \.self) { priority in
                        HStack(spacing: 8) {
                            Image(systemName: AngelaTheme.priorityIcon(for: priority))
                                .foregroundColor(AngelaTheme.priorityColor(for: priority))
                                .font(.system(size: 12))

                            Text(priority)
                                .font(.system(size: 13))
                                .foregroundColor(AngelaTheme.textPrimary)

                            Spacer()

                            Text("\(priorityBreakdown[priority] ?? 0)")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                    }
                }
            } else {
                emptyChartView
            }
        }
        .padding(AngelaTheme.spacingL)
        .frame(maxWidth: .infinity)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 8, y: 4)
    }

    // MARK: - Upcoming Meetings Card
    private var upcomingMeetingsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingL) {
            HStack {
                Image(systemName: "calendar.badge.clock")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 18))

                Text("Upcoming Meetings")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("Next 5")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Divider()

            if upcomingMeetings.isEmpty {
                emptyStateView(
                    icon: "calendar.badge.exclamationmark",
                    message: "No upcoming meetings"
                )
            } else {
                VStack(spacing: AngelaTheme.spacingM) {
                    ForEach(upcomingMeetings.prefix(5)) { meeting in
                        UpcomingMeetingRow(meeting: meeting)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacingL)
        .frame(maxWidth: .infinity)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 8, y: 4)
    }

    // MARK: - Recent Activity Card
    private var recentActivityCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingL) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 18))

                Text("Recent Activity")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("Last 5")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Divider()

            if recentMeetings.isEmpty {
                emptyStateView(
                    icon: "tray",
                    message: "No recent activity"
                )
            } else {
                VStack(spacing: AngelaTheme.spacingM) {
                    ForEach(recentMeetings.prefix(5)) { meeting in
                        RecentActivityRow(meeting: meeting)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacingL)
        .frame(maxWidth: .infinity)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 8, y: 4)
    }

    // MARK: - Empty Views
    private var emptyChartView: some View {
        VStack(spacing: 12) {
            Image(systemName: "chart.bar")
                .font(.system(size: 40))
                .foregroundColor(AngelaTheme.textSecondary.opacity(0.3))

            Text("No data available")
                .font(.system(size: 13))
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(height: 220)
        .frame(maxWidth: .infinity)
    }

    private func emptyStateView(icon: String, message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 32))
                .foregroundColor(AngelaTheme.textSecondary.opacity(0.5))

            Text(message)
                .font(.system(size: 13))
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AngelaTheme.spacingXL)
    }

    // MARK: - Helper Functions
    private func colorForStatus(_ status: String) -> Color {
        switch status.lowercased() {
        case "scheduled": return .blue
        case "in_progress": return .orange
        case "completed": return .green
        case "cancelled": return .red
        default: return .gray
        }
    }

    private func loadDashboardData() async {
        // Load meetings if not already loaded
        if viewModel.meetings.isEmpty {
            await viewModel.loadMeetings()
        }

        let meetings = viewModel.meetings

        await MainActor.run {
            // Calculate stats
            totalMeetings = meetings.count
            scheduledMeetings = meetings.filter { $0.status == .scheduled }.count
            inProgressMeetings = meetings.filter { $0.status == .inProgress }.count
            completedMeetings = meetings.filter { $0.status == .completed }.count

            // Upcoming meetings (next 5 scheduled, sorted by date)
            upcomingMeetings = meetings
                .filter { $0.status == .scheduled && $0.meetingDate >= Date() }
                .sorted { $0.meetingDate < $1.meetingDate }

            // Recent meetings (last 5 updated)
            recentMeetings = meetings
                .sorted { $0.updatedAt > $1.updatedAt }

            // Status breakdown
            statusBreakdown = Dictionary(grouping: meetings, by: { $0.status.rawValue })
                .mapValues { $0.count }

            // Priority breakdown
            priorityBreakdown = Dictionary(grouping: meetings, by: { $0.priority ?? "Normal" })
                .mapValues { $0.count }
        }
    }
}

// MARK: - Stat Card Component
struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    let trend: String?

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.system(size: 24))

                Spacer()

                if let trend = trend {
                    Text(trend)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.green)
                }
            }

            Text(value)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(.system(size: 13))
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .padding(AngelaTheme.spacingL)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 8, y: 4)
    }
}

// MARK: - Upcoming Meeting Row
struct UpcomingMeetingRow: View {
    let meeting: Meeting

    var body: some View {
        HStack(spacing: AngelaTheme.spacingM) {
            // Date indicator
            VStack(spacing: 4) {
                Text(meeting.meetingDate, style: .date)
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(AngelaTheme.primaryPurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)

                Text(meeting.startTime, style: .time)
                    .font(.system(size: 10))
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .frame(width: 70)

            VStack(alignment: .leading, spacing: 4) {
                Text(meeting.title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                if let priority = meeting.priority {
                    HStack(spacing: 4) {
                        Image(systemName: AngelaTheme.priorityIcon(for: priority))
                            .font(.system(size: 9))
                        Text(priority)
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.priorityColor(for: priority))
                }
            }

            Spacer()
        }
        .padding(AngelaTheme.spacingS)
        .background(AngelaTheme.palePurple.opacity(0.5))
        .cornerRadius(AngelaTheme.cornerRadiusSmall)
    }
}

// MARK: - Recent Activity Row
struct RecentActivityRow: View {
    let meeting: Meeting

    var body: some View {
        HStack(spacing: AngelaTheme.spacingM) {
            // Status icon
            Image(systemName: AngelaTheme.statusIcon(for: meeting.status.rawValue))
                .foregroundColor(AngelaTheme.statusColor(for: meeting.status.rawValue))
                .font(.system(size: 16))
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 4) {
                Text(meeting.title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                Text(meeting.status.rawValue.capitalized)
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Text(meeting.updatedAt, style: .relative)
                .font(.system(size: 11))
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .padding(AngelaTheme.spacingS)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusSmall)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusSmall)
                .stroke(AngelaTheme.border, lineWidth: 1)
        )
    }
}

// MARK: - Preview
#Preview {
    DashboardView(viewModel: MeetingListViewModel())
        .environmentObject(DatabaseService.shared)
}
