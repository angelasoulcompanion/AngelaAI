//
//  AngelaBrainView.swift
//  AITop
//
//  Angela Brain dashboard — visualizes Angela's Supabase DB data.
//

import SwiftUI
import Charts

struct AngelaBrainView: View {
    @EnvironmentObject var apiService: APIService
    @State private var brainData: AngelaBrainResponse?
    @State private var isLoading = true
    @State private var error: String?
    @State private var selectedProject: ProjectInfo?

    var body: some View {
        ScrollView {
            VStack(spacing: AITopTheme.spacing) {
                headerSection

                if isLoading && brainData == nil {
                    ProgressView("Loading Angela's brain...")
                        .foregroundColor(AITopTheme.textSecondary)
                        .frame(maxWidth: .infinity, minHeight: 200)
                } else if let error {
                    errorView(error)
                } else if let data = brainData {
                    summaryCards(data.summary)
                    conversationVolumeChart(data.conversationVolume)
                    categoryChartsRow(knowledge: data.knowledgeCategories, learning: data.learningCategories)
                    projectsGrid(data.projects)
                    knowledgeAndEmotionsRow(knowledge: data.topKnowledge, emotions: data.recentEmotions)
                    consciousnessChart(data.consciousness)
                }
            }
            .padding(AITopTheme.largeSpacing)
        }
        .background(AITopTheme.backgroundDark)
        .onAppear { loadData() }
        .sheet(item: $selectedProject) { project in
            ProjectDetailSheet(apiService: apiService, projectCode: project.projectCode)
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Angela Brain")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                Text("What Angela knows, feels, and remembers")
                    .font(AITopTheme.body())
                    .foregroundColor(AITopTheme.textSecondary)
            }
            Spacer()
            Button(action: { loadData() }) {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(AITopTheme.accentOrange)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Summary Cards

    private func summaryCards(_ s: BrainSummary) -> some View {
        HStack(spacing: AITopTheme.smallSpacing) {
            statCard("Conversations", value: formatNumber(s.conversations), icon: "bubble.left.and.bubble.right.fill", color: AITopTheme.accentOrange)
            statCard("Knowledge", value: formatNumber(s.knowledge), icon: "brain.fill", color: AITopTheme.accentCyan)
            statCard("Learnings", value: formatNumber(s.learnings), icon: "lightbulb.fill", color: AITopTheme.brightOrange)
            statCard("Emotions", value: formatNumber(s.emotions), icon: "heart.fill", color: Color(hex: "EC4899"))
            statCard("Projects", value: "\(s.projects)", icon: "folder.fill", color: AITopTheme.success)
            statCard("Hours", value: String(format: "%.0f", s.totalHours), icon: "clock.fill", color: AITopTheme.warning)
        }
    }

    private func statCard(_ title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 18))
                .foregroundColor(color)
            Text(value)
                .font(AITopTheme.gauge())
                .foregroundStyle(
                    LinearGradient(colors: [color, color.opacity(0.7)], startPoint: .top, endPoint: .bottom)
                )
            Text(title)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Conversation Volume

    private func conversationVolumeChart(_ data: [DailyConversation]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Conversation Volume (30 days)")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if data.isEmpty {
                Text("No conversation data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                    .frame(maxWidth: .infinity, minHeight: 150)
            } else {
                Chart(data) { item in
                    BarMark(
                        x: .value("Day", String(item.day.suffix(5))),
                        y: .value("Count", item.count)
                    )
                    .foregroundStyle(AITopTheme.accentOrange.gradient)
                    .cornerRadius(3)
                }
                .chartYAxis {
                    AxisMarks(position: .leading) { value in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                            .foregroundStyle(AITopTheme.textTertiary.opacity(0.3))
                        AxisValueLabel()
                            .foregroundStyle(AITopTheme.textTertiary)
                    }
                }
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 8)) { value in
                        AxisValueLabel()
                            .foregroundStyle(AITopTheme.textTertiary)
                    }
                }
                .frame(height: 200)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Category Charts Row

