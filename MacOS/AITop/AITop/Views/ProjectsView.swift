//
//  ProjectsView.swift
//  AITop
//
//  Detailed project tracker. Overview (portfolio grid) → drill-in Detail.
//  Visual sibling of the /recall CLI — surfaces project_work_sessions,
//  technical_decisions, mistakes, git_commits, milestones.
//

import SwiftUI

// MARK: - Shared helpers

private func shortDate(_ s: String?) -> String {
    guard let s, s.count >= 10 else { return s ?? "—" }
    return String(s.prefix(10))
}

private func statusColor(_ status: String) -> Color {
    switch status.lowercased() {
    case "active": return AITopTheme.success
    case "paused", "on_hold": return AITopTheme.warning
    case "completed", "done": return AITopTheme.accentCyan
    default: return AITopTheme.textTertiary
    }
}

private func severityColor(_ sev: String) -> Color {
    switch sev.lowercased() {
    case "critical": return AITopTheme.error
    case "high": return AITopTheme.warning
    case "medium": return AITopTheme.info
    default: return AITopTheme.textTertiary
    }
}

private func severityIcon(_ sev: String) -> String {
    switch sev.lowercased() {
    case "critical": return "exclamationmark.octagon.fill"
    case "high": return "exclamationmark.triangle.fill"
    default: return "info.circle.fill"
    }
}

/// Productivity sparkline as a line graph (0–10 scores), with a soft area
/// fill and an end-point dot. Expands to the available width.
private struct SparkLine: View {
    let values: [Double]
    var color: Color = AITopTheme.accentOrange
    var height: CGFloat = 28
    var maxValue: Double = 10
    private let inset: CGFloat = 3  // keep the stroke/dot off the edges

    var body: some View {
        GeometryReader { geo in
            let pts = points(in: geo.size)
            ZStack {
                if pts.count >= 2 {
                    areaPath(pts, in: geo.size)
                        .fill(LinearGradient(
                            colors: [color.opacity(0.28), color.opacity(0.02)],
                            startPoint: .top, endPoint: .bottom))
                    linePath(pts)
                        .stroke(color, style: StrokeStyle(lineWidth: 1.6, lineCap: .round, lineJoin: .round))
                    if let last = pts.last {
                        Circle().fill(color).frame(width: 5, height: 5).position(last)
                    }
                } else if let only = pts.first {
                    Circle().fill(color).frame(width: 5, height: 5).position(only)
                } else {
                    Text("no data")
                        .font(.system(size: 9))
                        .foregroundColor(AITopTheme.textTertiary)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
                }
            }
        }
        .frame(height: height)
    }

    private func points(in size: CGSize) -> [CGPoint] {
        guard !values.isEmpty else { return [] }
        let usableH = max(size.height - inset * 2, 1)
        let usableW = max(size.width - inset * 2, 1)
        let n = values.count
        return values.enumerated().map { i, v in
            let x = n == 1 ? size.width / 2 : inset + usableW * CGFloat(i) / CGFloat(n - 1)
            let norm = CGFloat(min(max(v, 0), maxValue) / maxValue)
            let y = inset + usableH * (1 - norm)
            return CGPoint(x: x, y: y)
        }
    }

    private func linePath(_ pts: [CGPoint]) -> Path {
        var p = Path()
        p.addLines(pts)
        return p
    }

    private func areaPath(_ pts: [CGPoint], in size: CGSize) -> Path {
        var p = Path()
        guard let first = pts.first, let last = pts.last else { return p }
        p.move(to: CGPoint(x: first.x, y: size.height))
        p.addLine(to: first)
        p.addLines(pts)
        p.addLine(to: CGPoint(x: last.x, y: size.height))
        p.closeSubpath()
        return p
    }
}

