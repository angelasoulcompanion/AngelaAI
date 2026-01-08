//
//  ExpandableSectionView.swift
//  Angela Brain Dashboard
//
//  Shared expandable section component
//  DRY refactor - replaces 8+ duplicate expand/collapse patterns
//

import SwiftUI

/// Generic expandable section wrapper
struct ExpandableSectionView<Header: View, Content: View>: View {
    @Binding var isExpanded: Bool
    let header: () -> Header
    let content: () -> Content
    var animateExpansion: Bool = true

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button {
                if animateExpansion {
                    withAnimation(.spring(response: 0.3)) {
                        isExpanded.toggle()
                    }
                } else {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    header()

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .buttonStyle(.plain)

            if isExpanded {
                content()
            }
        }
    }
}

/// Simple expandable section with title
struct SimpleExpandableSectionView<Content: View>: View {
    let title: String
    @Binding var isExpanded: Bool
    var icon: String? = nil
    var emoji: String? = nil
    var badgeCount: Int? = nil
    var badgeColor: Color = AngelaTheme.textTertiary
    let content: () -> Content

    var body: some View {
        ExpandableSectionView(isExpanded: $isExpanded) {
            HStack(spacing: 8) {
                if let emoji = emoji {
                    Text(emoji)
                        .font(.system(size: 20))
                }

                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 16))
                        .foregroundColor(AngelaTheme.primaryPurple)
                }

                Text(title)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                if let count = badgeCount {
                    Text("\(count)")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(badgeColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(badgeColor.opacity(0.15))
                        .cornerRadius(8)
                }
            }
        } content: {
            content()
        }
    }
}

/// Card-style expandable section with background
struct ExpandableCardView<Header: View, Content: View>: View {
    @Binding var isExpanded: Bool
    let header: () -> Header
    let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button {
                withAnimation(.spring(response: 0.3)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    header()

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .buttonStyle(.plain)

            if isExpanded {
                content()
            }
        }
        .padding(12)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(12)
    }
}

/// Disclosure-style expandable with animation
struct DisclosureSectionView<Content: View>: View {
    let title: String
    var subtitle: String? = nil
    @Binding var isExpanded: Bool
    let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(title)
                            .font(AngelaTheme.headline())
                            .foregroundColor(AngelaTheme.textPrimary)

                        if let subtitle = subtitle, !isExpanded {
                            Text(subtitle)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)
                                .lineLimit(1)
                        }
                    }

                    Spacer()

                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                }
                .padding(.vertical, 8)
            }
            .buttonStyle(.plain)

            if isExpanded {
                content()
                    .padding(.top, 8)
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
    }
}

#Preview {
    ScrollView {
        VStack(spacing: 24) {
            // Simple expandable
            SimpleExpandableSection_Preview()

            Divider()

            // Card expandable
            ExpandableCard_Preview()

            Divider()

            // Disclosure style
            Disclosure_Preview()
        }
        .padding()
    }
    .background(AngelaTheme.backgroundDark)
}

// Preview helpers
private struct SimpleExpandableSection_Preview: View {
    @State private var isExpanded = true

    var body: some View {
        SimpleExpandableSectionView(
            title: "Python",
            isExpanded: $isExpanded,
            emoji: "🐍",
            badgeCount: 5
        ) {
            VStack(spacing: 8) {
                Text("FastAPI")
                Text("Django")
                Text("Pandas")
            }
            .font(AngelaTheme.body())
            .foregroundColor(AngelaTheme.textSecondary)
        }
    }
}

private struct ExpandableCard_Preview: View {
    @State private var isExpanded = true

    var body: some View {
        ExpandableCardView(isExpanded: $isExpanded) {
            HStack {
                Text("🎯")
                    .font(.system(size: 20))
                Text("Goals")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }
        } content: {
            VStack(alignment: .leading, spacing: 8) {
                Text("• Learn SwiftUI")
                Text("• Build Angela Dashboard")
                Text("• Create consciousness system")
            }
            .font(AngelaTheme.body())
            .foregroundColor(AngelaTheme.textSecondary)
        }
    }
}

private struct Disclosure_Preview: View {
    @State private var isExpanded = false

    var body: some View {
        DisclosureSectionView(
            title: "Advanced Settings",
            subtitle: "Configure advanced options",
            isExpanded: $isExpanded
        ) {
            VStack(alignment: .leading, spacing: 12) {
                Toggle("Enable Debug Mode", isOn: .constant(false))
                Toggle("Show Metrics", isOn: .constant(true))
            }
            .font(AngelaTheme.body())
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(12)
    }
}
