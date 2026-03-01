//
//  TechnicalChartView.swift
//  Pythia — Technical Analysis Charts (Webull/TradingView-inspired)
//

import SwiftUI
import Charts

struct TechnicalChartView: View {
    @EnvironmentObject var db: DatabaseService

    let symbol: String

    // TA data
    @State private var ta: TechnicalAnalysisResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    // Period selector
    @State private var period = "6mo"
    private let periods = [("1mo", "1M"), ("3mo", "3M"), ("6mo", "6M"), ("1y", "1Y"), ("2y", "2Y"), ("5y", "5Y")]

    // Indicator toggles
    @State private var showSMA = true
    @State private var showEMA = false
    @State private var showBollinger = false
    @State private var showMACD = true
    @State private var showRSI = true
    @State private var showVolume = true

    // Configurable params
    @State private var showSettings = false
    @State private var macdFast = 12
    @State private var macdSlow = 26
    @State private var macdSignal = 9
    @State private var rsiPeriod = 14
    @State private var sma1 = 20
    @State private var sma2 = 50
    @State private var bbPeriod = 20
    @State private var bbStd = 2.0

    // Hover state — shared across all charts
    @State private var hoverIndex: Int?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header row: Title + OHLC hover data inline (TradingView style)
            HStack(spacing: 8) {
                Text("Technical Analysis")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)

                Text(symbol)
                    .font(.system(size: 14, weight: .bold, design: .monospaced))
                    .foregroundColor(PythiaTheme.accentGold)

                // Inline OHLC when hovering (like TradingView header)
                if let ta = ta, let idx = hoverIndex, idx < ta.dates.count {
                    inlineOHLC(ta, index: idx)
                }

                Spacer()

                // Settings button
                Button {
                    showSettings.toggle()
                } label: {
                    Image(systemName: "slider.horizontal.3")
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }

            // Period pills (Webull-style) + Indicator toggles
            HStack(spacing: 6) {
                // Period pills
                ForEach(periods, id: \.0) { val, label in
                    PeriodPill(label: label, isSelected: period == val) {
                        period = val
                        Task { await loadTA() }
                    }
                }

                Divider()
                    .frame(height: 20)
                    .padding(.horizontal, 4)

                // Indicator toggles
                IndicatorToggle(label: "SMA", isOn: $showSMA, color: PythiaTheme.accentGold)
                IndicatorToggle(label: "EMA", isOn: $showEMA, color: .cyan)
                IndicatorToggle(label: "BB", isOn: $showBollinger, color: .purple)
                IndicatorToggle(label: "MACD", isOn: $showMACD, color: PythiaTheme.secondaryBlue)
                IndicatorToggle(label: "RSI", isOn: $showRSI, color: .orange)
                IndicatorToggle(label: "Vol", isOn: $showVolume, color: PythiaTheme.textTertiary)
            }

            // Settings panel (collapsible)
            if showSettings {
                settingsPanel
            }

