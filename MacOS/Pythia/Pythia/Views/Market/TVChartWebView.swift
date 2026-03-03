//
//  TVChartWebView.swift
//  Pythia — TradingView Lightweight Charts v5 WebView Bridge
//

import SwiftUI
import WebKit

// MARK: - Bridge (shared state between TechnicalChartView and TVChartWebView)

class TVChartBridge: ObservableObject {
    weak var webView: WKWebView?
    var isReady = false
    var pendingPayload: String?

    func send(_ js: String) {
        webView?.evaluateJavaScript(js, completionHandler: nil)
    }

    func loadData(_ json: String) {
        if isReady, webView != nil {
            send("loadChartData(\(json))")
        } else {
            pendingPayload = json
        }
    }

    /// Toggle overlay series (SMA, EMA, Bollinger)
    func toggleOverlay(_ keys: [String], visible: Bool) {
        let js = keys.map { "toggleSeries('\($0)', \(visible))" }.joined(separator: "; ")
        send(js)
    }

    /// Rebuild sub-panes (Volume, MACD, RSI)
    func rebuildPanes(showVolume: Bool, showMACD: Bool, showRSI: Bool) {
        send("rebuildSubPanes(\(showVolume), \(showMACD), \(showRSI))")
    }
}

// MARK: - NSViewRepresentable

struct TVChartWebView: NSViewRepresentable {
    @ObservedObject var bridge: TVChartBridge
    var onCrosshairMove: (Int?) -> Void

    func makeNSView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let handler = WeakMessageHandler(delegate: context.coordinator)
        config.userContentController.add(handler, name: "pythia")

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.setValue(false, forKey: "drawsBackground")

        bridge.webView = webView

        let html = Self.cachedHTML
        webView.loadHTMLString(html, baseURL: nil)