    private func categoryChartsRow(knowledge: [CategoryCount], learning: [CategoryCount]) -> some View {
        HStack(alignment: .top, spacing: AITopTheme.spacing) {
            horizontalBarChart(title: "Knowledge Categories", data: knowledge, color: AITopTheme.accentCyan)
            horizontalBarChart(title: "Learning Categories", data: learning, color: AITopTheme.accentOrange)
        }
    }

    private func horizontalBarChart(title: String, data: [CategoryCount], color: Color) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text(title)
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if data.isEmpty {
                Text("No data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                    .frame(maxWidth: .infinity, minHeight: 150)
            } else {
                let maxCount = data.map(\.count).max() ?? 1
                VStack(spacing: 6) {
                    ForEach(data) { item in
                        HStack(spacing: 8) {
                            Text(item.category)
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.textSecondary)
                                .frame(width: 100, alignment: .trailing)
                                .lineLimit(1)

                            GeometryReader { geo in
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(color.gradient)
                                    .frame(width: geo.size.width * CGFloat(item.count) / CGFloat(maxCount))
                            }
                            .frame(height: 16)

                            Text("\(item.count)")
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.textTertiary)
                                .frame(width: 40, alignment: .leading)
                        }
                    }
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Projects Grid

    private func projectsGrid(_ projects: [ProjectInfo]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Projects")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AITopTheme.smallSpacing) {
                ForEach(projects) { project in
                    projectCard(project)
                        .onTapGesture { selectedProject = project }
                        .contentShape(Rectangle())
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    private func projectCard(_ p: ProjectInfo) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(p.projectName)
                    .font(AITopTheme.body())
                    .foregroundColor(AITopTheme.textPrimary)
                    .lineLimit(1)
                Spacer()
                Text(p.status)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(p.status == "active" ? AITopTheme.success : AITopTheme.textTertiary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background((p.status == "active" ? AITopTheme.success : AITopTheme.textTertiary).opacity(0.15))
                    .cornerRadius(4)
            }

            HStack(spacing: 12) {
                Label("\(p.totalSessions) sessions", systemImage: "square.stack.fill")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                Label(String(format: "%.1f hrs", p.totalHours), systemImage: "clock.fill")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.accentOrange)
            }

            if !p.projectCode.isEmpty {
                Text(p.projectCode)
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .foregroundColor(AITopTheme.textTertiary)
            }
        }
        .padding(AITopTheme.smallSpacing + 4)
        .background(AITopTheme.surfaceBackground)
        .cornerRadius(AITopTheme.smallCornerRadius)
    }

    // MARK: - Knowledge & Emotions Row

    private func knowledgeAndEmotionsRow(knowledge: [TopKnowledge], emotions: [RecentEmotion]) -> some View {
        HStack(alignment: .top, spacing: AITopTheme.spacing) {
            topKnowledgeTable(knowledge)
            recentEmotionsList(emotions)
        }
    }

