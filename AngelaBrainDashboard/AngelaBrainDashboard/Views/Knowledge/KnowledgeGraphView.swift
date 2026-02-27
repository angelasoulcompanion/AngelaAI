//
//  KnowledgeGraphView.swift
//  Angela Brain Dashboard
//
//  HSplitView: D3.js graph visualization (left) + node detail panel (right)
//  Toggle between Graph (D3.js force-directed) and Grid (card grid) views
//

import SwiftUI
import Combine

enum GraphViewMode: String, CaseIterable {
    case graph = "Graph"
    case grid = "Grid"
}

struct KnowledgeGraphView: View {
    @StateObject private var viewModel = KnowledgeGraphViewModel()
    @State private var viewMode: GraphViewMode = .graph

    var body: some View {
        VStack(spacing: 0) {
            // Filter bar + view mode toggle
            HStack {
                GraphFilterBar(
                    searchText: $viewModel.searchText,
                    selectedCategory: $viewModel.selectedCategory,
                    categories: viewModel.categories,
                    onSearch: { Task { await viewModel.search() } }
                )

                Picker("View", selection: $viewMode) {
                    ForEach(GraphViewMode.allCases, id: \.self) { mode in
                        Label(mode.rawValue, systemImage: mode == .graph ? "point.3.connected.trianglepath.dotted" : "square.grid.3x3")
                            .tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 160)
                .padding(.trailing, 16)
            }

            Divider()

            // Stats bar
            HStack(spacing: 16) {
                Label("\(viewModel.graph?.nodes.count ?? 0) nodes", systemImage: "circle.grid.3x3")
                Label("\(viewModel.graph?.edges.count ?? 0) edges", systemImage: "line.diagonal")
                if let stats = viewModel.stats {
                    Label("Neo4j: \(stats.neo4j.available ? "✅" : "❌")", systemImage: "server.rack")
                }
                Spacer()
                if viewModel.isLoading {
                    ProgressView()
                        .scaleEffect(0.7)
                    Text("Loading...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                Button(action: { Task { await viewModel.loadAll() } }) {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.plain)
            }
            .font(.caption)
            .padding(.horizontal, 16)
            .padding(.vertical, 6)
            .background(Color(.controlBackgroundColor).opacity(0.5))

            Divider()

            // Main content: HSplitView
            HSplitView {
                // Left: Graph or Grid
                Group {
                    switch viewMode {
                    case .graph:
                        // D3.js force-directed graph
                        KnowledgeGraphWebView(
                            graphData: viewModel.d3GraphData,
                            onNodeClick: { nodeId, nodeName in
                                // Find and select the node
                                if let node = viewModel.graph?.nodes.first(where: { $0.nodeId == nodeId }) {
                                    withAnimation(.easeInOut(duration: 0.2)) {
                                        viewModel.selectedNode = node
                                    }
                                }
                            }
                        )

                    case .grid:
                        // Card grid
                        ScrollView {
                            if viewModel.graph != nil {
                                LazyVGrid(columns: [
                                    GridItem(.adaptive(minimum: 160, maximum: 220), spacing: 12)
                                ], spacing: 12) {
                                    ForEach(viewModel.filteredNodes) { node in
                                        NodeCard(
                                            node: node,
                                            isSelected: viewModel.selectedNode?.nodeId == node.nodeId,
                                            edgeCount: viewModel.edgeCount(for: node.nodeId)
                                        )
                                        .onTapGesture {
                                            withAnimation(.easeInOut(duration: 0.2)) {
                                                viewModel.selectedNode = node
                                            }
                                        }
                                    }
                                }
                                .padding(16)
                            } else if !viewModel.isLoading {
                                ContentUnavailableView(
                                    "No Graph Data",
                                    systemImage: "point.3.connected.trianglepath.dotted",
                                    description: Text("Load the knowledge graph to explore Angela's knowledge")
                                )
                            }
                        }
                    }
                }
                .frame(minWidth: 500)

                // Right: Detail panel
                if let selected = viewModel.selectedNode {
                    NodeDetailPanel(node: selected)
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "point.3.connected.trianglepath.dotted")
                            .font(.system(size: 48))
                            .foregroundColor(.secondary.opacity(0.5))
                        Text("Select a node to view details")
                            .font(.callout)
                            .foregroundColor(.secondary)

                        if let communities = viewModel.communities {
                            Divider()
                                .padding(.vertical, 8)
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Communities (\(communities.totalCommunities))")
                                    .font(.headline)
                                ForEach(communities.communities.prefix(8)) { comm in
                                    HStack {
                                        Circle()
                                            .fill(communityColor(comm.communityId))
                                            .frame(width: 10, height: 10)
                                        Text(comm.representativeName)
                                            .font(.callout)
                                        Spacer()
                                        Text("\(comm.size)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                            .padding(.horizontal, 16)
                        }
                    }
                    .frame(width: 320)
                    .frame(maxHeight: .infinity)
                }
            }
        }
        .task { await viewModel.loadAll() }
    }

    private func communityColor(_ id: Int) -> Color {
        let colors: [Color] = [.purple, .blue, .green, .orange, .pink, .cyan, .yellow, .red]
        return colors[id % colors.count]
    }
}

// MARK: - Node Card

struct NodeCard: View {
    let node: KGNode
    let isSelected: Bool
    let edgeCount: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle()
                    .fill(categoryColor)
                    .frame(width: 10, height: 10)
                Text(node.conceptName)
                    .font(.callout)
                    .fontWeight(.semibold)
                    .lineLimit(2)
            }

            if let understanding = node.myUnderstanding, !understanding.isEmpty {
                Text(understanding)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(3)
            }

            HStack {
                ProgressView(value: node.understandingLevel)
                    .tint(levelColor)
                    .frame(width: 60)
                Text(String(format: "%.0f%%", node.understandingLevel * 100))
                    .font(.caption2)
                    .foregroundColor(.secondary)
                Spacer()
                if edgeCount > 0 {
                    HStack(spacing: 2) {
                        Image(systemName: "link")
                        Text("\(edgeCount)")
                    }
                    .font(.caption2)
                    .foregroundColor(.secondary)
                }
            }
        }
        .padding(12)
        .background(isSelected ? Color.purple.opacity(0.1) : Color(.controlBackgroundColor))
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(isSelected ? Color.purple : Color.clear, lineWidth: 2)
        )
    }