            if isLoading {
                LoadingView("Computing indicators...")
            } else if let error = errorMessage {
                Text(error)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.errorRed)
            } else if let ta = ta {
                // Price chart (with optional volume overlay)
                priceChart(ta)

                // Sub-charts
                if showVolume {
                    volumeChart(ta)
                }
                if showMACD {
                    macdChart(ta)
                }
                if showRSI {
                    rsiChart(ta)
                }
            }
        }
        .padding(PythiaTheme.largeSpacing)
        .pythiaCard()
        .task { await loadTA() }
    }

    // MARK: - Inline OHLC (TradingView-style header)

    private func inlineOHLC(_ ta: TechnicalAnalysisResponse, index: Int) -> some View {
        let o = ta.ohlcv.open[index]
        let h = ta.ohlcv.high[index]
        let l = ta.ohlcv.low[index]
        let c = ta.ohlcv.close[index]
        let isUp = c >= o
        let changeColor = isUp ? PythiaTheme.profit : PythiaTheme.loss

        // Change from previous close (TradingView-style: −8.77 (−3.21%))
        let prevClose = index > 0 ? ta.ohlcv.close[index - 1] : o
        let chg = c - prevClose
        let chgPct = prevClose != 0 ? (chg / prevClose * 100) : 0

        return HStack(spacing: 10) {
            Text(ta.dates[index])
                .foregroundColor(PythiaTheme.textTertiary)

            ohlcLabel("O", value: o)
            ohlcLabel("H", value: h, color: PythiaTheme.profit)
            ohlcLabel("L", value: l, color: PythiaTheme.loss)
            ohlcLabel("C", value: c, color: changeColor)

            // Change value + percent (TradingView-style)
            Text(String(format: "%+.2f (%+.2f%%)", chg, chgPct))
                .foregroundColor(changeColor)

            Text("Vol")
                .foregroundColor(PythiaTheme.textTertiary)
            Text(MarketDataService.shared.formatVolume(ta.ohlcv.volume[index]))
                .foregroundColor(PythiaTheme.textSecondary)

            if let rsi = ta.rsi.values[safe: index] ?? nil {
                HStack(spacing: 2) {
                    Text("RSI")
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(String(format: "%.1f", rsi))
                        .foregroundColor(rsi > 70 ? PythiaTheme.loss : rsi < 30 ? PythiaTheme.profit : .orange)
                }
            }

            if let macd = ta.macd.macd[safe: index] ?? nil {
                HStack(spacing: 2) {
                    Text("MACD")
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(String(format: "%.3f", macd))
                        .foregroundColor(macd >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                }
            }
        }
        .font(.system(size: 11, weight: .medium, design: .monospaced))
    }

    private func ohlcLabel(_ label: String, value: Double, color: Color = PythiaTheme.textPrimary) -> some View {
        HStack(spacing: 2) {
            Text(label)
                .foregroundColor(PythiaTheme.textTertiary)
            Text(String(format: "%.2f", value))
                .foregroundColor(color)
        }
    }

    // MARK: - Settings Panel

    private var settingsPanel: some View {
        VStack(spacing: 10) {
            HStack(spacing: 24) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("MACD")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                    HStack(spacing: 8) {
                        paramField("Fast", value: $macdFast)
                        paramField("Slow", value: $macdSlow)
                        paramField("Signal", value: $macdSignal)
                    }
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("RSI")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                    paramField("Period", value: $rsiPeriod)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("SMA")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                    HStack(spacing: 8) {
                        paramField("MA1", value: $sma1)
                        paramField("MA2", value: $sma2)
                    }
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Bollinger")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                    HStack(spacing: 8) {
                        paramField("Period", value: $bbPeriod)
                        paramFieldDouble("StdDev", value: $bbStd)
                    }
                }

                Spacer()

                Button("Apply") {
                    Task { await loadTA() }
                }
                .pythiaPrimaryButton()
            }
        }
        .padding(12)
        .background(PythiaTheme.surfaceBackground)
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }

    private func paramField(_ label: String, value: Binding<Int>) -> some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(PythiaTheme.textTertiary)
            TextField("", value: value, format: .number)
                .textFieldStyle(.roundedBorder)
                .frame(width: 44)
                .font(.system(size: 12, design: .monospaced))
        }
    }

    private func paramFieldDouble(_ label: String, value: Binding<Double>) -> some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(PythiaTheme.textTertiary)
            TextField("", value: value, format: .number.precision(.fractionLength(1)))
                .textFieldStyle(.roundedBorder)
                .frame(width: 44)
                .font(.system(size: 12, design: .monospaced))
        }
    }

    // MARK: - Hover Overlay Helper (TradingView-style: vertical + horizontal crosshair)

    @State private var hoverY: CGFloat?

    /// yDomain: when provided, shows a TradingView-style red price badge on the Y-axis at hover position
    private func chartHoverOverlay(dataCount: Int, yDomain: (lo: Double, hi: Double)? = nil) -> some View {
        GeometryReader { geo in
            Rectangle()
                .fill(Color.clear)
                .contentShape(Rectangle())
                .onContinuousHover { phase in
                    switch phase {
                    case .active(let location):
                        let fraction = location.x / geo.size.width
                        let index = Int(fraction * CGFloat(dataCount))
                        hoverIndex = min(max(index, 0), dataCount - 1)
                        hoverY = location.y
                    case .ended:
                        hoverIndex = nil
                        hoverY = nil
                    }
                }
                .overlay {
                    if let idx = hoverIndex {
                        let xPos = (CGFloat(idx) + 0.5) / CGFloat(dataCount) * geo.size.width
                        let crosshairStyle = StrokeStyle(lineWidth: 0.5, dash: [4, 3])
                        let crosshairColor = PythiaTheme.textTertiary.opacity(0.5)

                        // Vertical crosshair
                        Path { path in
                            path.move(to: CGPoint(x: xPos, y: 0))
                            path.addLine(to: CGPoint(x: xPos, y: geo.size.height))
                        }
                        .stroke(crosshairColor, style: crosshairStyle)

                        // Horizontal crosshair
                        if let yPos = hoverY, yPos >= 0, yPos <= geo.size.height {
                            Path { path in
                                path.move(to: CGPoint(x: 0, y: yPos))
                                path.addLine(to: CGPoint(x: geo.size.width, y: yPos))
                            }
                            .stroke(crosshairColor, style: crosshairStyle)

                            // Y-axis price badge (TradingView-style red label at right edge)
                            if let domain = yDomain {
                                let range = domain.hi - domain.lo
                                let price = domain.hi - (Double(yPos) / Double(geo.size.height)) * range

                                Text(formatAxisPrice(price))
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundColor(.white)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(
                                        RoundedRectangle(cornerRadius: 3)
                                            .fill(Color(red: 0.8, green: 0.2, blue: 0.2))
                                    )
                                    .fixedSize()
                                    .position(x: geo.size.width - 24, y: yPos)
                            }
                        }
                    }
                }
        }
    }

    // MARK: - Price Chart (Webull/TradingView-style Candlestick + overlays)

    private func priceChart(_ ta: TechnicalAnalysisResponse) -> some View {
        let points = buildPricePoints(ta)
        let lastClose = ta.ohlcv.close.last ?? 0
        let prevClose = ta.ohlcv.close.count >= 2 ? ta.ohlcv.close[ta.ohlcv.close.count - 2] : lastClose
        let isLastUp = lastClose >= prevClose

        // Dynamic candle width based on data density
        let candleWidth: CGFloat = points.count > 200 ? 3 : points.count > 100 ? 5 : 7
        let wickWidth: CGFloat = 1

        // TradingView-style: tight Y-axis from actual price range (not starting from 0)
        let allLows = ta.ohlcv.low
        let allHighs = ta.ohlcv.high
        var yMin = allLows.min() ?? 0
        var yMax = allHighs.max() ?? 100

        // Include BB bands in range if visible
        if showBollinger {
            let bbLows = ta.bollinger.lower.compactMap { $0 }
            let bbHighs = ta.bollinger.upper.compactMap { $0 }
            if let bbMin = bbLows.min() { yMin = min(yMin, bbMin) }
            if let bbMax = bbHighs.max() { yMax = max(yMax, bbMax) }
        }

        // Include SMA/EMA in range if visible
        if showSMA {
            let smaKey1 = String(sma1)
            let smaKey2 = String(sma2)
            if let vals = ta.sma[smaKey1] {
                let nonNil = vals.compactMap { $0 }
                if let lo = nonNil.min() { yMin = min(yMin, lo) }
                if let hi = nonNil.max() { yMax = max(yMax, hi) }
            }
            if let vals = ta.sma[smaKey2] {
                let nonNil = vals.compactMap { $0 }
                if let lo = nonNil.min() { yMin = min(yMin, lo) }
                if let hi = nonNil.max() { yMax = max(yMax, hi) }
            }
        }

        // 5% padding so candles don't touch edges
        let yRange = max(yMax - yMin, 0.01)
        let yPad = yRange * 0.05
        let domainLo = yMin - yPad
        let domainHi = yMax + yPad

        return VStack(alignment: .leading, spacing: 4) {
            // SMA/EMA legend (only when active)
            if showSMA || showEMA || showBollinger {
                HStack(spacing: 12) {
                    if showSMA {
                        legendItem("SMA\(sma1)", color: PythiaTheme.accentGold, solid: true)
                        legendItem("SMA\(sma2)", color: PythiaTheme.darkGold, solid: false)
                    }
                    if showEMA {
                        legendItem("EMA12", color: .cyan, solid: true)
                        legendItem("EMA26", color: .cyan.opacity(0.6), solid: false)
                    }
                    if showBollinger {
                        legendItem("BB", color: .purple.opacity(0.7), solid: false)
                    }
                }
            }

            Chart {
                // Current price line (TradingView-style dashed line with badge)
                RuleMark(y: .value("Current", lastClose))
                    .foregroundStyle(isLastUp ? PythiaTheme.profit.opacity(0.6) : PythiaTheme.loss.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 0.8, dash: [4, 4]))
                    .annotation(position: .trailing, spacing: 2) {
                        Text(String(format: "%.2f", lastClose))
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundColor(.white)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(isLastUp ? PythiaTheme.profit : PythiaTheme.loss)
                            )
                    }

                ForEach(points) { p in
                    // Wick (High-Low thin line)
                    BarMark(
                        x: .value("Date", p.date),
                        yStart: .value("Low", p.low),
                        yEnd: .value("High", p.high),
                        width: .fixed(wickWidth)
                    )
                    .foregroundStyle(p.isUp ? PythiaTheme.profit : PythiaTheme.loss)

                    // Candle Body (Open-Close) — wider bar
                    BarMark(
                        x: .value("Date", p.date),
                        yStart: .value("Open", p.open),
                        yEnd: .value("Close", p.close),
                        width: .fixed(candleWidth)
                    )
                    .foregroundStyle(p.isUp ? PythiaTheme.profit : PythiaTheme.loss)

                    // SMA overlays
                    if showSMA, let sma1Val = p.sma1 {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("SMA\(sma1)", sma1Val),
                            series: .value("Series", "SMA\(sma1)")
                        )
                        .foregroundStyle(PythiaTheme.accentGold)
                        .lineStyle(StrokeStyle(lineWidth: 1.5))
                    }

                    if showSMA, let sma2Val = p.sma2 {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("SMA\(sma2)", sma2Val),
                            series: .value("Series", "SMA\(sma2)")
                        )
                        .foregroundStyle(PythiaTheme.darkGold)
                        .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [6, 3]))
                    }

                    // EMA overlays
                    if showEMA, let ema1Val = p.ema1 {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("EMA12", ema1Val),
                            series: .value("Series", "EMA12")
                        )
                        .foregroundStyle(.cyan)
                        .lineStyle(StrokeStyle(lineWidth: 1.5))
                    }

                    if showEMA, let ema2Val = p.ema2 {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("EMA26", ema2Val),
                            series: .value("Series", "EMA26")
                        )
                        .foregroundStyle(.cyan.opacity(0.6))
                        .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [6, 3]))
                    }

                    // Bollinger Bands
                    if showBollinger, let bbUpper = p.bbUpper {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("BB Upper", bbUpper),
                            series: .value("Series", "BB Upper")
                        )
                        .foregroundStyle(.purple.opacity(0.7))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
                    }

                    if showBollinger, let bbLower = p.bbLower {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("BB Lower", bbLower),
                            series: .value("Series", "BB Lower")
                        )
                        .foregroundStyle(.purple.opacity(0.7))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
                    }

                    if showBollinger, let bbUpper = p.bbUpper, let bbLower = p.bbLower {
                        AreaMark(
                            x: .value("Date", p.date),
                            yStart: .value("BB Low", bbLower),
                            yEnd: .value("BB High", bbUpper),
                            series: .value("Series", "BB Fill")
                        )
                        .foregroundStyle(.purple.opacity(0.05))
                    }

                    if showBollinger, let bbMid = p.bbMiddle {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("BB Mid", bbMid),
                            series: .value("Series", "BB Mid")
                        )
                        .foregroundStyle(.purple.opacity(0.4))
                        .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [2, 2]))
                    }
                }
            }
            .chartYScale(domain: domainLo...domainHi)
            .chartYAxis {
                AxisMarks(position: .trailing, values: .automatic(desiredCount: 8)) { value in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.15))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(formatAxisPrice(v))
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .foregroundStyle(PythiaTheme.textSecondary)
                        }
                    }
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 8)) { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.08))
                    AxisValueLabel()
                        .font(.system(size: 10))
                        .foregroundStyle(PythiaTheme.textTertiary)
                }
            }
            .chartLegend(.hidden)
            .chartOverlay { _ in
                chartHoverOverlay(dataCount: points.count, yDomain: (domainLo, domainHi))
            }
            .frame(height: 380)
        }
    }

    /// Format Y-axis price labels — TradingView shows clean numbers
    private func formatAxisPrice(_ value: Double) -> String {
        if value >= 1000 {
            return String(format: "%.0f", value)
        } else if value >= 100 {
            return String(format: "%.1f", value)
        } else {
            return String(format: "%.2f", value)
        }
    }

    private func legendItem(_ label: String, color: Color, solid: Bool) -> some View {
        HStack(spacing: 3) {
            if solid {
                RoundedRectangle(cornerRadius: 1).fill(color).frame(width: 14, height: 2)
            } else {
                HStack(spacing: 1) {
                    Rectangle().fill(color).frame(width: 4, height: 2)
                    Rectangle().fill(color).frame(width: 4, height: 2)
                    Rectangle().fill(color).frame(width: 4, height: 2)
                }
            }
            Text(label).font(.system(size: 9)).foregroundColor(PythiaTheme.textTertiary)
        }
    }

    // MARK: - Volume Chart

    private func volumeChart(_ ta: TechnicalAnalysisResponse) -> some View {
        let points = buildVolumePoints(ta)

        return VStack(alignment: .leading, spacing: 4) {
            Text("Volume")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)

            Chart(points) { p in
                BarMark(
                    x: .value("Date", p.date),
                    y: .value("Volume", p.volume)
                )
                .foregroundStyle(p.isUp ? PythiaTheme.profit.opacity(0.5) : PythiaTheme.loss.opacity(0.5))
            }
            .chartYAxis {
                AxisMarks(position: .trailing, values: .automatic(desiredCount: 3)) { value in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.12))
                    AxisValueLabel {
                        if let v = value.as(Int.self) {
                            Text(MarketDataService.shared.formatVolume(v))
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundStyle(PythiaTheme.textTertiary)
                        }
                    }
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 8)) { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.08))
                    AxisValueLabel()
                        .font(.system(size: 10))
                        .foregroundStyle(PythiaTheme.textTertiary)
                }
            }
            .chartLegend(.hidden)
            .chartOverlay { _ in
                chartHoverOverlay(dataCount: points.count)
            }
            .frame(height: 80)
        }
    }

    // MARK: - MACD Chart

    private func macdChart(_ ta: TechnicalAnalysisResponse) -> some View {
        let points = buildMACDPoints(ta)

        // Compute tight Y-axis range from actual MACD data
        let allValues = points.compactMap { $0.macd } + points.compactMap { $0.signal } + points.compactMap { $0.histogram }
        let yMin = allValues.min() ?? -1
        let yMax = allValues.max() ?? 1
        let yPad = max(abs(yMax - yMin) * 0.15, 0.001)

        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("MACD")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                Text("(\(ta.macd.params.fast), \(ta.macd.params.slow), \(ta.macd.params.signal))")
                    .font(.system(size: 10))
                    .foregroundColor(PythiaTheme.textTertiary)
                Spacer()
                // Legend
                HStack(spacing: 10) {
                    HStack(spacing: 3) {
                        RoundedRectangle(cornerRadius: 1).fill(PythiaTheme.secondaryBlue).frame(width: 12, height: 2)
                        Text("MACD").font(.system(size: 9)).foregroundColor(PythiaTheme.textTertiary)
                    }
                    HStack(spacing: 3) {
                        RoundedRectangle(cornerRadius: 1).fill(PythiaTheme.accentGold).frame(width: 12, height: 2)
                        Text("Signal").font(.system(size: 9)).foregroundColor(PythiaTheme.textTertiary)
                    }
                    HStack(spacing: 3) {
                        Rectangle().fill(PythiaTheme.profit.opacity(0.4)).frame(width: 8, height: 8)
                        Text("Hist").font(.system(size: 9)).foregroundColor(PythiaTheme.textTertiary)
                    }
                }
            }

            Chart {
                // Zero line
                RuleMark(y: .value("Zero", 0))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.5))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))

                ForEach(points) { p in
                    // Histogram bars
                    if let hist = p.histogram {
                        BarMark(
                            x: .value("Date", p.date),
                            y: .value("Histogram", hist)
                        )
                        .foregroundStyle(hist >= 0 ? PythiaTheme.profit.opacity(0.5) : PythiaTheme.loss.opacity(0.5))
                    }

                    // MACD line
                    if let macd = p.macd {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("MACD", macd),
                            series: .value("Series", "MACD")
                        )
                        .foregroundStyle(PythiaTheme.secondaryBlue)
                        .lineStyle(StrokeStyle(lineWidth: 1.5))
                    }

                    // Signal line
                    if let signal = p.signal {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("Signal", signal),
                            series: .value("Series", "Signal")
                        )
                        .foregroundStyle(PythiaTheme.accentGold)
                        .lineStyle(StrokeStyle(lineWidth: 1.5))
                    }
                }
            }
            .chartYScale(domain: (yMin - yPad)...(yMax + yPad))
            .chartYAxis {
                AxisMarks(position: .trailing, values: .automatic(desiredCount: 5)) { value in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.12))
                    AxisValueLabel {
                        if let v = value.as(Double.self) {
                            Text(String(format: "%.2f", v))
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundStyle(PythiaTheme.textSecondary)
                        }
                    }
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 8)) { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.08))
                    AxisValueLabel()
                        .font(.system(size: 10))
                        .foregroundStyle(PythiaTheme.textTertiary)
                }
            }
            .chartLegend(.hidden)
            .chartOverlay { _ in
                chartHoverOverlay(dataCount: points.count)
            }
            .frame(height: 140)
        }
    }

    // MARK: - RSI Chart

    private func rsiChart(_ ta: TechnicalAnalysisResponse) -> some View {
        let points = buildRSIPoints(ta)

        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("RSI")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                Text("(\(ta.rsi.params.period))")
                    .font(.system(size: 10))
                    .foregroundColor(PythiaTheme.textTertiary)
                Spacer()
                // Legend
                HStack(spacing: 12) {
                    HStack(spacing: 3) {
                        Rectangle().fill(PythiaTheme.loss.opacity(0.15)).frame(width: 12, height: 8)
                        Text("Overbought 70").font(.system(size: 9)).foregroundColor(PythiaTheme.textTertiary)
                    }
                    HStack(spacing: 3) {
                        Rectangle().fill(PythiaTheme.profit.opacity(0.15)).frame(width: 12, height: 8)
                        Text("Oversold 30").font(.system(size: 9)).foregroundColor(PythiaTheme.textTertiary)
                    }
                }
            }

            Chart {
                // Overbought zone (70-100) — filled area
                ForEach(points) { p in
                    AreaMark(
                        x: .value("Date", p.date),
                        yStart: .value("OB Lo", 70),
                        yEnd: .value("OB Hi", 100),
                        series: .value("Zone", "Overbought")
                    )
                    .foregroundStyle(PythiaTheme.loss.opacity(0.08))
                }

                // Oversold zone (0-30) — filled area
                ForEach(points) { p in
                    AreaMark(
                        x: .value("Date", p.date),
                        yStart: .value("OS Lo", 0),
                        yEnd: .value("OS Hi", 30),
                        series: .value("Zone", "Oversold")
                    )
                    .foregroundStyle(PythiaTheme.profit.opacity(0.08))
                }

                // Upper line (70)
                RuleMark(y: .value("Overbought", 70))
                    .foregroundStyle(PythiaTheme.loss.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [6, 3]))
                    .annotation(position: .trailing, spacing: 4) {
                        Text("70")
                            .font(.system(size: 9, weight: .medium))
                            .foregroundColor(PythiaTheme.loss.opacity(0.8))
                    }

                // Lower line (30)
                RuleMark(y: .value("Oversold", 30))
                    .foregroundStyle(PythiaTheme.profit.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [6, 3]))
                    .annotation(position: .trailing, spacing: 4) {
                        Text("30")
                            .font(.system(size: 9, weight: .medium))
                            .foregroundColor(PythiaTheme.profit.opacity(0.8))
                    }

                // Middle line (50)
                RuleMark(y: .value("Middle", 50))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    .lineStyle(StrokeStyle(lineWidth: 0.5, dash: [2, 2]))

                // RSI line
                ForEach(points) { p in
                    if let rsi = p.rsi {
                        LineMark(
                            x: .value("Date", p.date),
                            y: .value("RSI", rsi),
                            series: .value("Series", "RSI")
                        )
                        .foregroundStyle(.orange)
                        .lineStyle(StrokeStyle(lineWidth: 2))
                    }
                }
            }
            .chartYScale(domain: 0...100)
            .chartYAxis {
                AxisMarks(position: .trailing, values: [0, 30, 50, 70, 100]) { value in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.12))
                    AxisValueLabel {
                        if let v = value.as(Int.self) {
                            Text("\(v)")
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundStyle(PythiaTheme.textSecondary)
                        }
                    }
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 8)) { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.08))
                    AxisValueLabel()
                        .font(.system(size: 10))
                        .foregroundStyle(PythiaTheme.textTertiary)
                }
            }
            .chartLegend(.hidden)
            .chartOverlay { _ in
                chartHoverOverlay(dataCount: points.count)
            }
            .frame(height: 140)
        }
    }

    // MARK: - Data Loading

    private func loadTA() async {
        isLoading = true
        errorMessage = nil
        do {
            ta = try await db.fetchTechnicalAnalysis(
                symbol: symbol,
                period: period,
                macdFast: macdFast, macdSlow: macdSlow, macdSignal: macdSignal,
                rsiPeriod: rsiPeriod,
                smaPeriods: "\(sma1),\(sma2)",
                emaPeriods: "12,26",
                bbPeriod: bbPeriod, bbStd: bbStd
            )
        } catch {
            errorMessage = "Failed to load TA: \(error.localizedDescription)"
        }
        isLoading = false
    }

    // MARK: - Point Builders

    private func buildPricePoints(_ ta: TechnicalAnalysisResponse) -> [PricePoint] {
        let smaKey1 = String(sma1)
        let smaKey2 = String(sma2)
        let sma1Arr = ta.sma[smaKey1]
        let sma2Arr = ta.sma[smaKey2]
        let ema1Arr = ta.ema["12"]
        let ema2Arr = ta.ema["26"]

        return ta.dates.enumerated().compactMap { i, dateStr in
            PricePoint(
                date: dateStr,
                open: ta.ohlcv.open[i],
                high: ta.ohlcv.high[i],
                low: ta.ohlcv.low[i],
                close: ta.ohlcv.close[i],
                sma1: sma1Arr?[safe: i] ?? nil,
                sma2: sma2Arr?[safe: i] ?? nil,
                ema1: ema1Arr?[safe: i] ?? nil,
                ema2: ema2Arr?[safe: i] ?? nil,
                bbUpper: ta.bollinger.upper[safe: i] ?? nil,
                bbMiddle: ta.bollinger.middle[safe: i] ?? nil,
                bbLower: ta.bollinger.lower[safe: i] ?? nil
            )
        }
    }

    private func buildVolumePoints(_ ta: TechnicalAnalysisResponse) -> [VolumePoint] {
        ta.dates.enumerated().map { i, dateStr in
            let isUp = i == 0 || ta.ohlcv.close[i] >= ta.ohlcv.close[max(0, i - 1)]
            return VolumePoint(date: dateStr, volume: ta.ohlcv.volume[i], isUp: isUp)
        }
    }

    private func buildMACDPoints(_ ta: TechnicalAnalysisResponse) -> [MACDPoint] {
        ta.dates.enumerated().compactMap { i, dateStr in
            MACDPoint(
                date: dateStr,
                macd: ta.macd.macd[safe: i] ?? nil,
                signal: ta.macd.signal[safe: i] ?? nil,
                histogram: ta.macd.histogram[safe: i] ?? nil
            )
        }
    }

    private func buildRSIPoints(_ ta: TechnicalAnalysisResponse) -> [RSIPoint] {
        ta.dates.enumerated().compactMap { i, dateStr in
            RSIPoint(date: dateStr, rsi: ta.rsi.values[safe: i] ?? nil)
        }
    }
}

