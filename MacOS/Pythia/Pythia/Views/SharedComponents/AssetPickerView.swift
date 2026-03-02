//
//  AssetPickerView.swift
//  Pythia — Reusable asset selection picker
//
//  Replaces duplicated Asset Picker + loadAssets() across
//  BacktestView, MonteCarloView, StatisticsView, SentimentView, ForecastView.
//

import SwiftUI

/// Self-loading asset picker. Fetches assets on appear, presents a Picker bound to `selectedId`.
struct AssetPickerView: View {
    @EnvironmentObject var db: DatabaseService
    @Binding var selectedId: String?

    /// Whether to show asset name alongside symbol (e.g. "AAPL — Apple Inc.")
    var showName: Bool = false

    @State private var assets: [Asset] = []

    var body: some View {
        Picker("Asset", selection: Binding(
            get: { selectedId ?? "" },
            set: { selectedId = $0.isEmpty ? nil : $0 }
        )) {
            Text("Select Asset").tag("")
            ForEach(assets) { a in
                if showName {
                    Text("\(a.symbol) — \(a.name)").tag(a.assetId)
                } else {
                    Text(a.symbol).tag(a.assetId)
                }
            }
        }
        .frame(width: showName ? 250 : 200)
        .task {
            do { assets = try await db.fetchAssets() } catch {}
        }
    }
}
