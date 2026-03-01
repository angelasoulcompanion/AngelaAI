//
//  TechnicalView.swift
//  Pythia — Technical Analysis / Stock Detail
//

import SwiftUI
import Charts

struct TechnicalView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var symbol = ""
    @State private var quote: StockQuote?
    @State private var history: HistoryResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var period = "1y"

    private let periods = [("1mo", "1M"), ("3mo", "3M"), ("6mo", "6M"), ("1y", "1Y"), ("2y", "2Y"), ("5y", "5Y")]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Technical Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Search bar
                HStack(spacing: PythiaTheme.spacing) {
                    TextField("Enter Symbol (e.g. ADVANC.BK, AAPL)", text: $symbol)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 300)
                        .onSubmit { Task { await loadData() } }

                    Picker("Period", selection: $period) {
                        ForEach(periods, id: \.0) { val, label in
                            Text(label).tag(val)
                        }
                    }
                    .frame(width: 100)

                    Button("Load") { Task { await loadData() } }
                        .pythiaPrimaryButton()
                        .disabled(symbol.isEmpty)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Loading market data...") }

                if let q = quote {
                    quoteCard(q)
                }

                if let h = history, !h.data.isEmpty {
                    priceChart(h)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
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

    private func priceChart(_ h: HistoryResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Price History")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(h.data) { bar in
                LineMark(
                    x: .value("Date", bar.date),
                    y: .value("Close", bar.close)
                )
                .foregroundStyle(PythiaTheme.secondaryBlue)

                AreaMark(
                    x: .value("Date", bar.date),
                    y: .value("Close", bar.close)
                )
                .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.08))
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 6)) { _ in
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .frame(height: 300)
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
        guard !symbol.isEmpty else { return }
        isLoading = true; errorMessage = nil
        do {
            async let q = db.fetchQuote(symbol: symbol)
            async let h = db.fetchHistory(symbol: symbol, period: period)
            quote = try await q
            history = try await h
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