// MARK: - Data Point Structs

private struct PricePoint: Identifiable {
    let date: String
    let open: Double
    let high: Double
    let low: Double
    let close: Double
    let sma1: Double?
    let sma2: Double?
    let ema1: Double?
    let ema2: Double?
    let bbUpper: Double?
    let bbMiddle: Double?
    let bbLower: Double?

    var id: String { date }
    var isUp: Bool { close >= open }
}

private struct VolumePoint: Identifiable {
    let date: String
    let volume: Int
    let isUp: Bool
    var id: String { date }
}

private struct MACDPoint: Identifiable {
    let date: String
    let macd: Double?
    let signal: Double?
    let histogram: Double?
    var id: String { date }
}

private struct RSIPoint: Identifiable {
    let date: String
    let rsi: Double?
    var id: String { date }
}

// MARK: - Period Pill (Webull-style)

private struct PeriodPill: View {
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: 12, weight: isSelected ? .bold : .medium))
                .foregroundColor(isSelected ? PythiaTheme.backgroundDark : PythiaTheme.textSecondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 5)
                .background(isSelected ? PythiaTheme.accentGold : Color.clear)
                .cornerRadius(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(isSelected ? Color.clear : PythiaTheme.textTertiary.opacity(0.3), lineWidth: 0.5)
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Indicator Toggle Button

private struct IndicatorToggle: View {
    let label: String
    @Binding var isOn: Bool
    let color: Color

    var body: some View {
        Button {
            isOn.toggle()
        } label: {
            HStack(spacing: 4) {
                Circle()
                    .fill(isOn ? color : PythiaTheme.textTertiary.opacity(0.3))
                    .frame(width: 8, height: 8)
                Text(label)
                    .font(.system(size: 12, weight: isOn ? .semibold : .regular))
                    .foregroundColor(isOn ? PythiaTheme.textPrimary : PythiaTheme.textTertiary)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(isOn ? color.opacity(0.15) : PythiaTheme.surfaceBackground.opacity(0.5))
            .cornerRadius(12)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Safe Array Subscript

extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
