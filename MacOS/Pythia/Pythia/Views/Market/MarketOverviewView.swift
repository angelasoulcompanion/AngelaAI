//
//  MarketOverviewView.swift
//  Pythia — Market Overview with Watchlist Cards
//

import SwiftUI
import Charts
import os.log

struct MarketOverviewView: View {
    @EnvironmentObject var db: DatabaseService
    @EnvironmentObject var backend: BackendManager

    @State private var searchText = ""
    @State private var quote: StockQuote?
    @State private var isSearching = false
    @State private var errorMessage: String?

    // Watchlist quotes + filter
    @State private var watchlistQuotes: [WatchlistQuote] = []
    @State private var isLoadingWatchlist = true
    @State private var watchlists: [Watchlist] = []
    @State private var selectedWatchlistId: String? = nil  // nil = All
    @State private var selectedCardSymbol: String?
    @State private var selectedCardQuote: StockQuote?
    @State private var isLoadingCardQuote = false

    // Background refresh
    @State private var isRefreshing = false

    // Horizontal scroll navigation
    @State private var scrollTarget: String?
    @State private var scrollIndex: Int = 0

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                // Header + Search
                HStack {
                    Text("Market Overview")
                        .font(PythiaTheme.title())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Spacer()
                }

                // Search bar
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(PythiaTheme.textTertiary)
                    TextField("Search symbol (e.g., AOT.BK, AAPL)", text: $searchText)
                        .textFieldStyle(.plain)
                        .foregroundColor(PythiaTheme.textPrimary)
                        .onSubmit { searchSymbol() }
                    if isSearching {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }
                .padding(12)
                .background(PythiaTheme.surfaceBackground)
                .cornerRadius(PythiaTheme.smallCornerRadius)

