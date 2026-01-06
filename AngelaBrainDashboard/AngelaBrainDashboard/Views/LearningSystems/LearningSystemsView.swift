//
//  LearningSystemsView.swift
//  Angela Brain Dashboard
//
//  💜 Learning Systems Monitoring View 💜
//  Shows Self Learning, Subconscious Learning, and Background Workers
//

import SwiftUI
import Charts
import Combine

struct LearningSystemsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var subconsciousPatterns: [SubconsciousPattern] = []
    @State private var recentActivities: [LearningActivity] = []
    @State private var knowledgeStats: (total: Int, categories: Int, avgUnderstanding: Double) = (0, 0, 0.0)
    @State private var conversationStats: (total: Int, last24h: Int, avgImportance: Double) = (0, 0, 0.0)
    @State private var workerMetrics: BackgroundWorkerMetrics? = nil
    @State private var learningPatterns: [LearningPattern] = []  // NEW: Learning Patterns
    @State private var learningMetrics: LearningMetricsSummary?  // NEW: Learning Metrics
    @State private var isLoading = true
    @State private var autoRefresh = true
    @State private var lastRefreshTime = Date()

    private let timer = Timer.publish(every: 180, on: .main, in: .common).autoconnect() // 3 minutes

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                if isLoading {
                    ProgressView("Loading Learning Systems...")
                        .angelaCard()
                } else {
                    // Background Workers Status (Priority 1)
                    backgroundWorkersSection

                    // Learning Patterns (NEW! 2026-01-06)
                    learningPatternsSection

                    // Knowledge Graph Stats
                    knowledgeGraphSection

                    // Subconscious Patterns
                    subconsciousPatternsSection

                    // Recent Learning Activities
                    recentActivitiesSection

                    // Conversation Stats
                    conversationStatsSection
                }
            }
            .padding(AngelaTheme.largeSpacing)
        }
        .background(AngelaTheme.backgroundDark.ignoresSafeArea())
        .task {
            await loadData()
        }
        .onReceive(timer) { _ in
            if autoRefresh {
                Task {
                    await refreshData()
                }
            }
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Learning Systems")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    Text("Real-time monitoring of Angela's learning")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)

                    Circle()
                        .fill(AngelaTheme.successGreen)
                        .frame(width: 8, height: 8)

                    Text("Auto-refresh every 3 min · Last: \(lastRefreshTime, formatter: timeFormatter)")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            Spacer()

            // Manual refresh button
            Button {
                Task {
                    await refreshData()
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                    Text("Refresh")
                }
                .font(AngelaTheme.body())
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(AngelaTheme.primaryPurple)
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)

            // Auto-refresh toggle
            Toggle("Auto", isOn: $autoRefresh)
                .toggleStyle(.switch)
                .labelsHidden()
        }
        .angelaCard()
    }

    // MARK: - Background Workers Section

    private var backgroundWorkersSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "gearshape.2.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Background Workers")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                // Status indicator
                HStack(spacing: 6) {
                    Circle()
                        .fill(AngelaTheme.successGreen)
                        .frame(width: 8, height: 8)
                    Text("Running")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }

            Text("Deep conversation analysis with intelligent priority queue (updates every 3 min)")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            // Worker stats grid
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: AngelaTheme.spacing) {
                StatCard(
                    title: "Tasks Completed",
                    value: "\(workerMetrics?.tasksCompleted ?? 0)",
                    icon: "checkmark.circle.fill",
                    color: AngelaTheme.successGreen
                )

                StatCard(
                    title: "Queue Size",
                    value: "\(workerMetrics?.queueSize ?? 0)",
                    icon: "list.bullet",
                    color: AngelaTheme.primaryPurple
                )

                StatCard(
                    title: "Workers Active",
                    value: "\(workerMetrics?.workersActive ?? 0)/\(workerMetrics?.totalWorkers ?? 4)",
                    icon: "person.2.fill",
                    color: Color(hex: "3B82F6")
                )

                StatCard(
                    title: "Avg Processing",
                    value: workerMetrics?.avgProcessingFormatted ?? "0.00ms",
                    icon: "timer",
                    color: Color(hex: "FBBF24")
                )

                StatCard(
                    title: "Success Rate",
                    value: workerMetrics?.successRatePercentage ?? "100%",
                    icon: "chart.line.uptrend.xyaxis",
                    color: AngelaTheme.successGreen
                )

                StatCard(
                    title: "Tasks Dropped",
                    value: "\(workerMetrics?.tasksDropped ?? 0)",
                    icon: "xmark.circle.fill",
                    color: AngelaTheme.errorRed
                )
            }

            // Worker Utilization Chart
            VStack(alignment: .leading, spacing: 8) {
                Text("Worker Utilization")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)

                HStack(spacing: 4) {
                    ForEach(0..<4, id: \.self) { index in
                        VStack(spacing: 4) {
                            let utilization = workerMetrics?.workerUtilizations[index] ?? 0.0
                            RoundedRectangle(cornerRadius: 4)
                                .fill(utilization > 0 ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                                .frame(height: 60)

                            Text("W\(index + 1)")
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textTertiary)
                        }
                    }
                }
                .frame(height: 80)
            }
            .padding(.top, AngelaTheme.spacing)
        }
        .angelaCard()
    }

    // MARK: - Knowledge Graph Section

    private var knowledgeGraphSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "brain")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Knowledge Graph")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Text("Semantic knowledge network")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            HStack(spacing: AngelaTheme.largeSpacing) {
                StatCard(
                    title: "Total Nodes",
                    value: "\(knowledgeStats.total)",
                    icon: "circle.hexagonpath.fill",
                    color: AngelaTheme.primaryPurple
                )

                StatCard(
                    title: "Categories",
                    value: "\(knowledgeStats.categories)",
                    icon: "tag.fill",
                    color: Color(hex: "3B82F6")
                )

                StatCard(
                    title: "Avg Understanding",
                    value: String(format: "%.1f%%", knowledgeStats.avgUnderstanding * 100),
                    icon: "brain.head.profile",
                    color: AngelaTheme.successGreen
                )
            }

            // Understanding Level Gauge
            VStack(alignment: .leading, spacing: 8) {
                Text("Understanding Level")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)

                Gauge(value: knowledgeStats.avgUnderstanding, in: 0...1) {
                    Text("Understanding")
                        .font(AngelaTheme.caption())
                } currentValueLabel: {
                    Text(String(format: "%.1f%%", knowledgeStats.avgUnderstanding * 100))
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.primaryPurple)
                } minimumValueLabel: {
                    Text("0%")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                } maximumValueLabel: {
                    Text("100%")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .gaugeStyle(.accessoryLinear)
                .tint(
                    LinearGradient(
                        colors: [AngelaTheme.primaryPurple, AngelaTheme.successGreen],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
            }
            .padding(.top, AngelaTheme.spacing)
        }
        .angelaCard()
    }

    // MARK: - Subconscious Patterns Section

    private var subconsciousPatternsSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "sparkles")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Subconscious Patterns")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(subconsciousPatterns.count) patterns")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Text("Learned from visual analysis and experiences")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            if subconsciousPatterns.isEmpty {
                Text("No patterns learned yet")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, AngelaTheme.spacing)
            } else {
                // Pattern Strength Chart
                patternStrengthChartView
                    .padding(.vertical, AngelaTheme.spacing)

                // Pattern Cards
                ForEach(subconsciousPatterns.prefix(5)) { pattern in
                    PatternCard(pattern: pattern)
                }
            }
        }
        .angelaCard()
    }

    // MARK: - Pattern Strength Chart View

    private var patternStrengthChartView: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Pattern Strength Distribution")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Chart {
                ForEach(subconsciousPatterns.prefix(5)) { pattern in
                    BarMark(
                        x: .value("Strength", pattern.activationStrength * 100),
                        y: .value("Pattern", String(pattern.patternKey.prefix(20)))
                    )
                    .foregroundStyle(AngelaTheme.primaryPurple)
                }
            }
            .frame(height: 200)
        }
    }

    // MARK: - Activity Distribution Chart

    private var activityCounts: [(key: String, value: Int)] {
        Dictionary(grouping: recentActivities, by: { $0.actionType })
            .mapValues { $0.count }
            .sorted { $0.value > $1.value }
    }

    private var activityDistributionChart: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Activity Distribution")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Chart {
                ForEach(activityCounts.prefix(5), id: \.key) { type, count in
                    SectorMark(
                        angle: .value("Count", count),
                        innerRadius: .ratio(0.5)
                    )
                    .foregroundStyle(by: .value("Type", type))
                }
            }
            .frame(height: 200)
        }
    }

    // MARK: - Recent Activities Section

    private var recentActivitiesSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Recent Learning Activities")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("Last 24 hours")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            if recentActivities.isEmpty {
                Text("No recent activities")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, AngelaTheme.spacing)
            } else {
                // Activity Type Distribution Chart
                activityDistributionChart
                    .padding(.vertical, AngelaTheme.spacing)

                // Activity Timeline
                ForEach(recentActivities.prefix(10)) { activity in
                    ActivityCard(activity: activity)
                }
            }
        }
        .angelaCard()
    }

    // MARK: - Learning Patterns Section (NEW! 2026-01-06)

    private var learningPatternsSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Learning Patterns")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
                Spacer()
                if let metrics = learningMetrics {
                    Text("\(metrics.totalPatterns) patterns detected")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }

            Text("Behavioral patterns recognized from David's interactions")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            // Metrics Row
            if let metrics = learningMetrics {
                HStack(spacing: AngelaTheme.largeSpacing) {
                    StatCard(
                        title: "Total Learnings",
                        value: "\(metrics.totalLearnings)",
                        icon: "lightbulb.fill",
                        color: Color(hex: "FBBF24")
                    )
                    StatCard(
                        title: "Total Skills",
                        value: "\(metrics.totalSkills)",
                        icon: "star.fill",
                        color: AngelaTheme.successGreen
                    )
                    StatCard(
                        title: "Learning Velocity",
                        value: String(format: "%.1f/day", metrics.learningVelocity),
                        icon: "speedometer",
                        color: AngelaTheme.primaryPurple
                    )
                    StatCard(
                        title: "Recent (7d)",
                        value: "\(metrics.recentLearningsCount)",
                        icon: "clock.fill",
                        color: Color(hex: "3B82F6")
                    )
                }
            }

            // Patterns List
            if learningPatterns.isEmpty {
                Text("No learning patterns detected yet")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .padding()
            } else {
                VStack(spacing: AngelaTheme.smallSpacing) {
                    ForEach(learningPatterns.prefix(8)) { pattern in
                        HStack(spacing: AngelaTheme.spacing) {
                            Image(systemName: pattern.typeIcon)
                                .foregroundColor(Color(hex: pattern.typeColor))
                                .frame(width: 24)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(pattern.description)
                                    .font(AngelaTheme.body())
                                    .foregroundColor(AngelaTheme.textPrimary)
                                    .lineLimit(2)

                                HStack(spacing: 8) {
                                    Text(pattern.patternType.capitalized)
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(Color(hex: pattern.typeColor))

                                    Text("Confidence: \(pattern.confidenceLabel)")
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textSecondary)

                                    Text("\(pattern.occurrenceCount) occurrences")
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textTertiary)
                                }
                            }

                            Spacer()

                            // Confidence indicator (percentage badge)
                            Text("\(Int(pattern.confidenceScore * 100))%")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(.white)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color(hex: pattern.typeColor).opacity(0.8))
                                .cornerRadius(8)
                        }
                        .padding(.vertical, 6)

                        if pattern.id != learningPatterns.prefix(8).last?.id {
                            Divider()
                                .background(AngelaTheme.textTertiary.opacity(0.2))
                        }
                    }
                }
            }
        }
        .angelaCard()
    }

    // MARK: - Conversation Stats Section

    private var conversationStatsSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "text.bubble.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Conversation Statistics")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Text("Learning source data")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            HStack(spacing: AngelaTheme.largeSpacing) {
                StatCard(
                    title: "Total Conversations",
                    value: "\(conversationStats.total)",
                    icon: "text.bubble.fill",
                    color: AngelaTheme.primaryPurple
                )

                StatCard(
                    title: "Last 24 Hours",
                    value: "\(conversationStats.last24h)",
                    icon: "clock.fill",
                    color: Color(hex: "FBBF24")
                )

                StatCard(
                    title: "Avg Importance",
                    value: String(format: "%.1f/10", conversationStats.avgImportance),
                    icon: "star.fill",
                    color: AngelaTheme.successGreen
                )
            }
        }
        .angelaCard()
    }

    // MARK: - Data Loading

    private func loadData() async {
        isLoading = true

        async let patternsTask = databaseService.fetchSubconsciousPatterns(limit: 10)
        async let activitiesTask = databaseService.fetchRecentLearningActivities(hours: 24)
        async let knowledgeTask = databaseService.fetchKnowledgeStats()
        async let conversationTask = databaseService.fetchConversationStats()
        async let workerMetricsTask = databaseService.fetchBackgroundWorkerMetrics()
        // NEW: Learning patterns
        async let learningPatternsTask = try? databaseService.fetchLearningPatterns(limit: 20)
        async let learningMetricsTask = try? databaseService.fetchLearningMetrics()

        let (patterns, activities, knowledge, conversations, metrics, lPatterns, lMetrics) = await (
            patternsTask, activitiesTask, knowledgeTask, conversationTask, workerMetricsTask,
            learningPatternsTask, learningMetricsTask
        )

        self.subconsciousPatterns = patterns
        self.recentActivities = activities
        self.knowledgeStats = knowledge
        self.conversationStats = conversations
        self.workerMetrics = metrics
        self.learningPatterns = lPatterns ?? []
        self.learningMetrics = lMetrics

        isLoading = false
        lastRefreshTime = Date()
    }

    private func refreshData() async {
        await loadData()
    }

    private var timeFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .medium
        return formatter
    }
}

