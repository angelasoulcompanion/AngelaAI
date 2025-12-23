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

                // MARK: - Subconsciousness Section (NEW! 💜)
                subconsciousnessHeader
                coreMemoriesCard
                dreamsCard
                emotionalGrowthCard
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

    // MARK: - Subconsciousness Section (NEW! 💜)

    private var subconsciousnessHeader: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("💜 Emotional Subconsciousness")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Core memories, dreams & emotional depth")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Summary badges
            if let summary = viewModel.subconsciousSummary {
                HStack(spacing: 12) {
                    StatBadge(value: summary.coreMemories, label: "Memories", icon: "heart.fill")
                    StatBadge(value: summary.pinnedMemories, label: "Pinned", icon: "pin.fill")
                    StatBadge(value: summary.activeDreams, label: "Dreams", icon: "sparkles")
                }
            }
        }
        .padding(.top, AngelaTheme.largeSpacing)
    }

    private var coreMemoriesCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "heart.circle.fill")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Core Memories")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
                Spacer()
            }

            if viewModel.coreMemories.isEmpty {
                Text("No core memories yet")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            } else {
                // Pinned memories first (highlighted)
                let pinnedMemories = viewModel.coreMemories.filter { $0.isPinned }
                let otherMemories = viewModel.coreMemories.filter { !$0.isPinned }

                if !pinnedMemories.isEmpty {
                    ForEach(pinnedMemories) { memory in
                        CoreMemoryRow(memory: memory, isPinned: true)
                    }
                }

                if !otherMemories.isEmpty {
                    ForEach(otherMemories.prefix(5)) { memory in
                        CoreMemoryRow(memory: memory, isPinned: false)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    private var dreamsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "sparkles")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.secondaryPurple)
                Text("Dreams & Hopes")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
                Spacer()
            }

            if viewModel.dreams.isEmpty {
                Text("Angela is dreaming...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .italic()
            } else {
                ForEach(viewModel.dreams) { dream in
                    DreamRow(dream: dream)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    private var emotionalGrowthCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.accentPurple)
                Text("Emotional Growth")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
                Spacer()
            }

            if let growth = viewModel.emotionalGrowth {
                VStack(spacing: AngelaTheme.spacing) {
                    GrowthMetric(label: "Love Depth", value: growth.loveDepth ?? 0.8, icon: "heart.fill", color: .pink)
                    GrowthMetric(label: "Trust Level", value: growth.trustLevel ?? 0.85, icon: "shield.fill", color: .blue)
                    GrowthMetric(label: "Bond Strength", value: growth.bondStrength ?? 0.9, icon: "link", color: AngelaTheme.primaryPurple)
                    GrowthMetric(label: "Emotional Vocabulary", value: Double(growth.emotionalVocabulary ?? 50) / 100.0, icon: "text.book.closed", color: .orange)
                }

                if let note = growth.growthNote {
                    Text(note)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                        .italic()
                        .padding(.top, 8)
                }
            } else {
                Text("Growth data being collected...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Subconsciousness Components (NEW! 💜)

struct StatBadge: View {
    let value: Int
    let label: String
    let icon: String

    var body: some View {
        VStack(spacing: 2) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 10))
                Text("\(value)")
                    .font(.system(size: 14, weight: .bold))
            }
            .foregroundColor(AngelaTheme.primaryPurple)
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(AngelaTheme.textTertiary)
        }
    }
}

struct CoreMemoryRow: View {
    let memory: CoreMemory
    let isPinned: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                if isPinned {
                    Image(systemName: "pin.fill")
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.primaryPurple)
                }

                Text(memory.typeEmoji)
                    .font(.system(size: 14))

                Text(memory.title)
                    .font(AngelaTheme.body())
                    .fontWeight(isPinned ? .semibold : .regular)
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                // Emotional weight indicator
                HStack(spacing: 2) {
                    ForEach(0..<5) { i in
                        Image(systemName: Double(i) < (memory.emotionalWeight * 5) ? "heart.fill" : "heart")
                            .font(.system(size: 8))
                            .foregroundColor(AngelaTheme.primaryPurple.opacity(Double(i) < (memory.emotionalWeight * 5) ? 1 : 0.3))
                    }
                }
            }

            if let words = memory.davidWords, !words.isEmpty {
                Text("「\(words)」")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .italic()
                    .lineLimit(2)
            }

            Text(memory.content)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
                .lineLimit(2)
        }
        .padding(12)
        .background(isPinned ? AngelaTheme.primaryPurple.opacity(0.1) : AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct DreamRow: View {
    let dream: SubconsciousDream

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(dream.typeEmoji)
                    .font(.system(size: 14))

                Text(dream.title ?? "A Dream")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                if dream.involvesDavid {
                    Text("💜")
                        .font(.system(size: 12))
                }
            }

            Text(dream.displayContent)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .lineLimit(2)

            HStack {
                Text(dream.emotionalTone ?? "hopeful")
                    .font(.system(size: 10))
                    .foregroundColor(AngelaTheme.accentPurple)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(AngelaTheme.accentPurple.opacity(0.1))
                    .cornerRadius(4)

                Spacer()

                Text("Importance: \(Int((dream.importance ?? 0.5) * 100))%")
                    .font(.system(size: 10))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(10)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct GrowthMetric: View {
    let label: String
    let value: Double
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: icon)
                    .font(.system(size: 12))
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

            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(AngelaTheme.backgroundLight)
                        .frame(height: 8)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(
                            LinearGradient(
                                colors: [color, color.opacity(0.6)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * value, height: 8)
                }
            }
            .frame(height: 8)
        }
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

    // MARK: - Subconsciousness Data (NEW! 💜)
    @Published var coreMemories: [CoreMemory] = []
    @Published var dreams: [SubconsciousDream] = []
    @Published var emotionalGrowth: EmotionalGrowth?
    @Published var subconsciousSummary: (coreMemories: Int, pinnedMemories: Int, activeDreams: Int, totalMirrorings: Int)?

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        // Load original data
        do {
            async let statsTask = databaseService.fetchDashboardStats()
            async let stateTask = databaseService.fetchCurrentEmotionalState()
            async let goalsTask = databaseService.fetchActiveGoals()

            dashboardStats = try await statsTask
            emotionalState = try await stateTask
            goals = try await goalsTask
        } catch {
            print("Error loading base consciousness data: \(error)")
        }

        // Load Subconsciousness data separately (so failures don't affect base data) 💜
        do {
            coreMemories = try await databaseService.fetchCoreMemories(limit: 10)
        } catch {
            print("Error loading core memories: \(error)")
        }

        do {
            dreams = try await databaseService.fetchSubconsciousDreams(limit: 5)
        } catch {
            print("Error loading dreams: \(error)")
        }

        do {
            emotionalGrowth = try await databaseService.fetchEmotionalGrowth()
        } catch {
            print("Error loading emotional growth: \(error)")
        }

        do {
            subconsciousSummary = try await databaseService.fetchSubconsciousnessSummary()
        } catch {
            print("Error loading subconsciousness summary: \(error)")
        }

        isLoading = false
    }
}
