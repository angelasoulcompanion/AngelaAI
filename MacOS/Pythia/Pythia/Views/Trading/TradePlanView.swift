//
//  TradePlanView.swift
//  Pythia — Trade Plan Generator (Phase 8.2)
//

import SwiftUI

struct TradePlanView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var plan: TradePlanResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Trade Plan Generator")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)
                    Button("Generate Plan") { Task { await generate() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)
                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Generating trade plan...") }

                if let p = plan, p.success {
                    planCard(p)
                    levelsCard(p)
                    if let rationale = p.rationale, !rationale.isEmpty {
                        rationaleCard(rationale)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func planCard(_ p: TradePlanResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(p.symbol)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: p.direction == "long" ? "arrow.up.right" : "arrow.down.right")
                    Text(p.direction.uppercased())
                }
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(p.direction == "long" ? PythiaTheme.profit : PythiaTheme.loss)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background((p.direction == "long" ? PythiaTheme.profit : PythiaTheme.loss).opacity(0.15))
                .cornerRadius(8)

                if let regime = p.regime, !regime.isEmpty {
                    Text(regime.uppercased())
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(6)
                }
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 4), spacing: PythiaTheme.spacing) {
                MetricBox("Entry", String(format: "%.4f", p.entryPrice), PythiaTheme.textPrimary, size: .medium)
                MetricBox("Stop Loss", String(format: "%.4f", p.stopLoss), PythiaTheme.loss, size: .medium)
                MetricBox("TP1 (1R)", String(format: "%.4f", p.takeProfit1), PythiaTheme.profit, size: .medium)
                MetricBox("TP2 (2R)", String(format: "%.4f", p.takeProfit2), PythiaTheme.profit, size: .medium)
                MetricBox("Risk", String(format: "%.1f%%", p.riskPct * 100), PythiaTheme.warningOrange, size: .medium)
                MetricBox("R:R", String(format: "%.1f:1", p.riskReward), p.riskReward >= 2 ? PythiaTheme.profit : PythiaTheme.accentGold, size: .medium)
                MetricBox("Size", String(format: "%.1f%%", p.positionSizePct * 100), PythiaTheme.secondaryBlue, size: .medium)
                MetricBox("TP3 (3R)", String(format: "%.4f", p.takeProfit3), PythiaTheme.profit, size: .medium)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func levelsCard(_ p: TradePlanResponse) -> some View {
        HStack(spacing: PythiaTheme.largeSpacing) {
            VStack(alignment: .leading, spacing: 8) {
                Text("SUPPORT")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(PythiaTheme.profit)
                ForEach(p.supportLevels ?? [], id: \.self) { level in
                    Text(String(format: "%.4f", level))
                        .font(.system(size: 14, weight: .medium, design: .monospaced))
                        .foregroundColor(PythiaTheme.profit)
                }
            }

            Divider().frame(height: 60).background(PythiaTheme.surfaceBackground)

            VStack(alignment: .leading, spacing: 8) {
                Text("RESISTANCE")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(PythiaTheme.loss)
                ForEach(p.resistanceLevels ?? [], id: \.self) { level in
                    Text(String(format: "%.4f", level))
                        .font(.system(size: 14, weight: .medium, design: .monospaced))
                        .foregroundColor(PythiaTheme.loss)
                }
            }

            Spacer()
        }
        .padding()
        .pythiaCard()
    }

    private func rationaleCard(_ rationale: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("AI Trade Rationale")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
            }
            Text(rationale)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
                .lineSpacing(4)
        }
        .padding()
        .pythiaCard()
    }

    private func generate() async {
        guard let id = selectedAssetId else { return }
        isLoading = true; defer { isLoading = false }
        do { plan = try await db.post("/trade-plans/\(id)?risk_per_trade=0.02", body: EmptyBody()) }
        catch { plan = nil }
    }
}
