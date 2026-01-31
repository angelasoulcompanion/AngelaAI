//
//  ControlCenterView.swift
//  Angela Brain Dashboard
//
//  Control Center - Daemon Tasks & MCP Servers
//

import SwiftUI

struct ControlCenterView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var daemons: [DaemonStatus] = []
    @State private var mcpServers: [MCPServerInfo] = []
    @State private var isLoading = true
    @State private var selectedLogDaemon: DaemonStatus?
    @State private var logLines: [String] = []
    @State private var loadingAction: String?  // label of daemon being acted on
    @State private var togglingServer: String?  // name of MCP server being toggled
    @State private var autoRefreshTimer: Timer?

    // Daemon categories in display order
    private let categoryOrder = ["core", "communication", "consciousness", "productivity"]
    private let categoryNames = [
        "core": "Core",
        "communication": "Communication",
        "consciousness": "Consciousness",
        "productivity": "Productivity",
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AngelaTheme.largeSpacing) {
                // Header
                headerSection

                // Stats cards
                statsSection

                // Daemon Tasks
                daemonSection

                // MCP Servers
                mcpSection
            }
            .padding(AngelaTheme.largeSpacing)
        }
        .background(AngelaTheme.backgroundDark)
        .task {
            await loadData()
            startAutoRefresh()
        }
        .onDisappear {
            stopAutoRefresh()
        }
        .sheet(item: $selectedLogDaemon) { daemon in
            LogViewerSheet(daemon: daemon, databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Control Center")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)
                Text("Daemon Tasks & MCP Servers")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Button {
                Task { await loadData() }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                    Text("Refresh")
                }
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.primaryPurple)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(AngelaTheme.primaryPurple.opacity(0.15))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Stats Cards

    private var statsSection: some View {
        HStack(spacing: AngelaTheme.spacing) {
            statCard(
                title: "Running",
                value: "\(daemons.filter { $0.status == "running" }.count)/\(daemons.count)",
                icon: "power",
                color: AngelaTheme.successGreen
            )
            statCard(
                title: "MCP Enabled",
                value: "\(mcpServers.filter { $0.enabled }.count)/\(mcpServers.count)",
                icon: "puzzlepiece.extension.fill",
                color: AngelaTheme.emotionMotivated
            )
            statCard(
                title: "KeepAlive",
                value: "\(daemons.filter { $0.keepAlive }.count)",
                icon: "heart.fill",
                color: AngelaTheme.emotionLoved
            )
            statCard(
                title: "Scheduled",
                value: "\(daemons.filter { !$0.keepAlive }.count)",
                icon: "clock.fill",
                color: AngelaTheme.warningOrange
            )
        }
    }

    private func statCard(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                    .foregroundColor(color)
                Text(title)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textPrimary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .angelaCard()
    }

    // MARK: - Daemon Section

    private var daemonSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack(spacing: 8) {
                Image(systemName: "bolt.fill")
                    .foregroundColor(AngelaTheme.warningOrange)
                Text("Daemon Tasks")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            ForEach(categoryOrder, id: \.self) { category in
                let categoryDaemons = daemons.filter { $0.category == category }
                if !categoryDaemons.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        // Category header
                        HStack(spacing: 6) {
                            Image(systemName: categoryDaemons.first?.categoryIcon ?? "gearshape.fill")
                                .font(.system(size: 11))
                                .foregroundColor(categoryDaemons.first?.categoryColor ?? .gray)
                            Text(categoryNames[category] ?? category.capitalized)
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(AngelaTheme.textSecondary)
                                .textCase(.uppercase)
                                .tracking(0.5)
                        }
                        .padding(.leading, 4)

                        // Daemon rows
                        VStack(spacing: 0) {
                            ForEach(categoryDaemons) { daemon in
                                daemonRow(daemon)
                                if daemon.id != categoryDaemons.last?.id {
                                    Divider()
                                        .background(AngelaTheme.backgroundDark.opacity(0.5))
                                }
                            }
                        }
                        .angelaCard()
                    }
                }
            }
        }
    }

    private func daemonRow(_ daemon: DaemonStatus) -> some View {
        HStack(spacing: 12) {
            // Status indicator
            Image(systemName: daemon.statusIcon)
                .font(.system(size: 10))
                .foregroundColor(daemon.statusColor)

            // Info
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 8) {
                    Text(daemon.name)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text(daemon.schedule)
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(AngelaTheme.backgroundDark.opacity(0.5))
                        .cornerRadius(4)
                }

                Text(daemon.description)
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(1)
            }

            Spacer()

            // Status text
            VStack(alignment: .trailing, spacing: 2) {
                Text(daemon.status.capitalized)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(daemon.statusColor)

                if let pid = daemon.pid {
                    Text("PID \(pid)")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            // Action buttons
            HStack(spacing: 4) {
                // Log viewer
                Button {
                    selectedLogDaemon = daemon
                } label: {
                    Image(systemName: "doc.text.magnifyingglass")
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(width: 28, height: 28)
                        .background(AngelaTheme.backgroundDark.opacity(0.5))
                        .cornerRadius(6)
                }
                .buttonStyle(.plain)

                // Start/Stop
                if loadingAction == daemon.label {
                    ProgressView()
                        .scaleEffect(0.6)
                        .frame(width: 28, height: 28)
                } else if daemon.isRunning || daemon.status == "idle" {
                    Button {
                        Task { await stopDaemon(daemon) }
                    } label: {
                        Image(systemName: "stop.fill")
                            .font(.system(size: 10))
                            .foregroundColor(.red)
                            .frame(width: 28, height: 28)
                            .background(Color.red.opacity(0.15))
                            .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                } else {
                    Button {
                        Task { await startDaemon(daemon) }
                    } label: {
                        Image(systemName: "play.fill")
                            .font(.system(size: 10))
                            .foregroundColor(.green)
                            .frame(width: 28, height: 28)
                            .background(Color.green.opacity(0.15))
                            .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }

    // MARK: - MCP Section

    private var mcpSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack(spacing: 8) {
                Image(systemName: "puzzlepiece.extension.fill")
                    .foregroundColor(AngelaTheme.emotionMotivated)
                Text("MCP Servers")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            VStack(spacing: 0) {
                ForEach(mcpServers) { server in
                    mcpServerRow(server)
                    if server.id != mcpServers.last?.id {
                        Divider()
                            .background(AngelaTheme.backgroundDark.opacity(0.5))
                    }
                }
            }
            .angelaCard()
        }
    }

    private func mcpServerRow(_ server: MCPServerInfo) -> some View {
        HStack(spacing: 12) {
            // Icon
            Image(systemName: server.icon)
                .font(.system(size: 16))
                .foregroundColor(server.enabled ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary)
                .frame(width: 32, height: 32)
                .background(
                    (server.enabled ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary)
                        .opacity(0.12)
                )
                .cornerRadius(8)

            // Info
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 8) {
                    Text(server.name)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("\(server.toolsCount) tools")
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(AngelaTheme.backgroundDark.opacity(0.5))
                        .cornerRadius(4)
                }

                Text(server.description)
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(1)
            }

            Spacer()

            // Toggle
            if togglingServer == server.name {
                ProgressView()
                    .scaleEffect(0.6)
            } else {
                Toggle("", isOn: Binding(
                    get: { server.enabled },
                    set: { newValue in
                        Task { await toggleMCP(server, enabled: newValue) }
                    }
                ))
                .toggleStyle(.switch)
                .labelsHidden()
                .tint(AngelaTheme.successGreen)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }

    // MARK: - Data Loading

    private func loadData() async {
        do {
            async let daemonResult = databaseService.fetchDaemonStatuses()
            async let mcpResult = databaseService.fetchMCPServers()
            let (d, m) = try await (daemonResult, mcpResult)
            await MainActor.run {
                daemons = d
                mcpServers = m
                isLoading = false
            }
        } catch {
            print("Error loading control center data: \(error)")
            await MainActor.run { isLoading = false }
        }
    }

    private func startDaemon(_ daemon: DaemonStatus) async {
        loadingAction = daemon.label
        do {
            _ = try await databaseService.startDaemon(label: daemon.label)
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            await loadData()
        } catch {
            print("Error starting daemon: \(error)")
        }
        loadingAction = nil
    }

    private func stopDaemon(_ daemon: DaemonStatus) async {
        loadingAction = daemon.label
        do {
            _ = try await databaseService.stopDaemon(label: daemon.label)
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            await loadData()
        } catch {
            print("Error stopping daemon: \(error)")
        }
        loadingAction = nil
    }

    private func toggleMCP(_ server: MCPServerInfo, enabled: Bool) async {
        togglingServer = server.name
        do {
            _ = try await databaseService.toggleMCPServer(name: server.name, enabled: enabled)
            await loadData()
        } catch {
            print("Error toggling MCP server: \(error)")
        }
        togglingServer = nil
    }

    // MARK: - Auto Refresh

    private func startAutoRefresh() {
        autoRefreshTimer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { _ in
            Task { await loadData() }
        }
    }

    private func stopAutoRefresh() {
        autoRefreshTimer?.invalidate()
        autoRefreshTimer = nil
    }
}

// MARK: - Log Viewer Sheet

struct LogViewerSheet: View {
    let daemon: DaemonStatus
    let databaseService: DatabaseService
    @State private var logLines: [String] = []
    @State private var isLoading = true
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(daemon.name)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)
                    if let logFile = daemon.logFile {
                        Text(logFile)
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(AngelaTheme.textTertiary)
                            .lineLimit(1)
                            .truncationMode(.middle)
                    }
                }

                Spacer()

                Button {
                    Task { await fetchLogs() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)

                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
            .padding()
            .background(AngelaTheme.cardBackground)

            Divider()

            // Log content
            if isLoading {
                VStack {
                    Spacer()
                    ProgressView()
                    Spacer()
                }
            } else {
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 1) {
                            ForEach(Array(logLines.enumerated()), id: \.offset) { index, line in
                                Text(line)
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(logLineColor(line))
                                    .textSelection(.enabled)
                                    .id(index)
                            }
                        }
                        .padding(12)
                    }
                    .background(Color(hex: "1A1A2E"))
                    .onAppear {
                        if !logLines.isEmpty {
                            proxy.scrollTo(logLines.count - 1, anchor: .bottom)
                        }
                    }
                }
            }
        }
        .frame(minWidth: 700, minHeight: 450)
        .background(AngelaTheme.backgroundDark)
        .task {
            await fetchLogs()
        }
    }

    private func fetchLogs() async {
        isLoading = true
        do {
            let response = try await databaseService.fetchDaemonLogs(label: daemon.label)
            await MainActor.run {
                logLines = response.lines
                isLoading = false
            }
        } catch {
            await MainActor.run {
                logLines = ["Error loading logs: \(error.localizedDescription)"]
                isLoading = false
            }
        }
    }

    private func logLineColor(_ line: String) -> Color {
        let lower = line.lowercased()
        if lower.contains("error") || lower.contains("traceback") || lower.contains("exception") {
            return AngelaTheme.errorRed
        }
        if lower.contains("warning") || lower.contains("warn") {
            return AngelaTheme.warningOrange
        }
        if lower.contains("success") || lower.contains("completed") {
            return AngelaTheme.successGreen
        }
        return AngelaTheme.textSecondary
    }
}