/// Reusable section wrapper: heading + content card.
private struct SectionCard<Content: View>: View {
    let title: String
    var count: Int? = nil
    var systemImage: String? = nil
    @ViewBuilder var content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            HStack(spacing: 6) {
                if let systemImage {
                    Image(systemName: systemImage)
                        .font(.system(size: 12))
                        .foregroundColor(AITopTheme.accentOrange)
                }
                Text(title)
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
                if let count {
                    Text("\(count)")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(AITopTheme.textSecondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 1)
                        .background(AITopTheme.surfaceBackground)
                        .cornerRadius(6)
                }
                Spacer()
            }
            content()
        }
        .padding(AITopTheme.spacing)
        .frame(maxWidth: .infinity, alignment: .leading)
        .aiTopCard()
    }
}

private struct StatTile: View {
    let title: String
    let value: String
    let icon: String
    var color: Color = AITopTheme.accentOrange

    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(color)
            Text(value)
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundColor(AITopTheme.textPrimary)
                .lineLimit(1).minimumScaleFactor(0.6)
            Text(title)
                .font(.system(size: 10))
                .foregroundColor(AITopTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AITopTheme.smallSpacing + 2)
        .aiTopCard()
    }
}

private struct ChipLabel: View {
    let text: String
    var color: Color = AITopTheme.accentCyan

    var body: some View {
        Text(text)
            .font(.system(size: 10, weight: .medium))
            .foregroundColor(color)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.15))
            .cornerRadius(4)
    }
}

// MARK: - Overview

struct ProjectsView: View {
    @State private var overview: ProjectsOverview?
    @State private var isLoading = true
    @State private var error: String?
    @State private var selectedCode: String?

    private let columns = [GridItem(.adaptive(minimum: 240), spacing: AITopTheme.spacing)]

