//
//  BacktestView.swift
//  Pythia — SMA Crossover Backtesting
//

import SwiftUI
import Charts

struct BacktestView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var assets: [Asset] = []
    @State private var selectedAssetId: String?
    @State private var shortWindow = 20
    @State private var longWindow = 50
    @State private var capital = 1_000_000.0
    @State private var result: BacktestResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Backtesting")
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
                            Text("\(a.symbol) — \(a.name)").tag(a.assetId)
                        }
                    }
                    .frame(width: 250)

                    Stepper("Short SMA: \(shortWindow)", value: $shortWindow, in: 5...100)
                        .frame(width: 180)
                    Stepper("Long SMA: \(longWindow)", value: $longWindow, in: 10...300)
                        .frame(width: 180)

                    Button("Run Backtest") { Task { await runBacktest() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Running backtest...") }

                if let r = result, r.success {
                    summaryCard(r)
                    equityChart(r)
                    tradesCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { assets = try await db.fetchAssets() } catch {} }
    }

    private func summaryCard(_ r: BacktestResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("\(r.strategyName) — \(r.symbol)")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("\(r.startDate) → \(r.endDate)")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                metricBox("Total Return", PythiaTheme.formatPercent(r.totalReturn), PythiaTheme.profitLossColor(r.totalReturn))
                metricBox("Ann. Return", PythiaTheme.formatPercent(r.annualizedReturn), PythiaTheme.profitLossColor(r.annualizedReturn))
                metricBox("Max Drawdown", PythiaTheme.formatPercent(abs(r.maxDrawdown)), PythiaTheme.loss)
                metricBox("Sharpe", String(format: "%.3f", r.sharpeRatio), PythiaTheme.secondaryBlue)
                metricBox("Win Rate", PythiaTheme.formatPercent(r.winRate), r.winRate > 0.5 ? PythiaTheme.profit : PythiaTheme.loss)
                metricBox("Trades", "\(r.nTrades)", PythiaTheme.textPrimary)
            }

            Divider().background(PythiaTheme.textTertiary)

            HStack(spacing: PythiaTheme.largeSpacing) {
                metricBox("Strategy", PythiaTheme.formatCurrency(r.finalValue), PythiaTheme.profitLossColor(r.totalReturn))
                metricBox("Benchmark", PythiaTheme.formatPercent(r.benchmarkReturn), PythiaTheme.textSecondary)
                metricBox("Excess", PythiaTheme.formatPercent(r.excessReturn), PythiaTheme.profitLossColor(r.excessReturn))
            }
        }
        .padding()
        .pythiaCard()
    }

    private func equityChart(_ r: BacktestResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Equity Curve")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(r.equityCurve) { point in
                LineMark(
                    x: .value("Date", point.date),
                    y: .value("Value", point.value)
                )
                .foregroundStyle(PythiaTheme.secondaryBlue)
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 6)) { _ in
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .frame(height: 250)
        }
        .padding()
        .pythiaCard()
    }

    private func tradesCard(_ r: BacktestResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Trade Log (\(r.trades.count) trades)")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            ForEach(r.trades) { t in
                HStack {
                    Text(t.date)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                        .frame(width: 100)
                    Text(t.type)
                        .font(PythiaTheme.body())
                        .foregroundColor(t.type == "BUY" ? PythiaTheme.profit : PythiaTheme.loss)
                        .frame(width: 50)
                    Text(String(format: "%.2f", t.price))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(width: 80)
                    Text("\(t.shares) shares")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                    if let pnl = t.pnl {
                        Text(PythiaTheme.formatCurrency(pnl))
                            .font(PythiaTheme.monospace())
                            .foregroundColor(PythiaTheme.profitLossColor(pnl))
                    }
                    Spacer()
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func metricBox(_ label: String, _ value: String, _ color: Color) -> some View {
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

    private func runBacktest() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true; errorMessage = nil
        do {
            result = try await db.runBacktest(assetId: aid, shortWindow: shortWindow, longWindow: longWindow, capital: capital)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