        return webView
    }

    func updateNSView(_ nsView: WKWebView, context: Context) {}

    static func dismantleNSView(_ nsView: WKWebView, coordinator: Coordinator) {
        nsView.configuration.userContentController.removeScriptMessageHandler(forName: "pythia")
        // Reset bridge so next makeNSView can re-init properly
        coordinator.bridge.isReady = false
        coordinator.bridge.webView = nil
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(bridge: bridge, onCrosshairMove: onCrosshairMove)
    }

    // MARK: - Coordinator

    class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        let bridge: TVChartBridge
        let onCrosshairMove: (Int?) -> Void

        init(bridge: TVChartBridge, onCrosshairMove: @escaping (Int?) -> Void) {
            self.bridge = bridge
            self.onCrosshairMove = onCrosshairMove
        }

        func userContentController(
            _ userContentController: WKUserContentController,
            didReceive message: WKScriptMessage
        ) {
            guard let body = message.body as? [String: Any],
                  let type = body["type"] as? String else { return }

            switch type {
            case "ready":
                bridge.isReady = true
                if let payload = bridge.pendingPayload {
                    bridge.send("loadChartData(\(payload))")
                    bridge.pendingPayload = nil
                }
            case "crosshair":
                let index = body["index"] as? Int
                DispatchQueue.main.async { self.onCrosshairMove(index) }
            case "crosshairLeave":
                DispatchQueue.main.async { self.onCrosshairMove(nil) }
            default:
                break
            }
        }
    }

    // MARK: - Weak Message Handler (prevent WKWebView retain cycle)

    class WeakMessageHandler: NSObject, WKScriptMessageHandler {
        weak var delegate: WKScriptMessageHandler?

        init(delegate: WKScriptMessageHandler) {
            self.delegate = delegate
        }

        func userContentController(
            _ userContentController: WKUserContentController,
            didReceive message: WKScriptMessage
        ) {
            delegate?.userContentController(userContentController, didReceive: message)
        }
    }

    // MARK: - HTML (cached — avoids re-reading 189KB JS from disk on every makeNSView)

    private static let cachedHTML: String = {
        let jsLib: String
        if let path = Bundle.main.path(
            forResource: "lightweight-charts.standalone.production", ofType: "js"
        ),
            let content = try? String(contentsOfFile: path, encoding: .utf8)
        {
            jsLib = content
        } else {
            jsLib = "console.error('lightweight-charts.js not found in bundle');"
        }

        return """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { background: #0F172A; overflow: hidden; }
            #chart { width: 100%; height: 100vh; }
        </style>
        </head>
        <body>
        <div id="chart"></div>
        <script>\(jsLib)</script>
        <script>
        \(chartJS)
        </script>
        </body>
        </html>
        """
    }()

    // MARK: - Chart JavaScript

    private static let chartJS = """
    const { createChart, CandlestickSeries, LineSeries, HistogramSeries, CrosshairMode, LineStyle } = LightweightCharts;

    let chart, candleSeries;
    let sma1Series, sma2Series, ema1Series, ema2Series;
    let bbUpperSeries, bbMiddleSeries, bbLowerSeries;
    let volumeSeries, macdHistSeries, macdLineSeries, macdSignalSeries, rsiSeries;
    let currentPayload = null;
    let dateIndex = {};
    let currentPriceLine = null;

    // === Initialize chart ===
    const container = document.getElementById('chart');

    chart = createChart(container, {
        layout: {
            background: { color: '#0F172A' },
            textColor: '#94A3B8',
            fontSize: 11,
            fontFamily: '-apple-system, BlinkMacSystemFont, system-ui',
        },
        grid: {
            vertLines: { color: '#1e222d' },
            horzLines: { color: '#1e222d' },
        },
        crosshair: {
            mode: CrosshairMode.Normal,
            vertLine: {
                color: 'rgba(148, 163, 184, 0.4)',
                style: LineStyle.Dashed,
                width: 1,
                labelVisible: true,
            },
            horzLine: {
                color: 'rgba(148, 163, 184, 0.4)',
                style: LineStyle.Dashed,
                width: 1,
                labelVisible: true,
            },
        },
        rightPriceScale: {
            borderColor: '#334155',
            scaleMargins: { top: 0.05, bottom: 0.05 },
        },
        timeScale: {
            borderColor: '#334155',
            rightOffset: 5,
            timeVisible: false,
        },
    });

    // === Pane 0: Price + Overlays ===
    candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#059669',
        downColor: '#DC2626',
        borderUpColor: '#059669',
        borderDownColor: '#DC2626',
        wickUpColor: '#059669',
        wickDownColor: '#DC2626',
    });

    sma1Series = chart.addSeries(LineSeries, {
        color: '#F59E0B',
        lineWidth: 1.5,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    sma2Series = chart.addSeries(LineSeries, {
        color: '#D97706',
        lineWidth: 1.5,
        lineStyle: LineStyle.Dashed,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    ema1Series = chart.addSeries(LineSeries, {
        color: '#22D3EE',
        lineWidth: 1.5,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    ema2Series = chart.addSeries(LineSeries, {
        color: '#22D3EE',
        lineWidth: 1.5,
        lineStyle: LineStyle.Dashed,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    bbUpperSeries = chart.addSeries(LineSeries, {
        color: '#A78BFA',
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    bbMiddleSeries = chart.addSeries(LineSeries, {
        color: 'rgba(167, 139, 250, 0.4)',
        lineWidth: 0.5,
        lineStyle: LineStyle.Dotted,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    bbLowerSeries = chart.addSeries(LineSeries, {
        color: '#A78BFA',
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        lastValueVisible: false,
        priceLineVisible: false,
    });

    // === Helper: set line series data (skips nulls) ===
    function setLineData(series, dates, values) {
        if (!values) { series.setData([]); return; }
        const data = [];
        for (let i = 0; i < dates.length; i++) {
            if (values[i] != null) {
                data.push({ time: dates[i], value: values[i] });
            }
        }
        series.setData(data);
    }

    // === Helper: build volume data with up/down colors ===
    function buildVolumeData(payload) {
        const data = [];
        for (let i = 0; i < payload.dates.length; i++) {
            const isUp = i === 0 || payload.ohlcv.close[i] >= payload.ohlcv.close[i - 1];
            data.push({
                time: payload.dates[i],
                value: payload.ohlcv.volume[i],
                color: isUp ? 'rgba(5, 150, 105, 0.5)' : 'rgba(220, 38, 38, 0.5)',
            });
        }
        return data;
    }

    // === Helper: build MACD histogram data with colors ===
    function buildMACDHistData(payload) {
        const data = [];
        if (!payload.macdHist) return data;
        for (let i = 0; i < payload.dates.length; i++) {
            if (payload.macdHist[i] != null) {
                data.push({
                    time: payload.dates[i],
                    value: payload.macdHist[i],
                    color: payload.macdHist[i] >= 0 ? 'rgba(5, 150, 105, 0.5)' : 'rgba(220, 38, 38, 0.5)',
                });
            }
        }
        return data;
    }

    // Track current pane config for deferred height application
    let activePaneConfig = [];

    // === Rebuild sub-panes (Volume, MACD, RSI) ===
    function rebuildSubPanes(showVol, showMACD, showRSI) {
        // Remove all existing sub-pane series
        [volumeSeries, macdHistSeries, macdLineSeries, macdSignalSeries, rsiSeries].forEach(function(s) {
            if (s) { try { chart.removeSeries(s); } catch(e) {} }
        });
        volumeSeries = macdHistSeries = macdLineSeries = macdSignalSeries = rsiSeries = null;
        activePaneConfig = [];

        // Re-add enabled panes in order
        let nextPane = 1;

        if (showVol) {
            volumeSeries = chart.addSeries(HistogramSeries, {
                priceFormat: { type: 'volume' },
                priceLineVisible: false,
                lastValueVisible: false,
            }, nextPane);
            if (currentPayload) volumeSeries.setData(buildVolumeData(currentPayload));
            activePaneConfig.push({ idx: nextPane, height: 80 });
            nextPane++;
        }

        if (showMACD) {
            macdHistSeries = chart.addSeries(HistogramSeries, {
                priceLineVisible: false,
                lastValueVisible: false,
            }, nextPane);
            macdLineSeries = chart.addSeries(LineSeries, {
                color: '#3B82F6',
                lineWidth: 1.5,
                priceLineVisible: false,
                lastValueVisible: false,
            }, nextPane);
            macdSignalSeries = chart.addSeries(LineSeries, {
                color: '#F59E0B',
                lineWidth: 1.5,
                priceLineVisible: false,
                lastValueVisible: false,
            }, nextPane);
            if (currentPayload) {
                macdHistSeries.setData(buildMACDHistData(currentPayload));
                setLineData(macdLineSeries, currentPayload.dates, currentPayload.macdLine);
                setLineData(macdSignalSeries, currentPayload.dates, currentPayload.macdSignal);
            }
            // Zero line
            macdLineSeries.createPriceLine({
                price: 0,
                color: 'rgba(148, 163, 184, 0.5)',
                lineWidth: 0.5,
                lineStyle: LineStyle.Solid,
                axisLabelVisible: false,
            });
            activePaneConfig.push({ idx: nextPane, height: 150 });
            nextPane++;
        }

        if (showRSI) {
            rsiSeries = chart.addSeries(LineSeries, {
                color: '#F97316',
                lineWidth: 2,
                priceLineVisible: false,
                lastValueVisible: false,
            }, nextPane);
            if (currentPayload) {
                setLineData(rsiSeries, currentPayload.dates, currentPayload.rsi);
            }
            // Reference lines
            rsiSeries.createPriceLine({ price: 70, color: 'rgba(220, 38, 38, 0.5)', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true });
            rsiSeries.createPriceLine({ price: 50, color: 'rgba(148, 163, 184, 0.3)', lineWidth: 1, lineStyle: LineStyle.Dotted, axisLabelVisible: false });
            rsiSeries.createPriceLine({ price: 30, color: 'rgba(5, 150, 105, 0.5)', lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true });
            activePaneConfig.push({ idx: nextPane, height: 150 });
            nextPane++;
        }

        applyPaneHeights();
    }

    // === Deferred pane height application (must run after layout) ===
    function applyPaneHeights() {
        requestAnimationFrame(function() {
            const panes = chart.panes();
            activePaneConfig.forEach(function(cfg) {
                if (panes[cfg.idx]) {
                    panes[cfg.idx].setHeight(cfg.height);
                }
            });
        });
    }

    // === Load chart data (called from Swift) ===
    function loadChartData(payload) {
        currentPayload = payload;
        dateIndex = {};

        // Build candle data
        const candleData = [];
        for (let i = 0; i < payload.dates.length; i++) {
            dateIndex[payload.dates[i]] = i;
            candleData.push({
                time: payload.dates[i],
                open: payload.ohlcv.open[i],
                high: payload.ohlcv.high[i],
                low: payload.ohlcv.low[i],
                close: payload.ohlcv.close[i],
            });
        }
        candleSeries.setData(candleData);

        // Overlay series data
        setLineData(sma1Series, payload.dates, payload.sma1);
        setLineData(sma2Series, payload.dates, payload.sma2);
        setLineData(ema1Series, payload.dates, payload.ema1);
        setLineData(ema2Series, payload.dates, payload.ema2);
        setLineData(bbUpperSeries, payload.dates, payload.bbUpper);
        setLineData(bbMiddleSeries, payload.dates, payload.bbMiddle);
        setLineData(bbLowerSeries, payload.dates, payload.bbLower);

        // Overlay visibility
        const v = payload.visible || {};
        sma1Series.applyOptions({ visible: v.sma !== false });
        sma2Series.applyOptions({ visible: v.sma !== false });
        ema1Series.applyOptions({ visible: v.ema !== false });
        ema2Series.applyOptions({ visible: v.ema !== false });
        bbUpperSeries.applyOptions({ visible: v.bb !== false });
        bbMiddleSeries.applyOptions({ visible: v.bb !== false });
        bbLowerSeries.applyOptions({ visible: v.bb !== false });

        // Sub-panes
        rebuildSubPanes(v.volume !== false, v.macd !== false, v.rsi !== false);

        // Current price line
        if (currentPriceLine) {
            try { candleSeries.removePriceLine(currentPriceLine); } catch(e) {}
        }
        if (candleData.length > 0) {
            const last = candleData[candleData.length - 1];
            const prev = candleData.length > 1 ? candleData[candleData.length - 2].close : last.open;
            const isUp = last.close >= prev;
            currentPriceLine = candleSeries.createPriceLine({
                price: last.close,
                color: isUp ? '#059669' : '#DC2626',
                lineWidth: 1,
                lineStyle: LineStyle.Dashed,
                axisLabelVisible: true,
                title: '',
            });
        }

        chart.timeScale().fitContent();
        applyPaneHeights();
    }

    // === Toggle overlay series visibility (called from Swift) ===
    function toggleSeries(key, visible) {
        const map = {
            sma1: sma1Series, sma2: sma2Series,
            ema1: ema1Series, ema2: ema2Series,
            bbUpper: bbUpperSeries, bbMiddle: bbMiddleSeries, bbLower: bbLowerSeries,
        };
        if (map[key]) {
            map[key].applyOptions({ visible: visible });
        }
    }

    // === Crosshair subscription ===
    chart.subscribeCrosshairMove(function(param) {
        if (!param.time) {
            window.webkit.messageHandlers.pythia.postMessage({ type: 'crosshairLeave' });
            return;
        }
        let timeKey = param.time;
        if (typeof timeKey === 'object' && timeKey.year) {
            const m = String(timeKey.month).padStart(2, '0');
            const d = String(timeKey.day).padStart(2, '0');
            timeKey = timeKey.year + '-' + m + '-' + d;
        }
        const idx = dateIndex[timeKey];
        if (idx !== undefined) {
            window.webkit.messageHandlers.pythia.postMessage({ type: 'crosshair', index: idx });
        }
    });

    // === Resize observer (debounced — skip if dimensions unchanged) ===
    let lastW = 0, lastH = 0;
    new ResizeObserver(function() {
        const w = container.clientWidth, h = container.clientHeight;
        if (w === lastW && h === lastH) return;
        lastW = w; lastH = h;
        chart.applyOptions({ width: w, height: h });
    }).observe(container);

    // === Signal ready ===
    window.webkit.messageHandlers.pythia.postMessage({ type: 'ready' });
    """
}
