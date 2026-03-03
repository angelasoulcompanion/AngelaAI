//
//  PortfolioDetailView.swift
//  Pythia
//

import SwiftUI
import Charts

struct PortfolioDetailView: View {
    @EnvironmentObject var db: DatabaseService
    let portfolioId: String
    var onDelete: (() -> Void)?

    @State private var detail: PortfolioDetail?
    @State private var transactions: [Transaction] = []
    @State private var isLoading = true
    @State private var errorMessage: String?

    // Sheet toggles
    @State private var showEditSheet = false
    @State private var showDeleteConfirmation = false
    @State private var showAddHolding = false
    @State private var showAddTransaction = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                if isLoading {
                    LoadingView("Loading portfolio...")
                } else if let detail = detail {
                    // MARK: - Header
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
                        Menu {
                            Button("Edit Portfolio") { showEditSheet = true }
                            Divider()
                            Button("Delete Portfolio", role: .destructive) {
                                showDeleteConfirmation = true
                            }
                        } label: {
                            Image(systemName: "gearshape.fill")
                                .font(.system(size: 18))
                                .foregroundColor(PythiaTheme.textTertiary)
                        }
                        .menuStyle(.borderlessButton)
                        .frame(width: 32)
                    }

                    // MARK: - Info pills
                    HStack(spacing: PythiaTheme.spacing) {
                        InfoPill(label: "Currency", value: detail.baseCurrency ?? "THB")
                        InfoPill(label: "Benchmark", value: detail.benchmarkSymbol ?? "^SET")
                        InfoPill(label: "Risk-Free", value: PythiaTheme.formatPercent(detail.riskFreeRate ?? 0.02))
                    }

                    // MARK: - Error
                    if let errorMessage = errorMessage {
                        ErrorMessageView(message: errorMessage)
                    }

                    // MARK: - Holdings
                    HoldingsView(
                        holdings: detail.holdings,
                        onAdd: { showAddHolding = true },
                        onDelete: { holding in deleteHolding(holding) }
                    )

                    // MARK: - Weight Allocation
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

