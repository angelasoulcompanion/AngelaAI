//
//  RegimeView.swift
//  Pythia — Market Regime Detection (Phase 7.1)
//

import SwiftUI
import Charts

struct RegimeView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var symbol = "^GSPC"
    @State private var regimeResult: RegimeResponse?
    @State private var history: [RegimeHistoryPoint] = []
    @State private var marketState: MarketStateResponse?
    @State private var isLoading = false
    @State private var showHistory = false

    private let quickSymbols = [
        ("S&P 500", "^GSPC"),
        ("SET", "^SET.BK"),
        ("Nikkei", "^N225"),
        ("VIX", "^VIX"),
        ("DAX", "^GDAXI"),
        ("ASX", "^AXJO"),
        ("Vietnam", "VNM"),
        ("HSI", "^HSI"),
        ("FTSE", "^FTSE"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Market Regime Detection")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    TextField("Symbol", text: $symbol)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 120)

                    ForEach(quickSymbols, id: \.1) { name, sym in
                        Button(name) { symbol = sym; Task { await detectRegime() } }
                            .buttonStyle(.plain)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(symbol == sym ? PythiaTheme.accentGold.opacity(0.2) : PythiaTheme.surfaceBackground)
                            .foregroundColor(symbol == sym ? PythiaTheme.accentGold : PythiaTheme.textSecondary)
                            .cornerRadius(8)
                    }

                    Button("Detect") { Task { await detectRegime() } }
                        .pythiaPrimaryButton()

                    Button("Market Overview") { Task { await fetchMarketState() } }
                        .pythiaPrimaryButton()

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Fitting HMM model...") }

                // Current Regime Card
                if let r = regimeResult, r.success {
                    currentRegimeCard(r)
                }

                // Market State Overview
                if let ms = marketState, ms.success {
                    marketStateCard(ms)
                }

                // Regime History Chart
                if !history.isEmpty {
                    regimeHistoryChart()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Current Regime Card

    private func currentRegimeCard(_ r: RegimeResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(r.symbol)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                regimeBadge(r.regime, probability: r.probability)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Regime", r.regime.uppercased(), regimeColor(r.regime), size: .large)
                MetricBox("Confidence", String(format: "%.1f%%", r.probability * 100), PythiaTheme.accentGold, size: .large)
                MetricBox("Volatility", String(format: "%.2f%%", r.volatility * 100), PythiaTheme.textPrimary, size: .large)
                MetricBox("Trend", String(format: "%+.3f", r.trendStrength), r.trendStrength > 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .large)
            }

            // Probability bars
            if let probs = r.allProbabilities {
                VStack(alignment: .leading, spacing: 8) {
                    Text("State Probabilities")
                        .font(PythiaTheme.heading())
                        .foregroundColor(PythiaTheme.textPrimary)

                    ForEach(["bull", "sideways", "bear", "crisis"], id: \.self) { regime in
                        if let prob = probs[regime] {
                            HStack {
                                Text(regime.capitalized)
                                    .font(PythiaTheme.caption())
                                    .foregroundColor(PythiaTheme.textSecondary)
                                    .frame(width: 70, alignment: .leading)

                                GeometryReader { geo in
                                    ZStack(alignment: .leading) {
                                        Rectangle()
                                            .fill(PythiaTheme.surfaceBackground)
                                            .frame(height: 20)
                                            .cornerRadius(4)

                                        Rectangle()
                                            .fill(regimeColor(regime))
                                            .frame(width: geo.size.width * CGFloat(prob), height: 20)
                                            .cornerRadius(4)
                                    }
                                }
                                .frame(height: 20)

                                Text(String(format: "%.1f%%", prob * 100))
                                    .font(PythiaTheme.caption())
                                    .foregroundColor(PythiaTheme.textSecondary)
                                    .frame(width: 50, alignment: .trailing)
                            }
                        }
                    }
                }
            }

            // Show/hide history
            Button(showHistory ? "Hide History" : "Show History") {
                if !showHistory {
                    Task { await fetchHistory() }
                }
                showHistory.toggle()
            }
            .buttonStyle(.plain)
            .foregroundColor(PythiaTheme.accentGold)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Market State Card

    private func marketStateCard(_ ms: MarketStateResponse) -> some View {
        let regions = ["Asia-Pacific", "Americas", "Europe", "Volatility"]
        let grouped = Dictionary(grouping: ms.components) { $0.region ?? "Other" }

        return VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text("Global Market State")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                regimeBadge(ms.overallRegime, probability: 0)
                riskBadge(ms.riskLevel)
            }

            ForEach(regions, id: \.self) { region in
                if let items = grouped[region], !items.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(region.uppercased())
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(PythiaTheme.accentGold)
                            .padding(.top, 4)

                        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 5), spacing: 10) {
                            ForEach(items) { comp in
                                VStack(spacing: 6) {
                                    Text(comp.name)
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(PythiaTheme.textPrimary)
                                        .lineLimit(1)

                                    regimeBadge(comp.regime, probability: comp.probability)

                                    HStack(spacing: 8) {
                                        Text(String(format: "Vol: %.1f%%", comp.volatility * 100))
                                            .font(.system(size: 10))
                                            .foregroundColor(PythiaTheme.textTertiary)

                                        Text(String(format: "%+.2f", comp.trendStrength))
                                            .font(.system(size: 10, weight: .medium))
                                            .foregroundColor(comp.trendStrength > 0 ? PythiaTheme.profit : PythiaTheme.loss)
                                    }
                                }
                                .padding(.vertical, 10)
                                .padding(.horizontal, 6)
                                .frame(maxWidth: .infinity)
                                .background(regimeColor(comp.regime).opacity(0.08))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(regimeColor(comp.regime).opacity(0.25), lineWidth: 1)
                                )
                                .cornerRadius(8)
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - History Chart

    private func regimeHistoryChart() -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Regime History")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(history) { point in
                RectangleMark(
                    x: .value("Date", point.date),
                    y: .value("Prob", point.probability)
                )
                .foregroundStyle(regimeColor(point.regime))
            }
            .chartYAxis {
                AxisMarks(values: [0, 0.25, 0.5, 0.75, 1.0]) { value in
                    AxisValueLabel {
                        Text(String(format: "%.0f%%", (value.as(Double.self) ?? 0) * 100))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }
            .frame(height: 200)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Helpers

    private func regimeBadge(_ regime: String, probability: Double) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(regimeColor(regime))
                .frame(width: 8, height: 8)
            Text(regime.uppercased())
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(regimeColor(regime))
            if probability > 0 {
                Text(String(format: "%.0f%%", probability * 100))
                    .font(.system(size: 11))
                    .foregroundColor(PythiaTheme.textSecondary)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(regimeColor(regime).opacity(0.15))
        .cornerRadius(8)
    }

    private func riskBadge(_ level: String) -> some View {
        let color: Color = switch level {
        case "low": PythiaTheme.profit
        case "normal": PythiaTheme.accentGold
        case "elevated": PythiaTheme.warningOrange
        case "high": PythiaTheme.errorRed
        default: PythiaTheme.textSecondary
        }
        return Text("Risk: \(level.uppercased())")
            .font(.system(size: 12, weight: .bold))
            .foregroundColor(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(color.opacity(0.15))
            .cornerRadius(8)
    }

    private func regimeColor(_ regime: String) -> Color {
        switch regime.lowercased() {
        case "bull": return PythiaTheme.profit
        case "bear": return PythiaTheme.loss
        case "sideways": return PythiaTheme.accentGold
        case "crisis": return PythiaTheme.errorRed
        default: return PythiaTheme.textSecondary
        }
    }

    // MARK: - API Calls

    private func detectRegime() async {
        isLoading = true
        defer { isLoading = false }
        do {
            regimeResult = try await db.get("/regime/\(symbol)?days=500", timeout: 60.0)
        } catch {
            regimeResult = nil
        }
    }

    private func fetchHistory() async {
        do {
            let resp: RegimeHistoryResponse = try await db.get("/regime/\(symbol)/history?days=365", timeout: 60.0)
            history = resp.history
        } catch {
            history = []
        }
    }

    private func fetchMarketState() async {
        isLoading = true
        defer { isLoading = false }
        do {
            marketState = try await db.get("/regime/market-state/overview", timeout: 120.0)
        } catch {
            marketState = nil
        }
    }
}
