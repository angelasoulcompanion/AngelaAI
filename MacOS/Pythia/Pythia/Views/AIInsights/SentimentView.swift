//
//  SentimentView.swift
//  Pythia — AI Sentiment Analysis
//

import SwiftUI

struct SentimentView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var assets: [Asset] = []
    @State private var selectedAssetId: String?
    @State private var result: AISentimentResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Sentiment Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    Picker("Asset", selection: Binding(
                        get: { selectedAssetId ?? "" },
                        set: { selectedAssetId = $0.isEmpty ? nil : $0 }
                    )) {
                        Text("Select Asset").tag("")
                        ForEach(assets) { a in
                            Text(a.symbol).tag(a.assetId)
                        }
                    }
                    .frame(width: 200)

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Analyzing sentiment...") }

                if let r = result, r.success {
                    sentimentCard(r)
                    signalsCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { assets = try await db.fetchAssets() } catch {} }
    }

    private func sentimentCard(_ r: AISentimentResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(r.symbol)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(r.sentiment.uppercased())
                    .font(PythiaTheme.heading())
                    .foregroundColor(sentimentColor(r.sentiment))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(sentimentColor(r.sentiment).opacity(0.15))
                    .cornerRadius(8)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                VStack(spacing: 4) {
                    // Sentiment gauge
                    Gauge(value: (r.score + 1) / 2, in: 0...1) {
                        Text("Score")
                    } currentValueLabel: {
                        Text(String(format: "%.2f", r.score))
                            .font(PythiaTheme.monospace())
                    }
                    .gaugeStyle(.accessoryLinear)
                    .tint(Gradient(colors: [PythiaTheme.loss, PythiaTheme.accentGold, PythiaTheme.profit]))
                    .frame(width: 200)
                }

                metricCol("Momentum", PythiaTheme.formatPercent(r.priceMomentum),
                          PythiaTheme.profitLossColor(r.priceMomentum))
                metricCol("Volume", String(format: "%.2fx", r.volumeTrend), PythiaTheme.textPrimary)
                metricCol("Volatility", r.volatilityRegime.capitalized,
                          r.volatilityRegime == "high" ? PythiaTheme.loss : PythiaTheme.profit)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func signalsCard(_ r: AISentimentResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Signals")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            ForEach(r.signals) { signal in
                HStack {
                    Image(systemName: signalIcon(signal.impact))
                        .foregroundColor(sentimentColor(signal.impact))
                        .frame(width: 24)

                    Text(signal.signal)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)

                    Spacer()

                    if let val = signal.value {
                        Text(String(format: "%.4f", val))
                            .font(PythiaTheme.monospace())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }

                    Text(signal.impact.uppercased())
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(sentimentColor(signal.impact))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(sentimentColor(signal.impact).opacity(0.15))
                        .cornerRadius(4)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func metricCol(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value).font(.system(size: 18, weight: .bold, design: .rounded)).foregroundColor(color)
            Text(label).font(PythiaTheme.caption()).foregroundColor(PythiaTheme.textSecondary)
        }
    }

    private func sentimentColor(_ s: String) -> Color {
        switch s.lowercased() {
        case "bullish": return PythiaTheme.profit
        case "bearish": return PythiaTheme.loss
        case "cautious": return PythiaTheme.warningOrange
        default: return PythiaTheme.textSecondary
        }
    }

    private func signalIcon(_ impact: String) -> String {
        switch impact.lowercased() {
        case "bullish": return "arrow.up.circle.fill"
        case "bearish": return "arrow.down.circle.fill"
        case "cautious": return "exclamationmark.circle.fill"
        default: return "minus.circle.fill"
        }
    }

    private func analyze() async {
        guard let aid = selectedAssetId else { return }
        isLoading = true
        do { result = try await db.getSentiment(assetId: aid) } catch {}
        isLoading = false
    }
}
