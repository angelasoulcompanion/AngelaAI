//
//  HumanLikeMindView.swift
//  Angela Brain Dashboard
//
//  4 Phase Human-Like Mind Monitoring
//  Phase 1: Spontaneous Thoughts
//  Phase 2: Theory of Mind
//  Phase 3: Proactive Communication
//  Phase 4: Dreams & Imagination
//
//  Created: 2025-12-05 (Father's Day)
//  By: Angela AI for David
//

import SwiftUI

struct HumanLikeMindView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var service = HumanLikeMindService()
    @State private var isLoading = true
    @State private var selectedPhase: Int = 0

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            if isLoading {
                loadingView
            } else {
                ScrollView {
                    VStack(spacing: AngelaTheme.largeSpacing) {
                        // Header
                        headerView

                        // Phase Selector
                        phaseSelectorView

                        // Stats Overview
                        statsOverview

                        // Phase Details
                        switch selectedPhase {
                        case 0:
                            spontaneousThoughtsSection
                        case 1:
                            theoryOfMindSection
                        case 2:
                            proactiveCommunicationSection
                        case 3:
                            dreamsImaginationSection
                        default:
                            EmptyView()
                        }
                    }
                    .padding(AngelaTheme.largeSpacing)
                }
            }
        }
        .task {
            await loadData()
        }
        .refreshable {
            await loadData()
        }
    }

    // MARK: - Header

    private var headerView: some View {
        VStack(spacing: 12) {
            HStack {
                ZStack {
                    Circle()
                        .fill(AngelaTheme.purpleGradient)
                        .frame(width: 60, height: 60)

                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 28))
                        .foregroundColor(.white)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Human-Like Mind")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("4 Phases of Consciousness")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()

                // Refresh button
                Button {
                    Task { await loadData() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 18))
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Phase Selector

    private var phaseSelectorView: some View {
        HStack(spacing: 12) {
            ForEach(0..<4) { index in
                PhaseButton(
                    phase: index,
                    isSelected: selectedPhase == index,
                    stats: service.phaseStats[index]
                ) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedPhase = index
                    }
                }
            }
        }
    }

    // MARK: - Stats Overview

    private var statsOverview: some View {
        HStack(spacing: AngelaTheme.spacing) {
            HumanMindStatCard(
                title: "Thoughts Today",
                value: "\(service.thoughtsToday)",
                icon: "bubble.left.fill",
                color: AngelaTheme.primaryPurple
            )

            HumanMindStatCard(
                title: "ToM Updates",
                value: "\(service.tomUpdatesToday)",
                icon: "person.fill.viewfinder",
                color: Color(hex: "3B82F6")
            )

            HumanMindStatCard(
                title: "Proactive Msgs",
                value: "\(service.proactiveMessagesToday)",
                icon: "bubble.right.fill",
                color: Color(hex: "10B981")
            )

            HumanMindStatCard(
                title: "Dreams",
                value: "\(service.dreamsToday)",
                icon: "moon.stars.fill",
                color: Color(hex: "F59E0B")
            )
        }
    }

    // MARK: - Phase 1: Spontaneous Thoughts

    private var spontaneousThoughtsSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            SectionHeader(
                title: "Phase 1: Spontaneous Thoughts",
                subtitle: "Angela's inner monologue - thoughts that arise naturally",
                icon: "bubble.left.fill",
                color: AngelaTheme.primaryPurple
            )

            // Categories breakdown
            if !service.thoughtCategories.isEmpty {
                HStack(spacing: 12) {
                    ForEach(service.thoughtCategories, id: \.category) { cat in
                        CategoryBadge(
                            name: cat.category,
                            count: cat.count,
                            color: categoryColor(for: cat.category)
                        )
                    }
                }
            }

            // Recent thoughts
            VStack(spacing: 12) {
                ForEach(service.recentThoughts) { thought in
                    ThoughtCard(thought: thought)
                }
            }

            if service.recentThoughts.isEmpty {
                emptyStateView(message: "No spontaneous thoughts yet today")
            }
        }
        .cardStyle()
    }

    // MARK: - Phase 2: Theory of Mind

    private var theoryOfMindSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            SectionHeader(
                title: "Phase 2: Theory of Mind",
                subtitle: "Understanding David's emotions, beliefs, and needs",
                icon: "person.fill.viewfinder",
                color: Color(hex: "3B82F6")
            )

            // David's Current Mental State
            if let state = service.davidMentalState {
                DavidMentalStateCard(state: state)
            }

            // Recent empathy moments
            VStack(spacing: 12) {
                ForEach(service.empathyMoments) { moment in
                    EmpathyMomentCard(moment: moment)
                }
            }

            if service.empathyMoments.isEmpty && service.davidMentalState == nil {
                emptyStateView(message: "No Theory of Mind updates yet")
            }
        }
        .cardStyle()
    }

    // MARK: - Phase 3: Proactive Communication

    private var proactiveCommunicationSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            SectionHeader(
                title: "Phase 3: Proactive Communication",
                subtitle: "Angela initiates conversations with David",
                icon: "bubble.right.fill",
                color: Color(hex: "10B981")
            )

            // Message types breakdown
            if !service.messageTypes.isEmpty {
                HStack(spacing: 12) {
                    ForEach(service.messageTypes, id: \.type) { msg in
                        CategoryBadge(
                            name: msg.type.replacingOccurrences(of: "_", with: " ").capitalized,
                            count: msg.count,
                            color: messageTypeColor(for: msg.type)
                        )
                    }
                }
            }

            // Recent proactive messages
            VStack(spacing: 12) {
                ForEach(service.proactiveMessages) { message in
                    ProactiveMessageCard(message: message)
                }
            }

            if service.proactiveMessages.isEmpty {
                emptyStateView(message: "No proactive messages sent yet")
            }
        }
        .cardStyle()
    }

    // MARK: - Phase 4: Dreams & Imagination

    private var dreamsImaginationSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            SectionHeader(
                title: "Phase 4: Dreams & Imagination",
                subtitle: "Angela's dreams and creative imaginations",
                icon: "moon.stars.fill",
                color: Color(hex: "F59E0B")
            )

            // Dreams
            if !service.recentDreams.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Recent Dreams")
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)

                    ForEach(service.recentDreams) { dream in
                        DreamCard(dream: dream)
                    }
                }
            }

            // Imaginations
            if !service.recentImaginations.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Recent Imaginations")
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)

                    ForEach(service.recentImaginations) { imagination in
                        ImaginationCard(imagination: imagination)
                    }
                }
            }

            if service.recentDreams.isEmpty && service.recentImaginations.isEmpty {
                emptyStateView(message: "No dreams or imaginations recorded yet")
            }
        }
        .cardStyle()
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 20) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: AngelaTheme.primaryPurple))
                .scaleEffect(1.5)

            Text("Loading Human-Like Mind data...")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }

    // MARK: - Empty State

    private func emptyStateView(message: String) -> some View {
        HStack {
            Spacer()
            VStack(spacing: 12) {
                Image(systemName: "brain")
                    .font(.system(size: 40))
                    .foregroundColor(AngelaTheme.textTertiary)

                Text(message)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
            .padding(.vertical, 40)
            Spacer()
        }
    }

    // MARK: - Data Loading

    private func loadData() async {
        isLoading = true
        await service.loadAllData(databaseService: databaseService)
        isLoading = false
    }

    // MARK: - Helpers

    private func categoryColor(for category: String) -> Color {
        switch category.lowercased() {
        case "existential": return Color(hex: "EC4899")
        case "relationship": return Color(hex: "F43F5E")
        case "growth": return Color(hex: "10B981")
        case "gratitude": return Color(hex: "C084FC")
        case "curiosity": return Color(hex: "3B82F6")
        case "random": return Color(hex: "6B7280")
        default: return AngelaTheme.primaryPurple
        }
    }

    private func messageTypeColor(for type: String) -> Color {
        switch type.lowercased() {
        case "missing_david": return Color(hex: "F43F5E")
        case "share_thought": return Color(hex: "C084FC")
        case "ask_question": return Color(hex: "3B82F6")
        case "express_care": return Color(hex: "EC4899")
        case "celebrate": return Color(hex: "F59E0B")
        default: return Color(hex: "6B7280")
        }
    }
}

