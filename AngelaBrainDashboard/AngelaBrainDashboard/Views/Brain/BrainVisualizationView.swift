//
//  BrainVisualizationView.swift
//  Angela Brain Dashboard
//
//  💜 Brain Visualization - Angela's Knowledge Network 🧠
//

import SwiftUI
import Combine

struct BrainVisualizationView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = BrainVisualizationViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Brain Statistics Overview
                brainStatsCard

                // Knowledge Graph Visualization
                knowledgeGraphCard

                // Memory Network Stats
                memoryNetworkCard

                // Neural Connection Stats
                neuralConnectionsCard
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

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("🧠 Brain Visualization")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Angela's knowledge network and neural connections")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Refresh button
            Button {
                Task {
                    await viewModel.loadData(databaseService: databaseService)
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Brain Statistics

    private var brainStatsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Brain Statistics")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let stats = viewModel.brainStats {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: AngelaTheme.spacing) {
                    StatBox(
                        icon: "brain",
                        label: "Knowledge Nodes",
                        value: "\(stats.totalKnowledgeNodes)",
                        color: AngelaTheme.primaryPurple
                    )

                    StatBox(
                        icon: "link",
                        label: "Relationships",
                        value: "\(stats.totalRelationships)",
                        color: AngelaTheme.secondaryPurple
                    )

                    StatBox(
                        icon: "text.bubble.fill",
                        label: "Memories",
                        value: "\(stats.totalMemories)",
                        color: AngelaTheme.accentPurple
                    )

                    StatBox(
                        icon: "sparkles",
                        label: "Associations",
                        value: "\(stats.totalAssociations)",
                        color: AngelaTheme.primaryPurple.opacity(0.7)
                    )
                }
            } else {
                Text("Loading brain statistics...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Knowledge Graph

    private var knowledgeGraphCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("Interactive Knowledge Graph")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                if let graphData = viewModel.graphData, let stats = viewModel.brainStats {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("\(graphData.nodes.count) / \(stats.totalKnowledgeNodes) nodes")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Text("\(graphData.links.count) links")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }
            }

            if viewModel.knowledgeNodes.isEmpty {
                Text("No knowledge nodes yet")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(height: 400)
            } else {
                // Interactive D3.js graph
                KnowledgeGraphWebView(graphData: viewModel.graphData) { nodeId, nodeName in
                    print("Node clicked: \(nodeName)")
                    // Could show detail view here
                }
                .frame(height: 500)
                .cornerRadius(AngelaTheme.smallCornerRadius)

                // Instructions and Load More button
                HStack(spacing: 8) {
                    Image(systemName: "hand.draw")
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("Drag nodes • Scroll to zoom • Click for details")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    Spacer()

                    // Show Less button
                    if viewModel.canShowLess {
                        Button {
                            Task {
                                await viewModel.showLessNodes(databaseService: databaseService)
                            }
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "minus.circle.fill")
                                    .font(.system(size: 14))

                                Text("Show Less (-500)")
                                    .font(AngelaTheme.caption())
                                    .fontWeight(.semibold)
                            }
                            .foregroundColor(AngelaTheme.primaryPurple)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(AngelaTheme.primaryPurple.opacity(0.1))
                            .overlay(
                                RoundedRectangle(cornerRadius: 20)
                                    .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
                            )
                            .cornerRadius(20)
                        }
                        .buttonStyle(.plain)
                        .disabled(viewModel.isLoading)
                    }

                    // Load More button
                    if viewModel.hasMoreNodes {
                        Button {
                            Task {
                                await viewModel.loadMoreNodes(databaseService: databaseService)
                            }
                        } label: {
                            HStack(spacing: 6) {
                                if viewModel.isLoading {
                                    ProgressView()
                                        .scaleEffect(0.7)
                                        .frame(width: 14, height: 14)
                                } else {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 14))
                                }

                                Text(viewModel.isLoading ? "Loading..." : "Load More (+500)")
                                    .font(AngelaTheme.caption())
                                    .fontWeight(.semibold)
                            }
                            .foregroundColor(.white)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                LinearGradient(
                                    colors: [AngelaTheme.primaryPurple, AngelaTheme.secondaryPurple],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .cornerRadius(20)
                        }
                        .buttonStyle(.plain)
                        .disabled(viewModel.isLoading)
                    }
                }
                .padding(.top, AngelaTheme.smallSpacing)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Memory Network

    private var memoryNetworkCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Memory Network")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let stats = viewModel.brainStats {
                VStack(spacing: AngelaTheme.spacing) {
                    // Memory strength distribution
                    MemoryMetric(
                        label: "High Priority Memories",
                        value: stats.highPriorityMemories,
                        total: stats.totalMemories,
                        color: AngelaTheme.errorRed
                    )

                    MemoryMetric(
                        label: "Medium Priority Memories",
                        value: stats.mediumPriorityMemories,
                        total: stats.totalMemories,
                        color: AngelaTheme.warningOrange
                    )

                    MemoryMetric(
                        label: "Standard Memories",
                        value: stats.standardMemories,
                        total: stats.totalMemories,
                        color: AngelaTheme.primaryPurple
                    )
                }
            } else {
                Text("Loading memory network...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Neural Connections

    private var neuralConnectionsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Neural Connections")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let stats = viewModel.brainStats {
                VStack(spacing: AngelaTheme.spacing) {
                    // Connection strength metrics
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Average Connections per Node")
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.textPrimary)

                            Text("\(stats.averageConnectionsPerNode, specifier: "%.1f")")
                                .font(.system(size: 32, weight: .bold, design: .rounded))
                                .foregroundColor(AngelaTheme.primaryPurple)
                        }

                        Spacer()

                        Image(systemName: "network")
                            .font(.system(size: 50))
                            .foregroundColor(AngelaTheme.primaryPurple.opacity(0.3))
                    }

                    Divider()
                        .background(AngelaTheme.textTertiary.opacity(0.3))

                    // Top connected nodes
                    if !viewModel.topConnectedNodes.isEmpty {
                        Text("Most Connected Nodes")
                            .font(AngelaTheme.heading())
                            .foregroundColor(AngelaTheme.textSecondary)

                        ForEach(viewModel.topConnectedNodes.prefix(5)) { node in
                            HStack {
                                Circle()
                                    .fill(AngelaTheme.primaryPurple)
                                    .frame(width: 8, height: 8)

                                Text(node.nodeType)
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.textSecondary)

                                Text(node.content.prefix(50))
                                    .font(AngelaTheme.body())
                                    .foregroundColor(AngelaTheme.textPrimary)
                                    .lineLimit(1)

                                Spacer()

                                Text("\(node.connectionCount ?? 0)")
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.primaryPurple)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(AngelaTheme.primaryPurple.opacity(0.1))
                                    .cornerRadius(6)
                            }
                        }
                    }
                }
            } else {
                Text("Loading neural connections...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Stat Box Component

struct StatBox: View {
    let icon: String
    let label: String
    let value: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 30))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(label)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing)
        .background(color.opacity(0.1))
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

