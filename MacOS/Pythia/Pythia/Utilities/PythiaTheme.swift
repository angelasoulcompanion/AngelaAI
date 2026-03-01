//
//  PythiaTheme.swift
//  Pythia
//
//  Professional Finance Theme — Deep Blue + Gold
//

import SwiftUI

struct PythiaTheme {
    // MARK: - Primary Colors

    /// Deep Blue — primary brand
    static let primaryBlue = Color(hex: "1E40AF")
    static let secondaryBlue = Color(hex: "3B82F6")
    static let accentBlue = Color(hex: "60A5FA")

    /// Gold — accent
    static let accentGold = Color(hex: "F59E0B")
    static let darkGold = Color(hex: "D97706")

    // MARK: - Semantic Colors

    static let profit = Color(hex: "059669")
    static let loss = Color(hex: "DC2626")

    // MARK: - Background Colors

    static let backgroundDark = Color(hex: "0F172A")
    static let backgroundMedium = Color(hex: "1E293B")
    static let cardBackground = Color(hex: "1E293B")
    static let surfaceBackground = Color(hex: "334155")

    // MARK: - Text Colors

    static let textPrimary = Color.white
    static let textSecondary = Color(hex: "94A3B8")
    static let textTertiary = Color(hex: "64748B")

    // MARK: - Status Colors

    static let successGreen = Color(hex: "059669")
    static let warningOrange = Color(hex: "F59E0B")
    static let errorRed = Color(hex: "DC2626")
    static let infoBlue = Color(hex: "3B82F6")

    // MARK: - Gradients

    static let blueGradient = LinearGradient(
        colors: [primaryBlue, secondaryBlue],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let goldGradient = LinearGradient(
        colors: [accentGold, darkGold],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let cardGradient = LinearGradient(
        colors: [cardBackground.opacity(0.8), cardBackground.opacity(0.4)],
        startPoint: .top,
        endPoint: .bottom
    )

    // MARK: - Shadows

    static let cardShadow = Shadow(
        color: Color.black.opacity(0.3),
        radius: 10,
        x: 0,
        y: 4
    )

    // MARK: - Spacing

    static let spacing: CGFloat = 16
    static let smallSpacing: CGFloat = 8
    static let largeSpacing: CGFloat = 24

    // MARK: - Corner Radius

    static let cornerRadius: CGFloat = 12
    static let smallCornerRadius: CGFloat = 8
    static let largeCornerRadius: CGFloat = 16

    // MARK: - Fonts

    static func title() -> Font {
        .system(size: 24, weight: .bold)
    }

    static func heading() -> Font {
        .system(size: 16, weight: .semibold)
    }

    static func headline() -> Font {
        .system(size: 18, weight: .semibold)
    }

    static func body() -> Font {
        .system(size: 14, weight: .regular)
    }

    static func caption() -> Font {
        .system(size: 12, weight: .regular)
    }

    static func number() -> Font {
        .system(size: 32, weight: .bold, design: .rounded)
    }

    static func monospace() -> Font {
        .system(size: 14, weight: .medium, design: .monospaced)
    }

    // MARK: - Helper

    struct Shadow {
        let color: Color
        let radius: CGFloat
        let x: CGFloat
        let y: CGFloat
    }

    /// Format number as percentage string
    static func formatPercent(_ value: Double, decimals: Int = 2) -> String {
        String(format: "%.\(decimals)f%%", value * 100)
    }

    /// Format number as currency
    static func formatCurrency(_ value: Double, currency: String = "THB") -> String {
        let symbols = ["THB": "฿", "USD": "$", "EUR": "€"]
        let sym = symbols[currency] ?? currency
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        return "\(sym)\(formatter.string(from: NSNumber(value: value)) ?? "0.00")"
    }

    /// Color for profit/loss value
    static func profitLossColor(_ value: Double) -> Color {
        if value > 0 { return profit }
        if value < 0 { return loss }
        return textSecondary
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
    func pythiaCard() -> some View {
        self
            .background(PythiaTheme.cardBackground)
            .cornerRadius(PythiaTheme.cornerRadius)
            .shadow(
                color: PythiaTheme.cardShadow.color,
                radius: PythiaTheme.cardShadow.radius,
                x: PythiaTheme.cardShadow.x,
                y: PythiaTheme.cardShadow.y
            )
    }

    func pythiaPrimaryButton() -> some View {
        self
            .padding(.horizontal, PythiaTheme.spacing)
            .padding(.vertical, PythiaTheme.smallSpacing)
            .background(PythiaTheme.blueGradient)
            .foregroundColor(.white)
            .cornerRadius(PythiaTheme.smallCornerRadius)
    }

    func pythiaSecondaryButton() -> some View {
        self
            .padding(.horizontal, PythiaTheme.spacing)
            .padding(.vertical, PythiaTheme.smallSpacing)
            .background(PythiaTheme.surfaceBackground)
            .foregroundColor(PythiaTheme.secondaryBlue)
            .cornerRadius(PythiaTheme.smallCornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: PythiaTheme.smallCornerRadius)
                    .stroke(PythiaTheme.secondaryBlue.opacity(0.5), lineWidth: 1)
            )
    }
}
