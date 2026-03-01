//
//  TransactionsView.swift
//  Pythia
//

import SwiftUI

struct TransactionsView: View {
    @EnvironmentObject var db: DatabaseService
    @State private var portfolios: [Portfolio] = []
    @State private var transactions: [Transaction] = []
    @State private var selectedPortfolioId: String?
    @State private var isLoading = true

    var body: some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            // Header
            HStack {
                Text("Transactions")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Picker("Portfolio", selection: $selectedPortfolioId) {
                    Text("Select Portfolio").tag(nil as String?)
                    ForEach(portfolios) { p in
                        Text(p.name).tag(p.portfolioId as String?)
                    }
                }
                .frame(width: 200)
            }
            .padding(.horizontal, PythiaTheme.largeSpacing)
            .padding(.top, PythiaTheme.largeSpacing)

            if isLoading {
                LoadingView("Loading transactions...")
            } else if transactions.isEmpty {
                EmptyStateView(
                    icon: "arrow.left.arrow.right",
                    title: "No Transactions",
                    message: selectedPortfolioId == nil
                        ? "Select a portfolio to view transactions."
                        : "No transactions recorded for this portfolio."
                )
            } else {
                // Table header
                HStack {
                    Text("Date").frame(width: 90, alignment: .leading)
                    Text("Symbol").frame(width: 70, alignment: .leading)
                    Text("Type").frame(width: 80, alignment: .leading)
                    Text("Qty").frame(width: 80, alignment: .trailing)
                    Text("Price").frame(width: 90, alignment: .trailing)
                    Text("Fees").frame(width: 70, alignment: .trailing)
                    Text("Total").frame(width: 110, alignment: .trailing)
                    Spacer()
                }
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
                .padding(.horizontal, PythiaTheme.largeSpacing)

                Divider().background(PythiaTheme.textTertiary.opacity(0.3))
                    .padding(.horizontal, PythiaTheme.largeSpacing)

                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(transactions) { txn in
                            TransactionRow(transaction: txn)
                        }
                    }
                }
            }
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            do {
                portfolios = try await db.fetchPortfolios()
            } catch { }
            isLoading = false
        }
        .onChange(of: selectedPortfolioId) {
            guard let id = selectedPortfolioId else { return }
            Task {
                isLoading = true
                do {
                    transactions = try await db.fetchTransactions(portfolioId: id)
                } catch { }
                isLoading = false
            }
        }
    }
}

struct TransactionRow: View {
    let transaction: Transaction

    var typeColor: Color {
        switch transaction.transactionType {
        case "buy": return PythiaTheme.profit
        case "sell": return PythiaTheme.loss
        case "dividend": return PythiaTheme.accentGold
        default: return PythiaTheme.textSecondary
        }
    }

    var body: some View {
        HStack {
            Text(transaction.transactionDate != nil
                 ? transaction.transactionDate!.formatted(.dateTime.day().month().year())
                 : "-")
                .frame(width: 90, alignment: .leading)
            Text(transaction.symbol)
                .font(.system(size: 13, weight: .semibold, design: .monospaced))
                .foregroundColor(PythiaTheme.accentGold)
                .frame(width: 70, alignment: .leading)
            Text(transaction.transactionType.uppercased())
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(typeColor)
                .frame(width: 80, alignment: .leading)
            Text(String(format: "%.2f", transaction.quantity))
                .frame(width: 80, alignment: .trailing)
            Text(String(format: "%.2f", transaction.price))
                .frame(width: 90, alignment: .trailing)
            Text(String(format: "%.2f", transaction.fees ?? 0))
                .frame(width: 70, alignment: .trailing)
            Text(PythiaTheme.formatCurrency(transaction.totalAmount))
                .font(.system(size: 13, weight: .medium, design: .monospaced))
                .frame(width: 110, alignment: .trailing)
            Spacer()
        }
        .font(.system(size: 13, design: .monospaced))
        .foregroundColor(PythiaTheme.textSecondary)
        .padding(.horizontal, PythiaTheme.largeSpacing)
        .padding(.vertical, 6)
    }
}
