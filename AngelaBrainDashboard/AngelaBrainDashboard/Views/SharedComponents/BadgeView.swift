//
//  BadgeView.swift
//  Angela Brain Dashboard
//
//  Shared badge/tag/chip components
//  DRY refactor - replaces 8+ duplicate badge patterns
//

import SwiftUI

/// Size variants for badges
enum BadgeSize {
    case small   // For compact displays
    case medium  // Default
    case large   // For emphasis

    var horizontalPadding: CGFloat {
        switch self {
        case .small: return 6
        case .medium: return 10
        case .large: return 14
        }
    }

    var verticalPadding: CGFloat {
        switch self {
        case .small: return 2
        case .medium: return 4
        case .large: return 6
        }
    }

    var fontSize: CGFloat {
        switch self {
        case .small: return 10
        case .medium: return 12
        case .large: return 14
        }
    }
}

/// Generic badge/tag view
struct BadgeView: View {
    let text: String
    var color: Color = AngelaTheme.primaryPurple
    var size: BadgeSize = .medium
    var style: BadgeStyle = .filled

    enum BadgeStyle {
        case filled    // Solid background
        case outlined  // Border only
        case subtle    // Light background with colored text
    }

    var body: some View {
        Text(text)
            .font(.system(size: size.fontSize, weight: .medium))
            .foregroundColor(textColor)
            .padding(.horizontal, size.horizontalPadding)
            .padding(.vertical, size.verticalPadding)
            .background(backgroundColor)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(borderColor, lineWidth: style == .outlined ? 1 : 0)
            )
            .cornerRadius(6)
    }

    private var textColor: Color {
        switch style {
        case .filled: return .white
        case .outlined: return color
        case .subtle: return color
        }
    }

    private var backgroundColor: Color {
        switch style {
        case .filled: return color
        case .outlined: return .clear
        case .subtle: return color.opacity(0.15)
        }
    }

    private var borderColor: Color {
        style == .outlined ? color : .clear
    }
}

/// Status badge with icon (like SystemStatusBadge)
struct StatusBadgeView: View {
    let title: String
    let isActive: Bool
    var icon: String? = nil
    var size: BadgeSize = .medium

    var body: some View {
        HStack(spacing: 6) {
            if let icon = icon {
                Image(systemName: icon)
                    .font(.system(size: size.fontSize))
            }

            Text(title)
                .font(.system(size: size.fontSize, weight: .medium))

            Circle()
                .fill(isActive ? AngelaTheme.successGreen : AngelaTheme.errorRed)
                .frame(width: 8, height: 8)
        }
        .foregroundColor(isActive ? AngelaTheme.successGreen : AngelaTheme.textSecondary)
        .padding(.horizontal, size.horizontalPadding)
        .padding(.vertical, size.verticalPadding)
        .background(isActive ? AngelaTheme.successGreen.opacity(0.1) : AngelaTheme.backgroundLight)
        .cornerRadius(6)
    }
}

/// Category chip (for filtering, selection)
struct CategoryChipView: View {
    let label: String
    let isSelected: Bool
    var icon: String? = nil
    var color: Color = AngelaTheme.primaryPurple
    var onTap: (() -> Void)? = nil

    var body: some View {
        Button(action: { onTap?() }) {
            HStack(spacing: 6) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 12))
                }

                Text(label)
                    .font(AngelaTheme.caption())
            }
            .foregroundColor(isSelected ? .white : color)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(isSelected ? color : color.opacity(0.1))
            .cornerRadius(16)
        }
        .buttonStyle(.plain)
    }
}

/// Count badge (number in circle)
struct CountBadgeView: View {
    let count: Int
    var color: Color = AngelaTheme.primaryPurple
    var maxDisplay: Int = 99

    var body: some View {
        Text(count > maxDisplay ? "\(maxDisplay)+" : "\(count)")
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(.white)
            .padding(.horizontal, count > 9 ? 6 : 4)
            .padding(.vertical, 2)
            .background(color)
            .clipShape(Capsule())
    }
}

/// System status badge with vertical layout (from TrainingStudioView)
struct SystemStatusVerticalBadge: View {
    let title: String
    let isAvailable: Bool
    let icon: String
    var activeText: String = "Ready"
    var inactiveText: String = "Not Available"
    var circleSize: CGFloat = 50
    var iconSize: CGFloat = 24

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(isAvailable ? AngelaTheme.successGreen.opacity(0.2) : AngelaTheme.errorRed.opacity(0.2))
                    .frame(width: circleSize, height: circleSize)

                Image(systemName: icon)
                    .font(.system(size: iconSize))
                    .foregroundColor(isAvailable ? AngelaTheme.successGreen : AngelaTheme.errorRed)
            }

            VStack(spacing: 2) {
                Text(title)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                Text(isAvailable ? activeText : inactiveText)
                    .font(AngelaTheme.caption().weight(.semibold))
                    .foregroundColor(isAvailable ? AngelaTheme.successGreen : AngelaTheme.errorRed)
            }
        }
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    VStack(spacing: 24) {
        // Basic badges
        HStack(spacing: 8) {
            BadgeView(text: "Active", color: AngelaTheme.successGreen, style: .filled)
            BadgeView(text: "Pending", color: AngelaTheme.warningOrange, style: .subtle)
            BadgeView(text: "Inactive", color: AngelaTheme.textTertiary, style: .outlined)
        }

        // Size variants
        HStack(spacing: 8) {
            BadgeView(text: "Small", size: .small)
            BadgeView(text: "Medium", size: .medium)
            BadgeView(text: "Large", size: .large)
        }

        // Status badges
        HStack(spacing: 12) {
            StatusBadgeView(title: "MLX", isActive: true, icon: "cpu")
            StatusBadgeView(title: "Ollama", isActive: false, icon: "server.rack")
        }

        // Category chips
        HStack(spacing: 8) {
            CategoryChipView(label: "All", isSelected: true)
            CategoryChipView(label: "Learning", isSelected: false, icon: "book.fill", color: AngelaTheme.successGreen)
            CategoryChipView(label: "Personal", isSelected: false, icon: "person.fill")
        }

        // Count badges
        HStack(spacing: 16) {
            HStack {
                Text("Messages")
                CountBadgeView(count: 5)
            }
            HStack {
                Text("Notifications")
                CountBadgeView(count: 128, color: AngelaTheme.errorRed)
            }
        }

        // System status vertical
        HStack(spacing: 20) {
            SystemStatusVerticalBadge(title: "MLX", isAvailable: true, icon: "cpu")
            SystemStatusVerticalBadge(title: "Ollama", isAvailable: true, icon: "server.rack")
            SystemStatusVerticalBadge(title: "GPU", isAvailable: false, icon: "memorychip")
        }
    }
    .padding()
    .background(AngelaTheme.backgroundDark)
}
