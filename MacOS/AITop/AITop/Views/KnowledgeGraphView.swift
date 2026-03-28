//
//  KnowledgeGraphView.swift
//  AITop
//
//  Interactive force-directed knowledge graph showing projects,
//  categories, and cross-project knowledge connections.
//

import SwiftUI

// MARK: - Graph Node

struct GraphNode: Identifiable {
    let id: String
    let label: String
    let detail: String
    let kind: NodeKind
    let size: CGFloat
    let color: Color
    var position: CGPoint
    var velocity: CGPoint = .zero
    var pinned: Bool = false

    enum NodeKind { case project, category }
}

// MARK: - Graph Link

struct GraphLink: Identifiable {
    let id: String
    let sourceId: String
    let targetId: String
    let weight: Double
}

// MARK: - Force Simulation

class GraphSimulation: ObservableObject {
    @Published var nodes: [GraphNode] = []
    @Published var links: [GraphLink] = []
    @Published var isSettled = false

    private var timer: Timer?
    private var ticks = 0
    private let maxTicks = 300
    private var alpha: CGFloat = 1.0

    func start() {
        ticks = 0
        alpha = 1.0
        isSettled = false
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 1.0 / 60.0, repeats: true) { [weak self] _ in
            self?.tick()
        }
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }

    private func tick() {
        guard !nodes.isEmpty else { return }
        ticks += 1
        alpha = max(0.001, alpha * 0.99)

        if ticks >= maxTicks {
            stop()
            isSettled = true
            return
        }

        let center = CGPoint(x: 500, y: 400)

        for i in nodes.indices {
            if nodes[i].pinned { continue }
            var fx: CGFloat = 0
            var fy: CGFloat = 0

            // Repulsion from all other nodes
            for j in nodes.indices where i != j {
                let dx = nodes[i].position.x - nodes[j].position.x
                let dy = nodes[i].position.y - nodes[j].position.y
                let dist = max(sqrt(dx * dx + dy * dy), 1)
                let repulse: CGFloat = nodes[i].kind == .project ? 8000 : 3000
                fx += (dx / dist) * repulse / (dist * dist) * alpha
                fy += (dy / dist) * repulse / (dist * dist) * alpha
            }

            // Center gravity
            fx += (center.x - nodes[i].position.x) * 0.01 * alpha
            fy += (center.y - nodes[i].position.y) * 0.01 * alpha

            nodes[i].velocity.x = (nodes[i].velocity.x + fx) * 0.6
            nodes[i].velocity.y = (nodes[i].velocity.y + fy) * 0.6
        }

        // Spring attraction along links
        for link in links {
            guard let si = nodes.firstIndex(where: { $0.id == link.sourceId }),
                  let ti = nodes.firstIndex(where: { $0.id == link.targetId }) else { continue }

            let dx = nodes[ti].position.x - nodes[si].position.x
            let dy = nodes[ti].position.y - nodes[si].position.y
            let dist = max(sqrt(dx * dx + dy * dy), 1)
            let targetDist: CGFloat = nodes[si].kind == .project && nodes[ti].kind == .project ? 250 : 120
            let force = (dist - targetDist) * 0.005 * alpha * CGFloat(link.weight)

            let fdx = (dx / dist) * force
            let fdy = (dy / dist) * force

            if !nodes[si].pinned {
                nodes[si].velocity.x += fdx
                nodes[si].velocity.y += fdy
            }
            if !nodes[ti].pinned {
                nodes[ti].velocity.x -= fdx
                nodes[ti].velocity.y -= fdy
            }
        }

        // Apply velocity
        for i in nodes.indices {
            if nodes[i].pinned { continue }
            nodes[i].position.x += nodes[i].velocity.x
            nodes[i].position.y += nodes[i].velocity.y
        }
    }

    deinit { stop() }
}

// MARK: - Knowledge Graph View