                if let error = errorMessage {
                    Text(error)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.errorRed)
                }

                // Watchlist filter pills
                if !watchlists.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            FilterPill(label: "All", isSelected: selectedWatchlistId == nil) {
                                selectedWatchlistId = nil
                                Task {
                                    await loadWatchlistQuotesCached()
                                    await refreshWatchlistQuotes()
                                }
                            }
                            ForEach(watchlists) { wl in
                                FilterPill(label: wl.name, isSelected: selectedWatchlistId == wl.watchlistId) {
                                    selectedWatchlistId = wl.watchlistId
                                    Task {
                                        await loadWatchlistQuotesCached()
                                        await refreshWatchlistQuotes()
                                    }
                                }
                            }
                        }
                    }
                }

                // Watchlist Cards (streaming-style horizontal scroll, 2 rows)
                if !watchlistQuotes.isEmpty {
                    let half = (watchlistQuotes.count + 1) / 2
                    let topRow = Array(watchlistQuotes.prefix(half))
                    let bottomRow = Array(watchlistQuotes.dropFirst(half))

                    VStack(alignment: .leading, spacing: 12) {
                        HStack(spacing: 8) {
                            Text("Watchlist")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textSecondary)
                            if isRefreshing {
                                HStack(spacing: 4) {
                                    ProgressView()
                                        .scaleEffect(0.6)
                                    Text("Updating prices...")
                                        .font(.system(size: 11))
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }
                            }
                        }

                        ZStack {
                            ScrollViewReader { proxy in
                                ScrollView(.horizontal, showsIndicators: false) {
                                    VStack(alignment: .leading, spacing: 12) {
                                        HStack(spacing: 12) {
                                            ForEach(topRow) { wq in
                                                WatchlistStockCard(
                                                    quote: wq,
                                                    isSelected: selectedCardSymbol == wq.symbol
                                                )
                                                .frame(width: 240)
                                                .id("top_\(wq.symbol)")
                                                .onTapGesture { selectCard(wq.symbol) }
                                            }
                                        }
                                        if !bottomRow.isEmpty {
                                            HStack(spacing: 12) {
                                                ForEach(bottomRow) { wq in
                                                    WatchlistStockCard(
                                                        quote: wq,
                                                        isSelected: selectedCardSymbol == wq.symbol
                                                    )
                                                    .frame(width: 240)
                                                    .id("bot_\(wq.symbol)")
                                                    .onTapGesture { selectCard(wq.symbol) }
                                                }
                                            }
                                        }
                                    }
                                }
                                .onChange(of: scrollTarget) { _, target in
                                    guard let target else { return }
                                    withAnimation(.easeInOut(duration: 0.3)) {
                                        proxy.scrollTo(target, anchor: .leading)
                                    }
                                    scrollTarget = nil
                                }
                            }

                            // Left arrow
                            HStack {
                                ScrollArrowButton(direction: .left) {
                                    scrollToNeighbor(topRow, offset: -3)
                                }
                                Spacer()
                                ScrollArrowButton(direction: .right) {
                                    scrollToNeighbor(topRow, offset: 3)
                                }
                            }
                        }
                    }
                } else if isLoadingWatchlist {
                    LoadingView("Loading watchlist...")
                } else if quote == nil {
                    EmptyStateView(
                        icon: "globe",
                        title: "Search for a Symbol",
                        message: "Enter a stock symbol to view real-time market data.\nExamples: AOT.BK, PTT.BK, AAPL, TSLA"
                    )
                }

                // Detail card (from search OR card tap) — always below watchlist
                if isLoadingCardQuote {
                    LoadingView("Loading \(selectedCardSymbol ?? "")...")
                }
                if let detail = activeDetailQuote {
                    QuoteCardView(quote: detail)

                    // Financial Outlook
                    FinancialOutlookView(symbol: detail.symbol, currentPrice: detail.currentPrice)

                    // Technical Analysis charts
                    TechnicalChartView(symbol: detail.symbol)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            // Wait for backend to be connected before fetching
            while !backend.isConnected {
                try? await Task.sleep(nanoseconds: 500_000_000) // 0.5s
            }
            await loadWatchlists()

            // Phase 1: Show cached data instantly (from DB, no Yahoo calls)
            await loadWatchlistQuotesCached()

            // Phase 2: Refresh with fresh data in background
            await refreshWatchlistQuotes()
        }
    }

    /// Show card-tap detail if selected, otherwise show search result
    private var activeDetailQuote: StockQuote? {
        selectedCardQuote ?? quote
    }

    private func searchSymbol() {
        guard !searchText.isEmpty else { return }
        isSearching = true
        errorMessage = nil
        selectedCardSymbol = nil
        selectedCardQuote = nil
        Task {
            do {
                let symbol = searchText.trimmingCharacters(in: .whitespaces)
                quote = try await db.fetchQuote(symbol: symbol)

                // Auto-add to default watchlist so it shows as a card next time
                await autoAddToWatchlist(symbol: symbol)

                // Refresh watchlist cards immediately
                await loadWatchlistQuotesCached()
                await refreshWatchlistQuotes()
            } catch {
                errorMessage = "Failed to fetch quote: \(error.localizedDescription)"
                quote = nil
            }
            isSearching = false
        }
    }

    /// Ensure a default "My Watchlist" exists and add the symbol to it
    private func autoAddToWatchlist(symbol: String) async {
        do {
            let watchlists = try await db.fetchWatchlists()
            let watchlistId: String

            if let first = watchlists.first {
                watchlistId = first.watchlistId
            } else {
                // Create a default watchlist
                let created = try await db.createWatchlist(name: "My Watchlist", description: "Auto-created from search")
                watchlistId = created.watchlistId
            }

            _ = try await db.addWatchlistItemBySymbol(watchlistId: watchlistId, symbol: symbol)
        } catch {
            // Silently ignore — search still works even if watchlist save fails
        }
    }

    private func selectCard(_ symbol: String) {
        if selectedCardSymbol == symbol {
            // Deselect on second tap
            selectedCardSymbol = nil
            selectedCardQuote = nil
            return
        }
        selectedCardSymbol = symbol
        selectedCardQuote = nil
        quote = nil
        isLoadingCardQuote = true
        Task {
            do {
                selectedCardQuote = try await db.fetchQuote(symbol: symbol)
            } catch {
                errorMessage = "Failed to load \(symbol)"
            }
            isLoadingCardQuote = false
        }
    }

    /// Phase 1: Load from DB cache — instant, no Yahoo calls
    private func loadWatchlistQuotesCached() async {
        isLoadingWatchlist = true
        do {
            let cached = try await db.fetchWatchlistQuotesCached(watchlistId: selectedWatchlistId)
            if !cached.isEmpty {
                watchlistQuotes = cached
                debugLog("[MarketOverview] Cached \(cached.count) quotes for wl=\(selectedWatchlistId ?? "all")")
            }
        } catch {
            debugLog("[MarketOverview] loadCached ERROR: \(error)")
        }
        isLoadingWatchlist = false
    }

    /// Phase 2: Fetch fresh data via batch download, update cards when ready
    private func refreshWatchlistQuotes() async {
        isRefreshing = true
        do {
            let fresh = try await db.fetchWatchlistQuotes(watchlistId: selectedWatchlistId)
            watchlistQuotes = fresh
            debugLog("[MarketOverview] Refreshed \(fresh.count) quotes for wl=\(selectedWatchlistId ?? "all")")
        } catch {
            debugLog("[MarketOverview] refresh ERROR: \(error)")
        }
        isRefreshing = false
    }

    private func debugLog(_ msg: String) {
        let ts = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        let line = "[\(ts)] \(msg)\n"
        guard let dir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first else { return }
        let path = dir.appendingPathComponent("pythia_debug.log")
        if let data = line.data(using: .utf8) {
            if FileManager.default.fileExists(atPath: path.path) {
                if let fh = try? FileHandle(forWritingTo: path) {
                    fh.seekToEndOfFile()
                    fh.write(data)
                    try? fh.close()
                }
            } else {
                try? data.write(to: path)
            }
        }
    }

    /// Scroll the watchlist by `offset` cards relative to current position
    private func scrollToNeighbor(_ row: [WatchlistQuote], offset: Int) {
        guard !row.isEmpty else { return }
        scrollIndex = max(0, min(row.count - 1, scrollIndex + offset))
        scrollTarget = "top_\(row[scrollIndex].symbol)"
    }

    private func loadWatchlists() async {
        do {
            watchlists = try await db.fetchWatchlists()
            Logger().info("[MarketOverview] Loaded \(self.watchlists.count) watchlists")
            // Default to "Thai Stocks" watchlist
            if selectedWatchlistId == nil,
               let thai = watchlists.first(where: { $0.name == "Thai Stocks" }) {
                selectedWatchlistId = thai.watchlistId
                Logger().info("[MarketOverview] Auto-selected Thai Stocks: \(thai.watchlistId)")
            }
        } catch {
            Logger().error("[MarketOverview] loadWatchlists error: \(error.localizedDescription)")
        }
    }
}

