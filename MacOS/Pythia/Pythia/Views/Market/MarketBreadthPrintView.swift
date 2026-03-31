//
//  MarketBreadthPrintView.swift
//  Pythia — Light-themed printable view for Market Breadth PDF export
//

import SwiftUI
import Charts

struct MarketBreadthPrintView: View {
    let breadth: BreadthResponse
    let universe: String
    let universeName: String

    private let L = PythiaTheme.Light.self
    private let profitColor = Color(hex: "16A34A")
    private let lossColor = Color(hex: "DC2626")
    private let blueColor = Color(hex: "2563EB")
    private let goldColor = Color(hex: "D97706")

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            header
            regimeSection
            summaryCards
            marketSummarySection
            adLineChart
            pctAboveMAChart
            mcclEllanChart
            newHighsLowsChart
            trinChart
            if !breadth.current.divergences.isEmpty {
                divergenceSection
            }
            conclusionSection
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
                Text("Pythia — Market Breadth Report")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(L.textPrimary)
                Text("\(universeName) · \(breadth.universeSize) stocks · \(breadth.period ?? "1Y")")
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

    // MARK: - Regime

    private var regimeSection: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(regimeColor(breadth.current.regime))
                .frame(width: 10, height: 10)
            Text("Market Regime:")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(L.textPrimary)
            Text(breadth.current.regime.replacingOccurrences(of: "_", with: " ").uppercased())
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(regimeColor(breadth.current.regime))
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(regimeColor(breadth.current.regime).opacity(0.12))
                .cornerRadius(6)
            Spacer()
        }
        .padding(10)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Summary Cards

    private var summaryCards: some View {
        let c = breadth.current
        return HStack(spacing: 10) {
            printKPI(title: "A/D Ratio", value: fmtVal(c.adRatio, d: 2),
                     color: (c.adRatio ?? 1) > 1 ? profitColor : lossColor)
            printKPI(title: "% > 200MA", value: fmtPct(c.pctAbove200ma),
                     color: (c.pctAbove200ma ?? 50) > 50 ? profitColor : lossColor)
            printKPI(title: "McClellan Osc", value: fmtVal(c.mcclEllanOscillator, d: 1),
                     color: (c.mcclEllanOscillator ?? 0) > 0 ? profitColor : lossColor)
            printKPI(title: "TRIN (10d)", value: fmtVal(c.trin, d: 2),
                     color: (c.trin ?? 1) < 1 ? profitColor : lossColor)
        }
    }

    private func printKPI(title: String, value: String, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 10))
                .foregroundColor(L.textSecondary)
            Text(value)
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Market Summary

    private var marketSummarySection: some View {
        let c = breadth.current
        let adRatio = c.adRatio ?? 1.0
        let pctAbove200 = c.pctAbove200ma ?? 50.0
        let mcclellan = c.mcclEllanOscillator ?? 0.0
        let trin = c.trin ?? 1.0

        var bullCount = 0
        var bearCount = 0
        if adRatio > 1.0 { bullCount += 1 } else { bearCount += 1 }
        if pctAbove200 > 50 { bullCount += 1 } else { bearCount += 1 }
        if mcclellan > 0 { bullCount += 1 } else { bearCount += 1 }
        if trin < 1.0 { bullCount += 1 } else { bearCount += 1 }

        let verdict = regimeVerdict(c.regime, bullCount: bullCount, bearCount: bearCount)
        let summaryColor = bullCount >= 3 ? profitColor : (bearCount >= 3 ? lossColor : goldColor)

        let bullets: [(String, Bool)] = [
            (adInterpretation(adRatio), adRatio > 1.0),
            (maInterpretation(pctAbove200), pctAbove200 > 50),
            (mccInterpretation(mcclellan), mcclellan > 0),
            (trinInterpretation(trin), trin < 1.0),
        ]

        return VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: "chart.bar.doc.horizontal.fill")
                    .foregroundColor(summaryColor)
                    .font(.system(size: 13))
                Text("สรุปภาพรวมตลาด")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
                Spacer()
                Text("Bullish \(bullCount) / Bearish \(bearCount)")
                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
                    .foregroundColor(summaryColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(summaryColor.opacity(0.1))
                    .cornerRadius(6)
            }

            Text(verdict)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(L.textPrimary)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(summaryColor.opacity(0.06))
                .cornerRadius(6)

            ForEach(Array(bullets.enumerated()), id: \.offset) { _, item in
                HStack(alignment: .top, spacing: 6) {
                    Image(systemName: item.1 ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                        .font(.system(size: 10))
                        .foregroundColor(item.1 ? profitColor : lossColor)
                        .padding(.top, 2)
                    Text(item.0)
                        .font(.system(size: 11))
                        .foregroundColor(L.textPrimary)
                }
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - A/D Line Chart

    private var adLineChart: some View {
        let data = buildChartData(values: breadth.indicators.adLine)

        return chartCard(title: "Advance/Decline Line") {
            Chart(data) { p in
                AreaMark(x: .value("Date", p.date), y: .value("A/D", p.value))
                    .foregroundStyle(
                        LinearGradient(colors: [blueColor.opacity(0.15), blueColor.opacity(0.02)],
                                       startPoint: .top, endPoint: .bottom)
                    )
                LineMark(x: .value("Date", p.date), y: .value("A/D", p.value))
                    .foregroundStyle(blueColor)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))
            }
            .printChartAxes()
            .frame(height: 180)
        }
    }

    // MARK: - % Above MA Chart

    private var pctAboveMAChart: some View {
        let data50 = buildChartData(values: breadth.indicators.pctAbove50ma, series: "50d MA")
        let data200 = buildChartData(values: breadth.indicators.pctAbove200ma, series: "200d MA")
        let allData = data50 + data200

        return chartCard(title: "% Above Moving Average", legend: [("50d", blueColor), ("200d", goldColor)]) {
            Chart(allData) { p in
                AreaMark(x: .value("Date", p.date), y: .value("%", p.value))
                    .foregroundStyle(by: .value("S", p.series))
                    .opacity(0.08)
                LineMark(x: .value("Date", p.date), y: .value("%", p.value))
                    .foregroundStyle(by: .value("S", p.series))
                    .lineStyle(StrokeStyle(lineWidth: 1.5))
                RuleMark(y: .value("", 30))
                    .foregroundStyle(lossColor.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 50))
                    .foregroundStyle(L.textTertiary.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 70))
                    .foregroundStyle(profitColor.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
            }
            .chartForegroundStyleScale(["50d MA": blueColor, "200d MA": goldColor])
            .chartYScale(domain: 0...100)
            .printChartAxes()
            .frame(height: 180)
        }
    }

    // MARK: - McClellan Oscillator

    private var mcclEllanChart: some View {
        let data = buildChartData(values: breadth.indicators.mcclEllanOscillator)

        return chartCard(title: "McClellan Oscillator") {
            Chart(data) { p in
                BarMark(x: .value("Date", p.date), y: .value("Val", p.value))
                    .foregroundStyle(p.value >= 0 ? profitColor : lossColor)
                RuleMark(y: .value("", 0))
                    .foregroundStyle(L.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .printChartAxes()
            .frame(height: 160)
        }
    }

    // MARK: - New Highs vs Lows

    private var newHighsLowsChart: some View {
        let highs = buildChartData(values: breadth.indicators.newHighs, series: "New Highs")
        let lows = buildChartData(values: breadth.indicators.newLows.map { v in v.map { -$0 } }, series: "New Lows")
        let allData = highs + lows

        return chartCard(title: "New 52-Week Highs vs Lows", legend: [("Highs", profitColor), ("Lows", lossColor)]) {
            Chart(allData) { p in
                BarMark(x: .value("Date", p.date), y: .value("Count", p.value))
                    .foregroundStyle(by: .value("S", p.series))
                RuleMark(y: .value("", 0))
                    .foregroundStyle(L.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .chartForegroundStyleScale(["New Highs": profitColor, "New Lows": lossColor])
            .printChartAxes()
            .frame(height: 160)
        }
    }

    // MARK: - TRIN Chart

    private var trinChart: some View {
        let data = buildChartData(values: breadth.indicators.trin10dAvg)

        return chartCard(title: "TRIN (Arms Index) — 10d Avg") {
            Chart(data) { p in
                LineMark(x: .value("Date", p.date), y: .value("TRIN", p.value))
                    .foregroundStyle(goldColor)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))
                RuleMark(y: .value("", 0.75))
                    .foregroundStyle(profitColor.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 1.0))
                    .foregroundStyle(L.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 1.25))
                    .foregroundStyle(lossColor.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
            }
            .printChartAxes()
            .frame(height: 160)
        }
    }

    // MARK: - Divergence

    private var divergenceSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(goldColor)
                    .font(.system(size: 13))
                Text("Divergence Alerts")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
            }
            ForEach(breadth.current.divergences, id: \.self) { msg in
                HStack(alignment: .top, spacing: 6) {
                    Text("•").foregroundColor(goldColor)
                    Text(msg)
                        .font(.system(size: 11))
                        .foregroundColor(L.textPrimary)
                }
            }
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(goldColor.opacity(0.4), lineWidth: 1))
    }

    // MARK: - Conclusion

    private var conclusionSection: some View {
        let c = breadth.current
        let adRatio = c.adRatio ?? 1.0
        let pctAbove200 = c.pctAbove200ma ?? 50.0
        let pctAbove50 = c.pctAbove50ma ?? 50.0
        let mcclellan = c.mcclEllanOscillator ?? 0.0
        let trin = c.trin ?? 1.0
        let regime = c.regime

        // Score
        var bullCount = 0
        var bearCount = 0
        if adRatio > 1.0 { bullCount += 1 } else { bearCount += 1 }
        if pctAbove200 > 50 { bullCount += 1 } else { bearCount += 1 }
        if mcclellan > 0 { bullCount += 1 } else { bearCount += 1 }
        if trin < 1.0 { bullCount += 1 } else { bearCount += 1 }

        // Breadth Score 0-100
        let breadthScore = min(100, max(0, Int(
            (min(adRatio, 3.0) / 3.0 * 25) +
            (pctAbove200 / 100.0 * 25) +
            (min(max(mcclellan + 100, 0), 200) / 200.0 * 25) +
            ((2.0 - min(trin, 2.0)) / 2.0 * 25)
        )))

        let scoreLabel: String = {
            if breadthScore >= 75 { return "Strong" }
            if breadthScore >= 55 { return "Moderate" }
            if breadthScore >= 35 { return "Weak" }
            return "Very Weak"
        }()

        let scoreColor: Color = {
            if breadthScore >= 75 { return profitColor }
            if breadthScore >= 55 { return Color(hex: "CA8A04") }
            if breadthScore >= 35 { return goldColor }
            return lossColor
        }()

        // Strategy suggestion
        let strategy: String = {
            switch regime {
            case "strong_bull":
                return "กลยุทธ์: Trend Following — เพิ่มสัดส่วนหุ้น, เน้น momentum stocks ที่ทำ New High, ใช้ trailing stop แทน fixed stop"
            case "bull":
                return "กลยุทธ์: Selective Long — เลือกหุ้นที่ยืนเหนือ 200MA และมี volume สนับสนุน, เริ่มระวัง divergence ใน A/D Line"
            case "neutral":
                if bullCount > bearCount {
                    return "กลยุทธ์: Cautious Long — ตลาดมีสัญญาณฟื้นตัว แต่ยังไม่ยืนยัน ควร position size เล็กลง, เน้น sector ที่ breadth แข็งแกร่ง"
                } else {
                    return "กลยุทธ์: Wait & See — สัญญาณผสม ลด position size, ถือ cash สัดส่วนมากขึ้น, รอ McClellan Oscillator กลับเป็นบวกก่อนเข้า"
                }
            case "bear":
                return "กลยุทธ์: Defensive — ลดสัดส่วนหุ้นลง, เน้น defensive sectors, พิจารณา inverse ETF หรือ hedge ด้วย options"
            case "strong_bear":
                return "กลยุทธ์: Capital Preservation — ถือ cash สัดส่วนสูง, หลีกเลี่ยงการ bottom-fishing จนกว่า breadth จะเริ่มฟื้น (McClellan > 0 + A/D Ratio > 1)"
            default:
                return "กลยุทธ์: รอข้อมูลเพิ่มเติม"
            }
        }()

        // Key observations
        var observations: [String] = []

        // A/D Line trend
        if let adLine = breadth.indicators.adLine.compactMap({ $0 }).suffix(20).first,
           let adLineLast = breadth.indicators.adLine.compactMap({ $0 }).last {
            if adLineLast > adLine {
                observations.append("A/D Line มีแนวโน้มขาขึ้นใน 20 วันล่าสุด — หุ้นที่มีส่วนร่วมเพิ่มขึ้น")
            } else {
                observations.append("A/D Line มีแนวโน้มขาลงใน 20 วันล่าสุด — หุ้นที่มีส่วนร่วมลดลง")
            }
        }

        // MA breadth gap
        if pctAbove50 > pctAbove200 + 15 {
            observations.append("% Above 50MA สูงกว่า 200MA มาก — short-term momentum แข็ง แต่อาจ overbought ระยะสั้น")
        } else if pctAbove200 > pctAbove50 + 10 {
            observations.append("% Above 200MA สูงกว่า 50MA — long-term trend ยังดี แต่ short-term momentum อ่อนตัว")
        }

        // TRIN extreme
        if trin < 0.6 {
            observations.append("TRIN ต่ำผิดปกติ (< 0.6) — อาจเป็น short-term overbought signal ระวัง pullback")
        } else if trin > 1.5 {
            observations.append("TRIN สูงผิดปกติ (> 1.5) — oversold extreme อาจเป็นจุด reversal ที่ดี")
        }

        // Divergences
        if !c.divergences.isEmpty {
            observations.append("พบ Divergence \(c.divergences.count) รายการ — สัญญาณเตือนว่าแนวโน้มปัจจุบันอาจอ่อนกำลังลง")
        }

        if observations.isEmpty {
            observations.append("ไม่พบสัญญาณผิดปกติ — breadth สอดคล้องกับทิศทางตลาด")
        }

        return VStack(alignment: .leading, spacing: 12) {
            // Title + Score
            HStack(spacing: 10) {
                Image(systemName: "checkmark.seal.fill")
                    .foregroundColor(scoreColor)
                    .font(.system(size: 15))
                Text("สรุปและข้อเสนอแนะ")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(L.textPrimary)
                Spacer()
                VStack(alignment: .trailing, spacing: 2) {
                    Text("Breadth Score")
                        .font(.system(size: 9))
                        .foregroundColor(L.textTertiary)
                    HStack(spacing: 4) {
                        Text("\(breadthScore)")
                            .font(.system(size: 20, weight: .bold, design: .rounded))
                            .foregroundColor(scoreColor)
                        Text("/ 100")
                            .font(.system(size: 11))
                            .foregroundColor(L.textTertiary)
                        Text(scoreLabel)
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(scoreColor)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(scoreColor.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }

            // Score bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(L.cardBorder)
                        .frame(height: 8)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(LinearGradient(
                            colors: [lossColor, goldColor, profitColor],
                            startPoint: .leading, endPoint: .trailing
                        ))
                        .frame(width: geo.size.width * CGFloat(breadthScore) / 100, height: 8)
                }
            }
            .frame(height: 8)

            // Indicator summary table
            VStack(spacing: 0) {
                conclusionRow(indicator: "A/D Ratio", value: String(format: "%.2f", adRatio),
                             signal: adRatio > 1.5 ? "Strong Bullish" : adRatio > 1.0 ? "Bullish" : adRatio > 0.7 ? "Bearish" : "Strong Bearish",
                             isBullish: adRatio > 1.0)
                Divider().background(L.cardBorder)
                conclusionRow(indicator: "% Above 200MA", value: String(format: "%.1f%%", pctAbove200),
                             signal: pctAbove200 > 70 ? "Strong Bullish" : pctAbove200 > 50 ? "Bullish" : pctAbove200 > 30 ? "Bearish" : "Strong Bearish",
                             isBullish: pctAbove200 > 50)
                Divider().background(L.cardBorder)
                conclusionRow(indicator: "McClellan Osc", value: String(format: "%.1f", mcclellan),
                             signal: mcclellan > 50 ? "Strong Bullish" : mcclellan > 0 ? "Bullish" : mcclellan > -50 ? "Bearish" : "Strong Bearish",
                             isBullish: mcclellan > 0)
                Divider().background(L.cardBorder)
                conclusionRow(indicator: "TRIN (10d)", value: String(format: "%.2f", trin),
                             signal: trin < 0.75 ? "Strong Bullish" : trin < 1.0 ? "Bullish" : trin < 1.25 ? "Bearish" : "Strong Bearish",
                             isBullish: trin < 1.0)
            }
            .background(L.cardBackground)
            .cornerRadius(6)
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(L.cardBorder, lineWidth: 1))

            // Strategy
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 6) {
                    Image(systemName: "lightbulb.fill")
                        .foregroundColor(goldColor)
                        .font(.system(size: 11))
                    Text("Strategy")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(L.textPrimary)
                }
                Text(strategy)
                    .font(.system(size: 11))
                    .foregroundColor(L.textPrimary)
                    .lineSpacing(3)
            }
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(goldColor.opacity(0.05))
            .cornerRadius(6)
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(goldColor.opacity(0.3), lineWidth: 1))

            // Key observations
            if !observations.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Key Observations")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(L.textPrimary)
                    ForEach(Array(observations.enumerated()), id: \.offset) { _, obs in
                        HStack(alignment: .top, spacing: 6) {
                            Text("•").foregroundColor(blueColor)
                            Text(obs)
                                .font(.system(size: 10))
                                .foregroundColor(L.textPrimary)
                        }
                    }
                }
            }
        }
        .padding(14)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(scoreColor.opacity(0.4), lineWidth: 1.5))
    }

    private func conclusionRow(indicator: String, value: String, signal: String, isBullish: Bool) -> some View {
        HStack {
            Text(indicator)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(L.textSecondary)
                .frame(width: 110, alignment: .leading)
            Text(value)
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundColor(L.textPrimary)
                .frame(width: 80, alignment: .trailing)
            Spacer()
            HStack(spacing: 4) {
                Image(systemName: isBullish ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                    .font(.system(size: 9))
                    .foregroundColor(isBullish ? profitColor : lossColor)
                Text(signal)
                    .font(.system(size: 9, weight: .semibold))
                    .foregroundColor(isBullish ? profitColor : lossColor)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background((isBullish ? profitColor : lossColor).opacity(0.08))
            .cornerRadius(4)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
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

    // MARK: - Chart Card Builder

    private func chartCard<C: View>(
        title: String,
        legend: [(String, Color)] = [],
        @ViewBuilder chart: () -> C
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(L.textPrimary)
                Spacer()
                if !legend.isEmpty {
                    HStack(spacing: 10) {
                        ForEach(legend, id: \.0) { item in
                            HStack(spacing: 4) {
                                Circle().fill(item.1).frame(width: 7, height: 7)
                                Text(item.0)
                                    .font(.system(size: 9))
                                    .foregroundColor(L.textSecondary)
                            }
                        }
                    }
                }
            }
            chart()
        }
        .padding(12)
        .background(L.cardBackground)
        .cornerRadius(8)
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(L.cardBorder, lineWidth: 1))
    }

    // MARK: - Chart Data

    private struct PrintChartPoint: Identifiable {
        let id = UUID()
        let date: Date
        let value: Double
        let series: String
    }

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    private func buildChartData(values: [Double?], series: String = "default") -> [PrintChartPoint] {
        var points: [PrintChartPoint] = []
        let dates = breadth.dates
        let step = max(1, dates.count / 250)

        for i in stride(from: 0, to: min(dates.count, values.count), by: step) {
            guard let val = values[i],
                  let date = Self.dateFormatter.date(from: dates[i]) else { continue }
            points.append(PrintChartPoint(date: date, value: val, series: series))
        }
        return points
    }

    // MARK: - Text Interpretations

    private func adInterpretation(_ v: Double) -> String {
        if v > 1.5 { return "A/D Ratio สูงที่ \(String(format: "%.2f", v)) หุ้นขึ้นมากกว่าลงอย่างชัดเจน" }
        if v > 1.0 { return "A/D Ratio อยู่ที่ \(String(format: "%.2f", v)) หุ้นขึ้นมากกว่าลงเล็กน้อย" }
        if v > 0.7 { return "A/D Ratio อยู่ที่ \(String(format: "%.2f", v)) หุ้นลงมากกว่าขึ้นเล็กน้อย" }
        return "A/D Ratio ต่ำที่ \(String(format: "%.2f", v)) หุ้นส่วนใหญ่ปรับตัวลง"
    }

    private func maInterpretation(_ v: Double) -> String {
        if v > 70 { return "หุ้น \(String(format: "%.1f", v))% เทรดเหนือ 200MA ตลาดกระทิงแข็งแกร่ง" }
        if v > 50 { return "หุ้น \(String(format: "%.1f", v))% เทรดเหนือ 200MA ตลาดยังเป็นบวก" }
        if v > 30 { return "หุ้นเพียง \(String(format: "%.1f", v))% เทรดเหนือ 200MA ตลาดเริ่มอ่อนแอ" }
        return "หุ้นเพียง \(String(format: "%.1f", v))% เทรดเหนือ 200MA อยู่ในโซน Oversold"
    }

    private func mccInterpretation(_ v: Double) -> String {
        if v > 50 { return "McClellan Oscillator สูงที่ \(String(format: "%.1f", v)) โมเมนตัมเร่งตัวแรง" }
        if v > 0 { return "McClellan Oscillator เป็นบวกที่ \(String(format: "%.1f", v)) โมเมนตัมยังเป็นขาขึ้น" }
        if v > -50 { return "McClellan Oscillator ติดลบที่ \(String(format: "%.1f", v)) โมเมนตัมชะลอตัว" }
        return "McClellan Oscillator ต่ำมากที่ \(String(format: "%.1f", v)) แรงขายกระจายตัวหนัก"
    }

    private func trinInterpretation(_ v: Double) -> String {
        if v < 0.75 { return "TRIN ต่ำที่ \(String(format: "%.2f", v)) volume ไหลเข้าหุ้นขาขึ้นอย่างแข็งแกร่ง" }
        if v < 1.0 { return "TRIN อยู่ที่ \(String(format: "%.2f", v)) volume เอนเอียงไปทางฝั่งซื้อ" }
        if v < 1.25 { return "TRIN อยู่ที่ \(String(format: "%.2f", v)) volume เอนเอียงไปทางฝั่งขาย" }
        return "TRIN สูงที่ \(String(format: "%.2f", v)) แรงขายหนัก volume ไหลเข้าหุ้นขาลง"
    }

    private func regimeVerdict(_ regime: String, bullCount: Int, bearCount: Int) -> String {
        switch regime {
        case "strong_bull": return "ตลาดอยู่ในภาวะกระทิงแข็งแกร่ง — Breadth กว้าง หุ้นส่วนใหญ่มีส่วนร่วมในขาขึ้น"
        case "bull": return "ตลาดอยู่ในภาวะกระทิง — Breadth ค่อนข้างดี แต่ควรเฝ้าระวัง Divergence"
        case "neutral":
            return bullCount > bearCount
                ? "ตลาดทรงตัว สัญญาณบวกมากกว่าลบ — อาจเริ่มฟื้นตัว"
                : "ตลาดทรงตัว สัญญาณผสม — ควรระมัดระวังและรอความชัดเจน"
        case "bear": return "ตลาดอยู่ในภาวะหมี — Breadth อ่อนแอ ควรลดความเสี่ยง"
        case "strong_bear": return "ตลาดอยู่ในภาวะหมีรุนแรง — แรงขายกระจายตัวทั่วตลาด ควร Defensive"
        default: return "ไม่สามารถระบุภาวะตลาดได้ชัดเจน"
        }
    }

    private func regimeColor(_ regime: String) -> Color {
        switch regime {
        case "strong_bull": return profitColor
        case "bull": return profitColor.opacity(0.7)
        case "neutral": return goldColor
        case "bear": return lossColor.opacity(0.7)
        case "strong_bear": return lossColor
        default: return L.textTertiary
        }
    }

    private func fmtVal(_ value: Double?, d: Int) -> String {
        guard let v = value else { return "—" }
        return String(format: "%.\(d)f", v)
    }

    private func fmtPct(_ value: Double?) -> String {
        guard let v = value else { return "—" }
        return String(format: "%.1f%%", v)
    }
}

// MARK: - Print Chart Axes Modifier

private extension View {
    func printChartAxes() -> some View {
        self
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 6)) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(Color(hex: "9CA3AF").opacity(0.3))
                    AxisValueLabel {
                        if let d = value.as(Date.self) {
                            Text(d, format: .dateTime.month(.abbreviated).day())
                                .font(.system(size: 8))
                                .foregroundColor(Color(hex: "6B7280"))
                        }
                    }
                }
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(Color(hex: "9CA3AF").opacity(0.3))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(String(format: "%.0f", v))
                                .font(.system(size: 8, design: .monospaced))
                                .foregroundColor(Color(hex: "6B7280"))
                        }
                    }
                }
            }
            .chartLegend(.hidden)
    }
}
