//
//  MarketOverviewView.swift
//  Pythia — Market Overview with Watchlist Cards
//

import SwiftUI
import Charts

struct MarketOverviewView: View {
    @EnvironmentObject var db: DatabaseService

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
                                Task { await loadWatchlistQuotes() }
                            }
                            ForEach(watchlists) { wl in
                                FilterPill(label: wl.name, isSelected: selectedWatchlistId == wl.watchlistId) {
                                    selectedWatchlistId = wl.watchlistId
                                    Task { await loadWatchlistQuotes() }
                                }
                            }
                        }
                    }
                }

                // Watchlist Cards
                if !watchlistQuotes.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Watchlist")
                            .font(PythiaTheme.headline())
                            .foregroundColor(PythiaTheme.textSecondary)

                        LazyVGrid(columns: [
                            GridItem(.adaptive(minimum: 200, maximum: 260), spacing: 12)
                        ], spacing: 12) {
                            ForEach(watchlistQuotes) { wq in
                                WatchlistStockCard(
                                    quote: wq,
                                    isSelected: selectedCardSymbol == wq.symbol
                                )
                                .onTapGesture { selectCard(wq.symbol) }
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
            await loadWatchlists()
            await loadWatchlistQuotes()
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
                await loadWatchlistQuotes()
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

    private func loadWatchlistQuotes() async {
        isLoadingWatchlist = true
        do {
            watchlistQuotes = try await db.fetchWatchlistQuotes(watchlistId: selectedWatchlistId)
        } catch {}
        isLoadingWatchlist = false
    }

    private func loadWatchlists() async {
        do {
            watchlists = try await db.fetchWatchlists()
            // Default to "Thai Stocks" watchlist
            if selectedWatchlistId == nil,
               let thai = watchlists.first(where: { $0.name == "Thai Stocks" }) {
                selectedWatchlistId = thai.watchlistId
            }
        } catch {}
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
