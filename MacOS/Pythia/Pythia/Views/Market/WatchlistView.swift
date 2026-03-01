//
//  WatchlistView.swift
//  Pythia
//

import SwiftUI

struct WatchlistView: View {
    @EnvironmentObject var db: DatabaseService
    @State private var watchlists: [Watchlist] = []
    @State private var selectedWatchlist: WatchlistDetail?
    @State private var isLoading = true

    var body: some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text("Watchlists")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
            }
            .padding(.horizontal, PythiaTheme.largeSpacing)
            .padding(.top, PythiaTheme.largeSpacing)

            if isLoading {
                LoadingView("Loading watchlists...")
            } else if watchlists.isEmpty {
                EmptyStateView(
                    icon: "star",
                    title: "No Watchlists",
                    message: "Create a watchlist to track your favorite assets."
                )
            } else {
                HStack(alignment: .top, spacing: PythiaTheme.spacing) {
                    // Watchlist selector
                    VStack(spacing: 8) {
                        ForEach(watchlists) { wl in
                            Button(action: { loadWatchlist(wl.watchlistId) }) {
                                HStack {
                                    Image(systemName: "star.fill")
                                        .foregroundColor(PythiaTheme.accentGold)
                                    VStack(alignment: .leading) {
                                        Text(wl.name)
                                            .font(PythiaTheme.heading())
                                            .foregroundColor(PythiaTheme.textPrimary)
                                        Text("\(wl.itemCount ?? 0) items")
                                            .font(PythiaTheme.caption())
                                            .foregroundColor(PythiaTheme.textTertiary)
                                    }
                                    Spacer()
                                }
                                .padding()
                                .background(
                                    selectedWatchlist?.watchlistId == wl.watchlistId
                                    ? PythiaTheme.secondaryBlue.opacity(0.15)
                                    : PythiaTheme.surfaceBackground.opacity(0.3)
                                )
                                .cornerRadius(PythiaTheme.smallCornerRadius)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .frame(width: 250)

                    // Watchlist items
                    if let detail = selectedWatchlist {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(detail.name)
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)

                            ForEach(detail.items) { item in
                                HStack {
                                    Text(item.symbol)
                                        .font(.system(size: 13, weight: .semibold, design: .monospaced))
                                        .foregroundColor(PythiaTheme.accentGold)
                                        .frame(width: 80, alignment: .leading)
                                    Text(item.assetName ?? "")
                                        .font(PythiaTheme.body())
                                        .foregroundColor(PythiaTheme.textPrimary)
                                    Spacer()
                                    Text(item.assetType ?? "")
                                        .font(PythiaTheme.caption())
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }
                                .padding(.vertical, 4)
                            }
                        }
                        .padding()
                        .pythiaCard()
                    } else {
                        EmptyStateView(
                            icon: "star",
                            title: "Select a Watchlist",
                            message: "Choose a watchlist to view its items."
                        )
                    }
                }
                .padding(.horizontal, PythiaTheme.largeSpacing)
            }

            Spacer()
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            do {
                watchlists = try await db.fetchWatchlists()
            } catch { }
            isLoading = false
        }
    }

    private func loadWatchlist(_ id: String) {
        Task {
            do {
                selectedWatchlist = try await db.fetchWatchlist(id: id)
            } catch {
                print("Error loading watchlist: \(error)")
            }
        }
    }
}
