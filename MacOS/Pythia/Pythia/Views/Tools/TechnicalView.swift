//
//  TechnicalView.swift
//  Pythia — Technical Analysis / Stock Detail
//

import SwiftUI

struct TechnicalView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var assets: [Asset] = []
    @State private var quote: StockQuote?
    @State private var loadedSymbol: String?
    @State private var isLoading = false
    @State private var errorMessage: String?

    private var selectedSymbol: String? {
        assets.first(where: { $0.assetId == selectedAssetId })?.symbol
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Technical Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Search bar — Asset Picker
                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    Button("Load") { Task { await loadData() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if isLoading { LoadingView("Loading market data...") }

                if let q = quote {
                    quoteCard(q)
                }

                if let sym = loadedSymbol {
                    TechnicalChartView(symbol: sym)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            do { assets = try await db.fetchAssets() } catch {}
        }
    }

    private func quoteCard(_ q: StockQuote) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading) {
                    Text(q.symbol)
                        .font(PythiaTheme.title())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(q.name ?? "")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                Spacer()
                VStack(alignment: .trailing) {
                    Text(String(format: "%.2f", q.currentPrice ?? 0))
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(PythiaTheme.textPrimary)
                    HStack(spacing: 4) {
                        Image(systemName: (q.changePercent ?? 0) >= 0 ? "arrow.up.right" : "arrow.down.right")
                        Text(String(format: "%.2f%%", (q.changePercent ?? 0) * 100))
                    }
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.profitLossColor(q.changePercent ?? 0))
                }
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: 12) {
                numericMetric("Open", q.openPrice)
                numericMetric("High", q.dayHigh)
                numericMetric("Low", q.dayLow)
                numericMetric("Prev Close", q.previousClose)
                stringMetric("Volume", q.volume.map { MarketDataService.shared.formatVolume($0) })
                stringMetric("Market Cap", q.marketCap.map { MarketDataService.shared.formatMarketCap($0) })
                numericMetric("52W High", q.fiftyTwoWeekHigh)
                numericMetric("52W Low", q.fiftyTwoWeekLow)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func numericMetric(_ label: String, _ value: Double?) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value.map { String(format: "%.2f", $0) } ?? "-")
                .font(PythiaTheme.monospace())
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    private func stringMetric(_ label: String, _ value: String?) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value ?? "-")
                .font(PythiaTheme.monospace())
                .foregroundColor(PythiaTheme.textPrimary)
        }
    }

    private func loadData() async {
        guard let sym = selectedSymbol, !sym.isEmpty else { return }
        isLoading = true; errorMessage = nil
        do {
            quote = try await db.fetchQuote(symbol: sym)
            loadedSymbol = sym.uppercased()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
