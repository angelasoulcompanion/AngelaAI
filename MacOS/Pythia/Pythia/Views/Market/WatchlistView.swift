//
//  WatchlistView.swift
//  Pythia — Watchlist CRUD
//

import SwiftUI

struct WatchlistView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var watchlists: [Watchlist] = []
    @State private var selectedWatchlist: WatchlistDetail?
    @State private var isLoading = true

    // Create watchlist
    @State private var showCreateSheet = false
    @State private var newName = ""
    @State private var newDescription = ""

    // Add item by symbol
    @State private var showAddItemSheet = false
    @State private var symbolToAdd = ""
    @State private var isAddingSymbol = false
    @State private var addError: String?

    // Sorting
    @State private var sortColumn: SortColumn = .symbol
    @State private var sortAscending = true

    private enum SortColumn: String {
        case symbol, name, type, sector
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                Text("Watchlists")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Button(action: { showCreateSheet = true }) {
                    Label("New Watchlist", systemImage: "plus")
                }
                .pythiaPrimaryButton()
            }
            .padding(.horizontal, PythiaTheme.largeSpacing)
            .padding(.top, PythiaTheme.largeSpacing)
            .padding(.bottom, PythiaTheme.spacing)

            if isLoading {
                LoadingView("Loading watchlists...")
            } else if watchlists.isEmpty {
                EmptyStateView(
                    icon: "star",
                    title: "No Watchlists",
                    message: "Create a watchlist to track your favorite assets.",
                    actionTitle: "New Watchlist"
                ) {
                    showCreateSheet = true
                }
            } else {
                HStack(alignment: .top, spacing: 0) {
                    // Left: Watchlist list
                    ScrollView {
                        VStack(spacing: 8) {
                            ForEach(watchlists) { wl in
                                watchlistRow(wl)
                            }
                        }
                        .padding(PythiaTheme.spacing)
                    }
                    .frame(width: 260)
                    .background(PythiaTheme.surfaceBackground.opacity(0.15))

                    // Divider between panels
                    Divider()
                        .background(PythiaTheme.textTertiary.opacity(0.3))

                    // Right: Selected watchlist detail
                    ScrollView {
                        if let detail = selectedWatchlist {
                            watchlistDetailPanel(detail)
                                .padding(PythiaTheme.largeSpacing)
                        } else {
                            EmptyStateView(
                                icon: "star",
                                title: "Select a Watchlist",
                                message: "Choose a watchlist to view its items."
                            )
                            .padding(PythiaTheme.largeSpacing)
                        }
                    }
                }
                .frame(maxHeight: .infinity)
            }
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadWatchlists() }
        .sheet(isPresented: $showCreateSheet) { createWatchlistSheet }
        .sheet(isPresented: $showAddItemSheet) { addItemSheet }
    }

    // MARK: - Watchlist Row

    private func watchlistRow(_ wl: Watchlist) -> some View {
        HStack {
            Button(action: { loadWatchlist(wl.watchlistId) }) {
                HStack {
                    Image(systemName: "star.fill")
                        .foregroundColor(PythiaTheme.accentGold)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(wl.name)
                            .font(PythiaTheme.heading())
                            .foregroundColor(PythiaTheme.textPrimary)
                        Text("\(wl.itemCount ?? 0) items")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                    }
                    Spacer()
                }
                .padding(10)
                .background(
                    selectedWatchlist?.watchlistId == wl.watchlistId
                    ? PythiaTheme.secondaryBlue.opacity(0.25)
                    : PythiaTheme.surfaceBackground.opacity(0.5)
                )
                .cornerRadius(PythiaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)

            // Delete button
            Button(action: { deleteWatchlist(wl.watchlistId) }) {
                Image(systemName: "trash")
                    .font(.system(size: 12))
                    .foregroundColor(PythiaTheme.loss.opacity(0.7))
            }
            .buttonStyle(.plain)
            .help("Delete watchlist")
        }
    }

    // MARK: - Detail Panel

    private func watchlistDetailPanel(_ detail: WatchlistDetail) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(detail.name)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                if let desc = detail.description, !desc.isEmpty {
                    Text("— \(desc)")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                Spacer()
                Button(action: {
                    symbolToAdd = ""
                    addError = nil
                    showAddItemSheet = true
                }) {
                    Label("Add Asset", systemImage: "plus.circle")
                        .font(.system(size: 13, weight: .medium))
                }
                .buttonStyle(.plain)
                .foregroundColor(PythiaTheme.secondaryBlue)
            }

            if detail.items.isEmpty {
                Text("No assets in this watchlist yet.")
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textTertiary)
                    .padding(.vertical, 20)
            } else {
                // Sortable header row
                HStack {
                    sortableHeader("Symbol", column: .symbol, width: 80)
                    sortableHeaderFlex("Name", column: .name)
                    sortableHeader("Type", column: .type, width: 100)
                    sortableHeader("Sector", column: .sector, width: 120)
                    Text("").frame(width: 30)
                }
                .padding(.horizontal, 8)

                Divider().background(PythiaTheme.textTertiary.opacity(0.3))

                ForEach(sortedItems(detail.items)) { item in
                    HStack {
                        Text(item.symbol)
                            .font(.system(size: 13, weight: .semibold, design: .monospaced))
                            .foregroundColor(PythiaTheme.accentGold)
                            .frame(width: 80, alignment: .leading)
                        Text(item.assetName ?? "")
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textPrimary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                        Text((item.assetType ?? "").replacingOccurrences(of: "_", with: " ").capitalized)
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 100, alignment: .leading)
                        Text(item.sector ?? "—")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textTertiary)
                            .frame(width: 120, alignment: .leading)
                        Button(action: { removeItem(watchlistId: detail.watchlistId, assetId: item.assetId) }) {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 14))
                                .foregroundColor(PythiaTheme.loss.opacity(0.6))
                        }
                        .buttonStyle(.plain)
                        .help("Remove from watchlist")
                        .frame(width: 30)
                    }
                    .padding(.vertical, 4)
                    .padding(.horizontal, 8)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Sorting Helpers

    private func sortableHeader(_ title: String, column: SortColumn, width: CGFloat) -> some View {
        Button(action: {
            if sortColumn == column {
                sortAscending.toggle()
            } else {
                sortColumn = column
                sortAscending = true
            }
        }) {
            HStack(spacing: 4) {
                Text(title)
                if sortColumn == column {
                    Image(systemName: sortAscending ? "chevron.up" : "chevron.down")
                        .font(.system(size: 8, weight: .bold))
                        .foregroundColor(PythiaTheme.accentGold)
                }
            }
            .font(.system(size: 11, weight: .semibold))
            .foregroundColor(sortColumn == column ? PythiaTheme.accentGold : PythiaTheme.textTertiary)
        }
        .buttonStyle(.plain)
        .frame(width: width, alignment: .leading)
    }

    private func sortableHeaderFlex(_ title: String, column: SortColumn) -> some View {
        Button(action: {
            if sortColumn == column {
                sortAscending.toggle()
            } else {
                sortColumn = column
                sortAscending = true
            }
        }) {
            HStack(spacing: 4) {
                Text(title)
                if sortColumn == column {
                    Image(systemName: sortAscending ? "chevron.up" : "chevron.down")
                        .font(.system(size: 8, weight: .bold))
                        .foregroundColor(PythiaTheme.accentGold)
                }
            }
            .font(.system(size: 11, weight: .semibold))
            .foregroundColor(sortColumn == column ? PythiaTheme.accentGold : PythiaTheme.textTertiary)
        }
        .buttonStyle(.plain)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func sortedItems(_ items: [WatchlistItem]) -> [WatchlistItem] {
        items.sorted { a, b in
            let result: Bool
            switch sortColumn {
            case .symbol:
                result = a.symbol.localizedCaseInsensitiveCompare(b.symbol) == .orderedAscending
            case .name:
                result = (a.assetName ?? "").localizedCaseInsensitiveCompare(b.assetName ?? "") == .orderedAscending
            case .type:
                result = (a.assetType ?? "").localizedCaseInsensitiveCompare(b.assetType ?? "") == .orderedAscending
            case .sector:
                result = (a.sector ?? "").localizedCaseInsensitiveCompare(b.sector ?? "") == .orderedAscending
            }
            return sortAscending ? result : !result
        }
    }

    // MARK: - Create Sheet

    private var createWatchlistSheet: some View {
        VStack(spacing: 16) {
            Text("New Watchlist")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            TextField("Name", text: $newName)
                .textFieldStyle(.roundedBorder)
                .frame(width: 300)

            TextField("Description (optional)", text: $newDescription)
                .textFieldStyle(.roundedBorder)
                .frame(width: 300)

            HStack(spacing: 12) {
                Button("Cancel") { showCreateSheet = false }
                    .keyboardShortcut(.cancelAction)
                Button("Create") {
                    Task { await createWatchlist() }
                }
                .pythiaPrimaryButton()
                .disabled(newName.trimmingCharacters(in: .whitespaces).isEmpty)
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(24)
        .frame(width: 360)
    }

    // MARK: - Add Item Sheet (by symbol)

    private var addItemSheet: some View {
        VStack(spacing: 16) {
            Text("Add Stock by Symbol")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Text("Enter a stock symbol. It will be fetched from Yahoo Finance automatically.")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
                .multilineTextAlignment(.center)
                .frame(width: 300)

            TextField("e.g. AAPL, SE, PTT.BK", text: $symbolToAdd)
                .textFieldStyle(.roundedBorder)
                .frame(width: 300)
                .onSubmit {
                    if !symbolToAdd.trimmingCharacters(in: .whitespaces).isEmpty {
                        Task { await addItemBySymbol() }
                    }
                }

            if isAddingSymbol {
                HStack(spacing: 8) {
                    ProgressView().scaleEffect(0.8)
                    Text("Looking up \(symbolToAdd.uppercased())...")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }
            }

            if let error = addError {
                Text(error)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.errorRed)
            }

            HStack(spacing: 12) {
                Button("Cancel") {
                    showAddItemSheet = false
                    symbolToAdd = ""
                    addError = nil
                }
                .keyboardShortcut(.cancelAction)
                Button("Add") {
                    Task { await addItemBySymbol() }
                }
                .pythiaPrimaryButton()
                .disabled(symbolToAdd.trimmingCharacters(in: .whitespaces).isEmpty || isAddingSymbol)
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(24)
        .frame(width: 380)
    }

    // MARK: - Actions

    private func loadWatchlists() async {
        isLoading = true
        do { watchlists = try await db.fetchWatchlists() } catch {}
        isLoading = false
    }

    private func loadWatchlist(_ id: String) {
        Task {
            do { selectedWatchlist = try await db.fetchWatchlist(id: id) } catch {}
        }
    }

    private func createWatchlist() async {
        let desc = newDescription.trimmingCharacters(in: .whitespaces)
        _ = try? await db.createWatchlist(
            name: newName.trimmingCharacters(in: .whitespaces),
            description: desc.isEmpty ? nil : desc
        )
        newName = ""
        newDescription = ""
        showCreateSheet = false
        await loadWatchlists()
    }

    private func deleteWatchlist(_ id: String) {
        Task {
            try? await db.deleteWatchlist(id: id)
            if selectedWatchlist?.watchlistId == id { selectedWatchlist = nil }
            await loadWatchlists()
        }
    }

    private func addItemBySymbol() async {
        guard let wlId = selectedWatchlist?.watchlistId else { return }
        let symbol = symbolToAdd.trimmingCharacters(in: .whitespaces)
        guard !symbol.isEmpty else { return }

        isAddingSymbol = true
        addError = nil
        do {
            _ = try await db.addWatchlistItemBySymbol(watchlistId: wlId, symbol: symbol)
            showAddItemSheet = false
            symbolToAdd = ""
            loadWatchlist(wlId)
            do { watchlists = try await db.fetchWatchlists() } catch {}
        } catch {
            addError = "Failed to add '\(symbol)': \(error.localizedDescription)"
        }
        isAddingSymbol = false
    }

    private func removeItem(watchlistId: String, assetId: String) {
        Task {
            try? await db.removeWatchlistItem(watchlistId: watchlistId, assetId: assetId)
            loadWatchlist(watchlistId)
            do { watchlists = try await db.fetchWatchlists() } catch {}
        }
    }
}
