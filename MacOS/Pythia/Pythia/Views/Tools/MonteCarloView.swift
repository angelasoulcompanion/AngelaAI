//
//  MonteCarloView.swift
//  Pythia — Monte Carlo GBM Simulation
//

import SwiftUI
import Charts

// Rainbow palette for multi-color simulation paths
private let mcRainbowPalette: [Color] = [
    .red, .blue, .green, .purple, .orange,
    .cyan, .pink, .yellow, .mint, .indigo,
    Color(hex: "DC2626"), Color(hex: "059669"), Color(hex: "7C3AED"),
    Color(hex: "0891B2"), Color(hex: "CA8A04"), Color(hex: "BE185D")
]

// Pre-computed point for sample paths — avoids Swift type-checker explosion
private struct PathPoint: Identifiable {
    let id: Int          // unique across all points
    let pathIndex: Int
    let step: Int
    let price: Double
    let colorIndex: Int
}

// Pre-computed histogram bin
private struct MCHistBin: Identifiable {
    let id: Int
    let mid: Double
    let count: Int
    let aboveCurrent: Bool
}

struct MonteCarloView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var simulations = 10000
    @State private var steps = 252
    @State private var result: MonteCarloResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Monte Carlo Simulation")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    Picker("Simulations", selection: $simulations) {
                        Text("1,000").tag(1000)
                        Text("10,000").tag(10000)
                        Text("50,000").tag(50000)
                    }
                    .frame(width: 180)

                    Picker("Horizon", selection: $steps) {
                        Text("63 days (3M)").tag(63)
                        Text("126 days (6M)").tag(126)
                        Text("252 days (1Y)").tag(252)
                    }
                    .frame(width: 200)

                    Button("Simulate") { Task { await simulate() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if isLoading { LoadingView("Running \(simulations) simulations...") }

                if let r = result, r.success {
                    statsCard(r)
                    fanChart(r)

                    samplePathsChart(r)
                    distributionChart(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        
    }

    private func statsCard(_ r: MonteCarloResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(r.symbol) — \(r.nSimulations) Simulations")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("Current: \(PythiaTheme.formatCurrency(r.currentPrice))")
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.accentGold)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Mean", PythiaTheme.formatCurrency(r.statistics.meanFinalPrice), PythiaTheme.textPrimary, size: .small)
                MetricBox("Median", PythiaTheme.formatCurrency(r.statistics.medianFinalPrice), PythiaTheme.secondaryBlue, size: .small)
                MetricBox("5th %ile", PythiaTheme.formatCurrency(r.statistics.percentile5), PythiaTheme.loss, size: .small)
                MetricBox("95th %ile", PythiaTheme.formatCurrency(r.statistics.percentile95), PythiaTheme.profit, size: .small)
                MetricBox("P(Above)", PythiaTheme.formatPercent(r.statistics.probAboveCurrent),
                          r.statistics.probAboveCurrent > 0.5 ? PythiaTheme.profit : PythiaTheme.loss, size: .small)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Expected Return", PythiaTheme.formatPercent(r.parameters.expectedReturn), PythiaTheme.textSecondary, size: .small)
                MetricBox("Volatility", PythiaTheme.formatPercent(r.parameters.volatility), PythiaTheme.accentGold, size: .small)
                MetricBox("Std Dev", PythiaTheme.formatCurrency(r.statistics.stdFinalPrice), PythiaTheme.textTertiary, size: .small)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func fanChart(_ r: MonteCarloResponse) -> some View {
        // Auto-fit Y domain from data — prevent AreaMark from anchoring to 0
        let yMin = r.percentileBands.map(\.p5).min() ?? r.currentPrice
        let yMax = r.percentileBands.map(\.p95).max() ?? r.currentPrice
        let yPad = max((yMax - yMin) * 0.1, 1.0)

        return VStack(alignment: .leading, spacing: 8) {
            Text("Price Fan Chart (Percentile Bands)")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart {
                // 5-95 band
                ForEach(r.percentileBands) { band in
                    AreaMark(
                        x: .value("Step", band.step),
                        yStart: .value("P5", band.p5),
                        yEnd: .value("P95", band.p95)
                    )
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.15))
                }

                // 25-75 band
                ForEach(r.percentileBands) { band in
                    AreaMark(
                        x: .value("Step", band.step),
                        yStart: .value("P25", band.p25),
                        yEnd: .value("P75", band.p75)
                    )
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.30))
                }

                // Median line
                ForEach(r.percentileBands) { band in
                    LineMark(
                        x: .value("Step", band.step),
                        y: .value("Median", band.p50)
                    )
                    .foregroundStyle(PythiaTheme.accentGold)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                }

                // Current price reference
                RuleMark(y: .value("Current", r.currentPrice))
                    .foregroundStyle(PythiaTheme.textTertiary)
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [5]))
            }
            .chartYScale(domain: (yMin - yPad)...(yMax + yPad))
            .chartXAxisLabel("Trading Days")
            .chartYAxisLabel("Price")
            .pythiaChartAxes(gridOpacity: 0.2)
            .frame(height: 350)

            // Legend
            HStack(spacing: 16) {
                legendItem(color: PythiaTheme.accentGold, label: "Median")
                legendItem(color: PythiaTheme.secondaryBlue.opacity(0.5), label: "25th-75th %ile")
                legendItem(color: PythiaTheme.secondaryBlue.opacity(0.25), label: "5th-95th %ile")
                HStack(spacing: 4) {
                    Rectangle()
                        .stroke(PythiaTheme.textTertiary, style: StrokeStyle(lineWidth: 1, dash: [4]))
                        .frame(width: 16, height: 1)
                    Text("Current Price")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func legendItem(color: Color, label: String) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }

    // MARK: - Sample Paths Chart

    private func buildPathPoints(_ r: MonteCarloResponse) -> [PathPoint] {
        var points = [PathPoint]()
        var uid = 0
        let paletteSize = mcRainbowPalette.count
        // Limit to 30 paths for SwiftUI Charts performance
        let maxPaths = min(r.samplePaths.count, 30)
        for pIdx in 0..<maxPaths {
            let path = r.samplePaths[pIdx]
            let cIdx = pIdx % paletteSize
            for (sIdx, price) in path.enumerated() {
                points.append(PathPoint(id: uid, pathIndex: pIdx, step: sIdx, price: price, colorIndex: cIdx))
                uid += 1
            }
        }
        return points
    }

    private func samplePathsChart(_ r: MonteCarloResponse) -> some View {
        let points = buildPathPoints(r)
        let priceMin = points.map(\.price).min() ?? r.currentPrice
        let priceMax = points.map(\.price).max() ?? r.currentPrice
        let pad = max((priceMax - priceMin) * 0.05, 1.0)

        return VStack(alignment: .leading, spacing: 8) {
            Text("Sample Simulation Paths")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            samplePathsChartContent(points: points, currentPrice: r.currentPrice,
                                    yDomain: (priceMin - pad)...(priceMax + pad))

            HStack(spacing: 16) {
                Text("\(result?.samplePaths.count ?? 0) simulation paths")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
                HStack(spacing: 4) {
                    Rectangle()
                        .stroke(PythiaTheme.textPrimary, style: StrokeStyle(lineWidth: 1.5, dash: [4]))
                        .frame(width: 16, height: 1)
                    Text("Current Price")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func samplePathsChartContent(points: [PathPoint], currentPrice: Double,
                                         yDomain: ClosedRange<Double>) -> some View {
        Chart {
            ForEach(points) { pt in
                LineMark(
                    x: .value("Step", pt.step),
                    y: .value("Price", pt.price),
                    series: .value("Path", pt.pathIndex)
                )
                .foregroundStyle(by: .value("Path", "P\(pt.pathIndex)"))
                .opacity(0.5)
                .lineStyle(StrokeStyle(lineWidth: 1.0))
            }

            RuleMark(y: .value("Current", currentPrice))
                .foregroundStyle(PythiaTheme.textPrimary)
                .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [5]))
        }
        .chartYScale(domain: yDomain)
        .chartXAxisLabel("Trading Days")
        .chartYAxisLabel("Price")
        .chartLegend(.hidden)
        .pythiaChartAxes(gridOpacity: 0.15)
        .frame(height: 350)
    }

    // MARK: - Distribution Histogram

    private func buildMCHistBins(_ r: MonteCarloResponse) -> [MCHistBin] {
        let values = r.finalDistribution
        let binCount = 25
        guard let minV = values.min(), let maxV = values.max(), minV < maxV else { return [] }
        let binWidth = (maxV - minV) / Double(binCount)
        var bins = [MCHistBin]()
        for i in 0..<binCount {
            let lo = minV + Double(i) * binWidth
            let hi = lo + binWidth
            let mid = (lo + hi) / 2
            let cnt = values.filter { $0 >= lo && ($0 < hi || i == binCount - 1) }.count
            bins.append(MCHistBin(id: i, mid: mid, count: cnt, aboveCurrent: mid > r.currentPrice))
        }
        return bins
    }

    private func distributionChart(_ r: MonteCarloResponse) -> some View {
        let bins = buildMCHistBins(r)
        let currentPrice = r.currentPrice
        let meanPrice = r.statistics.meanFinalPrice

        return VStack(alignment: .leading, spacing: 8) {
            Text("Final Price Distribution")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            histogramChartContent(bins: bins, currentPrice: currentPrice, meanPrice: meanPrice)

            distributionLegend()

            distributionPercentiles(r)
        }
        .padding()
        .pythiaCard()
    }

    private func histogramChartContent(bins: [MCHistBin], currentPrice: Double, meanPrice: Double) -> some View {
        Chart(bins) { bin in
            BarMark(
                x: .value("Price", bin.mid),
                y: .value("Count", bin.count)
            )
            .foregroundStyle(bin.aboveCurrent ? PythiaTheme.profit : PythiaTheme.loss)
            .opacity(0.7)
        }
        .chartOverlay { proxy in
            GeometryReader { _ in
                if let xCur = proxy.position(forX: currentPrice) {
                    Rectangle()
                        .fill(PythiaTheme.accentGold)
                        .frame(width: 1.5, height: proxy.plotSize.height)
                        .position(x: xCur, y: proxy.plotSize.height / 2)
                }
                if let xMean = proxy.position(forX: meanPrice) {
                    Rectangle()
                        .fill(PythiaTheme.secondaryBlue)
                        .frame(width: 1.5, height: proxy.plotSize.height)
                        .opacity(0.8)
                        .position(x: xMean, y: proxy.plotSize.height / 2)
                }
            }
        }
        .chartXAxisLabel("Final Price")
        .chartYAxisLabel("Frequency")
        .pythiaChartAxes(gridOpacity: 0.2)
        .frame(height: 250)
    }

    private func distributionLegend() -> some View {
        HStack(spacing: 16) {
            legendItem(color: PythiaTheme.profit, label: "Above Current")
            legendItem(color: PythiaTheme.loss, label: "Below Current")
            legendItem(color: PythiaTheme.accentGold, label: "Current Price")
            legendItem(color: PythiaTheme.secondaryBlue, label: "Mean Price")
        }
    }

    private func distributionPercentiles(_ r: MonteCarloResponse) -> some View {
        HStack(spacing: PythiaTheme.largeSpacing) {
            VStack(spacing: 4) {
                Text("25th-75th Percentile")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
                Text("\(PythiaTheme.formatCurrency(r.statistics.percentile25)) — \(PythiaTheme.formatCurrency(r.statistics.percentile75))")
                    .font(PythiaTheme.monospace())
                    .foregroundColor(PythiaTheme.secondaryBlue)
            }
            VStack(spacing: 4) {
                Text("5th-95th Percentile")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
                Text("\(PythiaTheme.formatCurrency(r.statistics.percentile5)) — \(PythiaTheme.formatCurrency(r.statistics.percentile95))")
                    .font(PythiaTheme.monospace())
                    .foregroundColor(PythiaTheme.accentGold)
            }
        }
        .padding(.top, 4)
    }

    private func simulate() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        errorMessage = nil
        result = nil
        do {
            let r = try await db.runMonteCarlo(assetId: aid, simulations: simulations, steps: steps)
            if r.success {
                result = r
            } else {
                errorMessage = r.message ?? "Simulation failed — asset may not have enough historical data."
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
