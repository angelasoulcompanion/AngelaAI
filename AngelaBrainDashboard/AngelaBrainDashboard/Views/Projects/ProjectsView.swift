//
//  ProjectsView.swift
//  Angela Brain Dashboard
//
//  💜 Projects View - Track David & Angela's Collaborative Work 🏗️
//

import SwiftUI
import Charts
import Combine

struct ProjectsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = ProjectsViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Analytics Cards Row
                analyticsCardsRow

                // Charts Row
                chartsRow

                // Tech Stack Knowledge Graph
                techStackGraphCard

                // Active Projects
                activeProjectsCard

                // Recent Sessions
                recentSessionsCard

                // Milestones & Learnings
                HStack(alignment: .top, spacing: AngelaTheme.spacing) {
                    recentMilestonesCard
                    recentLearningsCard
                }
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

    // MARK: - Helper Functions

    private func colorForType(_ type: String) -> Color {
        switch type {
        case "Client": return AngelaTheme.emotionMotivated
        case "Personal": return AngelaTheme.successGreen
        case "Our Future": return Color(hex: "EC4899")
        default: return AngelaTheme.textTertiary
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Projects")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("\(viewModel.projects.count) projects • \(viewModel.totalSessions) sessions • \(String(format: "%.1f", viewModel.totalHours)) hours")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Weekly summary
            VStack(alignment: .trailing, spacing: 4) {
                Text("This Week")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)

                Text("\(viewModel.weekSessions) sessions")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
        }
    }

    // MARK: - Analytics Cards

    private var analyticsCardsRow: some View {
        HStack(spacing: AngelaTheme.spacing) {
            // Total Projects
            AnalyticsCard(
                title: "Projects",
                value: "\(viewModel.projects.count)",
                subtitle: "\(viewModel.activeProjects) active",
                icon: "folder.fill",
                color: AngelaTheme.primaryPurple
            )

            // Total Sessions
            AnalyticsCard(
                title: "Sessions",
                value: "\(viewModel.totalSessions)",
                subtitle: "\(viewModel.weekSessions) this week",
                icon: "clock.fill",
                color: AngelaTheme.emotionMotivated
            )

            // Total Hours
            AnalyticsCard(
                title: "Hours Worked",
                value: String(format: "%.0f", viewModel.totalHours),
                subtitle: String(format: "%.1f avg/session", viewModel.avgSessionHours),
                icon: "timer",
                color: AngelaTheme.successGreen
            )

            // Avg Productivity
            AnalyticsCard(
                title: "Avg Productivity",
                value: String(format: "%.1f", viewModel.avgProductivity),
                subtitle: "out of 10",
                icon: "star.fill",
                color: AngelaTheme.accentGold
            )
        }
    }

    // MARK: - Charts Row

    private var chartsRow: some View {
        HStack(spacing: AngelaTheme.spacing) {
            // Sessions per week chart
            sessionsChartCard

            // Projects by type chart
            projectTypeChartCard

            // Hours by type chart
            hoursTypeChartCard
        }
    }

    private var hoursTypeChartCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Hours by Type")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.hoursByType.isEmpty {
                Text("No hours data")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity, minHeight: 150)
            } else {
                Chart(viewModel.hoursByType) { item in
                    SectorMark(
                        angle: .value("Hours", item.hours),
                        innerRadius: .ratio(0.5),
                        angularInset: 2
                    )
                    .foregroundStyle(by: .value("Type", item.type))
                    .cornerRadius(4)
                }
                .frame(height: 150)
                .chartForegroundStyleScale([
                    "Client": AngelaTheme.emotionMotivated,
                    "Personal": AngelaTheme.successGreen,
                    "Our Future": Color(hex: "EC4899")
                ])
                .chartLegend(position: .trailing, alignment: .center)

                // Hours summary
                HStack(spacing: 16) {
                    ForEach(viewModel.hoursByType) { item in
                        HStack(spacing: 4) {
                            Circle()
                                .fill(colorForType(item.type))
                                .frame(width: 8, height: 8)
                            Text("\(item.type): \(String(format: "%.1f", item.hours))h")
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                    }
                }
                .padding(.top, 4)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    private var sessionsChartCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Sessions (Last 7 Days)")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.dailySessionCounts.isEmpty {
                Text("No session data")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity, minHeight: 150)
            } else {
                Chart(viewModel.dailySessionCounts) { item in
                    BarMark(
                        x: .value("Day", item.day),
                        y: .value("Sessions", item.count)
                    )
                    .foregroundStyle(AngelaTheme.purpleGradient)
                    .cornerRadius(4)
                }
                .frame(height: 150)
                .chartXAxis {
                    AxisMarks(values: .automatic) { _ in
                        AxisValueLabel()
                            .foregroundStyle(AngelaTheme.textSecondary)
                    }
                }
                .chartYAxis {
                    AxisMarks(values: .automatic) { _ in
                        AxisValueLabel()
                            .foregroundStyle(AngelaTheme.textSecondary)
                        AxisGridLine()
                            .foregroundStyle(AngelaTheme.textTertiary.opacity(0.2))
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    private var projectTypeChartCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Projects by Type")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.projectTypeCounts.isEmpty {
                Text("No project data")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity, minHeight: 150)
            } else {
                Chart(viewModel.projectTypeCounts) { item in
                    SectorMark(
                        angle: .value("Count", item.count),
                        innerRadius: .ratio(0.5),
                        angularInset: 2
                    )
                    .foregroundStyle(by: .value("Type", item.type))
                    .cornerRadius(4)
                }
                .frame(height: 150)
                .chartForegroundStyleScale([
                    "Personal": AngelaTheme.successGreen,
                    "Client": AngelaTheme.emotionMotivated,
                    "Our Future": Color(hex: "EC4899"),
                    "Learning": Color(hex: "10B981"),
                    "Maintenance": Color(hex: "F59E0B")
                ])
                .chartLegend(position: .trailing, alignment: .center)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Tech Stack Graph

    private var techStackGraphCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "cpu.fill")
                        .font(.system(size: 18))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("Tech Stack Knowledge")
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                Spacer()

                if let graphData = viewModel.techStackGraphData {
                    let techCount = graphData.nodes.filter { $0.nodeType == "tech" }.count
                    let projectCount = graphData.nodes.filter { $0.nodeType == "project" }.count

                    VStack(alignment: .trailing, spacing: 2) {
                        Text("\(techCount) technologies • \(projectCount) projects")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Text("\(graphData.links.count) connections")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }
            }

            Text("Angela's knowledge of technologies learned from projects")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)

            if viewModel.techStackGraphData == nil || viewModel.techStackGraphData?.nodes.isEmpty == true {
                VStack(spacing: 12) {
                    Image(systemName: "cpu")
                        .font(.system(size: 40))
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text("No tech stack data yet")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text("Add projects with technologies to see the graph")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .frame(maxWidth: .infinity)
                .frame(height: 400)
            } else {
                // Interactive D3.js graph
                TechStackGraphWebView(graphData: viewModel.techStackGraphData) { nodeId, nodeName in
                    print("Tech node clicked: \(nodeName)")
                }
                .frame(height: 500)
                .cornerRadius(AngelaTheme.smallCornerRadius)

                // Instructions
                HStack(spacing: 8) {
                    Image(systemName: "hand.draw")
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("Drag nodes • Scroll to zoom • Hover for details")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    Spacer()

                    // Legend inline
                    HStack(spacing: 12) {
                        LegendItem(color: Color(hex: "#9333EA"), label: "Project", isCircle: true)
                        LegendItem(color: Color(hex: "#8B5CF6"), label: "Language", isCircle: false)
                        LegendItem(color: Color(hex: "#3B82F6"), label: "Framework", isCircle: false)
                        LegendItem(color: Color(hex: "#10B981"), label: "Database", isCircle: false)
                    }
                }
                .padding(.top, AngelaTheme.smallSpacing)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Active Projects

    private var activeProjectsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("Active Projects")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(viewModel.activeProjects) active")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.successGreen)
            }

            if viewModel.projects.isEmpty {
                ProjectEmptyStateView(
                    icon: "folder",
                    message: "No projects yet"
                )
            } else {
                VStack(spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.projects.prefix(5)) { project in
                        ProjectCard(project: project)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Recent Sessions

    private var recentSessionsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("Recent Work Sessions")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("Last 7 days")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            if viewModel.recentSessions.isEmpty {
                ProjectEmptyStateView(
                    icon: "clock",
                    message: "No recent sessions"
                )
            } else {
                VStack(spacing: AngelaTheme.smallSpacing) {
                    ForEach(viewModel.recentSessions.prefix(10)) { session in
                        SessionRow(session: session)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Milestones

    private var recentMilestonesCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("Recent Milestones")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Image(systemName: "flag.fill")
                    .foregroundColor(AngelaTheme.accentGold)
            }

            if viewModel.recentMilestones.isEmpty {
                ProjectEmptyStateView(
                    icon: "flag",
                    message: "No milestones yet"
                )
            } else {
                VStack(spacing: AngelaTheme.smallSpacing) {
                    ForEach(viewModel.recentMilestones.prefix(5)) { milestone in
                        MilestoneRow(milestone: milestone)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Learnings

    private var recentLearningsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("Project Learnings")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Image(systemName: "lightbulb.fill")
                    .foregroundColor(AngelaTheme.emotionMotivated)
            }

            if viewModel.recentLearnings.isEmpty {
                ProjectEmptyStateView(
                    icon: "lightbulb",
                    message: "No learnings yet"
                )
            } else {
                VStack(spacing: AngelaTheme.smallSpacing) {
                    ForEach(viewModel.recentLearnings.prefix(5)) { learning in
                        LearningRow(learning: learning)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Analytics Card Component

struct AnalyticsCard: View {
    let title: String
    let value: String
    let subtitle: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 16))
                    .foregroundColor(color)

                Spacer()
            }

            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)

            Text(subtitle)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(
                colors: [color.opacity(0.1), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(color.opacity(0.3), lineWidth: 1)
        )
    }
}

// MARK: - Project Card Component

struct ProjectCard: View {
    let project: Project

    private var typeColor: Color {
        switch project.projectType {
        case "client": return AngelaTheme.emotionMotivated
        case "personal": return AngelaTheme.primaryPurple
        case "learning": return AngelaTheme.successGreen
        case "Our Future": return Color(hex: "EC4899")  // Pink - Our Future together 💜
        default: return AngelaTheme.textTertiary
        }
    }

    private var statusColor: Color {
        switch project.status {
        case "active": return AngelaTheme.successGreen
        case "paused": return AngelaTheme.warningOrange
        case "completed": return AngelaTheme.primaryPurple
        default: return AngelaTheme.textTertiary
        }
    }

    var body: some View {
        HStack(spacing: 16) {
            // Project icon with type color
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(typeColor.opacity(0.2))
                    .frame(width: 50, height: 50)

                Image(systemName: project.typeIcon)
                    .font(.system(size: 20))
                    .foregroundColor(typeColor)
            }

            // Project info
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(project.projectName)
                        .font(AngelaTheme.body())
                        .fontWeight(.medium)
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text(project.projectCode)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(AngelaTheme.backgroundLight)
                        .cornerRadius(4)
                }

                HStack(spacing: 12) {
                    // Type badge
                    Text(project.projectType.capitalized)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(typeColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(typeColor.opacity(0.15))
                        .cornerRadius(4)

                    // Sessions count
                    Label("\(project.totalSessions) sessions", systemImage: "clock")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    // Hours
                    Label(String(format: "%.1fh", project.totalHours), systemImage: "timer")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }

            Spacer()

            // Status and last session
            VStack(alignment: .trailing, spacing: 6) {
                Text(project.status.capitalized)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(statusColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor.opacity(0.15))
                    .cornerRadius(6)

                if let lastSession = project.lastSessionDate {
                    Text(lastSession, style: .relative)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.smallCornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.smallCornerRadius)
                .stroke(typeColor.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Session Row Component

struct SessionRow: View {
    let session: WorkSession

    private var moodColor: Color {
        switch session.mood {
        case "productive": return AngelaTheme.successGreen
        case "learning": return AngelaTheme.emotionMotivated
        case "debugging": return AngelaTheme.warningOrange
        case "challenging": return AngelaTheme.errorRed
        default: return AngelaTheme.primaryPurple
        }
    }

    private var moodIcon: String {
        switch session.mood {
        case "productive": return "bolt.fill"
        case "learning": return "book.fill"
        case "debugging": return "ant.fill"
        case "challenging": return "exclamationmark.triangle.fill"
        default: return "sparkles"
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            // Session number and mood
            ZStack {
                Circle()
                    .fill(moodColor.opacity(0.2))
                    .frame(width: 36, height: 36)

                Image(systemName: moodIcon)
                    .font(.system(size: 14))
                    .foregroundColor(moodColor)
            }

            // Session info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(session.projectName ?? "Unknown Project")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("#\(session.sessionNumber)")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }

                if let summary = session.summary, !summary.isEmpty {
                    Text(summary)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            // Duration and score
            VStack(alignment: .trailing, spacing: 4) {
                if let duration = session.durationMinutes {
                    Text("\(duration) min")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                if let score = session.productivityScore {
                    HStack(spacing: 2) {
                        Image(systemName: "star.fill")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.accentGold)
                        Text(String(format: "%.1f", score))
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                }
            }

            // Date
            Text(session.sessionDate, style: .date)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
                .frame(width: 80, alignment: .trailing)
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(moodColor.opacity(0.03))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - Milestone Row Component

struct MilestoneRow: View {
    let milestone: ProjectMilestone

    private var typeIcon: String {
        switch milestone.milestoneType {
        case "feature_complete": return "checkmark.seal.fill"
        case "bug_fixed": return "ant.fill"
        case "release": return "shippingbox.fill"
        case "project_start": return "play.fill"
        case "project_complete": return "flag.fill"
        case "breakthrough": return "lightbulb.fill"
        default: return "star.fill"
        }
    }

    private var typeColor: Color {
        switch milestone.milestoneType {
        case "feature_complete": return AngelaTheme.successGreen
        case "bug_fixed": return AngelaTheme.warningOrange
        case "release": return AngelaTheme.emotionMotivated
        case "project_start": return AngelaTheme.primaryPurple
        case "project_complete": return AngelaTheme.accentGold
        case "breakthrough": return AngelaTheme.emotionMotivated
        default: return AngelaTheme.primaryPurple
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: typeIcon)
                .font(.system(size: 14))
                .foregroundColor(typeColor)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(milestone.title)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                if let celebration = milestone.celebrationNote {
                    Text(celebration)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)
                }
            }

            Spacer()

            Text(milestone.achievedAt, style: .relative)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(.vertical, 6)
    }
}

// MARK: - Learning Row Component

struct LearningRow: View {
    let learning: ProjectLearning

    private var typeIcon: String {
        switch learning.learningType {
        case "technical": return "wrench.and.screwdriver.fill"
        case "process": return "flowchart.fill"
        case "mistake": return "exclamationmark.triangle.fill"
        case "best_practice": return "star.fill"
        default: return "lightbulb.fill"
        }
    }

    private var typeColor: Color {
        switch learning.learningType {
        case "technical": return AngelaTheme.primaryPurple
        case "process": return AngelaTheme.emotionMotivated
        case "mistake": return AngelaTheme.warningOrange
        case "best_practice": return AngelaTheme.successGreen
        default: return AngelaTheme.accentGold
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: typeIcon)
                .font(.system(size: 14))
                .foregroundColor(typeColor)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(learning.title)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                Text(learning.insight)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .lineLimit(1)
            }

            Spacer()

            // Confidence indicator
            Text("\(Int(learning.confidence * 100))%")
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(typeColor)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(typeColor.opacity(0.15))
                .cornerRadius(4)
        }
        .padding(.vertical, 6)
    }
}

// MARK: - Empty State

struct ProjectEmptyStateView: View {
    let icon: String
    let message: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 32))
                .foregroundColor(AngelaTheme.textTertiary)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 30)
    }
}

// MARK: - View Model

@MainActor
class ProjectsViewModel: ObservableObject {
    @Published var projects: [Project] = []
    @Published var recentSessions: [WorkSession] = []
    @Published var recentMilestones: [ProjectMilestone] = []
    @Published var recentLearnings: [ProjectLearning] = []
    @Published var dailySessionCounts: [DailySessionCount] = []
    @Published var projectTypeCounts: [ProjectTypeCount] = []
    @Published var hoursByType: [HoursByType] = []
    @Published var techStackGraphData: TechStackGraphData?
    @Published var isLoading = false

    var totalSessions: Int {
        projects.reduce(0) { $0 + $1.totalSessions }
    }

    var totalHours: Double {
        projects.reduce(0.0) { $0 + $1.totalHours }
    }

    var avgSessionHours: Double {
        guard totalSessions > 0 else { return 0 }
        return totalHours / Double(totalSessions)
    }

    var activeProjects: Int {
        projects.filter { $0.status == "active" }.count
    }

    var weekSessions: Int {
        recentSessions.filter { session in
            Calendar.current.isDate(session.sessionDate, equalTo: Date(), toGranularity: .weekOfYear)
        }.count
    }

    var avgProductivity: Double {
        let sessionsWithScore = recentSessions.compactMap { $0.productivityScore }
        guard !sessionsWithScore.isEmpty else { return 0 }
        return sessionsWithScore.reduce(0, +) / Double(sessionsWithScore.count)
    }

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            // Load projects
            projects = try await databaseService.fetchProjects()

            // Load recent sessions
            recentSessions = try await databaseService.fetchRecentWorkSessions(days: 7)

            // Load milestones
            recentMilestones = try await databaseService.fetchRecentMilestones(limit: 10)

            // Load learnings
            recentLearnings = try await databaseService.fetchRecentProjectLearnings(limit: 10)

            // Load tech stack graph data
            techStackGraphData = try await databaseService.fetchTechStackGraphData()

            // Calculate daily session counts for chart
            calculateDailySessionCounts()

            // Calculate project type distribution
            calculateProjectTypeCounts()

            // Calculate hours by type
            calculateHoursByType()

        } catch {
            print("Error loading project data: \(error)")
        }

        isLoading = false
    }

    private func calculateDailySessionCounts() {
        let calendar = Calendar.current
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "E"  // "Mon", "Tue", etc.

        // Create array of last 7 days with their dates (for proper ordering)
        var dayData: [(date: Date, dayName: String, count: Int)] = []

        for i in (0..<7).reversed() {  // Start from 6 days ago to today
            if let date = calendar.date(byAdding: .day, value: -i, to: Date()) {
                let dayName = dateFormatter.string(from: date)
                let startOfDay = calendar.startOfDay(for: date)

                // Count sessions for this specific day
                let count = recentSessions.filter { session in
                    calendar.isDate(session.sessionDate, inSameDayAs: startOfDay)
                }.count

                dayData.append((date: date, dayName: dayName, count: count))
            }
        }

        // Convert to DailySessionCount array (already in chronological order)
        dailySessionCounts = dayData.map { DailySessionCount(day: $0.dayName, count: $0.count) }
    }

    private func calculateProjectTypeCounts() {
        var counts: [String: Int] = [:]

        for project in projects {
            counts[project.projectType, default: 0] += 1
        }

        projectTypeCounts = counts.map { ProjectTypeCount(type: $0.key.capitalized, count: $0.value) }
    }

    private func calculateHoursByType() {
        var hoursCounts: [String: Double] = [:]

        for project in projects {
            let typeKey = project.projectType.capitalized
            hoursCounts[typeKey, default: 0] += project.totalHours
        }

        hoursByType = hoursCounts.map { HoursByType(type: $0.key, hours: $0.value) }
            .sorted { $0.hours > $1.hours }
    }
}

// MARK: - Chart Data Models

struct DailySessionCount: Identifiable {
    let id = UUID()
    let day: String
    let count: Int
}

struct ProjectTypeCount: Identifiable {
    let id = UUID()
    let type: String
    let count: Int
}

struct HoursByType: Identifiable {
    let id = UUID()
    let type: String
    let hours: Double
}

// MARK: - Legend Item Component

struct LegendItem: View {
    let color: Color
    let label: String
    let isCircle: Bool

    var body: some View {
        HStack(spacing: 4) {
            if isCircle {
                Circle()
                    .fill(color)
                    .frame(width: 8, height: 8)
            } else {
                RoundedRectangle(cornerRadius: 2)
                    .fill(color)
                    .frame(width: 10, height: 6)
            }

            Text(label)
                .font(.system(size: 10))
                .foregroundColor(AngelaTheme.textTertiary)
        }
    }
}

