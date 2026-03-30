//
//  StrategyBuilderView.swift
//  Pythia — Strategy Builder + Backtesting (Phase 7.6 + 7.7)
//

import SwiftUI
import Charts

struct StrategyBuilderView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var strategies: [StrategyItem] = []
    @State private var presets: [PresetItem] = []
    @State private var selectedAssetId: String?
    @State private var evalResult: StrategyEvalResponse?
    @State private var isLoading = false
    @State private var isEvaluating = false
    @State private var selectedStrategyId: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Strategy Builder")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Preset strategies
                presetSection

                // My strategies list
                strategyListSection

                // Evaluate
                evaluateSection

                if isEvaluating { LoadingView("Running backtest...") }

                // Results
                if let r = evalResult, r.success {
                    metricsCard(r)
                    equityChart(r)
                    tradeListCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadData() }
    }

    // MARK: - Preset Section

    private var presetSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Quick Start — Preset Strategies")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 10), count: 3), spacing: 10) {
                ForEach(presets) { preset in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(preset.name)
                            .font(.system(size: 13, weight: .bold))
                            .foregroundColor(PythiaTheme.textPrimary)
                            .lineLimit(1)

                        Text(preset.description)
                            .font(.system(size: 11))
                            .foregroundColor(PythiaTheme.textSecondary)
                            .lineLimit(2)

                        HStack {
                            Text(preset.type.uppercased())
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(PythiaTheme.accentGold)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(PythiaTheme.accentGold.opacity(0.15))
                                .cornerRadius(4)

                            Spacer()

                            Button("Create") {
                                Task { await createFromPreset(preset.key) }
                            }
                            .buttonStyle(.plain)
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(PythiaTheme.secondaryBlue)
                        }
                    }
                    .padding(10)
                    .background(PythiaTheme.surfaceBackground.opacity(0.5))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(PythiaTheme.surfaceBackground, lineWidth: 1))
                    .cornerRadius(8)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Strategy List

    private var strategyListSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("My Strategies (\(strategies.count))")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Button("Refresh") { Task { await loadStrategies() } }
                    .buttonStyle(.plain)
                    .foregroundColor(PythiaTheme.accentGold)
            }

            if strategies.isEmpty {
                Text("No strategies yet. Create one from presets above.")
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textTertiary)
            } else {
                ForEach(strategies) { s in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(s.name)
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(PythiaTheme.textPrimary)
                            Text(s.strategyType.uppercased())
                                .font(.system(size: 10))
                                .foregroundColor(PythiaTheme.textTertiary)
                        }

                        Spacer()

                        Button(selectedStrategyId == s.strategyId ? "Selected" : "Select") {
                            selectedStrategyId = s.strategyId
                        }
                        .buttonStyle(.plain)
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(selectedStrategyId == s.strategyId ? PythiaTheme.profit : PythiaTheme.secondaryBlue)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(selectedStrategyId == s.strategyId ? PythiaTheme.profit.opacity(0.15) : PythiaTheme.surfaceBackground)
                        .cornerRadius(6)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Evaluate Section

    private var evaluateSection: some View {
        HStack(spacing: PythiaTheme.spacing) {
            AssetPickerView(selectedId: $selectedAssetId)

            Button("Run Backtest") { Task { await evaluate() } }
                .pythiaPrimaryButton()
                .disabled(selectedStrategyId == nil || selectedAssetId == nil)

            if let sid = selectedStrategyId {
                Text("Strategy: \(strategies.first { $0.strategyId == sid }?.name ?? sid.prefix(8).description)")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
            }

            Spacer()
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Metrics Card

    private func metricsCard(_ r: StrategyEvalResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(r.strategyName)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(r.totalReturn >= 0 ? "PROFITABLE" : "LOSS")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(r.totalReturn >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background((r.totalReturn >= 0 ? PythiaTheme.profit : PythiaTheme.loss).opacity(0.15))
                    .cornerRadius(6)
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: PythiaTheme.spacing) {
                MetricBox("Return", String(format: "%+.1f%%", r.totalReturn * 100),
                          r.totalReturn >= 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .medium)
                MetricBox("Sharpe", String(format: "%.2f", r.sharpeRatio),
                          r.sharpeRatio > 1 ? PythiaTheme.profit : PythiaTheme.accentGold, size: .medium)
                MetricBox("Max DD", String(format: "%.1f%%", r.maxDrawdown * 100),
                          PythiaTheme.loss, size: .medium)
                MetricBox("Win Rate", String(format: "%.0f%%", r.winRate * 100),
                          r.winRate > 0.5 ? PythiaTheme.profit : PythiaTheme.loss, size: .medium)
                MetricBox("Trades", "\(r.totalTrades)",
                          PythiaTheme.accentGold, size: .medium)
                MetricBox("Profit Factor", String(format: "%.2f", r.profitFactor),
                          r.profitFactor > 1 ? PythiaTheme.profit : PythiaTheme.loss, size: .medium)
                MetricBox("Avg Hold", String(format: "%.0fd", r.avgHoldingDays),
                          PythiaTheme.textPrimary, size: .medium)
                MetricBox("Ann. Return", String(format: "%+.1f%%", r.annualizedReturn * 100),
                          r.annualizedReturn >= 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .medium)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Equity Curve

    private func equityChart(_ r: StrategyEvalResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Equity Curve")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(r.equityCurve) { point in
                LineMark(
                    x: .value("Date", point.date),
                    y: .value("Equity", point.equity)
                )
                .foregroundStyle(PythiaTheme.accentGold)

                AreaMark(
                    x: .value("Date", point.date),
                    y: .value("Equity", point.equity)
                )
                .foregroundStyle(PythiaTheme.accentGold.opacity(0.1))
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisValueLabel {
                        Text(String(format: "%.0f", value.as(Double.self) ?? 0))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }
            .frame(height: 250)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Trade List

    private func tradeListCard(_ r: StrategyEvalResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Trade History (\(r.trades.count))")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            // Header
            HStack {
                Text("Entry").frame(width: 90, alignment: .leading)
                Text("Exit").frame(width: 90, alignment: .leading)
                Text("Dir").frame(width: 50, alignment: .center)
                Text("PnL %").frame(width: 70, alignment: .trailing)
                Text("PnL $").frame(width: 80, alignment: .trailing)
                Text("Days").frame(width: 40, alignment: .trailing)
                Text("Reason").frame(width: 90, alignment: .leading)
            }
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(PythiaTheme.textSecondary)

            Divider().background(PythiaTheme.surfaceBackground)

            ForEach(r.trades) { trade in
                HStack {
                    Text(String(trade.entryDate.prefix(10)))
                        .frame(width: 90, alignment: .leading)
                    Text(String(trade.exitDate.prefix(10)))
                        .frame(width: 90, alignment: .leading)
                    Text(trade.direction == "long" ? "LONG" : "SHORT")
                        .frame(width: 50, alignment: .center)
                        .foregroundColor(trade.direction == "long" ? PythiaTheme.profit : PythiaTheme.loss)
                    Text(String(format: "%+.2f%%", trade.pnlPct * 100))
                        .frame(width: 70, alignment: .trailing)
                        .foregroundColor(trade.pnlPct >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                    Text(String(format: "%+.0f", trade.pnlValue))
                        .frame(width: 80, alignment: .trailing)
                        .foregroundColor(trade.pnlValue >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                    Text("\(trade.holdingDays)")
                        .frame(width: 40, alignment: .trailing)
                    Text(trade.exitReason.replacingOccurrences(of: "_", with: " "))
                        .frame(width: 90, alignment: .leading)
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                .font(.system(size: 11, design: .monospaced))
                .foregroundColor(PythiaTheme.textSecondary)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - API

    private func loadData() async {
        await loadStrategies()
        await loadPresets()
    }

    private func loadStrategies() async {
        do {
            let resp: StrategyListResponse = try await db.get("/strategies/")
            strategies = resp.strategies
        } catch { strategies = [] }
    }

    private func loadPresets() async {
        do {
            let resp: PresetListResponse = try await db.get("/strategies/presets")
            presets = resp.presets
        } catch { presets = [] }
    }

    private func createFromPreset(_ key: String) async {
        do {
            let _: CreateStrategyResponse = try await db.post("/strategies/from-preset/\(key)", body: EmptyBody())
            await loadStrategies()
        } catch {}
    }

    private func evaluate() async {
        guard let sid = selectedStrategyId, let aid = selectedAssetId else { return }
        isEvaluating = true
        defer { isEvaluating = false }
        do {
            let body = ["asset_id": aid]
            evalResult = try await db.post("/strategies/\(sid)/evaluate", body: body)
        } catch {
            evalResult = nil
        }
    }
}

// EmptyBody is defined elsewhere — reuse it