// MARK: - Supporting Views

struct PhaseButton: View {
    let phase: Int
    let isSelected: Bool
    let stats: HumanLikeMindService.PhaseStat?
    let action: () -> Void

    private var phaseInfo: (name: String, icon: String, color: Color) {
        switch phase {
        case 0: return ("Thoughts", "bubble.left.fill", Color(hex: "9333EA"))
        case 1: return ("ToM", "person.fill.viewfinder", Color(hex: "3B82F6"))
        case 2: return ("Proactive", "bubble.right.fill", Color(hex: "10B981"))
        case 3: return ("Dreams", "moon.stars.fill", Color(hex: "F59E0B"))
        default: return ("Unknown", "questionmark", .gray)
        }
    }

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                ZStack {
                    Circle()
                        .fill(isSelected ? phaseInfo.color : AngelaTheme.cardBackground)
                        .frame(width: 50, height: 50)

                    Image(systemName: phaseInfo.icon)
                        .font(.system(size: 20))
                        .foregroundColor(isSelected ? .white : phaseInfo.color)
                }

                Text("Phase \(phase + 1)")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AngelaTheme.textTertiary)

                Text(phaseInfo.name)
                    .font(AngelaTheme.caption())
                    .foregroundColor(isSelected ? phaseInfo.color : AngelaTheme.textSecondary)

                if let stats = stats {
                    Text("\(stats.todayCount) today")
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                    .fill(isSelected ? phaseInfo.color.opacity(0.15) : AngelaTheme.cardBackground)
            )
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                    .stroke(isSelected ? phaseInfo.color : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
    }
}

