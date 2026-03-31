//
//  MarketBreadthView.swift
//  Pythia — Market Breadth Indicators
//

import SwiftUI
import Charts
import AppKit
import UniformTypeIdentifiers

struct MarketBreadthView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var universes: [BreadthUniverse] = []
    @State private var selectedUniverse: String = "SET50"
    @State private var selectedPeriod: String = "1y"
    @State private var breadth: BreadthResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let periods = [("3mo", "3M"), ("6mo", "6M"), ("1y", "1Y"), ("2y", "2Y")]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                headerSection

                if isLoading {
                    LoadingView("Computing breadth indicators...")
                } else if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if let b = breadth, b.success {
                    regimeBadge(b.current)
                    summaryCards(b.current)
                    marketSummary(b.current)
                    adLineChart(b)
                    pctAboveMAChart(b)
                    mcclEllanChart(b)
                    newHighsLowsChart(b)
                    trinChart(b)
                    divergenceAlerts(b.current)
                    breadthTheorySection
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadUniverses() }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Market Breadth")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            HStack(spacing: PythiaTheme.spacing) {
                Picker("Universe", selection: $selectedUniverse) {
                    ForEach(universes) { u in
                        Text("\(u.name) (\(u.size))").tag(u.id)
                    }
                }
                .frame(width: 320)

                ForEach(periods, id: \.0) { value, label in
                    Button(label) {
                        selectedPeriod = value
                        Task { await loadBreadth() }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(selectedPeriod == value ? PythiaTheme.primaryBlue : PythiaTheme.surfaceBackground)
                    .foregroundColor(selectedPeriod == value ? .white : PythiaTheme.textSecondary)
                    .cornerRadius(PythiaTheme.smallCornerRadius)
                }

                Button("Load") {
                    Task { await loadBreadth() }
                }
                .pythiaPrimaryButton()

                if breadth != nil {
                    Button(action: exportPDF) {
                        HStack(spacing: 4) {
                            Image(systemName: "arrow.down.doc.fill")
                            Text("PDF")
                        }
                    }
                    .pythiaSecondaryButton()
                }

                Spacer()
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Regime Badge

    private func regimeBadge(_ current: BreadthCurrent) -> some View {
        HStack(spacing: 12) {
            Circle()
                .fill(regimeColor(current.regime))
                .frame(width: 12, height: 12)

            Text(regimeLabel(current.regime))
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Text(current.regime.replacingOccurrences(of: "_", with: " ").uppercased())
                .font(PythiaTheme.caption())
                .fontWeight(.bold)
                .foregroundColor(regimeColor(current.regime))
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(regimeColor(current.regime).opacity(0.15))
                .cornerRadius(12)

            Spacer()

            if let size = breadth?.universeSize {
                Text("\(size) stocks")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Summary Cards

    private func summaryCards(_ current: BreadthCurrent) -> some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: PythiaTheme.spacing), count: 4), spacing: PythiaTheme.spacing) {
            MetricBox(
                "A/D Ratio",
                formatVal(current.adRatio, decimals: 2),
                (current.adRatio ?? 1) > 1 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
            MetricBox(
                "% > 200MA",
                formatPct(current.pctAbove200ma),
                (current.pctAbove200ma ?? 50) > 50 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
            MetricBox(
                "McClellan Osc",
                formatVal(current.mcclEllanOscillator, decimals: 1),
                (current.mcclEllanOscillator ?? 0) > 0 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
            MetricBox(
                "TRIN (10d)",
                formatVal(current.trin, decimals: 2),
                (current.trin ?? 1) < 1 ? PythiaTheme.profit : PythiaTheme.loss,
                size: .medium
            )
        }
    }

    // MARK: - Market Summary

    private func marketSummary(_ current: BreadthCurrent) -> some View {
        let adRatio = current.adRatio ?? 1.0
        let pctAbove200 = current.pctAbove200ma ?? 50.0
        let mcclellan = current.mcclEllanOscillator ?? 0.0
        let trin = current.trin ?? 1.0
        let regime = current.regime

        // Score: count bullish/bearish signals
        var bullCount = 0
        var bearCount = 0

        if adRatio > 1.0 { bullCount += 1 } else { bearCount += 1 }
        if pctAbove200 > 50 { bullCount += 1 } else { bearCount += 1 }
        if mcclellan > 0 { bullCount += 1 } else { bearCount += 1 }
        if trin < 1.0 { bullCount += 1 } else { bearCount += 1 }

        // A/D Ratio interpretation
        let adText: String = {
            if adRatio > 1.5 { return "A/D Ratio สูงที่ \(String(format: "%.2f", adRatio)) หุ้นขึ้นมากกว่าลงอย่างชัดเจน" }
            if adRatio > 1.0 { return "A/D Ratio อยู่ที่ \(String(format: "%.2f", adRatio)) หุ้นขึ้นมากกว่าลงเล็กน้อย" }
            if adRatio > 0.7 { return "A/D Ratio อยู่ที่ \(String(format: "%.2f", adRatio)) หุ้นลงมากกว่าขึ้นเล็กน้อย" }
            return "A/D Ratio ต่ำที่ \(String(format: "%.2f", adRatio)) หุ้นส่วนใหญ่ปรับตัวลง"
        }()

        // % Above 200MA interpretation
        let maText: String = {
            if pctAbove200 > 70 { return "หุ้น \(String(format: "%.1f", pctAbove200))% เทรดเหนือ 200MA แสดงถึงตลาดกระทิงที่แข็งแกร่ง" }
            if pctAbove200 > 50 { return "หุ้น \(String(format: "%.1f", pctAbove200))% เทรดเหนือ 200MA ตลาดยังมีแนวโน้มเป็นบวก" }
            if pctAbove200 > 30 { return "หุ้นเพียง \(String(format: "%.1f", pctAbove200))% เทรดเหนือ 200MA ตลาดเริ่มอ่อนแอ" }
            return "หุ้นเพียง \(String(format: "%.1f", pctAbove200))% เทรดเหนือ 200MA อยู่ในโซน Oversold"
        }()

        // McClellan interpretation
        let mccText: String = {
            if mcclellan > 50 { return "McClellan Oscillator สูงที่ \(String(format: "%.1f", mcclellan)) โมเมนตัมเร่งตัวแรง" }
            if mcclellan > 0 { return "McClellan Oscillator เป็นบวกที่ \(String(format: "%.1f", mcclellan)) โมเมนตัมยังเป็นขาขึ้น" }
            if mcclellan > -50 { return "McClellan Oscillator ติดลบที่ \(String(format: "%.1f", mcclellan)) โมเมนตัมชะลอตัว" }
            return "McClellan Oscillator ต่ำมากที่ \(String(format: "%.1f", mcclellan)) แรงขายกระจายตัวหนัก"
        }()

        // TRIN interpretation
        let trinText: String = {
            if trin < 0.75 { return "TRIN ต่ำที่ \(String(format: "%.2f", trin)) volume ไหลเข้าหุ้นขาขึ้นอย่างแข็งแกร่ง" }
            if trin < 1.0 { return "TRIN อยู่ที่ \(String(format: "%.2f", trin)) volume เอนเอียงไปทางฝั่งซื้อ" }
            if trin < 1.25 { return "TRIN อยู่ที่ \(String(format: "%.2f", trin)) volume เอนเอียงไปทางฝั่งขาย" }
            return "TRIN สูงที่ \(String(format: "%.2f", trin)) แรงขายหนัก volume ไหลเข้าหุ้นขาลง"
        }()

        // Overall verdict
        let verdict: String = {
            switch regime {
            case "strong_bull": return "ตลาดอยู่ในภาวะกระทิงแข็งแกร่ง — Breadth กว้าง หุ้นส่วนใหญ่มีส่วนร่วมในขาขึ้น เหมาะกับกลยุทธ์ตาม Trend"
            case "bull": return "ตลาดอยู่ในภาวะกระทิง — Breadth ค่อนข้างดี แต่ควรเฝ้าระวัง Divergence ที่อาจเกิดขึ้น"
            case "neutral":
                if bullCount > bearCount {
                    return "ตลาดอยู่ในภาวะทรงตัว แต่มีสัญญาณบวกมากกว่าลบ — อาจเริ่มฟื้นตัว ควรรอยืนยันจาก Breadth ก่อนเข้า"
                } else {
                    return "ตลาดอยู่ในภาวะทรงตัว สัญญาณผสม — ควรระมัดระวังและรอความชัดเจนก่อนตัดสินใจ"
                }
            case "bear": return "ตลาดอยู่ในภาวะหมี — Breadth อ่อนแอ หุ้นส่วนน้อยที่ยังยืนได้ ควรลดความเสี่ยงหรือรอสัญญาณกลับตัว"
            case "strong_bear": return "ตลาดอยู่ในภาวะหมีรุนแรง — แรงขายกระจายตัวทั่วทั้งตลาด ควร Defensive หรือถือเงินสด"
            default: return "ไม่สามารถระบุภาวะตลาดได้ชัดเจน"
            }
        }()

        let summaryColor: Color = {
            if bullCount >= 3 { return PythiaTheme.profit }
            if bearCount >= 3 { return PythiaTheme.loss }
            return PythiaTheme.accentGold
        }()

        return VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "chart.bar.doc.horizontal.fill")
                    .foregroundColor(summaryColor)
                Text("สรุปภาพรวมตลาด")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("Bullish \(bullCount) / Bearish \(bearCount)")
                    .font(.system(size: 12, weight: .semibold, design: .monospaced))
                    .foregroundColor(summaryColor)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(summaryColor.opacity(0.12))
                    .cornerRadius(8)
            }

            Text(verdict)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(PythiaTheme.textPrimary)
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(summaryColor.opacity(0.06))
                .cornerRadius(8)

            VStack(alignment: .leading, spacing: 6) {
                summaryBullet(adText, bullish: adRatio > 1.0)
                summaryBullet(maText, bullish: pctAbove200 > 50)
                summaryBullet(mccText, bullish: mcclellan > 0)
                summaryBullet(trinText, bullish: trin < 1.0)
            }

            if !current.divergences.isEmpty {
                HStack(spacing: 6) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 11))
                        .foregroundColor(PythiaTheme.warningOrange)
                    Text("พบ Divergence \(current.divergences.count) รายการ — ควรระวังการกลับตัวของตลาด")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.warningOrange)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func summaryBullet(_ text: String, bullish: Bool) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: bullish ? "arrow.up.circle.fill" : "arrow.down.circle.fill")
                .font(.system(size: 11))
                .foregroundColor(bullish ? PythiaTheme.profit : PythiaTheme.loss)
                .padding(.top, 2)
            Text(text)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }

    // MARK: - A/D Line Chart

    private func adLineChart(_ b: BreadthResponse) -> some View {
        let data = chartData(dates: b.dates, values: b.indicators.adLine)

        return VStack(alignment: .leading, spacing: 8) {
            Text("Advance/Decline Line")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(data) { point in
                AreaMark(x: .value("Date", point.date), y: .value("A/D", point.value))
                    .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.08))
                LineMark(x: .value("Date", point.date), y: .value("A/D", point.value))
                    .foregroundStyle(PythiaTheme.secondaryBlue)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))
            }
            .frame(height: 200)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - % Above MA Chart

    private func pctAboveMAChart(_ b: BreadthResponse) -> some View {
        let data50 = chartData(dates: b.dates, values: b.indicators.pctAbove50ma, series: "50d MA")
        let data200 = chartData(dates: b.dates, values: b.indicators.pctAbove200ma, series: "200d MA")
        let allData = data50 + data200

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("% Above Moving Average")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                HStack(spacing: 12) {
                    legendDot(color: PythiaTheme.accentBlue, label: "50d")
                    legendDot(color: PythiaTheme.accentGold, label: "200d")
                }
            }

            Chart(allData) { point in
                AreaMark(
                    x: .value("Date", point.date),
                    y: .value("%", point.value)
                )
                .foregroundStyle(by: .value("Series", point.series))
                .opacity(0.08)

                LineMark(
                    x: .value("Date", point.date),
                    y: .value("%", point.value)
                )
                .foregroundStyle(by: .value("Series", point.series))
                .lineStyle(StrokeStyle(lineWidth: 1.5))

                // Reference lines
                RuleMark(y: .value("", 30))
                    .foregroundStyle(PythiaTheme.loss.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 50))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                RuleMark(y: .value("", 70))
                    .foregroundStyle(PythiaTheme.profit.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
            }
            .chartForegroundStyleScale([
                "50d MA": PythiaTheme.accentBlue,
                "200d MA": PythiaTheme.accentGold,
            ])
            .chartYScale(domain: 0...100)
            .frame(height: 200)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - McClellan Oscillator

    private func mcclEllanChart(_ b: BreadthResponse) -> some View {
        let data = chartData(dates: b.dates, values: b.indicators.mcclEllanOscillator)

        return VStack(alignment: .leading, spacing: 8) {
            Text("McClellan Oscillator")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(data) { point in
                BarMark(
                    x: .value("Date", point.date),
                    y: .value("McClellan", point.value)
                )
                .foregroundStyle(point.value >= 0 ? PythiaTheme.profit : PythiaTheme.loss)

                RuleMark(y: .value("", 0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .frame(height: 180)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - New Highs vs Lows

    private func newHighsLowsChart(_ b: BreadthResponse) -> some View {
        let highs = chartData(dates: b.dates, values: b.indicators.newHighs, series: "New Highs")
        let lows = chartData(dates: b.dates, values: b.indicators.newLows.map { v in
            v.map { -$0 }  // flip lows negative
        }, series: "New Lows")
        let allData = highs + lows

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("New 52-Week Highs vs Lows")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                HStack(spacing: 12) {
                    legendDot(color: PythiaTheme.profit, label: "Highs")
                    legendDot(color: PythiaTheme.loss, label: "Lows")
                }
            }

            Chart(allData) { point in
                BarMark(
                    x: .value("Date", point.date),
                    y: .value("Count", point.value)
                )
                .foregroundStyle(by: .value("Series", point.series))

                RuleMark(y: .value("", 0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .chartForegroundStyleScale([
                "New Highs": PythiaTheme.profit,
                "New Lows": PythiaTheme.loss,
            ])
            .frame(height: 180)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - TRIN Chart

    private func trinChart(_ b: BreadthResponse) -> some View {
        let data = chartData(dates: b.dates, values: b.indicators.trin10dAvg)

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("TRIN (Arms Index) — 10d Avg")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("< 1.0 = Bullish")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            Chart(data) { point in
                LineMark(x: .value("Date", point.date), y: .value("TRIN", point.value))
                    .foregroundStyle(PythiaTheme.accentGold)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))

                // Zone rules
                RuleMark(y: .value("", 0.75))
                    .foregroundStyle(PythiaTheme.profit.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                    .annotation(position: .leading) {
                        Text("0.75")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundColor(PythiaTheme.profit.opacity(0.5))
                    }

                RuleMark(y: .value("", 1.0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))

                RuleMark(y: .value("", 1.25))
                    .foregroundStyle(PythiaTheme.loss.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [4]))
                    .annotation(position: .leading) {
                        Text("1.25")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundColor(PythiaTheme.loss.opacity(0.5))
                    }
            }
            .frame(height: 180)
            .pythiaChartAxes(gridOpacity: 0.1)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Divergence Alerts

    @ViewBuilder
    private func divergenceAlerts(_ current: BreadthCurrent) -> some View {
        if !current.divergences.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(PythiaTheme.warningOrange)
                    Text("Divergence Alerts")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)
                }

                ForEach(current.divergences, id: \.self) { msg in
                    HStack(alignment: .top, spacing: 8) {
                        Circle()
                            .fill(PythiaTheme.warningOrange)
                            .frame(width: 6, height: 6)
                            .padding(.top, 6)

                        Text(msg)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }
            .padding()
            .background(PythiaTheme.warningOrange.opacity(0.05))
            .overlay(RoundedRectangle(cornerRadius: PythiaTheme.cornerRadius).stroke(PythiaTheme.warningOrange.opacity(0.3), lineWidth: 1))
            .cornerRadius(PythiaTheme.cornerRadius)
        }
    }

    // MARK: - Breadth Theory

    private var breadthTheorySection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Image(systemName: "book.fill")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("Market Breadth Analysis Guide")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            VStack(alignment: .leading, spacing: 14) {
                theoryItem(
                    title: "Advance/Decline Line",
                    description: "ผลรวมสะสมของ (หุ้นขึ้น - หุ้นลง) ถ้า A/D Line ขึ้นตามดัชนี แสดงว่าหุ้นส่วนใหญ่มีส่วนร่วมในขาขึ้น แต่ถ้าดัชนีขึ้นแต่ A/D Line ลง เป็นสัญญาณเตือนว่าหุ้นน้อยตัวลงเรื่อยๆ ที่หนุนตลาด",
                    bullish: "ขึ้นพร้อมดัชนี = หุ้นมีส่วนร่วมกว้าง",
                    bearish: "ลงขณะดัชนีขึ้น = ผู้นำแคบลง เสี่ยงกลับตัว"
                )
                Divider().background(PythiaTheme.textTertiary.opacity(0.2))

                theoryItem(
                    title: "% Above Moving Average",
                    description: "สัดส่วนหุ้นที่เทรดเหนือเส้น MA 50 วัน หรือ 200 วัน ใช้วัด Overbought/Oversold ของทั้งตลาด",
                    bullish: "> 70% เหนือ 200MA = ตลาดกระทิงแข็งแกร่ง",
                    bearish: "< 30% เหนือ 200MA = Oversold อาจเด้งหรืออ่อนตัวต่อ"
                )
                Divider().background(PythiaTheme.textTertiary.opacity(0.2))

                theoryItem(
                    title: "McClellan Oscillator",
                    description: "ผลต่างระหว่าง EMA 19 วัน กับ 39 วัน ของ (หุ้นขึ้น - หุ้นลง) วัดโมเมนตัมของ breadth ว่าการมีส่วนร่วมเร่งตัวหรือชะลอ",
                    bullish: "> 0 และเพิ่มขึ้น = โมเมนตัม breadth เร่งตัว",
                    bearish: "< 0 และลดลง = การมีส่วนร่วมลดลง แรงขายกระจายตัว"
                )
                Divider().background(PythiaTheme.textTertiary.opacity(0.2))

                theoryItem(
                    title: "New 52-Week Highs vs Lows",
                    description: "นับหุ้นที่ทำ New High/Low รอบ 52 สัปดาห์ ตลาดกระทิงที่แข็งแรงจะมี New Highs มากกว่า New Lows อย่างสม่ำเสมอ",
                    bullish: "Highs >> Lows = เทรนด์แข็ง หุ้นทำ breakout กว้าง",
                    bearish: "Lows >> Highs = หุ้นหลุดแนวรับทั่วตัว เข้าสู่ช่วง distribution"
                )
                Divider().background(PythiaTheme.textTertiary.opacity(0.2))

                theoryItem(
                    title: "TRIN (Arms Index)",
                    description: "อัตราส่วนของ (หุ้นขึ้น/หุ้นลง) ต่อ (volume ขึ้น/volume ลง) วัดว่า volume ไหลเข้าหุ้นขาขึ้นหรือขาลงมากกว่า",
                    bullish: "< 1.0 = volume ไหลเข้าหุ้นขาขึ้น (แรงซื้อ)",
                    bearish: "> 1.0 = volume ไหลเข้าหุ้นขาลง (แรงขาย)"
                )
            }
        }
        .padding()
        .pythiaCard()
    }

    private func theoryItem(title: String, description: String, bullish: String, bearish: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(PythiaTheme.accentGold)

            Text(description)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)

            HStack(alignment: .top, spacing: 16) {
                HStack(alignment: .top, spacing: 6) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 11))
                        .foregroundColor(PythiaTheme.profit)
                        .padding(.top, 2)
                    Text(bullish)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.profit.opacity(0.8))
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                HStack(alignment: .top, spacing: 6) {
                    Image(systemName: "arrow.down.circle.fill")
                        .font(.system(size: 11))
                        .foregroundColor(PythiaTheme.loss)
                        .padding(.top, 2)
                    Text(bearish)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.loss.opacity(0.8))
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }

    // MARK: - Export PDF

    @MainActor
    private func exportPDF() {
        guard let b = breadth else { return }

        let uName = universes.first(where: { $0.id == selectedUniverse })
            .map { "\($0.name) (\($0.size))" } ?? selectedUniverse
        let printView = MarketBreadthPrintView(breadth: b, universe: selectedUniverse, universeName: uName)
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
        let safeName = uName.replacingOccurrences(of: " ", with: "_")
            .replacingOccurrences(of: "(", with: "").replacingOccurrences(of: ")", with: "")
        panel.nameFieldStringValue = "\(safeName)_breadth.pdf"
        panel.title = "Export Market Breadth PDF"

        if panel.runModal() == .OK, let url = panel.url {
            try? pdfData.write(to: url, options: .atomic)
        }
    }

    // MARK: - Data Loading

    private func loadUniverses() async {
        do {
            universes = try await db.fetchBreadthUniverses()
            if !universes.isEmpty {
                await loadBreadth()
            }
        } catch {
            errorMessage = "Failed to load universes: \(error.localizedDescription)"
        }
    }

    private func loadBreadth() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            breadth = try await db.fetchBreadth(universe: selectedUniverse, period: selectedPeriod)
        } catch {
            errorMessage = "Failed to load breadth: \(error.localizedDescription)"
        }
    }

    // MARK: - Helpers

    private func regimeColor(_ regime: String) -> Color {
        switch regime {
        case "strong_bull": return PythiaTheme.profit
        case "bull": return PythiaTheme.profit.opacity(0.7)
        case "neutral": return PythiaTheme.accentGold
        case "bear": return PythiaTheme.loss.opacity(0.7)
        case "strong_bear": return PythiaTheme.loss
        default: return PythiaTheme.textTertiary
        }
    }

    private func regimeLabel(_ regime: String) -> String {
        switch regime {
        case "strong_bull": return "Market Regime:"
        case "bull": return "Market Regime:"
        case "neutral": return "Market Regime:"
        case "bear": return "Market Regime:"
        case "strong_bear": return "Market Regime:"
        default: return "Market Regime:"
        }
    }

    private func formatVal(_ value: Double?, decimals: Int = 2) -> String {
        guard let v = value else { return "—" }
        return String(format: "%.\(decimals)f", v)
    }

    private func formatPct(_ value: Double?) -> String {
        guard let v = value else { return "—" }
        return String(format: "%.1f%%", v)
    }

    private func legendDot(color: Color, label: String) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }
}

// MARK: - Chart Data Helper

private struct ChartPoint: Identifiable {
    let id = UUID()
    let date: Date
    let value: Double
    let series: String
}

private let chartDateFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "yyyy-MM-dd"
    f.locale = Locale(identifier: "en_US_POSIX")
    return f
}()

private func chartData(dates: [String], values: [Double?], series: String = "default") -> [ChartPoint] {
    var points: [ChartPoint] = []
    let step = max(1, dates.count / 250)  // downsample to ~250 points for performance

    for i in stride(from: 0, to: dates.count, by: step) {
        guard let val = values[safe: i] ?? nil,
              let date = chartDateFormatter.date(from: dates[i]) else { continue }
        points.append(ChartPoint(date: date, value: val, series: series))
    }
    return points
}

private extension Collection {
    subscript(safe index: Index) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