// MARK: - Watchlist Stock Card (like the reference image)

struct WatchlistStockCard: View {
    let quote: WatchlistQuote
    var isSelected: Bool = false

    private var isPositive: Bool { (quote.change ?? 0) >= 0 }
    private var changeColor: Color { PythiaTheme.profitLossColor(quote.change ?? 0) }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Row 1: Symbol + Change%
            HStack {
                HStack(spacing: 4) {
                    Image(systemName: isPositive ? "arrowtriangle.up.fill" : "arrowtriangle.down.fill")
                        .font(.system(size: 9))
                        .foregroundColor(changeColor)
                    Text(quote.symbol)
                        .font(.system(size: 14, weight: .bold, design: .monospaced))
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                Spacer()
                if let pct = quote.changePercent {
                    Text(String(format: "%+.2f%%", pct))
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(changeColor)
                }
            }

            // Row 2: Name + Change value
            HStack {
                Text(quote.name ?? "")
                    .font(.system(size: 11))
                    .foregroundColor(PythiaTheme.textTertiary)
                    .lineLimit(1)
                Spacer()
                if let chg = quote.change {
                    Text(String(format: "%+.2f", chg))
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(changeColor)
                }
            }

            // Sparkline chart
            if quote.sparkline.count >= 2 {
                SparklineView(data: quote.sparkline, color: changeColor)
                    .frame(height: 32)
            } else {
                Rectangle()
                    .fill(PythiaTheme.textTertiary.opacity(0.1))
                    .frame(height: 32)
                    .cornerRadius(4)
            }

            // Price (large)
            if let price = quote.currentPrice {
                Text(formatPrice(price, currency: quote.currency))
                    .font(.system(size: 22, weight: .bold, design: .rounded))
                    .foregroundColor(PythiaTheme.textPrimary)
                    .frame(maxWidth: .infinity, alignment: .center)
            } else {
                Text("—")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(PythiaTheme.textTertiary)
                    .frame(maxWidth: .infinity, alignment: .center)
            }

            // Volume bar
            if let vol = quote.volume, vol > 0 {
                HStack(spacing: 4) {
                    Image(systemName: "chart.bar.fill")
                        .font(.system(size: 8))
                        .foregroundColor(PythiaTheme.textTertiary.opacity(0.6))
                    Text("Vol")
                        .font(.system(size: 9))
                        .foregroundColor(PythiaTheme.textTertiary.opacity(0.6))
                    Text(MarketDataService.shared.formatVolume(vol))
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                .frame(maxWidth: .infinity)
            }
        }
        .padding(12)
        .background(PythiaTheme.surfaceBackground)
        .cornerRadius(PythiaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: PythiaTheme.cornerRadius)
                .stroke(isSelected ? PythiaTheme.accentGold : Color.clear, lineWidth: 2)
        )
        .contentShape(Rectangle())
    }

    private func formatPrice(_ price: Double, currency: String?) -> String {
        let curr = currency ?? ""
        if curr == "THB" {
            return String(format: "฿%.2f", price)
        } else if curr == "USD" {
            return String(format: "$%.2f", price)
        }
        return String(format: "%.2f", price)
    }
}

// MARK: - Sparkline

struct SparklineView: View {
    let data: [Double]
    let color: Color

