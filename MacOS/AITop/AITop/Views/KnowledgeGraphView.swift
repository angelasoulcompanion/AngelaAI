//
//  KnowledgeGraphView.swift
//  AITop
//
//  Cross-project knowledge overview with compact network graph
//  and detailed project cards.
//

import SwiftUI
import Charts

// MARK: - Knowledge Graph View

struct KnowledgeGraphView: View {
    @EnvironmentObject var apiService: APIService
    @State private var graphData: KnowledgeGraphResponse?
    @State private var isLoading = true
    @State private var error: String?
    @State private var selectedProjectCode: String?

    private let projectColors: [Color] = [
        AITopTheme.accentOrange, AITopTheme.accentCyan,
        Color(hex: "EC4899"), AITopTheme.success,
        AITopTheme.warning, AITopTheme.info,
        Color(hex: "8B5CF6"), Color(hex: "F97316"),
        Color(hex: "14B8A6"), Color(hex: "EF4444"),
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: AITopTheme.spacing) {
                headerSection

                if isLoading {
                    ProgressView("Loading knowledge graph...")
                        .foregroundColor(AITopTheme.textSecondary)
                        .frame(maxWidth: .infinity, minHeight: 200)
                } else if let error {
                    errorView(error)
                } else if let data = graphData {
                    // Row 1: Summary stats
                    summaryRow(data)

                    // Row 2: Network graph (compact) + Knowledge types
                    HStack(alignment: .top, spacing: AITopTheme.spacing) {
                        networkGraphCard(data)
                        knowledgeTypesCard(data)
                    }
                    .frame(height: 360)

                    // Row 3: Project cards grid
                    projectCardsSection(data)
                }
            }
            .padding(AITopTheme.largeSpacing)
        }
        .background(AITopTheme.backgroundDark)
        .onAppear { loadData() }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Knowledge Graph")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                if let data = graphData {
                    Text("\(data.projects.count) projects  |  \(totalKB(data)) knowledge entries  |  \(data.edges.count) cross-project links")
                        .font(AITopTheme.body())
                        .foregroundColor(AITopTheme.textSecondary)
                }
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

    // MARK: - Summary Row

    private func summaryRow(_ data: KnowledgeGraphResponse) -> some View {
        HStack(spacing: AITopTheme.smallSpacing) {
            summaryCard("Total KB", value: "\(totalKB(data))", icon: "brain.fill", color: AITopTheme.accentCyan)
            summaryCard("Projects", value: "\(data.projects.count)", icon: "folder.fill", color: AITopTheme.accentOrange)
            summaryCard("Categories", value: "\(data.categories.count)", icon: "tag.fill", color: AITopTheme.success)
            summaryCard("Cross Links", value: "\(data.edges.count)", icon: "link", color: AITopTheme.info)
            summaryCard("Types", value: "\(data.typeBreakdown.count)", icon: "square.grid.2x2.fill", color: Color(hex: "8B5CF6"))
            summaryCard("Total Hours", value: String(format: "%.0f", data.projects.map(\.hours).reduce(0, +)), icon: "clock.fill", color: AITopTheme.warning)
        }
    }

    private func summaryCard(_ title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(color)
            Text(value)
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundStyle(LinearGradient(colors: [color, color.opacity(0.7)], startPoint: .top, endPoint: .bottom))
            Text(title)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(AITopTheme.smallSpacing)
        .aiTopCard()
    }

    // MARK: - Network Graph Card (projects + tech stack with animation)

    private func networkGraphCard(_ data: KnowledgeGraphResponse) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            HStack {
                Text("Project × Tech Stack Network")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                Text("\(data.techStack?.filter { $0.projectCount >= 2 }.count ?? 0) shared techs")
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textTertiary)
            }

            AnimatedNetworkGraph(data: data, projectColors: projectColors, selectedProjectCode: $selectedProjectCode)
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
        .frame(maxWidth: .infinity)
    }

    // MARK: - Knowledge Types Card

    private func knowledgeTypesCard(_ data: KnowledgeGraphResponse) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Knowledge Types")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            Chart(data.typeBreakdown) { item in
                BarMark(
                    x: .value("Count", item.count),
                    y: .value("Type", item.type)
                )
                .foregroundStyle(typeColor(item.type).gradient)
                .cornerRadius(3)
                .annotation(position: .trailing, spacing: 4) {
                    Text("\(item.count)")
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(AITopTheme.textTertiary)
                }
            }
            .chartXAxis(.hidden)
            .chartYAxis {
                AxisMarks { value in
                    AxisValueLabel()
                        .font(.system(size: 11))
                        .foregroundStyle(AITopTheme.textSecondary)
                }
            }
            .frame(maxHeight: .infinity)

            // Top cross-project links
            AITopDivider()

            Text("Top Cross-Project Links")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(AITopTheme.textPrimary)

            ForEach(data.edges.prefix(5)) { edge in
                HStack(spacing: 4) {
                    Text(edge.fromProject)
                        .font(.system(size: 9, weight: .semibold, design: .monospaced))
                        .foregroundColor(AITopTheme.accentOrange)
                    Image(systemName: "arrow.left.arrow.right")
                        .font(.system(size: 7))
                        .foregroundColor(AITopTheme.textTertiary)
                    Text(edge.toProject)
                        .font(.system(size: 9, weight: .semibold, design: .monospaced))
                        .foregroundColor(AITopTheme.accentCyan)
                    Spacer()
                    Text("\(edge.sharedCount) shared")
                        .font(.system(size: 9))
                        .foregroundColor(AITopTheme.textTertiary)
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
        .frame(width: 300)
    }

    // MARK: - Project Cards Grid

    private func projectCardsSection(_ data: KnowledgeGraphResponse) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Projects")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AITopTheme.smallSpacing) {
                ForEach(Array(data.projects.enumerated()), id: \.element.id) { idx, project in
                    projectCard(project, color: projectColors[idx % projectColors.count])
                }
            }
        }
    }

    private func projectCard(_ p: GraphProject, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header: name + status
            HStack {
                Circle().fill(color).frame(width: 10, height: 10)
                Text(p.code)
                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                if let status = p.status {
                    Text(status)
                        .font(.system(size: 9, weight: .medium))
                        .foregroundColor(status == "active" ? AITopTheme.success : AITopTheme.textTertiary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background((status == "active" ? AITopTheme.success : AITopTheme.textTertiary).opacity(0.15))
                        .cornerRadius(3)
                }
            }

            Text(p.name)
                .font(.system(size: 11))
                .foregroundColor(AITopTheme.textSecondary)
                .lineLimit(1)

            // Stats row
            HStack(spacing: 12) {
                Label("\(p.kbCount)", systemImage: "brain.fill")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AITopTheme.accentCyan)
                Label("\(p.sessions ?? 0)", systemImage: "square.stack.fill")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AITopTheme.accentOrange)
                Label(String(format: "%.0fh", p.hours), systemImage: "clock.fill")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AITopTheme.warning)
                Spacer()
            }

            // Knowledge breakdown mini bar
            if let breakdown = p.typeBreakdown {
                let items = breakdown.sorted { $0.value > $1.value }.filter { $0.value > 0 }
                let total = max(items.map(\.value).reduce(0, +), 1)

                if !items.isEmpty {
                    GeometryReader { geo in
                        HStack(spacing: 1) {
                            ForEach(items, id: \.key) { type, count in
                                RoundedRectangle(cornerRadius: 2)
                                    .fill(typeColor(type))
                                    .frame(width: max(4, geo.size.width * CGFloat(count) / CGFloat(total)))
                            }
                        }
                    }
                    .frame(height: 6)
                    .clipShape(RoundedRectangle(cornerRadius: 3))

                    // Type labels
                    HStack(spacing: 8) {
                        ForEach(items.prefix(4), id: \.key) { type, count in
                            HStack(spacing: 3) {
                                Circle().fill(typeColor(type)).frame(width: 5, height: 5)
                                Text("\(type) \(count)")
                                    .font(.system(size: 8))
                                    .foregroundColor(AITopTheme.textTertiary)
                            }
                        }
                        Spacer()
                    }
                }
            }

            // Dates
            HStack(spacing: 12) {
                if let created = p.createdAt {
                    HStack(spacing: 3) {
                        Image(systemName: "calendar")
                            .font(.system(size: 8))
                        Text(formatDate(created))
                            .font(.system(size: 9, design: .monospaced))
                    }
                    .foregroundColor(AITopTheme.textTertiary)
                }
                if let lastKB = p.lastKnowledgeAt {
                    HStack(spacing: 3) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: 8))
                        Text(formatDate(lastKB))
                            .font(.system(size: 9, design: .monospaced))
                    }
                    .foregroundColor(AITopTheme.textTertiary)
                }
                Spacer()
            }
        }
        .padding(AITopTheme.smallSpacing + 4)
        .background(selectedProjectCode == p.code ? color.opacity(0.08) : AITopTheme.cardBackground)
        .cornerRadius(AITopTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AITopTheme.cornerRadius)
                .stroke(selectedProjectCode == p.code ? color.opacity(0.5) : Color.clear, lineWidth: 1)
        )
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                selectedProjectCode = selectedProjectCode == p.code ? nil : p.code
            }
        }
    }

    // MARK: - Error

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
        error = nil
        Task {
            do {
                let result: KnowledgeGraphResponse = try await apiService.get("/angela-brain/knowledge-graph")
                await MainActor.run {
                    graphData = result
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

    private func totalKB(_ data: KnowledgeGraphResponse) -> Int {
        data.typeBreakdown.map(\.count).reduce(0, +)
    }

    private func formatDate(_ iso: String?) -> String {
        guard let iso, iso.count >= 10 else { return "-" }
        return String(iso.prefix(10))
    }

    private func circleLayout(count: Int, center: CGPoint, radius: CGFloat) -> [CGPoint] {
        (0..<count).map { i in
            let angle = 2.0 * .pi * Double(i) / Double(max(count, 1)) - .pi / 2
            return CGPoint(x: center.x + radius * cos(angle), y: center.y + radius * sin(angle))
        }
    }

    private func typeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "learning": return AITopTheme.accentCyan
        case "gotcha": return AITopTheme.error
        case "pattern": return AITopTheme.success
        case "workflow": return AITopTheme.warning
        case "decision": return AITopTheme.info
        case "standard": return Color(hex: "8B5CF6")
        case "preference": return Color(hex: "EC4899")
        case "technique": return AITopTheme.accentOrange
        case "ui_pattern": return Color(hex: "14B8A6")
        default: return AITopTheme.textTertiary
        }
    }
}

