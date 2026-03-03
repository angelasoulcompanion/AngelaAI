//
//  StressTestView.swift
//  Pythia — Stress Test Scenario Analysis
//

import SwiftUI
import Charts

struct StressTestView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedPortfolioId: String?
    @State private var allResults: StressTestAllResponse?
    @State private var detailResult: StressTestResponse?
    @State private var selectedScenario: String?
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Stress Testing")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    PortfolioPickerView(selectedId: $selectedPortfolioId)

                    Button("Run All Scenarios") {
                        Task { await runAll() }
                    }
                    .pythiaPrimaryButton()
                    .disabled(selectedPortfolioId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading {
                    LoadingView("Running stress tests...")
                }

                if let all = allResults {
                    scenarioSummaryCard(all)
                }

                if let detail = detailResult {
                    scenarioDetailCard(detail)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func scenarioSummaryCard(_ all: StressTestAllResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Scenario Overview")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            // Bar chart of PnL per scenario
            Chart(all.scenarios) { s in
                BarMark(
                    x: .value("P&L %", s.portfolioPnlPct * 100),
                    y: .value("Scenario", s.scenarioName)
                )
                .foregroundStyle(s.portfolioPnlPct >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
            }
            .chartXAxisLabel("Portfolio Impact %")
            .chartXAxis {
                AxisMarks { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .frame(height: CGFloat(all.scenarios.count * 50 + 40))


            // Clickable rows
            ForEach(all.scenarios) { s in
                Button {
                    selectedScenario = s.scenarioName
                    Task { await loadDetail(s.scenarioName) }
                } label: {
                    HStack {
                        Image(systemName: "bolt.fill")
                            .foregroundColor(PythiaTheme.accentGold)

                        Text(s.scenarioName)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textPrimary)

                        Spacer()

                        Text(PythiaTheme.formatPercent(s.portfolioPnlPct))
                            .font(PythiaTheme.monospace())
                            .foregroundColor(PythiaTheme.profitLossColor(s.portfolioPnlPct))

                        Text(PythiaTheme.formatCurrency(s.portfolioPnl))
                            .font(PythiaTheme.monospace())
                            .foregroundColor(PythiaTheme.profitLossColor(s.portfolioPnl))
                            .frame(width: 120, alignment: .trailing)

                        Image(systemName: "chevron.right")
                            .foregroundColor(PythiaTheme.textTertiary)
                    }
                    .padding(.vertical, 6)
                }
                .buttonStyle(.plain)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func scenarioDetailCard(_ d: StressTestResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                VStack(alignment: .leading) {
                    Text(d.scenarioName)
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(d.description)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
                Spacer()
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Before", PythiaTheme.formatCurrency(d.portfolioValueBefore), PythiaTheme.textPrimary, size: .medium)
                MetricBox("After", PythiaTheme.formatCurrency(d.portfolioValueAfter), PythiaTheme.profitLossColor(d.portfolioPnl), size: .medium)
                MetricBox("P&L", PythiaTheme.formatCurrency(d.portfolioPnl), PythiaTheme.profitLossColor(d.portfolioPnl), size: .medium)
                MetricBox("Impact", PythiaTheme.formatPercent(d.portfolioPnlPct), PythiaTheme.profitLossColor(d.portfolioPnlPct), size: .medium)
            }

            PythiaDivider()

            Text("Asset-Level Impact")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            ForEach(d.assetImpacts) { a in
                HStack {
                    Text(a.symbol)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(width: 80, alignment: .leading)
                    Text(a.sector ?? "-")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                        .frame(width: 120, alignment: .leading)
                    Text(PythiaTheme.formatPercent(a.shockPct))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.profitLossColor(a.shockPct))
                        .frame(width: 80)
                    Text(PythiaTheme.formatCurrency(a.pnl))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.profitLossColor(a.pnl))
                        .frame(width: 100, alignment: .trailing)
                    Spacer()
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func runAll() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true; errorMessage = nil; detailResult = nil
        do {
            allResults = try await db.runAllStressTests(portfolioId: pid)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func loadDetail(_ scenarioName: String) async {
        guard let pid = selectedPortfolioId else { return }
        // Map display name → key
        let keyMap = [
            "Market Crash (2008-style)": "market_crash",
            "Tech Sector Selloff": "tech_selloff",
            "Interest Rate Shock (+300bps)": "interest_rate_shock",
            "Currency Crisis": "currency_crisis",
            "Pandemic Shock (COVID-style)": "pandemic",
            "Mild Correction (-10%)": "mild_correction",
        ]
        let key = keyMap[scenarioName] ?? scenarioName
        do {
            detailResult = try await db.runStressTest(portfolioId: pid, scenario: key)
        } catch {}
    }
}
