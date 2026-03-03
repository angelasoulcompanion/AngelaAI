//
//  TechnicalChartView.swift
//  Pythia — Technical Analysis Charts (TradingView Lightweight Charts v5)
//

import SwiftUI
import WebKit

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

    // Hover state
    @State private var hoverIndex: Int?

    // WebView bridge
    @StateObject private var bridge = TVChartBridge()

    /// Dynamic chart height based on which panes are visible
    private var chartHeight: CGFloat {
        380 + (showVolume ? 80 : 0) + (showMACD ? 150 : 0) + (showRSI ? 150 : 0)
    }

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

            // Show loading only on first load (ta still nil)
            if isLoading && ta == nil {
                LoadingView("Computing indicators...")
            }

            if let error = errorMessage, ta == nil {
                Text(error)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.errorRed)
            }

            // Keep web view alive once ta has been loaded — never destroy on period change
            if ta != nil {
                TVChartWebView(bridge: bridge, onCrosshairMove: { idx in hoverIndex = idx })
                    .frame(height: chartHeight)
                    .cornerRadius(PythiaTheme.smallCornerRadius)
                    .opacity(isLoading ? 0.4 : 1.0)
                    .animation(.easeInOut(duration: 0.15), value: isLoading)
            }
        }
        .padding(PythiaTheme.largeSpacing)
        .pythiaCard()
        .task { await loadTA() }
        // Overlay toggle listeners
        .onChange(of: showSMA) { _, newValue in
            bridge.toggleOverlay(["sma1", "sma2"], visible: newValue)
        }
        .onChange(of: showEMA) { _, newValue in
            bridge.toggleOverlay(["ema1", "ema2"], visible: newValue)
        }
        .onChange(of: showBollinger) { _, newValue in
            bridge.toggleOverlay(["bbUpper", "bbMiddle", "bbLower"], visible: newValue)
        }
        // Sub-pane toggle listeners — rebuild panes
        .onChange(of: showVolume) { _, _ in sendPaneState() }
        .onChange(of: showMACD) { _, _ in sendPaneState() }
        .onChange(of: showRSI) { _, _ in sendPaneState() }
    }

    /// Tell JS to rebuild sub-panes based on current toggle state
    private func sendPaneState() {
        bridge.rebuildPanes(showVolume: showVolume, showMACD: showMACD, showRSI: showRSI)
    }

    // MARK: - Inline OHLC (TradingView-style header)

    private func inlineOHLC(_ ta: TechnicalAnalysisResponse, index: Int) -> some View {
        let o = ta.ohlcv.open[index]
        let h = ta.ohlcv.high[index]
        let l = ta.ohlcv.low[index]
        let c = ta.ohlcv.close[index]
        let isUp = c >= o
        let changeColor = isUp ? PythiaTheme.profit : PythiaTheme.loss

        // Change from previous close (TradingView-style: -8.77 (-3.21%))
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

    // MARK: - Data Loading

    private func loadTA() async {
        isLoading = true
        errorMessage = nil
        do {
            let result = try await db.fetchTechnicalAnalysis(
                symbol: symbol,
                period: period,
                macdFast: macdFast, macdSlow: macdSlow, macdSignal: macdSignal,
                rsiPeriod: rsiPeriod,
                smaPeriods: "\(sma1),\(sma2)",
                emaPeriods: "12,26",
                bbPeriod: bbPeriod, bbStd: bbStd
            )
            ta = result
            if let json = buildChartPayload(result) {
                bridge.loadData(json)
            }
        } catch {
            errorMessage = "Failed to load TA: \(error.localizedDescription)"
        }
        isLoading = false
    }

    // MARK: - Chart Payload Builder

    /// Serialize TechnicalAnalysisResponse to JSON for JS loadChartData()
    private func buildChartPayload(_ ta: TechnicalAnalysisResponse) -> String? {
        let smaKey1 = String(sma1)
        let smaKey2 = String(sma2)

        func nullableArray(_ arr: [Double?]) -> [Any] {
            arr.map { val -> Any in
                if let v = val { return v }
                return NSNull()
            }
        }

        let payload: [String: Any] = [
            "dates": ta.dates,
            "ohlcv": [
                "open": ta.ohlcv.open,
                "high": ta.ohlcv.high,
                "low": ta.ohlcv.low,
                "close": ta.ohlcv.close,
                "volume": ta.ohlcv.volume,
            ],
            "sma1": nullableArray(ta.sma[smaKey1] ?? []),
            "sma2": nullableArray(ta.sma[smaKey2] ?? []),
            "ema1": nullableArray(ta.ema["12"] ?? []),
            "ema2": nullableArray(ta.ema["26"] ?? []),
            "bbUpper": nullableArray(ta.bollinger.upper),
            "bbMiddle": nullableArray(ta.bollinger.middle),
            "bbLower": nullableArray(ta.bollinger.lower),
            "macdLine": nullableArray(ta.macd.macd),
            "macdSignal": nullableArray(ta.macd.signal),
            "macdHist": nullableArray(ta.macd.histogram),
            "rsi": nullableArray(ta.rsi.values),
            "visible": [
                "sma": showSMA,
                "ema": showEMA,
                "bb": showBollinger,
                "volume": showVolume,
                "macd": showMACD,
                "rsi": showRSI,
            ],
        ]

        guard let data = try? JSONSerialization.data(withJSONObject: payload),
              let json = String(data: data, encoding: .utf8)
        else { return nil }
        return json
    }
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