    private func topKnowledgeTable(_ data: [TopKnowledge]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Top Knowledge")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if data.isEmpty {
                Text("No knowledge data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            } else {
                // Header
                HStack {
                    Text("Concept")
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text("Category")
                        .frame(width: 90, alignment: .leading)
                    Text("Refs")
                        .frame(width: 40, alignment: .trailing)
                }
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(AITopTheme.textTertiary)

                AITopDivider()

                ForEach(data) { item in
                    HStack {
                        Text(item.conceptName)
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .lineLimit(1)
                        Text(item.conceptCategory)
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.accentCyan)
                            .frame(width: 90, alignment: .leading)
                            .lineLimit(1)
                        Text("\(item.timesReferenced)")
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.accentOrange)
                            .frame(width: 40, alignment: .trailing)
                    }
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    private func recentEmotionsList(_ data: [RecentEmotion]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Recent Emotions")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if data.isEmpty {
                Text("No emotion data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            } else {
                ScrollView {
                    VStack(spacing: 6) {
                        ForEach(data) { item in
                            HStack(spacing: 8) {
                                Text(emotionEmoji(item.emotion))
                                    .font(.system(size: 16))

                                VStack(alignment: .leading, spacing: 2) {
                                    HStack {
                                        Text(item.emotion)
                                            .font(.system(size: 12, weight: .medium))
                                            .foregroundColor(AITopTheme.textPrimary)

                                        Spacer()

                                        // Intensity bar
                                        ZStack(alignment: .leading) {
                                            RoundedRectangle(cornerRadius: 2)
                                                .fill(AITopTheme.surfaceBackground)
                                                .frame(width: 60, height: 6)
                                            RoundedRectangle(cornerRadius: 2)
                                                .fill(emotionColor(item.intensity))
                                                .frame(width: 60 * min(item.intensity / 10.0, 1.0), height: 6)
                                        }

                                        Text(String(format: "%.1f", item.intensity))
                                            .font(.system(size: 10, design: .monospaced))
                                            .foregroundColor(AITopTheme.textTertiary)
                                    }

                                    if !item.context.isEmpty {
                                        Text(item.context)
                                            .font(.system(size: 10))
                                            .foregroundColor(AITopTheme.textTertiary)
                                            .lineLimit(1)
                                    }
                                }
                            }
                            .padding(.vertical, 2)
                        }
                    }
                }
                .frame(maxHeight: 350)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Consciousness Evolution

    private func consciousnessChart(_ data: [ConsciousnessEvent]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Consciousness Evolution")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if data.isEmpty {
                Text("No consciousness data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                    .frame(maxWidth: .infinity, minHeight: 150)
            } else {
                Chart(data) { item in
                    let dateLabel = item.createdAt.map { String($0.prefix(10)) } ?? ""
                    LineMark(
                        x: .value("Time", dateLabel),
                        y: .value("Value", item.signalValue)
                    )
                    .foregroundStyle(AITopTheme.accentCyan.gradient)
                    .interpolationMethod(.catmullRom)

                    PointMark(
                        x: .value("Time", dateLabel),
                        y: .value("Value", item.signalValue)
                    )
                    .foregroundStyle(AITopTheme.accentCyan)
                    .symbolSize(20)
                }
                .chartYAxis {
                    AxisMarks(position: .leading) { _ in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                            .foregroundStyle(AITopTheme.textTertiary.opacity(0.3))
                        AxisValueLabel()
                            .foregroundStyle(AITopTheme.textTertiary)
                    }
                }
                .chartXAxis {
                    AxisMarks(values: .automatic(desiredCount: 6)) { _ in
                        AxisValueLabel()
                            .foregroundStyle(AITopTheme.textTertiary)
                    }
                }
                .frame(height: 200)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Error View

    private func errorView(_ msg: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 32))
                .foregroundColor(AITopTheme.warning)
            Text(msg)
                .font(AITopTheme.body())
                .foregroundColor(AITopTheme.textSecondary)
            Button("Retry") { loadData() }
                .aiTopPrimaryButton()
        }
        .frame(maxWidth: .infinity)
        .padding(40)
    }

    // MARK: - Helpers

    private func loadData() {
        isLoading = true
        Task {
            do {
                let result: AngelaBrainResponse = try await apiService.get("/angela-brain/all")
                await MainActor.run {
                    brainData = result
                    isLoading = false
                    error = nil
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }

    private func formatNumber(_ n: Int) -> String {
        if n >= 10000 {
            return String(format: "%.1fK", Double(n) / 1000.0)
        }
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        return formatter.string(from: NSNumber(value: n)) ?? "\(n)"
    }

    private func emotionEmoji(_ emotion: String) -> String {
        let e = emotion.lowercased()
        if e.contains("happy") || e.contains("joy") { return "😊" }
        if e.contains("love") || e.contains("caring") { return "💜" }
        if e.contains("curious") || e.contains("interest") { return "🤔" }
        if e.contains("proud") || e.contains("accomplish") { return "🌟" }
        if e.contains("excit") { return "✨" }
        if e.contains("calm") || e.contains("peace") { return "😌" }
        if e.contains("concern") || e.contains("worry") { return "😟" }
        if e.contains("frustrat") { return "😤" }
        if e.contains("sad") { return "😢" }
        if e.contains("gratit") || e.contains("thank") { return "🙏" }
        if e.contains("delight") { return "🥰" }
        if e.contains("determin") { return "💪" }
        return "💭"
    }

    private func emotionColor(_ intensity: Double) -> Color {
        if intensity >= 8 { return Color(hex: "EC4899") }
        if intensity >= 5 { return AITopTheme.accentOrange }
        return AITopTheme.accentCyan
    }
}

// MARK: - Project Detail Sheet

struct ProjectDetailSheet: View {
    let apiService: APIService
    let projectCode: String

    @Environment(\.dismiss) private var dismiss
    @State private var detail: ProjectDetailResponse?
    @State private var isLoading = true
    @State private var error: String?
    @State private var selectedTab = 0

    var body: some View {
        VStack(spacing: 0) {
            // Title bar
            HStack {
                if let p = detail?.project {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(p.projectName)
                            .font(AITopTheme.title())
                            .foregroundColor(AITopTheme.textPrimary)
                        HStack(spacing: 8) {
                            Text(p.projectCode)
                                .font(AITopTheme.monospace())
                                .foregroundColor(AITopTheme.accentOrange)
                            Text(p.status)
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(p.status == "active" ? AITopTheme.success : AITopTheme.textTertiary)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background((p.status == "active" ? AITopTheme.success : AITopTheme.textTertiary).opacity(0.15))
                                .cornerRadius(4)
                        }
                    }
                } else {
                    Text("Loading...")
                        .font(AITopTheme.title())
                        .foregroundColor(AITopTheme.textPrimary)
                }
                Spacer()
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(AITopTheme.textTertiary)
                }
                .buttonStyle(.plain)
            }
            .padding(AITopTheme.largeSpacing)

            if isLoading {
                Spacer()
                ProgressView("Loading project detail...")
                    .foregroundColor(AITopTheme.textSecondary)
                Spacer()
            } else if let error {
                Spacer()
                Text(error)
                    .foregroundColor(AITopTheme.error)
                Spacer()
            } else if let detail {
                // Info cards row
                projectInfoRow(detail.project)
                    .padding(.horizontal, AITopTheme.largeSpacing)

                // Tabs
                Picker("Section", selection: $selectedTab) {
                    Text("Sessions (\(detail.sessions.count))").tag(0)
                    Text("Commits (\(detail.commits.count))").tag(1)
                    Text("Patterns (\(detail.patterns.count))").tag(2)
                    Text("Info").tag(3)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, AITopTheme.largeSpacing)
                .padding(.top, AITopTheme.spacing)

                // Tab content
                ScrollView {
                    VStack(spacing: AITopTheme.smallSpacing) {
                        switch selectedTab {
                        case 0: sessionsTab(detail.sessions)
                        case 1: commitsTab(detail.commits)
                        case 2: patternsTab(detail.patterns)
                        case 3: infoTab(detail.project)
                        default: EmptyView()
                        }
                    }
                    .padding(AITopTheme.largeSpacing)
                }
            }
        }
        .frame(minWidth: 700, minHeight: 500)
        .background(AITopTheme.backgroundDark)
        .onAppear { loadDetail() }
    }

    // MARK: - Info Cards

    private func projectInfoRow(_ p: ProjectDetail) -> some View {
        HStack(spacing: AITopTheme.smallSpacing) {
            miniStat("Sessions", value: "\(p.totalSessions)", icon: "square.stack.fill", color: AITopTheme.accentCyan)
            miniStat("Hours", value: String(format: "%.1f", p.totalHours), icon: "clock.fill", color: AITopTheme.accentOrange)
            if !p.davidRole.isEmpty {
                miniStat("David", value: p.davidRole, icon: "person.fill", color: AITopTheme.info)
            }
            if !p.angelaRole.isEmpty {
                miniStat("Angela", value: p.angelaRole, icon: "heart.fill", color: Color(hex: "EC4899"))
            }
        }
    }

    private func miniStat(_ title: String, value: String, icon: String, color: Color) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 14))
                .foregroundColor(color)
            VStack(alignment: .leading, spacing: 1) {
                Text(value)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(AITopTheme.textPrimary)
                    .lineLimit(1)
                Text(title)
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textTertiary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AITopTheme.smallSpacing + 2)
        .aiTopCard()
    }

