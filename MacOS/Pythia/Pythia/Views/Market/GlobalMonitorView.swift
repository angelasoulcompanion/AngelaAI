//
//  GlobalMonitorView.swift
//  Pythia
//
//  Global command center — 15 world indices, market status, heatmap, timeline
//

import SwiftUI

struct GlobalMonitorView: View {
    @EnvironmentObject var db: DatabaseService
    @EnvironmentObject var backend: BackendManager

    @State private var data: GlobalMonitorResponse?
    @State private var isLoading = true
    @State private var errorMsg: String?
    @State private var autoRefreshTask: Task<Void, Never>?

    var body: some View {
        Group {
            if isLoading && data == nil {
                LoadingView("Loading Global Monitor...")
            } else if let error = errorMsg, data == nil {
                EmptyStateView(
                    icon: "globe",
                    title: "Connection Error",
                    message: error,
                    actionTitle: "Retry"
                ) { Task { await load() } }
            } else if let data = data {
                monitorContent(data)
            }
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            while !backend.isConnected {
                try? await Task.sleep(nanoseconds: 500_000_000)
            }
            await load()
            startAutoRefresh()
        }
        .onDisappear {
            autoRefreshTask?.cancel()
        }
    }

    // MARK: - Main Content

    private func monitorContent(_ data: GlobalMonitorResponse) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                // Header
                headerBar(data)

                // Pulse Bar
                pulseBar(data.pulseBar)

                // KPI Cards
                kpiCards(data.summary)

                // Region Cards
                regionCards(data.regions)

                // Global Heatmap
                heatmapSection(data.heatmap)

                // 24h Trading Timeline
                timelineSection(data.timeline, utcTime: data.utcTime)

