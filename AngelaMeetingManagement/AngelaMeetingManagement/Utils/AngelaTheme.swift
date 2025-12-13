//
//  AngelaTheme.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜
//  Inspired by ClickUp Design System
//

import SwiftUI

// MARK: - Color Extension for Adaptive Colors
extension Color {
    init(light: Color, dark: Color) {
        #if os(macOS)
        self.init(nsColor: NSColor(name: nil, dynamicProvider: { appearance in
            appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua ? NSColor(dark) : NSColor(light)
        }))
        #else
        self.init(uiColor: UIColor { traitCollection in
            traitCollection.userInterfaceStyle == .dark ? UIColor(dark) : UIColor(light)
        })
        #endif
    }
}

// MARK: - Angela Purple Theme Colors
struct AngelaTheme {

    // MARK: Primary Colors (Purple - Angela's signature!)
    static let primaryPurple = Color(red: 0.48, green: 0.41, blue: 0.93)      // #7B68EE
    static let lightPurple = Color(red: 0.69, green: 0.61, blue: 0.85)        // #B19CD9
    static let darkPurple = Color(red: 0.42, green: 0.35, blue: 0.80)         // #6A5ACD
    static let palePurple = Color(red: 0.97, green: 0.97, blue: 1.0)          // #F8F7FF

    // MARK: Accent Colors
    static let accentPink = Color(red: 0.91, green: 0.12, blue: 0.39)         // #E91E63
    static let accentBlue = Color(red: 0.40, green: 0.61, blue: 1.0)          // #669CFF

    // MARK: Status Colors (ClickUp-inspired)
    static let statusOpen = Color(red: 0.60, green: 0.60, blue: 0.60)         // Gray
    static let statusTodo = Color(red: 0.85, green: 0.53, blue: 0.13)         // Orange
    static let statusInProgress = primaryPurple                               // Purple
    static let statusFollowUp = Color(red: 0.20, green: 0.78, blue: 0.65)     // Teal
    static let statusCompleted = Color(red: 0.30, green: 0.69, blue: 0.31)    // Green

    // MARK: Priority Colors
    static let priorityUrgent = Color(red: 0.96, green: 0.26, blue: 0.21)     // Red
    static let priorityHigh = Color(red: 1.0, green: 0.60, blue: 0.0)         // Orange
    static let priorityNormal = Color(red: 0.40, green: 0.61, blue: 1.0)      // Blue
    static let priorityLow = Color(red: 0.60, green: 0.60, blue: 0.60)        // Gray

    // MARK: Neutral Colors - Adaptive (works with light/dark mode)
    static let background = Color(
        light: Color(white: 0.98),      // #FAFAFA (light mode)
        dark: Color(white: 0.11)        // #1C1C1C (dark mode)
    )

    static let cardBackground = Color(
        light: Color.white,             // White (light mode)
        dark: Color(white: 0.15)        // #262626 (dark mode)
    )

    static let textPrimary = Color(
        light: Color(white: 0.13),      // #222222 (light mode)
        dark: Color(white: 0.95)        // #F2F2F2 (dark mode)
    )

    static let textSecondary = Color(
        light: Color(white: 0.45),      // #737373 (light mode)
        dark: Color(white: 0.65)        // #A6A6A6 (dark mode)
    )

    static let border = Color(
        light: Color(white: 0.90),      // #E5E5E5 (light mode)
        dark: Color(white: 0.25)        // #404040 (dark mode)
    )

    // MARK: - Gradients
    static let purpleGradient = LinearGradient(
        colors: [primaryPurple, lightPurple],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let cardGradient = LinearGradient(
        colors: [Color.white, palePurple],
        startPoint: .top,
        endPoint: .bottom
    )

    // MARK: - Shadows
    static func cardShadow(isHovered: Bool = false) -> Color {
        isHovered ? primaryPurple.opacity(0.15) : Color.black.opacity(0.05)
    }

    // MARK: - Corner Radius
    static let cornerRadiusSmall: CGFloat = 6
    static let cornerRadiusMedium: CGFloat = 10
    static let cornerRadiusLarge: CGFloat = 16

    // MARK: - Spacing
    static let spacingXS: CGFloat = 4
    static let spacingS: CGFloat = 8
    static let spacingM: CGFloat = 12
    static let spacingL: CGFloat = 16
    static let spacingXL: CGFloat = 24

    // MARK: - Helper Functions
    static func statusColor(for status: String) -> Color {
        switch status.lowercased() {
        case "open": return statusOpen
        case "to do", "todo": return statusTodo
        case "in progress", "in_progress": return statusInProgress
        case "follow up", "follow_up": return statusFollowUp
        case "completed", "done": return statusCompleted
        default: return statusOpen
        }
    }

    static func priorityColor(for priority: String) -> Color {
        switch priority.lowercased() {
        case "urgent": return priorityUrgent
        case "high": return priorityHigh
        case "normal": return priorityNormal
        case "low": return priorityLow
        default: return priorityNormal
        }
    }

    static func statusIcon(for status: String) -> String {
        switch status.lowercased() {
        case "open": return "circle"
        case "to do", "todo": return "circle.dotted"
        case "in progress", "in_progress": return "arrow.clockwise.circle.fill"
        case "follow up", "follow_up": return "eye.circle.fill"
        case "completed", "done": return "checkmark.circle.fill"
        default: return "circle"
        }
    }

    static func priorityIcon(for priority: String) -> String {
        switch priority.lowercased() {
        case "urgent": return "exclamationmark.2"
        case "high": return "exclamationmark"
        case "normal": return "minus"
        case "low": return "arrow.down"
        default: return "minus"
        }
    }
}

// MARK: - Custom Button Styles

struct AngelaPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .semibold))
            .foregroundColor(.white)
            .padding(.horizontal, AngelaTheme.spacingL)
            .padding(.vertical, AngelaTheme.spacingM)
            .background(
                AngelaTheme.purpleGradient
                    .opacity(configuration.isPressed ? 0.8 : 1.0)
            )
            .cornerRadius(AngelaTheme.cornerRadiusMedium)
            .shadow(
                color: AngelaTheme.primaryPurple.opacity(0.3),
                radius: configuration.isPressed ? 4 : 8,
                y: configuration.isPressed ? 2 : 4
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.spring(response: 0.3), value: configuration.isPressed)
    }
}

struct AngelaSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .medium))
            .foregroundColor(AngelaTheme.primaryPurple)
            .padding(.horizontal, AngelaTheme.spacingL)
            .padding(.vertical, AngelaTheme.spacingM)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadiusMedium)
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                    .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.spring(response: 0.3), value: configuration.isPressed)
    }
}

// MARK: - Custom Card Style

struct AngelaCardStyle: ViewModifier {
    var isHovered: Bool = false

    func body(content: Content) -> some View {
        content
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadiusMedium)
            .shadow(
                color: AngelaTheme.cardShadow(isHovered: isHovered),
                radius: isHovered ? 12 : 6,
                y: isHovered ? 6 : 3
            )
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                    .stroke(isHovered ? AngelaTheme.primaryPurple.opacity(0.3) : AngelaTheme.border, lineWidth: 1)
            )
            .scaleEffect(isHovered ? 1.02 : 1.0)
            .animation(.spring(response: 0.3), value: isHovered)
    }
}

extension View {
    func angelaCard(isHovered: Bool = false) -> some View {
        modifier(AngelaCardStyle(isHovered: isHovered))
    }
}