                    // MARK: - Recent Transactions
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Recent Transactions")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)
                            Spacer()
                            Button(action: { showAddTransaction = true }) {
                                Image(systemName: "plus.circle.fill")
                                    .font(.system(size: 18))
                                    .foregroundColor(PythiaTheme.secondaryBlue)
                            }
                            .buttonStyle(.plain)
                        }

                        if transactions.isEmpty {
                            Text("No transactions yet")
                                .font(PythiaTheme.body())
                                .foregroundColor(PythiaTheme.textTertiary)
                                .padding()
                        } else {
                            // Header
                            HStack {
                                Text("Date").frame(width: 90, alignment: .leading)
                                Text("Symbol").frame(width: 70, alignment: .leading)
                                Text("Type").frame(width: 70, alignment: .leading)
                                Text("Qty").frame(width: 80, alignment: .trailing)
                                Text("Price").frame(width: 90, alignment: .trailing)
                                Text("Total").frame(width: 110, alignment: .trailing)
                            }
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                            .padding(.horizontal)

                            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

                            ForEach(transactions.prefix(5)) { txn in
                                HStack {
                                    Text(txn.transactionDate != nil
                                         ? txn.transactionDate!.formatted(.dateTime.day().month().year())
                                         : "-")
                                        .frame(width: 90, alignment: .leading)
                                    Text(txn.symbol)
                                        .font(.system(size: 13, weight: .semibold, design: .monospaced))
                                        .foregroundColor(PythiaTheme.accentGold)
                                        .frame(width: 70, alignment: .leading)
                                    Text(txn.transactionType.uppercased())
                                        .font(.system(size: 11, weight: .semibold))
                                        .foregroundColor(txnTypeColor(txn.transactionType))
                                        .frame(width: 70, alignment: .leading)
                                    Text(String(format: "%.2f", txn.quantity))
                                        .frame(width: 80, alignment: .trailing)
                                    Text(String(format: "%.2f", txn.price))
                                        .frame(width: 90, alignment: .trailing)
                                    Text(PythiaTheme.formatCurrency(txn.totalAmount))
                                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                                        .frame(width: 110, alignment: .trailing)
                                }
                                .font(.system(size: 13, design: .monospaced))
                                .foregroundColor(PythiaTheme.textSecondary)
                                .padding(.horizontal)
                                .padding(.vertical, 4)
                            }
                        }
                    }
                    .padding()
                    .pythiaCard()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            await loadAll()
        }
        .onChange(of: portfolioId) {
            Task { await loadAll() }
        }
        .confirmationDialog(
            "Delete Portfolio",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) { performDeletePortfolio() }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This portfolio will be deactivated. This action cannot be easily undone.")
        }
        .sheet(isPresented: $showEditSheet) {
            if let detail = detail {
                EditPortfolioSheet(detail: detail) {
                    Task { await loadAll() }
                }
            }
        }
        .sheet(isPresented: $showAddHolding) {
            AddHoldingSheet(portfolioId: portfolioId) {
                Task { await loadAll() }
            }
        }
        .sheet(isPresented: $showAddTransaction) {
            if let detail = detail {
                AddTransactionSheet(portfolioId: portfolioId, holdings: detail.holdings) {
                    Task { await loadAll() }
                }
            }
        }
    }

    // MARK: - Data Loading

    private func loadAll() async {
        isLoading = true
        errorMessage = nil
        do {
            async let detailFetch = db.fetchPortfolio(id: portfolioId)
            async let txnFetch = db.fetchTransactions(portfolioId: portfolioId, limit: 5)
            detail = try await detailFetch
            transactions = try await txnFetch
        } catch {
            errorMessage = "Failed to load portfolio: \(error.localizedDescription)"
        }
        isLoading = false
    }

    // MARK: - Actions

    private func deleteHolding(_ holding: Holding) {
        Task {
            do {
                try await db.deleteHolding(portfolioId: portfolioId, assetId: holding.assetId)
                await loadAll()
            } catch {
                errorMessage = "Failed to remove holding: \(error.localizedDescription)"
            }
        }
    }

    private func performDeletePortfolio() {
        Task {
            do {
                try await db.deletePortfolio(id: portfolioId)
                onDelete?()
            } catch {
                errorMessage = "Failed to delete portfolio: \(error.localizedDescription)"
            }
        }
    }

    private func txnTypeColor(_ type: String) -> Color {
        switch type {
        case "buy": return PythiaTheme.profit
        case "sell": return PythiaTheme.loss
        case "dividend": return PythiaTheme.accentGold
        default: return PythiaTheme.textSecondary
        }
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

// MARK: - Edit Portfolio Sheet

struct EditPortfolioSheet: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var db: DatabaseService
    let detail: PortfolioDetail
    var onSaved: () -> Void

    @State private var name: String = ""
    @State private var description: String = ""
    @State private var benchmark: String = ""
    @State private var riskFreeRate: String = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 20) {
            Text("Edit Portfolio")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            Form {
                TextField("Name", text: $name)
                TextField("Description", text: $description)
                TextField("Benchmark Symbol", text: $benchmark)
                TextField("Risk-Free Rate", text: $riskFreeRate)
            }
            .formStyle(.grouped)

            if let errorMessage = errorMessage {
                Text(errorMessage)
                    .foregroundColor(PythiaTheme.errorRed)
                    .font(PythiaTheme.caption())
            }

            HStack {
                Button("Cancel") { dismiss() }
                    .buttonStyle(.plain)
                Spacer()
                Button("Save") { save() }
                    .disabled(name.isEmpty || isSaving)
                    .buttonStyle(.borderedProminent)
                    .tint(Color(hex: "1E40AF"))
            }
        }
        .padding(24)
        .frame(width: 400, height: 380)
        .background(PythiaTheme.backgroundMedium)
        .onAppear {
            name = detail.name
            description = detail.description ?? ""
            benchmark = detail.benchmarkSymbol ?? "^SET"
            riskFreeRate = String(format: "%.4f", detail.riskFreeRate ?? 0.02)
        }
    }

    private func save() {
        isSaving = true
        errorMessage = nil
        Task {
            do {
                let request = PortfolioUpdateRequest(
                    name: name,
                    description: description.isEmpty ? nil : description,
                    benchmarkSymbol: benchmark.isEmpty ? nil : benchmark,
                    riskFreeRate: Double(riskFreeRate)
                )
                try await db.updatePortfolio(id: detail.portfolioId, request: request)
                onSaved()
                dismiss()
            } catch {
                errorMessage = "Failed to update: \(error.localizedDescription)"
            }
            isSaving = false
        }
    }
}

// MARK: - Add Holding Sheet

