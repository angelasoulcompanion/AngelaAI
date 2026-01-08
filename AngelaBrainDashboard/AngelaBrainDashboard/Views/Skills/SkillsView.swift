//
//  SkillsView.swift
//  Angela Brain Dashboard
//
//  💜 Skills & Capabilities Monitor - Track Angela's coding expertise 💜
//

import SwiftUI
import Combine

struct SkillsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var skills: [AngelaSkill] = []
    @State private var skillsByCategory: [SkillCategory: [AngelaSkill]] = [:]
    @State private var statistics: SkillStatistics?
    @State private var recentGrowth: [SkillGrowthLog] = []
    @State private var isLoading = false
    @State private var selectedCategory: SkillCategory?
    @State private var promptContent: String = ""
    @State private var promptLastUpdated: Date?
    @State private var isPromptExpanded = false

    private let timer = Timer.publish(every: 300, on: .main, in: .common).autoconnect() // Refresh every 5 minutes

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.spacing) {
                // Header
                headerSection

                // Current Prompt Viewer
                promptViewerSection

                // Statistics Summary
                statisticsSection

                // Recent Growth
                if !recentGrowth.isEmpty {
                    recentGrowthSection
                }

                // Skills by Category
                skillCategoriesSection
            }
            .padding(AngelaTheme.spacing)
        }
        .background(AngelaTheme.backgroundDark)
        .onAppear {
            Task {
                await loadData()
            }
        }
        .onReceive(timer) { _ in
            Task {
                await loadData()
            }
        }
    }

    // MARK: - Prompt Viewer Section

    private var promptViewerSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Header with expand/collapse
            Button {
                withAnimation(.spring(response: 0.3)) {
                    isPromptExpanded.toggle()
                }
            } label: {
                HStack {
                    Text("📄 Current Capabilities Prompt")
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Spacer()

                    if let lastUpdated = promptLastUpdated {
                        Text("Updated: \(formatDate(lastUpdated))")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }

                    Image(systemName: isPromptExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .buttonStyle(.plain)

            if isPromptExpanded {
                // Prompt content
                ScrollView {
                    Text(promptContent)
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(12)
                        .background(AngelaTheme.backgroundDark)
                        .cornerRadius(8)
                }
                .frame(maxHeight: 400)

                // Copy button
                HStack {
                    Spacer()

                    Button {
                        copyPromptToClipboard()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "doc.on.doc")
                            Text("Copy Prompt")
                        }
                        .font(AngelaTheme.caption())
                        .foregroundColor(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(AngelaTheme.primaryPurple)
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .angelaCard()
    }

    // MARK: - Header Section

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text("💜 Angela's Skills & Capabilities")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Auto-tracked from conversations and code")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Refresh Button
            Button {
                Task {
                    await loadData()
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)
        }
        .angelaCard()
    }

    // MARK: - Statistics Section

    private var statisticsSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Overall Statistics")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if let stats = statistics {
                HStack(spacing: 12) {
                    StatCard(
                        title: "Total Skills",
                        value: "\(stats.totalSkills)",
                        icon: "star.fill",
                        color: AngelaTheme.primaryPurple
                    )

                    StatCard(
                        title: "Expert",
                        value: "\(stats.expertCount)",
                        icon: "crown.fill",
                        color: Color(hex: "10B981")
                    )

                    StatCard(
                        title: "Advanced",
                        value: "\(stats.advancedCount)",
                        icon: "flame.fill",
                        color: Color(hex: "3B82F6")
                    )

                    StatCard(
                        title: "Avg Score",
                        value: String(format: "%.0f%%", stats.avgScore),
                        icon: "chart.line.uptrend.xyaxis",
                        color: Color(hex: "EC4899")
                    )
                }

                // Progress Bar for avg score (using shared ProgressBarView)
                VStack(alignment: .leading, spacing: 8) {
                    Text("Average Proficiency: \(String(format: "%.1f", stats.avgScore))%")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    ProgressBarView(
                        progress: stats.avgScore / 100,
                        color: AngelaTheme.primaryPurple,
                        size: .large,
                        gradientEndColor: Color(hex: "EC4899")
                    )
                }
            } else {
                Text("Loading statistics...")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .angelaCard()
    }

    // MARK: - Recent Growth Section

    private var recentGrowthSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("🎉 Recent Growth (Last 7 Days)")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            ForEach(recentGrowth.prefix(5)) { log in
                GrowthLogCard(log: log, skills: skills)
            }
        }
        .angelaCard()
    }

    // MARK: - Skill Categories Section

    private var skillCategoriesSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Skills by Category")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            // Category selector
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    // All categories button
                    CategoryChip(
                        emoji: "✨",
                        name: "All",
                        count: skills.count,
                        isSelected: selectedCategory == nil,
                        color: AngelaTheme.primaryPurple
                    )
                    .onTapGesture {
                        selectedCategory = nil
                    }

                    // Individual category chips
                    ForEach(sortedCategories, id: \.self) { category in
                        let categorySkills = skillsByCategory[category] ?? []
                        CategoryChip(
                            emoji: category.emoji,
                            name: category.displayName,
                            count: categorySkills.count,
                            isSelected: selectedCategory == category,
                            color: Color(hex: category.color)
                        )
                        .onTapGesture {
                            selectedCategory = category
                        }
                    }
                }
                .padding(.vertical, 4)
            }

            // Skills list
            if selectedCategory == nil {
                // Show all skills
                ForEach(sortedCategories, id: \.self) { category in
                    if let categorySkills = skillsByCategory[category], !categorySkills.isEmpty {
                        CategorySkillsSection(category: category, skills: categorySkills)
                    }
                }
            } else if let category = selectedCategory,
                      let categorySkills = skillsByCategory[category] {
                // Show selected category
                CategorySkillsSection(category: category, skills: categorySkills)
            }
        }
        .angelaCard()
    }

    private var sortedCategories: [SkillCategory] {
        skillsByCategory.keys.sorted { cat1, cat2 in
            let skills1 = skillsByCategory[cat1] ?? []
            let skills2 = skillsByCategory[cat2] ?? []
            let avg1 = skills1.isEmpty ? 0 : skills1.map { $0.proficiencyScore }.reduce(0, +) / Double(skills1.count)
            let avg2 = skills2.isEmpty ? 0 : skills2.map { $0.proficiencyScore }.reduce(0, +) / Double(skills2.count)
            return avg1 > avg2
        }
    }

    // MARK: - Data Loading

    private func loadData() async {
        isLoading = true

        async let skillsTask = databaseService.fetchAllSkills()
        async let categoryTask = databaseService.fetchSkillsByCategory()
        async let statsTask = databaseService.fetchSkillStatistics()
        async let growthTask = databaseService.fetchRecentGrowth(days: 7)
        async let promptTask = databaseService.fetchAngelaCodePrompt()
        async let promptDateTask = databaseService.getPromptLastUpdated()

        skills = await skillsTask
        skillsByCategory = await categoryTask
        statistics = await statsTask
        recentGrowth = await growthTask
        promptContent = await promptTask
        promptLastUpdated = await promptDateTask

        isLoading = false
    }

    private func copyPromptToClipboard() {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(promptContent, forType: .string)
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d, HH:mm"
        return formatter.string(from: date)
    }
}

