//
//  OptionsChainView.swift
//  Pythia — Options Analysis with AI Suggestion
//

import SwiftUI
import Charts

struct OptionsChainView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var strikeStr = ""
    @State private var selectedExpiry = 0.25
    @State private var result: OptionAnalysisResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let expiries: [(Double, String)] = [
        (1.0/12, "1M"), (0.25, "3M"), (0.5, "6M"), (1.0, "1Y"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Options Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Control Bar
                controlBar

                if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if isLoading { LoadingView("Fetching market data & analyzing...") }

                if let r = result {
                    quoteCard(r)
                    suggestionCard(r.suggestion)
                    pricingCards(r)
                    greeksTable(r)
                    optionPayoffChart(r)
                    if let bs = r.bsModel {
                        blackScholesSection(r, bs: bs)
                    }
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

            VStack(alignment: .leading, spacing: 2) {
                Text("Strike")
                    .font(.system(size: 10))
                    .foregroundColor(PythiaTheme.textTertiary)
                TextField("ATM", text: $strikeStr)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 80)
                    .font(PythiaTheme.monospace())
            }

            // Expiry chips
            Picker("Expiry", selection: $selectedExpiry) {
                ForEach(expiries, id: \.0) { val, label in
                    Text(label).tag(val)
                }
            }
            .pickerStyle(.segmented)
            .frame(width: 220)

            Button("Analyze") { Task { await analyze() } }
                .pythiaPrimaryButton()
                .disabled(selectedAssetId == nil)

            Spacer()
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Quote Card

    private func quoteCard(_ r: OptionAnalysisResponse) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(r.symbol)
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)
                Text(r.quote.name)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textSecondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                Text(String(format: "%.2f", r.spot))
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundColor(PythiaTheme.textPrimary)
                HStack(spacing: 4) {
                    Image(systemName: r.quote.changePercent >= 0 ? "arrow.up.right" : "arrow.down.right")
                    Text(String(format: "%.2f%%", r.quote.changePercent * 100))
                }
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.profitLossColor(r.quote.changePercent))
            }
            Divider().frame(height: 40).padding(.horizontal, 12)
            VStack(alignment: .leading, spacing: 4) {
                metricRow("Hist Vol", String(format: "%.1f%%", r.historicalVol * 100))
                metricRow("Risk-Free", String(format: "%.2f%%", r.riskFreeRate * 100))
                metricRow("Expiry", String(format: "%.2f yr", r.timeToExpiry))
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Suggestion Card

    private func suggestionCard(_ s: OptionSuggestion) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                Text(s.direction == "call" ? "📈" : s.direction == "put" ? "📉" : "⚖️")
                    .font(.system(size: 36))

                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 8) {
                        Text(s.direction.uppercased())
                            .font(.system(size: 22, weight: .bold, design: .rounded))
                            .foregroundColor(directionColor(s.direction))

                        Text(s.confidence.capitalized)
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(confidenceColor(s.confidence))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(confidenceColor(s.confidence).opacity(0.15))
                            .cornerRadius(8)
                    }
                    Text(s.summary)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                Spacer()
            }

            // Recommended Contract
            if let c = s.contract {
                contractCard(c, direction: s.direction)
            }

            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

            ForEach(s.signals) { sig in
                HStack {
                    Circle()
                        .fill(signalColor(sig.signal))
                        .frame(width: 8, height: 8)
                    Text(sig.name)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(width: 110, alignment: .leading)
                    Text(sig.value.displayString)
                        .font(PythiaTheme.monospace())
                        .foregroundColor(signalColor(sig.signal))
                        .frame(width: 100, alignment: .trailing)
                    Text(sig.detail)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                        .lineLimit(1)
                    Spacer()
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Pricing Cards (Call vs Put)

    private func pricingCards(_ r: OptionAnalysisResponse) -> some View {
        HStack(spacing: PythiaTheme.spacing) {
            pricingSide("CALL", side: r.call, color: PythiaTheme.profit,
                        isRecommended: r.suggestion.direction == "call")
            pricingSide("PUT", side: r.put, color: PythiaTheme.loss,
                        isRecommended: r.suggestion.direction == "put")
        }
    }

    private func pricingSide(_ label: String, side: OptionSide, color: Color, isRecommended: Bool) -> some View {
        VStack(spacing: 12) {
            HStack {
                if isRecommended {
                    Image(systemName: "star.fill")
                        .font(.caption)
                        .foregroundColor(PythiaTheme.accentGold)
                }
                Text(label)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(color)
                Spacer()
            }

            Text(String(format: "%.4f", side.price))
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(PythiaTheme.textPrimary)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                pricingMetric("Intrinsic", side.intrinsicValue)
                pricingMetric("Time Value", side.timeValue)
            }
        }
        .padding()
        .background(isRecommended ? color.opacity(0.08) : Color.clear)
        .pythiaCard()
    }

    // MARK: - Greeks Table

    private func greeksTable(_ r: OptionAnalysisResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Greeks")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            let rows: [(String, String, Double, Double)] = [
                ("Delta", "Δ", r.call.greeks.delta, r.put.greeks.delta),
                ("Gamma", "Γ", r.call.greeks.gamma, r.put.greeks.gamma),
                ("Theta", "Θ", r.call.greeks.theta, r.put.greeks.theta),
                ("Vega", "ν", r.call.greeks.vega, r.put.greeks.vega),
                ("Rho", "ρ", r.call.greeks.rho, r.put.greeks.rho),
            ]

            HStack {
                Text("").frame(width: 100, alignment: .leading)
                Text("Call").frame(maxWidth: .infinity, alignment: .trailing)
                    .foregroundColor(PythiaTheme.profit)
                Text("Put").frame(maxWidth: .infinity, alignment: .trailing)
                    .foregroundColor(PythiaTheme.loss)
            }
            .font(.system(size: 11, weight: .semibold))
            .foregroundColor(PythiaTheme.textTertiary)

            ForEach(rows, id: \.0) { name, symbol, callVal, putVal in
                HStack {
                    HStack(spacing: 4) {
                        Text(symbol)
                            .font(.system(size: 13, weight: .semibold, design: .serif))
                            .foregroundColor(PythiaTheme.accentGold)
                        Text(name)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textPrimary)
                    }
                    .frame(width: 100, alignment: .leading)

                    Text(String(format: "%+.6f", callVal))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                    Text(String(format: "%+.6f", putVal))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                }
                .padding(.vertical, 4)
                Divider().background(PythiaTheme.textTertiary.opacity(0.2))
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Recommended Contract

    private func contractCard(_ c: RecommendedContract, direction: String) -> some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: "doc.text.fill")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Recommended Contract")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(PythiaTheme.accentGold)
                Spacer()
                Text(c.type.uppercased())
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(directionColor(direction))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(directionColor(direction).opacity(0.15))
                    .cornerRadius(6)
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 10) {
                contractMetric("Strike", String(format: "%.2f", c.strike))
                contractMetric("Premium", String(format: "%.4f", c.premium))
                contractMetric("Expiry", expiryLabel(c.expiryYears))
                contractMetric("Break-even", String(format: "%.2f", c.breakeven))
                contractMetric("Profit Target", String(format: "%.2f", c.profitTarget))
                contractMetric("Max Loss", String(format: "%.4f", c.maxLoss))
                contractMetric("Risk/Reward", String(format: "%.1fx", c.riskReward))
                contractMetric("Type", c.strike > (result?.spot ?? 0) ? "OTM" : "ITM")
            }
        }
        .padding(12)
        .background(PythiaTheme.accentGold.opacity(0.06))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(PythiaTheme.accentGold.opacity(0.2), lineWidth: 1)
        )
    }

    private func contractMetric(_ label: String, _ value: String) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(.system(size: 12, weight: .semibold, design: .monospaced))
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    private func expiryLabel(_ years: Double) -> String {
        if years <= 1.0/12 { return "1M" }
        if years <= 0.25 { return "3M" }
        if years <= 0.5 { return "6M" }
        return "1Y"
    }

    // MARK: - Option Payoff & Price Chart

    private struct PayoffPoint: Identifiable {
        let id = UUID()
        let spotPrice: Double
        let value: Double
        let series: String
    }

    private func optionPayoffChart(_ r: OptionAnalysisResponse) -> some View {
        // Generate B-S prices across spot range (±40% from current strike)
        let K = r.strike
        let T = r.timeToExpiry
        let rf = r.riskFreeRate
        let sigma = r.historicalVol
        let spotMin = K * 0.6
        let spotMax = K * 1.4
        let steps = 80

        var points: [PayoffPoint] = []

        for i in 0...steps {
            let s = spotMin + (spotMax - spotMin) * Double(i) / Double(steps)

            // Call payoff at expiry
            let callPayoff = max(s - K, 0) - r.call.price
            points.append(PayoffPoint(spotPrice: s, value: callPayoff, series: "Call Payoff"))

            // Put payoff at expiry
            let putPayoff = max(K - s, 0) - r.put.price
            points.append(PayoffPoint(spotPrice: s, value: putPayoff, series: "Put Payoff"))

            // B-S Call price (current)
            if T > 0 && sigma > 0 {
                let sqrtT = sqrt(T)
                let d1 = (log(s / K) + (rf + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
                let d2 = d1 - sigma * sqrtT
                let nd1 = 0.5 * (1.0 + erf(d1 / sqrt(2.0)))
                let nd2 = 0.5 * (1.0 + erf(d2 / sqrt(2.0)))
                let callPrice = s * nd1 - K * exp(-rf * T) * nd2
                points.append(PayoffPoint(spotPrice: s, value: callPrice - r.call.price, series: "Call Value"))

                // B-S Put price (current)
                let nNegd1 = 1.0 - nd1
                let nNegd2 = 1.0 - nd2
                let putPrice = K * exp(-rf * T) * nNegd2 - s * nNegd1
                points.append(PayoffPoint(spotPrice: s, value: putPrice - r.put.price, series: "Put Value"))
            }
        }

        let allValues = points.map(\.value)
        let yMin = max((allValues.min() ?? -1) * 1.1, -K * 0.3)
        let yMax = min((allValues.max() ?? 1) * 1.1, K * 0.3)

        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "chart.xyaxis.line")
                        .foregroundColor(PythiaTheme.accentGold)
                    Text("Option P&L Diagram")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                Spacer()
                HStack(spacing: 16) {
                    legendItem("Call Payoff", PythiaTheme.profit, dashed: true)
                    legendItem("Call Value", PythiaTheme.profit, dashed: false)
                    legendItem("Put Payoff", PythiaTheme.loss, dashed: true)
                    legendItem("Put Value", PythiaTheme.loss, dashed: false)
                }
            }

            Chart {
                // Zero line
                RuleMark(y: .value("Zero", 0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))

                // Current spot vertical line
                RuleMark(x: .value("Spot", r.spot))
                    .foregroundStyle(PythiaTheme.accentGold.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [6, 4]))
                    .annotation(position: .top, alignment: .center) {
                        Text("Spot")
                            .font(.system(size: 9, weight: .semibold))
                            .foregroundColor(PythiaTheme.accentGold)
                    }

                // Strike vertical line
                RuleMark(x: .value("Strike", K))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
                    .annotation(position: .top, alignment: .center) {
                        Text("K")
                            .font(.system(size: 9, weight: .semibold))
                            .foregroundColor(PythiaTheme.textTertiary)
                    }

                // Call Payoff (dashed)
                ForEach(points.filter { $0.series == "Call Payoff" }) { p in
                    LineMark(
                        x: .value("Spot", p.spotPrice),
                        y: .value("P&L", p.value),
                        series: .value("S", "Call Payoff")
                    )
                    .foregroundStyle(PythiaTheme.profit.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [6, 4]))
                }

                // Call Value (solid)
                ForEach(points.filter { $0.series == "Call Value" }) { p in
                    LineMark(
                        x: .value("Spot", p.spotPrice),
                        y: .value("P&L", p.value),
                        series: .value("S", "Call Value")
                    )
                    .foregroundStyle(PythiaTheme.profit)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                }

                // Put Payoff (dashed)
                ForEach(points.filter { $0.series == "Put Payoff" }) { p in
                    LineMark(
                        x: .value("Spot", p.spotPrice),
                        y: .value("P&L", p.value),
                        series: .value("S", "Put Payoff")
                    )
                    .foregroundStyle(PythiaTheme.loss.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [6, 4]))
                }

                // Put Value (solid)
                ForEach(points.filter { $0.series == "Put Value" }) { p in
                    LineMark(
                        x: .value("Spot", p.spotPrice),
                        y: .value("P&L", p.value),
                        series: .value("S", "Put Value")
                    )
                    .foregroundStyle(PythiaTheme.loss)
                    .lineStyle(StrokeStyle(lineWidth: 2))
                }
            }
            .chartYScale(domain: yMin...yMax)
            .chartLegend(.hidden)
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 8)) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.15))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(String(format: "%.2f", v))
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                }
            }
            .chartYAxis {
                AxisMarks(values: .automatic(desiredCount: 6)) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.15))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(String(format: "%.3f", v))
                                .font(.system(size: 9, design: .monospaced))
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                }
            }
            .frame(height: 280)

            // Breakeven annotation
            HStack(spacing: 20) {
                HStack(spacing: 6) {
                    Circle().fill(PythiaTheme.profit).frame(width: 6, height: 6)
                    Text("Call B/E: \(String(format: "%.4f", K + r.call.price))")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                HStack(spacing: 6) {
                    Circle().fill(PythiaTheme.loss).frame(width: 6, height: 6)
                    Text("Put B/E: \(String(format: "%.4f", K - r.put.price))")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                Spacer()
                Text("Dashed = Payoff at expiry · Solid = Current value (B-S)")
                    .font(.system(size: 9))
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func legendItem(_ label: String, _ color: Color, dashed: Bool) -> some View {
        HStack(spacing: 4) {
            if dashed {
                RoundedRectangle(cornerRadius: 1)
                    .stroke(color.opacity(0.6), style: StrokeStyle(lineWidth: 2, dash: [4, 3]))
                    .frame(width: 14, height: 2)
            } else {
                RoundedRectangle(cornerRadius: 1)
                    .fill(color)
                    .frame(width: 14, height: 2)
            }
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }

    // MARK: - Black-Scholes Model

    private func blackScholesSection(_ r: OptionAnalysisResponse, bs: BSModel) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            // Header
            HStack(spacing: 8) {
                Image(systemName: "function")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Black-Scholes-Merton Model")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("European Options")
                    .font(.system(size: 10))
                    .foregroundColor(PythiaTheme.textTertiary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(PythiaTheme.textTertiary.opacity(0.1))
                    .cornerRadius(4)
            }

            // Formula display
            VStack(alignment: .leading, spacing: 8) {
                Text("C = S·N(d₁) − K·e⁻ʳᵀ·N(d₂)")
                    .font(.system(size: 15, weight: .medium, design: .serif))
                    .foregroundColor(PythiaTheme.profit)
                Text("P = K·e⁻ʳᵀ·N(−d₂) − S·N(−d₁)")
                    .font(.system(size: 15, weight: .medium, design: .serif))
                    .foregroundColor(PythiaTheme.loss)

                Divider().background(PythiaTheme.textTertiary.opacity(0.2))

                HStack(spacing: 0) {
                    Text("d₁ = ")
                        .font(.system(size: 13, design: .serif))
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text("[ln(S/K) + (r + σ²/2)·T]")
                        .font(.system(size: 12, design: .serif))
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(" / ")
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text("σ√T")
                        .font(.system(size: 12, design: .serif))
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                Text("d₂ = d₁ − σ√T")
                    .font(.system(size: 13, design: .serif))
                    .foregroundColor(PythiaTheme.textSecondary)
            }
            .padding(12)
            .background(PythiaTheme.backgroundDark.opacity(0.5))
            .cornerRadius(8)

            // Model Inputs
            VStack(alignment: .leading, spacing: 6) {
                Text("Model Inputs")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(PythiaTheme.textTertiary)

                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 5), spacing: 8) {
                    bsInputCell("S (Spot)", String(format: "%.4f", r.spot))
                    bsInputCell("K (Strike)", String(format: "%.2f", r.strike))
                    bsInputCell("σ (Vol)", String(format: "%.2f%%", r.historicalVol * 100))
                    bsInputCell("r (Rate)", String(format: "%.2f%%", r.riskFreeRate * 100))
                    bsInputCell("T (Years)", String(format: "%.4f", r.timeToExpiry))
                }
            }

            // Computed Values
            VStack(alignment: .leading, spacing: 6) {
                Text("Computed Values")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(PythiaTheme.textTertiary)

                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 8) {
                    bsValueCell("d₁", String(format: "%+.6f", bs.d1), highlight: true)
                    bsValueCell("d₂", String(format: "%+.6f", bs.d2), highlight: true)
                    bsValueCell("N(d₁)", String(format: "%.6f", bs.nD1))
                    bsValueCell("N(d₂)", String(format: "%.6f", bs.nD2))
                    bsValueCell("N(−d₁)", String(format: "%.6f", bs.nNegD1))
                    bsValueCell("N(−d₂)", String(format: "%.6f", bs.nNegD2))
                    bsValueCell("e⁻ʳᵀ", String(format: "%.6f", bs.discountFactor))
                    bsValueCell("Forward", String(format: "%.4f", bs.forwardPrice))
                }
            }

            // Pricing Decomposition
            VStack(alignment: .leading, spacing: 6) {
                Text("Pricing Decomposition")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(PythiaTheme.textTertiary)

                HStack(spacing: 12) {
                    // Call decomposition
                    VStack(alignment: .leading, spacing: 4) {
                        Text("CALL")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(PythiaTheme.profit)
                        bsDecompRow("S × N(d₁)", r.spot * bs.nD1)
                        bsDecompRow("K × e⁻ʳᵀ × N(d₂)", r.strike * bs.discountFactor * bs.nD2, subtract: true)
                        Divider().background(PythiaTheme.profit.opacity(0.3))
                        HStack {
                            Text("= Call Price")
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(PythiaTheme.textSecondary)
                            Spacer()
                            Text(String(format: "%.4f", r.call.price))
                                .font(.system(size: 14, weight: .bold, design: .monospaced))
                                .foregroundColor(PythiaTheme.profit)
                        }
                    }
                    .padding(10)
                    .background(PythiaTheme.profit.opacity(0.05))
                    .cornerRadius(8)

                    // Put decomposition
                    VStack(alignment: .leading, spacing: 4) {
                        Text("PUT")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(PythiaTheme.loss)
                        bsDecompRow("K × e⁻ʳᵀ × N(−d₂)", r.strike * bs.discountFactor * bs.nNegD2)
                        bsDecompRow("S × N(−d₁)", r.spot * bs.nNegD1, subtract: true)
                        Divider().background(PythiaTheme.loss.opacity(0.3))
                        HStack {
                            Text("= Put Price")
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(PythiaTheme.textSecondary)
                            Spacer()
                            Text(String(format: "%.4f", r.put.price))
                                .font(.system(size: 14, weight: .bold, design: .monospaced))
                                .foregroundColor(PythiaTheme.loss)
                        }
                    }
                    .padding(10)
                    .background(PythiaTheme.loss.opacity(0.05))
                    .cornerRadius(8)
                }
            }

            // Put-Call Parity check
            let parityLeft = r.call.price - r.put.price
            let parityRight = r.spot - r.strike * bs.discountFactor
            let parityDiff = abs(parityLeft - parityRight)

            HStack(spacing: 8) {
                Image(systemName: parityDiff < 0.01 ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                    .font(.system(size: 11))
                    .foregroundColor(parityDiff < 0.01 ? PythiaTheme.profit : PythiaTheme.accentGold)
                Text("Put-Call Parity: C − P = S − K·e⁻ʳᵀ")
                    .font(.system(size: 11, design: .serif))
                    .foregroundColor(PythiaTheme.textSecondary)
                Spacer()
                Text(String(format: "%.4f ≈ %.4f", parityLeft, parityRight))
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundColor(parityDiff < 0.01 ? PythiaTheme.profit : PythiaTheme.accentGold)
                Text(parityDiff < 0.01 ? "✓" : String(format: "Δ%.4f", parityDiff))
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(parityDiff < 0.01 ? PythiaTheme.profit : PythiaTheme.accentGold)
            }
            .padding(8)
            .background(PythiaTheme.backgroundDark.opacity(0.5))
            .cornerRadius(6)
        }
        .padding()
        .pythiaCard()
    }

    private func bsInputCell(_ label: String, _ value: String) -> some View {
        VStack(spacing: 3) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(.system(size: 13, weight: .semibold, design: .monospaced))
                .foregroundColor(PythiaTheme.textPrimary)
        }
        .padding(8)
        .background(PythiaTheme.backgroundDark.opacity(0.4))
        .cornerRadius(6)
    }

    private func bsValueCell(_ label: String, _ value: String, highlight: Bool = false) -> some View {
        VStack(spacing: 3) {
            Text(label)
                .font(.system(size: 10, design: .serif))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(.system(size: 12, weight: highlight ? .bold : .medium, design: .monospaced))
                .foregroundColor(highlight ? PythiaTheme.accentGold : PythiaTheme.textPrimary)
        }
        .padding(8)
        .background(highlight ? PythiaTheme.accentGold.opacity(0.06) : PythiaTheme.backgroundDark.opacity(0.4))
        .cornerRadius(6)
    }

    private func bsDecompRow(_ label: String, _ value: Double, subtract: Bool = false) -> some View {
        HStack {
            Text(subtract ? "−" : "+")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundColor(PythiaTheme.textTertiary)
                .frame(width: 10)
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(PythiaTheme.textSecondary)
                .lineLimit(1)
            Spacer()
            Text(String(format: "%.4f", value))
                .font(.system(size: 11, design: .monospaced))
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    // MARK: - Helpers

    private func metricRow(_ label: String, _ value: String) -> some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(PythiaTheme.monospace())
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    private func pricingMetric(_ label: String, _ value: Double) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(String(format: "%.4f", value))
                .font(PythiaTheme.monospace())
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    private func directionColor(_ d: String) -> Color {
        switch d {
        case "call": return PythiaTheme.profit
        case "put": return PythiaTheme.loss
        default: return PythiaTheme.textSecondary
        }
    }

    private func confidenceColor(_ c: String) -> Color {
        switch c {
        case "high": return PythiaTheme.profit
        case "medium": return PythiaTheme.accentGold
        default: return PythiaTheme.textTertiary
        }
    }

    private func signalColor(_ s: String) -> Color {
        switch s {
        case "bullish": return PythiaTheme.profit
        case "bearish": return PythiaTheme.loss
        default: return PythiaTheme.textTertiary
        }
    }

    private func analyze() async {
        guard let aid = selectedAssetId else { return }
        let strike = Double(strikeStr) ?? 0
        isLoading = true; errorMessage = nil; result = nil
        do {
            result = try await db.analyzeOption(assetId: aid, strike: strike, expiry: selectedExpiry)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