    private var categoryColor: Color {
        switch node.conceptCategory?.lowercased() ?? "" {
        case "technical": return .blue
        case "emotional": return .pink
        case "personal": return .purple
        case "social": return .orange
        case "creative": return .green
        default: return .gray
        }
    }

    private var levelColor: Color {
        if node.understandingLevel >= 0.8 { return .green }
        if node.understandingLevel >= 0.5 { return .orange }
        return .red
    }
}

// MARK: - ViewModel

@MainActor
class KnowledgeGraphViewModel: ObservableObject {
    @Published var graph: FullGraph?
    @Published var stats: GraphStats?
    @Published var communities: CommunityResponse?
    @Published var selectedNode: KGNode?
    @Published var searchText = ""
    @Published var selectedCategory: String?
    @Published var isLoading = false

    private let baseURL = "http://127.0.0.1:8765"

    /// Convert FullGraph → GraphData for D3.js WebView
    var d3GraphData: GraphData? {
        guard let graph = graph else { return nil }
        let nodes = graph.nodes.map { node in
            GraphNode(
                id: node.nodeId,
                name: node.conceptName,
                category: node.conceptCategory,
                understanding: node.understandingLevel,
                references: node.timesReferenced
            )
        }
        let links = graph.edges.map { edge in
            GraphLink(
                source: edge.fromNodeId,
                target: edge.toNodeId,
                strength: edge.strength
            )
        }
        return GraphData(nodes: nodes, links: links, totalNodes: graph.nodes.count)
    }

    var categories: [String] {
        guard let nodes = graph?.nodes else { return [] }
        let cats = Set(nodes.compactMap { $0.conceptCategory?.lowercased() })
        return cats.sorted()
    }

    var filteredNodes: [KGNode] {
        guard let nodes = graph?.nodes else { return [] }
        var filtered = nodes

        if let cat = selectedCategory {
            filtered = filtered.filter { $0.conceptCategory?.lowercased() == cat }
        }

        if !searchText.isEmpty {
            let q = searchText.lowercased()
            filtered = filtered.filter {
                $0.conceptName.lowercased().contains(q) ||
                ($0.myUnderstanding?.lowercased().contains(q) ?? false)
            }
        }

        return filtered
    }

    func edgeCount(for nodeId: String) -> Int {
        guard let edges = graph?.edges else { return 0 }
        return edges.filter { $0.fromNodeId == nodeId || $0.toNodeId == nodeId }.count
    }

    func loadAll() async {
        isLoading = true
        defer { isLoading = false }

        async let graphTask = fetchGraph()
        async let statsTask = fetchStats()
        async let commTask = fetchCommunities()

        let (g, s, c) = await (graphTask, statsTask, commTask)
        graph = g
        stats = s
        communities = c
    }

    func search() async {
        if searchText.isEmpty { return }
    }

    private func fetchGraph() async -> FullGraph? {
        guard let url = URL(string: "\(baseURL)/api/graph/full?limit=500") else { return nil }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            return try JSONDecoder().decode(FullGraph.self, from: data)
        } catch {
            print("Graph fetch error: \(error)")
            return nil
        }
    }

    private func fetchStats() async -> GraphStats? {
        guard let url = URL(string: "\(baseURL)/api/graph/stats") else { return nil }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            return try JSONDecoder().decode(GraphStats.self, from: data)
        } catch {
            print("Stats fetch error: \(error)")
            return nil
        }
    }

    private func fetchCommunities() async -> CommunityResponse? {
        guard let url = URL(string: "\(baseURL)/api/graph/communities?min_size=3") else { return nil }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            return try JSONDecoder().decode(CommunityResponse.self, from: data)
        } catch {
            print("Communities fetch error: \(error)")
            return nil
        }
    }
}