struct AddHoldingSheet: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var db: DatabaseService
    let portfolioId: String
    var onAdded: () -> Void

    @State private var selectedAssetId: String?
    @State private var weight: String = ""
    @State private var quantity: String = ""
    @State private var averageCost: String = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 20) {
            Text("Add Holding")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            VStack(alignment: .leading, spacing: 12) {
                Text("Asset")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                AssetPickerView(selectedId: $selectedAssetId)

                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Weight (0-1)")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("0.10", text: $weight)
                            .textFieldStyle(.roundedBorder)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Quantity")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("100", text: $quantity)
                            .textFieldStyle(.roundedBorder)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Avg Cost")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("25.50", text: $averageCost)
                            .textFieldStyle(.roundedBorder)
                    }
                }
            }

            if let errorMessage = errorMessage {
                Text(errorMessage)
                    .foregroundColor(PythiaTheme.errorRed)
                    .font(PythiaTheme.caption())
            }

            HStack {
                Button("Cancel") { dismiss() }
                    .buttonStyle(.plain)
                Spacer()
                Button("Add") { addHolding() }
                    .disabled(selectedAssetId == nil || weight.isEmpty || isSaving)
                    .buttonStyle(.borderedProminent)
                    .tint(Color(hex: "1E40AF"))
            }
        }
        .padding(24)
        .frame(width: 440, height: 340)
        .background(PythiaTheme.backgroundMedium)
    }

    private func addHolding() {
        guard let assetId = selectedAssetId,
              let w = Double(weight) else {
            errorMessage = "Please select an asset and enter a valid weight."
            return
        }
        isSaving = true
        errorMessage = nil
        Task {
            do {
                let request = HoldingCreateRequest(
                    assetId: assetId,
                    weight: w,
                    quantity: Double(quantity),
                    averageCost: Double(averageCost)
                )
                try await db.addHolding(portfolioId: portfolioId, request: request)
                onAdded()
                dismiss()
            } catch {
                errorMessage = "Failed to add holding: \(error.localizedDescription)"
            }
            isSaving = false
        }
    }
}

// MARK: - Add Transaction Sheet

struct AddTransactionSheet: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var db: DatabaseService
    let portfolioId: String
    let holdings: [Holding]
    var onAdded: () -> Void

    @State private var selectedAssetId: String?
    @State private var transactionType = "buy"
    @State private var quantity: String = ""
    @State private var price: String = ""
    @State private var fees: String = "0"
    @State private var taxes: String = "0"
    @State private var transactionDate = Date()
    @State private var notes: String = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

    private let types = ["buy", "sell", "dividend"]

    private var computedTotal: Double {
        let qty = Double(quantity) ?? 0
        let px = Double(price) ?? 0
        let f = Double(fees) ?? 0
        let t = Double(taxes) ?? 0
        return qty * px + f + t
    }

    var body: some View {
        VStack(spacing: 16) {
            Text("Add Transaction")
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            VStack(alignment: .leading, spacing: 12) {
                Text("Asset")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                AssetPickerView(selectedId: $selectedAssetId)

                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Type")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        Picker("Type", selection: $transactionType) {
                            ForEach(types, id: \.self) { Text($0.uppercased()).tag($0) }
                        }
                        .labelsHidden()
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Quantity")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("100", text: $quantity)
                            .textFieldStyle(.roundedBorder)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Price")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("25.50", text: $price)
                            .textFieldStyle(.roundedBorder)
                    }
                }

                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Fees")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("0", text: $fees)
                            .textFieldStyle(.roundedBorder)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Taxes")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("0", text: $taxes)
                            .textFieldStyle(.roundedBorder)
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Date")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                        DatePicker("", selection: $transactionDate, displayedComponents: .date)
                            .labelsHidden()
                    }
                }

                HStack {
                    Text("Total:")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text(PythiaTheme.formatCurrency(computedTotal))
                        .font(.system(size: 16, weight: .bold, design: .monospaced))
                        .foregroundColor(PythiaTheme.accentGold)
                }

                TextField("Notes (optional)", text: $notes)
                    .textFieldStyle(.roundedBorder)
            }

            if let errorMessage = errorMessage {
                Text(errorMessage)
                    .foregroundColor(PythiaTheme.errorRed)
                    .font(PythiaTheme.caption())
            }

            HStack {
                Button("Cancel") { dismiss() }
                    .buttonStyle(.plain)
                Spacer()
                Button("Record") { addTransaction() }
                    .disabled(selectedAssetId == nil || quantity.isEmpty || price.isEmpty || isSaving)
                    .buttonStyle(.borderedProminent)
                    .tint(Color(hex: "1E40AF"))
            }
        }
        .padding(24)
        .frame(width: 480, height: 480)
        .background(PythiaTheme.backgroundMedium)
    }

    private func addTransaction() {
        guard let assetId = selectedAssetId,
              let qty = Double(quantity),
              let px = Double(price) else {
            errorMessage = "Please select an asset and enter valid quantity/price."
            return
        }
        isSaving = true
        errorMessage = nil

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateStr = formatter.string(from: transactionDate)

        Task {
            do {
                let request = TransactionCreateRequest(
                    assetId: assetId,
                    transactionType: transactionType,
                    quantity: qty,
                    price: px,
                    fees: Double(fees) ?? 0,
                    taxes: Double(taxes) ?? 0,
                    totalAmount: computedTotal,
                    transactionDate: dateStr,
                    notes: notes.isEmpty ? nil : notes
                )
                try await db.addTransaction(portfolioId: portfolioId, request: request)
                onAdded()
                dismiss()
            } catch {
                errorMessage = "Failed to record transaction: \(error.localizedDescription)"
            }
            isSaving = false
        }
    }
}
