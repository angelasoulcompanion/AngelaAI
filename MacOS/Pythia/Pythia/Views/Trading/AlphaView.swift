//
//  AlphaView.swift
//  Pythia — Alpha Generation ML (Phase 7.4)
//

import SwiftUI
import Charts

struct AlphaView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var result: AlphaResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Alpha Generation (ML)")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    Button("Predict") { Task { await predict() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Training ML model (walk-forward)...") }

                if let r = result, r.success {
                    predictionCard(r)
                    featureImportanceChart(r)
                }

                if let r = result, !r.success {
                    Text("Error: \(r.message ?? "")")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.errorRed)
                        .padding()
                        .pythiaCard()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Prediction Card

    private func predictionCard(_ r: AlphaResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(r.symbol)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                directionBadge(r.predictedDirection)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                // Large prediction gauge
                VStack(spacing: 8) {
                    ZStack {
                        Circle()
                            .stroke(PythiaTheme.surfaceBackground, lineWidth: 12)
                            .frame(width: 100, height: 100)

                        Circle()
                            .trim(from: 0, to: CGFloat(r.probability))
                            .stroke(directionColor(r.predictedDirection), style: StrokeStyle(lineWidth: 12, lineCap: .round))
                            .frame(width: 100, height: 100)
                            .rotationEffect(.degrees(-90))

                        VStack(spacing: 2) {
                            Text(String(format: "%.0f%%", r.probability * 100))
                                .font(.system(size: 22, weight: .bold, design: .rounded))
                                .foregroundColor(directionColor(r.predictedDirection))
                            Text(r.predictedDirection.uppercased())
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                    Text("5-Day Prediction")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }

                VStack(spacing: PythiaTheme.spacing) {
                    HStack(spacing: PythiaTheme.largeSpacing) {
                        MetricBox("Direction", r.predictedDirection.uppercased(),
                                  directionColor(r.predictedDirection), size: .medium)
                        MetricBox("Confidence", String(format: "%.1f%%", r.probability * 100),
                                  PythiaTheme.accentGold, size: .medium)
                        MetricBox("OOS Accuracy", String(format: "%.1f%%", r.modelAccuracy * 100),
                                  r.modelAccuracy > 0.55 ? PythiaTheme.profit : PythiaTheme.warningOrange, size: .medium)
                        MetricBox("Train Samples", "\(r.trainingSamples)",
                                  PythiaTheme.textPrimary, size: .medium)
                    }
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Feature Importance Chart

    private func featureImportanceChart(_ r: AlphaResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Feature Importance")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            if let features = r.featureImportance, !features.isEmpty {
                Chart(features) { fi in
                    BarMark(
                        x: .value("Importance", fi.importance),
                        y: .value("Feature", fi.feature)
                    )
                    .foregroundStyle(
                        fi.importance > 0.15 ? PythiaTheme.accentGold :
                        fi.importance > 0.08 ? PythiaTheme.secondaryBlue :
                        PythiaTheme.textTertiary
                    )
                    .annotation(position: .trailing) {
                        Text(String(format: "%.1f%%", fi.importance * 100))
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
                .chartXAxis {
                    AxisMarks { value in
                        AxisValueLabel {
                            Text(String(format: "%.0f%%", (value.as(Double.self) ?? 0) * 100))
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                }
                .frame(height: CGFloat(max((r.featureImportance?.count ?? 0) * 35, 200)))

                // Legend
                HStack(spacing: PythiaTheme.spacing) {
                    Text("Features: ret=return, vol=volatility, rsi=RSI, macd_hist=MACD, volume_zscore=volume anomaly, price_vs_sma50=trend")
                        .font(.system(size: 10))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Helpers

    private func directionBadge(_ direction: String) -> some View {
        let icon: String = switch direction {
        case "up": "arrow.up.right"
        case "down": "arrow.down.right"
        default: "minus"
        }
        return HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 12, weight: .bold))
            Text(direction.uppercased())
                .font(.system(size: 13, weight: .bold))
        }
        .foregroundColor(directionColor(direction))
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(directionColor(direction).opacity(0.15))
        .cornerRadius(8)
    }

    private func directionColor(_ direction: String) -> Color {
        switch direction {
        case "up": return PythiaTheme.profit
        case "down": return PythiaTheme.loss
        default: return PythiaTheme.accentGold
        }
    }

    // MARK: - API

    private func predict() async {
        guard let id = selectedAssetId else { return }
        isLoading = true; defer { isLoading = false }
        do { result = try await db.get("/signals/\(id)/alpha?days=500", timeout: 120.0) }
        catch { result = nil }
    }
}