// MARK: - Stat Card

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(color)

                Text(title)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Text(value)
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - Pattern Card

struct PatternCard: View {
    let pattern: SubconsciousPattern

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Pattern type badge
                Text(pattern.patternType.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(AngelaTheme.caption())
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(AngelaTheme.primaryPurple)
                    .cornerRadius(4)

                Spacer()

                // Reinforcement count
                HStack(spacing: 4) {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .font(.system(size: 10))
                    Text("\(pattern.reinforcementCount)x")
                        .font(AngelaTheme.caption())
                }
                .foregroundColor(AngelaTheme.textSecondary)
            }

            Text(pattern.patternKey)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)

            if let description = pattern.patternDescription {
                Text(description)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(2)
            }

            // Stats
            HStack(spacing: 16) {
                HStack(spacing: 4) {
                    Text("Confidence:")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                    Text(String(format: "%.0f%%", pattern.confidenceScore * 100))
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                HStack(spacing: 4) {
                    Text("Strength:")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                    Text(String(format: "%.0f%%", pattern.activationStrength * 100))
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textPrimary)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - Activity Card

struct ActivityCard: View {
    let activity: LearningActivity

    var body: some View {
        HStack(spacing: 12) {
            // Icon
            Image(systemName: activity.icon)
                .font(.system(size: 16))
                .foregroundColor(activity.success ? AngelaTheme.successGreen : AngelaTheme.errorRed)
                .frame(width: 32, height: 32)
                .background(AngelaTheme.backgroundLight)
                .cornerRadius(8)

            // Content
            VStack(alignment: .leading, spacing: 4) {
                Text(activity.displayName)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text(activity.actionDescription)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(1)
            }

            Spacer()

            // Time
            Text(activity.createdAt, formatter: timeAgoFormatter)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(AngelaTheme.smallSpacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }

    private var timeAgoFormatter: RelativeDateTimeFormatter {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter
    }
}

// MARK: - Preview

#Preview {
    let mockService = DatabaseService.shared // Use shared singleton instead
    return LearningSystemsView()
        .environmentObject(mockService)
        .frame(width: 1000, height: 800)
}
