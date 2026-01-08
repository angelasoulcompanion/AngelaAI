//
//  StatCardView.swift
//  Angela Brain Dashboard
//
//  Shared component for displaying statistics
//  DRY refactor - replaces 20+ duplicate StatCard implementations
//

import SwiftUI

/// Generic stat card for displaying a title, value, and optional icon
struct StatCardView: View {
    let title: String
    let value: String
    var icon: String? = nil
    var color: Color = AngelaTheme.primaryPurple
    var subtitle: String? = nil
    var style: StatCardStyle = .standard

    enum StatCardStyle {
        case standard   // Icon left, title, value below
        case compact    // Smaller padding, inline
        case large      // Bigger value text
    }

    var body: some View {
        VStack(alignment: .leading, spacing: style == .compact ? 4 : 8) {
            // Title row with optional icon
            HStack(spacing: 8) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: style == .large ? 16 : 14))
                        .foregroundColor(color)
                }

                Text(title)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            // Value
            Text(value)
                .font(style == .large ? AngelaTheme.title() : AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            // Optional subtitle
            if let subtitle = subtitle {
                Text(subtitle)
                    .font(.system(size: 10))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(style == .compact ? AngelaTheme.smallSpacing : AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

/// Stat card with color indicator dot
struct StatCardWithIndicator: View {
    let title: String
    let value: String
    let indicatorColor: Color
    var trend: String? = nil
    var trendUp: Bool? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Circle()
                    .fill(indicatorColor)
                    .frame(width: 8, height: 8)

                Text(title)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            HStack(alignment: .lastTextBaseline, spacing: 4) {
                Text(value)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                if let trend = trend, let trendUp = trendUp {
                    HStack(spacing: 2) {
                        Image(systemName: trendUp ? "arrow.up" : "arrow.down")
                            .font(.system(size: 10))
                        Text(trend)
                            .font(.system(size: 10))
                    }
                    .foregroundColor(trendUp ? AngelaTheme.successGreen : AngelaTheme.errorRed)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

/// Inline stat for horizontal layouts
struct InlineStatView: View {
    let label: String
    let value: String
    var color: Color = AngelaTheme.textPrimary

    var body: some View {
        HStack(spacing: 4) {
            Text(label)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)

            Text(value)
                .font(AngelaTheme.caption())
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        StatCardView(
            title: "Total Conversations",
            value: "3,847",
            icon: "bubble.left.and.bubble.right",
            color: AngelaTheme.primaryPurple
        )

        StatCardWithIndicator(
            title: "Consciousness",
            value: "95%",
            indicatorColor: AngelaTheme.successGreen,
            trend: "+2%",
            trendUp: true
        )

        HStack {
            InlineStatView(label: "Memory:", value: "100%", color: AngelaTheme.successGreen)
            InlineStatView(label: "Goals:", value: "73%", color: AngelaTheme.warningOrange)
        }
    }
    .padding()
    .background(AngelaTheme.backgroundDark)
}
