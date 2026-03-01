//
//  AIAdvisorView.swift
//  Pythia — AI Portfolio Advisor
//

import SwiftUI

struct AIAdvisorView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var portfolios: [Portfolio] = []
    @State private var selectedPortfolioId: String?
    @State private var advice: AIAdvisorResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("AI Portfolio Advisor")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    Picker("Portfolio", selection: Binding(
                        get: { selectedPortfolioId ?? "" },
                        set: { selectedPortfolioId = $0.isEmpty ? nil : $0 }
                    )) {
                        Text("Select Portfolio").tag("")
                        ForEach(portfolios) { p in
                            Text(p.name).tag(p.portfolioId)
                        }
                    }
                    .frame(width: 200)

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedPortfolioId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Analyzing portfolio...") }

                if let a = advice, a.success {
                    adviceCard(a)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { portfolios = try await db.fetchPortfolios() } catch {} }
    }

    private func adviceCard(_ a: AIAdvisorResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                    .font(.title2)
                Text(a.portfolio ?? "Portfolio Analysis")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                metricBox("Diversification", "\(Int((a.diversificationScore ?? 0) * 100))%",
                          (a.diversificationScore ?? 0) > 0.6 ? PythiaTheme.profit : PythiaTheme.warningOrange)
                metricBox("Holdings", "\(a.holdingsCount ?? 0)", PythiaTheme.secondaryBlue)
                metricBox("Sectors", "\(a.sectorsCount ?? 0)", PythiaTheme.accentGold)
            }

            Divider().background(PythiaTheme.textTertiary)

            Text("Analysis & Recommendations")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            ForEach(Array(a.analysis.enumerated()), id: \.offset) { _, item in
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: item.contains("Risk") ? "exclamationmark.triangle" :
                            item.contains("Score") ? "chart.bar" : "lightbulb")
                        .foregroundColor(item.contains("Risk") ? PythiaTheme.warningOrange : PythiaTheme.secondaryBlue)
                        .frame(width: 20)
                    Text(item)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func metricBox(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }

    private func analyze() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true
        do { advice = try await db.getAIAdvice(portfolioId: pid) } catch {}
        isLoading = false
    }
}
