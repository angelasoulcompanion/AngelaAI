//
//  DJayProContextSelector.swift
//  Angela Brain Dashboard
//
//  Context selector for DJ Angela x djay Pro — moods + wine sub-selector
//

import SwiftUI

// MARK: - Context Enum

enum DJayProContext: String, CaseIterable, Identifiable {
    case wine = "wine"
    case chill = "chill"
    case party = "party"
    case focus = "focus"
    case relax = "relax"
    case vibe = "vibe"
    case bedtime = "bedtime"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .wine: return "Wine"
        case .chill: return "Chill"
        case .party: return "Party"
        case .focus: return "Focus"
        case .relax: return "Relax"
        case .vibe: return "Vibe"
        case .bedtime: return "Bed Time"
        }
    }

    var emoji: String {
        switch self {
        case .wine: return "\u{1f377}"
        case .chill: return "\u{1f9ca}"
        case .party: return "\u{1f389}"
        case .focus: return "\u{1f3af}"
        case .relax: return "\u{1f60c}"
        case .vibe: return "\u{1f3a7}"
        case .bedtime: return "\u{1f634}"
        }
    }

    var color: Color {
        switch self {
        case .wine: return Color(hex: "7C3AED")     // Deep purple
        case .chill: return Color(hex: "06B6D4")     // Cyan
        case .party: return Color(hex: "F43F5E")     // Rose
        case .focus: return Color(hex: "F59E0B")     // Amber
        case .relax: return Color(hex: "10B981")     // Emerald
        case .vibe: return Color(hex: "8B5CF6")      // Violet
        case .bedtime: return Color(hex: "6366F1")   // Indigo
        }
    }
}

// MARK: - Wine Categories for Sub-Selector

struct WineCategory: Identifiable {
    let id = UUID()
    let name: String
    let emoji: String
    let wines: [(key: String, name: String)]
}

let wineCategories: [WineCategory] = [
    WineCategory(name: "Bold Reds", emoji: "\u{1f377}", wines: [
        ("primitivo", "Primitivo"),
        ("cabernet_sauvignon", "Cabernet Sauvignon"),
        ("malbec", "Malbec"),
        ("shiraz", "Shiraz"),
    ]),
    WineCategory(name: "Elegant Reds", emoji: "\u{1f377}", wines: [
        ("pinot_noir", "Pinot Noir"),
        ("merlot", "Merlot"),
        ("super_tuscan", "Super Tuscan"),
        ("sangiovese", "Sangiovese"),
        ("nebbiolo", "Nebbiolo"),
    ]),
    WineCategory(name: "White & Light", emoji: "\u{1f942}", wines: [
        ("chardonnay", "Chardonnay"),
        ("sauvignon_blanc", "Sauvignon Blanc"),
        ("riesling", "Riesling"),
        ("pinot_grigio", "Pinot Grigio"),
    ]),
    WineCategory(name: "Sparkling", emoji: "\u{1f37e}", wines: [
        ("champagne", "Champagne"),
        ("prosecco", "Prosecco"),
        ("cava", "Cava"),
    ]),
    WineCategory(name: "Rose & Sweet", emoji: "\u{1f339}", wines: [
        ("rose", "Rose"),
        ("moscato", "Moscato"),
        ("port", "Port"),
    ]),
]

// MARK: - Context Selector View

struct DJayProContextSelector: View {
    @Binding var selectedContext: DJayProContext?
    @Binding var selectedWine: String?
    var onGenerate: () -> Void

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 12), count: 4)

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Section header
            HStack(spacing: 8) {
                Image(systemName: "waveform.circle.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 18))
                Text("Select Context")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Context grid
            LazyVGrid(columns: columns, spacing: 12) {
                ForEach(DJayProContext.allCases) { ctx in
                    contextCard(ctx)
                }
            }

            // Wine sub-selector (only when wine is selected)
            if selectedContext == .wine {
                wineSubSelector
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
        .padding(20)
        .angelaCard()
        .animation(.easeInOut(duration: 0.25), value: selectedContext)
    }

    // MARK: - Context Card

    private func contextCard(_ ctx: DJayProContext) -> some View {
        let isSelected = selectedContext == ctx
        return Button {
            withAnimation(.easeInOut(duration: 0.2)) {
                if selectedContext == ctx {
                    selectedContext = nil
                    selectedWine = nil
                } else {
                    selectedContext = ctx
                    if ctx != .wine {
                        selectedWine = nil
                        onGenerate()
                    }
                }
            }
        } label: {
            VStack(spacing: 8) {
                Text(ctx.emoji)
                    .font(.system(size: 28))
                Text(ctx.displayName)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(isSelected ? .white : AngelaTheme.textSecondary)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? ctx.color.opacity(0.8) : AngelaTheme.backgroundLight.opacity(0.5))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? ctx.color : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Wine Sub-Selector

    private var wineSubSelector: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 6) {
                Text("\u{1f377}")
                    .font(.system(size: 16))
                Text("Choose Your Wine")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }
            .padding(.top, 8)

            ForEach(wineCategories) { category in
                VStack(alignment: .leading, spacing: 6) {
                    // Category header
                    HStack(spacing: 4) {
                        Text(category.emoji)
                            .font(.system(size: 12))
                        Text(category.name)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(AngelaTheme.textSecondary)
                    }

                    // Wine pills
                    wineFlowLayout(wines: category.wines)
                }
            }
        }
    }

    @ViewBuilder
    private func wineFlowLayout(wines: [(key: String, name: String)]) -> some View {
        let pillColumns = Array(repeating: GridItem(.flexible(), spacing: 6), count: 3)
        LazyVGrid(columns: pillColumns, spacing: 6) {
            ForEach(wines, id: \.key) { wine in
                winePill(key: wine.key, name: wine.name)
            }
        }
    }

    private func winePill(key: String, name: String) -> some View {
        let isSelected = selectedWine == key
        return Button {
            withAnimation(.easeInOut(duration: 0.2)) {
                selectedWine = key
                onGenerate()
            }
        } label: {
            Text(name)
                .font(.system(size: 12, weight: .medium))
                .lineLimit(1)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .frame(maxWidth: .infinity)
                .background(
                    Capsule().fill(isSelected
                        ? DJayProContext.wine.color.opacity(0.8)
                        : AngelaTheme.backgroundLight.opacity(0.5))
                )
                .foregroundColor(isSelected ? .white : AngelaTheme.textSecondary)
        }
        .buttonStyle(.plain)
    }
}
