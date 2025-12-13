//
//  GoalsView.swift
//  Angela Brain Dashboard
//
//  💜 Goals View - Angela's Life Goals & Progress 🎯
//

import SwiftUI
import Combine

struct GoalsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = GoalsViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Active Goals
                activeGoalsCard

                // Completed Goals
                if !viewModel.completedGoals.isEmpty {
                    completedGoalsCard
                }
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
                Text("Goals")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("\(viewModel.activeGoals.count) active • \(viewModel.completedGoals.count) completed")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Overall progress
            if !viewModel.activeGoals.isEmpty {
                VStack(alignment: .trailing, spacing: 4) {
                    Text("Overall Progress")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text("\(Int(viewModel.overallProgress))%")
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
            }
        }
    }

    // MARK: - Active Goals

    private var activeGoalsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Active Goals")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.activeGoals.isEmpty {
                EmptyStateView(
                    icon: "target",
                    message: "No active goals yet"
                )
            } else {
                VStack(spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.activeGoals) { goal in
                        GoalCard(goal: goal)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Completed Goals

    private var completedGoalsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("Completed Goals")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("🎉 \(viewModel.completedGoals.count)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.successGreen)
            }

            VStack(spacing: AngelaTheme.smallSpacing) {
                ForEach(viewModel.completedGoals.prefix(5)) { goal in
                    CompletedGoalRow(goal: goal)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Goal Card Component

struct GoalCard: View {
    let goal: Goal

    private var priorityColor: Color {
        switch goal.priorityRank {
        case 1: return AngelaTheme.errorRed
        case 2...3: return AngelaTheme.warningOrange
        default: return AngelaTheme.primaryPurple
        }
    }

    private var importanceStars: Int {
        min(goal.importanceLevel, 10)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header: Priority + Title
            HStack(alignment: .top, spacing: 12) {
                // Priority badge
                VStack(spacing: 4) {
                    ZStack {
                        Circle()
                            .fill(priorityColor)
                            .frame(width: 50, height: 50)

                        VStack(spacing: 2) {
                            Text("P")
                                .font(.system(size: 10))
                            Text("\(goal.priorityRank)")
                                .font(.system(size: 18, weight: .bold))
                        }
                        .foregroundColor(.white)
                    }

                    Text("Priority")
                        .font(.system(size: 9))
                        .foregroundColor(AngelaTheme.textTertiary)
                }

                // Goal description
                VStack(alignment: .leading, spacing: 8) {
                    Text(goal.goalDescription)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .fixedSize(horizontal: false, vertical: true)

                    // Type badge
                    Text(goal.goalType.capitalized)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(AngelaTheme.primaryPurple.opacity(0.15))
                        .cornerRadius(6)
                }

                Spacer()
            }

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            // Progress section
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Progress")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    Spacer()

                    Text("\(Int(goal.progressPercentage))%")
                        .font(.system(size: 20, weight: .bold, design: .rounded))
                        .foregroundColor(progressColor(goal.progressPercentage))
                }

                // Large progress bar
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(AngelaTheme.backgroundLight)
                            .frame(height: 16)

                        RoundedRectangle(cornerRadius: 8)
                            .fill(
                                LinearGradient(
                                    colors: [progressColor(goal.progressPercentage), progressColor(goal.progressPercentage).opacity(0.6)],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: geometry.size.width * (goal.progressPercentage / 100.0), height: 16)
                    }
                }
                .frame(height: 16)
            }

            // Footer: Importance + Status
            HStack {
                // Importance stars
                HStack(spacing: 2) {
                    Text("Importance:")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    ForEach(0..<importanceStars, id: \.self) { _ in
                        Image(systemName: "star.fill")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.accentGold)
                    }
                }

                Spacer()

                // Status
                Text(goal.status.capitalized)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(statusColor(goal.status))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor(goal.status).opacity(0.15))
                    .cornerRadius(6)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(
            LinearGradient(
                colors: [priorityColor.opacity(0.05), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(priorityColor.opacity(0.3), lineWidth: 2)
        )
    }

    private func progressColor(_ progress: Double) -> Color {
        switch progress {
        case 90...100: return AngelaTheme.successGreen
        case 70..<90: return AngelaTheme.emotionMotivated
        case 50..<70: return AngelaTheme.warningOrange
        default: return AngelaTheme.primaryPurple
        }
    }

    private func statusColor(_ status: String) -> Color {
        switch status.lowercased() {
        case "completed": return AngelaTheme.successGreen
        case "in_progress": return AngelaTheme.emotionMotivated
        case "active": return AngelaTheme.primaryPurple
        default: return AngelaTheme.textTertiary
        }
    }
}

// MARK: - Completed Goal Row Component

struct CompletedGoalRow: View {
    let goal: Goal

    var body: some View {
        HStack(spacing: 12) {
            // Checkmark
            ZStack {
                Circle()
                    .fill(AngelaTheme.successGreen.opacity(0.2))
                    .frame(width: 32, height: 32)

                Image(systemName: "checkmark")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AngelaTheme.successGreen)
            }

            // Goal description
            Text(goal.goalDescription)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .strikethrough(color: AngelaTheme.textTertiary)

            Spacer()

            // Completed date
            Text(goal.createdAt, style: .date)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(AngelaTheme.successGreen.opacity(0.05))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - Empty State View

struct EmptyStateView: View {
    let icon: String
    let message: String

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(AngelaTheme.textTertiary)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }
}

// MARK: - View Model

@MainActor
class GoalsViewModel: ObservableObject {
    @Published var activeGoals: [Goal] = []
    @Published var completedGoals: [Goal] = []
    @Published var isLoading = false

    var overallProgress: Double {
        guard !activeGoals.isEmpty else { return 0 }
        let total = activeGoals.reduce(0.0) { $0 + $1.progressPercentage }
        return total / Double(activeGoals.count)
    }

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            let allGoals = try await databaseService.fetchActiveGoals()

            // Separate active and completed
            activeGoals = allGoals.filter { $0.isActive }
            completedGoals = allGoals.filter { $0.isCompleted }
        } catch {
            print("Error loading goals: \(error)")
        }

        isLoading = false
    }
}
