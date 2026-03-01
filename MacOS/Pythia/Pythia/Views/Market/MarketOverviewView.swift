//
//  MarketOverviewView.swift
//  Pythia
//

import SwiftUI

struct MarketOverviewView: View {
    @EnvironmentObject var db: DatabaseService
    @State private var searchText = ""
    @State private var quote: StockQuote?
    @State private var isSearching = false
    @State private var errorMessage: String?

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

                // Quote display
                if let quote = quote {
                    QuoteCardView(quote: quote)
                } else {
                    EmptyStateView(
                        icon: "globe",
                        title: "Search for a Symbol",
                        message: "Enter a stock symbol to view real-time market data.\nExamples: AOT.BK, PTT.BK, AAPL, TSLA"
                    )
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func searchSymbol() {
        guard !searchText.isEmpty else { return }
        isSearching = true
        errorMessage = nil
        Task {
            do {
                quote = try await db.fetchQuote(symbol: searchText.trimmingCharacters(in: .whitespaces))
            } catch {
                errorMessage = "Failed to fetch quote: \(error.localizedDescription)"
                quote = nil
            }
            isSearching = false
        }
    }
}

// MARK: - Quote Card

struct QuoteCardView: View {
    let quote: StockQuote

    var body: some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            // Symbol & Name
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

            // Details grid
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 16) {
                QuoteMetric(label: "Open", value: formatPrice(quote.openPrice))
                QuoteMetric(label: "Day High", value: formatPrice(quote.dayHigh))
                QuoteMetric(label: "Day Low", value: formatPrice(quote.dayLow))
                QuoteMetric(label: "Volume", value: MarketDataService.shared.formatVolume(quote.volume))
                QuoteMetric(label: "Market Cap", value: MarketDataService.shared.formatMarketCap(quote.marketCap))
                QuoteMetric(label: "P/E Ratio", value: quote.peRatio != nil ? String(format: "%.2f", quote.peRatio!) : "N/A")
                QuoteMetric(label: "52W High", value: formatPrice(quote.fiftyTwoWeekHigh))
                QuoteMetric(label: "52W Low", value: formatPrice(quote.fiftyTwoWeekLow))
                QuoteMetric(label: "Dividend Yield", value: quote.dividendYield != nil ? String(format: "%.2f%%", quote.dividendYield! * 100) : "N/A")
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
