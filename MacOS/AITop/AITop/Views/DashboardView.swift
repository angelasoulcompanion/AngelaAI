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

                    // Memory & Disk bars
                    barsSection(dashboard.hardware)

                    // Ollama status + running models
                    ollamaSection(dashboard)
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
                percent: (hw.neuralEngine.active == true) ? 100 : 0,
                subtitle: hw.neuralEngine.powerMw.map { $0 > 0 ? "\($0) mW" : "\(hw.neuralEngine.cores) cores" } ?? "\(hw.neuralEngine.cores) cores"
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
