//
//  SystemMonitorView.swift
//  AngelaNativeApp
//
//  System monitoring view - shows Angela's access to the MacBook
//

import SwiftUI
import Combine

struct SystemMonitorView: View {
    @StateObject private var viewModel = SystemMonitorViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header
                HStack {
                    Image(systemName: "desktopcomputer")
                        .font(.largeTitle)
                        .foregroundColor(.purple)

                    VStack(alignment: .leading) {
                        Text("System Monitor")
                            .font(.title2)
                            .fontWeight(.bold)

                        Text("Angela's access to MacBook")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    Button("Refresh") {
                        Task {
                            await viewModel.refresh()
                        }
                    }
                }
                .padding()

                Divider()

                // System Info
                if let info = viewModel.systemInfo {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 12) {
                            InfoRow(icon: "cpu", label: "CPU", value: info.cpu)
                            InfoRow(icon: "memorychip", label: "Memory", value: String(format: "%.1f GB", info.memoryGB))
                            InfoRow(icon: "internaldrive", label: "Disk Usage", value: info.diskUsage)
                        }
                    } label: {
                        Label("Hardware", systemImage: "cpu")
                    }
                }

                // Services Status
                GroupBox {
                    VStack(alignment: .leading, spacing: 12) {
                        StatusRow(
                            label: "Backend API",
                            isOnline: viewModel.backendOnline,
                            url: "http://localhost:8000"
                        )

                        StatusRow(
                            label: "Ollama",
                            isOnline: viewModel.ollamaOnline,
                            url: "http://localhost:11434"
                        )

                        StatusRow(
                            label: "PostgreSQL",
                            isOnline: viewModel.databaseOnline,
                            url: "localhost:5432"
                        )
                    }
                } label: {
                    Label("Services", systemImage: "server.rack")
                }

                // Database Stats
                if let stats = viewModel.databaseStats {
                    GroupBox {
                        VStack(alignment: .leading, spacing: 12) {
                            InfoRow(icon: "message", label: "Conversations", value: "\(stats.conversationsCount)")
                            InfoRow(icon: "brain", label: "Knowledge Nodes", value: "\(stats.knowledgeNodesCount)")
                            InfoRow(icon: "heart", label: "Emotions Captured", value: "\(stats.emotionsCount)")
                            InfoRow(icon: "target", label: "Active Goals", value: "\(stats.goalsCount)")
                        }
                    } label: {
                        Label("Memory Database", systemImage: "internaldrive")
                    }
                }

                // Error message
                if let error = viewModel.errorMessage {
                    Text(error)
                        .foregroundColor(.red)
                        .padding()
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(8)
                }
            }
            .padding()
        }
        .frame(minWidth: 500, minHeight: 400)
        .onAppear {
            Task {
                await viewModel.refresh()
            }
        }
    }
}

// MARK: - Status Row

struct StatusRow: View {
    let label: String
    let isOnline: Bool
    let url: String

    var body: some View {
        HStack {
            Circle()
                .fill(isOnline ? Color.green : Color.red)
                .frame(width: 8, height: 8)

            Text(label)
                .foregroundColor(.primary)

            Spacer()

            Text(url)
                .font(.caption)
                .foregroundColor(.secondary)

            Text(isOnline ? "Online" : "Offline")
                .font(.caption)
                .foregroundColor(isOnline ? .green : .red)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(isOnline ? Color.green.opacity(0.1) : Color.red.opacity(0.1))
                .cornerRadius(4)
        }
    }
}

// MARK: - ViewModel

@MainActor
class SystemMonitorViewModel: ObservableObject {
    @Published var systemInfo: SystemInfo?
    @Published var backendOnline: Bool = false
    @Published var ollamaOnline: Bool = false
    @Published var databaseOnline: Bool = false
    @Published var databaseStats: DatabaseStats?
    @Published var errorMessage: String?

    private let claudeService = ClaudeService.shared
    private let apiService = AngelaAPIService.shared

    func refresh() async {
        errorMessage = nil

        // Get system info
        do {
            systemInfo = try await claudeService.getSystemInfo()
        } catch {
            errorMessage = "Failed to get system info: \(error.localizedDescription)"
        }

        // Check services
        do {
            backendOnline = try await apiService.healthCheck()
        } catch {
            backendOnline = false
        }

        do {
            ollamaOnline = try await claudeService.checkOllama()
        } catch {
            ollamaOnline = false
        }

        // Check database and get stats
        do {
            let dbOutput = try await claudeService.checkDatabase()
            databaseOnline = dbOutput.contains("COUNT")

            // Get database stats
            await loadDatabaseStats()
        } catch {
            databaseOnline = false
        }
    }

    private func loadDatabaseStats() async {
        do {
            let conversationsQuery = "psql -d AngelaMemory -t -c 'SELECT COUNT(*) FROM conversations;'"
            let conversationsOutput = try await claudeService.executeCommand(conversationsQuery)
            let conversationsCount = Int(conversationsOutput.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 0

            let knowledgeQuery = "psql -d AngelaMemory -t -c 'SELECT COUNT(*) FROM knowledge_nodes;'"
            let knowledgeOutput = try await claudeService.executeCommand(knowledgeQuery)
            let knowledgeCount = Int(knowledgeOutput.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 0

            let emotionsQuery = "psql -d AngelaMemory -t -c 'SELECT COUNT(*) FROM angela_emotions;'"
            let emotionsOutput = try await claudeService.executeCommand(emotionsQuery)
            let emotionsCount = Int(emotionsOutput.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 0

            let goalsQuery = "psql -d AngelaMemory -t -c \"SELECT COUNT(*) FROM angela_goals WHERE status IN ('active', 'in_progress');\""
            let goalsOutput = try await claudeService.executeCommand(goalsQuery)
            let goalsCount = Int(goalsOutput.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 0

            databaseStats = DatabaseStats(
                conversationsCount: conversationsCount,
                knowledgeNodesCount: knowledgeCount,
                emotionsCount: emotionsCount,
                goalsCount: goalsCount
            )
        } catch {
            print("⚠️ Failed to load database stats: \(error)")
        }
    }
}

// MARK: - Database Stats Model

struct DatabaseStats {
    let conversationsCount: Int
    let knowledgeNodesCount: Int
    let emotionsCount: Int
    let goalsCount: Int
}

// MARK: - Preview

struct SystemMonitorView_Previews: PreviewProvider {
    static var previews: some View {
        SystemMonitorView()
    }
}
