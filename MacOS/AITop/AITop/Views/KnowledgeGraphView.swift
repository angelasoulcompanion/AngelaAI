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

                    // Row 2: Network graph (large, interactive) + Knowledge types
                    HStack(alignment: .top, spacing: AITopTheme.spacing) {
                        networkGraphCard(data)
                        knowledgeTypesCard(data)
                    }
                    .frame(height: 500)

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

// MARK: - Force-Directed Network Graph with Zoom/Hover/Drag

private struct GraphNode {
    let id: String
    let label: String
    let kind: NodeKind
    let baseRadius: CGFloat
    let color: Color
    var x: CGFloat
    var y: CGFloat
    var vx: CGFloat = 0
    var vy: CGFloat = 0
    var pinned = false
    enum NodeKind { case project, tech }
}

private struct GraphLink {
    let sourceIdx: Int
    let targetIdx: Int
    let weight: CGFloat
    let dashed: Bool
    let color: Color
}

struct AnimatedNetworkGraph: View {
    let data: KnowledgeGraphResponse
    let projectColors: [Color]
    @Binding var selectedProjectCode: String?

    @State private var nodes: [GraphNode] = []
    @State private var links: [GraphLink] = []
    @State private var time: Double = 0
    @State private var scale: CGFloat = 1.0
    @State private var offset: CGSize = .zero
    @State private var dragNodeIdx: Int? = nil
    @State private var hoveredNodeIdx: Int? = nil
    @State private var lastDragPos: CGPoint = .zero
    @State private var initialized = false

    private let timer = Timer.publish(every: 1.0 / 40.0, on: .main, in: .common).autoconnect()

    private let techTypeColors: [String: Color] = [
        "language": Color(hex: "3B82F6"), "framework": Color(hex: "8B5CF6"),
        "database": Color(hex: "14B8A6"), "library": Color(hex: "6B7280"),
        "ai": Color(hex: "F97316"), "embedding": Color(hex: "EC4899"),
        "auth": Color(hex: "EF4444"), "frontend": Color(hex: "22C55E"),
        "styling": Color(hex: "06B6D4"), "tool": Color(hex: "A3A3A3"),
    ]

