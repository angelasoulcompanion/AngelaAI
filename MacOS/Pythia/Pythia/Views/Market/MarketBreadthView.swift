//
//  MarketBreadthView.swift
//  Pythia — Market Breadth Indicators
//

import SwiftUI
import Charts

struct MarketBreadthView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var universes: [BreadthUniverse] = []
    @State private var selectedUniverse: String = "SET50"
    @State private var selectedPeriod: String = "1y"
    @State private var breadth: BreadthResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let periods = [("3mo", "3M"), ("6mo", "6M"), ("1y", "1Y"), ("2y", "2Y")]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                headerSection

                if isLoading {
                    LoadingView("Computing breadth indicators...")
                } else if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if let b = breadth, b.success {
                    regimeBadge(b.current)
                    summaryCards(b.current)
                    adLineChart(b)
                    pctAboveMAChart(b)
                    mcclEllanChart(b)
                    newHighsLowsChart(b)
                    trinChart(b)
                    divergenceAlerts(b.current)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadUniverses() }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Market Breadth")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            HStack(spacing: PythiaTheme.spacing) {
                Picker("Universe", selection: $selectedUniverse) {
                    ForEach(universes) { u in
                        Text("\(u.name) (\(u.size))").tag(u.id)
                    }
                }
                .frame(width: 200)

                ForEach(periods, id: \.0) { value, label in
                    Button(label) {
                        selectedPeriod = value
                        Task { await loadBreadth() }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(selectedPeriod == value ? PythiaTheme.primaryBlue : PythiaTheme.surfaceBackground)
                    .foregroundColor(selectedPeriod == value ? .white : PythiaTheme.textSecondary)
                    .cornerRadius(PythiaTheme.smallCornerRadius)
                }

                Button("Load") {
                    Task { await loadBreadth() }
                }
                .pythiaPrimaryButton()

                Spacer()
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Regime Badge

    private func regimeBadge(_ current: BreadthCurrent) -> some View {
        HStack(spacing: 12) {
            Circle()
                .fill(regimeColor(current.regime))
                .frame(width: 12, height: 12)

            Text(regimeLabel(current.regime))
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Text(current.regime.replacingOccurrences(of: "_", with: " ").uppercased())
                .font(PythiaTheme.caption())
                .fontWeight(.bold)
                .foregroundColor(regimeColor(current.regime))
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(regimeColor(current.regime).opacity(0.15))
                .cornerRadius(12)

            Spacer()

            if let size = breadth?.universeSize {
                Text("\(size) stocks")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Summary Cards

    private func summaryCards(_ current: BreadthCurrent) -> some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: PythiaTheme.spacing), count: 4), spacing: PythiaTheme.spacing) {
            MetricBox(
                "A/D Ratio",
                formatVal(current.adRatio, decimals: 2),
                (current.adRatio ?? 1) > 1 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
            MetricBox(
                "% > 200MA",
                formatPct(current.pctAbove200ma),
                (current.pctAbove200ma ?? 50) > 50 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
            MetricBox(
                "McClellan Osc",
                formatVal(current.mcclEllanOscillator, decimals: 1),
                (current.mcclEllanOscillator ?? 0) > 0 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
            MetricBox(
                "TRIN (10d)",
                formatVal(current.trin, decimals: 2),
                (current.trin ?? 1) < 1 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
        }
    }

    // MARK: - A/D Line Chart

    private func adLineChart(_ b: BreadthResponse) -> some View {
        let data = chartData(dates: b.dates, values: b.indicators.adLine)

        return VStack(alignment: .leading, spacing: 8) {
            Text("Advance/Decline Line")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(data) { point in
                AreaMark(x: .value("Date", point.date), y: .value("A/D", point.value))
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.08))
                LineMark(x: .value("Date", point.date), y: .value("A/D", point.value))
                    .foregroundStyle(PythiaTheme.secondaryBlue)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))
            }
            .frame(height: 200)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - % Above MA Chart

    private func pctAboveMAChart(_ b: BreadthResponse) -> some View {
        let data50 = chartData(dates: b.dates, values: b.indicators.pctAbove50ma, series: "50d MA")
        let data200 = chartData(dates: b.dates, values: b.indicators.pctAbove200ma, series: "200d MA")
        let allData = data50 + data200

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("% Above Moving Average")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                HStack(spacing: 12) {
                    legendDot(color: PythiaTheme.accentBlue, label: "50d")
                    legendDot(color: PythiaTheme.accentGold, label: "200d")
                }
            }

            Chart(allData) { point in
                AreaMark(
                    x: .value("Date", point.date),
                    y: .value("%", point.value)
                )
                .foregroundStyle(by: .value("Series", point.series))
                .opacity(0.08)

                LineMark(
                    x: .value("Date", point.date),
                    y: .value("%", point.value)
                )
                .foregroundStyle(by: .value("Series", point.series))
                .lineStyle(StrokeStyle(lineWidth: 1.5))

                // Reference lines
                RuleMark(y: .value("", 30))
                    .foregroundStyle(PythiaTheme.loss.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 50))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 70))
                    .foregroundStyle(PythiaTheme.profit.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
            }
            .chartForegroundStyleScale([
                "50d MA": PythiaTheme.accentBlue,
                "200d MA": PythiaTheme.accentGold,
            ])
            .chartYScale(domain: 0...100)
            .frame(height: 200)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - McClellan Oscillator

    private func mcclEllanChart(_ b: BreadthResponse) -> some View {
        let data = chartData(dates: b.dates, values: b.indicators.mcclEllanOscillator)

        return VStack(alignment: .leading, spacing: 8) {
            Text("McClellan Oscillator")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(data) { point in
                BarMark(
                    x: .value("Date", point.date),
                    y: .value("McClellan", point.value)
                )
                .foregroundStyle(point.value >= 0 ? PythiaTheme.profit : PythiaTheme.loss)

                RuleMark(y: .value("", 0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .frame(height: 180)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - New Highs vs Lows

    private func newHighsLowsChart(_ b: BreadthResponse) -> some View {
        let highs = chartData(dates: b.dates, values: b.indicators.newHighs, series: "New Highs")
        let lows = chartData(dates: b.dates, values: b.indicators.newLows.map { v in
            v.map { -$0 }  // flip lows negative
        }, series: "New Lows")
        let allData = highs + lows

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("New 52-Week Highs vs Lows")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                HStack(spacing: 12) {
                    legendDot(color: PythiaTheme.profit, label: "Highs")
                    legendDot(color: PythiaTheme.loss, label: "Lows")
                }
            }

            Chart(allData) { point in
                BarMark(
                    x: .value("Date", point.date),
                    y: .value("Count", point.value)
                )
                .foregroundStyle(by: .value("Series", point.series))

                RuleMark(y: .value("", 0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .chartForegroundStyleScale([
                "New Highs": PythiaTheme.profit,
                "New Lows": PythiaTheme.loss,
            ])
            .frame(height: 180)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - TRIN Chart

    private func trinChart(_ b: BreadthResponse) -> some View {
        let data = chartData(dates: b.dates, values: b.indicators.trin10dAvg)

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("TRIN (Arms Index) — 10d Avg")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("< 1.0 = Bullish")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            Chart(data) { point in
                LineMark(x: .value("Date", point.date), y: .value("TRIN", point.value))
                    .foregroundStyle(PythiaTheme.accentGold)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))

                // Zone rules
                RuleMark(y: .value("", 0.75))
                    .foregroundStyle(PythiaTheme.profit.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                    .annotation(position: .leading) {
                        Text("0.75")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundColor(PythiaTheme.profit.opacity(0.5))
                    }

                RuleMark(y: .value("", 1.0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))

                RuleMark(y: .value("", 1.25))
                    .foregroundStyle(PythiaTheme.loss.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                    .annotation(position: .leading) {
                        Text("1.25")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundColor(PythiaTheme.loss.opacity(0.5))
                    }
            }
            .frame(height: 180)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Divergence Alerts

    @ViewBuilder
    private func divergenceAlerts(_ current: BreadthCurrent) -> some View {
        if !current.divergences.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(PythiaTheme.warningOrange)
                    Text("Divergence Alerts")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)
                }

                ForEach(current.divergences, id: \.self) { msg in
                    HStack(alignment: .top, spacing: 8) {
                        Circle()
                            .fill(PythiaTheme.warningOrange)
                            .frame(width: 6, height: 6)
                            .padding(.top, 6)

                        Text(msg)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }
            .padding()
            .background(PythiaTheme.warningOrange.opacity(0.05))
            .overlay(RoundedRectangle(cornerRadius: PythiaTheme.cornerRadius).stroke(PythiaTheme.warningOrange.opacity(0.3), lineWidth: 1))
            .cornerRadius(PythiaTheme.cornerRadius)
        }
    }

    // MARK: - Data Loading

    private func loadUniverses() async {
        do {
            universes = try await db.fetchBreadthUniverses()
            if !universes.isEmpty {
                await loadBreadth()
            }
        } catch {
            errorMessage = "Failed to load universes: \(error.localizedDescription)"
        }
    }

    private func loadBreadth() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            breadth = try await db.fetchBreadth(universe: selectedUniverse, period: selectedPeriod)
        } catch {
            errorMessage = "Failed to load breadth: \(error.localizedDescription)"
        }
    }

    // MARK: - Helpers

    private func regimeColor(_ regime: String) -> Color {
        switch regime {
        case "strong_bull": return PythiaTheme.profit
        case "bull": return PythiaTheme.profit.opacity(0.7)
        case "neutral": return PythiaTheme.accentGold
        case "bear": return PythiaTheme.loss.opacity(0.7)
        case "strong_bear": return PythiaTheme.loss
        default: return PythiaTheme.textTertiary
        }
    }

    private func regimeLabel(_ regime: String) -> String {
        switch regime {
        case "strong_bull": return "Market Regime:"
        case "bull": return "Market Regime:"
        case "neutral": return "Market Regime:"
        case "bear": return "Market Regime:"
        case "strong_bear": return "Market Regime:"
        default: return "Market Regime:"
        }
    }

    private func formatVal(_ value: Double?, decimals: Int = 2) -> String {
        guard let v = value else { return "—" }
        return String(format: "%.\(decimals)f", v)
    }

    private func formatPct(_ value: Double?) -> String {
        guard let v = value else { return "—" }
        return String(format: "%.1f%%", v)
    }

    private func legendDot(color: Color, label: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }
}

// MARK: - Chart Data Helper

private struct ChartPoint: Identifiable {
    let id = UUID()
    let date: Date
    let value: Double
    let series: String
}

private let chartDateFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "yyyy-MM-dd"
    f.locale = Locale(identifier: "en_US_POSIX")
    return f
}()

private func chartData(dates: [String], values: [Double?], series: String = "default") -> [ChartPoint] {
    var points: [ChartPoint] = []
    let step = max(1, dates.count / 250)  // downsample to ~250 points for performance

    for i in stride(from: 0, to: dates.count, by: step) {
        guard let val = values[safe: i] ?? nil,
              let date = chartDateFormatter.date(from: dates[i]) else { continue }
        points.append(ChartPoint(date: date, value: val, series: series))
    }
    return points
}

private extension Collection {
    subscript(safe index: Index) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