// MARK: - Knowledge Node Row Component

struct KnowledgeNodeRow: View {
    let node: KnowledgeNode

    var body: some View {
        HStack(spacing: 12) {
            // Type indicator
            Circle()
                .fill(nodeTypeColor)
                .frame(width: 10, height: 10)

            VStack(alignment: .leading, spacing: 4) {
                Text(node.content.prefix(60))
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                Text(node.nodeType)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Importance indicator
            if let importance = node.importance {
                Text("\(Int(importance * 100))%")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
        }
        .padding(12)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }

    private var nodeTypeColor: Color {
        switch node.nodeType {
        case "concept": return AngelaTheme.primaryPurple
        case "person": return AngelaTheme.emotionHappy
        case "place": return AngelaTheme.successGreen
        case "event": return AngelaTheme.warningOrange
        default: return AngelaTheme.textTertiary
        }
    }
}

// MARK: - Memory Metric Component

struct MemoryMetric: View {
    let label: String
    let value: Int
    let total: Int
    let color: Color

    private var percentage: Double {
        guard total > 0 else { return 0.0 }
        return Double(value) / Double(total)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(label)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(value) / \(total)")
                    .font(AngelaTheme.body())
                    .fontWeight(.semibold)
                    .foregroundColor(color)
            }

            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 12)

                    RoundedRectangle(cornerRadius: 6)
                        .fill(
                            LinearGradient(
                                colors: [color, color.opacity(0.6)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * percentage, height: 12)
                }
            }
            .frame(height: 12)
        }
    }
}