    var body: some View {
        GeometryReader { geo in
            let size = geo.size
            Canvas { context, _ in
                let tx = size.width / 2 + offset.width
                let ty = size.height / 2 + offset.height

                // Draw links
                for link in links {
                    guard link.sourceIdx < nodes.count, link.targetIdx < nodes.count else { continue }
                    let s = nodes[link.sourceIdx]
                    let t = nodes[link.targetIdx]
                    let x1 = s.x * scale + tx, y1 = s.y * scale + ty
                    let x2 = t.x * scale + tx, y2 = t.y * scale + ty

                    var path = Path()
                    path.move(to: CGPoint(x: x1, y: y1))
                    path.addLine(to: CGPoint(x: x2, y: y2))

                    if link.dashed {
                        let phase = CGFloat(time.truncatingRemainder(dividingBy: 3.0)) * 8.0
                        context.stroke(path, with: .color(link.color),
                                       style: StrokeStyle(lineWidth: link.weight * scale, dash: [4, 4], dashPhase: phase))
                    } else {
                        context.stroke(path, with: .color(link.color), lineWidth: link.weight * scale)
                    }
                }

                // Draw nodes
                for (i, node) in nodes.enumerated() {
                    let x = node.x * scale + tx
                    let y = node.y * scale + ty
                    let pulse = CGFloat(sin(time * 1.5 + Double(i) * 0.6)) * 1.5 * scale
                    let r = (node.baseRadius + pulse) * scale
                    let isHovered = i == hoveredNodeIdx
                    let isSelected = node.kind == .project && selectedProjectCode == node.id

                    // Glow
                    if isHovered || isSelected {
                        let gr = r + 6 * scale
                        context.fill(Path(ellipseIn: CGRect(x: x - gr, y: y - gr, width: gr * 2, height: gr * 2)),
                                     with: .color(node.color.opacity(0.3)))
                    }

                    // Node
                    context.fill(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                                 with: .color(node.color.opacity(isHovered || isSelected ? 1.0 : 0.8)))

                    // Border
                    context.stroke(Path(ellipseIn: CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)),
                                   with: .color(node.color), lineWidth: isSelected ? 2 : 0.5)

                    // Label
                    let fontSize: CGFloat = node.kind == .project ? 10 : 7
                    let label = Text(node.label)
                        .font(.system(size: fontSize * min(scale, 1.5), weight: node.kind == .project ? .bold : .medium))
                        .foregroundColor(node.kind == .project ? .white : node.color)
                    context.draw(label, at: CGPoint(x: x, y: y + r + 8 * scale))

                    // Count inside project nodes
                    if node.kind == .project && r >= 14 * scale {
                        let countLabel = Text(node.id.hasPrefix("cat_") ? "" : "\(Int(node.baseRadius - 10) * 6)")
                        // Actually show kbCount - find from data
                        if let proj = data.projects.first(where: { $0.code == node.id }) {
                            let ct = Text("\(proj.kbCount)")
                                .font(.system(size: 9 * min(scale, 1.5), weight: .bold, design: .rounded))
                                .foregroundColor(.white.opacity(0.9))
                            context.draw(ct, at: CGPoint(x: x, y: y))
                        }
                    }

                    // Hover tooltip
                    if isHovered && node.kind == .tech {
                        if let tech = (data.techStack ?? []).first(where: { $0.name == node.id }) {
                            let tip = Text("\(tech.name) (\(tech.techType)) — \(tech.projectCount) projects")
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(.white)
                            let bg = Path(roundedRect: CGRect(x: x - 80, y: y - r - 28 * scale, width: 160, height: 20),
                                          cornerRadius: 4)
                            context.fill(bg, with: .color(Color.black.opacity(0.85)))
                            context.draw(tip, at: CGPoint(x: x, y: y - r - 18 * scale))
                        }
                    }
                }
            }
            // Hover tracking
            .onContinuousHover { phase in
                switch phase {
                case .active(let loc):
                    let tx = size.width / 2 + offset.width
                    let ty = size.height / 2 + offset.height
                    hoveredNodeIdx = nil
                    for (i, node) in nodes.enumerated() {
                        let nx = node.x * scale + tx, ny = node.y * scale + ty
                        let r = node.baseRadius * scale + 6
                        if (loc.x - nx) * (loc.x - nx) + (loc.y - ny) * (loc.y - ny) <= r * r {
                            hoveredNodeIdx = i
                            break
                        }
                    }
                case .ended:
                    hoveredNodeIdx = nil
                }
            }
            // Drag nodes or pan
            .gesture(
                DragGesture(minimumDistance: 2)
                    .onChanged { value in
                        let tx = size.width / 2 + offset.width
                        let ty = size.height / 2 + offset.height

                        if dragNodeIdx == nil {
                            // Hit test for drag start
                            let start = value.startLocation
                            for (i, node) in nodes.enumerated() {
                                let nx = node.x * scale + tx, ny = node.y * scale + ty
                                let r = node.baseRadius * scale + 8
                                if (start.x - nx) * (start.x - nx) + (start.y - ny) * (start.y - ny) <= r * r {
                                    dragNodeIdx = i
                                    nodes[i].pinned = true
                                    lastDragPos = value.location
                                    return
                                }
                            }
                            // Pan canvas
                            dragNodeIdx = -1
                            lastDragPos = value.location
                        }

                        if let idx = dragNodeIdx, idx >= 0, idx < nodes.count {
                            let dx = (value.location.x - lastDragPos.x) / scale
                            let dy = (value.location.y - lastDragPos.y) / scale
                            nodes[idx].x += dx
                            nodes[idx].y += dy
                            lastDragPos = value.location
                        } else if dragNodeIdx == -1 {
                            let dx = value.location.x - lastDragPos.x
                            let dy = value.location.y - lastDragPos.y
                            offset.width += dx
                            offset.height += dy
                            lastDragPos = value.location
                        }
                    }
                    .onEnded { _ in
                        if let idx = dragNodeIdx, idx >= 0, idx < nodes.count {
                            nodes[idx].pinned = false
                        }
                        dragNodeIdx = nil
                    }
            )
            // Zoom
            .gesture(
                MagnificationGesture()
                    .onChanged { value in
                        scale = max(0.3, min(3.0, value))
                    }
            )
            // Click to select project
            .onTapGesture { location in
                let tx = size.width / 2 + offset.width
                let ty = size.height / 2 + offset.height
                for node in nodes where node.kind == .project {
                    let nx = node.x * scale + tx, ny = node.y * scale + ty
                    let r = node.baseRadius * scale + 8
                    if (location.x - nx) * (location.x - nx) + (location.y - ny) * (location.y - ny) <= r * r {
                        withAnimation { selectedProjectCode = selectedProjectCode == node.id ? nil : node.id }
                        return
                    }
                }
                selectedProjectCode = nil
            }
        }
        .onReceive(timer) { _ in
            time += 1.0 / 40.0
            simulateForces()
        }
        .onAppear { buildGraph() }
        .onChange(of: data.projects.count) { _ in buildGraph() }
    }

    // MARK: - Build graph from data

    private func buildGraph() {
        guard !initialized else { return }
        initialized = true
        var newNodes: [GraphNode] = []
        var newLinks: [GraphLink] = []

        let activeProjects = data.projects.filter { $0.kbCount > 0 || $0.hours > 0 }
        let sharedTechs = (data.techStack ?? []).filter { $0.projectCount >= 2 }

        // Project nodes in circle
        for (i, project) in activeProjects.enumerated() {
            let angle = 2.0 * .pi * Double(i) / Double(max(activeProjects.count, 1)) - .pi / 2
            let r: CGFloat = 180
            newNodes.append(GraphNode(
                id: project.code, label: project.code, kind: .project,
                baseRadius: max(16, min(34, CGFloat(project.kbCount) / 5.0 + 14)),
                color: projectColors[i % projectColors.count],
                x: r * cos(angle), y: r * sin(angle)
            ))
        }

        // Tech nodes scattered near center
        for (ti, tech) in sharedTechs.enumerated() {
            let angle = 2.0 * .pi * Double(ti) / Double(max(sharedTechs.count, 1))
            let r: CGFloat = 70 + CGFloat.random(in: -20...20)
            newNodes.append(GraphNode(
                id: tech.name, label: tech.name, kind: .tech,
                baseRadius: max(4, min(10, CGFloat(tech.projectCount) * 2.5)),
                color: techTypeColors[tech.techType] ?? AITopTheme.textTertiary,
                x: r * cos(angle), y: r * sin(angle)
            ))

            // Links from tech to each project
            let techIdx = newNodes.count - 1
            for projectCode in tech.projects {
                if let pi = newNodes.firstIndex(where: { $0.id == projectCode }) {
                    newLinks.append(GraphLink(
                        sourceIdx: techIdx, targetIdx: pi, weight: 0.7,
                        dashed: true, color: (techTypeColors[tech.techType] ?? AITopTheme.textTertiary).opacity(0.2)
                    ))
                }
            }
        }

        // Project-to-project edges
        for edge in data.edges {
            if let si = newNodes.firstIndex(where: { $0.id == edge.fromProject }),
               let ti = newNodes.firstIndex(where: { $0.id == edge.toProject }) {
                newLinks.append(GraphLink(
                    sourceIdx: si, targetIdx: ti,
                    weight: max(1.5, min(4, CGFloat(edge.sharedCount) * 0.4)),
                    dashed: false,
                    color: AITopTheme.accentOrange.opacity(min(0.4, Double(edge.sharedCount) * 0.05 + 0.08))
                ))
            }
        }

        nodes = newNodes
        links = newLinks
    }

    // MARK: - Force simulation

    private func simulateForces() {
        guard nodes.count > 1 else { return }
        let alpha: CGFloat = 0.3

        for i in nodes.indices {
            guard !nodes[i].pinned else { continue }
            var fx: CGFloat = 0, fy: CGFloat = 0

            // Repulsion
            for j in nodes.indices where i != j {
                let dx = nodes[i].x - nodes[j].x
                let dy = nodes[i].y - nodes[j].y
                let dist = max(sqrt(dx * dx + dy * dy), 1)
                let repulse: CGFloat = nodes[i].kind == .project ? 5000 : 1500
                fx += (dx / dist) * repulse / (dist * dist) * alpha
                fy += (dy / dist) * repulse / (dist * dist) * alpha
            }

            // Center gravity
            fx -= nodes[i].x * 0.003 * alpha
            fy -= nodes[i].y * 0.003 * alpha

            nodes[i].vx = (nodes[i].vx + fx) * 0.6
            nodes[i].vy = (nodes[i].vy + fy) * 0.6
        }

        // Spring attraction along links
        for link in links {
            let si = link.sourceIdx, ti = link.targetIdx
            guard si < nodes.count, ti < nodes.count else { continue }
            let dx = nodes[ti].x - nodes[si].x
            let dy = nodes[ti].y - nodes[si].y
            let dist = max(sqrt(dx * dx + dy * dy), 1)
            let target: CGFloat = nodes[si].kind == .project && nodes[ti].kind == .project ? 200 : 100
            let force = (dist - target) * 0.003 * alpha

            if !nodes[si].pinned {
                nodes[si].vx += (dx / dist) * force
                nodes[si].vy += (dy / dist) * force
            }
            if !nodes[ti].pinned {
                nodes[ti].vx -= (dx / dist) * force
                nodes[ti].vy -= (dy / dist) * force
            }
        }

        // Apply velocity
        for i in nodes.indices where !nodes[i].pinned {
            nodes[i].x += nodes[i].vx
            nodes[i].y += nodes[i].vy
        }
    }
}
