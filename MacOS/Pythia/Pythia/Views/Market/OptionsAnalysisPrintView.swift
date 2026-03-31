//
//  OptionsAnalysisPrintView.swift
//  Pythia — Light-themed printable view for Options Analysis PDF export
//

import SwiftUI
import Charts

struct OptionsAnalysisPrintView: View {
    let result: OptionAnalysisResponse

    private let L = PythiaTheme.Light.self
    private let profitColor = Color(hex: "16A34A")
    private let lossColor = Color(hex: "DC2626")
    private let goldColor = Color(hex: "D97706")
    private let blueColor = Color(hex: "2563EB")

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            header
            quoteSection
            suggestionSection
            pricingSection
            greeksSection
            payoffChart
            if let bs = result.bsModel {
                bsModelSection(bs)
            }
            footer
        }
        .padding(24)
        .frame(width: 700)
        .background(L.background)
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Pythia — Options Analysis Report")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(L.textPrimary)
                Text("\(result.symbol) · Strike \(fmt2(result.strike)) · \(expiryLabel(result.timeToExpiry))")
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

    // MARK: - Quote

    private var quoteSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(result.symbol)
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(L.textPrimary)
                Text(result.quote.name)
                    .font(.system(size: 11))
                    .foregroundColor(L.textSecondary)
            }
            Spacer()
            Text(fmt4(result.spot))
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(L.textPrimary)
            Divider().frame(height: 30).padding(.horizontal, 8)
            VStack(alignment: .leading, spacing: 3) {
                kv("Hist Vol", String(format: "%.1f%%", result.historicalVol * 100))
                kv("Risk-Free", String(format: "%.2f%%", result.riskFreeRate * 100))
                kv("Expiry", String(format: "%.2f yr", result.timeToExpiry))
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Suggestion

    private var suggestionSection: some View {
        let s = result.suggestion
        let dirColor = s.direction == "call" ? profitColor : (s.direction == "put" ? lossColor : goldColor)

        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Text(s.direction.uppercased())
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(dirColor)
                Text(s.confidence.capitalized)
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(dirColor)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(dirColor.opacity(0.12))
                    .cornerRadius(4)
                Spacer()
            }
            Text(s.summary)
                .font(.system(size: 11))
                .foregroundColor(L.textSecondary)

            // Recommended contract
            if let c = s.contract {
                HStack(spacing: 10) {
                    contractKV("Strike", fmt2(c.strike))
                    contractKV("Premium", fmt4(c.premium))
                    contractKV("Expiry", expiryLabel(c.expiryYears))
                    contractKV("B/E", fmt4(c.breakeven))
                    contractKV("Max Loss", fmt4(c.maxLoss))
                    contractKV("R/R", String(format: "%.1fx", c.riskReward))
                }
                .padding(8)
                .background(goldColor.opacity(0.05))
                .cornerRadius(6)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(goldColor.opacity(0.3), lineWidth: 1))
            }

            // Signals
            ForEach(s.signals) { sig in
                HStack(spacing: 6) {
                    Circle()
                        .fill(sig.signal == "bullish" ? profitColor : (sig.signal == "bearish" ? lossColor : L.textTertiary))
                        .frame(width: 7, height: 7)
                    Text(sig.name)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(L.textPrimary)
                        .frame(width: 90, alignment: .leading)
                    Text(sig.value.displayString)
                        .font(.system(size: 10, weight: .semibold, design: .monospaced))
                        .foregroundColor(sig.signal == "bullish" ? profitColor : (sig.signal == "bearish" ? lossColor : L.textSecondary))
                        .frame(width: 70, alignment: .trailing)
                    Text(sig.detail)
                        .font(.system(size: 9))
                        .foregroundColor(L.textTertiary)
                        .lineLimit(1)
                    Spacer()
                }
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Pricing

    private var pricingSection: some View {
        HStack(spacing: 10) {
            priceSide("CALL", side: result.call, color: profitColor,
                      recommended: result.suggestion.direction == "call")
            priceSide("PUT", side: result.put, color: lossColor,
                      recommended: result.suggestion.direction == "put")
        }
    }

    private func priceSide(_ label: String, side: OptionSide, color: Color, recommended: Bool) -> some View {
        VStack(spacing: 8) {
            HStack {
                if recommended {
                    Image(systemName: "star.fill").font(.system(size: 10)).foregroundColor(goldColor)
                }
                Text(label).font(.system(size: 12, weight: .bold)).foregroundColor(color)
                Spacer()
            }
            Text(fmt4(side.price))
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundColor(L.textPrimary)
            HStack(spacing: 16) {
                VStack(spacing: 2) {
                    Text("Intrinsic").font(.system(size: 9)).foregroundColor(L.textTertiary)
                    Text(fmt4(side.intrinsicValue)).font(.system(size: 11, design: .monospaced)).foregroundColor(L.textPrimary)
                }
                VStack(spacing: 2) {
                    Text("Time Value").font(.system(size: 9)).foregroundColor(L.textTertiary)
                    Text(fmt4(side.timeValue)).font(.system(size: 11, design: .monospaced)).foregroundColor(L.textPrimary)
                }
            }
        }
        .padding(10)
        .background(recommended ? color.opacity(0.05) : L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(recommended ? color.opacity(0.3) : L.cardBorder, lineWidth: 1))
    }

    // MARK: - Greeks

    private var greeksSection: some View {
        let rows: [(String, String, Double, Double)] = [
            ("Delta", "Δ", result.call.greeks.delta, result.put.greeks.delta),
            ("Gamma", "Γ", result.call.greeks.gamma, result.put.greeks.gamma),
            ("Theta", "Θ", result.call.greeks.theta, result.put.greeks.theta),
            ("Vega", "ν", result.call.greeks.vega, result.put.greeks.vega),
            ("Rho", "ρ", result.call.greeks.rho, result.put.greeks.rho),
        ]

        return VStack(alignment: .leading, spacing: 6) {
            Text("Greeks")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(L.textPrimary)

            HStack {
                Text("").frame(width: 80, alignment: .leading)
                Text("Call").frame(maxWidth: .infinity, alignment: .trailing)
                    .font(.system(size: 10, weight: .semibold)).foregroundColor(profitColor)
                Text("Put").frame(maxWidth: .infinity, alignment: .trailing)
                    .font(.system(size: 10, weight: .semibold)).foregroundColor(lossColor)
            }

            ForEach(rows, id: \.0) { name, symbol, callVal, putVal in
                HStack {
                    HStack(spacing: 3) {
                        Text(symbol).font(.system(size: 12, weight: .semibold, design: .serif)).foregroundColor(goldColor)
                        Text(name).font(.system(size: 11)).foregroundColor(L.textPrimary)
                    }
                    .frame(width: 80, alignment: .leading)
                    Text(String(format: "%+.6f", callVal))
                        .font(.system(size: 10, design: .monospaced)).foregroundColor(L.textPrimary)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                    Text(String(format: "%+.6f", putVal))
                        .font(.system(size: 10, design: .monospaced)).foregroundColor(L.textPrimary)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                }
                .padding(.vertical, 2)
                if name != "Rho" {
                    Divider().background(L.cardBorder)
                }
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Payoff Chart

    private struct PayoffPt: Identifiable {
        let id = UUID()
        let s: Double
        let v: Double
        let series: String
    }

    private var payoffChart: some View {
        let K = result.strike
        let T = result.timeToExpiry
        let rf = result.riskFreeRate
        let sigma = result.historicalVol

        var pts: [PayoffPt] = []
        let steps = 60
        let sMin = K * 0.65, sMax = K * 1.35

        for i in 0...steps {
            let s = sMin + (sMax - sMin) * Double(i) / Double(steps)

            // Payoff at expiry
            pts.append(PayoffPt(s: s, v: max(s - K, 0) - result.call.price, series: "Call Payoff"))
            pts.append(PayoffPt(s: s, v: max(K - s, 0) - result.put.price, series: "Put Payoff"))

            // B-S current value
            if T > 0 && sigma > 0 {
                let sqrtT = sqrt(T)
                let d1 = (log(s / K) + (rf + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
                let d2 = d1 - sigma * sqrtT
                let nd1 = 0.5 * (1.0 + erf(d1 / sqrt(2.0)))
                let nd2 = 0.5 * (1.0 + erf(d2 / sqrt(2.0)))
                let callP = s * nd1 - K * exp(-rf * T) * nd2
                let putP = K * exp(-rf * T) * (1 - nd2) - s * (1 - nd1)
                pts.append(PayoffPt(s: s, v: callP - result.call.price, series: "Call Value"))
                pts.append(PayoffPt(s: s, v: putP - result.put.price, series: "Put Value"))
            }
        }

        let vals = pts.map(\.v)
        let yMin = max((vals.min() ?? -1) * 1.1, -K * 0.25)
        let yMax = min((vals.max() ?? 1) * 1.1, K * 0.25)

        return VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Option P&L Diagram")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
                Spacer()
                HStack(spacing: 12) {
                    pLegend("Call Payoff", profitColor, dash: true)
                    pLegend("Call Value", profitColor, dash: false)
                    pLegend("Put Payoff", lossColor, dash: true)
                    pLegend("Put Value", lossColor, dash: false)
                }
            }

            Chart {
                RuleMark(y: .value("", 0))
                    .foregroundStyle(L.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
                RuleMark(x: .value("Spot", result.spot))
                    .foregroundStyle(goldColor.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [5, 3]))
                RuleMark(x: .value("K", K))
                    .foregroundStyle(L.textTertiary.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))

                ForEach(pts.filter { $0.series == "Call Payoff" }) { p in
                    LineMark(x: .value("S", p.s), y: .value("PL", p.v), series: .value("", "CP"))
                        .foregroundStyle(profitColor.opacity(0.5))
                        .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [5, 3]))
                }
                ForEach(pts.filter { $0.series == "Call Value" }) { p in
                    LineMark(x: .value("S", p.s), y: .value("PL", p.v), series: .value("", "CV"))
                        .foregroundStyle(profitColor)
                        .lineStyle(StrokeStyle(lineWidth: 2))
                }
                ForEach(pts.filter { $0.series == "Put Payoff" }) { p in
                    LineMark(x: .value("S", p.s), y: .value("PL", p.v), series: .value("", "PP"))
                        .foregroundStyle(lossColor.opacity(0.5))
                        .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [5, 3]))
                }
                ForEach(pts.filter { $0.series == "Put Value" }) { p in
                    LineMark(x: .value("S", p.s), y: .value("PL", p.v), series: .value("", "PV"))
                        .foregroundStyle(lossColor)
                        .lineStyle(StrokeStyle(lineWidth: 2))
                }
            }
            .chartYScale(domain: yMin...yMax)
            .chartLegend(.hidden)
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 7)) { val in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(L.textTertiary.opacity(0.2))
                    AxisValueLabel {
                        if let v = val.as(Double.self) {
                            Text(String(format: "%.2f", v)).font(.system(size: 8, design: .monospaced)).foregroundColor(L.textSecondary)
                        }
                    }
                }
            }
            .chartYAxis {
                AxisMarks(values: .automatic(desiredCount: 5)) { val in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(L.textTertiary.opacity(0.2))
                    AxisValueLabel {
                        if let v = val.as(Double.self) {
                            Text(String(format: "%.3f", v)).font(.system(size: 8, design: .monospaced)).foregroundColor(L.textSecondary)
                        }
                    }
                }
            }
            .frame(height: 220)

            HStack(spacing: 16) {
                Text("Call B/E: \(fmt4(K + result.call.price))")
                    .font(.system(size: 9, design: .monospaced)).foregroundColor(profitColor)
                Text("Put B/E: \(fmt4(K - result.put.price))")
                    .font(.system(size: 9, design: .monospaced)).foregroundColor(lossColor)
                Spacer()
                Text("Dashed = expiry payoff · Solid = B-S value")
                    .font(.system(size: 8)).foregroundColor(L.textTertiary)
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - B-S Model

    private func bsModelSection(_ bs: BSModel) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Text("f(x)")
                    .font(.system(size: 12, weight: .bold, design: .serif))
                    .foregroundColor(goldColor)
                Text("Black-Scholes-Merton Model")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
            }

            // Formulas
            VStack(alignment: .leading, spacing: 4) {
                Text("C = S·N(d₁) − K·e⁻ʳᵀ·N(d₂)")
                    .font(.system(size: 13, weight: .medium, design: .serif))
                    .foregroundColor(profitColor)
                Text("P = K·e⁻ʳᵀ·N(−d₂) − S·N(−d₁)")
                    .font(.system(size: 13, weight: .medium, design: .serif))
                    .foregroundColor(lossColor)
            }
            .padding(8)
            .background(L.cardBorder.opacity(0.3))
            .cornerRadius(6)

            // Inputs + computed
            HStack(spacing: 8) {
                bsCell("S", fmt4(result.spot))
                bsCell("K", fmt2(result.strike))
                bsCell("σ", String(format: "%.2f%%", result.historicalVol * 100))
                bsCell("r", String(format: "%.2f%%", result.riskFreeRate * 100))
                bsCell("T", String(format: "%.4f", result.timeToExpiry))
            }

            HStack(spacing: 8) {
                bsCell("d₁", String(format: "%+.6f", bs.d1), gold: true)
                bsCell("d₂", String(format: "%+.6f", bs.d2), gold: true)
                bsCell("N(d₁)", String(format: "%.6f", bs.nD1))
                bsCell("N(d₂)", String(format: "%.6f", bs.nD2))
                bsCell("e⁻ʳᵀ", String(format: "%.6f", bs.discountFactor))
            }

            // Put-Call Parity
            let pLeft = result.call.price - result.put.price
            let pRight = result.spot - result.strike * bs.discountFactor
            HStack(spacing: 6) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 10)).foregroundColor(profitColor)
                Text("Put-Call Parity: C − P = S − K·e⁻ʳᵀ")
                    .font(.system(size: 10, design: .serif)).foregroundColor(L.textSecondary)
                Spacer()
                Text(String(format: "%.4f ≈ %.4f ✓", pLeft, pRight))
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .foregroundColor(profitColor)
            }
            .padding(6)
            .background(L.cardBorder.opacity(0.3))
            .cornerRadius(4)
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Footer

    private var footer: some View {
        HStack {
            Text("Pythia Quantitative Finance Platform")
                .font(.system(size: 9)).foregroundColor(L.textTertiary)
            Spacer()
            Text("This is not investment advice. Past performance does not guarantee future results.")
                .font(.system(size: 8)).foregroundColor(L.textTertiary)
        }
        .padding(.top, 4)
    }

    // MARK: - Helpers

    private func kv(_ label: String, _ value: String) -> some View {
        HStack(spacing: 4) {
            Text(label).font(.system(size: 9)).foregroundColor(L.textTertiary)
            Text(value).font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundColor(L.textPrimary)
        }
    }

    private func contractKV(_ label: String, _ value: String) -> some View {
        VStack(spacing: 2) {
            Text(label).font(.system(size: 8)).foregroundColor(L.textTertiary)
            Text(value).font(.system(size: 10, weight: .semibold, design: .monospaced)).foregroundColor(L.textPrimary)
        }
        .frame(maxWidth: .infinity)
    }

    private func bsCell(_ label: String, _ value: String, gold: Bool = false) -> some View {
        VStack(spacing: 2) {
            Text(label).font(.system(size: 9, design: .serif)).foregroundColor(L.textTertiary)
            Text(value)
                .font(.system(size: 10, weight: gold ? .bold : .medium, design: .monospaced))
                .foregroundColor(gold ? Color(hex: "B45309") : L.textPrimary)
        }
        .frame(maxWidth: .infinity)
        .padding(6)
        .background(gold ? Color(hex: "FEF3C7") : L.cardBorder.opacity(0.2))
        .cornerRadius(4)
    }

    private func pLegend(_ label: String, _ color: Color, dash: Bool) -> some View {
        HStack(spacing: 3) {
            if dash {
                RoundedRectangle(cornerRadius: 1)
                    .stroke(color.opacity(0.6), style: StrokeStyle(lineWidth: 2, dash: [4, 2]))
                    .frame(width: 12, height: 2)
            } else {
                RoundedRectangle(cornerRadius: 1).fill(color).frame(width: 12, height: 2)
            }
            Text(label).font(.system(size: 8)).foregroundColor(L.textSecondary)
        }
    }

    private func fmt2(_ v: Double) -> String { String(format: "%.2f", v) }
    private func fmt4(_ v: Double) -> String { String(format: "%.4f", v) }

    private func expiryLabel(_ years: Double) -> String {
        if years <= 1.0/12 { return "1M" }
        if years <= 0.25 { return "3M" }
        if years <= 0.5 { return "6M" }
        return "1Y"
    }
}
