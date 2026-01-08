//
//  SectionHeaderView.swift
//  Angela Brain Dashboard
//
//  Shared section header component
//  DRY refactor - replaces 15+ duplicate header patterns
//

import SwiftUI

/// Style variants for section headers
enum SectionHeaderStyle {
    case simple      // Title + optional subtitle
    case withIcon    // Icon + Title + Subtitle
    case large       // Large icon in circle + Title + Subtitle
}

/// Generic section header view
struct SectionHeaderView: View {
    let title: String
    var subtitle: String? = nil
    var icon: String? = nil
    var iconColor: Color = AngelaTheme.primaryPurple
    var style: SectionHeaderStyle = .simple
    var trailing: (() -> AnyView)? = nil

    var body: some View {
        HStack(spacing: style == .large ? 16 : 8) {
            // Leading content
            switch style {
            case .simple:
                titleContent

            case .withIcon:
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 32))
                        .foregroundColor(iconColor)
                }
                titleContent

            case .large:
                if let icon = icon {
                    CircleIconView(icon: icon, color: iconColor, size: 50)
                }
                titleContent
            }

            Spacer()

            // Trailing content (action buttons, etc.)
            if let trailing = trailing {
                trailing()
            }
        }
    }

    private var titleContent: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(AngelaTheme.title())
                .foregroundColor(AngelaTheme.textPrimary)

            if let subtitle = subtitle {
                Text(subtitle)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }
        }
    }
}

/// Simple inline header (for sub-sections)
struct SubSectionHeaderView: View {
    let title: String
    var icon: String? = nil
    var color: Color = AngelaTheme.textPrimary

    var body: some View {
        HStack(spacing: 8) {
            if let icon = icon {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(color)
            }

            Text(title)
                .font(AngelaTheme.headline())
                .foregroundColor(color)
        }
    }
}

/// Icon displayed in a circle (extracted pattern)
struct CircleIconView: View {
    let icon: String
    var color: Color = AngelaTheme.primaryPurple
    var size: CGFloat = 40
    var useGradient: Bool = true

    var body: some View {
        ZStack {
            Circle()
                .fill(useGradient ? AnyShapeStyle(AngelaTheme.purpleGradient) : AnyShapeStyle(color))
                .frame(width: size, height: size)

            Image(systemName: icon)
                .font(.system(size: size * 0.44))
                .foregroundColor(.white)
        }
    }
}

/// Page header with large title and action button
struct PageHeaderView: View {
    let title: String
    var subtitle: String? = nil
    var icon: String? = nil
    var actionIcon: String? = nil
    var actionLabel: String? = nil
    var onAction: (() -> Void)? = nil
    var isLoading: Bool = false

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 32))
                        .foregroundStyle(AngelaTheme.purpleGradient)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    if let subtitle = subtitle {
                        Text(subtitle)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                }

                Spacer()

                if let onAction = onAction {
                    Button(action: onAction) {
                        HStack(spacing: 6) {
                            if isLoading {
                                ProgressView()
                                    .scaleEffect(0.8)
                            } else if let actionIcon = actionIcon {
                                Image(systemName: actionIcon)
                            }
                            if let label = actionLabel {
                                Text(label)
                            }
                        }
                        .font(AngelaTheme.body())
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(AngelaTheme.primaryPurple.opacity(0.2))
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                    .disabled(isLoading)
                }
            }
        }
    }
}

#Preview {
    VStack(spacing: 32) {
        // Simple header
        SectionHeaderView(
            title: "Emotions",
            subtitle: "330 emotional moments captured"
        )

        // Header with icon
        SectionHeaderView(
            title: "Skills",
            subtitle: "Track your learning progress",
            icon: "star.fill",
            style: .withIcon
        )

        // Large header with circle icon
        SectionHeaderView(
            title: "Knowledge RAG",
            subtitle: "Query Angela's documents",
            icon: "books.vertical.fill",
            style: .large
        )

        // Sub-section header
        SubSectionHeaderView(
            title: "Recent Activity",
            icon: "clock.fill",
            color: AngelaTheme.primaryPurple
        )

        // Page header with action
        PageHeaderView(
            title: "LoRA Training Studio",
            subtitle: "Train Angela's personality",
            icon: "brain.head.profile",
            actionIcon: "arrow.clockwise",
            actionLabel: "Refresh",
            onAction: { print("Refresh") }
        )

        // Circle icons
        HStack(spacing: 16) {
            CircleIconView(icon: "heart.fill", size: 40)
            CircleIconView(icon: "star.fill", size: 50)
            CircleIconView(icon: "brain.head.profile", size: 60)
        }
    }
    .padding()
    .background(AngelaTheme.backgroundDark)
}