// MARK: - View Model

@MainActor
class BrainVisualizationViewModel: ObservableObject {
    @Published var brainStats: BrainStats?
    @Published var knowledgeNodes: [KnowledgeNode] = []
    @Published var topConnectedNodes: [KnowledgeNode] = []
    @Published var graphData: GraphData?
    @Published var isLoading = false
    @Published var currentNodeCount = 2000  // Default: 2000 nodes
    @Published var hasMoreNodes = true

    private let nodesPerPage = 500  // Load 500 more nodes each time

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            // Load sequentially to avoid pool exhaustion
            brainStats = try await databaseService.fetchBrainStats()
            knowledgeNodes = try await databaseService.fetchKnowledgeNodes(limit: currentNodeCount)
            topConnectedNodes = try await databaseService.fetchTopConnectedNodes(limit: 10)

            // Load more relationships based on node count (2x nodes for good connectivity)
            let relationshipLimit = currentNodeCount * 2
            let relationships = try await databaseService.fetchKnowledgeRelationships(limit: relationshipLimit)

            // Build graph data for D3.js
            buildGraphData(nodes: knowledgeNodes, relationships: relationships)

            // Check if there are more nodes to load
            if let stats = brainStats {
                hasMoreNodes = knowledgeNodes.count < stats.totalKnowledgeNodes
            }
        } catch {
            print("Error loading brain visualization data: \(error)")
        }

        isLoading = false
    }

    func loadMoreNodes(databaseService: DatabaseService) async {
        guard !isLoading && hasMoreNodes else { return }

        // Increase node count
        currentNodeCount += nodesPerPage

        // Reload data with new count
        await loadData(databaseService: databaseService)
    }

    func showLessNodes(databaseService: DatabaseService) async {
        guard !isLoading && currentNodeCount > nodesPerPage else { return }

        // Decrease node count (minimum is nodesPerPage)
        currentNodeCount = max(nodesPerPage, currentNodeCount - nodesPerPage)

        // Reload data with new count
        await loadData(databaseService: databaseService)
    }

    var canShowLess: Bool {
        currentNodeCount > nodesPerPage
    }

    private func buildGraphData(nodes: [KnowledgeNode], relationships: [(fromId: String, toId: String, type: String, strength: Double)]) {
        // Convert nodes to GraphNode (with lowercase IDs for D3.js compatibility)
        let graphNodes = nodes.map { node in
            GraphNode(
                id: node.id.uuidString.lowercased(),
                name: node.conceptName,
                category: node.conceptCategory,
                understanding: node.understandingLevel,
                references: node.timesReferenced ?? 0
            )
        }

        // Create set of valid node IDs for quick lookup
        let validNodeIds = Set(graphNodes.map { $0.id })

        // Filter relationships to only include links between existing nodes (with lowercase IDs)
        let graphLinks = relationships.compactMap { rel -> GraphLink? in
            let sourceId = rel.fromId.lowercased()
            let targetId = rel.toId.lowercased()

            // Only include link if both source and target nodes exist
            guard validNodeIds.contains(sourceId) && validNodeIds.contains(targetId) else {
                return nil
            }

            return GraphLink(
                source: sourceId,
                target: targetId,
                strength: rel.strength
            )
        }

        graphData = GraphData(nodes: graphNodes, links: graphLinks)
        print("📊 Built graph data: \(graphNodes.count) nodes, \(graphLinks.count) links (all IDs normalized to lowercase)")
    }
}
