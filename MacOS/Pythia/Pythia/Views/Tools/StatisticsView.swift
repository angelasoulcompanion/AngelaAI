//
//  StatisticsView.swift
//  Pythia — Statistical Distribution Analysis
//

import SwiftUI
import Charts

struct StatisticsView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var days = 365
    @State private var result: StatisticsResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Statistical Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)
                    PeriodPicker(days: $days)

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if isLoading { LoadingView("Running statistical tests...") }

                if let r = result, r.success {
                    annualizedCard(r)
                    descriptiveCard(r)
                    histogramChart(r)
                    testsCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Annualized Metrics

    private func annualizedCard(_ r: StatisticsResponse) -> some View {
        let d = r.descriptive
        let annReturn = d.mean * 252
        let annVol = d.std * sqrt(252.0)
        let sharpe = annVol > 0 ? annReturn / annVol : 0
        let dailyVaR = d.mean - 1.645 * d.std

        return VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Annualized Metrics")

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Ann. Return", PythiaTheme.formatPercent(annReturn),
                          PythiaTheme.profitLossColor(annReturn), size: .small)
                MetricBox("Ann. Volatility", PythiaTheme.formatPercent(annVol),
                          PythiaTheme.warningOrange, size: .small)
                MetricBox("Sharpe Ratio", String(format: "%.3f", sharpe),
                          sharpe > 1 ? PythiaTheme.profit : (sharpe < 0 ? PythiaTheme.loss : PythiaTheme.textPrimary), size: .small)
                MetricBox("Daily VaR 95%", PythiaTheme.formatPercent(dailyVaR),
                          PythiaTheme.loss, size: .small)
            }

            Text(sharpe > 1 ? "Strong risk-adjusted performance (Sharpe > 1)"
                 : sharpe > 0 ? "Positive but modest risk-adjusted return"
                 : "Negative risk-adjusted return — losses exceed risk-free rate")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Descriptive Statistics

    private func descriptiveCard(_ r: StatisticsResponse) -> some View {
        let d = r.descriptive

        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                sectionHeader("Descriptive Statistics")
                Spacer()
                Text("\(r.nObservations) observations")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 12) {
                MetricBox("Mean", String(format: "%.6f", d.mean),
                          PythiaTheme.profitLossColor(d.mean), size: .small)
                MetricBox("Std Dev", String(format: "%.6f", d.std), size: .small)
                MetricBox("Median", String(format: "%.6f", d.median),
                          PythiaTheme.profitLossColor(d.median), size: .small)
                MetricBox("Skewness", String(format: "%.4f", d.skewness),
                          d.skewness < -0.5 ? PythiaTheme.loss : (d.skewness > 0.5 ? PythiaTheme.profit : PythiaTheme.textPrimary), size: .small)
                MetricBox("Kurtosis", String(format: "%.4f", d.kurtosis),
                          d.kurtosis > 3 ? PythiaTheme.warningOrange : PythiaTheme.textPrimary, size: .small)
                MetricBox("Min", String(format: "%.6f", d.min), PythiaTheme.loss, size: .small)
                MetricBox("Max", String(format: "%.6f", d.max), PythiaTheme.profit, size: .small)
                MetricBox("Range", String(format: "%.6f", d.max - d.min), size: .small)
            }

            // Interpretive text
            Text(d.skewness < -0.5 ? "Negative skew: heavier left tail (more extreme losses than gains)"
                 : d.skewness > 0.5 ? "Positive skew: heavier right tail (larger upside moves)"
                 : "Approximately symmetric distribution")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
            Text(d.kurtosis > 3 ? "Leptokurtic: fat tails — more extreme events than normal distribution"
                 : d.kurtosis < 3 ? "Platykurtic: thin tails — fewer extreme events than normal"
                 : "Approximately normal tails (mesokurtic)")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)

            PythiaDivider()

            Text("Percentiles")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("1st", String(format: "%.6f", r.percentiles.p1), PythiaTheme.loss, size: .small)
                MetricBox("5th", String(format: "%.6f", r.percentiles.p5), PythiaTheme.warningOrange, size: .small)
                MetricBox("95th", String(format: "%.6f", r.percentiles.p95), PythiaTheme.profit, size: .small)
                MetricBox("99th", String(format: "%.6f", r.percentiles.p99), PythiaTheme.profit, size: .small)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Histogram with Normal Curve

    private func histogramChart(_ r: StatisticsResponse) -> some View {
        let d = r.descriptive
        let totalCount = r.histogram.reduce(0) { $0 + $1.count }
        let binWidth = r.histogram.count > 1 ? r.histogram[1].binStart - r.histogram[0].binStart : 0.01

        return VStack(alignment: .leading, spacing: 8) {
            sectionHeader("Return Distribution")

            Chart {
                ForEach(r.histogram) { bin in
                    let midpoint = (bin.binStart + bin.binEnd) / 2
                    BarMark(
                        x: .value("Return", midpoint),
                        y: .value("Count", bin.count)
                    )
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.7))
                }

                // Normal distribution curve overlay
                if totalCount > 0 && d.std > 0 {
                    let minX = r.histogram.first?.binStart ?? d.mean - 3 * d.std
                    let maxX = r.histogram.last?.binEnd ?? d.mean + 3 * d.std
                    let steps = 60
                    let stepSize = (maxX - minX) / Double(steps)

                    ForEach(0...steps, id: \.self) { i in
                        let x = minX + Double(i) * stepSize
                        let z = (x - d.mean) / d.std
                        let pdf = exp(-0.5 * z * z) / (d.std * sqrt(2 * .pi))
                        let scaledY = pdf * Double(totalCount) * binWidth

                        LineMark(
                            x: .value("Return", x),
                            y: .value("Normal", scaledY)
                        )
                        .foregroundStyle(PythiaTheme.warningOrange)
                        .lineStyle(StrokeStyle(lineWidth: 2, dash: [6, 3]))
                    }
                }
            }
            .chartXAxisLabel("Daily Return")
            .chartYAxisLabel("Frequency")
            .pythiaChartAxes(gridOpacity: 0.2)
            .frame(height: 250)

            HStack(spacing: 16) {
                HStack(spacing: 4) {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(PythiaTheme.secondaryBlue.opacity(0.7))
                        .frame(width: 12, height: 12)
                    Text("Actual")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                HStack(spacing: 4) {
                    Rectangle()
                        .fill(PythiaTheme.warningOrange)
                        .frame(width: 12, height: 2)
                    Text("Normal Dist.")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Statistical Tests

    private func testsCard(_ r: StatisticsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Normality & Statistical Tests")

            ForEach(r.tests) { test in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: test.significant ? "xmark.circle.fill" : "checkmark.circle.fill")
                            .foregroundColor(test.significant ? PythiaTheme.loss : PythiaTheme.profit)

                        Text(test.testName)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textPrimary)
                            .frame(width: 200, alignment: .leading)

                        Text("Stat: \(String(format: "%.4f", test.statistic))")
                            .font(PythiaTheme.monospace())
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 140)

                        Text("p: \(String(format: "%.6f", test.pValue))")
                            .font(PythiaTheme.monospace())
                            .foregroundColor(test.pValue < 0.05 ? PythiaTheme.loss : PythiaTheme.profit)
                            .frame(width: 120)

                        Text(test.conclusion)
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)

                        Spacer()
                    }

                    Text(testInterpretation(test))
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                        .padding(.leading, 28)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(PythiaTheme.headline())
            .foregroundColor(PythiaTheme.textPrimary)
    }

    private func testInterpretation(_ test: StatTest) -> String {
        let name = test.testName.lowercased()
        if test.pValue < 0.05 {
            if name.contains("jarque") || name.contains("shapiro") || name.contains("normality") || name.contains("agostino") {
                return "Returns are NOT normally distributed (p < 0.05) — standard models may underestimate tail risk"
            } else if name.contains("adf") || name.contains("dickey") || name.contains("stationar") {
                return "Series is stationary — no unit root detected, suitable for mean-reversion analysis"
            } else if name.contains("ljung") || name.contains("autocorrelation") {
                return "Significant autocorrelation detected — past returns may predict future returns"
            }
            return "Statistically significant at 95% confidence (p < 0.05)"
        } else {
            if name.contains("jarque") || name.contains("shapiro") || name.contains("normality") || name.contains("agostino") {
                return "Cannot reject normality — returns are approximately normal, standard models apply"
            } else if name.contains("adf") || name.contains("dickey") || name.contains("stationar") {
                return "Cannot reject unit root — series may be non-stationary, trend could dominate"
            } else if name.contains("ljung") || name.contains("autocorrelation") {
                return "No significant autocorrelation — returns appear independent"
            }
            return "Not statistically significant at 95% confidence (p >= 0.05)"
        }
    }

    private func analyze() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        errorMessage = nil
        do {
            var r = try await db.analyzeDistribution(assetId: aid, days: days)

            // Auto-fetch prices if insufficient data, then retry
            if !r.success, let msg = r.message, msg.contains("data point") {
                let _ = try? await db.fetchAndStorePrices(assetId: aid, days: days)
                r = try await db.analyzeDistribution(assetId: aid, days: days)
            }

            if r.success {
                result = r
                errorMessage = nil
            } else {
                errorMessage = r.message ?? "Analysis returned no data"
                result = nil
            }
        } catch {
            errorMessage = "Analysis failed: \(error.localizedDescription)"
            result = nil
        }
        isLoading = false
    }
}