// MARK: - Animated Network Graph

struct AnimatedNetworkGraph: View {
    let data: KnowledgeGraphResponse
    let projectColors: [Color]
    @Binding var selectedProjectCode: String?

    private let techTypeColors: [String: Color] = [
        "language": Color(hex: "3B82F6"),
        "framework": Color(hex: "8B5CF6"),
        "database": Color(hex: "14B8A6"),
        "library": Color(hex: "6B7280"),
        "ai": Color(hex: "F97316"),
        "embedding": Color(hex: "EC4899"),
        "auth": Color(hex: "EF4444"),
        "frontend": Color(hex: "22C55E"),
        "styling": Color(hex: "06B6D4"),
        "tool": Color(hex: "A3A3A3"),
        "ocr": Color(hex: "D97706"),
    ]

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0)) { timeline in
            GeometryReader { geo in
                let time = timeline.date.timeIntervalSinceReferenceDate
                let size = geo.size
                let cx = size.width / 2
                let cy = size.height / 2

                let activeProjects = data.projects.filter { $0.kbCount > 0 || $0.hours > 0 }
                let sharedTechs = (data.techStack ?? []).filter { $0.projectCount >= 2 }

                // Layout: projects in outer ring, tech in inner ring
                let pRadius = min(cx, cy) * 0.75
                let tRadius = min(cx, cy) * 0.35
                let pPositions = circleLayout(count: activeProjects.count, center: CGPoint(x: cx, y: cy), radius: pRadius)
                let tPositions = circleLayout(count: sharedTechs.count, center: CGPoint(x: cx, y: cy), radius: tRadius)

                Canvas { context, _ in
                    // 1. Draw tech-to-project links (animated pulse)
                    for (ti, tech) in sharedTechs.enumerated() {
                        let tPos = tPositions[ti]
                        for projectCode in tech.projects {
                            guard let pi = activeProjects.firstIndex(where: { $0.code == projectCode }) else { continue }
                            let pPos = pPositions[pi]

                            // Animated dash phase
                            let phase = CGFloat(time.truncatingRemainder(dividingBy: 3.0)) * 8.0
                            var path = Path()
                            path.move(to: tPos)
                            path.addLine(to: pPos)

                            let isHighlighted = selectedProjectCode == projectCode
                            let baseOpacity = isHighlighted ? 0.4 : 0.12
                            let color = techTypeColors[tech.techType] ?? AITopTheme.textTertiary

                            context.stroke(
                                path,
                                with: .color(color.opacity(baseOpacity)),
                                style: StrokeStyle(lineWidth: isHighlighted ? 1.5 : 0.7, dash: [4, 4], dashPhase: phase)
                            )
                        }
                    }

                    // 2. Draw project-to-project edges (solid, shared knowledge)
                    for edge in data.edges {
                        guard let si = activeProjects.firstIndex(where: { $0.code == edge.fromProject }),
                              let ti = activeProjects.firstIndex(where: { $0.code == edge.toProject }) else { continue }
                        var path = Path()
                        path.move(to: pPositions[si])
                        path.addLine(to: pPositions[ti])
                        let w = max(1.5, min(4, CGFloat(edge.sharedCount) * 0.4))
                        let opacity = min(0.4, Double(edge.sharedCount) * 0.05 + 0.08)
                        context.stroke(path, with: .color(AITopTheme.accentOrange.opacity(opacity)), lineWidth: w)
                    }

                    // 3. Draw tech nodes (inner ring, small with pulse)
                    for (ti, tech) in sharedTechs.enumerated() {
                        let pos = tPositions[ti]
                        let baseR: CGFloat = max(4, min(10, CGFloat(tech.projectCount) * 2.5))
                        // Gentle pulse animation
                        let pulse = CGFloat(sin(time * 2.0 + Double(ti) * 0.5)) * 1.5
                        let r = baseR + pulse
                        let color = techTypeColors[tech.techType] ?? AITopTheme.textTertiary

                        // Glow
                        context.fill(
                            Path(ellipseIn: CGRect(x: pos.x - r - 3, y: pos.y - r - 3, width: (r + 3) * 2, height: (r + 3) * 2)),
                            with: .color(color.opacity(0.15))
                        )
                        // Node
                        context.fill(
                            Path(ellipseIn: CGRect(x: pos.x - r, y: pos.y - r, width: r * 2, height: r * 2)),
                            with: .color(color.opacity(0.85))
                        )
                        // Label
                        let label = Text(tech.name)
                            .font(.system(size: 7, weight: .medium))
                            .foregroundColor(color)
                        context.draw(label, at: CGPoint(x: pos.x, y: pos.y + r + 7))
                    }

                    // 4. Draw project nodes (outer ring, large with breathing)
                    for (i, project) in activeProjects.enumerated() {
                        let pos = pPositions[i]
                        let baseR = max(14, min(32, CGFloat(project.kbCount) / 6.0 + 12))
                        let breath = CGFloat(sin(time * 1.2 + Double(i) * 0.8)) * 1.5
                        let r = baseR + breath
                        let color = projectColors[i % projectColors.count]
                        let isSelected = selectedProjectCode == project.code

                        // Outer glow (stronger for selected)
                        let glowR = r + (isSelected ? 8 : 4)
                        context.fill(
                            Path(ellipseIn: CGRect(x: pos.x - glowR, y: pos.y - glowR, width: glowR * 2, height: glowR * 2)),
                            with: .color(color.opacity(isSelected ? 0.25 : 0.1))
                        )

                        // Node
                        context.fill(
                            Path(ellipseIn: CGRect(x: pos.x - r, y: pos.y - r, width: r * 2, height: r * 2)),
                            with: .color(color.opacity(isSelected ? 1.0 : 0.85))
                        )

                        // Border ring
                        context.stroke(
                            Path(ellipseIn: CGRect(x: pos.x - r, y: pos.y - r, width: r * 2, height: r * 2)),
                            with: .color(color), lineWidth: isSelected ? 2 : 0.5
                        )

                        // Label below
                        let nameLabel = Text(project.code)
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.white)
                        context.draw(nameLabel, at: CGPoint(x: pos.x, y: pos.y + r + 12))

                        // KB count inside
                        if r >= 16 {
                            let countLabel = Text("\(project.kbCount)")
                                .font(.system(size: 9, weight: .bold, design: .rounded))
                                .foregroundColor(.white.opacity(0.9))
                            context.draw(countLabel, at: pos)
                        }
                    }
                }
                .onTapGesture { location in
                    for (i, project) in activeProjects.enumerated() {
                        let pos = pPositions[i]
                        let r = max(14, min(32, CGFloat(project.kbCount) / 6.0 + 12)) + 8
                        let dx = location.x - pos.x
                        let dy = location.y - pos.y
                        if dx * dx + dy * dy <= r * r {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                selectedProjectCode = selectedProjectCode == project.code ? nil : project.code
                            }
                            return
                        }
                    }
                    selectedProjectCode = nil
                }
            }
        }
    }

    private func circleLayout(count: Int, center: CGPoint, radius: CGFloat) -> [CGPoint] {
        (0..<count).map { i in
            let angle = 2.0 * .pi * Double(i) / Double(max(count, 1)) - .pi / 2
            return CGPoint(x: center.x + radius * cos(angle), y: center.y + radius * sin(angle))
        }
    }
}
