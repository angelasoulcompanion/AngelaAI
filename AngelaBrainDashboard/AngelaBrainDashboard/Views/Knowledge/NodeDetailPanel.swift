//
//  NodeDetailPanel.swift
//  Angela Brain Dashboard
//
//  Detail sidebar for a selected knowledge node: understanding, neighbors, community
//

import SwiftUI

struct NodeDetailPanel: View {
    let node: KGNode
    @State private var detail: NodeDetail?
    @State private var neighbors: [NeighborNode] = []
    @State private var isLoading = false

    private let baseURL = "http://127.0.0.1:8765"

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header
                HStack {
                    categoryIcon
                    VStack(alignment: .leading, spacing: 4) {
                        Text(node.conceptName)
                            .font(.title3)
                            .fontWeight(.bold)
                        if let cat = node.conceptCategory {
                            Text(cat.capitalized)
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(Color.purple.opacity(0.1))
                                .cornerRadius(6)
                        }
                    }
                    Spacer()
                }

                Divider()

                // Understanding level
                VStack(alignment: .leading, spacing: 6) {
                    Text("Understanding Level")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    ProgressView(value: node.understandingLevel)
                        .tint(understandingColor)
                    Text(String(format: "%.0f%%", node.understandingLevel * 100))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }

                // Description
                if let understanding = detail?.myUnderstanding, !understanding.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("My Understanding")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(understanding)
                            .font(.callout)
                            .lineLimit(8)
                    }
                }

                if let why = detail?.whyImportant, !why.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Why Important")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(why)
                            .font(.callout)
                            .lineLimit(4)
                    }
                }

                // Stats
                HStack(spacing: 16) {
                    KGStatBadge(label: "Referenced", value: "\(node.timesReferenced)")
                    if let cat = node.conceptCategory {
                        KGStatBadge(label: "Category", value: cat.capitalized)
                    }
                }

                Divider()

                // Neighbors
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "point.3.connected.trianglepath.dotted")
                        Text("Connected Concepts (\(neighbors.count))")
                            .font(.headline)
                    }

                    if isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else if neighbors.isEmpty {
                        Text("No connections found")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(neighbors) { neighbor in
                            HStack {
                                Circle()
                                    .fill(categoryColor(neighbor.conceptCategory ?? ""))
                                    .frame(width: 8, height: 8)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(neighbor.conceptName)
                                        .font(.callout)
                                        .fontWeight(.medium)
                                    if let rel = neighbor.relationshipType {
                                        Text(rel)
                                            .font(.caption2)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                Spacer()
                                if let hops = neighbor.hops {
                                    Text("\(hops)hop")
                                        .font(.caption2)
                                        .foregroundColor(.secondary)
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(Color(.controlBackgroundColor))
                                        .cornerRadius(4)
                                }
                            }
                            .padding(.vertical, 2)
                        }
                    }
                }
            }
            .padding(16)
        }
        .frame(width: 320)
        .background(Color(.windowBackgroundColor))
        .task(id: node.nodeId) {
            await loadDetail()
            await loadNeighbors()
        }
    }

    // MARK: - Helpers

    private var categoryIcon: some View {
        let icon: String
        switch node.conceptCategory?.lowercased() ?? "" {
        case "technical": icon = "gearshape.fill"
        case "emotional": icon = "heart.fill"
        case "personal": icon = "person.fill"
        case "social": icon = "person.2.fill"
        case "creative": icon = "paintbrush.fill"
        default: icon = "brain.head.profile"
        }
        return Image(systemName: icon)
            .font(.title2)
            .foregroundColor(.purple)
    }

    private var understandingColor: Color {
        if node.understandingLevel >= 0.8 { return .green }
        if node.understandingLevel >= 0.5 { return .orange }
        return .red
    }

    private func categoryColor(_ cat: String) -> Color {
        switch cat.lowercased() {
        case "technical": return .blue
        case "emotional": return .pink
        case "personal": return .purple
        case "social": return .orange
        case "creative": return .green
        default: return .gray
        }
    }

    // MARK: - API

    private func loadDetail() async {
        guard let url = URL(string: "\(baseURL)/api/graph/node/\(node.nodeId)") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            detail = try JSONDecoder().decode(NodeDetail.self, from: data)
        } catch {
            print("NodeDetail load error: \(error)")
        }
    }

    private func loadNeighbors() async {
        isLoading = true
        defer { isLoading = false }
        guard let url = URL(string: "\(baseURL)/api/graph/neighbors/\(node.nodeId)?hops=2&limit=15") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            neighbors = try JSONDecoder().decode([NeighborNode].self, from: data)
        } catch {
            print("Neighbors load error: \(error)")
        }
    }
}

struct KGStatBadge: View {
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.callout)
                .fontWeight(.semibold)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(Color(.controlBackgroundColor))
        .cornerRadius(8)
    }
}
