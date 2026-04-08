//
//  SignalDashboardView.swift
//  Pythia — Multi-Factor Signal Dashboard (Phase 7.2)
//

import SwiftUI
import Charts

struct SignalDashboardView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var signalResult: SignalResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Signal Dashboard")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    Button("Generate Signals") { Task { await generateSignals() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Generating multi-factor signals...") }

                if let r = signalResult, r.success {
                    // Composite Score
                    compositeScoreCard(r)

                    // Score Breakdown
                    scoreBreakdownCard(r)

                    // Individual Signals
                    signalListCard(r)

                    // AI Insight
                    if let insight = r.aiInsight, !insight.isEmpty {
                        aiInsightCard(insight)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Composite Score Card

    private func compositeScoreCard(_ r: SignalResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(r.symbol)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                directionBadge(r.compositeDirection)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                // Large composite score gauge
                VStack(spacing: 8) {
                    ZStack {
                        Circle()
                            .stroke(PythiaTheme.surfaceBackground, lineWidth: 12)
                            .frame(width: 100, height: 100)

                        Circle()
                            .trim(from: 0, to: CGFloat((r.compositeScore + 1) / 2))
                            .stroke(directionColor(r.compositeDirection), style: StrokeStyle(lineWidth: 12, lineCap: .round))
                            .frame(width: 100, height: 100)
                            .rotationEffect(.degrees(-90))

                        VStack(spacing: 2) {
                            Text(String(format: "%+.2f", r.compositeScore))
                                .font(.system(size: 22, weight: .bold, design: .rounded))
                                .foregroundColor(directionColor(r.compositeDirection))
                            Text(r.compositeDirection.uppercased())
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                    Text("Composite")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }

                // Score metrics
                VStack(spacing: PythiaTheme.spacing) {
                    HStack(spacing: PythiaTheme.largeSpacing) {
                        MetricBox("Technical", String(format: "%+.3f", r.technicalScore),
                                  scoreColor(r.technicalScore), size: .medium)
                        MetricBox("Quant", String(format: "%+.3f", r.quantScore),
                                  scoreColor(r.quantScore), size: .medium)
                        MetricBox("Sentiment", String(format: "%+.3f", r.sentimentScore),
                                  scoreColor(r.sentimentScore), size: .medium)
                    }
                    MetricBox("Signals", "\(r.signals.count)", PythiaTheme.accentGold, size: .small)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Score Breakdown Chart

    private func scoreBreakdownCard(_ r: SignalResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Score Breakdown")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            let scores: [(String, Double, Color)] = [
                ("Technical (35%)", r.technicalScore, PythiaTheme.secondaryBlue),
                ("Quant (30%)", r.quantScore, PythiaTheme.accentGold),
                ("Sentiment (20%)", r.sentimentScore, PythiaTheme.profit),
            ]

            ForEach(scores, id: \.0) { name, score, color in
                HStack {
                    Text(name)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                        .frame(width: 130, alignment: .leading)

                    GeometryReader { geo in
                        let width = geo.size.width
                        let center = width / 2

                        ZStack(alignment: .leading) {
                            Rectangle()
                                .fill(PythiaTheme.surfaceBackground)
                                .frame(height: 16)
                                .cornerRadius(4)

                            // Center line
                            Rectangle()
                                .fill(PythiaTheme.textTertiary.opacity(0.5))
                                .frame(width: 1, height: 16)
                                .offset(x: center)

                            // Score bar from center
                            if score >= 0 {
                                Rectangle()
                                    .fill(color)
                                    .frame(width: width * CGFloat(score) / 2, height: 16)
                                    .offset(x: center)
                                    .cornerRadius(4)
                            } else {
                                Rectangle()
                                    .fill(PythiaTheme.loss)
                                    .frame(width: width * CGFloat(-score) / 2, height: 16)
                                    .offset(x: center - width * CGFloat(-score) / 2)
                                    .cornerRadius(4)
                            }
                        }
                    }
                    .frame(height: 16)

                    Text(String(format: "%+.3f", score))
                        .font(.system(size: 12, weight: .bold, design: .rounded))
                        .foregroundColor(scoreColor(score))
                        .frame(width: 60, alignment: .trailing)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Signal List

    private func signalListCard(_ r: SignalResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Individual Signals (\(r.signals.count))")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            ForEach(r.signals) { signal in
                HStack {
                    // Type badge
                    Text(signal.signalType.prefix(4).uppercased())
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(PythiaTheme.textPrimary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(signalTypeColor(signal.signalType).opacity(0.3))
                        .cornerRadius(4)

                    Text(signal.signalName)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)

                    Spacer()

                    // Strength bar
                    HStack(spacing: 2) {
                        ForEach(0..<5) { i in
                            Rectangle()
                                .fill(Double(i) / 5.0 < signal.strength
                                      ? directionColor(signal.direction)
                                      : PythiaTheme.surfaceBackground)
                                .frame(width: 8, height: 14)
                                .cornerRadius(2)
                        }
                    }

                    directionBadge(signal.direction)
                }
                .padding(.vertical, 4)

                if signal != r.signals.last {
                    Divider().background(PythiaTheme.surfaceBackground)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - AI Insight

    private func aiInsightCard(_ insight: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("AI Trading Insight")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            Text(insight)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
                .lineSpacing(4)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Helpers

    private func directionBadge(_ direction: String) -> some View {
        let icon: String = switch direction {
        case "long": "arrow.up.right"
        case "short": "arrow.down.right"
        default: "minus"
        }
        return HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 10, weight: .bold))
            Text(direction.uppercased())
                .font(.system(size: 11, weight: .bold))
        }
        .foregroundColor(directionColor(direction))
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(directionColor(direction).opacity(0.15))
        .cornerRadius(6)
    }

    private func directionColor(_ direction: String) -> Color {
        switch direction.lowercased() {
        case "long": return PythiaTheme.profit
        case "short": return PythiaTheme.loss
        default: return PythiaTheme.accentGold
        }
    }

    private func scoreColor(_ score: Double) -> Color {
        if score > 0.1 { return PythiaTheme.profit }
        if score < -0.1 { return PythiaTheme.loss }
        return PythiaTheme.accentGold
    }

    private func signalTypeColor(_ type: String) -> Color {
        switch type {
        case "technical": return PythiaTheme.secondaryBlue
        case "quant": return PythiaTheme.accentGold
        case "sentiment": return PythiaTheme.profit
        case "fundamental": return PythiaTheme.accentBlue
        default: return PythiaTheme.textSecondary
        }
    }

    // MARK: - API

    private func generateSignals() async {
        guard let assetId = selectedAssetId else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            signalResult = try await db.get("/signals/\(assetId)?include_ai=true", timeout: 60.0)
        } catch {
            signalResult = nil
        }
    }
}

// Equatable for signal comparison in ForEach
extension TradingSignal: Equatable {
    static func == (lhs: TradingSignal, rhs: TradingSignal) -> Bool {
        lhs.signalName == rhs.signalName && lhs.signalType == rhs.signalType
    }
}
