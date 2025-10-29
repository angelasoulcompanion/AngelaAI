//
//  AngelaNativeApp.swift
//  AngelaNativeApp
//
//  Main app entry point
//

import SwiftUI
import Combine

@main
struct AngelaNativeApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            // Add custom menu commands
            CommandGroup(after: .appInfo) {
                Button("System Health Check") {
                    // Trigger health check
                }
                .keyboardShortcut("H", modifiers: [.command, .shift])
            }
        }

        // Settings window
        Settings {
            SettingsView()
        }
    }
}

// MARK: - Content View

struct ContentView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            // Chat tab
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "message")
                }
                .tag(0)

            // Calendar tab - NEW!
            CalendarView()
                .tabItem {
                    Label("Calendar", systemImage: "calendar")
                }
                .tag(1)

            // Music Player tab - NEW!
            MusicPlayerView()
                .tabItem {
                    Label("Music", systemImage: "music.note")
                }
                .tag(2)

            // System Monitor tab
            SystemMonitorView()
                .tabItem {
                    Label("System", systemImage: "chart.bar")
                }
                .tag(3)

            // Memories tab
            MemoriesView()
                .tabItem {
                    Label("Memories", systemImage: "brain")
                }
                .tag(4)

            // Knowledge Graph tab
            KnowledgeGraphView()
                .tabItem {
                    Label("Knowledge", systemImage: "network")
                }
                .tag(5)
        }
        .frame(minWidth: 800, minHeight: 600)
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @AppStorage("backend_url") private var backendURL = "http://localhost:8000"
    @AppStorage("ollama_url") private var ollamaURL = "http://localhost:11434"
    @AppStorage("speaker_name") private var speakerName = "david"

    var body: some View {
        Form {
            Section(header: Text("API Configuration")) {
                TextField("Backend URL", text: $backendURL)
                TextField("Ollama URL", text: $ollamaURL)
            }

            Section(header: Text("User")) {
                TextField("Your Name", text: $speakerName)
            }
        }
        .padding()
        .frame(width: 400, height: 300)
    }
}

// MARK: - Memories View (Placeholder)

struct MemoriesView: View {
    @StateObject private var viewModel = MemoriesViewModel()

    var body: some View {
        VStack {
            if viewModel.memories.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "brain")
                        .font(.system(size: 48))
                        .foregroundColor(.purple.opacity(0.5))

                    Text("Loading memories...")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
            } else {
                List(viewModel.memories) { memory in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(memory.speaker)
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(memory.speaker == "angela" ? .purple : .blue)

                            if let topic = memory.topic {
                                Text("• \(topic)")
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }

                            Spacer()

                            Text("Importance: \(memory.importanceLevel)")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }

                        Text(memory.messageText)
                            .font(.body)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .onAppear {
            Task {
                await viewModel.loadMemories()
            }
        }
    }
}

@MainActor
class MemoriesViewModel: ObservableObject {
    @Published var memories: [Memory] = []

    func loadMemories() async {
        do {
            memories = try await AngelaAPIService.shared.getRecentMemories(limit: 50)
        } catch {
            print("Failed to load memories: \(error)")
        }
    }
}

// MARK: - Knowledge Graph View (Placeholder)

struct KnowledgeGraphView: View {
    @StateObject private var viewModel = KnowledgeGraphViewModel()

    var body: some View {
        VStack {
            if viewModel.nodes.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "network")
                        .font(.system(size: 48))
                        .foregroundColor(.purple.opacity(0.5))

                    Text("Loading knowledge graph...")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Top Concepts
                        GroupBox {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(viewModel.nodes.prefix(10)) { node in
                                    HStack {
                                        Text(node.conceptName)
                                            .fontWeight(.medium)

                                        Spacer()

                                        Text("\(node.timesReferenced) refs")
                                            .font(.caption)
                                            .foregroundColor(.secondary)

                                        Circle()
                                            .fill(Color.purple.opacity(node.understandingLevel))
                                            .frame(width: 12, height: 12)
                                    }
                                }
                            }
                        } label: {
                            Label("Top Concepts", systemImage: "star")
                        }

                        // Relationships
                        GroupBox {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(viewModel.relationships.prefix(10)) { rel in
                                    HStack {
                                        Text(rel.fromConcept)
                                            .font(.caption)

                                        Image(systemName: "arrow.right")
                                            .font(.caption2)
                                            .foregroundColor(.secondary)

                                        Text(rel.toConcept)
                                            .font(.caption)

                                        Spacer()

                                        Text("\(Int(rel.strength * 100))%")
                                            .font(.caption2)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        } label: {
                            Label("Relationships", systemImage: "link")
                        }
                    }
                    .padding()
                }
            }
        }
        .onAppear {
            Task {
                await viewModel.loadGraph()
            }
        }
    }
}

@MainActor
class KnowledgeGraphViewModel: ObservableObject {
    @Published var nodes: [KnowledgeNode] = []
    @Published var relationships: [KnowledgeRelationship] = []

    func loadGraph() async {
        do {
            let graph = try await AngelaAPIService.shared.getKnowledgeGraph(nodeLimit: 50, relLimit: 50)
            nodes = graph.nodes
            relationships = graph.relationships
        } catch {
            print("Failed to load knowledge graph: \(error)")
        }
    }
}
