//
//  OptionStrategyView.swift
//  Pythia — Multi-leg Option Strategy Builder
//

import SwiftUI
import Charts

struct OptionStrategyView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var spot: String = "100"
    @State private var volatility: String = "0.20"
    @State private var expiry: Double = 0.25
    @State private var width: String = ""
    @State private var selectedStrategy: String = "bull_call_spread"
    @State private var data: StrategyResponse?
    @State private var isLoading = false
    @State private var errorMsg: String?
    @State private var scanData: WatchlistScanResponse?
    @State private var scanLoading = false
    @State private var watchlistName: String = "Angles"
    @State private var watchlists: [String] = []

    private let strategies = [
        ("bull_call_spread",  "Bull Call Spread",  "📈"),
        ("bear_put_spread",   "Bear Put Spread",   "📉"),
        ("long_straddle",     "Long Straddle",     "↕️"),
        ("long_strangle",     "Long Strangle",     "⇕"),
        ("iron_condor",       "Iron Condor",       "🦅"),
        ("butterfly",         "Butterfly Spread",  "🦋"),
        ("covered_call",      "Covered Call",      "🛡️"),
        ("protective_put",    "Protective Put",    "🔒"),
    ]

    private let expiryOptions: [(String, Double)] = [
        ("1M", 1.0/12), ("3M", 0.25), ("6M", 0.5), ("1Y", 1.0),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header
                HStack {
                    HStack(spacing: 8) {
                        Image(systemName: "puzzlepiece.fill")
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(PythiaTheme.accentGold)
                        Text("Option Strategy Builder")
                            .font(PythiaTheme.title())
                            .foregroundColor(PythiaTheme.textPrimary)
                    }
                    Spacer()
                }

                // Control bar
                controlBar()

                // Watchlist Scanner
                watchlistScannerSection()

                Divider().background(PythiaTheme.textTertiary.opacity(0.2)).padding(.vertical, 4)

                // Single Strategy Builder
                if isLoading {
                    LoadingView("Computing strategy...")
                } else if let error = errorMsg {
                    ErrorMessageView(message: error)
                } else if let data = data {
                    strategyContent(data)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .task {
            await loadWatchlists()
        }
    }

    private func loadWatchlists() async {
        struct WLItem: Codable { let name: String }
        do {
            let items: [WLItem] = try await db.get("/watchlists/", timeout: 10)
            let names = items.map { $0.name }
            watchlists = names
            if !names.isEmpty && !names.contains(watchlistName) {
                watchlistName = names.first ?? "Angles"
            }
        } catch {
            watchlists = ["Angles"]
        }
    }

    // MARK: - Controls

    private func controlBar() -> some View {
        VStack(spacing: 10) {
            HStack(spacing: 12) {
                // Strategy picker
                VStack(alignment: .leading, spacing: 2) {
                    Text("Strategy")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(PythiaTheme.textTertiary)
                    Picker("", selection: $selectedStrategy) {
                        ForEach(strategies, id: \.0) { s in
                            Text("\(s.2) \(s.1)").tag(s.0)
                        }
                    }
                    .frame(width: 200)
                }

                // Spot price
                VStack(alignment: .leading, spacing: 2) {
                    Text("Spot Price")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(PythiaTheme.textTertiary)
                    TextField("100", text: $spot)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 80)
                }

                // Volatility
                VStack(alignment: .leading, spacing: 2) {
                    Text("Volatility (σ)")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(PythiaTheme.textTertiary)
                    TextField("0.20", text: $volatility)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 70)
                }

                // Width
                VStack(alignment: .leading, spacing: 2) {
                    Text("Width (0=auto)")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(PythiaTheme.textTertiary)
                    TextField("auto", text: $width)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 70)
                }

                // Expiry
                VStack(alignment: .leading, spacing: 2) {
                    Text("Expiry")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(PythiaTheme.textTertiary)
                    Picker("", selection: $expiry) {
                        ForEach(expiryOptions, id: \.1) { opt in
                            Text(opt.0).tag(opt.1)
                        }
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 180)
                }

                Button {
                    Task { await analyze() }
                } label: {
                    Text("Build Strategy")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(PythiaTheme.accentGold)
                        .cornerRadius(8)
                }
            }
        }
        .padding(12)
        .pythiaCard()
    }

    // MARK: - Strategy Content

    private func strategyContent(_ data: StrategyResponse) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // Strategy header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(data.strategy.name)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(data.strategy.description)
                        .font(.system(size: 12))
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                Spacer()
                Text(data.strategy.outlook)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 5)
                    .background(PythiaTheme.secondaryBlue)
                    .cornerRadius(12)
            }

            // KPI Cards
            HStack(spacing: 12) {
                kpiBox("Net Cost", String(format: "%.4f", data.netCost), data.netCost < 0 ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                kpiBox("Max Profit", String(format: "%.4f", data.maxProfit), PythiaTheme.successGreen)
                kpiBox("Max Loss", String(format: "%.4f", data.maxLoss), PythiaTheme.errorRed)
                kpiBox("Risk/Reward", data.riskRewardRatio.map { String(format: "%.2f", $0) } ?? "∞", PythiaTheme.accentBlue)
                kpiBox("Breakeven", data.breakevens.map { String(format: "%.2f", $0) }.joined(separator: ", "), PythiaTheme.accentGold)
            }

            // P&L Diagram + Legs side by side
            HStack(alignment: .top, spacing: 12) {
                // P&L Chart
                VStack(alignment: .leading, spacing: 8) {
                    Text("📊 Strategy P&L Diagram")
                        .font(PythiaTheme.heading())
                        .foregroundColor(PythiaTheme.textPrimary)
                    payoffChart(data)
                }
                .padding(12)
                .pythiaCard()
                .frame(minWidth: 0, maxWidth: .infinity)

                // Legs + Greeks
                VStack(alignment: .leading, spacing: 12) {
                    legsTable(data)
                    greeksCard(data)
                }
                .frame(width: 340)
            }
        }
    }

    // MARK: - KPI Box

    private func kpiBox(_ title: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(title)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(.system(size: 14, weight: .bold, design: .monospaced))
                .foregroundColor(color)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .pythiaCard()
    }

    // MARK: - Payoff Chart

    private func payoffChart(_ data: StrategyResponse) -> some View {
        let curve = data.payoffCurve
        let spotLine = data.spot

        struct ChartPoint: Identifiable {
            let id = UUID()
            let spot: Double
            let value: Double
            let series: String
        }

        var points: [ChartPoint] = []
        for i in 0..<min(curve.spotRange.count, curve.payoffAtExpiry.count) {
            points.append(ChartPoint(spot: curve.spotRange[i], value: curve.payoffAtExpiry[i], series: "At Expiry"))
        }
        for i in 0..<min(curve.spotRange.count, curve.valueNow.count) {
            points.append(ChartPoint(spot: curve.spotRange[i], value: curve.valueNow[i], series: "Current Value"))
        }

        let allVals = points.map { $0.value }
        let yMin = (allVals.min() ?? 0) * 1.15
        let yMax = (allVals.max() ?? 0) * 1.15

        return Chart {
            // Zero line
            RuleMark(y: .value("Zero", 0))
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [4]))
                .foregroundStyle(PythiaTheme.textTertiary.opacity(0.5))

            // Spot line
            RuleMark(x: .value("Spot", spotLine))
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [4]))
                .foregroundStyle(PythiaTheme.accentGold.opacity(0.7))
                .annotation(position: .top) {
                    Text("Spot")
                        .font(.system(size: 9))
                        .foregroundColor(PythiaTheme.accentGold)
                }

            // Strike lines
            ForEach(data.legs) { leg in
                if leg.optionType != "stock" {
                    RuleMark(x: .value("K", leg.strike))
                        .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [3]))
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                }
            }

            // Payoff curves
            ForEach(points) { pt in
                LineMark(x: .value("Spot", pt.spot), y: .value("P&L", pt.value))
                    .foregroundStyle(by: .value("Series", pt.series))
                    .lineStyle(StrokeStyle(lineWidth: pt.series == "At Expiry" ? 2.5 : 1.5,
                                           dash: pt.series == "At Expiry" ? [] : [5, 3]))
            }

            // Breakeven markers
            ForEach(data.breakevens, id: \.self) { be in
                PointMark(x: .value("BE", be), y: .value("P&L", 0))
                    .foregroundStyle(PythiaTheme.warningOrange)
                    .symbolSize(40)
                    .annotation(position: .bottom) {
                        Text(String(format: "%.1f", be))
                            .font(.system(size: 8))
                            .foregroundColor(PythiaTheme.warningOrange)
                    }
            }
        }
        .chartForegroundStyleScale([
            "At Expiry": Color(hex: "22c55e"),
            "Current Value": Color(hex: "3b82f6"),
        ])
        .chartYScale(domain: yMin...yMax)
        .chartXAxisLabel("Spot Price")
        .chartYAxisLabel("Profit / Loss")
        .chartLegend(position: .top)
        .frame(height: 300)
    }

    // MARK: - Legs Table

    private func legsTable(_ data: StrategyResponse) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("📋 Strategy Legs")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            ForEach(data.legs) { leg in
                HStack {
                    // Position badge
                    Text(leg.position == "long" ? "BUY" : "SELL")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(leg.position == "long" ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                        .cornerRadius(4)

                    Text("\(leg.quantity)x")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundColor(PythiaTheme.textSecondary)

                    Text(leg.optionType.capitalized)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(PythiaTheme.textPrimary)

                    Text("K=\(String(format: "%.1f", leg.strike))")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(PythiaTheme.textSecondary)

                    Spacer()

                    Text(String(format: "%.4f", leg.price))
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundColor(PythiaTheme.accentGold)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .background(PythiaTheme.surfaceBackground.opacity(0.5))
                .cornerRadius(6)
            }
        }
        .padding(12)
        .pythiaCard()
    }

    // MARK: - Combined Greeks

    private func greeksCard(_ data: StrategyResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("📐 Combined Greeks")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            let greeks = data.combinedGreeks
            let items: [(String, String, Double)] = [
                ("Δ", "Delta", greeks.delta),
                ("Γ", "Gamma", greeks.gamma),
                ("Θ", "Theta", greeks.theta),
                ("ν", "Vega", greeks.vega),
                ("ρ", "Rho", greeks.rho),
            ]

            ForEach(items, id: \.1) { symbol, name, value in
                HStack {
                    Text(symbol)
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(PythiaTheme.accentGold)
                        .frame(width: 20)
                    Text(name)
                        .font(.system(size: 12))
                        .foregroundColor(PythiaTheme.textSecondary)
                    Spacer()
                    Text(String(format: "%+.6f", value))
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundColor(value >= 0 ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                }
            }
        }
        .padding(12)
        .pythiaCard()
    }

    // MARK: - Watchlist Scanner

    private func watchlistScannerSection() -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "bolt.shield.fill")
                        .foregroundColor(PythiaTheme.accentGold)
                    Text("Watchlist Strategy Scanner")
                        .font(PythiaTheme.heading())
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                Spacer()

                Picker("", selection: $watchlistName) {
                    ForEach(watchlists, id: \.self) { name in
                        Text(name).tag(name)
                    }
                }
                .frame(width: 160)

                Button {
                    Task { await scanWatchlist() }
                } label: {
                    HStack(spacing: 4) {
                        if scanLoading {
                            ProgressView().controlSize(.small)
                        }
                        Text("Scan & Optimize")
                            .font(.system(size: 12, weight: .bold))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 7)
                    .background(PythiaTheme.successGreen)
                    .cornerRadius(8)
                }
                .disabled(scanLoading)
            }

            if let scan = scanData {
                Text("\(scan.count) assets scanned — ranked by gain potential")
                    .font(.system(size: 11))
                    .foregroundColor(PythiaTheme.textTertiary)

                // Results table
                VStack(spacing: 0) {
                    // Header
                    HStack(spacing: 0) {
                        Text("#").frame(width: 30, alignment: .leading)
                        Text("Symbol").frame(width: 80, alignment: .leading)
                        Text("Spot").frame(width: 70, alignment: .trailing)
                        Text("Vol").frame(width: 55, alignment: .trailing)
                        Text("Direction").frame(width: 80, alignment: .center)
                        Text("Strategy").frame(minWidth: 140, alignment: .leading)
                        Text("Max Profit").frame(width: 80, alignment: .trailing)
                        Text("Max Loss").frame(width: 80, alignment: .trailing)
                        Text("R/R").frame(width: 50, alignment: .trailing)
                        Text("Score").frame(width: 55, alignment: .trailing)
                    }
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(PythiaTheme.textTertiary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .background(PythiaTheme.surfaceBackground.opacity(0.5))

                    ForEach(Array(scan.results.enumerated()), id: \.element.id) { idx, r in
                        if r.error == nil {
                            HStack(spacing: 0) {
                                Text("\(idx + 1)").frame(width: 30, alignment: .leading)
                                    .foregroundColor(PythiaTheme.textTertiary)
                                Text(r.symbol).frame(width: 80, alignment: .leading)
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundColor(PythiaTheme.accentBlue)
                                Text(r.spot.map { String(format: "%.1f", $0) } ?? "—")
                                    .frame(width: 70, alignment: .trailing)
                                    .font(.system(size: 11, design: .monospaced))
                                Text(r.volatility.map { String(format: "%.0f%%", $0 * 100) } ?? "—")
                                    .frame(width: 55, alignment: .trailing)
                                    .font(.system(size: 11, design: .monospaced))

                                // Direction badge
                                HStack(spacing: 3) {
                                    Circle()
                                        .fill(directionColor(r.direction ?? ""))
                                        .frame(width: 6, height: 6)
                                    Text((r.direction ?? "").capitalized)
                                        .font(.system(size: 10, weight: .semibold))
                                        .foregroundColor(directionColor(r.direction ?? ""))
                                }
                                .frame(width: 80)

                                Text(r.strategy?.name ?? "—")
                                    .frame(minWidth: 140, alignment: .leading)
                                    .font(.system(size: 11))
                                    .foregroundColor(PythiaTheme.textPrimary)
                                    .lineLimit(1)

                                Text(r.maxProfit.map { String(format: "%.2f", $0) } ?? "—")
                                    .frame(width: 80, alignment: .trailing)
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(PythiaTheme.successGreen)

                                Text(r.maxLoss.map { String(format: "%.2f", $0) } ?? "—")
                                    .frame(width: 80, alignment: .trailing)
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundColor(PythiaTheme.errorRed)

                                Text(r.riskReward.map { String(format: "%.1f", $0) } ?? "—")
                                    .frame(width: 50, alignment: .trailing)
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))

                                // Gain score bar
                                HStack(spacing: 4) {
                                    Text(String(format: "%.1f", r.gainScore ?? 0))
                                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                                        .foregroundColor(PythiaTheme.accentGold)
                                    Rectangle()
                                        .fill(PythiaTheme.accentGold)
                                        .frame(width: max(CGFloat(r.gainScore ?? 0) * 8, 2), height: 8)
                                        .cornerRadius(2)
                                }
                                .frame(width: 55, alignment: .trailing)
                            }
                            .font(.system(size: 11))
                            .foregroundColor(PythiaTheme.textSecondary)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(idx % 2 == 0 ? Color.clear : PythiaTheme.surfaceBackground.opacity(0.2))
                            .contentShape(Rectangle())
                            .onTapGesture { fillFromScan(r) }
                        }
                    }
                }
                .cornerRadius(8)
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(PythiaTheme.textTertiary.opacity(0.15)))
            }
        }
        .padding(12)
        .pythiaCard()
    }

    private func directionColor(_ dir: String) -> Color {
        switch dir {
        case "bullish": return PythiaTheme.successGreen
        case "bearish": return PythiaTheme.errorRed
        default: return PythiaTheme.warningOrange
        }
    }

    private func fillFromScan(_ r: WatchlistScanResult) {
        if let s = r.spot { spot = String(format: "%.2f", s) }
        if let v = r.volatility { volatility = String(format: "%.2f", v) }
        if let key = r.strategyKey, strategies.contains(where: { $0.0 == key }) {
            selectedStrategy = key
        }
        // Auto-build
        Task { await analyze() }
    }

    private func scanWatchlist() async {
        scanLoading = true
        do {
            let result: WatchlistScanResponse = try await db.get(
                "/options/strategy/watchlist-scan?watchlist_name=\(watchlistName.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? watchlistName)&time_to_expiry=\(expiry)",
                timeout: 120
            )
            scanData = result
        } catch {
            // silent — show empty
        }
        scanLoading = false
    }

    // MARK: - Load

    private func analyze() async {
        guard let spotVal = Double(spot), spotVal > 0 else {
            errorMsg = "Invalid spot price"
            return
        }
        let vol = Double(volatility) ?? 0.20
        let w = Double(width) ?? 0

        isLoading = true
        errorMsg = nil
        do {
            let endpoint = "/options/strategy/preset/\(selectedStrategy)?spot=\(spotVal)&time_to_expiry=\(expiry)&risk_free_rate=0.0225&volatility=\(vol)&width=\(w)"
            print("[OptionStrategy] GET \(endpoint)")
            let result: StrategyResponse = try await db.get(endpoint, timeout: 30)
            data = result
            print("[OptionStrategy] Success: \(result.strategy.name)")
        } catch {
            errorMsg = error.localizedDescription
            print("[OptionStrategy] Error: \(error)")
        }
        isLoading = false
    }
}
