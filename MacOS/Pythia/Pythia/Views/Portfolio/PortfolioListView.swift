//
//  PortfolioListView.swift
//  Pythia
//

import SwiftUI

struct PortfolioListView: View {
    @EnvironmentObject var db: DatabaseService
    @State private var portfolios: [Portfolio] = []
    @State private var isLoading = true
    @State private var selectedPortfolio: Portfolio?
    @State private var showCreateSheet = false

    var body: some View {
        HSplitView {
            // Portfolio list
            VStack(alignment: .leading, spacing: 0) {
                // Header
                HStack {
                    Text("Portfolios")
                        .font(PythiaTheme.title())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Spacer()
                    Button(action: { showCreateSheet = true }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 20))
                            .foregroundColor(PythiaTheme.secondaryBlue)
                    }
                    .buttonStyle(.plain)
                }
                .padding()

                if isLoading {
                    LoadingView("Loading portfolios...")
                } else if portfolios.isEmpty {
                    EmptyStateView(
                        icon: "briefcase",
                        title: "No Portfolios",
                        message: "Create your first portfolio to start tracking investments.",
                        actionTitle: "Create Portfolio",
                        action: { showCreateSheet = true }
                    )
                } else {
                    List(portfolios, selection: $selectedPortfolio) { portfolio in
                        PortfolioRow(portfolio: portfolio)
                            .tag(portfolio)
                    }
                    .listStyle(.inset)
                }
            }
            .frame(minWidth: 350)

            // Detail pane
            if let portfolio = selectedPortfolio {
                PortfolioDetailView(portfolioId: portfolio.portfolioId, onDelete: {
                    selectedPortfolio = nil
                    loadPortfolios()
                })
            } else {
                EmptyStateView(
                    icon: "briefcase",
                    title: "Select a Portfolio",
                    message: "Choose a portfolio from the list to view details."
                )
            }
        }
        .background(PythiaTheme.backgroundDark)
        .sheet(isPresented: $showCreateSheet) {
            CreatePortfolioSheet(onCreated: { loadPortfolios() })
        }
        .task {
            loadPortfolios()
        }
    }

    private func loadPortfolios() {
        Task {
            isLoading = true
            do {
                portfolios = try await db.fetchPortfolios()
            } catch {
                print("Error loading portfolios: \(error)")
            }
            isLoading = false
        }
    }
}

// MARK: - Portfolio Row

struct PortfolioRow: View {
    let portfolio: Portfolio

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(portfolio.name)
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(PythiaTheme.formatCurrency(portfolio.totalValue ?? 0))
                    .font(.system(size: 14, weight: .semibold, design: .monospaced))
                    .foregroundColor(PythiaTheme.accentGold)
            }

            HStack {
                if let desc = portfolio.description {
                    Text(desc)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                        .lineLimit(1)
                }
                Spacer()
                Text("\(portfolio.holdingCount ?? 0) holdings")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Create Portfolio Sheet

struct CreatePortfolioSheet: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var db: DatabaseService
    @State private var name = ""
    @State private var description = ""
    @State private var currency = "THB"
    @State private var benchmark = "^SET"
    @State private var riskFreeRate = 0.0225
    @State private var initialCapital = ""
    @State private var isCreating = false

    var onCreated: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            Text("Create Portfolio")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            Form {
                TextField("Name", text: $name)
                TextField("Description", text: $description)
                TextField("Currency", text: $currency)
                TextField("Benchmark", text: $benchmark)
                TextField("Initial Capital", text: $initialCapital)
            }
            .formStyle(.grouped)

            HStack {
                Button("Cancel") { dismiss() }
                    .buttonStyle(.plain)
                Spacer()
                Button("Create") {
                    createPortfolio()
                }
                .disabled(name.isEmpty || isCreating)
                .buttonStyle(.borderedProminent)
                .tint(Color(hex: "1E40AF"))
            }
        }
        .padding(24)
        .frame(width: 400, height: 400)
        .background(PythiaTheme.backgroundMedium)
    }

    private func createPortfolio() {
        isCreating = true
        Task {
            do {
                let request = PortfolioCreateRequest(
                    name: name,
                    description: description.isEmpty ? nil : description,
                    baseCurrency: currency,
                    benchmarkSymbol: benchmark,
                    riskFreeRate: riskFreeRate,
                    initialCapital: Double(initialCapital)
                )
                let _ = try await db.createPortfolio(request)
                onCreated()
                dismiss()
            } catch {
                print("Error creating portfolio: \(error)")
            }
            isCreating = false
        }
    }
}
