//
//  DashboardView.swift
//  AITop
//
//  Hardware monitoring dashboard with gauges — Gigabyte AI TOP style
//

import SwiftUI
import Charts

struct DashboardView: View {
    @EnvironmentObject var apiService: APIService
    @State private var dashboard: DashboardResponse?
    @State private var isLoading = true
    @State private var error: String?
    @State private var refreshTimer: Timer?

    var body: some View {
        ScrollView {
            VStack(spacing: AITopTheme.spacing) {
                // Header
                headerSection

                if isLoading && dashboard == nil {
                    ProgressView("Loading hardware stats...")
                        .foregroundColor(AITopTheme.textSecondary)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error {
                    errorView(error)
                } else if let dashboard {
                    // Gauges row
                    gaugesSection(dashboard.hardware)

                    // System info row (uptime, network, battery, thermal)
                    systemInfoRow(dashboard)

                    // Memory & Disk bars
                    barsSection(dashboard.hardware)

                    // Per-core CPU + Ollama side by side
                    HStack(alignment: .top, spacing: AITopTheme.spacing) {
                        perCoreCpuSection(dashboard.perCoreCpu ?? [])
                        ollamaSection(dashboard)
                    }

                    // Top processes
                    topProcessesSection(dashboard.topProcesses ?? [])
                }
            }
            .padding(AITopTheme.largeSpacing)
        }
        .background(AITopTheme.backgroundDark)
        .onAppear { startPolling() }
        .onDisappear { stopPolling() }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("AI TOP")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                Text("Hardware Monitor")
                    .font(AITopTheme.body())
                    .foregroundColor(AITopTheme.textSecondary)
            }
            Spacer()
            if let hw = dashboard?.hardware {
                HStack(spacing: 8) {
                    Text(hw.chip.chipName)
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.accentOrange)
                    Circle()
                        .fill(AITopTheme.success)
                        .frame(width: 10, height: 10)
                }
            }
        }
    }

    // MARK: - Gauges

    private func gaugesSection(_ hw: HardwareStats) -> some View {
        HStack(spacing: AITopTheme.spacing) {
            GaugeCard(title: "CPU", percent: hw.cpu.percent, subtitle: "\(hw.cpu.physicalCores) cores")
            GaugeCard(
                title: "GPU",
                percent: max(hw.gpu.percent, 0),
                subtitle: hw.gpu.vramUsedMb.map { "\($0) MB VRAM" } ?? "Unified"
            )
            GaugeCard(
                title: "Neural Engine",
                percent: hw.neuralEngine.usagePercent > 0 ? hw.neuralEngine.usagePercent : (hw.neuralEngine.active == true ? 50 : 0),
                subtitle: (hw.neuralEngine.active == true) ? "Active • \(hw.neuralEngine.cores) cores" : "Idle • \(hw.neuralEngine.cores) cores"
            )
            GaugeCard(title: "Memory", percent: hw.memory.percent, subtitle: String(format: "%.1f / %.0f GB", hw.memory.usedGb, hw.memory.totalGb))
        }
    }

    // MARK: - Bars

    private func barsSection(_ hw: HardwareStats) -> some View {
        VStack(spacing: AITopTheme.smallSpacing) {
            UsageBar(label: "Unified Memory", used: hw.memory.usedGb, total: hw.memory.totalGb, unit: "GB", color: AITopTheme.accentCyan)
            UsageBar(label: "SSD Storage", used: hw.disk.usedGb, total: hw.disk.totalGb, unit: "GB", color: AITopTheme.accentOrange)
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Ollama

    private func ollamaSection(_ dash: DashboardResponse) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            HStack {
                Text("Ollama")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                HStack(spacing: 6) {
                    Circle()
                        .fill(dash.ollama.running ? AITopTheme.success : AITopTheme.error)
                        .frame(width: 8, height: 8)
                    Text(dash.ollama.running ? "Running (\(dash.ollama.modelCount) models)" : "Not Running")
                        .font(AITopTheme.caption())
                        .foregroundColor(dash.ollama.running ? AITopTheme.success : AITopTheme.error)
                }
            }

            if !dash.runningModels.isEmpty {
                AITopDivider()
                ForEach(dash.runningModels.indices, id: \.self) { i in
                    let m = dash.runningModels[i]
                    HStack {
                        Image(systemName: "cpu.fill")
                            .foregroundColor(AITopTheme.accentOrange)
                        Text(m.name ?? m.model ?? "Unknown")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textPrimary)
                        Spacer()
                        if let size = m.size {
                            Text(AITopTheme.formatBytes(size))
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.textSecondary)
                        }
                    }
                }
            }

            HStack {
                Text("Thermal: \(dashboard?.hardware.thermalPressure ?? "—")")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                Spacer()
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - System Info Row

    private func systemInfoRow(_ dash: DashboardResponse) -> some View {
        HStack(spacing: AITopTheme.smallSpacing) {
            // Uptime
            if let uptime = dash.uptime {
                systemInfoCard("Uptime", value: uptime.label, icon: "power", color: AITopTheme.success)
            }

            // Thermal
            systemInfoCard(
                "Thermal",
                value: dash.hardware.thermalPressure.capitalized,
                icon: "thermometer.medium",
                color: dash.hardware.thermalPressure == "nominal" ? AITopTheme.success :
                       dash.hardware.thermalPressure == "moderate" ? AITopTheme.warning : AITopTheme.error
            )

            // Network
            if let net = dash.network {
                systemInfoCard("Network", value: net.ip, icon: "network", color: AITopTheme.accentCyan)
            }

            // Battery or Network IO
            if let bat = dash.battery {
                systemInfoCard(
                    bat.plugged ? "Charging" : "Battery",
                    value: "\(Int(bat.percent))%",
                    icon: bat.plugged ? "battery.100.bolt" : batteryIcon(bat.percent),
                    color: bat.percent > 20 ? AITopTheme.success : AITopTheme.error
                )
            } else if let net = dash.network {
                systemInfoCard(
                    "Net I/O",
                    value: String(format: "↑%.1f ↓%.1fGB", net.bytesSentGb, net.bytesRecvGb),
                    icon: "arrow.up.arrow.down.circle",
                    color: AITopTheme.brightOrange
                )
            }
        }
    }

    private func systemInfoCard(_ title: String, value: String, icon: String, color: Color) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(color)
            VStack(alignment: .leading, spacing: 1) {
                Text(value)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AITopTheme.textPrimary)
                    .lineLimit(1)
                Text(title)
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textTertiary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AITopTheme.smallSpacing + 2)
        .aiTopCard()
    }

    private func batteryIcon(_ percent: Double) -> String {
        if percent > 75 { return "battery.100" }
        if percent > 50 { return "battery.75" }
        if percent > 25 { return "battery.50" }
        return "battery.25"
    }

    // MARK: - Per-Core CPU

    private func perCoreCpuSection(_ cores: [Double]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("CPU Cores")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if cores.isEmpty {
                Text("No data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            } else {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 4), count: min(cores.count, 6)), spacing: 4) {
                    ForEach(cores.indices, id: \.self) { i in
                        VStack(spacing: 4) {
                            ZStack {
                                Circle()
                                    .stroke(AITopTheme.surfaceBackground, lineWidth: 4)
                                    .frame(width: 36, height: 36)
                                Circle()
                                    .trim(from: 0, to: min(cores[i], 100) / 100)
                                    .stroke(AITopTheme.gaugeColor(for: cores[i]), style: StrokeStyle(lineWidth: 4, lineCap: .round))
                                    .frame(width: 36, height: 36)
                                    .rotationEffect(.degrees(-90))
                                Text("\(Int(cores[i]))")
                                    .font(.system(size: 9, weight: .bold, design: .rounded))
                                    .foregroundColor(AITopTheme.textPrimary)
                            }
                            Text("C\(i)")
                                .font(.system(size: 8))
                                .foregroundColor(AITopTheme.textTertiary)
                        }
                    }
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Top Processes

    private func topProcessesSection(_ processes: [TopProcess]) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Top Processes")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            if processes.isEmpty {
                Text("No data")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            } else {
                // Header
                HStack {
                    Text("Process")
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text("MEM %")
                        .frame(width: 60, alignment: .trailing)
                    Text("CPU %")
                        .frame(width: 60, alignment: .trailing)
                    Text("")
                        .frame(width: 100)
                }
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(AITopTheme.textTertiary)

                AITopDivider()

                ForEach(processes) { proc in
                    HStack {
                        Text(proc.name)
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .lineLimit(1)

                        Text(String(format: "%.1f%%", proc.memoryPercent))
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(proc.memoryPercent > 5 ? AITopTheme.warning : AITopTheme.textSecondary)
                            .frame(width: 60, alignment: .trailing)

                        Text(String(format: "%.1f%%", proc.cpuPercent))
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(proc.cpuPercent > 50 ? AITopTheme.error : AITopTheme.textSecondary)
                            .frame(width: 60, alignment: .trailing)

                        // Memory bar
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 2)
                                    .fill(AITopTheme.surfaceBackground)
                                RoundedRectangle(cornerRadius: 2)
                                    .fill(AITopTheme.accentCyan.gradient)
                                    .frame(width: geo.size.width * min(proc.memoryPercent / 20.0, 1.0))
                            }
                        }
                        .frame(width: 100, height: 8)
                    }
                }
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Error View

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

    // MARK: - Data Loading

    private func startPolling() {
        loadData()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { _ in
            loadData()
        }
    }

    private func stopPolling() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    private func loadData() {
        Task {
            do {
                let result: DashboardResponse = try await apiService.getDashboard()
                await MainActor.run {
                    dashboard = result
                    isLoading = false
                    error = nil
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

// MARK: - Gauge Card Component

struct GaugeCard: View {
    let title: String
    let percent: Double
    let subtitle: String

    var body: some View {
        VStack(spacing: 8) {
            Text(title)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textSecondary)

            ZStack {
                // Background ring
                Circle()
                    .stroke(AITopTheme.surfaceBackground, lineWidth: 8)
                    .frame(width: 80, height: 80)

                // Progress ring
                Circle()
                    .trim(from: 0, to: min(max(percent, 0), 100) / 100)
                    .stroke(
                        AITopTheme.gaugeColor(for: percent),
                        style: StrokeStyle(lineWidth: 8, lineCap: .round)
                    )
                    .frame(width: 80, height: 80)
                    .rotationEffect(.degrees(-90))
                    .animation(.easeInOut(duration: 0.5), value: percent)

                // Percentage text
                Text(percent >= 0 ? "\(Int(percent))%" : "—")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
            }

            Text(subtitle)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textTertiary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity)
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }
}

// MARK: - Usage Bar Component

struct UsageBar: View {
    let label: String
    let used: Double
    let total: Double
    let unit: String
    let color: Color

    var percent: Double { total > 0 ? (used / total) * 100 : 0 }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label)
                    .font(AITopTheme.body())
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                Text(String(format: "%.1f / %.0f %@", used, total, unit))
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
            }

            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(AITopTheme.surfaceBackground)
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(color)
                        .frame(width: geometry.size.width * min(percent / 100, 1.0), height: 8)
                        .animation(.easeInOut(duration: 0.5), value: percent)
                }
            }
            .frame(height: 8)
        }
    }
}
