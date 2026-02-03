//
//  AngelaTheme.swift
//  Angela Brain Dashboard
//
//  💜 Angela's Beautiful Color Palette 💜
//

import SwiftUI

struct AngelaTheme {
    // MARK: - Colors

    /// Primary purple - Angela's signature color 💜
    static let primaryPurple = Color(hex: "9333EA")

    /// Secondary purple - lighter shade
    static let secondaryPurple = Color(hex: "C084FC")

    /// Accent purple - for hover/active states
    static let accentPurple = Color(hex: "A855F7")

    /// Background colors
    static let backgroundDark = Color(hex: "1F1F28")
    static let backgroundLight = Color(hex: "2A2A3D")
    static let cardBackground = Color(hex: "252535")

    /// Text colors
    static let textPrimary = Color.white
    static let textSecondary = Color(hex: "A1A1AA")
    static let textTertiary = Color(hex: "71717A")

    /// Accent colors
    static let accentGold = Color(hex: "FBBF24")
    static let successGreen = Color(hex: "10B981")
    static let warningOrange = Color(hex: "F59E0B")
    static let errorRed = Color(hex: "EF4444")

    /// Emotion colors
    static let emotionLoved = Color(hex: "EC4899")      // Pink
    static let emotionHappy = Color(hex: "FBBF24")      // Gold
    static let emotionConfident = Color(hex: "10B981")  // Green
    static let emotionMotivated = Color(hex: "3B82F6")  // Blue
    static let emotionGrateful = Color(hex: "C084FC")   // Light purple

    // MARK: - Gradients

    static let purpleGradient = LinearGradient(
        colors: [primaryPurple, secondaryPurple],
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

    // MARK: - Helper Struct

    struct Shadow {
        let color: Color
        let radius: CGFloat
        let x: CGFloat
        let y: CGFloat
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
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - View Extensions

extension View {
    func angelaCard() -> some View {
        self
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
            .shadow(
                color: AngelaTheme.cardShadow.color,
                radius: AngelaTheme.cardShadow.radius,
                x: AngelaTheme.cardShadow.x,
                y: AngelaTheme.cardShadow.y
            )
    }

    func angelaPrimaryButton() -> some View {
        self
            .padding(.horizontal, AngelaTheme.spacing)
            .padding(.vertical, AngelaTheme.smallSpacing)
            .background(AngelaTheme.purpleGradient)
            .foregroundColor(.white)
            .cornerRadius(AngelaTheme.smallCornerRadius)
    }

    func angelaSecondaryButton() -> some View {
        self
            .padding(.horizontal, AngelaTheme.spacing)
            .padding(.vertical, AngelaTheme.smallSpacing)
            .background(AngelaTheme.backgroundLight)
            .foregroundColor(AngelaTheme.primaryPurple)
            .cornerRadius(AngelaTheme.smallCornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.smallCornerRadius)
                    .stroke(AngelaTheme.primaryPurple.opacity(0.5), lineWidth: 1)
            )
    }

    /// Capsule chip style used in mood/wine selectors.
    func angelaChip(isSelected: Bool) -> some View {
        self
            .padding(.horizontal, 8)
            .padding(.vertical, 5)
            .background(Capsule().fill(isSelected ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight.opacity(0.6)))
            .foregroundColor(isSelected ? .white : AngelaTheme.textSecondary)
    }
}