                // News placeholder
                newsSection()
            }
            .padding(PythiaTheme.largeSpacing)
        }
    }

    // MARK: - Header

    private func headerBar(_ data: GlobalMonitorResponse) -> some View {
        HStack {
            HStack(spacing: 8) {
                Image(systemName: "globe")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Global Monitor")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            Spacer()

            HStack(spacing: 12) {
                Text("UTC \(data.utcTime)")
                    .font(PythiaTheme.monospace())
                    .foregroundColor(PythiaTheme.textSecondary)

                Button {
                    Task { await load() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(PythiaTheme.textSecondary)
                        .rotationEffect(.degrees(isLoading ? 360 : 0))
                        .animation(isLoading ? .linear(duration: 1).repeatForever(autoreverses: false) : .default, value: isLoading)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Pulse Bar

    private func pulseBar(_ items: [PulseBarItem]) -> some View {
        // Deduplicate by exchange name
        let unique = items.reduce(into: [String: PulseBarItem]()) { dict, item in
            if dict[item.exchange] == nil { dict[item.exchange] = item }
        }
        let sorted = unique.values.sorted { $0.exchange < $1.exchange }

        return ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(sorted) { item in
                    HStack(spacing: 4) {
                        Circle()
                            .fill(item.isOpen ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                            .frame(width: 8, height: 8)
                        Text(item.exchange)
                            .font(.system(size: 12, weight: .medium, design: .monospaced))
                            .foregroundColor(item.isOpen ? PythiaTheme.textPrimary : PythiaTheme.textTertiary)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
        .background(PythiaTheme.surfaceBackground.opacity(0.5))
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }

    // MARK: - KPI Cards

    private func kpiCards(_ summary: GlobalSummary) -> some View {
        HStack(spacing: 12) {
            kpiCard(
                title: "Markets Open",
                value: "\(summary.marketsOpen)/\(summary.marketsTotal)",
                icon: "building.columns.fill",
                color: summary.marketsOpen > 0 ? PythiaTheme.successGreen : PythiaTheme.textTertiary
            )

            kpiCard(
                title: "VIX",
                value: summary.vix.map { String(format: "%.1f", $0) } ?? "—",
                icon: "waveform.path.ecg",
                color: (summary.vix ?? 0) > 25 ? PythiaTheme.errorRed :
                       (summary.vix ?? 0) > 20 ? PythiaTheme.warningOrange : PythiaTheme.successGreen,
                change: summary.vixChange
            )

            kpiCard(
                title: "DXY",
                value: summary.dxy.map { String(format: "%.1f", $0) } ?? "—",
                icon: "dollarsign.circle.fill",
                color: PythiaTheme.accentBlue,
                change: summary.dxyChange
            )

            kpiCard(
                title: "Sentiment",
                value: summary.sentiment,
                icon: sentimentIcon(summary.sentiment),
                color: sentimentColor(summary.sentiment),
                subtitle: summary.sentimentDetail
            )
        }
    }

    private func kpiCard(title: String, value: String, icon: String, color: Color, change: Double? = nil, subtitle: String? = nil) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 12))
                    .foregroundColor(color)
                Text(title)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
            }

            Text(value)
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundColor(PythiaTheme.textPrimary)

            if let change = change {
                HStack(spacing: 2) {
                    Image(systemName: change >= 0 ? "arrow.up.right" : "arrow.down.right")
                        .font(.system(size: 10))
                    Text(String(format: "%+.2f%%", change))
                        .font(.system(size: 11, weight: .medium))
                }
                .foregroundColor(PythiaTheme.profitLossColor(change))
            } else if let subtitle = subtitle {
                Text(subtitle)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .pythiaCard()
    }

    // MARK: - Region Cards

    private func regionCards(_ regions: [String: RegionData]) -> some View {
        let order = ["Americas", "Europe", "Asia-Pac"]
        let regionFlags = ["Americas": "\u{1F1FA}\u{1F1F8}", "Europe": "\u{1F1EC}\u{1F1E7}", "Asia-Pac": "\u{1F1F9}\u{1F1ED}"]

        return HStack(alignment: .top, spacing: 12) {
            ForEach(order, id: \.self) { region in
                if let regionData = regions[region] {
                    regionCard(name: region, flag: regionFlags[region] ?? "", data: regionData)
                }
            }
        }
    }

    private func regionCard(name: String, flag: String, data: RegionData) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            // Region header
            HStack {
                Text("\(name) \(flag)")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                HStack(spacing: 4) {
                    Circle()
                        .fill(data.isOpen ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                        .frame(width: 8, height: 8)
                    Text(data.isOpen ? "Open" : "Closed")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(data.isOpen ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                }
            }

            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

            // Index rows
            ForEach(data.indices) { idx in
                indexRow(idx)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .pythiaCard()
    }

    private func indexRow(_ idx: IndexData) -> some View {
        HStack(spacing: 8) {
            VStack(alignment: .leading, spacing: 2) {
                Text(idx.name)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(PythiaTheme.textPrimary)
                if let price = idx.currentPrice {
                    Text(formatCompactPrice(price))
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
            }

            Spacer()

            // Sparkline
            if idx.sparkline.count >= 2 {
                SparklineView(
                    data: idx.sparkline,
                    color: PythiaTheme.profitLossColor(idx.change ?? 0)
                )
                .frame(width: 50, height: 20)
            }

            // Change %
            if let pct = idx.changePercent {
                Text(String(format: "%+.1f%%", pct))
                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                    .foregroundColor(PythiaTheme.profitLossColor(pct))
                    .frame(width: 60, alignment: .trailing)
            } else {
                Text("—")
                    .font(.system(size: 13))
                    .foregroundColor(PythiaTheme.textTertiary)
                    .frame(width: 60, alignment: .trailing)
            }
        }
        .padding(.vertical, 3)
    }

    // MARK: - Heatmap

    private func heatmapSection(_ items: [HeatmapItem]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Global Heatmap")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            // Wrap in a flexible grid
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 6), count: min(items.count, 7)), spacing: 6) {
                ForEach(items) { item in
                    heatmapTile(item)
                }
            }
        }
        .padding(12)
        .pythiaCard()
    }

    private func heatmapTile(_ item: HeatmapItem) -> some View {
        let pct = item.changePercent ?? 0
        let bgColor = heatmapColor(pct)

        return VStack(spacing: 2) {
            Text(item.flag)
                .font(.system(size: 16))
            Text(shortName(item.name))
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(.white)
                .lineLimit(1)
            Text(String(format: "%+.1f%%", pct))
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundColor(.white)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(bgColor)
        .cornerRadius(6)
    }

    // MARK: - Timeline

    private func timelineSection(_ exchanges: [TimelineExchange], utcTime: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("24h Trading Hours (UTC)")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            GeometryReader { geo in
                let width = geo.size.width
                let hourWidth = width / 24.0

                ZStack(alignment: .topLeading) {
                    // Hour labels
                    ForEach([0, 3, 6, 9, 12, 15, 18, 21], id: \.self) { hour in
                        Text(String(format: "%02d", hour))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(PythiaTheme.textTertiary)
                            .position(x: CGFloat(hour) * hourWidth, y: 8)
                    }

                    // Exchange bars
                    ForEach(Array(exchanges.enumerated()), id: \.element.id) { idx, ex in
                        let y = CGFloat(idx) * 18 + 24
                        let x = CGFloat(ex.utcOpen) * hourWidth
                        let barWidth = CGFloat(ex.utcClose - ex.utcOpen) * hourWidth

                        // Bar
                        RoundedRectangle(cornerRadius: 3)
                            .fill(barColor(for: idx))
                            .frame(width: max(barWidth, 0), height: 12)
                            .position(x: x + barWidth / 2, y: y)

                        // Label
                        Text(ex.name)
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(.white)
                            .position(x: x + barWidth / 2, y: y)
                    }

                    // NOW indicator
                    let nowHour = currentUTCHour()
                    let nowX = CGFloat(nowHour) * hourWidth

                    Path { p in
                        p.move(to: CGPoint(x: nowX, y: 16))
                        p.addLine(to: CGPoint(x: nowX, y: CGFloat(exchanges.count) * 18 + 30))
                    }
                    .stroke(PythiaTheme.accentGold, style: StrokeStyle(lineWidth: 1.5, dash: [4, 3]))

                    // NOW label
                    Text("NOW")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(PythiaTheme.accentGold)
                        .position(x: nowX, y: CGFloat(exchanges.count) * 18 + 38)
                }
            }
            .frame(height: CGFloat(exchanges.count) * 18 + 48)
        }
        .padding(12)
        .pythiaCard()
    }

    // MARK: - News Placeholder

    private func newsSection() -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "newspaper.fill")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Headlines")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            Text("Connect angela-news MCP for live headlines")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, 20)
        }
        .padding(12)
        .pythiaCard()
    }

    // MARK: - Helpers

    private func load() async {
        isLoading = true
        errorMsg = nil
        do {
            let result: GlobalMonitorResponse = try await db.get("/global-monitor/", timeout: 60)
            data = result
        } catch {
            if data == nil { errorMsg = error.localizedDescription }
        }
        isLoading = false
    }

    private func startAutoRefresh() {
        autoRefreshTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 120_000_000_000) // 2 min
                if !Task.isCancelled { await load() }
            }
        }
    }

    private func sentimentIcon(_ s: String) -> String {
        switch s {
        case "Bullish": return "chart.line.uptrend.xyaxis"
        case "Bearish": return "chart.line.downtrend.xyaxis"
        default: return "equal.circle.fill"
        }
    }

    private func sentimentColor(_ s: String) -> Color {
        switch s {
        case "Bullish": return PythiaTheme.successGreen
        case "Bearish": return PythiaTheme.errorRed
        default: return PythiaTheme.warningOrange
        }
    }

    private func heatmapColor(_ pct: Double) -> Color {
        if pct > 1.5 { return Color(hex: "15803d") }      // dark green
        if pct > 0.5 { return Color(hex: "22c55e") }      // green
        if pct > 0   { return Color(hex: "4ade80") }      // light green
        if pct > -0.5 { return Color(hex: "f87171") }     // light red
        if pct > -1.5 { return Color(hex: "ef4444") }     // red
        return Color(hex: "b91c1c")                         // dark red
    }

    private func barColor(for index: Int) -> Color {
        let colors: [Color] = [
            PythiaTheme.secondaryBlue,
            PythiaTheme.accentBlue,
            Color(hex: "8b5cf6"),  // purple
            PythiaTheme.accentGold,
            PythiaTheme.successGreen,
            Color(hex: "06b6d4"),  // cyan
            Color(hex: "ec4899"),  // pink
            Color(hex: "f97316"),  // orange
            Color(hex: "14b8a6"),  // teal
            Color(hex: "a78bfa"),  // light purple
            Color(hex: "fb923c"),  // light orange
        ]
        return colors[index % colors.count]
    }

    private func currentUTCHour() -> Double {
        let cal = Calendar(identifier: .gregorian)
        let utc = TimeZone(identifier: "UTC")!
        var components = cal.dateComponents(in: utc, from: Date())
        return Double(components.hour ?? 0) + Double(components.minute ?? 0) / 60.0
    }

    private func formatCompactPrice(_ price: Double) -> String {
        if price >= 10000 {
            return String(format: "%.0f", price)
        } else if price >= 100 {
            return String(format: "%.1f", price)
        } else {
            return String(format: "%.2f", price)
        }
    }

    private func shortName(_ name: String) -> String {
        // Shorten for heatmap tiles
        let map: [String: String] = [
            "S&P 500": "S&P",
            "Dow Jones": "DOW",
            "NASDAQ": "NDX",
            "Bovespa": "BVSP",
            "FTSE 100": "FTSE",
            "CAC 40": "CAC",
            "SET Index": "SET",
            "Nikkei 225": "N225",
            "Hang Seng": "HSI",
            "ASX 200": "ASX",
            "KOSPI": "KOS",
            "Shanghai": "SHCOMP",
        ]
        return map[name] ?? name
    }
}
