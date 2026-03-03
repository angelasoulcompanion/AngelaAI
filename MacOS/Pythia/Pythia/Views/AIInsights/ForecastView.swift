//
//  ForecastView.swift
//  Pythia — AI Price Forecasting (SECustomerAnalysis ForecastingEngine style)
//

import SwiftUI
import Charts
import AppKit
import UniformTypeIdentifiers

struct ForecastView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var method = "prophet"
    @State private var forecastDays = 30
    @State private var includeInterpretation = true
    @State private var result: AIForecastResponse?
    @State private var isLoading = false

    private let methods = [
        ("prophet", "Prophet (AI)"),
        ("moving_average", "Moving Average"),
        ("linear_regression", "Linear Regression"),
        ("growth_rate", "Growth Rate"),
    ]

    private let horizons = [
        (7, "7D"), (14, "14D"), (30, "30D"), (60, "60D"), (90, "90D"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                // Title
                Text("Price Forecast")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Control Bar
                controlBar

                if isLoading { LoadingView("Generating forecast...") }

                if let r = result, r.success {
                    // KPI Cards Row (SECustomerAnalysis pattern)
                    kpiCardsRow(r)

                    // Method info card
                    methodInfoCard(r)

                    // Main Forecast Chart (area + line + confidence band)
                    forecastChart(r)

                    // AI Interpretation
                    if let interp = r.interpretation, !interp.isEmpty {
                        interpretationCard(interp, provider: r.llmProvider)
                    }

                    // Risk Factors
                    if let risks = r.riskFactors, !risks.isEmpty {
                        riskFactorsCard(risks)
                    }
                } else if let r = result, !r.success {
                    ErrorMessageView(message: r.message ?? "Forecast failed")
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Control Bar

    private var controlBar: some View {
        HStack(spacing: PythiaTheme.spacing) {
            AssetPickerView(selectedId: $selectedAssetId)

            Picker("Method", selection: $method) {
                ForEach(methods, id: \.0) { val, label in
                    Text(label).tag(val)
                }
            }
            .frame(width: 180)

            // Horizon segmented picker (SE style)
            Picker("Horizon", selection: $forecastDays) {
                ForEach(horizons, id: \.0) { val, label in
                    Text(label).tag(val)
                }
            }
            .pickerStyle(.segmented)
            .frame(width: 260)

            Toggle("AI Insights", isOn: $includeInterpretation)
                .toggleStyle(.switch)
                .frame(width: 120)

            Button("Forecast") { Task { await forecast() } }
                .pythiaPrimaryButton()
                .disabled(selectedAssetId == nil)

            Spacer()

            if result?.success == true {
                Button { exportPDF() } label: {
                    Label("Export PDF", systemImage: "arrow.down.doc")
                }
                .pythiaSecondaryButton()
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - KPI Cards (SECustomerAnalysis 5-column pattern)

    private func kpiCardsRow(_ r: AIForecastResponse) -> some View {
        let lastPred = r.predictions.last
        let forecastPrice = lastPred?.price ?? r.currentPrice
        let changePct = r.currentPrice > 0
            ? (forecastPrice - r.currentPrice) / r.currentPrice * 100
            : 0
        let isPositive = changePct >= 0

        return HStack(spacing: PythiaTheme.spacing) {
            // 1. Current Price
            kpiCard(
                icon: "chart.line.uptrend.xyaxis",
                iconColor: PythiaTheme.secondaryBlue,
                title: "Current Price",
                value: PythiaTheme.formatCurrency(r.currentPrice),
                valueColor: PythiaTheme.textPrimary
            )

            // 2. Forecast Price (end of period)
            kpiCard(
                icon: "target",
                iconColor: Color(hex: "8B5CF6"),
                title: "\(r.forecastDays)-Day Forecast",
                value: PythiaTheme.formatCurrency(forecastPrice),
                valueColor: PythiaTheme.profitLossColor(forecastPrice - r.currentPrice)
            )

            // 3. Projected Change %
            kpiCard(
                icon: isPositive ? "arrow.up.right" : "arrow.down.right",
                iconColor: isPositive ? PythiaTheme.profit : PythiaTheme.loss,
                title: "Projected Change",
                value: String(format: "%@%.1f%%", isPositive ? "+" : "", changePct),
                valueColor: isPositive ? PythiaTheme.profit : PythiaTheme.loss
            )

            // 4. Confidence Level
            kpiCard(
                icon: "chart.bar.fill",
                iconColor: confidenceLevelColor(r.confidenceLevel),
                title: "Confidence",
                value: PythiaTheme.formatPercent(r.confidence),
                valueColor: PythiaTheme.textPrimary,
                badge: r.confidenceLevel,
                badgeColor: confidenceLevelColor(r.confidenceLevel)
            )

            // 5. Trend
            kpiCard(
                icon: r.trend == "upward" ? "arrow.up.circle.fill" :
                      (r.trend == "downward" ? "arrow.down.circle.fill" : "arrow.left.arrow.right.circle.fill"),
                iconColor: r.trend == "upward" ? PythiaTheme.profit :
                          (r.trend == "downward" ? PythiaTheme.loss : PythiaTheme.accentGold),
                title: "Trend",
                value: r.trend.uppercased(),
                valueColor: r.trend == "upward" ? PythiaTheme.profit :
                           (r.trend == "downward" ? PythiaTheme.loss : PythiaTheme.accentGold)
            )
        }
    }

    private func kpiCard(
        icon: String, iconColor: Color,
        title: String, value: String, valueColor: Color,
        badge: String? = nil, badgeColor: Color = .clear
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .foregroundColor(iconColor)
                    .font(.system(size: 14))
                Text(title)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
            }

            Text(value)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(valueColor)

            if let badge = badge {
                Text(badge)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(badgeColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(badgeColor.opacity(0.15))
                    .cornerRadius(4)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .pythiaCard()
    }

    // MARK: - Method Info Card

    private func methodInfoCard(_ r: AIForecastResponse) -> some View {
        let info = methodDescription(r.method)

        return HStack(spacing: 16) {
            Image(systemName: info.icon)
                .foregroundColor(Color(hex: "8B5CF6"))
                .font(.system(size: 20))
                .frame(width: 40)

            VStack(alignment: .leading, spacing: 4) {
                Text(info.name)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Text(info.description)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textSecondary)
            }

            Spacer()

            if let last = r.predictions.last {
                VStack(alignment: .trailing, spacing: 4) {
                    Text("Forecast Range")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text("\(PythiaTheme.formatCurrency(last.lower)) — \(PythiaTheme.formatCurrency(last.upper))")
                        .font(.system(size: 14, weight: .semibold, design: .monospaced))
                        .foregroundColor(PythiaTheme.textPrimary)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Forecast Chart (SE style: Actual blue + Forecast purple dashed)

    /// Unified chart data point with series label for color differentiation
    private struct ChartPoint: Identifiable {
        let id: Int
        let label: String
        let price: Double
        let series: String  // "Actual" or "Forecast"
    }

    private func buildChartData(_ r: AIForecastResponse) -> [ChartPoint] {
        var points: [ChartPoint] = []
        var idx = 0

        // Historical actual prices
        for h in (r.historicalPrices ?? []) {
            points.append(ChartPoint(id: idx, label: String(h.date.suffix(5)), price: h.price, series: "Actual"))
            idx += 1
        }

        // Bridge: duplicate last actual as first forecast for continuity
        if let lastActual = points.last {
            points.append(ChartPoint(id: idx, label: lastActual.label, price: lastActual.price, series: "Forecast"))
            idx += 1
        }

        // Forecast predictions
        for p in r.predictions {
            let label = p.date.map { String($0.suffix(5)) } ?? "D\(p.day)"
            points.append(ChartPoint(id: idx, label: label, price: p.price, series: "Forecast"))
            idx += 1
        }

        return points
    }

    private let actualColor = Color(hex: "3B82F6")    // blue
    private let forecastColor = Color(hex: "8B5CF6")   // purple

    private func forecastChart(_ r: AIForecastResponse) -> some View {
        let chartData = buildChartData(r)

        // Y-axis auto-fit
        let allPrices = chartData.map(\.price)
        let yMin = (allPrices.min() ?? 0) * 0.97
        let yMax = (allPrices.max() ?? 0) * 1.03

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Price Forecast")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                HStack(spacing: 16) {
                    HStack(spacing: 4) {
                        RoundedRectangle(cornerRadius: 2).fill(actualColor).frame(width: 16, height: 3)
                        Text("Actual").font(PythiaTheme.caption()).foregroundColor(PythiaTheme.textSecondary)
                    }
                    HStack(spacing: 4) {
                        RoundedRectangle(cornerRadius: 2).stroke(forecastColor, style: StrokeStyle(lineWidth: 2, dash: [4, 3]))
                            .frame(width: 16, height: 3)
                        Text("Forecast").font(PythiaTheme.caption()).foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }

            Chart {
                // Actual: area fill (blue gradient)
                ForEach(chartData.filter { $0.series == "Actual" }) { p in
                    AreaMark(
                        x: .value("Index", p.id),
                        y: .value("Price", p.price)
                    )
                    .foregroundStyle(
                        LinearGradient(
                            colors: [actualColor.opacity(0.30), actualColor.opacity(0.02)],
                            startPoint: .top, endPoint: .bottom
                        )
                    )
                    .interpolationMethod(.catmullRom)
                }

                // Actual: solid line (blue)
                ForEach(chartData.filter { $0.series == "Actual" }) { p in
                    LineMark(
                        x: .value("Index", p.id),
                        y: .value("Price", p.price),
                        series: .value("Series", "Actual")
                    )
                    .foregroundStyle(actualColor)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                    .interpolationMethod(.catmullRom)
                }

                // Forecast: dashed line only (purple, no area fill)
                ForEach(chartData.filter { $0.series == "Forecast" }) { p in
                    LineMark(
                        x: .value("Index", p.id),
                        y: .value("Price", p.price),
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
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.1))
                    AxisValueLabel {
                        if let idx = value.as(Int.self), idx >= 0, idx < chartData.count {
                            Text(chartData[idx].label)
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundColor(PythiaTheme.textSecondary)
                                .rotationEffect(.degrees(-45))
                        }
                    }
                }
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.15))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(PythiaTheme.formatCurrency(v))
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                }
            }
            .frame(height: 380)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - AI Interpretation Card

    private func interpretationCard(_ interpretation: String, provider: String?) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("AI Interpretation")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if let p = provider {
                    Text(p.uppercased())
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(4)
                }
            }

            Text(interpretation)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textPrimary)
                .lineSpacing(4)
        }
        .padding()
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(PythiaTheme.accentGold.opacity(0.3), lineWidth: 1)
        )
        .pythiaCard()
    }

    // MARK: - Risk Factors Card

    private func riskFactorsCard(_ risks: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(PythiaTheme.warningOrange)
                Text("Risk Factors")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            ForEach(Array(risks.enumerated()), id: \.offset) { _, risk in
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "exclamationmark.triangle")
                        .foregroundColor(PythiaTheme.warningOrange)
                        .frame(width: 20)
                        .font(.caption)
                    Text(risk)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                .padding(.vertical, 2)
            }
        }
        .padding()
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(PythiaTheme.warningOrange.opacity(0.3), lineWidth: 1)
        )
        .pythiaCard()
    }

    // MARK: - PDF Export

    @MainActor
    private func exportPDF() {
        guard let r = result else { return }

        let printView = ForecastPrintView(result: r)
        let renderer = ImageRenderer(content: printView)
        renderer.scale = 2.0

        let pdfData = NSMutableData()
        guard let consumer = CGDataConsumer(data: pdfData as CFMutableData) else { return }

        renderer.render { size, renderFn in
            var mediaBox = CGRect(origin: .zero, size: size)
            guard let context = CGContext(consumer: consumer, mediaBox: &mediaBox, nil) else { return }
            context.beginPDFPage(nil)
            renderFn(context)
            context.endPDFPage()
            context.closePDF()
        }

        let panel = NSSavePanel()
        panel.allowedContentTypes = [.pdf]
        panel.nameFieldStringValue = "\(r.symbol)_forecast.pdf"
        panel.title = "Export Forecast PDF"

        if panel.runModal() == .OK, let url = panel.url {
            try? pdfData.write(to: url, options: .atomic)
        }
    }

    // MARK: - Helpers

    private func forecast() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        do {
            result = try await db.getForecast(
                assetId: aid,
                method: method,
                days: forecastDays,
                includeInterpretation: includeInterpretation
            )
        } catch {}
        isLoading = false
    }

    private func confidenceLevelColor(_ level: String?) -> Color {
        switch level {
        case "High": return PythiaTheme.profit
        case "Medium": return PythiaTheme.accentGold
        case "Low": return PythiaTheme.loss
        default: return PythiaTheme.textSecondary
        }
    }

    private struct MethodInfo {
        let name: String
        let icon: String
        let description: String
    }

    private func methodDescription(_ method: String) -> MethodInfo {
        switch method {
        case "prophet":
            return MethodInfo(
                name: "Prophet (AI)",
                icon: "wand.and.stars",
                description: "Facebook Prophet model with multiplicative seasonality, weekly/yearly patterns, and automatic changepoint detection. 80% prediction interval."
            )
        case "moving_average":
            return MethodInfo(
                name: "Moving Average",
                icon: "chart.line.flattrend.xyaxis",
                description: "3-period moving average with trend adjustment from first/second half comparison. Confidence band ±20%."
            )
        case "linear_regression":
            return MethodInfo(
                name: "Linear Regression",
                icon: "function",
                description: "Least-squares linear regression with R²-based dynamic confidence bands. Higher R² = tighter bands (±15% to ±35%)."
            )
        case "growth_rate":
            return MethodInfo(
                name: "Growth Rate",
                icon: "chart.line.uptrend.xyaxis",
                description: "Compound daily growth rate extrapolation capped at ±0.5%/day. Confidence from growth stability. Band ±15%."
            )
        default:
            return MethodInfo(name: method, icon: "questionmark.circle", description: "")
        }
    }
}
