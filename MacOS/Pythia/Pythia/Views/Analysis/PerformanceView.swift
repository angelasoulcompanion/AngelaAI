//
//  PerformanceView.swift
//  Pythia — Performance Metrics Dashboard
//

import SwiftUI
import Charts

struct PerformanceView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var portfolios: [Portfolio] = []
    @State private var selectedPortfolioId: String?
    @State private var metrics: PerformanceMetricsResponse?
    @State private var drawdown: DrawdownResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var days = 365

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Performance Metrics")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    Picker("Portfolio", selection: Binding(
                        get: { selectedPortfolioId ?? "" },
                        set: { selectedPortfolioId = $0.isEmpty ? nil : $0 }
                    )) {
                        Text("Select Portfolio").tag("")
                        ForEach(portfolios) { p in
                            Text(p.name).tag(p.portfolioId)
                        }
                    }
                    .frame(width: 200)

                    Picker("Period", selection: $days) {
                        Text("90 Days").tag(90)
                        Text("1 Year").tag(365)
                        Text("3 Years").tag(1095)
                    }
                    .frame(width: 120)

                    Button("Analyze") {
                        Task { await loadMetrics() }
                    }
                    .pythiaPrimaryButton()
                    .disabled(selectedPortfolioId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading {
                    LoadingView("Calculating metrics...")
                }

                if let m = metrics, m.success {
                    returnsCard(m)
                    ratiosCard(m)
                    riskCard(m)
                    distributionCard(m)
                }

                if let dd = drawdown, dd.error == nil {
                    drawdownCard(dd)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadPortfolios() }
    }

    // MARK: - Returns Card

    private func returnsCard(_ m: PerformanceMetricsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Returns")

            HStack(spacing: PythiaTheme.largeSpacing) {
                perfMetric("Total Return", PythiaTheme.formatPercent(m.returns?.totalReturn ?? 0),
                           PythiaTheme.profitLossColor(m.returns?.totalReturn ?? 0))
                perfMetric("Annualized", PythiaTheme.formatPercent(m.returns?.annualizedReturn ?? 0),
                           PythiaTheme.profitLossColor(m.returns?.annualizedReturn ?? 0))
                perfMetric("Beta", String(format: "%.3f", m.market?.beta ?? 0), PythiaTheme.secondaryBlue)
                perfMetric("Alpha", PythiaTheme.formatPercent(m.market?.alpha ?? 0),
                           PythiaTheme.profitLossColor(m.market?.alpha ?? 0))
                perfMetric("R\u{00B2}", String(format: "%.3f", m.market?.rSquared ?? 0), PythiaTheme.textSecondary)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Ratios Card

    private func ratiosCard(_ m: PerformanceMetricsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Risk-Adjusted Ratios")

            HStack(spacing: PythiaTheme.largeSpacing) {
                ratioGauge("Sharpe", m.ratios?.sharpeRatio ?? 0)
                ratioGauge("Sortino", m.ratios?.sortinoRatio ?? 0)
                ratioGauge("Calmar", m.ratios?.calmarRatio ?? 0)
                ratioGauge("Treynor", m.ratios?.treynorRatio ?? 0)
                ratioGauge("Info Ratio", m.ratios?.informationRatio ?? 0)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Risk Card

    private func riskCard(_ m: PerformanceMetricsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Risk Metrics")

            HStack(spacing: PythiaTheme.largeSpacing) {
                perfMetric("Volatility", PythiaTheme.formatPercent(m.risk?.volatility ?? 0), PythiaTheme.accentGold)
                perfMetric("Downside Dev", PythiaTheme.formatPercent(m.risk?.downsideDeviation ?? 0), PythiaTheme.loss)
                perfMetric("Max Drawdown", PythiaTheme.formatPercent(abs(m.risk?.maxDrawdown ?? 0)), PythiaTheme.loss)
                perfMetric("VaR 95%", PythiaTheme.formatPercent(abs(m.risk?.var95 ?? 0)), PythiaTheme.warningOrange)
                perfMetric("CVaR 95%", PythiaTheme.formatPercent(abs(m.risk?.cvar95 ?? 0)), PythiaTheme.errorRed)
                perfMetric("Tracking Error", PythiaTheme.formatPercent(m.market?.trackingError ?? 0), PythiaTheme.textSecondary)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Distribution Card

    private func distributionCard(_ m: PerformanceMetricsResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Return Distribution")

            HStack(spacing: PythiaTheme.largeSpacing) {
                perfMetric("Skewness", String(format: "%.3f", m.distribution?.skewness ?? 0),
                           (m.distribution?.skewness ?? 0) < 0 ? PythiaTheme.loss : PythiaTheme.profit)
                perfMetric("Excess Kurtosis", String(format: "%.3f", m.distribution?.excessKurtosis ?? 0),
                           (m.distribution?.excessKurtosis ?? 0) > 3 ? PythiaTheme.warningOrange : PythiaTheme.textPrimary)
                perfMetric("Observations", "\(m.meta?.nObservations ?? 0)", PythiaTheme.textSecondary)
            }

            if let skew = m.distribution?.skewness, let kurt = m.distribution?.excessKurtosis {
                Text(skew < 0 ? "Negative skew: heavier left tail (more extreme losses)" : "Positive skew: heavier right tail")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                Text(kurt > 3 ? "Leptokurtic: fat tails — more extreme events than normal" : "Approximately normal tails")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Drawdown Card

    private func drawdownCard(_ dd: DrawdownResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Drawdown Analysis")

            HStack(spacing: PythiaTheme.largeSpacing) {
                perfMetric("Max Drawdown", PythiaTheme.formatPercent(abs(dd.maxDrawdown ?? 0)), PythiaTheme.loss)
                perfMetric("Current Drawdown", PythiaTheme.formatPercent(abs(dd.currentDrawdown ?? 0)),
                           (dd.currentDrawdown ?? 0) < -0.05 ? PythiaTheme.loss : PythiaTheme.profit)
            }

            if let periods = dd.topDrawdowns, !periods.isEmpty {
                Text("Top Drawdown Periods")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textSecondary)
                    .padding(.top, 4)

                ForEach(periods) { p in
                    HStack {
                        Text("\(p.startDate) → \(p.endDate)")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textSecondary)
                        Spacer()
                        Text(PythiaTheme.formatPercent(abs(p.drawdown)))
                            .font(PythiaTheme.monospace())
                            .foregroundColor(PythiaTheme.loss)
                        Text("\(p.durationDays)d")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                            .frame(width: 40)
                    }
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Components

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(PythiaTheme.headline())
            .foregroundColor(PythiaTheme.textPrimary)
    }

    private func perfMetric(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(minWidth: 90)
    }

    private func ratioGauge(_ label: String, _ value: Double) -> some View {
        VStack(spacing: 4) {
            Text(String(format: "%.3f", value))
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundColor(value > 0 ? PythiaTheme.profit : (value < 0 ? PythiaTheme.loss : PythiaTheme.textSecondary))
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
            // Quality indicator
            HStack(spacing: 2) {
                ForEach(0..<5) { i in
                    Circle()
                        .fill(Double(i) < (value + 1) * 2.5 ? PythiaTheme.accentGold : PythiaTheme.surfaceBackground)
                        .frame(width: 6, height: 6)
                }
            }
        }
        .frame(minWidth: 90)
    }

    // MARK: - Data

    private func loadPortfolios() async {
        do { portfolios = try await db.fetchPortfolios() } catch {}
    }

    private func loadMetrics() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true; errorMessage = nil
        do {
            async let m = db.fetchPerformanceMetrics(portfolioId: pid, days: days)
            async let d = db.fetchDrawdownAnalysis(portfolioId: pid, days: days)
            metrics = try await m
            drawdown = try await d
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
