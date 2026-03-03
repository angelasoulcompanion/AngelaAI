//
//  SentimentView.swift
//  Pythia — AI Sentiment Analysis (Enhanced with News + LLM Narrative)
//

import SwiftUI

struct SentimentView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var result: AISentimentResponse?
    @State private var isLoading = false
    @State private var includeNews = true
    @State private var includeNarrative = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Sentiment Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    Toggle("News", isOn: $includeNews)
                        .toggleStyle(.switch)
                        .frame(width: 80)

                    Toggle("AI Analysis", isOn: $includeNarrative)
                        .toggleStyle(.switch)
                        .frame(width: 120)

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

                    // Score comparison bar (Technical vs News vs Combined)
                    if r.technicalScore != nil || r.newsScore != nil {
                        scoreComparisonCard(r)
                    }

                    // AI narrative card
                    if let narrative = r.narrative, !narrative.isEmpty {
                        narrativeCard(narrative, provider: r.llmProvider)
                    }

                    signalsCard(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)

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

                MetricBox("Momentum", PythiaTheme.formatPercent(r.priceMomentum),
                          PythiaTheme.profitLossColor(r.priceMomentum), size: .small)
                MetricBox("Volume", String(format: "%.2fx", r.volumeTrend), PythiaTheme.textPrimary, size: .small)
                MetricBox("Volatility", r.volatilityRegime.capitalized,
                          r.volatilityRegime == "high" ? PythiaTheme.loss : PythiaTheme.profit, size: .small)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func scoreComparisonCard(_ r: AISentimentResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Score Breakdown")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            if let tech = r.technicalScore {
                scoreBar(label: "Technical", score: tech, color: PythiaTheme.secondaryBlue)
            }
            if let news = r.newsScore {
                scoreBar(label: "News", score: news, color: PythiaTheme.accentGold)
            }
            if let combined = r.combinedScore {
                scoreBar(label: "Combined", score: combined, color: sentimentColor(r.sentiment))
            }
        }
        .padding()
        .pythiaCard()
    }

    private func scoreBar(label: String, score: Double, color: Color) -> some View {
        HStack(spacing: 12) {
            Text(label)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
                .frame(width: 80, alignment: .leading)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(PythiaTheme.surfaceBackground)
                        .frame(height: 8)

                    let normalized = (score + 1) / 2  // -1..1 → 0..1
                    RoundedRectangle(cornerRadius: 4)
                        .fill(color)
                        .frame(width: max(4, geo.size.width * normalized), height: 8)
                }
            }
            .frame(height: 8)

            Text(String(format: "%+.2f", score))
                .font(PythiaTheme.monospace())
                .foregroundColor(PythiaTheme.profitLossColor(score))
                .frame(width: 60, alignment: .trailing)
        }
        .frame(height: 20)
    }

    private func narrativeCard(_ narrative: String, provider: String?) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("AI Analysis")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if let p = provider {
                    Text(p.uppercased())
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(4)
                }
            }

            Text(narrative)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textPrimary)
                .lineSpacing(4)
        }
        .padding()
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(PythiaTheme.accentGold.opacity(0.3), lineWidth: 1)
        )
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
        do {
            result = try await db.getSentiment(
                assetId: aid,
                includeNews: includeNews,
                includeNarrative: includeNarrative
            )
        } catch {}
        isLoading = false
    }
}
