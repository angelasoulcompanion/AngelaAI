//
//  StatisticsView.swift
//  Pythia — Statistical Distribution Analysis
//

import SwiftUI
import Charts

struct StatisticsView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var assets: [Asset] = []
    @State private var selectedAssetId: String?
    @State private var days = 365
    @State private var result: StatisticsResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Statistical Analysis")
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
                            Text(a.symbol).tag(a.assetId)
                        }
                    }
                    .frame(width: 200)

                    Picker("Period", selection: $days) {
                        Text("90 Days").tag(90)
                        Text("1 Year").tag(365)
                        Text("3 Years").tag(1095)
                    }
                    .frame(width: 120)

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Running statistical tests...") }

                if let r = result, r.success {
                    descriptiveCard(r)
                    histogramChart(r)
                    testsCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { assets = try await db.fetchAssets() } catch {} }
    }

    private func descriptiveCard(_ r: StatisticsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(r.symbol) — Descriptive Statistics")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("\(r.nObservations) observations")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 12) {
                statCell("Mean", String(format: "%.6f", r.descriptive.mean))
                statCell("Std Dev", String(format: "%.6f", r.descriptive.std))
                statCell("Median", String(format: "%.6f", r.descriptive.median))
                statCell("Skewness", String(format: "%.4f", r.descriptive.skewness),
                         r.descriptive.skewness < -0.5 ? PythiaTheme.loss : (r.descriptive.skewness > 0.5 ? PythiaTheme.profit : PythiaTheme.textPrimary))
                statCell("Kurtosis", String(format: "%.4f", r.descriptive.kurtosis),
                         r.descriptive.kurtosis > 3 ? PythiaTheme.warningOrange : PythiaTheme.textPrimary)
                statCell("Min", String(format: "%.6f", r.descriptive.min), PythiaTheme.loss)
                statCell("Max", String(format: "%.6f", r.descriptive.max), PythiaTheme.profit)
                statCell("Range", String(format: "%.6f", r.descriptive.max - r.descriptive.min))
            }

            Divider().background(PythiaTheme.textTertiary)

            Text("Percentiles")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            HStack(spacing: PythiaTheme.largeSpacing) {
                statCell("1st", String(format: "%.6f", r.percentiles.p1), PythiaTheme.loss)
                statCell("5th", String(format: "%.6f", r.percentiles.p5), PythiaTheme.warningOrange)
                statCell("95th", String(format: "%.6f", r.percentiles.p95), PythiaTheme.profit)
                statCell("99th", String(format: "%.6f", r.percentiles.p99), PythiaTheme.profit)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func histogramChart(_ r: StatisticsResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Return Distribution Histogram")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(r.histogram) { bin in
                BarMark(
                    x: .value("Return", (bin.binStart + bin.binEnd) / 2),
                    y: .value("Count", bin.count)
                )
                .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.7))
            }
            .chartXAxisLabel("Daily Return")
            .chartYAxisLabel("Frequency")
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
            .frame(height: 250)
        }
        .padding()
        .pythiaCard()
    }

    private func testsCard(_ r: StatisticsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Normality & Statistical Tests")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            ForEach(r.tests) { test in
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
                .padding(.vertical, 4)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func statCell(_ label: String, _ value: String, _ color: Color = PythiaTheme.textPrimary) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
            Text(value)
                .font(PythiaTheme.monospace())
                .foregroundColor(color)
        }
    }

    private func analyze() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        do {
            result = try await db.analyzeDistribution(assetId: aid, days: days)
        } catch {}
        isLoading = false
    }
}
