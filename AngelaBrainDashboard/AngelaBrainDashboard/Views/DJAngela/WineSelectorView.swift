//
//  WineSelectorView.swift
//  Angela Brain Dashboard
//
//  Wine selector popover for DJ Angela wine-to-music pairing
//

import SwiftUI

struct WineSelectorView: View {
    let onSelect: (String) -> Void
    /// Reaction counts per wine: [wine_key: ["up": N, "down": N, "love": N]]
    var reactions: [String: [String: Int]] = [:]

    private let categories: [(emoji: String, name: String, wines: [(key: String, name: String)])] = [
        ("\u{1f377}", "Bold Reds", [
            ("primitivo", "Primitivo"),
            ("cabernet_sauvignon", "Cabernet Sauvignon"),
            ("malbec", "Malbec"),
            ("shiraz", "Shiraz"),
        ]),
        ("\u{1f377}", "Elegant Reds", [
            ("pinot_noir", "Pinot Noir"),
            ("merlot", "Merlot"),
            ("super_tuscan", "Super Tuscan"),
            ("sangiovese", "Sangiovese"),
            ("nebbiolo", "Nebbiolo"),
        ]),
        ("\u{1f942}", "White & Light", [
            ("chardonnay", "Chardonnay"),
            ("sauvignon_blanc", "Sauvignon Blanc"),
            ("riesling", "Riesling"),
            ("pinot_grigio", "Pinot Grigio"),
        ]),
        ("\u{1f37e}", "Sparkling", [
            ("champagne", "Champagne"),
            ("prosecco", "Prosecco"),
            ("cava", "Cava"),
        ]),
        ("\u{1f339}", "Rose & Sweet", [
            ("rose", "Rose"),
            ("moscato", "Moscato"),
            ("port", "Port"),
        ]),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Header
            HStack(spacing: 6) {
                Text("\u{1f377}")
                    .font(.system(size: 16))
                Text("Wine Pairing")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }
            .padding(.bottom, 2)

            ForEach(Array(categories.enumerated()), id: \.offset) { _, category in
                VStack(alignment: .leading, spacing: 6) {
                    // Category header
                    HStack(spacing: 4) {
                        Text(category.emoji)
                            .font(.system(size: 12))
                        Text(category.name)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(AngelaTheme.textSecondary)
                    }

                    // Wine pills (flow layout via wrapping HStacks)
                    wineFlowLayout(wines: category.wines)
                }
            }
        }
        .padding(16)
        .frame(width: 280)
        .background(AngelaTheme.cardBackground)
    }

    @ViewBuilder
    private func wineFlowLayout(wines: [(key: String, name: String)]) -> some View {
        // Two columns for the wine pills
        let columns = Array(repeating: GridItem(.flexible(), spacing: 6), count: 2)
        LazyVGrid(columns: columns, spacing: 6) {
            ForEach(wines, id: \.key) { wine in
                Button {
                    onSelect(wine.key)
                } label: {
                    HStack(spacing: 4) {
                        Text(wine.name)
                            .font(.system(size: 12, weight: .medium))
                            .lineLimit(1)

                        // Reaction summary icons
                        if let counts = reactions[wine.key] {
                            reactionSummary(counts)
                        }
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .frame(maxWidth: .infinity)
                    .background(
                        Capsule().fill(Color.purple.opacity(0.12))
                    )
                    .foregroundColor(AngelaTheme.secondaryPurple)
                }
                .buttonStyle(.plain)
            }
        }
    }

    @ViewBuilder
    private func reactionSummary(_ counts: [String: Int]) -> some View {
        let up = counts["up"] ?? 0
        let love = counts["love"] ?? 0
        // Only show if there are any reactions
        if up > 0 || love > 0 {
            HStack(spacing: 2) {
                if up > 0 {
                    Text("\u{1f44d}\(up)")
                        .font(.system(size: 9))
                }
                if love > 0 {
                    Text("\u{2764}\u{fe0f}\(love)")
                        .font(.system(size: 9))
                }
            }
            .foregroundColor(AngelaTheme.textTertiary)
        }
    }
}
