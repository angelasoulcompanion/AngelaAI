//
//  PortfolioDetailView.swift
//  Pythia
//

import SwiftUI
import Charts

struct PortfolioDetailView: View {
    @EnvironmentObject var db: DatabaseService
    let portfolioId: String
    @State private var detail: PortfolioDetail?
    @State private var isLoading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                if isLoading {
                    LoadingView("Loading portfolio...")
                } else if let detail = detail {
                    // Header
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(detail.name)
                                .font(PythiaTheme.title())
                                .foregroundColor(PythiaTheme.textPrimary)
                            if let desc = detail.description {
                                Text(desc)
                                    .font(PythiaTheme.body())
                                    .foregroundColor(PythiaTheme.textSecondary)
                            }
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 4) {
                            Text(PythiaTheme.formatCurrency(detail.totalValue ?? 0))
                                .font(.system(size: 28, weight: .bold, design: .rounded))
                                .foregroundColor(PythiaTheme.accentGold)
                            Text("\(detail.holdings.count) holdings")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }

                    // Portfolio info
                    HStack(spacing: PythiaTheme.spacing) {
                        InfoPill(label: "Currency", value: detail.baseCurrency ?? "THB")
                        InfoPill(label: "Benchmark", value: detail.benchmarkSymbol ?? "^SET")
                        InfoPill(label: "Risk-Free", value: PythiaTheme.formatPercent(detail.riskFreeRate ?? 0.02))
                    }

                    // Holdings table
                    HoldingsView(holdings: detail.holdings)

                    // Weight chart
                    if !detail.holdings.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Weight Allocation")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)

                            Chart(detail.holdings) { holding in
                                SectorMark(
                                    angle: .value("Weight", holding.weight),
                                    innerRadius: .ratio(0.5)
                                )
                                .foregroundStyle(by: .value("Asset", holding.symbol))
                            }
                            .frame(height: 250)
                        }
                        .padding()
                        .pythiaCard()
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            await loadDetail()
        }
        .onChange(of: portfolioId) {
            Task { await loadDetail() }
        }
    }

    private func loadDetail() async {
        isLoading = true
        do {
            detail = try await db.fetchPortfolio(id: portfolioId)
        } catch {
            print("Error loading portfolio: \(error)")
        }
        isLoading = false
    }
}

// MARK: - Info Pill

struct InfoPill: View {
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 2) {
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
            Text(value)
                .font(.system(size: 13, weight: .medium, design: .monospaced))
                .foregroundColor(PythiaTheme.textPrimary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(PythiaTheme.surfaceBackground.opacity(0.5))
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }
}
