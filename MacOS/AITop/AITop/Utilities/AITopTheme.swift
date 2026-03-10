//
//  AITopTheme.swift
//  AITop
//
//  Dark theme — Gigabyte AI TOP inspired (orange accent + dark background)
//

import SwiftUI
import Charts

struct AITopTheme {
    // MARK: - Accent Colors (Orange — Gigabyte AI TOP style)

    static let accentOrange = Color(hex: "FF6B00")
    static let brightOrange = Color(hex: "FF8C38")
    static let deepOrange = Color(hex: "CC5500")

    // MARK: - Secondary Accent (Cyan/Teal for contrast)

    static let accentCyan = Color(hex: "00D4FF")
    static let accentTeal = Color(hex: "00B4D8")

    // MARK: - Semantic Colors

    static let success = Color(hex: "22C55E")
    static let warning = Color(hex: "F59E0B")
    static let error = Color(hex: "EF4444")
    static let info = Color(hex: "3B82F6")

    // MARK: - Background Colors

    static let backgroundDark = Color(hex: "0A0A0F")
    static let backgroundMedium = Color(hex: "141420")
    static let cardBackground = Color(hex: "1A1A2E")
    static let surfaceBackground = Color(hex: "252540")

    // MARK: - Text Colors

    static let textPrimary = Color.white
    static let textSecondary = Color(hex: "9CA3AF")
    static let textTertiary = Color(hex: "6B7280")

    // MARK: - Gauge Colors

    static let gaugeLow = Color(hex: "22C55E")       // green < 40%
    static let gaugeMedium = Color(hex: "F59E0B")     // yellow 40-70%
    static let gaugeHigh = Color(hex: "EF4444")        // red > 70%

    static func gaugeColor(for percent: Double) -> Color {
        if percent < 40 { return gaugeLow }
        if percent < 70 { return gaugeMedium }
        return gaugeHigh
    }

    // MARK: - Gradients

    static let orangeGradient = LinearGradient(
        colors: [accentOrange, deepOrange],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let cardGradient = LinearGradient(
        colors: [cardBackground.opacity(0.9), cardBackground.opacity(0.5)],
        startPoint: .top,
        endPoint: .bottom
    )

    // MARK: - Spacing & Radius

    static let spacing: CGFloat = 16
    static let smallSpacing: CGFloat = 8
    static let largeSpacing: CGFloat = 24
    static let cornerRadius: CGFloat = 12
    static let smallCornerRadius: CGFloat = 8
    static let largeCornerRadius: CGFloat = 16

    // MARK: - Fonts

    static func title() -> Font { .system(size: 24, weight: .bold) }
    static func heading() -> Font { .system(size: 16, weight: .semibold) }
    static func headline() -> Font { .system(size: 18, weight: .semibold) }
    static func body() -> Font { .system(size: 14, weight: .regular) }
    static func caption() -> Font { .system(size: 12, weight: .regular) }
    static func number() -> Font { .system(size: 32, weight: .bold, design: .rounded) }
    static func gauge() -> Font { .system(size: 28, weight: .bold, design: .rounded) }
    static func monospace() -> Font { .system(size: 14, weight: .medium, design: .monospaced) }

    // MARK: - Helpers

    static func formatBytes(_ bytes: Int64) -> String {
        let gb = Double(bytes) / 1_073_741_824
        if gb >= 1 {
            return String(format: "%.1f GB", gb)
        }
        let mb = Double(bytes) / 1_048_576
        return String(format: "%.0f MB", mb)
    }

    static func formatPercent(_ value: Double) -> String {
        String(format: "%.1f%%", value)
    }
}

// MARK: - Color Extension for Hex

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - View Extensions

extension View {
    func aiTopCard() -> some View {
        self
            .background(AITopTheme.cardBackground)
            .cornerRadius(AITopTheme.cornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: AITopTheme.cornerRadius)
                    .stroke(AITopTheme.surfaceBackground, lineWidth: 1)
            )
    }

    func aiTopPrimaryButton() -> some View {
        self
            .padding(.horizontal, AITopTheme.spacing)
            .padding(.vertical, AITopTheme.smallSpacing)
            .background(AITopTheme.orangeGradient)
            .foregroundColor(.white)
            .cornerRadius(AITopTheme.smallCornerRadius)
    }

    func aiTopSecondaryButton() -> some View {
        self
            .padding(.horizontal, AITopTheme.spacing)
            .padding(.vertical, AITopTheme.smallSpacing)
            .background(AITopTheme.surfaceBackground)
            .foregroundColor(AITopTheme.accentOrange)
            .cornerRadius(AITopTheme.smallCornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: AITopTheme.smallCornerRadius)
                    .stroke(AITopTheme.accentOrange.opacity(0.5), lineWidth: 1)
            )
    }
}

// MARK: - Divider

struct AITopDivider: View {
    var body: some View {
        Divider().background(AITopTheme.textTertiary.opacity(0.3))
    }
}
