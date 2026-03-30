//
//  RiskBudgetView.swift
//  Pythia — Risk Budget Advisor (Phase 8.3)
//

import SwiftUI

struct RiskBudgetView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedPortfolioId: String?
    @State private var result: RiskBudgetResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Risk Budget Advisor")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    PortfolioPickerView(selectedId: $selectedPortfolioId)
                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedPortfolioId == nil)
                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Analyzing risk budget...") }

                if let r = result, r.success {
                    // Summary
                    VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                        HStack {
                            Text("Risk Budget Allocation")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)
                            Spacer()
                            if let regime = r.regime, !regime.isEmpty {
                                Text("Regime: \(regime.uppercased())")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundColor(PythiaTheme.accentGold)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 4)
                                    .background(PythiaTheme.accentGold.opacity(0.15))
                                    .cornerRadius(6)
                            }
                        }

                        HStack(spacing: PythiaTheme.largeSpacing) {
                            MetricBox("Total Budget", String(format: "%.1f%%", r.totalBudget * 100), PythiaTheme.accentGold, size: .large)
                            MetricBox("Utilization", String(format: "%.0f%%", r.utilization * 100),
                                      r.utilization > 0.8 ? PythiaTheme.warningOrange : PythiaTheme.profit, size: .large)
                            MetricBox("Strategies", "\(r.allocations.filter { $0.strategyType != "buffer" }.count)", PythiaTheme.secondaryBlue, size: .large)
                        }
                    }
                    .padding()
                    .pythiaCard()

                    // Allocations
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Allocation Breakdown")
                            .font(PythiaTheme.heading())
                            .foregroundColor(PythiaTheme.textPrimary)

                        ForEach(r.allocations) { alloc in
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(alloc.strategyName)
                                        .font(.system(size: 13, weight: .medium))
                                        .foregroundColor(PythiaTheme.textPrimary)
                                    Text(alloc.strategyType.uppercased())
                                        .font(.system(size: 10))
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }

                                Spacer()

                                GeometryReader { geo in
                                    Rectangle()
                                        .fill(alloc.strategyType == "buffer" ? PythiaTheme.textTertiary : PythiaTheme.accentGold)
                                        .frame(width: geo.size.width * CGFloat(alloc.riskBudgetPct / (r.totalBudget * 100)), height: 16)
                                        .cornerRadius(4)
                                }
                                .frame(width: 200, height: 16)

                                Text(String(format: "%.1f%%", alloc.riskBudgetPct))
                                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                                    .foregroundColor(PythiaTheme.accentGold)
                                    .frame(width: 60, alignment: .trailing)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .pythiaCard()

                    // AI Advice
                    if let advice = r.aiAdvice, !advice.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Image(systemName: "brain.head.profile")
                                    .foregroundColor(PythiaTheme.accentGold)
                                Text("AI Risk Advice")
                                    .font(PythiaTheme.heading())
                                    .foregroundColor(PythiaTheme.textPrimary)
                            }
                            Text(advice)
                                .font(PythiaTheme.body())
                                .foregroundColor(PythiaTheme.textSecondary)
                                .lineSpacing(4)
                        }
                        .padding()
                        .pythiaCard()
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func analyze() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true; defer { isLoading = false }
        do { result = try await db.get("/risk/\(pid)/budget?total_budget=0.02", timeout: 60.0) }
        catch { result = nil }
    }
}
