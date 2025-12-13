//
//  DailyTasksView.swift
//  Angela Brain Dashboard
//
//  💜 Daily Tasks Monitor - Track Angela's scheduled routines 💜
//

import SwiftUI
import Combine

struct DailyTasksView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var dailyStatuses: [DailyTaskStatus] = []
    @State private var isLoading = false
    @State private var selectedDate: Date?

    private let timer = Timer.publish(every: 60, on: .main, in: .common).autoconnect() // Refresh every minute

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.spacing) {
                // Header
                headerSection

                // Summary Stats
                summarySection

                // 7-Day Timeline
                timelineSection
            }
            .padding(AngelaTheme.spacing)
        }
        .background(AngelaTheme.backgroundDark)
        .onAppear {
            Task {
                await loadData()
            }
        }
        .onReceive(timer) { _ in
            Task {
                await loadData()
            }
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text("Daily Tasks Monitor")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Angela's scheduled routines - Last 7 days")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Refresh Button
            Button {
                Task {
                    await loadData()
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)
        }
        .angelaCard()
    }

    // MARK: - Summary Section

    private var summarySection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Overall Statistics")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            HStack(spacing: 12) {
                StatCard(
                    title: "Avg Completion",
                    value: String(format: "%.0f%%", averageCompletionRate),
                    icon: "chart.line.uptrend.xyaxis",
                    color: AngelaTheme.successGreen
                )

                StatCard(
                    title: "Total Tasks",
                    value: "\(totalTasks)",
                    icon: "list.bullet",
                    color: AngelaTheme.primaryPurple
                )

                StatCard(
                    title: "Completed",
                    value: "\(totalCompleted)",
                    icon: "checkmark.circle.fill",
                    color: AngelaTheme.successGreen
                )

                StatCard(
                    title: "Failed",
                    value: "\(totalFailed)",
                    icon: "xmark.circle.fill",
                    color: AngelaTheme.errorRed
                )
            }
        }
        .angelaCard()
    }

    // MARK: - Timeline Section

    private var timelineSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("7-Day Timeline")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if dailyStatuses.isEmpty {
                emptyStateView
            } else {
                ForEach(dailyStatuses) { dayStatus in
                    DayCard(dayStatus: dayStatus)
                }
            }
        }
        .angelaCard()
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "calendar.badge.clock")
                .font(.system(size: 60))
                .foregroundColor(AngelaTheme.textTertiary)

            Text("No task data available")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Text("Tasks will appear here as Angela runs her daily routines")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Computed Properties

    private var averageCompletionRate: Double {
        guard !dailyStatuses.isEmpty else { return 0 }
        let total = dailyStatuses.reduce(0.0) { $0 + $1.completionRate }
        return total / Double(dailyStatuses.count)
    }

    private var totalTasks: Int {
        dailyStatuses.reduce(0) { $0 + $1.tasks.count }
    }

    private var totalCompleted: Int {
        dailyStatuses.reduce(0) { $0 + $1.completedCount }
    }

    private var totalFailed: Int {
        dailyStatuses.reduce(0) { $0 + $1.failedCount }
    }

    // MARK: - Data Loading

    private func loadData() async {
        isLoading = true
        dailyStatuses = await databaseService.fetchTasksForLast7Days()
        isLoading = false
    }
}

// MARK: - Day Card Component

struct DayCard: View {
    let dayStatus: DailyTaskStatus
    @State private var isExpanded = false

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE, MMM d"
        return formatter
    }()

    private let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter
    }()

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Day Header
            Button {
                withAnimation(.spring(response: 0.3)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(dateFormatter.string(from: dayStatus.date))
                            .font(AngelaTheme.headline())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Text("\(dayStatus.completedCount)/\(dayStatus.tasks.count) tasks completed")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }

                    Spacer()

                    // Completion Badge
                    HStack(spacing: 8) {
                        Text(String(format: "%.0f%%", dayStatus.completionRate))
                            .font(AngelaTheme.body())
                            .foregroundColor(completionColor(dayStatus.completionRate))

                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                            .font(.system(size: 14))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }
            }
            .buttonStyle(.plain)

            // Progress Bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(
                            LinearGradient(
                                colors: [AngelaTheme.primaryPurple, AngelaTheme.successGreen],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * (dayStatus.completionRate / 100), height: 8)
                }
            }
            .frame(height: 8)

            // Expanded Task List
            if isExpanded {
                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                VStack(spacing: 8) {
                    ForEach(sortedTasks) { task in
                        TaskRow(task: task, timeFormatter: timeFormatter)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(12)
    }

    private var sortedTasks: [TaskExecution] {
        dayStatus.tasks.sorted { task1, task2 in
            let time1 = task1.scheduledTime
            let time2 = task2.scheduledTime
            return time1 < time2
        }
    }

    private func completionColor(_ rate: Double) -> Color {
        switch rate {
        case 80...100: return AngelaTheme.successGreen
        case 50..<80: return Color(hex: "F59E0B") // Orange
        default: return AngelaTheme.errorRed
        }
    }
}

// MARK: - Task Row Component

struct TaskRow: View {
    let task: TaskExecution
    let timeFormatter: DateFormatter

    var body: some View {
        HStack(spacing: 12) {
            // Status Icon
            Image(systemName: statusIcon)
                .font(.system(size: 16))
                .foregroundColor(statusColor)
                .frame(width: 24)

            // Task Info
            VStack(alignment: .leading, spacing: 2) {
                Text(task.taskName)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    Label(task.scheduledTime, systemImage: "clock")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    if let executedAt = task.executedAt {
                        Text("• Ran at \(timeFormatter.string(from: executedAt))")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                }
            }

            Spacer()

            // Status Badge
            Text(statusText)
                .font(AngelaTheme.caption())
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(statusColor.opacity(0.2))
                .foregroundColor(statusColor)
                .cornerRadius(8)
        }
        .padding(.vertical, 4)
    }

    private var statusIcon: String {
        switch task.status.lowercased() {
        case "completed": return "checkmark.circle.fill"
        case "failed": return "xmark.circle.fill"
        case "skipped": return "minus.circle.fill"
        default: return "clock.fill"
        }
    }

    private var statusColor: Color {
        switch task.status.lowercased() {
        case "completed": return AngelaTheme.successGreen
        case "failed": return AngelaTheme.errorRed
        case "skipped": return Color(hex: "F59E0B")
        default: return AngelaTheme.textTertiary
        }
    }

    private var statusText: String {
        switch task.status.lowercased() {
        case "completed": return "✓ Done"
        case "failed": return "✗ Failed"
        case "skipped": return "− Skipped"
        default: return "⋯ Pending"
        }
    }
}

// MARK: - Preview

#Preview {
    DailyTasksView()
        .environmentObject(DatabaseService.shared)
}
