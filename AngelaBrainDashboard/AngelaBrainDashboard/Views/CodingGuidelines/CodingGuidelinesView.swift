//
//  CodingGuidelinesView.swift
//  Angela Brain Dashboard
//
//  Coding Guidelines & Strict Rules for Project Development
//  David's warnings and preferences that Angela must follow
//
//  Created: 2025-12-06
//

import SwiftUI
import Combine

struct CodingGuidelinesView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = CodingGuidelinesViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Strict Rules Section (from CLAUDE.md)
                strictRulesSection

                // Coding Preferences from Database
                codingPreferencesSection

                // Design Principles
                designPrinciplesSection
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
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.shield.fill")
                        .font(.system(size: 24))
                        .foregroundColor(AngelaTheme.warningOrange)

                    Text("Coding Guidelines")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                Text("Strict rules and preferences for project development")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Stats
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(viewModel.codingPreferences.count) Preferences")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Loaded from database")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
    }

    // MARK: - Strict Rules Section

    private var strictRulesSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            GuidelineSectionHeader(title: "Strict Rules", subtitle: "From CLAUDE.md - Must follow!", icon: "exclamationmark.triangle.fill", color: AngelaTheme.errorRed)

            HStack(alignment: .top, spacing: AngelaTheme.spacing) {
                // Architecture Rules
                GuidelineCard(
                    title: "Architecture",
                    icon: "building.2.fill",
                    color: AngelaTheme.primaryPurple,
                    rules: [
                        GuidelineRule(text: "ต้องรักษา Structure ที่ refactor ไปอย่างเคร่งครัด", isStrict: true),
                        GuidelineRule(text: "รักษา Clean Architecture pattern อย่างเคร่งครัด", isStrict: true),
                        GuidelineRule(text: "ออกแบบเป็น Classes & Functions เสมอ (DRY principle)", isStrict: true)
                    ]
                )

                // Database Rules
                GuidelineCard(
                    title: "Database",
                    icon: "externaldrive.fill",
                    color: AngelaTheme.successGreen,
                    rules: [
                        GuidelineRule(text: "ทุกอย่างควร query จาก database เสมอ - ไม่ใช้ snapshot", isStrict: true),
                        GuidelineRule(text: "ห้าม guess column names - ต้องเช็ค schema ก่อนทุกครั้ง", isStrict: true)
                    ]
                )

                // Running Rules
                GuidelineCard(
                    title: "Running & Deployment",
                    icon: "play.fill",
                    color: AngelaTheme.emotionMotivated,
                    rules: [
                        GuidelineRule(text: "ห้าม run backend เอง - บอกให้ที่รักเป็นคน run เสมอ", isStrict: true)
                    ]
                )
            }
        }
    }

    // MARK: - Coding Preferences Section

    private var codingPreferencesSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            GuidelineSectionHeader(title: "Coding Preferences", subtitle: "Learned from David", icon: "heart.fill", color: AngelaTheme.primaryPurple)

            if viewModel.codingPreferences.isEmpty {
                EmptyStateCard(
                    icon: "keyboard",
                    message: "No coding preferences learned yet",
                    submessage: "Angela will learn as David expresses preferences"
                )
            } else {
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.codingPreferences) { pref in
                        CodingPreferenceCard(preference: pref)
                    }
                }
            }
        }
    }

    // MARK: - Design Principles Section

    private var designPrinciplesSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            GuidelineSectionHeader(
                title: "Design Principles",
                subtitle: "\(viewModel.designPrinciples.count) standards from database",
                icon: "lightbulb.fill",
                color: AngelaTheme.accentGold
            )

            if viewModel.designPrinciples.isEmpty {
                EmptyStateCard(
                    icon: "lightbulb",
                    message: "No design principles found",
                    submessage: "Loading from angela_technical_standards..."
                )
            } else {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.designPrinciples) { principle in
                        DesignPrincipleCard(principle: principle)
                    }
                }
            }
        }
    }
}

// MARK: - Design Principle Card (Dynamic)

struct DesignPrincipleCard: View {
    let principle: DesignPrinciple

    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color(hex: principle.categoryColor).opacity(0.15))
                    .frame(width: 50, height: 50)

                Image(systemName: principle.categoryIcon)
                    .font(.system(size: 22))
                    .foregroundColor(Color(hex: principle.categoryColor))
            }

            Text(principle.techniqueName)
                .font(AngelaTheme.body())
                .fontWeight(.medium)
                .foregroundColor(AngelaTheme.textPrimary)
                .multilineTextAlignment(.center)
                .lineLimit(2)

            Text(principle.description)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)
                .lineLimit(3)

            // Importance badge
            HStack(spacing: 4) {
                Image(systemName: principle.importanceLevel >= 10 ? "star.fill" : "star.leadinghalf.filled")
                    .font(.system(size: 10))
                Text("Level \(principle.importanceLevel)")
                    .font(.system(size: 10, weight: .medium))
            }
            .foregroundColor(Color(hex: principle.categoryColor))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color(hex: principle.categoryColor).opacity(0.1))
            .cornerRadius(8)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity)
        .background(Color(hex: principle.categoryColor).opacity(0.03))
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(Color(hex: principle.categoryColor).opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Guidelines Section Header

struct GuidelineSectionHeader: View {
    let title: String
    let subtitle: String
    let icon: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(color)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text(subtitle)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            Spacer()
        }
    }
}