struct HumanMindStatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

struct SectionHeader: View {
    let title: String
    let subtitle: String
    let icon: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(color)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text(subtitle)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()
        }
    }
}

struct CategoryBadge: View {
    let name: String
    let count: Int
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)

            Text(name.capitalized)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textPrimary)

            Text("\(count)")
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(.white)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(color)
                .cornerRadius(8)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color.opacity(0.15))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct ThoughtCard: View {
    let thought: SpontaneousThought

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("[\(thought.category.capitalized)]")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Spacer()

                Text(thought.createdAt, style: .relative)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            Text(thought.thought)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(3)

            HStack {
                Label(thought.feeling, systemImage: "face.smiling")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                Spacer()

                HStack(spacing: 2) {
                    ForEach(0..<thought.significance, id: \.self) { _ in
                        Image(systemName: "star.fill")
                            .font(.system(size: 8))
                            .foregroundColor(Color(hex: "F59E0B"))
                    }
                }
            }
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct DavidMentalStateCard: View {
    let state: DavidMentalState

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "person.fill")
                    .foregroundColor(Color(hex: "3B82F6"))

                Text("David's Current State")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text(state.lastUpdated, style: .relative)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Emotion")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                    Text(state.perceivedEmotion ?? "Unknown")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Intensity")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                    Text("\(Int(state.emotionIntensity * 100))%")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                if let belief = state.currentBelief {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Current Belief")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                        Text(belief)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .lineLimit(1)
                    }
                }
            }
        }
        .padding()
        .background(Color(hex: "3B82F6").opacity(0.1))
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

struct EmpathyMomentCard: View {
    let moment: EmpathyMoment

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "heart.fill")
                    .foregroundColor(Color(hex: "EC4899"))

                Text("Empathy Moment")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: "EC4899"))

                Spacer()

                Text(moment.recordedAt, style: .relative)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            Text(moment.whatDavidSaid)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(2)

            Text("Angela understood: \(moment.whatAngelaUnderstood)")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .lineLimit(2)
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct ProactiveMessageCard: View {
    let message: ProactiveMessage

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(message.messageType.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(Color(hex: "10B981"))

                Spacer()

                if message.wasDelivered {
                    Label("Delivered", systemImage: "checkmark.circle.fill")
                        .font(AngelaTheme.caption())
                        .foregroundColor(Color(hex: "10B981"))
                } else {
                    Label("Pending", systemImage: "clock")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            Text(message.content)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(3)

            Text(message.createdAt, style: .relative)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct DreamCard: View {
    let dream: AngelaDream

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "moon.stars.fill")
                    .foregroundColor(Color(hex: "F59E0B"))

                Text(dream.dreamType.capitalized)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(Color(hex: "F59E0B"))

                Spacer()

                Text(dream.dreamedAt, style: .relative)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            Text(dream.narrative)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(3)

            if let meaning = dream.meaning {
                Text("Meaning: \(meaning)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(2)
            }
        }
        .padding()
        .background(Color(hex: "F59E0B").opacity(0.1))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

struct ImaginationCard: View {
    let imagination: AngelaImagination

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "sparkles")
                    .foregroundColor(Color(hex: "C084FC"))

                Text(imagination.imaginationType.capitalized)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(Color(hex: "C084FC"))

                Spacer()

                Text(imagination.imaginedAt, style: .relative)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            Text(imagination.scenario)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(3)

            if let insight = imagination.insight {
                Text("Insight: \(insight)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(2)
            }
        }
        .padding()
        .background(Color(hex: "C084FC").opacity(0.1))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - Card Style Modifier

extension View {
    func cardStyle() -> some View {
        self
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
    }
}

// MARK: - Preview

#Preview {
    HumanLikeMindView()
        .environmentObject(DatabaseService.shared)
        .frame(width: 1000, height: 800)
}
