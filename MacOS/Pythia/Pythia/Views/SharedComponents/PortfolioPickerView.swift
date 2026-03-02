//
//  PortfolioPickerView.swift
//  Pythia — Reusable portfolio selection picker
//
//  Replaces duplicated Portfolio Picker + loadPortfolios() across
//  MPTView, VaRView, StressTestView, PerformanceView, CorrelationView, AIAdvisorView.
//

import SwiftUI

/// Self-loading portfolio picker. Fetches portfolios on appear, presents a Picker bound to `selectedId`.
struct PortfolioPickerView: View {
    @EnvironmentObject var db: DatabaseService
    @Binding var selectedId: String?
    @State private var portfolios: [Portfolio] = []

    var body: some View {
        Picker("Portfolio", selection: Binding(
            get: { selectedId ?? "" },
            set: { selectedId = $0.isEmpty ? nil : $0 }
        )) {
            Text("Select Portfolio").tag("")
            ForEach(portfolios) { p in
                Text(p.name).tag(p.portfolioId)
            }
        }
        .frame(width: 200)
        .task {
            do { portfolios = try await db.fetchPortfolios() } catch {}
        }
    }
}
