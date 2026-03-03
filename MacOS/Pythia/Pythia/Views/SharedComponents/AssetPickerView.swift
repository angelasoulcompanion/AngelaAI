//
//  AssetPickerView.swift
//  Pythia — Searchable asset picker with sector filter
//

import SwiftUI

struct AssetPickerView: View {
    @EnvironmentObject var db: DatabaseService
    @Binding var selectedId: String?
    var showName: Bool = false

    @State private var assets: [Asset] = []
    @State private var searchText = ""
    @State private var selectedSector: String? = nil
    @State private var isOpen = false

    private var selectedSymbol: String {
        assets.first(where: { $0.assetId == selectedId })?.symbol ?? "Select Asset"
    }

    private var sectors: [String] {
        let raw = Set(assets.compactMap { $0.sector }).sorted()
        return raw
    }

    private var filtered: [Asset] {
        var list = assets

        // Sector filter
        if let sec = selectedSector {
            list = list.filter { $0.sector == sec }
        }

        // Text search
        if !searchText.isEmpty {
            let q = searchText.lowercased()
            list = list.filter {
                $0.symbol.lowercased().contains(q) || $0.name.lowercased().contains(q)
            }
        }

        return list
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Trigger button
            Button {
                withAnimation(.easeOut(duration: 0.15)) { isOpen.toggle() }
                if isOpen { searchText = "" }
            } label: {
                HStack(spacing: 6) {
                    Text("Asset")
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text(selectedSymbol)
                        .foregroundColor(selectedId != nil ? PythiaTheme.textPrimary : PythiaTheme.textTertiary)
                        .fontWeight(selectedId != nil ? .semibold : .regular)
                    Image(systemName: isOpen ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                .font(PythiaTheme.body())
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(PythiaTheme.backgroundMedium)
                .cornerRadius(6)
            }
            .buttonStyle(.plain)

            if isOpen {
                dropdownContent
            }
        }
        .task {
            do { assets = try await db.fetchAssets() } catch {}
        }
    }

    private var dropdownContent: some View {
        VStack(spacing: 0) {
            // Search field
            HStack(spacing: 6) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(PythiaTheme.textTertiary)
                    .font(.caption)
                TextField("Search symbol or name...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textPrimary)
                if !searchText.isEmpty {
                    Button { searchText = "" } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(PythiaTheme.textTertiary)
                            .font(.caption)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(PythiaTheme.backgroundDark)

            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

            // Sector chips
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 4) {
                    sectorChip("All", isSelected: selectedSector == nil) {
                        selectedSector = nil
                    }
                    ForEach(sectors, id: \.self) { sec in
                        sectorChip(shortSector(sec), isSelected: selectedSector == sec) {
                            selectedSector = selectedSector == sec ? nil : sec
                        }
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
            }
            .background(PythiaTheme.backgroundDark.opacity(0.5))

            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

            // Count
            HStack {
                Text("\(filtered.count) assets")
                    .font(.system(size: 10))
                    .foregroundColor(PythiaTheme.textTertiary)
                Spacer()
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 3)

            // Results
            ScrollView {
                LazyVStack(spacing: 0) {
                    ForEach(filtered) { asset in
                        assetRow(asset)
                    }
                }
            }
            .frame(maxHeight: 280)
        }
        .background(PythiaTheme.backgroundMedium)
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(PythiaTheme.textTertiary.opacity(0.3), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.3), radius: 8, y: 4)
        .frame(width: 380)
        .padding(.top, 4)
    }

    private func sectorChip(_ label: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: 10, weight: isSelected ? .semibold : .regular))
                .foregroundColor(isSelected ? PythiaTheme.backgroundDark : PythiaTheme.textSecondary)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(isSelected ? PythiaTheme.accentGold : PythiaTheme.backgroundDark)
                .cornerRadius(10)
        }
        .buttonStyle(.plain)
    }

    /// Shorten sector names for chips
    private func shortSector(_ sector: String) -> String {
        let map: [String: String] = [
            "Communication Services": "Comm",
            "Consumer Cyclical": "Consumer Cyc",
            "Consumer Defensive": "Consumer Def",
            "Financial Services": "Finance",
            "Basic Materials": "Materials",
            "Artificial Intelligence": "AI",
        ]
        return map[sector] ?? sector
    }

    private func assetRow(_ asset: Asset) -> some View {
        Button {
            selectedId = asset.assetId
            withAnimation(.easeOut(duration: 0.15)) { isOpen = false }
        } label: {
            HStack(spacing: 8) {
                Text(asset.symbol)
                    .font(PythiaTheme.body())
                    .fontWeight(.semibold)
                    .foregroundColor(asset.assetId == selectedId ? PythiaTheme.accentGold : PythiaTheme.textPrimary)
                    .frame(width: 90, alignment: .leading)

                Text(asset.name)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
                    .lineLimit(1)

                Spacer()

                if let sec = asset.sector {
                    Text(shortSector(sec))
                        .font(.system(size: 9))
                        .foregroundColor(PythiaTheme.textTertiary)
                }

                if asset.assetId == selectedId {
                    Image(systemName: "checkmark")
                        .font(.caption)
                        .foregroundColor(PythiaTheme.accentGold)
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(asset.assetId == selectedId
                        ? PythiaTheme.accentGold.opacity(0.1)
                        : Color.clear)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}
