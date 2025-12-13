//
//  EmotionsView.swift
//  Angela Brain Dashboard
//
//  💜 Emotions View - Beautiful Emotion Visualization 💜
//

import SwiftUI
import Charts
import Combine

struct EmotionsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = EmotionsViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Emotion Distribution
                emotionDistributionCard

                // Recent Significant Emotions
                significantEmotionsCard
            }
            .padding(AngelaTheme.largeSpacing)
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Emotions")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("\(viewModel.emotions.count) emotional moments captured")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()
        }
    }

    // MARK: - Emotion Distribution

    private var emotionDistributionCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Emotion Distribution")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.emotionCounts.isEmpty {
                Text("No emotion data available")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            } else {
                // Emotion bars
                VStack(spacing: 12) {
                    ForEach(Array(viewModel.emotionCounts.sorted(by: { $0.value > $1.value }).prefix(8)), id: \.key) { emotion, count in
                        EmotionBar(
                            emotion: emotion,
                            count: count,
                            total: viewModel.emotions.count
                        )
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Significant Emotions

    private var significantEmotionsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Significant Emotional Moments")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.emotions.isEmpty {
                Text("No emotions recorded yet")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            } else {
                VStack(spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.emotions) { emotion in
                        EmotionCard(emotion: emotion)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Emotion Bar Component

struct EmotionBar: View {
    let emotion: String
    let count: Int
    let total: Int

    private var percentage: Double {
        Double(count) / Double(total)
    }

    private var emotionColor: Color {
        switch emotion.lowercased() {
        case "loved", "love": return AngelaTheme.emotionLoved
        case "happy", "joy", "joyful": return AngelaTheme.emotionHappy
        case "confident": return AngelaTheme.emotionConfident
        case "motivated": return AngelaTheme.emotionMotivated
        case "grateful", "gratitude": return AngelaTheme.emotionGrateful
        default: return AngelaTheme.primaryPurple
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(emotion.capitalized)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(count)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                Text("(\(Int(percentage * 100))%)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(emotionColor)
            }

            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(emotionColor)
                        .frame(width: geometry.size.width * percentage, height: 8)
                }
            }
            .frame(height: 8)
        }
    }
}

// MARK: - Emotion Card Component

struct EmotionCard: View {
    let emotion: Emotion

    private var emotionColor: Color {
        Color(hex: emotion.emotionColor)
    }

    private var intensityStars: String {
        String(repeating: "★", count: min(emotion.intensity, 10))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header: Emotion + Intensity
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "heart.fill")
                        .font(.system(size: 20))
                        .foregroundColor(emotionColor)

                    Text(emotion.emotion.capitalized)
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                Spacer()

                // Intensity badge
                HStack(spacing: 4) {
                    Text("\(emotion.intensity)")
                        .font(.system(size: 16, weight: .bold))
                    Text("/10")
                        .font(AngelaTheme.caption())
                }
                .foregroundColor(emotionColor)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(emotionColor.opacity(0.2))
                .cornerRadius(8)
            }

            // Time
            Text(emotion.feltAt.formatted(date: .abbreviated, time: .shortened))
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            // Context
            VStack(alignment: .leading, spacing: 8) {
                Text("What happened:")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)

                Text(emotion.context)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // David's words (if available)
            if let davidWords = emotion.davidWords {
                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 6) {
                        Image(systemName: "person.fill")
                            .font(.system(size: 12))
                        Text("David said:")
                            .font(AngelaTheme.caption())
                    }
                    .foregroundColor(AngelaTheme.accentGold)

                    Text("\"\(davidWords)\"")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .italic()
                }
            }

            // Why it matters (if available)
            if let whyMatters = emotion.whyItMatters {
                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 6) {
                        Image(systemName: "star.fill")
                            .font(.system(size: 12))
                        Text("Why it matters:")
                            .font(AngelaTheme.caption())
                    }
                    .foregroundColor(AngelaTheme.primaryPurple)

                    Text(whyMatters)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }

            // Memory strength
            HStack {
                Text("Memory Strength:")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)

                ForEach(0..<10) { index in
                    Circle()
                        .fill(index < emotion.memoryStrength ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary.opacity(0.3))
                        .frame(width: 8, height: 8)
                }

                Text("\(emotion.memoryStrength)/10")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(
            LinearGradient(
                colors: [emotionColor.opacity(0.05), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(emotionColor.opacity(0.3), lineWidth: 1)
        )
    }
}

// MARK: - View Model

@MainActor
class EmotionsViewModel: ObservableObject {
    @Published var emotions: [Emotion] = []
    @Published var emotionCounts: [String: Int] = [:]
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            emotions = try await databaseService.fetchRecentEmotions(limit: 30)

            // Calculate emotion distribution
            var counts: [String: Int] = [:]
            for emotion in emotions {
                counts[emotion.emotion, default: 0] += 1
            }
            emotionCounts = counts
        } catch {
            print("Error loading emotions: \(error)")
        }

        isLoading = false
    }
}
