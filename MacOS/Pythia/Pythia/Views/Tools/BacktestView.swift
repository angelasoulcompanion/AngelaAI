//
//  BacktestView.swift
//  Pythia — SMA Crossover Backtesting
//

import SwiftUI
import Charts

struct BacktestView: View {
    @EnvironmentObject var db: DatabaseService

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
                    AssetPickerView(selectedId: $selectedAssetId, showName: true)

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
                MetricBox("Total Return", PythiaTheme.formatPercent(r.totalReturn), PythiaTheme.profitLossColor(r.totalReturn), size: .small)
                MetricBox("Ann. Return", PythiaTheme.formatPercent(r.annualizedReturn), PythiaTheme.profitLossColor(r.annualizedReturn), size: .small)
                MetricBox("Max Drawdown", PythiaTheme.formatPercent(abs(r.maxDrawdown)), PythiaTheme.loss, size: .small)
                MetricBox("Sharpe", String(format: "%.3f", r.sharpeRatio), PythiaTheme.secondaryBlue, size: .small)
                MetricBox("Win Rate", PythiaTheme.formatPercent(r.winRate), r.winRate > 0.5 ? PythiaTheme.profit : PythiaTheme.loss, size: .small)
                MetricBox("Trades", "\(r.nTrades)", PythiaTheme.textPrimary, size: .small)
            }

            PythiaDivider()

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Strategy", PythiaTheme.formatCurrency(r.finalValue), PythiaTheme.profitLossColor(r.totalReturn), size: .small)
                MetricBox("Benchmark", PythiaTheme.formatPercent(r.benchmarkReturn), PythiaTheme.textSecondary, size: .small)
                MetricBox("Excess", PythiaTheme.formatPercent(r.excessReturn), PythiaTheme.profitLossColor(r.excessReturn), size: .small)
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
            .pythiaChartAxes()
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
