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

                // Cross-Asset (Gold, Oil, 10Y, BTC, Copper)
                if let items = data.crossAsset, !items.isEmpty {
                    crossAssetRow(items)
                }

                // Yield Curve + Risk Regime (side by side)
                HStack(alignment: .top, spacing: 12) {
                    if let yc = data.yieldCurve {
                        yieldCurveCard(yc)
                    }
                    if let rr = data.riskRegime {
                        riskRegimeCard(rr)
                    }
                }

                // FX Strip
                if let pairs = data.fxPairs, !pairs.isEmpty {
                    fxStrip(pairs)
                }

                // Region Cards
                regionCards(data.regions)

                // Performance Ranking
                if let ranking = data.performanceRanking, !ranking.isEmpty {
                    performanceRankingSection(ranking)
                }

                // Global Heatmap
                heatmapSection(data.heatmap)

                // Economic Calendar
                if let events = data.economicCalendar, !events.isEmpty {
                    economicCalendarSection(events)
                }

                // 24h Trading Timeline
                timelineSection(data.timeline, utcTime: data.utcTime)

                // Headlines
                headlinesSection(data.headlines ?? [])
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
        VStack(alignment: .leading, spacing: 0) {
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

            // Futures hint (when market is closed)
            if let hint = idx.futuresHint, let pct = hint.changePercent {
                HStack(spacing: 4) {
                    Image(systemName: "arrow.triangle.swap")
                        .font(.system(size: 8))
                    Text(hint.name)
                        .font(.system(size: 10))
                    Text(String(format: "%+.2f%%", pct))
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundColor(PythiaTheme.profitLossColor(pct))
                }
                .foregroundColor(PythiaTheme.textTertiary)
                .padding(.top, 2)
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

    // MARK: - Headlines

    private func headlinesSection(_ headlines: [HeadlineItem]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "newspaper.fill")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Headlines")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("\(headlines.count) articles")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            if headlines.isEmpty {
                Text("No headlines available")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 20)
            } else {
                ForEach(headlines) { item in
                    headlineRow(item)
                }
            }
        }
        .padding(12)
        .pythiaCard()
    }

    private func headlineRow(_ item: HeadlineItem) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(item.title)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(PythiaTheme.textPrimary)
                .lineLimit(2)

            HStack(spacing: 8) {
                if !item.source.isEmpty {
                    Text(item.source)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(PythiaTheme.accentBlue)
                }
                if !item.published.isEmpty {
                    Text(formatTimeAgo(item.published))
                        .font(.system(size: 11))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
            }
        }
        .padding(.vertical, 6)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(alignment: .bottom) {
            Divider().background(PythiaTheme.textTertiary.opacity(0.2))
        }
        .onTapGesture {
            if let url = URL(string: item.url), !item.url.isEmpty {
                NSWorkspace.shared.open(url)
            }
        }
        .contentShape(Rectangle())
    }

    private func formatTimeAgo(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: dateString) ?? ISO8601DateFormatter().date(from: dateString) else {
            return dateString
        }
        let diff = Date().timeIntervalSince(date)
        if diff < 3600 { return "\(Int(diff / 60))m ago" }
        if diff < 86400 { return "\(Int(diff / 3600))h ago" }
        return "\(Int(diff / 86400))d ago"
    }

    // MARK: - Cross-Asset Row

    private func crossAssetRow(_ items: [CrossAssetItem]) -> some View {
        HStack(spacing: 12) {
            ForEach(items) { item in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Image(systemName: crossAssetIcon(item.name))
                            .font(.system(size: 12))
                            .foregroundColor(crossAssetColor(item.name))
                        Text(item.name)
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }

                    if let price = item.price {
                        Text(formatCrossAssetPrice(price, name: item.name))
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                            .foregroundColor(PythiaTheme.textPrimary)
                    } else {
                        Text("—")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(PythiaTheme.textTertiary)
                    }

                    if let pct = item.changePercent {
                        HStack(spacing: 2) {
                            Image(systemName: pct >= 0 ? "arrow.up.right" : "arrow.down.right")
                                .font(.system(size: 9))
                            Text(String(format: "%+.2f%%", pct))
                                .font(.system(size: 11, weight: .medium))
                        }
                        .foregroundColor(PythiaTheme.profitLossColor(pct))
                    }

                    Text(item.unit)
                        .font(.system(size: 9))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(10)
                .pythiaCard()
            }
        }
    }

    // MARK: - Yield Curve Card

    private func yieldCurveCard(_ yc: YieldCurveData) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "chart.line.flattrend.xyaxis")
                    .foregroundColor(yieldCurveStatusColor(yc.status))
                Text("Yield Curve")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(yc.status)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(yieldCurveStatusColor(yc.status))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(yieldCurveStatusColor(yc.status).opacity(0.15))
                    .cornerRadius(4)
            }

            // Yield points
            HStack(spacing: 16) {
                yieldPoint("3M", yc.t3m)
                yieldPoint("5Y", yc.t5y)
                yieldPoint("10Y", yc.t10y)
                yieldPoint("30Y", yc.t30y)
            }

            // Spread
            if let spread = yc.spread10y3m {
                HStack {
                    Text("10Y-3M Spread:")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text(String(format: "%+.2f%%", spread))
                        .font(.system(size: 13, weight: .bold, design: .monospaced))
                        .foregroundColor(spread < 0 ? PythiaTheme.errorRed : PythiaTheme.successGreen)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .pythiaCard()
    }

    private func yieldPoint(_ label: String, _ value: Double?) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value.map { String(format: "%.2f%%", $0) } ?? "—")
                .font(.system(size: 13, weight: .bold, design: .monospaced))
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    // MARK: - Risk Regime Card

    private func riskRegimeCard(_ rr: RiskRegimeData) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "gauge.with.dots.needle.50percent")
                    .foregroundColor(riskRegimeColor(rr.regime))
                Text("Risk Regime")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(rr.regime)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(riskRegimeColor(rr.regime))
            }

            // Gauge bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    // Background gradient bar
                    LinearGradient(
                        colors: [PythiaTheme.errorRed, PythiaTheme.warningOrange, PythiaTheme.successGreen],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                    .frame(height: 8)
                    .cornerRadius(4)

                    // Needle
                    Circle()
                        .fill(Color.white)
                        .frame(width: 14, height: 14)
                        .shadow(color: .black.opacity(0.3), radius: 2, x: 0, y: 1)
                        .offset(x: geo.size.width * CGFloat(rr.score) / 100 - 7)
                }
            }
            .frame(height: 14)

            HStack(spacing: 4) {
                Text("Risk-Off")
                    .font(.system(size: 9))
                    .foregroundColor(PythiaTheme.errorRed)
                Spacer()
                Text("Score: \(rr.score)")
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .foregroundColor(PythiaTheme.textSecondary)
                Spacer()
                Text("Risk-On")
                    .font(.system(size: 9))
                    .foregroundColor(PythiaTheme.successGreen)
            }

            // Indicators
            VStack(alignment: .leading, spacing: 4) {
                if let term = rr.vixTermStructure {
                    riskIndicator("VIX Term", term, term == "Contango" ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                }
                if let vix = rr.vix, let vix3m = rr.vix3m {
                    riskIndicator("VIX / VIX3M", String(format: "%.1f / %.1f", vix, vix3m), PythiaTheme.textSecondary)
                }
                if let hyg = rr.hygChange {
                    riskIndicator("HY Bonds", String(format: "%+.2f%%", hyg), PythiaTheme.profitLossColor(hyg))
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .pythiaCard()
    }

    private func riskIndicator(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textTertiary)
                .frame(width: 80, alignment: .leading)
            Text(value)
                .font(.system(size: 11, weight: .medium, design: .monospaced))
                .foregroundColor(color)
        }
    }

    // MARK: - FX Strip

    private func fxStrip(_ pairs: [FXPairItem]) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 16) {
                ForEach(pairs) { pair in
                    HStack(spacing: 6) {
                        Text(pair.name)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(PythiaTheme.textPrimary)
                        if let rate = pair.rate {
                            Text(formatFXRate(rate))
                                .font(.system(size: 12, weight: .medium, design: .monospaced))
                                .foregroundColor(PythiaTheme.accentBlue)
                        }
                        if let pct = pair.changePercent {
                            Text(String(format: "%+.2f%%", pct))
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundColor(PythiaTheme.profitLossColor(pct))
                        }
                    }

                    if pair.id != pairs.last?.id {
                        Rectangle()
                            .fill(PythiaTheme.textTertiary.opacity(0.3))
                            .frame(width: 1, height: 16)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
        .background(PythiaTheme.surfaceBackground.opacity(0.5))
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }

    // MARK: - Performance Ranking

    private func performanceRankingSection(_ ranking: [PerformanceRankItem]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "chart.bar.fill")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Today's Performance Ranking")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            let maxAbs = ranking.compactMap { $0.changePercent }.map { abs($0) }.max() ?? 1.0

            ForEach(ranking) { item in
                GeometryReader { geo in
                    let pct = item.changePercent ?? 0
                    let barRatio = abs(pct) / max(maxAbs, 0.01)
                    let halfWidth = geo.size.width / 2

                    ZStack(alignment: .leading) {
                        // Center line
                        Path { path in
                            path.move(to: CGPoint(x: halfWidth, y: 0))
                            path.addLine(to: CGPoint(x: halfWidth, y: geo.size.height))
                        }
                        .stroke(PythiaTheme.textTertiary.opacity(0.2), lineWidth: 1)

                        // Bar
                        let barWidth = halfWidth * barRatio
                        if pct >= 0 {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(PythiaTheme.successGreen.opacity(0.8))
                                .frame(width: barWidth, height: 14)
                                .offset(x: halfWidth)
                        } else {
                            RoundedRectangle(cornerRadius: 2)
                                .fill(PythiaTheme.errorRed.opacity(0.8))
                                .frame(width: barWidth, height: 14)
                                .offset(x: halfWidth - barWidth)
                        }

                        // Label (left)
                        HStack(spacing: 4) {
                            Text(item.flag)
                                .font(.system(size: 11))
                            Text(item.name)
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(PythiaTheme.textPrimary)
                        }
                        .offset(x: 4)

                        // Value (right)
                        Text(String(format: "%+.2f%%", pct))
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundColor(PythiaTheme.profitLossColor(pct))
                            .frame(maxWidth: .infinity, alignment: .trailing)
                            .padding(.trailing, 4)
                    }
                }
                .frame(height: 20)
            }
        }
        .padding(12)
        .pythiaCard()
    }

    // MARK: - Economic Calendar

    private func economicCalendarSection(_ events: [EconomicEvent]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "calendar.badge.clock")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Economic Calendar")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("Upcoming")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            ForEach(events) { event in
                HStack(spacing: 8) {
                    Text(event.flag)
                        .font(.system(size: 14))

                    VStack(alignment: .leading, spacing: 2) {
                        Text(event.event)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(PythiaTheme.textPrimary)
                        Text(formatEventDate(event.datetime))
                            .font(.system(size: 10))
                            .foregroundColor(PythiaTheme.textTertiary)
                    }

                    Spacer()

                    Text(event.countdown)
                        .font(.system(size: 11, weight: .medium, design: .monospaced))
                        .foregroundColor(PythiaTheme.accentBlue)

                    // Impact dot
                    Circle()
                        .fill(event.impact == "high" ? PythiaTheme.errorRed : PythiaTheme.warningOrange)
                        .frame(width: 8, height: 8)
                }
                .padding(.vertical, 4)
                .overlay(alignment: .bottom) {
                    Divider().background(PythiaTheme.textTertiary.opacity(0.2))
                }
            }
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

    // MARK: - New Section Helpers

    private func crossAssetIcon(_ name: String) -> String {
        switch name {
        case "Gold": return "sparkles"
        case "Crude Oil": return "drop.fill"
        case "10Y Yield": return "percent"
        case "Bitcoin": return "bitcoinsign.circle"
        case "Copper": return "cylinder.fill"
        default: return "chart.bar"
        }
    }

    private func crossAssetColor(_ name: String) -> Color {
        switch name {
        case "Gold": return PythiaTheme.accentGold
        case "Crude Oil": return PythiaTheme.warningOrange
        case "10Y Yield": return PythiaTheme.accentBlue
        case "Bitcoin": return Color(hex: "f7931a")
        case "Copper": return Color(hex: "b87333")
        default: return PythiaTheme.textSecondary
        }
    }

    private func formatCrossAssetPrice(_ price: Double, name: String) -> String {
        switch name {
        case "Bitcoin": return String(format: "$%.0f", price)
        case "10Y Yield": return String(format: "%.2f%%", price)
        case "Gold": return String(format: "$%.0f", price)
        default: return String(format: "%.2f", price)
        }
    }

    private func yieldCurveStatusColor(_ status: String) -> Color {
        switch status {
        case "Normal": return PythiaTheme.successGreen
        case "Flat": return PythiaTheme.warningOrange
        case "Inverted": return PythiaTheme.errorRed
        default: return PythiaTheme.textTertiary
        }
    }

    private func riskRegimeColor(_ regime: String) -> Color {
        switch regime {
        case "Risk-On": return PythiaTheme.successGreen
        case "Risk-Off": return PythiaTheme.errorRed
        default: return PythiaTheme.warningOrange
        }
    }

    private func formatFXRate(_ rate: Double) -> String {
        if rate > 100 { return String(format: "%.2f", rate) }
        return String(format: "%.4f", rate)
    }

    private func formatEventDate(_ iso: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        guard let date = formatter.date(from: iso) else { return iso }
        let df = DateFormatter()
        df.dateFormat = "MMM d, HH:mm 'UTC'"
        df.timeZone = TimeZone(identifier: "UTC")
        return df.string(from: date)
    }
}
