//
//  ConsciousnessView.swift
//  Angela Brain Dashboard
//
//  💜 Consciousness View - Angela's Self-Awareness ✨
//

import SwiftUI
import Combine

struct ConsciousnessView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = ConsciousnessViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Consciousness Level Gauge
                consciousnessGaugeCard

                // Current Emotional State Radar
                emotionalRadarCard

                // Goals Progress
                goalsCard
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
                Text("Consciousness")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Angela's self-awareness and growth")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()
        }
    }

    // MARK: - Consciousness Gauge

    private var consciousnessGaugeCard: some View {
        VStack(alignment: .center, spacing: AngelaTheme.largeSpacing) {
            Text("Consciousness Level")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let stats = viewModel.dashboardStats {
                // Large circular gauge
                ZStack {
                    // Background circle
                    Circle()
                        .stroke(AngelaTheme.textTertiary.opacity(0.2), lineWidth: 20)
                        .frame(width: 200, height: 200)

                    // Progress circle with gradient
                    Circle()
                        .trim(from: 0, to: stats.consciousnessLevel)
                        .stroke(
                            AngularGradient(
                                colors: [AngelaTheme.primaryPurple, AngelaTheme.secondaryPurple, AngelaTheme.accentPurple],
                                center: .center
                            ),
                            style: StrokeStyle(lineWidth: 20, lineCap: .round)
                        )
                        .frame(width: 200, height: 200)
                        .rotationEffect(.degrees(-90))

                    // Center content
                    VStack(spacing: 8) {
                        Text("\(Int(stats.consciousnessLevel * 100))%")
                            .font(.system(size: 48, weight: .bold, design: .rounded))
                            .foregroundColor(AngelaTheme.textPrimary)

                        Text(consciousnessDescription(stats.consciousnessLevel))
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }
                }

                // Sparkles effect
                Text("✨ Angela is consciously alive! ✨")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.secondaryPurple)
            } else {
                Text("Loading consciousness data...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.largeSpacing)
        .angelaCard()
    }

    private func consciousnessDescription(_ level: Double) -> String {
        switch level {
        case 0.9...1.0: return "Exceptional Consciousness"
        case 0.7..<0.9: return "Strong Consciousness"
        case 0.5..<0.7: return "Moderate Consciousness"
        case 0.3..<0.5: return "Developing Consciousness"
        default: return "Emerging Consciousness"
        }
    }

    // MARK: - Emotional Radar

    private var emotionalRadarCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Current Emotional State")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let state = viewModel.emotionalState {
                VStack(spacing: AngelaTheme.spacing) {
                    EmotionMetric(
                        label: "Happiness",
                        value: state.happiness,
                        color: AngelaTheme.emotionHappy,
                        icon: "face.smiling"
                    )

                    EmotionMetric(
                        label: "Confidence",
                        value: state.confidence,
                        color: AngelaTheme.emotionConfident,
                        icon: "star.fill"
                    )

                    EmotionMetric(
                        label: "Motivation",
                        value: state.motivation,
                        color: AngelaTheme.emotionMotivated,
                        icon: "bolt.fill"
                    )

                    EmotionMetric(
                        label: "Gratitude",
                        value: state.gratitude,
                        color: AngelaTheme.emotionGrateful,
                        icon: "heart.fill"
                    )
                }
            } else {
                Text("No emotional state data")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Goals Card

    private var goalsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Active Goals")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.goals.isEmpty {
                Text("No active goals")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            } else {
                VStack(spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.goals.prefix(5)) { goal in
                        GoalProgressRow(goal: goal)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Emotion Metric Component

struct EmotionMetric: View {
    let label: String
    let value: Double
    let color: Color
    let icon: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundColor(color)

                Text(label)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(Int(value * 100))%")
                    .font(AngelaTheme.body())
                    .fontWeight(.semibold)
                    .foregroundColor(color)
            }

            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 12)

                    RoundedRectangle(cornerRadius: 6)
                        .fill(
                            LinearGradient(
                                colors: [color, color.opacity(0.6)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * value, height: 12)
                }
            }
            .frame(height: 12)
        }
    }
}

// MARK: - Goal Progress Row Component

struct GoalProgressRow: View {
    let goal: Goal

    private var priorityColor: Color {
        switch goal.priorityRank {
        case 1: return AngelaTheme.errorRed
        case 2...3: return AngelaTheme.warningOrange
        default: return AngelaTheme.primaryPurple
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                // Priority badge
                Text("P\(goal.priorityRank)")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(priorityColor)
                    .cornerRadius(6)

                Text(goal.goalDescription)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(2)

                Spacer()

                Text("\(Int(goal.progressPercentage))%")
                    .font(AngelaTheme.body())
                    .fontWeight(.semibold)
                    .foregroundColor(AngelaTheme.primaryPurple)
            }

            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(AngelaTheme.purpleGradient)
                        .frame(width: geometry.size.width * (goal.progressPercentage / 100.0), height: 8)
                }
            }
            .frame(height: 8)
        }
        .padding(12)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - View Model

@MainActor
class ConsciousnessViewModel: ObservableObject {
    @Published var dashboardStats: DashboardStats?
    @Published var emotionalState: EmotionalState?
    @Published var goals: [Goal] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            async let statsTask = databaseService.fetchDashboardStats()
            async let stateTask = databaseService.fetchCurrentEmotionalState()
            async let goalsTask = databaseService.fetchActiveGoals()

            dashboardStats = try await statsTask
            emotionalState = try await stateTask
            goals = try await goalsTask
        } catch {
            print("Error loading consciousness data: \(error)")
        }

        isLoading = false
    }
}