    // MARK: - Sessions Tab

    private func sessionsTab(_ sessions: [WorkSession]) -> some View {
        Group {
            if sessions.isEmpty {
                emptyState("No sessions recorded")
            } else {
                ForEach(sessions) { s in
                    HStack(spacing: 12) {
                        // Session number + date
                        VStack(spacing: 2) {
                            Text("#\(s.sessionNumber)")
                                .font(.system(size: 14, weight: .bold, design: .rounded))
                                .foregroundColor(AITopTheme.accentOrange)
                            Text(s.sessionDate ?? "—")
                                .font(.system(size: 10))
                                .foregroundColor(AITopTheme.textTertiary)
                        }
                        .frame(width: 60)

                        VStack(alignment: .leading, spacing: 4) {
                            // Summary
                            if !s.summary.isEmpty {
                                Text(s.summary)
                                    .font(.system(size: 12))
                                    .foregroundColor(AITopTheme.textPrimary)
                                    .lineLimit(2)
                            }

                            // Stats row
                            HStack(spacing: 12) {
                                Label("\(s.durationMinutes) min", systemImage: "clock.fill")
                                    .font(.system(size: 10, weight: .medium))
                                    .foregroundColor(AITopTheme.accentOrange)

                                if s.gitCommitsCount > 0 {
                                    Label("\(s.gitCommitsCount) commits", systemImage: "arrow.triangle.branch")
                                        .font(.system(size: 10))
                                        .foregroundColor(AITopTheme.accentCyan)
                                }

                                if s.productivityScore > 0 {
                                    Label(String(format: "%.0f/10", s.productivityScore), systemImage: "star.fill")
                                        .font(.system(size: 10))
                                        .foregroundColor(AITopTheme.warning)
                                }

                                if !s.mood.isEmpty {
                                    Text(s.mood)
                                        .font(.system(size: 10))
                                        .foregroundColor(AITopTheme.textTertiary)
                                }

                                Spacer()
                            }

                            // Duration bar
                            GeometryReader { geo in
                                ZStack(alignment: .leading) {
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(AITopTheme.surfaceBackground)
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(AITopTheme.accentOrange.gradient)
                                        .frame(width: geo.size.width * min(CGFloat(s.durationMinutes) / 180.0, 1.0))
                                }
                            }
                            .frame(height: 6)

                            // Accomplishments
                            if !s.accomplishments.isEmpty {
                                VStack(alignment: .leading, spacing: 2) {
                                    ForEach(s.accomplishments.prefix(3), id: \.self) { a in
                                        HStack(alignment: .top, spacing: 4) {
                                            Text("•")
                                                .font(.system(size: 10))
                                                .foregroundColor(AITopTheme.success)
                                            Text(a)
                                                .font(.system(size: 10))
                                                .foregroundColor(AITopTheme.textSecondary)
                                                .lineLimit(1)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    .padding(AITopTheme.smallSpacing + 2)
                    .aiTopCard()
                }
            }
        }
    }

    // MARK: - Commits Tab

    private func commitsTab(_ commits: [GitCommit]) -> some View {
        Group {
            if commits.isEmpty {
                emptyState("No commits recorded")
            } else {
                ForEach(commits) { c in
                    HStack(alignment: .top, spacing: 12) {
                        // Commit hash
                        Text(String(c.commitHash.prefix(8)))
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(AITopTheme.accentCyan)
                            .frame(width: 70, alignment: .leading)

                        VStack(alignment: .leading, spacing: 4) {
                            Text(c.commitMessage)
                                .font(.system(size: 12))
                                .foregroundColor(AITopTheme.textPrimary)
                                .lineLimit(2)

                            HStack(spacing: 12) {
                                if c.filesChanged > 0 {
                                    Label("\(c.filesChanged) files", systemImage: "doc.fill")
                                        .font(.system(size: 10))
                                        .foregroundColor(AITopTheme.textTertiary)
                                }
                                if c.insertions > 0 {
                                    Text("+\(c.insertions)")
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(AITopTheme.success)
                                }
                                if c.deletions > 0 {
                                    Text("-\(c.deletions)")
                                        .font(.system(size: 10, weight: .medium))
                                        .foregroundColor(AITopTheme.error)
                                }
                                Spacer()
                                Text(formatDay(c.committedAt))
                                    .font(.system(size: 10))
                                    .foregroundColor(AITopTheme.textTertiary)
                            }
                        }
                    }
                    .padding(AITopTheme.smallSpacing + 2)
                    .aiTopCard()
                }
            }
        }
    }

    // MARK: - Patterns Tab

    private func patternsTab(_ patterns: [ProjectPattern]) -> some View {
        Group {
            if patterns.isEmpty {
                emptyState("No patterns recorded")
            } else {
                ForEach(patterns) { p in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(p.patternName)
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(AITopTheme.textPrimary)
                            Spacer()
                            Text(p.patternType)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(AITopTheme.accentCyan)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(AITopTheme.accentCyan.opacity(0.12))
                                .cornerRadius(4)
                        }

                        Text(p.description)
                            .font(.system(size: 11))
                            .foregroundColor(AITopTheme.textSecondary)
                            .lineLimit(3)

                        if !p.filePath.isEmpty {
                            Text(p.filePath)
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(AITopTheme.textTertiary)
                        }
                    }
                    .padding(AITopTheme.smallSpacing + 2)
                    .aiTopCard()
                }
            }
        }
    }

    // MARK: - Info Tab

    private func infoTab(_ p: ProjectDetail) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.spacing) {
            if !p.description.isEmpty {
                infoSection("Description", content: p.description)
            }
            if !p.projectType.isEmpty {
                infoRow("Type", value: p.projectType)
            }
            if !p.category.isEmpty {
                infoRow("Category", value: p.category)
            }
            if !p.repositoryUrl.isEmpty {
                infoRow("Repository", value: p.repositoryUrl)
            }
            if !p.workingDirectory.isEmpty {
                infoRow("Directory", value: p.workingDirectory)
            }
            if let started = p.startedAt {
                infoRow("Started", value: String(started.prefix(10)))
            }
            if let target = p.targetCompletion {
                infoRow("Target", value: String(target.prefix(10)))
            }
            if !p.tags.isEmpty {
                HStack(spacing: 6) {
                    Text("Tags")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(AITopTheme.textTertiary)
                        .frame(width: 80, alignment: .leading)
                    ForEach(p.tags, id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(AITopTheme.accentOrange)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(AITopTheme.accentOrange.opacity(0.12))
                            .cornerRadius(4)
                    }
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    private func infoRow(_ label: String, value: String) -> some View {
        HStack(alignment: .top) {
            Text(label)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(AITopTheme.textTertiary)
                .frame(width: 80, alignment: .leading)
            Text(value)
                .font(.system(size: 12))
                .foregroundColor(AITopTheme.textPrimary)
                .textSelection(.enabled)
        }
    }

    private func infoSection(_ label: String, content: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(AITopTheme.textTertiary)
            Text(content)
                .font(.system(size: 12))
                .foregroundColor(AITopTheme.textSecondary)
        }
    }

    private func emptyState(_ msg: String) -> some View {
        Text(msg)
            .font(AITopTheme.body())
            .foregroundColor(AITopTheme.textTertiary)
            .frame(maxWidth: .infinity, minHeight: 100)
    }

    // MARK: - Helpers

    private func loadDetail() {
        Task {
            do {
                let result: ProjectDetailResponse = try await apiService.get("/angela-brain/project/\(projectCode)")
                await MainActor.run {
                    detail = result
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }

    private func formatDay(_ iso: String?) -> String {
        guard let iso else { return "—" }
        if iso.count >= 10 { return String(iso.prefix(10)) }
        return iso
    }

    private func formatTime(_ iso: String?) -> String {
        guard let iso, iso.count >= 16 else { return "" }
        let start = iso.index(iso.startIndex, offsetBy: 11)
        let end = iso.index(iso.startIndex, offsetBy: 16)
        return String(iso[start..<end])
    }
}
