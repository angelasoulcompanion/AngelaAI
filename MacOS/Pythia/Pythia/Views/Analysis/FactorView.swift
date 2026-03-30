//
//  FactorView.swift
//  Pythia — Fama-French Factor Analysis (Phase 7.3)
//

import SwiftUI
import Charts

struct FactorView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var selectedModel = "ff3"
    @State private var assetResult: AssetFactorResponse?
    @State private var isLoading = false

    private let models = [("FF3", "ff3"), ("FF5", "ff5")]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Factor Analysis")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    ForEach(models, id: \.1) { name, model in
                        Button(name) { selectedModel = model }
                            .buttonStyle(.plain)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(selectedModel == model ? PythiaTheme.accentGold.opacity(0.2) : PythiaTheme.surfaceBackground)
                            .foregroundColor(selectedModel == model ? PythiaTheme.accentGold : PythiaTheme.textSecondary)
                            .cornerRadius(8)
                    }

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Running OLS regression...") }

                if let r = assetResult, r.success {
                    // Alpha & R² card
                    alphaCard(r)

                    // Factor exposure chart
                    exposureChart(r)

                    // Factor table
                    factorTable(r)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Alpha Card

    private func alphaCard(_ r: AssetFactorResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text("\(r.symbol) — \(r.model.uppercased())")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Alpha (ann.)", String(format: "%+.4f", r.alpha),
                          r.alpha > 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .large)
                MetricBox("Alpha t-stat", String(format: "%.2f", r.alphaTStat),
                          abs(r.alphaTStat) > 2 ? PythiaTheme.accentGold : PythiaTheme.textSecondary, size: .large)
                MetricBox("R²", String(format: "%.3f", r.rSquared),
                          PythiaTheme.secondaryBlue, size: .large)
                MetricBox("Factors", "\(r.exposures.count)",
                          PythiaTheme.accentGold, size: .large)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Exposure Chart

    private func exposureChart(_ r: AssetFactorResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Factor Exposures (Beta)")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(r.exposures) { exp in
                BarMark(
                    x: .value("Factor", exp.factorName.uppercased()),
                    y: .value("Beta", exp.beta)
                )
                .foregroundStyle(exp.beta > 0 ? PythiaTheme.profit : PythiaTheme.loss)
                .annotation(position: exp.beta > 0 ? .top : .bottom) {
                    Text(String(format: "%+.3f", exp.beta))
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(exp.beta > 0 ? PythiaTheme.profit : PythiaTheme.loss)
                }
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisValueLabel {
                        Text(String(format: "%.1f", value.as(Double.self) ?? 0))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }
            .frame(height: 250)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Factor Table

    private func factorTable(_ r: AssetFactorResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Regression Details")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            // Header
            HStack {
                Text("Factor").frame(width: 80, alignment: .leading)
                Text("Beta").frame(width: 80, alignment: .trailing)
                Text("t-stat").frame(width: 80, alignment: .trailing)
                Text("p-value").frame(width: 80, alignment: .trailing)
                Text("Sig.").frame(width: 60, alignment: .center)
            }
            .font(.system(size: 11, weight: .bold))
            .foregroundColor(PythiaTheme.textSecondary)

            Divider().background(PythiaTheme.surfaceBackground)

            ForEach(r.exposures) { exp in
                HStack {
                    Text(exp.factorName.uppercased())
                        .frame(width: 80, alignment: .leading)
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(String(format: "%+.4f", exp.beta))
                        .frame(width: 80, alignment: .trailing)
                        .foregroundColor(exp.beta > 0 ? PythiaTheme.profit : PythiaTheme.loss)
                    Text(String(format: "%.2f", exp.tStat))
                        .frame(width: 80, alignment: .trailing)
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text(String(format: "%.4f", exp.pValue))
                        .frame(width: 80, alignment: .trailing)
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text(exp.pValue < 0.05 ? "***" : exp.pValue < 0.10 ? "**" : "")
                        .frame(width: 60, alignment: .center)
                        .foregroundColor(PythiaTheme.accentGold)
                }
                .font(.system(size: 12, design: .monospaced))
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - API

    private func analyze() async {
        guard let assetId = selectedAssetId else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            assetResult = try await db.get("/factors/asset/\(assetId)?model=\(selectedModel)&days=365", timeout: 60.0)
        } catch {
            assetResult = nil
        }
    }
}
