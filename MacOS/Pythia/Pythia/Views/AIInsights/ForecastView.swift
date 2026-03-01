//
//  ForecastView.swift
//  Pythia — AI Price Forecasting
//

import SwiftUI
import Charts

struct ForecastView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var assets: [Asset] = []
    @State private var selectedAssetId: String?
    @State private var method = "moving_average"
    @State private var forecastDays = 30
    @State private var result: AIForecastResponse?
    @State private var isLoading = false

    private let methods = [
        ("moving_average", "Moving Average"),
        ("linear_regression", "Linear Regression"),
        ("exponential_smoothing", "Exponential Smoothing"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Price Forecast")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

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

                    Picker("Method", selection: $method) {
                        ForEach(methods, id: \.0) { val, label in
                            Text(label).tag(val)
                        }
                    }
                    .frame(width: 180)

                    Picker("Horizon", selection: $forecastDays) {
                        Text("7 Days").tag(7)
                        Text("14 Days").tag(14)
                        Text("30 Days").tag(30)
                        Text("90 Days").tag(90)
                    }
                    .frame(width: 120)

                    Button("Forecast") { Task { await forecast() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Generating forecast...") }

                if let r = result, r.success {
                    forecastSummary(r)
                    forecastChart(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { assets = try await db.fetchAssets() } catch {} }
    }

    private func forecastSummary(_ r: AIForecastResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(r.symbol) — \(r.method.replacingOccurrences(of: "_", with: " ").capitalized)")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()

                Text(r.trend.uppercased())
                    .font(PythiaTheme.heading())
                    .foregroundColor(r.trend == "upward" ? PythiaTheme.profit :
                                        (r.trend == "downward" ? PythiaTheme.loss : PythiaTheme.accentGold))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background((r.trend == "upward" ? PythiaTheme.profit :
                                    (r.trend == "downward" ? PythiaTheme.loss : PythiaTheme.accentGold)).opacity(0.15))
                    .cornerRadius(8)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                fcMetric("Current", PythiaTheme.formatCurrency(r.currentPrice), PythiaTheme.textPrimary)
                if let last = r.predictions.last {
                    fcMetric("Forecast", PythiaTheme.formatCurrency(last.price),
                             PythiaTheme.profitLossColor(last.price - r.currentPrice))
                    fcMetric("Range", "\(PythiaTheme.formatCurrency(last.lower)) — \(PythiaTheme.formatCurrency(last.upper))",
                             PythiaTheme.textSecondary)
                }
                fcMetric("Confidence", PythiaTheme.formatPercent(r.confidence), PythiaTheme.secondaryBlue)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func forecastChart(_ r: AIForecastResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Price Forecast with Confidence Band")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart {
                // Confidence band
                ForEach(r.predictions) { p in
                    AreaMark(
                        x: .value("Day", p.day),
                        yStart: .value("Lower", p.lower),
                        yEnd: .value("Upper", p.upper)
                    )
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.1))
                }

                // Forecast line
                ForEach(r.predictions) { p in
                    LineMark(
                        x: .value("Day", p.day),
                        y: .value("Price", p.price)
                    )
                    .foregroundStyle(PythiaTheme.accentGold)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                }

                // Current price reference
                RuleMark(y: .value("Current", r.currentPrice))
                    .foregroundStyle(PythiaTheme.textTertiary)
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [5]))
            }
            .chartXAxisLabel("Days")
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
            .frame(height: 300)
        }
        .padding()
        .pythiaCard()
    }

    private func fcMetric(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.system(size: 18, weight: .bold, design: .rounded)).foregroundColor(color)
            Text(label).font(PythiaTheme.caption()).foregroundColor(PythiaTheme.textSecondary)
        }
    }

    private func forecast() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        do { result = try await db.getForecast(assetId: aid, method: method, days: forecastDays) } catch {}
        isLoading = false
    }
}