    var body: some View {
        GeometryReader { geo in
            let minVal = data.min() ?? 0
            let maxVal = data.max() ?? 1
            let range = max(maxVal - minVal, 0.01)
            let stepX = geo.size.width / CGFloat(max(data.count - 1, 1))

            // Dashed midline
            let midY = geo.size.height / 2
            Path { path in
                path.move(to: CGPoint(x: 0, y: midY))
                path.addLine(to: CGPoint(x: geo.size.width, y: midY))
            }
            .stroke(PythiaTheme.textTertiary.opacity(0.3), style: StrokeStyle(lineWidth: 0.5, dash: [3, 3]))

            // Sparkline
            Path { path in
                for (i, val) in data.enumerated() {
                    let x = CGFloat(i) * stepX
                    let y = geo.size.height - ((CGFloat(val - minVal) / CGFloat(range)) * geo.size.height)
                    if i == 0 { path.move(to: CGPoint(x: x, y: y)) }
                    else { path.addLine(to: CGPoint(x: x, y: y)) }
                }
            }
            .stroke(color, lineWidth: 1.5)
        }
    }
}

// MARK: - Quote Card (for search result)

struct QuoteCardView: View {
    let quote: StockQuote

    var body: some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(quote.symbol)
                        .font(.system(size: 28, weight: .bold, design: .monospaced))
                        .foregroundColor(PythiaTheme.accentGold)
                    Text(quote.name ?? "")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 4) {
                    Text(String(format: "%.2f", quote.currentPrice ?? 0))
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(PythiaTheme.textPrimary)
                    HStack(spacing: 4) {
                        Image(systemName: (quote.change ?? 0) >= 0 ? "arrow.up.right" : "arrow.down.right")
                        Text(String(format: "%+.2f (%.2f%%)", quote.change ?? 0, quote.changePercent ?? 0))
                    }
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(PythiaTheme.profitLossColor(quote.change ?? 0))
                }
            }

            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 16) {
                QuoteMetric(label: "Open", value: formatPrice(quote.openPrice))
                QuoteMetric(label: "Day High", value: formatPrice(quote.dayHigh))
                QuoteMetric(label: "Day Low", value: formatPrice(quote.dayLow))
                QuoteMetric(label: "Volume", value: MarketDataService.shared.formatVolume(quote.volume))
                QuoteMetric(label: "Market Cap", value: MarketDataService.shared.formatMarketCap(quote.marketCap))
                QuoteMetric(label: "P/E Ratio", value: quote.peRatio != nil ? String(format: "%.2f", quote.peRatio!) : "N/A")
                QuoteMetric(label: "52W High", value: formatPrice(quote.fiftyTwoWeekHigh))
                QuoteMetric(label: "52W Low", value: formatPrice(quote.fiftyTwoWeekLow))
                QuoteMetric(label: "Dividend Yield", value: quote.dividendYield != nil ? String(format: "%.2f%%", quote.dividendYield!) : "N/A")
                QuoteMetric(label: "Beta", value: quote.beta != nil ? String(format: "%.2f", quote.beta!) : "N/A")
                QuoteMetric(label: "Avg Volume", value: MarketDataService.shared.formatVolume(quote.avgVolume))
                QuoteMetric(label: "Exchange", value: quote.exchange ?? "N/A")
            }
        }
        .padding(PythiaTheme.largeSpacing)
        .pythiaCard()
    }

    private func formatPrice(_ value: Double?) -> String {
        guard let value = value else { return "N/A" }
        return String(format: "%.2f", value)
    }
}

struct QuoteMetric: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(.system(size: 14, weight: .medium, design: .monospaced))
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }
}

// MARK: - Scroll Arrow Button (Netflix/Disney+ style)

private struct ScrollArrowButton: View {
    enum Direction { case left, right }

    let direction: Direction
    let action: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            ZStack {
                // Gradient fade edge
                LinearGradient(
                    colors: direction == .left
                        ? [PythiaTheme.backgroundDark, PythiaTheme.backgroundDark.opacity(0)]
                        : [PythiaTheme.backgroundDark.opacity(0), PythiaTheme.backgroundDark],
                    startPoint: .leading,
                    endPoint: .trailing
                )
                .frame(width: 48)

                Image(systemName: direction == .left ? "chevron.left" : "chevron.right")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(PythiaTheme.textSecondary.opacity(isHovered ? 1.0 : 0.5))
            }
        }
        .frame(width: 48)
        .buttonStyle(.plain)
        .onHover { hovering in
            withAnimation(.easeInOut(duration: 0.15)) { isHovered = hovering }
        }
    }
}

// MARK: - Filter Pill

struct FilterPill: View {
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: 13, weight: isSelected ? .bold : .medium))
                .foregroundColor(isSelected ? PythiaTheme.backgroundDark : PythiaTheme.textSecondary)
                .padding(.horizontal, 14)
                .padding(.vertical, 6)
                .background(isSelected ? PythiaTheme.accentGold : PythiaTheme.surfaceBackground)
                .cornerRadius(16)
        }
        .buttonStyle(.plain)
    }
}
