//
//  EmptyStateView.swift
//  Angela Brain Dashboard
//
//  Shared empty state component
//  DRY refactor - replaces scattered "No data" text patterns
//

import SwiftUI

/// Configurable empty state view
struct EmptyStateView: View {
    let message: String
    var icon: String? = nil
    var subtitle: String? = nil
    var actionLabel: String? = nil
    var onAction: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: 16) {
            if let icon = icon {
                Image(systemName: icon)
                    .font(.system(size: 40))
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            VStack(spacing: 4) {
                Text(message)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)

                if let subtitle = subtitle {
                    Text(subtitle)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary.opacity(0.7))
                }
            }
            .multilineTextAlignment(.center)

            if let actionLabel = actionLabel, let onAction = onAction {
                Button(action: onAction) {
                    Text(actionLabel)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing * 2)
    }
}

/// Simple inline empty state (for lists)
struct InlineEmptyStateView: View {
    let message: String

    var body: some View {
        Text(message)
            .font(AngelaTheme.body())
            .foregroundColor(AngelaTheme.textTertiary)
            .frame(maxWidth: .infinity)
            .padding(AngelaTheme.spacing)
    }
}

/// Loading state view
struct LoadingStateView: View {
    var message: String = "Loading..."

    var body: some View {
        VStack(spacing: 12) {
            ProgressView()
                .scaleEffect(1.2)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing * 2)
    }
}

/// Error state view
struct ErrorStateView: View {
    let message: String
    var retryLabel: String = "Retry"
    var onRetry: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 40))
                .foregroundColor(AngelaTheme.errorRed)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)

            if let onRetry = onRetry {
                Button(action: onRetry) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                        Text(retryLabel)
                    }
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing * 2)
    }
}

#Preview {
    VStack(spacing: 32) {
        // Empty state with icon
        EmptyStateView(
            message: "No emotions recorded yet",
            icon: "heart.slash",
            subtitle: "Start a conversation to track emotions"
        )

        Divider()

        // Empty state with action
        EmptyStateView(
            message: "No documents found",
            icon: "doc.text.magnifyingglass",
            actionLabel: "Upload Document",
            onAction: { print("Upload") }
        )

        Divider()

        // Inline empty state
        InlineEmptyStateView(message: "No data available")

        Divider()

        // Loading state
        LoadingStateView(message: "Fetching memories...")

        Divider()

        // Error state
        ErrorStateView(
            message: "Failed to connect to database",
            onRetry: { print("Retry") }
        )
    }
    .padding()
    .background(AngelaTheme.backgroundDark)
}
