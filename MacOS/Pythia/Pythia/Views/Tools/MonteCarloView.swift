//
//  MonteCarloView.swift
//  Pythia — Monte Carlo GBM Simulation
//

import SwiftUI
import Charts

struct MonteCarloView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var assets: [Asset] = []
    @State private var selectedAssetId: String?
    @State private var simulations = 10000
    @State private var steps = 252
    @State private var result: MonteCarloResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Monte Carlo Simulation")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    Picker("Asset", selection: Binding(
                        get: { selectedAssetId ?? "" },
                        set: { selectedAssetId = $0.isEmpty ? nil : $0 }
                    )) {
                        Text("Select Asset").tag("")
                        ForEach(assets) { a in
                            Text("\(a.symbol)").tag(a.assetId)
                        }
                    }
                    .frame(width: 200)

                    Picker("Simulations", selection: $simulations) {
                        Text("1,000").tag(1000)
                        Text("10,000").tag(10000)
                        Text("50,000").tag(50000)
                    }
                    .frame(width: 130)

                    Picker("Horizon", selection: $steps) {
                        Text("63 days (3M)").tag(63)
                        Text("126 days (6M)").tag(126)
                        Text("252 days (1Y)").tag(252)
                    }
                    .frame(width: 160)

                    Button("Simulate") { Task { await simulate() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Running \(simulations) simulations...") }

                if let r = result, r.success {
                    statsCard(r)
                    fanChart(r)
                    distributionCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { assets = try await db.fetchAssets() } catch {} }
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
                mcMetric("Mean", PythiaTheme.formatCurrency(r.statistics.meanFinalPrice), PythiaTheme.textPrimary)
                mcMetric("Median", PythiaTheme.formatCurrency(r.statistics.medianFinalPrice), PythiaTheme.secondaryBlue)
                mcMetric("5th %ile", PythiaTheme.formatCurrency(r.statistics.percentile5), PythiaTheme.loss)
                mcMetric("95th %ile", PythiaTheme.formatCurrency(r.statistics.percentile95), PythiaTheme.profit)
                mcMetric("P(Above)", PythiaTheme.formatPercent(r.statistics.probAboveCurrent),
                         r.statistics.probAboveCurrent > 0.5 ? PythiaTheme.profit : PythiaTheme.loss)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                mcMetric("Expected Return", PythiaTheme.formatPercent(r.parameters.expectedReturn), PythiaTheme.textSecondary)
                mcMetric("Volatility", PythiaTheme.formatPercent(r.parameters.volatility), PythiaTheme.accentGold)
                mcMetric("Std Dev", PythiaTheme.formatCurrency(r.statistics.stdFinalPrice), PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func fanChart(_ r: MonteCarloResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
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
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.08))
                }

                // 25-75 band
                ForEach(r.percentileBands) { band in
                    AreaMark(
                        x: .value("Step", band.step),
                        yStart: .value("P25", band.p25),
                        yEnd: .value("P75", band.p75)
                    )
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.15))
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
            .chartXAxisLabel("Trading Days")
            .chartYAxisLabel("Price")
            .chartXAxis {
                AxisMarks { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.2))
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.2))
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .frame(height: 350)
        }
        .padding()
        .pythiaCard()
    }

    private func distributionCard(_ r: MonteCarloResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Final Price Distribution")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

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
        }
        .padding()
        .pythiaCard()
    }

    private func mcMetric(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(minWidth: 80)
    }

    private func simulate() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        do {
            result = try await db.runMonteCarlo(assetId: aid, simulations: simulations, steps: steps)
        } catch {}
        isLoading = false
    }
}
