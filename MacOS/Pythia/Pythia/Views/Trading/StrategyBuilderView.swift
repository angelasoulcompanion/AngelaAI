//
//  StrategyBuilderView.swift
//  Pythia — Strategy Builder with Visual Rule Editor
//

import SwiftUI
import Charts

struct StrategyBuilderView: View {
    @EnvironmentObject var db: DatabaseService

    // Data
    @State private var strategies: [StrategyItem] = []
    @State private var presets: [PresetItem] = []

    // Builder state
    @State private var strategyName = ""
    @State private var strategyType = "custom"
    @State private var strategyDescription = ""
    @State private var entryRules: [EntryRuleConfig] = []
    @State private var exitRules: [ExitRuleConfig] = []
    @State private var txnCostBps = 10

    // Backtest state
    @State private var selectedAssetId: String?
    @State private var initialCapital: Double = 1_000_000
    @State private var evalResult: StrategyEvalResponse?

    // UI state
    @State private var selectedStrategyId: String?
    @State private var isEditing = false
    @State private var isLoading = false
    @State private var isEvaluating = false
    @State private var isSaving = false
    @State private var showEntryPicker = false
    @State private var showExitPicker = false

    private let strategyTypes = ["custom", "trend_following", "mean_reversion", "momentum", "breakout"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                headerSection
                presetSection
                strategyListSection
                builderSection
                rulesSection
                actionBar

                if isEvaluating { LoadingView("Running backtest...") }

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

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            Text("Strategy Builder")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)
            Spacer()
            Button { resetBuilder() } label: {
                Label("New", systemImage: "plus.circle")
                    .font(.system(size: 13, weight: .medium))
            }
            .buttonStyle(.plain)
            .foregroundColor(PythiaTheme.accentGold)
        }
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
                    .font(.system(size: 12))
            }

            if strategies.isEmpty {
                Text("No strategies yet. Create one from presets or build your own below.")
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textTertiary)
            } else {
                ForEach(strategies) { s in
                    HStack(spacing: 12) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(s.name)
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(PythiaTheme.textPrimary)
                            Text(s.strategyType.replacingOccurrences(of: "_", with: " ").uppercased())
                                .font(.system(size: 10))
                                .foregroundColor(PythiaTheme.textTertiary)
                        }

                        Spacer()

                        // Edit
                        Button {
                            Task { await loadStrategyConfig(s.strategyId) }
                        } label: {
                            Image(systemName: "pencil")
                                .font(.system(size: 11))
                        }
                        .buttonStyle(.plain)
                        .foregroundColor(PythiaTheme.accentGold)

                        // Delete
                        Button {
                            Task { await deleteStrategy(s.strategyId) }
                        } label: {
                            Image(systemName: "trash")
                                .font(.system(size: 11))
                        }
                        .buttonStyle(.plain)
                        .foregroundColor(PythiaTheme.loss.opacity(0.7))

                        // Select for backtest
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

    // MARK: - Builder Section

    private var builderSection: some View {
        HStack(alignment: .top, spacing: PythiaTheme.spacing) {
            // Left: Strategy config
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text(isEditing ? "Edit Strategy" : "Build Custom Strategy")
                        .font(PythiaTheme.heading())
                        .foregroundColor(PythiaTheme.textPrimary)
                    if isEditing {
                        Text("EDITING")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(PythiaTheme.accentGold)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(PythiaTheme.accentGold.opacity(0.15))
                            .cornerRadius(4)
                    }
                }

                builderField("Name", text: $strategyName, placeholder: "My Strategy")

                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Type")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(PythiaTheme.textSecondary)
                        Picker("", selection: $strategyType) {
                            ForEach(strategyTypes, id: \.self) { t in
                                Text(t.replacingOccurrences(of: "_", with: " ").capitalized).tag(t)
                            }
                        }
                        .labelsHidden()
                        .frame(width: 160)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Txn Cost (bps)")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(PythiaTheme.textSecondary)
                        TextField("10", value: $txnCostBps, format: .number)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 80)
                    }
                }

                builderField("Description", text: $strategyDescription, placeholder: "Optional description...")
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            Divider().background(PythiaTheme.surfaceBackground)

            // Right: Backtest config
            VStack(alignment: .leading, spacing: 12) {
                Text("Backtest Settings")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)

                AssetPickerView(selectedId: $selectedAssetId)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Initial Capital")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(PythiaTheme.textSecondary)
                    TextField("1000000", value: $initialCapital, format: .number)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 160)
                }

                if let sid = selectedStrategyId,
                   let name = strategies.first(where: { $0.strategyId == sid })?.name {
                    HStack(spacing: 6) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(PythiaTheme.profit)
                            .font(.system(size: 12))
                        Text(name)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(PythiaTheme.textPrimary)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Rules Section

    private var rulesSection: some View {
        HStack(alignment: .top, spacing: PythiaTheme.spacing) {
            // Entry Rules
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Entry Rules")
                        .font(PythiaTheme.heading())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text("(\(entryRules.count))")
                        .font(.system(size: 12))
                        .foregroundColor(PythiaTheme.textTertiary)
                    Spacer()
                }

                if entryRules.isEmpty {
                    emptyRuleHint("No entry rules — default: SMA20 > SMA50")
                }

                ForEach($entryRules) { $rule in
                    entryRuleCard($rule)
                }

                Menu {
                    ForEach(EntryRuleType.allCases) { type in
                        Button {
                            entryRules.append(EntryRuleConfig(type: type))
                        } label: {
                            Label(type.displayName, systemImage: type.icon)
                        }
                    }
                } label: {
                    Label("Add Entry Rule", systemImage: "plus.circle.fill")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(PythiaTheme.secondaryBlue)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(PythiaTheme.secondaryBlue.opacity(0.1))
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            Divider().background(PythiaTheme.surfaceBackground)

            // Exit Rules
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Exit Rules")
                        .font(PythiaTheme.heading())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text("(\(exitRules.count))")
                        .font(.system(size: 12))
                        .foregroundColor(PythiaTheme.textTertiary)
                    Spacer()
                }

                if exitRules.isEmpty {
                    emptyRuleHint("No exit rules — default: 10% TP, 5% SL, 20d time")
                }

                ForEach($exitRules) { $rule in
                    exitRuleCard($rule)
                }

                Menu {
                    ForEach(ExitRuleType.allCases) { type in
                        Button {
                            exitRules.append(ExitRuleConfig(type: type))
                        } label: {
                            Label(type.displayName, systemImage: type.icon)
                        }
                    }
                } label: {
                    Label("Add Exit Rule", systemImage: "plus.circle.fill")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(PythiaTheme.secondaryBlue)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(PythiaTheme.secondaryBlue.opacity(0.1))
                        .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Entry Rule Card

    private func entryRuleCard(_ rule: Binding<EntryRuleConfig>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: rule.wrappedValue.type.icon)
                    .foregroundColor(PythiaTheme.secondaryBlue)
                    .font(.system(size: 12))
                Text(rule.wrappedValue.type.displayName)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Button {
                    entryRules.removeAll { $0.id == rule.wrappedValue.id }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(PythiaTheme.textTertiary)
                        .font(.system(size: 14))
                }
                .buttonStyle(.plain)
            }

            Text(rule.wrappedValue.type.description)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textTertiary)

            HStack(spacing: 12) {
                paramField(rule.wrappedValue.type.param1Label, value: rule.param1)

                if rule.wrappedValue.type.param2Label != nil {
                    paramField(rule.wrappedValue.type.param2Label!, value: rule.param2)
                }
            }
        }
        .padding(10)
        .background(PythiaTheme.surfaceBackground.opacity(0.5))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(PythiaTheme.secondaryBlue.opacity(0.3), lineWidth: 1))
        .cornerRadius(8)
    }

    // MARK: - Exit Rule Card

    private func exitRuleCard(_ rule: Binding<ExitRuleConfig>) -> some View {
        let ruleType = rule.wrappedValue.type
        let color: Color = ruleType == .take_profit ? PythiaTheme.profit :
                           ruleType == .stop_loss ? PythiaTheme.loss :
                           ruleType == .trailing_stop ? PythiaTheme.accentGold : PythiaTheme.secondaryBlue

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: ruleType.icon)
                    .foregroundColor(color)
                    .font(.system(size: 12))
                Text(ruleType.displayName)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(PythiaTheme.textPrimary)

                Spacer()

                if ruleType.isPercentage {
                    Text(String(format: "%.0f%%", rule.wrappedValue.value * 100))
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundColor(color)
                } else {
                    Text(String(format: "%.0f days", rule.wrappedValue.value))
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundColor(color)
                }

                Button {
                    exitRules.removeAll { $0.id == rule.wrappedValue.id }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(PythiaTheme.textTertiary)
                        .font(.system(size: 14))
                }
                .buttonStyle(.plain)
            }

            Text(ruleType.description)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textTertiary)

            HStack(spacing: 12) {
                paramField(ruleType.valueLabel, value: rule.value)

                if ruleType.isPercentage {
                    Slider(value: rule.value, in: 0.01...0.50, step: 0.01)
                        .tint(color)
                } else {
                    Slider(value: rule.value, in: 1...100, step: 1)
                        .tint(color)
                }
            }
        }
        .padding(10)
        .background(PythiaTheme.surfaceBackground.opacity(0.5))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(color.opacity(0.3), lineWidth: 1))
        .cornerRadius(8)
    }

    // MARK: - Action Bar

    private var actionBar: some View {
        HStack(spacing: 12) {
            // Save Strategy
            Button {
                Task { await saveStrategy() }
            } label: {
                Label(isEditing ? "Update Strategy" : "Save Strategy", systemImage: "square.and.arrow.down")
                    .font(.system(size: 13, weight: .bold))
            }
            .pythiaSecondaryButton()
            .disabled(strategyName.isEmpty || isSaving)

            // Run Backtest
            Button {
                Task { await evaluate() }
            } label: {
                Label("Run Backtest", systemImage: "play.fill")
                    .font(.system(size: 13, weight: .bold))
            }
            .pythiaPrimaryButton()
            .disabled(selectedStrategyId == nil || selectedAssetId == nil || isEvaluating)

            if isSaving {
                ProgressView()
                    .controlSize(.small)
            }

            Spacer()

            if isEditing {
                Button("Cancel Edit") { resetBuilder() }
                    .buttonStyle(.plain)
                    .font(.system(size: 12))
                    .foregroundColor(PythiaTheme.textTertiary)
            }
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

    // MARK: - Helper Views

    private func builderField(_ label: String, text: Binding<String>, placeholder: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(PythiaTheme.textSecondary)
            TextField(placeholder, text: text)
                .textFieldStyle(.roundedBorder)
        }
    }

    private func paramField(_ label: String, value: Binding<Double>) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(PythiaTheme.textTertiary)
            TextField("", value: value, format: .number)
                .textFieldStyle(.roundedBorder)
                .font(.system(size: 11, design: .monospaced))
                .frame(width: 80)
        }
    }

    private func emptyRuleHint(_ text: String) -> some View {
        Text(text)
            .font(.system(size: 11))
            .foregroundColor(PythiaTheme.textTertiary)
            .italic()
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.vertical, 8)
    }

    // MARK: - API Calls

    private func loadData() async {
        isLoading = true
        defer { isLoading = false }
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

    private func loadStrategyConfig(_ strategyId: String) async {
        do {
            let detail: StrategyDetailResponse = try await db.get("/strategies/\(strategyId)")
            selectedStrategyId = strategyId
            strategyName = detail.name
            strategyType = detail.strategyType
            strategyDescription = detail.description ?? ""
            txnCostBps = detail.config.transactionCostBps ?? 10

            entryRules = (detail.config.entryRules ?? []).map { EntryRuleConfig.fromPayload($0) }
            exitRules = (detail.config.exitRules ?? []).map { ExitRuleConfig.fromPayload($0) }

            isEditing = true
        } catch {}
    }

    private func saveStrategy() async {
        guard !strategyName.isEmpty else { return }
        isSaving = true
        defer { isSaving = false }

        let body = StrategyCreateBody(
            name: strategyName,
            strategyType: strategyType,
            description: strategyDescription,
            entryRules: entryRules.map { $0.toPayload() },
            exitRules: exitRules.map { $0.toPayload() },
            positionSizing: PositionSizingPayload(method: "fixed_pct", value: 0.1),
            transactionCostBps: txnCostBps
        )

        do {
            if isEditing, let sid = selectedStrategyId {
                let _: CreateStrategyResponse = try await db.put("/strategies/\(sid)", body: body)
            } else {
                let resp: CreateStrategyResponse = try await db.post("/strategies/", body: body)
                selectedStrategyId = resp.strategyId
            }
            await loadStrategies()
            if !isEditing { resetBuilder() }
        } catch {}
    }

    private func deleteStrategy(_ strategyId: String) async {
        do {
            try await db.delete("/strategies/\(strategyId)")
            if selectedStrategyId == strategyId {
                selectedStrategyId = nil
                evalResult = nil
            }
            await loadStrategies()
        } catch {}
    }

    private func evaluate() async {
        guard let sid = selectedStrategyId, let aid = selectedAssetId else { return }
        isEvaluating = true
        defer { isEvaluating = false }
        do {
            let body = StrategyEvalBody(assetId: aid, initialCapital: initialCapital)
            evalResult = try await db.post("/strategies/\(sid)/evaluate", body: body)
        } catch {
            evalResult = nil
        }
    }

    private func resetBuilder() {
        strategyName = ""
        strategyType = "custom"
        strategyDescription = ""
        entryRules = []
        exitRules = []
        txnCostBps = 10
        isEditing = false
    }
}