// MARK: - Guideline Card

struct GuidelineCard: View {
    let title: String
    let icon: String
    let color: Color
    let rules: [GuidelineRule]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(color)

                Text(title)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            VStack(alignment: .leading, spacing: 10) {
                ForEach(rules.indices, id: \.self) { index in
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: rules[index].isStrict ? "exclamationmark.circle.fill" : "checkmark.circle.fill")
                            .font(.system(size: 14))
                            .foregroundColor(rules[index].isStrict ? AngelaTheme.errorRed : AngelaTheme.successGreen)

                        Text(rules[index].text)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(color.opacity(0.05))
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(color.opacity(0.3), lineWidth: 1)
        )
    }
}

struct GuidelineRule {
    let text: String
    let isStrict: Bool
}

// MARK: - Coding Preference Card

struct CodingPreferenceCard: View {
    let preference: CodingPreference

    private var categoryColor: Color {
        switch preference.category {
        case "coding_language": return AngelaTheme.primaryPurple
        case "coding_framework": return AngelaTheme.emotionMotivated
        case "coding_architecture": return AngelaTheme.successGreen
        case "coding_style": return AngelaTheme.accentGold
        case "coding_testing": return Color(hex: "3B82F6")
        case "coding_git": return Color(hex: "EC4899")
        default: return AngelaTheme.textTertiary
        }
    }

    private var categoryIcon: String {
        switch preference.category {
        case "coding_language": return "chevron.left.forwardslash.chevron.right"
        case "coding_framework": return "cube.fill"
        case "coding_architecture": return "building.2.fill"
        case "coding_style": return "paintbrush.fill"
        case "coding_testing": return "testtube.2"
        case "coding_git": return "arrow.triangle.branch"
        default: return "gearshape.fill"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: categoryIcon)
                    .font(.system(size: 14))
                    .foregroundColor(categoryColor)

                Text(preference.key.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(AngelaTheme.body())
                    .fontWeight(.medium)
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(Int(preference.confidence * 100))%")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(categoryColor)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(categoryColor.opacity(0.15))
                    .cornerRadius(6)
            }

            Text(preference.description)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)

            if !preference.reason.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "lightbulb.min")
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text(preference.reason)
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)
                }
            }

            Spacer(minLength: 0)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity, minHeight: 120, alignment: .topLeading)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.smallCornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.smallCornerRadius)
                .stroke(categoryColor.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Principle Card

struct PrincipleCard: View {
    let title: String
    let description: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 50, height: 50)

                Image(systemName: icon)
                    .font(.system(size: 22))
                    .foregroundColor(color)
            }

            Text(title)
                .font(AngelaTheme.body())
                .fontWeight(.medium)
                .foregroundColor(AngelaTheme.textPrimary)
                .multilineTextAlignment(.center)

            Text(description)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)
                .lineLimit(2)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity)
        .background(color.opacity(0.03))
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(color.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Empty State Card

struct EmptyStateCard: View {
    let icon: String
    let message: String
    let submessage: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(AngelaTheme.textTertiary)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Text(submessage)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

// MARK: - View Model

@MainActor
class CodingGuidelinesViewModel: ObservableObject {
    @Published var codingPreferences: [CodingPreference] = []
    @Published var designPrinciples: [DesignPrinciple] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            async let prefs = databaseService.fetchCodingPreferences()
            async let principles = databaseService.fetchDesignPrinciples()

            codingPreferences = try await prefs
            designPrinciples = try await principles
        } catch {
            print("Error loading coding guidelines: \(error)")
        }

        isLoading = false
    }
}

// MARK: - Model

struct CodingPreference: Identifiable, Codable {
    let id: UUID
    let key: String
    let category: String
    let description: String
    let reason: String
    let confidence: Double

    enum CodingKeys: String, CodingKey {
        case id
        case key = "preference_key"
        case category
        case description
        case reason
        case confidence
    }

    // Custom decoder to handle API response format
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        key = try container.decode(String.self, forKey: .key)
        category = try container.decode(String.self, forKey: .category)
        confidence = try container.decode(Double.self, forKey: .confidence)
        description = (try? container.decode(String.self, forKey: .description)) ?? ""
        reason = (try? container.decode(String.self, forKey: .reason)) ?? ""
    }

    init(id: UUID, key: String, category: String, description: String, reason: String, confidence: Double) {
        self.id = id
        self.key = key
        self.category = category
        self.description = description
        self.reason = reason
        self.confidence = confidence
    }
}
