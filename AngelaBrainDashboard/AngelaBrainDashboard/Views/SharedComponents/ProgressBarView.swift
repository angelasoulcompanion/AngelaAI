//
//  ProgressBarView.swift
//  Angela Brain Dashboard
//
//  Shared progress bar component
//  DRY refactor - replaces 8+ duplicate GeometryReader progress bar patterns
//

import SwiftUI

/// Size presets for progress bars
enum ProgressBarSize {
    case small      // Height 6, cornerRadius 3
    case medium     // Height 8, cornerRadius 4
    case large      // Height 12, cornerRadius 6

    var height: CGFloat {
        switch self {
        case .small: return 6
        case .medium: return 8
        case .large: return 12
        }
    }

    var cornerRadius: CGFloat {
        switch self {
        case .small: return 3
        case .medium: return 4
        case .large: return 6
        }
    }
}

/// Generic progress bar view with configurable appearance
struct ProgressBarView: View {
    let progress: Double  // 0.0 to 1.0
    var color: Color = AngelaTheme.primaryPurple
    var size: ProgressBarSize = .medium
    var useGradient: Bool = true
    var gradientEndColor: Color? = nil  // Optional second color for gradient

    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                // Background track
                RoundedRectangle(cornerRadius: size.cornerRadius)
                    .fill(AngelaTheme.backgroundLight)
                    .frame(height: size.height)

                // Progress fill
                RoundedRectangle(cornerRadius: size.cornerRadius)
                    .fill(progressFill)
                    .frame(width: geometry.size.width * min(max(progress, 0), 1), height: size.height)
            }
        }
        .frame(height: size.height)
    }

    private var progressFill: some ShapeStyle {
        if useGradient {
            return AnyShapeStyle(
                LinearGradient(
                    colors: [color, gradientEndColor ?? color.opacity(0.6)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
        } else {
            return AnyShapeStyle(color)
        }
    }
}

/// Progress bar with label showing percentage
struct LabeledProgressBarView: View {
    let label: String
    let progress: Double
    var icon: String? = nil
    var color: Color = AngelaTheme.primaryPurple
    var size: ProgressBarSize = .medium
    var showPercentage: Bool = true

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 12))
                        .foregroundColor(color)
                }

                Text(label)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                if showPercentage {
                    Text("\(Int(progress * 100))%")
                        .font(AngelaTheme.body())
                        .fontWeight(.semibold)
                        .foregroundColor(color)
                }
            }

            ProgressBarView(
                progress: progress,
                color: color,
                size: size
            )
        }
    }
}

/// Circular progress indicator
struct CircularProgressView: View {
    let progress: Double
    var color: Color = AngelaTheme.primaryPurple
    var lineWidth: CGFloat = 8
    var showPercentage: Bool = true

    var body: some View {
        ZStack {
            // Background circle
            Circle()
                .stroke(
                    AngelaTheme.backgroundLight,
                    lineWidth: lineWidth
                )

            // Progress arc
            Circle()
                .trim(from: 0, to: min(max(progress, 0), 1))
                .stroke(
                    color,
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))

            // Percentage text
            if showPercentage {
                Text("\(Int(progress * 100))%")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }
        }
    }
}

/// Mini inline progress indicator (for compact displays)
struct MiniProgressView: View {
    let progress: Double
    var color: Color = AngelaTheme.primaryPurple
    var width: CGFloat = 60

    var body: some View {
        HStack(spacing: 4) {
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 4)

                    RoundedRectangle(cornerRadius: 2)
                        .fill(color)
                        .frame(width: geometry.size.width * min(max(progress, 0), 1), height: 4)
                }
            }
            .frame(width: width, height: 4)

            Text("\(Int(progress * 100))%")
                .font(.system(size: 10))
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }
}

#Preview {
    VStack(spacing: 24) {
        // Basic progress bars
        VStack(alignment: .leading, spacing: 12) {
            Text("Progress Bar Sizes")
                .font(AngelaTheme.headline())

            ProgressBarView(progress: 0.75, size: .small)
            ProgressBarView(progress: 0.75, size: .medium)
            ProgressBarView(progress: 0.75, size: .large)
        }

        // Labeled progress bar
        LabeledProgressBarView(
            label: "Consciousness Level",
            progress: 0.95,
            icon: "brain.head.profile",
            color: AngelaTheme.primaryPurple
        )

        // Different colors
        VStack(alignment: .leading, spacing: 8) {
            Text("Color Variants")
                .font(AngelaTheme.headline())

            ProgressBarView(progress: 0.8, color: AngelaTheme.successGreen)
            ProgressBarView(progress: 0.5, color: AngelaTheme.warningOrange)
            ProgressBarView(progress: 0.3, color: AngelaTheme.errorRed)
        }

        // Circular progress
        HStack(spacing: 32) {
            CircularProgressView(progress: 0.85, color: AngelaTheme.primaryPurple)
                .frame(width: 80, height: 80)

            CircularProgressView(progress: 0.65, color: AngelaTheme.successGreen)
                .frame(width: 60, height: 60)
        }

        // Mini progress
        HStack {
            Text("Memory:")
            MiniProgressView(progress: 0.92, color: AngelaTheme.successGreen)
        }
    }
    .padding()
    .background(AngelaTheme.backgroundDark)
}