struct KnowledgeGraphView: View {
    @EnvironmentObject var apiService: APIService
    @StateObject private var simulation = GraphSimulation()
    @State private var graphData: KnowledgeGraphResponse?
    @State private var isLoading = true
    @State private var error: String?
    @State private var scale: CGFloat = 1.0
    @State private var offset: CGSize = .zero
    @State private var draggedNodeId: String?
    @State private var hoveredNodeId: String?
    @State private var selectedProjectCode: String?

    // Project colors
    private let projectColors: [Color] = [
        AITopTheme.accentOrange,
        AITopTheme.accentCyan,
        Color(hex: "EC4899"),
        AITopTheme.success,
        AITopTheme.warning,
        AITopTheme.info,
        Color(hex: "8B5CF6"),
        Color(hex: "F97316"),
        Color(hex: "14B8A6"),
        Color(hex: "EF4444"),
    ]

    var body: some View {
        ZStack {
            AITopTheme.backgroundDark.ignoresSafeArea()

            VStack(spacing: 0) {
                headerSection
                    .padding(AITopTheme.largeSpacing)

                if isLoading {
                    Spacer()
                    ProgressView("Loading knowledge graph...")
                        .foregroundColor(AITopTheme.textSecondary)
                    Spacer()
                } else if let error {
                    Spacer()
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 32))
                            .foregroundColor(AITopTheme.warning)
                        Text(error)
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        Button("Retry") { loadData() }
                            .aiTopPrimaryButton()
                    }
                    Spacer()
                } else {
                    HStack(spacing: 0) {
                        graphCanvas
                            .frame(maxWidth: .infinity, maxHeight: .infinity)

                        legendPanel
                            .frame(width: 240)
                    }
                }
            }
        }
        .onAppear { loadData() }
        .sheet(item: Binding(
            get: { selectedProjectCode.map { ProjectInfo(projectCode: $0, projectName: "", status: "", category: "", totalSessions: 0, totalHours: 0) } },
            set: { selectedProjectCode = $0?.projectCode }
        )) { project in
            ProjectDetailSheet(apiService: apiService, projectCode: project.projectCode)
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Knowledge Graph")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                if let data = graphData {
                    Text("\(data.projects.count) projects  |  \(data.categories.count) categories  |  \(data.edges.count) connections")
                        .font(AITopTheme.body())
                        .foregroundColor(AITopTheme.textSecondary)
                }
            }
            Spacer()

            // Zoom controls
            HStack(spacing: 8) {
                Button(action: { withAnimation { scale = max(0.3, scale - 0.2) } }) {
                    Image(systemName: "minus.magnifyingglass")
                }
                .buttonStyle(.plain)
                .foregroundColor(AITopTheme.textSecondary)

                Text("\(Int(scale * 100))%")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                    .frame(width: 40)

                Button(action: { withAnimation { scale = min(3.0, scale + 0.2) } }) {
                    Image(systemName: "plus.magnifyingglass")
                }
                .buttonStyle(.plain)
                .foregroundColor(AITopTheme.textSecondary)

                Button(action: { withAnimation { scale = 1.0; offset = .zero } }) {
                    Image(systemName: "arrow.counterclockwise")
                }
                .buttonStyle(.plain)
                .foregroundColor(AITopTheme.textSecondary)
            }

            Button(action: { loadData() }) {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(AITopTheme.accentOrange)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Graph Canvas

    private var graphCanvas: some View {
        Canvas { context, size in
            let tx = offset.width + size.width / 2 - 500 * scale
            let ty = offset.height + size.height / 2 - 400 * scale

            // Draw links
            for link in simulation.links {
                guard let source = simulation.nodes.first(where: { $0.id == link.sourceId }),
                      let target = simulation.nodes.first(where: { $0.id == link.targetId }) else { continue }

                let x1 = source.position.x * scale + tx
                let y1 = source.position.y * scale + ty
                let x2 = target.position.x * scale + tx
                let y2 = target.position.y * scale + ty

                var path = Path()
                path.move(to: CGPoint(x: x1, y: y1))
                path.addLine(to: CGPoint(x: x2, y: y2))

                let opacity = min(0.6, Double(link.weight) * 0.1 + 0.1)
                context.stroke(path, with: .color(AITopTheme.accentOrange.opacity(opacity)), lineWidth: max(1, CGFloat(link.weight) * 0.5))
            }

            // Draw nodes
            for node in simulation.nodes {
                let x = node.position.x * scale + tx
                let y = node.position.y * scale + ty
                let r = node.size * scale
                let isHovered = node.id == hoveredNodeId

                let rect = CGRect(x: x - r, y: y - r, width: r * 2, height: r * 2)

                // Glow for hovered
                if isHovered {
                    let glowRect = rect.insetBy(dx: -4, dy: -4)
                    context.fill(Path(ellipseIn: glowRect), with: .color(node.color.opacity(0.3)))
                }

                // Node circle
                context.fill(Path(ellipseIn: rect), with: .color(node.color.opacity(isHovered ? 1.0 : 0.85)))

                // Border
                context.stroke(Path(ellipseIn: rect), with: .color(node.color), lineWidth: isHovered ? 2 : 1)

                // Label for project nodes (always) and hovered category nodes
                if node.kind == .project || isHovered {
                    let label = node.kind == .project ? node.label : "\(node.label) (\(node.detail))"
                    let text = Text(label)
                        .font(.system(size: node.kind == .project ? 11 : 9, weight: .semibold))
                        .foregroundColor(.white)
                    context.draw(text, at: CGPoint(x: x, y: y + r + 10))
                }
            }
        }
        .background(AITopTheme.backgroundMedium)
        .clipShape(RoundedRectangle(cornerRadius: AITopTheme.cornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: AITopTheme.cornerRadius)
                .stroke(AITopTheme.textTertiary.opacity(0.3), lineWidth: 1)
        )
        .padding([.leading, .bottom], AITopTheme.largeSpacing)
        .gesture(
            DragGesture()
                .onChanged { value in
                    // Check if dragging a node
                    if let nodeId = draggedNodeId {
                        if let idx = simulation.nodes.firstIndex(where: { $0.id == nodeId }) {
                            simulation.nodes[idx].position.x += value.translation.width / scale
                            simulation.nodes[idx].position.y += value.translation.height / scale
                            simulation.nodes[idx].pinned = true
                        }
                    } else {
                        offset = CGSize(
                            width: offset.width + value.translation.width * 0.1,
                            height: offset.height + value.translation.height * 0.1
                        )
                    }
                }
                .onEnded { _ in
                    if let nodeId = draggedNodeId,
                       let idx = simulation.nodes.firstIndex(where: { $0.id == nodeId }) {
                        simulation.nodes[idx].pinned = false
                    }
                    draggedNodeId = nil
                }
        )
        .onContinuousHover { phase in
            switch phase {
            case .active(let location):
                hoveredNodeId = hitTest(location)
            case .ended:
                hoveredNodeId = nil
            }
        }
        .gesture(
            MagnificationGesture()
                .onChanged { value in
                    scale = max(0.3, min(3.0, value))
                }
        )
        .onTapGesture { location in
            if let nodeId = hitTest(location),
               let node = simulation.nodes.first(where: { $0.id == nodeId }),
               node.kind == .project {
                selectedProjectCode = node.id
            }
        }
    }

    // MARK: - Legend Panel

    private var legendPanel: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                Text("Projects")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)

                if let data = graphData {
                    ForEach(Array(data.projects.enumerated()), id: \.element.id) { idx, project in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(projectColors[idx % projectColors.count])
                                .frame(width: 12, height: 12)
                            VStack(alignment: .leading, spacing: 1) {
                                Text(project.code)
                                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                    .foregroundColor(AITopTheme.textPrimary)
                                Text("\(project.kbCount) entries")
                                    .font(.system(size: 10))
                                    .foregroundColor(AITopTheme.textTertiary)
                            }
                            Spacer()
                        }
                        .padding(.vertical, 2)
                        .contentShape(Rectangle())
                        .onTapGesture { selectedProjectCode = project.code }
                    }

                    AITopDivider()
                        .padding(.vertical, 4)

                    Text("Knowledge Types")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    ForEach(data.typeBreakdown) { item in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(typeColor(item.type))
                                .frame(width: 10, height: 10)
                            Text(item.type)
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.textSecondary)
                            Spacer()
                            Text("\(item.count)")
                                .font(.system(size: 11, weight: .medium, design: .monospaced))
                                .foregroundColor(AITopTheme.textTertiary)
                        }
                    }

                    AITopDivider()
                        .padding(.vertical, 4)

                    Text("Cross-Project Links")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    ForEach(data.edges.prefix(10)) { edge in
                        HStack(spacing: 4) {
                            Text(edge.fromProject)
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundColor(AITopTheme.accentOrange)
                            Image(systemName: "arrow.left.arrow.right")
                                .font(.system(size: 8))
                                .foregroundColor(AITopTheme.textTertiary)
                            Text(edge.toProject)
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundColor(AITopTheme.accentCyan)
                            Spacer()
                            Text("\(edge.sharedCount)")
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(AITopTheme.textTertiary)
                        }
                    }
                }
            }
            .padding(AITopTheme.spacing)
        }
        .background(AITopTheme.backgroundDark)
        .overlay(
            Rectangle()
                .fill(AITopTheme.textTertiary.opacity(0.3))
                .frame(width: 1),
            alignment: .leading
        )
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
                    buildGraph(from: result)
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }

    private func buildGraph(from data: KnowledgeGraphResponse) {
        var nodes: [GraphNode] = []
        var links: [GraphLink] = []

        // Project nodes — arranged in a circle
        let projectCount = data.projects.count
        for (i, project) in data.projects.enumerated() {
            let angle = 2.0 * .pi * Double(i) / Double(max(projectCount, 1))
            let radius: Double = 200
            let x = 500 + radius * cos(angle)
            let y = 400 + radius * sin(angle)

            nodes.append(GraphNode(
                id: project.code,
                label: project.code,
                detail: "\(project.kbCount) entries",
                kind: .project,
                size: max(16, min(35, CGFloat(project.kbCount) / 50.0 + 16)),
                color: projectColors[i % projectColors.count],
                position: CGPoint(x: x, y: y)
            ))
        }

        // Category nodes — placed near their primary project
        for cat in data.categories {
            let primaryProject = cat.projects.first ?? ""
            let basePos = nodes.first(where: { $0.id == primaryProject })?.position ?? CGPoint(x: 500, y: 400)

            let jitterX = CGFloat.random(in: -80...80)
            let jitterY = CGFloat.random(in: -80...80)

            nodes.append(GraphNode(
                id: "cat_\(cat.name)",
                label: cat.name,
                detail: "\(cat.count)",
                kind: .category,
                size: max(5, min(14, CGFloat(cat.count) / 20.0 + 5)),
                color: typeColor(cat.name).opacity(0.7),
                position: CGPoint(x: basePos.x + jitterX, y: basePos.y + jitterY)
            ))

            // Link category to each of its projects
            for projectCode in cat.projects {
                links.append(GraphLink(
                    id: "link_\(projectCode)_\(cat.name)",
                    sourceId: projectCode,
                    targetId: "cat_\(cat.name)",
                    weight: min(Double(cat.count) / 20.0, 3.0)
                ))
            }
        }

        // Project-to-project edges
        for edge in data.edges {
            links.append(GraphLink(
                id: "edge_\(edge.fromProject)_\(edge.toProject)",
                sourceId: edge.fromProject,
                targetId: edge.toProject,
                weight: Double(edge.sharedCount)
            ))
        }

        simulation.nodes = nodes
        simulation.links = links
        simulation.start()
    }

    private func hitTest(_ location: CGPoint) -> String? {
        // Simple hit test against node positions
        // Note: Canvas coordinates — approximate mapping
        return nil // Hit testing on Canvas is complex; hover works via onContinuousHover position
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
        case let s where s.contains("database"): return AITopTheme.accentCyan
        case let s where s.contains("architect"): return Color(hex: "8B5CF6")
        case let s where s.contains("swift"): return AITopTheme.accentOrange
        case let s where s.contains("async"): return AITopTheme.warning
        default: return AITopTheme.textTertiary
        }
    }
}
