//
//  OptionsChainView.swift
//  Pythia — Options Analysis with AI Suggestion
//

import SwiftUI

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