    var body: some View {
        Group {
            if let code = selectedCode {
                ProjectDetailPage(projectCode: code) { selectedCode = nil }
            } else {
                overviewPage
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AITopTheme.backgroundDark)
    }

    private var overviewPage: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                header
                if isLoading {
                    ProgressView("Loading projects…")
                        .foregroundColor(AITopTheme.textSecondary)
                        .frame(maxWidth: .infinity, minHeight: 300)
                } else if let error {
                    errorView(error)
                } else if let overview {
                    kpiRow(overview.totals)
                    LazyVGrid(columns: columns, spacing: AITopTheme.spacing) {
                        ForEach(overview.projects) { p in
                            projectCard(p)
                                .onTapGesture { selectedCode = p.projectCode }
                        }
                    }
                }
            }
            .padding(AITopTheme.largeSpacing)
        }
        .task { await load() }
    }

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Projects")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                Text("Portfolio tracker")
                    .font(AITopTheme.body())
                    .foregroundColor(AITopTheme.textSecondary)
            }
            Spacer()
            if let t = overview?.totals {
                Text("\(t.active) active · \(t.weekSessions) sessions this week")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.accentOrange)
            }
        }
    }

    private func kpiRow(_ t: PortfolioTotals) -> some View {
        HStack(spacing: AITopTheme.spacing) {
            StatTile(title: "Projects", value: "\(t.projects)", icon: "square.stack.3d.up.fill", color: AITopTheme.accentOrange)
            StatTile(title: "Sessions", value: "\(t.sessions)", icon: "calendar.badge.clock", color: AITopTheme.accentCyan)
            StatTile(title: "Hours", value: String(format: "%.0f", t.hours), icon: "clock.fill", color: AITopTheme.brightOrange)
            StatTile(title: "Decisions", value: "\(t.decisions)", icon: "ruler.fill", color: AITopTheme.info)
            StatTile(title: "Gotchas", value: "\(t.activeGotchas)", icon: "exclamationmark.triangle.fill", color: AITopTheme.warning)
            StatTile(title: "Commits", value: "\(t.commits)", icon: "arrow.triangle.branch", color: AITopTheme.success)
        }
    }

    private func projectCard(_ p: ProjectCardInfo) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            HStack {
                Text(p.projectCode)
                    .font(AITopTheme.monospace())
                    .foregroundColor(AITopTheme.accentOrange)
                Spacer()
                HStack(spacing: 4) {
                    Circle().fill(statusColor(p.status)).frame(width: 7, height: 7)
                    Text(p.status)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(statusColor(p.status))
                }
            }
            Text(p.projectName)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(AITopTheme.textPrimary)
                .lineLimit(2)
                .frame(maxWidth: .infinity, alignment: .leading)
                .frame(minHeight: 38, alignment: .topLeading)

            HStack(alignment: .center, spacing: 8) {
                SparkLine(values: p.spark).frame(maxWidth: .infinity)
                if p.avgProductivity > 0 {
                    Text(String(format: "prod %.1f", p.avgProductivity))
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AITopTheme.warning)
                        .fixedSize()
                }
            }

            Divider().background(AITopTheme.surfaceBackground)

            HStack(spacing: 10) {
                Label("\(p.totalSessions)", systemImage: "calendar")
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textSecondary)
                Label(String(format: "%.0fh", p.totalHours), systemImage: "clock")
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textSecondary)
                Spacer()
                if p.openThreads > 0 {
                    Label("\(p.openThreads)", systemImage: "link")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AITopTheme.accentCyan)
                }
                if p.activeGotchas > 0 {
                    Label("\(p.activeGotchas)", systemImage: "exclamationmark.triangle.fill")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AITopTheme.warning)
                }
            }
            Text("last \(shortDate(p.lastActive))")
                .font(.system(size: 9))
                .foregroundColor(AITopTheme.textTertiary)
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
        .contentShape(Rectangle())
    }

    private func errorView(_ msg: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 28))
                .foregroundColor(AITopTheme.error)
            Text(msg)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textSecondary)
                .multilineTextAlignment(.center)
            Button("Retry") { Task { await load() } }
                .aiTopSecondaryButton()
        }
        .frame(maxWidth: .infinity, minHeight: 300)
    }

    private func load() async {
        isLoading = true
        error = nil
        do {
            overview = try await APIService.shared.getProjectsOverview()
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

// MARK: - Detail

struct ProjectDetailPage: View {
    let projectCode: String
    let onBack: () -> Void

    @State private var detail: ProjectFullDetail?
    @State private var isLoading = true
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                backBar
                if isLoading {
                    ProgressView("Loading project…")
                        .foregroundColor(AITopTheme.textSecondary)
                        .frame(maxWidth: .infinity, minHeight: 300)
                } else if let error {
                    Text(error)
                        .foregroundColor(AITopTheme.error)
                        .frame(maxWidth: .infinity, minHeight: 200)
                } else if let d = detail {
                    headerCard(d)
                    kpiStrip(d)
                    HStack(alignment: .top, spacing: AITopTheme.spacing) {
                        productivityCard(d.productivity).frame(maxWidth: .infinity)
                        threadsCard(d.threads).frame(maxWidth: .infinity)
                    }
                    timelineCard(d.sessions)
                    HStack(alignment: .top, spacing: AITopTheme.spacing) {
                        decisionsCard(d.decisions).frame(maxWidth: .infinity)
                        gotchasCard(d.gotchas).frame(maxWidth: .infinity)
                    }
                    HStack(alignment: .top, spacing: AITopTheme.spacing) {
                        commitsCard(d.commits).frame(maxWidth: .infinity)
                        milestonesCard(d.milestones).frame(maxWidth: .infinity)
                    }
                    if !d.project.tags.isEmpty {
                        techStackCard(d.project.tags)
                    }
                }
            }
            .padding(AITopTheme.largeSpacing)
        }
        .task(id: projectCode) { await load() }
    }

    private var backBar: some View {
        Button(action: onBack) {
            HStack(spacing: 4) {
                Image(systemName: "chevron.left")
                Text("Projects")
            }
            .font(.system(size: 13, weight: .medium))
            .foregroundColor(AITopTheme.accentOrange)
        }
        .buttonStyle(.plain)
    }

    private func headerCard(_ d: ProjectFullDetail) -> some View {
        let p = d.project
        return VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(p.projectName)
                        .font(AITopTheme.title())
                        .foregroundColor(AITopTheme.textPrimary)
                    HStack(spacing: 8) {
                        Text(p.projectCode)
                            .font(AITopTheme.monospace())
                            .foregroundColor(AITopTheme.accentOrange)
                        HStack(spacing: 4) {
                            Circle().fill(statusColor(p.status)).frame(width: 7, height: 7)
                            Text(p.status)
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(statusColor(p.status))
                        }
                        if !p.category.isEmpty { ChipLabel(text: p.category) }
                    }
                }
                Spacer()
                if !p.repositoryUrl.isEmpty, let url = URL(string: p.repositoryUrl) {
                    Link(destination: url) {
                        Label("Repo", systemImage: "arrow.up.forward.square")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(AITopTheme.accentCyan)
                }
            }
            if !p.description.isEmpty {
                Text(p.description)
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                    .lineLimit(3)
            }
            HStack(spacing: 12) {
                if !p.davidRole.isEmpty {
                    Label("David: \(p.davidRole)", systemImage: "person.fill")
                        .font(.system(size: 11)).foregroundColor(AITopTheme.info)
                }
                if !p.angelaRole.isEmpty {
                    Label("Angela: \(p.angelaRole)", systemImage: "heart.fill")
                        .font(.system(size: 11)).foregroundColor(Color(hex: "EC4899"))
                }
                if let started = p.startedAt {
                    Text("since \(shortDate(started))")
                        .font(.system(size: 11)).foregroundColor(AITopTheme.textTertiary)
                }
            }
        }
        .padding(AITopTheme.spacing)
        .frame(maxWidth: .infinity, alignment: .leading)
        .aiTopCard()
    }

    private func kpiStrip(_ d: ProjectFullDetail) -> some View {
        HStack(spacing: AITopTheme.spacing) {
            StatTile(title: "Sessions", value: "\(d.project.totalSessions)", icon: "calendar.badge.clock", color: AITopTheme.accentCyan)
            StatTile(title: "Hours", value: String(format: "%.0f", d.project.totalHours), icon: "clock.fill", color: AITopTheme.brightOrange)
            StatTile(title: "Decisions", value: "\(d.kpis.decisions)", icon: "ruler.fill", color: AITopTheme.info)
            StatTile(title: "Gotchas", value: "\(d.kpis.activeGotchas)", icon: "exclamationmark.triangle.fill", color: AITopTheme.warning)
            StatTile(title: "Commits", value: "\(d.kpis.commits)", icon: "arrow.triangle.branch", color: AITopTheme.success)
            StatTile(title: "Milestones", value: "\(d.kpis.milestones)", icon: "flag.checkered", color: AITopTheme.accentOrange)
        }
    }

    private func productivityCard(_ pts: [ProductivityPoint]) -> some View {
        SectionCard(title: "Productivity", systemImage: "chart.bar.fill") {
            if pts.isEmpty {
                Text("No scored sessions yet")
                    .font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                let avg = pts.map(\.score).reduce(0, +) / Double(pts.count)
                VStack(alignment: .leading, spacing: 6) {
                    SparkLine(values: pts.map(\.score), color: AITopTheme.accentOrange, height: 60)
                        .frame(maxWidth: .infinity)
                    HStack {
                        Text(String(format: "avg %.1f / 10", avg))
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(AITopTheme.warning)
                        Spacer()
                        Text("\(pts.count) sessions")
                            .font(.system(size: 10)).foregroundColor(AITopTheme.textTertiary)
                    }
                }
            }
        }
    }

    private func threadsCard(_ threads: [String]) -> some View {
        SectionCard(title: "Open Threads", count: threads.count, systemImage: "link") {
            if threads.isEmpty {
                Text("Nothing pending 🎉")
                    .font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(Array(threads.enumerated()), id: \.offset) { _, t in
                        HStack(alignment: .top, spacing: 6) {
                            Image(systemName: "arrow.right.circle.fill")
                                .font(.system(size: 11)).foregroundColor(AITopTheme.accentCyan)
                            Text(t).font(.system(size: 12)).foregroundColor(AITopTheme.textPrimary)
                        }
                    }
                }
            }
        }
    }

    private func timelineCard(_ sessions: [ProjectSession]) -> some View {
        SectionCard(title: "Activity Timeline", count: sessions.count, systemImage: "clock.arrow.circlepath") {
            if sessions.isEmpty {
                Text("No sessions recorded")
                    .font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                VStack(spacing: AITopTheme.smallSpacing) {
                    ForEach(sessions) { s in sessionRow(s) }
                }
            }
        }
    }

    private func sessionRow(_ s: ProjectSession) -> some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(spacing: 2) {
                Text("#\(s.sessionNumber)")
                    .font(.system(size: 13, weight: .bold, design: .rounded))
                    .foregroundColor(AITopTheme.accentOrange)
                Text(shortDate(s.sessionDate))
                    .font(.system(size: 9)).foregroundColor(AITopTheme.textTertiary)
            }
            .frame(width: 64)

            VStack(alignment: .leading, spacing: 4) {
                if !s.summary.isEmpty {
                    Text(s.summary).font(.system(size: 12, weight: .medium))
                        .foregroundColor(AITopTheme.textPrimary).lineLimit(2)
                } else if !s.sessionGoal.isEmpty {
                    Text(s.sessionGoal).font(.system(size: 12, weight: .medium))
                        .foregroundColor(AITopTheme.textPrimary).lineLimit(2)
                }
                HStack(spacing: 10) {
                    if s.durationMinutes > 0 {
                        Label("\(s.durationMinutes)m", systemImage: "clock.fill")
                            .font(.system(size: 10)).foregroundColor(AITopTheme.accentOrange)
                    }
                    if s.gitCommitsCount > 0 {
                        Label("\(s.gitCommitsCount)", systemImage: "arrow.triangle.branch")
                            .font(.system(size: 10)).foregroundColor(AITopTheme.accentCyan)
                    }
                    if s.productivityScore > 0 {
                        Label(String(format: "%.0f/10", s.productivityScore), systemImage: "star.fill")
                            .font(.system(size: 10)).foregroundColor(AITopTheme.warning)
                    }
                    if !s.mood.isEmpty {
                        Text(s.mood).font(.system(size: 10)).foregroundColor(AITopTheme.textTertiary)
                    }
                }
                ForEach(Array(s.accomplishments.prefix(3).enumerated()), id: \.offset) { _, a in
                    bullet(a, color: AITopTheme.success, symbol: "checkmark")
                }
                ForEach(Array(s.blockers.prefix(2).enumerated()), id: \.offset) { _, b in
                    bullet(b, color: AITopTheme.error, symbol: "xmark")
                }
                ForEach(Array(s.nextSteps.prefix(2).enumerated()), id: \.offset) { _, n in
                    bullet(n, color: AITopTheme.accentCyan, symbol: "arrow.right")
                }
            }
            Spacer()
        }
        .padding(AITopTheme.smallSpacing + 2)
        .background(AITopTheme.backgroundMedium)
        .cornerRadius(AITopTheme.smallCornerRadius)
    }

    private func bullet(_ text: String, color: Color, symbol: String) -> some View {
        HStack(alignment: .top, spacing: 5) {
            Image(systemName: symbol).font(.system(size: 8, weight: .bold)).foregroundColor(color)
                .frame(width: 10)
            Text(text).font(.system(size: 10)).foregroundColor(AITopTheme.textSecondary).lineLimit(2)
        }
    }

    private func decisionsCard(_ decisions: [ProjectDecision]) -> some View {
        SectionCard(title: "Technical Decisions", count: decisions.count, systemImage: "ruler.fill") {
            if decisions.isEmpty {
                Text("None recorded").font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
                    ForEach(decisions) { d in
                        VStack(alignment: .leading, spacing: 3) {
                            HStack(spacing: 6) {
                                if !d.category.isEmpty { ChipLabel(text: d.category) }
                                Text(shortDate(d.decidedAt))
                                    .font(.system(size: 9)).foregroundColor(AITopTheme.textTertiary)
                            }
                            Text(d.decisionTitle).font(.system(size: 12, weight: .medium))
                                .foregroundColor(AITopTheme.textPrimary).lineLimit(2)
                            if !d.decisionMade.isEmpty {
                                Text(d.decisionMade).font(.system(size: 10))
                                    .foregroundColor(AITopTheme.textSecondary).lineLimit(2)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.bottom, 2)
                    }
                }
            }
        }
    }

    private func gotchasCard(_ gotchas: [ProjectGotcha]) -> some View {
        SectionCard(title: "Gotchas — ห้ามทำผิดซ้ำ", count: gotchas.count, systemImage: "exclamationmark.shield.fill") {
            if gotchas.isEmpty {
                Text("Clean record 🎉").font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
                    ForEach(gotchas) { g in
                        VStack(alignment: .leading, spacing: 3) {
                            HStack(alignment: .top, spacing: 6) {
                                Image(systemName: severityIcon(g.severity))
                                    .font(.system(size: 11)).foregroundColor(severityColor(g.severity))
                                Text(g.title).font(.system(size: 12, weight: .medium))
                                    .foregroundColor(AITopTheme.textPrimary).lineLimit(2)
                            }
                            if !g.howToPrevent.isEmpty {
                                Text(g.howToPrevent).font(.system(size: 10))
                                    .foregroundColor(AITopTheme.textSecondary).lineLimit(2)
                                    .padding(.leading, 17)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.bottom, 2)
                    }
                }
            }
        }
    }

    private func commitsCard(_ commits: [ProjectCommit]) -> some View {
        SectionCard(title: "Git Commits", count: commits.count, systemImage: "arrow.triangle.branch") {
            if commits.isEmpty {
                Text("No commits").font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(commits) { c in
                        HStack(alignment: .top, spacing: 8) {
                            Text(String(c.commitHash.prefix(7)))
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(AITopTheme.accentOrange)
                            Text(c.commitMessage.components(separatedBy: "\n").first ?? c.commitMessage)
                                .font(.system(size: 11)).foregroundColor(AITopTheme.textSecondary).lineLimit(1)
                            Spacer()
                        }
                    }
                }
            }
        }
    }

    private func milestonesCard(_ milestones: [ProjectMilestone]) -> some View {
        SectionCard(title: "Milestones", count: milestones.count, systemImage: "flag.checkered") {
            if milestones.isEmpty {
                Text("None yet").font(AITopTheme.caption()).foregroundColor(AITopTheme.textTertiary)
            } else {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(milestones) { m in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "checkmark.seal.fill")
                                .font(.system(size: 11)).foregroundColor(AITopTheme.success)
                            VStack(alignment: .leading, spacing: 1) {
                                Text(m.title).font(.system(size: 11, weight: .medium))
                                    .foregroundColor(AITopTheme.textPrimary).lineLimit(2)
                                Text(shortDate(m.achievedAt))
                                    .font(.system(size: 9)).foregroundColor(AITopTheme.textTertiary)
                            }
                            Spacer()
                        }
                    }
                }
            }
        }
    }

    private func techStackCard(_ tags: [String]) -> some View {
        SectionCard(title: "Tech Stack / Tags", count: tags.count, systemImage: "puzzlepiece.fill") {
            FlexibleChips(tags: tags)
        }
    }

    private func load() async {
        isLoading = true
        error = nil
        do {
            detail = try await APIService.shared.getProjectDetail(code: projectCode)
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

/// Simple wrapping chip row.
private struct FlexibleChips: View {
    let tags: [String]

    var body: some View {
        // macOS 13+: a lazy grid of adaptive chips wraps acceptably.
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 70), spacing: 6, alignment: .leading)],
                  alignment: .leading, spacing: 6) {
            ForEach(Array(tags.enumerated()), id: \.offset) { _, t in
                Text(t)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AITopTheme.accentCyan)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(AITopTheme.surfaceBackground)
                    .cornerRadius(6)
            }
        }
    }
}