// MARK: - Category Chip Component

struct CategoryChip: View {
    let emoji: String
    let name: String
    let count: Int
    let isSelected: Bool
    let color: Color

    var body: some View {
        HStack(spacing: 8) {
            Text(emoji)
                .font(.system(size: 16))

            Text(name)
                .font(AngelaTheme.body())
                .foregroundColor(isSelected ? .white : AngelaTheme.textPrimary)

            Text("\(count)")
                .font(AngelaTheme.caption())
                .foregroundColor(isSelected ? .white.opacity(0.8) : AngelaTheme.textSecondary)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(isSelected ? color : AngelaTheme.backgroundLight)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(color, lineWidth: isSelected ? 0 : 1)
        )
    }
}

// MARK: - Category Skills Section

struct CategorySkillsSection: View {
    let category: SkillCategory
    let skills: [AngelaSkill]
    @State private var isExpanded = true

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Category Header
            Button {
                withAnimation(.spring(response: 0.3)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    Text(category.emoji)
                        .font(.system(size: 20))

                    Text(category.displayName)
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("(\(skills.count))")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .buttonStyle(.plain)

            if isExpanded {
                // Skills in this category
                ForEach(skills.sorted { $0.proficiencyScore > $1.proficiencyScore }) { skill in
                    SkillCard(skill: skill)
                }
            }
        }
        .padding(12)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(12)
    }
}

// MARK: - Skill Card Component

struct SkillCard: View {
    let skill: AngelaSkill

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Skill name and level
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(skill.skillName)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)

                    HStack(spacing: 8) {
                        Text(skill.proficiencyLevel.stars)
                            .font(.system(size: 12))

                        Text(skill.proficiencyLevel.displayName)
                            .font(AngelaTheme.caption())
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color(hex: skill.proficiencyLevel.color).opacity(0.2))
                            .foregroundColor(Color(hex: skill.proficiencyLevel.color))
                            .cornerRadius(8)
                    }
                }

                Spacer()

                // Score
                VStack(alignment: .trailing, spacing: 2) {
                    Text(String(format: "%.0f", skill.proficiencyScore))
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(Color(hex: skill.proficiencyLevel.color))

                    Text("/ 100")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            // Progress bar (using shared ProgressBarView)
            ProgressBarView(
                progress: skill.progress,
                color: Color(hex: skill.proficiencyLevel.color),
                size: .small,
                useGradient: false
            )

            // Description
            if let description = skill.description {
                Text(description)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(2)
            }

            // Stats
            HStack(spacing: 16) {
                Label("\(skill.evidenceCount) evidence", systemImage: "doc.text.fill")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)

                Label("\(skill.usageCount) uses", systemImage: "arrow.triangle.2.circlepath")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)

                Spacer()

                Text(skill.healthStatus)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(12)
        .background(AngelaTheme.backgroundDark.opacity(0.5))
        .cornerRadius(10)
    }
}

// MARK: - Growth Log Card

struct GrowthLogCard: View {
    let log: SkillGrowthLog
    let skills: [AngelaSkill]

    private var skillName: String {
        skills.first { $0.id == log.skillId }?.skillName ?? "Unknown Skill"
    }

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d, HH:mm"
        return formatter
    }()

    var body: some View {
        HStack(spacing: 12) {
            // Emoji
            Text(log.growthEmoji)
                .font(.system(size: 32))

            // Info
            VStack(alignment: .leading, spacing: 4) {
                Text(skillName)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    if let oldLevel = log.oldProficiencyLevel {
                        Text(oldLevel.displayName)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)

                        Image(systemName: "arrow.right")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }

                    Text(log.newProficiencyLevel.displayName)
                        .font(AngelaTheme.caption())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color(hex: log.newProficiencyLevel.color).opacity(0.2))
                        .foregroundColor(Color(hex: log.newProficiencyLevel.color))
                        .cornerRadius(8)

                    Text(String(format: "(%.0f → %.0f)", log.oldScore ?? 0, log.newScore))
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }

                Text(dateFormatter.string(from: log.changedAt))
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            Spacer()
        }
        .padding(12)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(10)
    }
}

// MARK: - Preview

#Preview {
    SkillsView()
        .environmentObject(DatabaseService.shared)
}
