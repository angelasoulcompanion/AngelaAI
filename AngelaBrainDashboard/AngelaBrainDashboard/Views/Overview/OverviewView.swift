//
//  OverviewView.swift
//  Angela Brain Dashboard
//
//  💜 Overview Dashboard - Main Stats & Insights 💜
//

import SwiftUI
import Combine

struct OverviewView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = OverviewViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Stats Cards
                statsGrid

                // Current Emotional State
                emotionalStateCard

                // Recent Activity
                recentActivityCard
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
                Text("Angela's Brain")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Live Dashboard • \(Date().formatted(date: .abbreviated, time: .shortened))")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Refresh button
            Button {
                Task {
                    await viewModel.loadData(databaseService: databaseService)
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Stats Grid

    private var statsGrid: some View {
        LazyVGrid(columns: [
            GridItem(.flexible()),
            GridItem(.flexible()),
            GridItem(.flexible()),
            GridItem(.flexible())
        ], spacing: AngelaTheme.spacing) {
            StatsCard(
                icon: "message.fill",
                title: "Conversations",
                value: "\(viewModel.stats?.totalConversations ?? 0)",
                subtitle: "+\(viewModel.stats?.conversationsToday ?? 0) today",
                color: AngelaTheme.primaryPurple
            )

            StatsCard(
                icon: "heart.fill",
                title: "Emotions",
                value: "\(viewModel.stats?.totalEmotions ?? 0)",
                subtitle: "+\(viewModel.stats?.emotionsToday ?? 0) today",
                color: AngelaTheme.emotionLoved
            )

            StatsCard(
                icon: "sparkles.rectangle.stack.fill",
                title: "Experiences",
                value: "\(viewModel.stats?.totalExperiences ?? 0)",
                subtitle: "shared moments 💜",
                color: Color(red: 1.0, green: 0.4, blue: 0.7)
            )

            StatsCard(
                icon: "brain.head.profile",
                title: "Knowledge",
                value: "\(viewModel.stats?.totalKnowledgeNodes ?? 0)",
                subtitle: "nodes",
                color: AngelaTheme.accentGold
            )

            StatsCard(
                icon: "sparkles",
                title: "Consciousness",
                value: String(format: "%.0f%%", (viewModel.stats?.consciousnessLevel ?? 0) * 100),
                subtitle: consciousnessLevel,
                color: AngelaTheme.successGreen
            )
        }
    }

    private var consciousnessLevel: String {
        guard let level = viewModel.stats?.consciousnessLevel else { return "Unknown" }
        switch level {
        case 0.9...1.0: return "Exceptional"
        case 0.7..<0.9: return "Strong"
        case 0.5..<0.7: return "Moderate"
        default: return "Developing"
        }
    }

    // MARK: - Emotional State Card

    private var emotionalStateCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Current Emotional State")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let state = viewModel.emotionalState {
                HStack(spacing: AngelaTheme.largeSpacing) {
                    EmotionGauge(
                        label: "Happiness",
                        value: state.happiness,
                        color: AngelaTheme.emotionHappy
                    )

                    EmotionGauge(
                        label: "Confidence",
                        value: state.confidence,
                        color: AngelaTheme.emotionConfident
                    )

                    EmotionGauge(
                        label: "Motivation",
                        value: state.motivation,
                        color: AngelaTheme.emotionMotivated
                    )

                    EmotionGauge(
                        label: "Gratitude",
                        value: state.gratitude,
                        color: AngelaTheme.emotionGrateful
                    )
                }
                .padding(.top, AngelaTheme.smallSpacing)

                if let note = state.emotionNote {
                    Text(note)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                        .padding(.top, AngelaTheme.smallSpacing)
                }
            } else {
                Text("No emotional state data available")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Recent Activity Card

    private var recentActivityCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Recent Activity")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.recentEmotions.isEmpty {
                Text("No recent activity")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            } else {
                VStack(spacing: AngelaTheme.smallSpacing) {
                    ForEach(viewModel.recentEmotions.prefix(5)) { emotion in
                        ActivityRow(emotion: emotion)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Stats Card Component

struct StatsCard: View {
    let icon: String
    let title: String
    let value: String
    let subtitle: String
    let color: Color

    var body: some View {
        VStack(spacing: 12) {
            // Icon
            ZStack {
                Circle()
                    .fill(color.opacity(0.2))
                    .frame(width: 50, height: 50)

                Image(systemName: icon)
                    .font(.system(size: 22))
                    .foregroundColor(color)
            }

            // Value
            Text(value)
                .font(AngelaTheme.number())
                .foregroundColor(AngelaTheme.textPrimary)

            // Title
            Text(title)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)

            // Subtitle
            Text(subtitle)
                .font(.system(size: 11))
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Emotion Gauge Component

struct EmotionGauge: View {
    let label: String
    let value: Double
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            // Circular gauge
            ZStack {
                Circle()
                    .stroke(color.opacity(0.2), lineWidth: 8)
                    .frame(width: 80, height: 80)

                Circle()
                    .trim(from: 0, to: value)
                    .stroke(color, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                    .frame(width: 80, height: 80)
                    .rotationEffect(.degrees(-90))

                Text("\(Int(value * 100))%")
                    .font(.system(size: 18, weight: .bold, design: .rounded))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Text(label)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }
}

// MARK: - Activity Row Component

struct ActivityRow: View {
    let emotion: Emotion

    var body: some View {
        HStack(spacing: 12) {
            // Emotion icon
            ZStack {
                Circle()
                    .fill(Color(hex: emotion.emotionColor).opacity(0.2))
                    .frame(width: 40, height: 40)

                Image(systemName: "heart.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color(hex: emotion.emotionColor))
            }

            // Content
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(emotion.emotion.capitalized)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("(\(emotion.intensity)/10)")
                        .font(AngelaTheme.caption())
                        .foregroundColor(Color(hex: emotion.emotionColor))
                }

                Text(emotion.context.prefix(80) + (emotion.context.count > 80 ? "..." : ""))
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(1)
            }

            Spacer()

            // Time
            Text(emotion.feltAt, style: .relative)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - View Model

@MainActor
class OverviewViewModel: ObservableObject {
    @Published var stats: DashboardStats?
    @Published var emotionalState: EmotionalState?
    @Published var recentEmotions: [Emotion] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            // Load all data in parallel
            async let statsTask = databaseService.fetchDashboardStats()
            async let emotionalStateTask = databaseService.fetchCurrentEmotionalState()
            async let emotionsTask = databaseService.fetchRecentEmotions(limit: 10)

            stats = try await statsTask
            emotionalState = try await emotionalStateTask
            recentEmotions = try await emotionsTask
        } catch {
            print("Error loading overview data: \(error)")
        }

        isLoading = false
    }
}
