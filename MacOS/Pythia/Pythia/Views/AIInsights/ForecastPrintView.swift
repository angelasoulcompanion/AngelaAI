//
//  ForecastPrintView.swift
//  Pythia — Light-themed printable view for PDF export
//

import SwiftUI
import Charts

struct ForecastPrintView: View {
    let result: AIForecastResponse

    private let L = PythiaTheme.Light.self
    private let actualColor = Color(hex: "2563EB")    // blue-600
    private let forecastColor = Color(hex: "7C3AED")   // violet-600

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            header
            kpiCards
            methodInfo
            forecastChart
            if let interp = result.interpretation, !interp.isEmpty {
                interpretationSection(interp)
            }
            if let risks = result.riskFactors, !risks.isEmpty {
                riskFactorsSection(risks)
            }
            footer
        }
        .padding(24)
        .frame(width: 700)
        .background(PythiaTheme.Light.background)
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Pythia — Price Forecast")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(L.textPrimary)
                Text("\(result.symbol) · \(result.forecastDays)-Day · \(result.method.replacingOccurrences(of: "_", with: " ").capitalized)")
                    .font(.system(size: 13))
                    .foregroundColor(L.textSecondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text("Generated")
                    .font(.system(size: 10))
                    .foregroundColor(L.textTertiary)
                Text(Date(), style: .date)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(L.textSecondary)
            }
        }
        .padding(.bottom, 4)
    }

    // MARK: - KPI Cards

    private var kpiCards: some View {
        let lastPred = result.predictions.last
        let forecastPrice = lastPred?.price ?? result.currentPrice
        let changePct = result.currentPrice > 0
            ? (forecastPrice - result.currentPrice) / result.currentPrice * 100
            : 0
        let isPositive = changePct >= 0

        return HStack(spacing: 10) {
            printKPI(title: "Current Price", value: PythiaTheme.formatCurrency(result.currentPrice))
            printKPI(
                title: "\(result.forecastDays)-Day Forecast",
                value: PythiaTheme.formatCurrency(forecastPrice),
                valueColor: PythiaTheme.profitLossColor(forecastPrice - result.currentPrice)
            )
            printKPI(
                title: "Projected Change",
                value: String(format: "%@%.1f%%", isPositive ? "+" : "", changePct),
                valueColor: isPositive ? PythiaTheme.profit : PythiaTheme.loss
            )
            printKPI(
                title: "Confidence",
                value: PythiaTheme.formatPercent(result.confidence),
                badge: result.confidenceLevel
            )
            printKPI(
                title: "Trend",
                value: result.trend.uppercased(),
                valueColor: result.trend == "upward" ? PythiaTheme.profit :
                           (result.trend == "downward" ? PythiaTheme.loss : Color(hex: "B45309"))
            )
        }
    }

    private func printKPI(
        title: String, value: String,
        valueColor: Color? = nil, badge: String? = nil
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 10))
                .foregroundColor(L.textSecondary)
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .foregroundColor(valueColor ?? L.textPrimary)
            if let badge = badge {
                Text(badge)
                    .font(.system(size: 9, weight: .semibold))
                    .foregroundColor(L.textSecondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 1)
                    .background(L.cardBorder)
                    .cornerRadius(3)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(L.cardBorder, lineWidth: 1)
        )
    }

    // MARK: - Method Info

    private var methodInfo: some View {
        let info = methodDescription(result.method)

        return HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(info.name)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
                Text(info.description)
                    .font(.system(size: 11))
                    .foregroundColor(L.textSecondary)
            }
            Spacer()
            if let last = result.predictions.last {
                VStack(alignment: .trailing, spacing: 2) {
                    Text("Forecast Range")
                        .font(.system(size: 10))
                        .foregroundColor(L.textSecondary)
                    Text("\(PythiaTheme.formatCurrency(last.lower)) — \(PythiaTheme.formatCurrency(last.upper))")
                        .font(.system(size: 12, weight: .semibold, design: .monospaced))
                        .foregroundColor(L.textPrimary)
                }
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(L.cardBorder, lineWidth: 1)
        )
    }

    // MARK: - Chart

    private struct ChartPoint: Identifiable {
        let id: Int
        let label: String
        let price: Double
        let series: String
    }

    private func buildChartData() -> [ChartPoint] {
        var points: [ChartPoint] = []
        var idx = 0

        for h in (result.historicalPrices ?? []) {
            points.append(ChartPoint(id: idx, label: String(h.date.suffix(5)), price: h.price, series: "Actual"))
            idx += 1
        }

        if let lastActual = points.last {
            points.append(ChartPoint(id: idx, label: lastActual.label, price: lastActual.price, series: "Forecast"))
            idx += 1
        }

        for p in result.predictions {
            let label = p.date.map { String($0.suffix(5)) } ?? "D\(p.day)"
            points.append(ChartPoint(id: idx, label: label, price: p.price, series: "Forecast"))
            idx += 1
        }

        return points
    }

    private var forecastChart: some View {
        let chartData = buildChartData()
        let allPrices = chartData.map(\.price)
        let yMin = (allPrices.min() ?? 0) * 0.97
        let yMax = (allPrices.max() ?? 0) * 1.03

        return VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Price Forecast")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
                Spacer()
                HStack(spacing: 12) {
                    HStack(spacing: 4) {
                        RoundedRectangle(cornerRadius: 1).fill(actualColor).frame(width: 14, height: 2)
                        Text("Actual").font(.system(size: 9)).foregroundColor(L.textSecondary)
                    }
                    HStack(spacing: 4) {
                        RoundedRectangle(cornerRadius: 1).stroke(forecastColor, style: StrokeStyle(lineWidth: 2, dash: [4, 3]))
                            .frame(width: 14, height: 2)
                        Text("Forecast").font(.system(size: 9)).foregroundColor(L.textSecondary)
                    }
                }
            }

            Chart {
                ForEach(chartData.filter { $0.series == "Actual" }) { p in
                    AreaMark(x: .value("Index", p.id), y: .value("Price", p.price))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [actualColor.opacity(0.20), actualColor.opacity(0.02)],
                                startPoint: .top, endPoint: .bottom
                            )
                        )
                        .interpolationMethod(.catmullRom)
                }

                ForEach(chartData.filter { $0.series == "Actual" }) { p in
                    LineMark(
                        x: .value("Index", p.id), y: .value("Price", p.price),
                        series: .value("Series", "Actual")
                    )
                    .foregroundStyle(actualColor)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                    .interpolationMethod(.catmullRom)
                }

                ForEach(chartData.filter { $0.series == "Forecast" }) { p in
                    LineMark(
                        x: .value("Index", p.id), y: .value("Price", p.price),
                        series: .value("Series", "Forecast")
                    )
                    .foregroundStyle(forecastColor)
                    .lineStyle(StrokeStyle(lineWidth: 2, dash: [6, 4]))
                    .interpolationMethod(.catmullRom)
                }
            }
            .chartLegend(.hidden)
            .chartYScale(domain: yMin...yMax)
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 8)) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(L.textTertiary.opacity(0.3))
                    AxisValueLabel {
                        if let idx = value.as(Int.self), idx >= 0, idx < chartData.count {
                            Text(chartData[idx].label)
                                .font(.system(size: 8, design: .monospaced))
                                .foregroundColor(L.textSecondary)
                                .rotationEffect(.degrees(-45))
                        }
                    }
                }
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(L.textTertiary.opacity(0.3))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(PythiaTheme.formatCurrency(v))
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundColor(L.textSecondary)
                        }
                    }
                }
            }
            .frame(height: 300)
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(L.cardBorder, lineWidth: 1)
        )
    }

    // MARK: - AI Interpretation

    private func interpretationSection(_ text: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(Color(hex: "B45309"))
                    .font(.system(size: 13))
                Text("AI Interpretation")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
            }
            Text(text)
                .font(.system(size: 11))
                .foregroundColor(L.textPrimary)
                .lineSpacing(3)
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color(hex: "F59E0B").opacity(0.4), lineWidth: 1)
        )
    }

    // MARK: - Risk Factors

    private func riskFactorsSection(_ risks: [String]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(Color(hex: "D97706"))
                    .font(.system(size: 13))
                Text("Risk Factors")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
            }
            ForEach(Array(risks.enumerated()), id: \.offset) { _, risk in
                HStack(alignment: .top, spacing: 6) {
                    Text("•")
                        .foregroundColor(Color(hex: "D97706"))
                    Text(risk)
                        .font(.system(size: 11))
                        .foregroundColor(L.textPrimary)
                }
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color(hex: "F59E0B").opacity(0.4), lineWidth: 1)
        )
    }

    // MARK: - Footer

    private var footer: some View {
        HStack {
            Text("Pythia Quantitative Finance Platform")
                .font(.system(size: 9))
                .foregroundColor(L.textTertiary)
            Spacer()
            Text("This is not investment advice. Past performance does not guarantee future results.")
                .font(.system(size: 8))
                .foregroundColor(L.textTertiary)
        }
        .padding(.top, 4)
    }

    // MARK: - Helpers

    private func methodDescription(_ method: String) -> (name: String, description: String) {
        switch method {
        case "prophet":
            return ("Prophet (AI)", "Facebook Prophet with multiplicative seasonality, weekly/yearly patterns, automatic changepoint detection. 80% interval.")
        case "moving_average":
            return ("Moving Average", "3-period moving average with trend adjustment. Confidence band ±20%.")
        case "linear_regression":
            return ("Linear Regression", "Least-squares with R²-based dynamic confidence bands (±15%–35%).")
        case "growth_rate":
            return ("Growth Rate", "Compound daily growth rate extrapolation capped at ±0.5%/day. Band ±15%.")
        default:
            return (method, "")
        }
    }
}
