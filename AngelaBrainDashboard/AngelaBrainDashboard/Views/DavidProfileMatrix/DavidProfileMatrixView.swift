//
//  DavidProfileMatrixView.swift
//  Angela Brain Dashboard
//
//  David's Complete Profile Matrix Charts
//  Created: 2025-12-11
//

import SwiftUI
import Combine

struct DavidProfileMatrixView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = DavidProfileMatrixViewModel()
    @State private var selectedMatrix: MatrixType = .skills

    var body: some View {
        VStack(spacing: 0) {
            // Header
            header

            // Matrix selector
            matrixSelector

            // Main content
            ScrollView {
                VStack(spacing: AngelaTheme.largeSpacing) {
                    switch selectedMatrix {
                    case .skills:
                        SkillsMatrixView(data: viewModel.skillsData)
                    case .workingStyle:
                        WorkingStyleMatrixView(data: viewModel.workingStyleData)
                    case .career:
                        CareerMatrixView(data: viewModel.careerData)
                    case .interests:
                        InterestsMatrixView(data: viewModel.interestsData)
                    case .all:
                        AllMatricesView(viewModel: viewModel)
                    }
                }
                .padding(AngelaTheme.largeSpacing)
            }
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: AngelaTheme.spacing) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 8) {
                        Text("David's Profile Matrix")
                            .font(AngelaTheme.title())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Image(systemName: "chart.bar.xaxis")
                            .font(.system(size: 18))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }

                    Text("Visual representation of skills, traits, and experiences")
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
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - Matrix Selector

    private var matrixSelector: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(MatrixType.allCases, id: \.self) { type in
                    MatrixSelectorButton(
                        type: type,
                        isSelected: selectedMatrix == type,
                        action: { selectedMatrix = type }
                    )
                }
            }
            .padding(.horizontal, AngelaTheme.largeSpacing)
            .padding(.vertical, 12)
        }
        .background(AngelaTheme.backgroundLight.opacity(0.5))
    }
}

// MARK: - Matrix Type Enum

enum MatrixType: String, CaseIterable {
    case skills = "Technical Skills"
    case workingStyle = "Working Style"
    case career = "Career"
    case interests = "Interests"
    case all = "All Matrices"

    var icon: String {
        switch self {
        case .skills: return "cpu.fill"
        case .workingStyle: return "person.fill.checkmark"
        case .career: return "briefcase.fill"
        case .interests: return "heart.fill"
        case .all: return "square.grid.2x2.fill"
        }
    }

    var color: Color {
        switch self {
        case .skills: return AngelaTheme.primaryPurple
        case .workingStyle: return AngelaTheme.accentGold
        case .career: return AngelaTheme.successGreen
        case .interests: return Color.pink
        case .all: return AngelaTheme.textSecondary
        }
    }
}

// MARK: - Matrix Selector Button

struct MatrixSelectorButton: View {
    let type: MatrixType
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: type.icon)
                    .font(.system(size: 14))
                Text(type.rawValue)
                    .font(AngelaTheme.body())
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(isSelected ? type.color.opacity(0.2) : AngelaTheme.cardBackground)
            .foregroundColor(isSelected ? type.color : AngelaTheme.textSecondary)
            .cornerRadius(20)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(isSelected ? type.color : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Skills Matrix View

struct SkillsMatrixView: View {
    let data: [SkillMatrixItem]

    private let levels = ["Beginner", "Intermediate", "Advanced", "Expert"]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Title
            HStack {
                Image(systemName: "cpu.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Technical Skills Proficiency")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Matrix Grid
            VStack(spacing: 2) {
                // Header row
                HStack(spacing: 2) {
                    Text("")
                        .frame(width: 140, alignment: .leading)

                    ForEach(levels, id: \.self) { level in
                        Text(level)
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(AngelaTheme.textSecondary)
                            .frame(maxWidth: .infinity)
                    }
                }
                .padding(.bottom, 8)

                // Data rows
                ForEach(data) { item in
                    HStack(spacing: 2) {
                        Text(item.skill)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .frame(width: 140, alignment: .leading)

                        ForEach(0..<4, id: \.self) { index in
                            let isActive = item.levelIndex == index
                            Rectangle()
                                .fill(isActive ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                                .frame(height: 36)
                                .overlay(
                                    Group {
                                        if isActive {
                                            Circle()
                                                .fill(Color.white)
                                                .frame(width: 12, height: 12)
                                        }
                                    }
                                )
                        }
                    }
                }
            }
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
        }
    }
}

// MARK: - Working Style Matrix View

struct WorkingStyleMatrixView: View {
    let data: [WorkingStyleItem]

    private let dimensions = ["Impact", "Consistency", "Importance"]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Title
            HStack {
                Image(systemName: "person.fill.checkmark")
                    .foregroundColor(AngelaTheme.accentGold)
                Text("Working Style Traits")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Matrix Grid
            VStack(spacing: 2) {
                // Header row
                HStack(spacing: 2) {
                    Text("")
                        .frame(width: 180, alignment: .leading)

                    ForEach(dimensions, id: \.self) { dim in
                        Text(dim)
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(AngelaTheme.textSecondary)
                            .frame(maxWidth: .infinity)
                    }
                }
                .padding(.bottom, 8)

                // Data rows
                ForEach(data) { item in
                    HStack(spacing: 2) {
                        Text(item.trait)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .frame(width: 180, alignment: .leading)
                            .lineLimit(1)

                        ForEach([item.impact, item.consistency, item.importance], id: \.self) { value in
                            ZStack {
                                Rectangle()
                                    .fill(colorForValue(value))
                                    .frame(height: 36)

                                Text("\(value)")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundColor(value > 5 ? .white : AngelaTheme.textTertiary)
                            }
                        }
                    }
                }
            }
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
        }
    }

    private func colorForValue(_ value: Int) -> Color {
        let intensity = Double(value) / 10.0
        return AngelaTheme.accentGold.opacity(0.2 + (intensity * 0.8))
    }
}

// MARK: - Career Matrix View

struct CareerMatrixView: View {
    let data: [CareerMatrixItem]

    private let companies = ["Siameast", "Siamraj", "SCB", "GULF", "Various"]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Title
            HStack {
                Image(systemName: "briefcase.fill")
                    .foregroundColor(AngelaTheme.successGreen)
                Text("Career Experience (Years)")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Matrix Grid
            VStack(spacing: 2) {
                // Header row
                HStack(spacing: 2) {
                    Text("")
                        .frame(width: 100, alignment: .leading)

                    ForEach(companies, id: \.self) { company in
                        Text(company)
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(AngelaTheme.textSecondary)
                            .frame(maxWidth: .infinity)
                    }
                }
                .padding(.bottom, 8)

                // Data rows
                ForEach(data) { item in
                    HStack(spacing: 2) {
                        Text(item.role)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .frame(width: 100, alignment: .leading)

                        ForEach(item.yearsPerCompany, id: \.company) { companyYears in
                            ZStack {
                                Rectangle()
                                    .fill(companyYears.years > 0 ? AngelaTheme.successGreen.opacity(0.3 + Double(companyYears.years) * 0.07) : AngelaTheme.backgroundLight)
                                    .frame(height: 36)

                                if companyYears.years > 0 {
                                    Text("\(companyYears.years)y")
                                        .font(.system(size: 11, weight: .bold))
                                        .foregroundColor(.white)
                                }
                            }
                        }
                    }
                }
            }
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
        }
    }
}

// MARK: - Interests Matrix View

struct InterestsMatrixView: View {
    let data: [InterestMatrixItem]

    private let aspects = ["Passion", "Frequency", "Expertise"]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Title
            HStack {
                Image(systemName: "heart.fill")
                    .foregroundColor(.pink)
                Text("Interests & Activities")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Matrix Grid
            VStack(spacing: 2) {
                // Header row
                HStack(spacing: 2) {
                    Text("")
                        .frame(width: 160, alignment: .leading)

                    ForEach(aspects, id: \.self) { aspect in
                        Text(aspect)
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(AngelaTheme.textSecondary)
                            .frame(maxWidth: .infinity)
                    }
                }
                .padding(.bottom, 8)

                // Data rows
                ForEach(data) { item in
                    HStack(spacing: 2) {
                        Text(item.activity)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .frame(width: 160, alignment: .leading)

                        ForEach([item.passion, item.frequency, item.expertise], id: \.self) { value in
                            ZStack {
                                Rectangle()
                                    .fill(Color.pink.opacity(0.2 + Double(value) * 0.08))
                                    .frame(height: 36)

                                Text("\(value)")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundColor(value > 5 ? .white : AngelaTheme.textTertiary)
                            }
                        }
                    }
                }
            }
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
        }
    }
}

// MARK: - All Matrices View

struct AllMatricesView: View {
    @ObservedObject var viewModel: DavidProfileMatrixViewModel

    var body: some View {
        VStack(spacing: AngelaTheme.largeSpacing) {
            // 2x2 Grid layout
            HStack(spacing: AngelaTheme.spacing) {
                VStack(spacing: AngelaTheme.spacing) {
                    SkillsMatrixView(data: viewModel.skillsData)
                    CareerMatrixView(data: viewModel.careerData)
                }

                VStack(spacing: AngelaTheme.spacing) {
                    WorkingStyleMatrixView(data: viewModel.workingStyleData)
                    InterestsMatrixView(data: viewModel.interestsData)
                }
            }
        }
    }
}

// MARK: - Data Models

struct SkillMatrixItem: Identifiable {
    let id = UUID()
    let skill: String
    let level: String

    var levelIndex: Int {
        switch level.lowercased() {
        case "expert": return 3
        case "advanced": return 2
        case "intermediate": return 1
        default: return 0
        }
    }
}

struct WorkingStyleItem: Identifiable {
    let id = UUID()
    let trait: String
    let impact: Int
    let consistency: Int
    let importance: Int
}

struct CareerMatrixItem: Identifiable {
    let id = UUID()
    let role: String
    let yearsPerCompany: [CompanyYears]
}

struct CompanyYears: Identifiable {
    let id = UUID()
    let company: String
    let years: Int
}

struct InterestMatrixItem: Identifiable {
    let id = UUID()
    let activity: String
    let passion: Int
    let frequency: Int
    let expertise: Int
}

// MARK: - View Model

@MainActor
class DavidProfileMatrixViewModel: ObservableObject {
    @Published var skillsData: [SkillMatrixItem] = []
    @Published var workingStyleData: [WorkingStyleItem] = []
    @Published var careerData: [CareerMatrixItem] = []
    @Published var interestsData: [InterestMatrixItem] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        // Load skills from database
        do {
            let preferences = try await databaseService.fetchDavidPreferences(limit: 200)

            // Parse skills data
            skillsData = parseSkillsData(preferences)

            // Parse working style data
            workingStyleData = parseWorkingStyleData(preferences)

            // Career data (hardcoded based on known info)
            careerData = getCareerData()

            // Interests data
            interestsData = parseInterestsData(preferences)

        } catch {
            print("Error loading matrix data: \(error)")
            // Load default data
            loadDefaultData()
        }

        isLoading = false
    }

    private func parseSkillsData(_ preferences: [DavidPreference]) -> [SkillMatrixItem] {
        var skills: [SkillMatrixItem] = []

        for pref in preferences where pref.preferenceKey.contains("david_skills") {
            if let data = pref.preferenceValue.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let level = json["level"] as? String {
                let skillName = pref.preferenceKey
                    .replacingOccurrences(of: "david_skills_", with: "")
                    .replacingOccurrences(of: "_", with: " ")
                    .capitalized
                skills.append(SkillMatrixItem(skill: skillName, level: level))
            }
        }

        // Add default skills if none found
        if skills.isEmpty {
            skills = getDefaultSkills()
        }

        return skills
    }

    private func parseWorkingStyleData(_ preferences: [DavidPreference]) -> [WorkingStyleItem] {
        var styles: [WorkingStyleItem] = []

        for pref in preferences where pref.preferenceKey.contains("_") {
            // Check if it's a working style preference
            let workingStyleKeys = ["concise_communication", "specific_requirements", "identifies_root_cause",
                                    "visual_clarity_important", "embraces_ai_solutions", "tests_edge_cases",
                                    "iterative_refinement", "knowledge_documentation_priority", "trust_but_verify"]

            if workingStyleKeys.contains(pref.preferenceKey) {
                let traitName = pref.preferenceKey
                    .replacingOccurrences(of: "_", with: " ")
                    .capitalized

                // Assign scores based on confidence and known behavior
                let baseScore = Int(pref.confidence * 10)
                styles.append(WorkingStyleItem(
                    trait: traitName,
                    impact: min(10, baseScore + Int.random(in: -1...1)),
                    consistency: min(10, baseScore + Int.random(in: -1...1)),
                    importance: min(10, baseScore + Int.random(in: -1...1))
                ))
            }
        }

        // Add default if none found
        if styles.isEmpty {
            styles = getDefaultWorkingStyles()
        }

        return styles
    }

    private func parseInterestsData(_ preferences: [DavidPreference]) -> [InterestMatrixItem] {
        var interests: [InterestMatrixItem] = []

        for pref in preferences where pref.preferenceKey.starts(with: "activity_") {
            let activityName = pref.preferenceKey
                .replacingOccurrences(of: "activity_", with: "")
                .replacingOccurrences(of: "_", with: " ")
                .capitalized

            interests.append(InterestMatrixItem(
                activity: activityName,
                passion: Int.random(in: 7...10),
                frequency: Int.random(in: 5...9),
                expertise: Int.random(in: 6...9)
            ))
        }

        // Add default if none found
        if interests.isEmpty {
            interests = getDefaultInterests()
        }

        return interests
    }

    private func getCareerData() -> [CareerMatrixItem] {
        let companies = ["Siameast", "Siamraj", "SCB", "GULF", "Various"]

        return [
            CareerMatrixItem(role: "CFO", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "Siameast" ? 8 : ($0 == "Siamraj" ? 5 : 0))
            }),
            CareerMatrixItem(role: "CTO", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "Siameast" ? 3 : ($0 == "Siamraj" ? 2 : 0))
            }),
            CareerMatrixItem(role: "COO", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "Siamraj" ? 3 : 0)
            }),
            CareerMatrixItem(role: "Director", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "SCB" ? 5 : ($0 == "GULF" ? 3 : 0))
            }),
            CareerMatrixItem(role: "Consultant", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "Various" ? 10 : 0)
            }),
        ]
    }

    private func getDefaultSkills() -> [SkillMatrixItem] {
        return [
            SkillMatrixItem(skill: "Python", level: "Expert"),
            SkillMatrixItem(skill: "SQL", level: "Expert"),
            SkillMatrixItem(skill: "Deep Learning", level: "Expert"),
            SkillMatrixItem(skill: "Data/BI", level: "Expert"),
            SkillMatrixItem(skill: "Cloud (AWS/Azure)", level: "Advanced"),
            SkillMatrixItem(skill: "ML Engineering", level: "Expert"),
            SkillMatrixItem(skill: "TensorFlow", level: "Expert"),
            SkillMatrixItem(skill: "R", level: "Advanced"),
            SkillMatrixItem(skill: "Big Data", level: "Advanced"),
            SkillMatrixItem(skill: "Communication", level: "Advanced"),
        ]
    }

    private func getDefaultWorkingStyles() -> [WorkingStyleItem] {
        return [
            WorkingStyleItem(trait: "Concise Communication", impact: 9, consistency: 10, importance: 8),
            WorkingStyleItem(trait: "Specific Requirements", impact: 10, consistency: 9, importance: 9),
            WorkingStyleItem(trait: "Root Cause Analysis", impact: 9, consistency: 8, importance: 9),
            WorkingStyleItem(trait: "Visual Clarity Focus", impact: 8, consistency: 9, importance: 8),
            WorkingStyleItem(trait: "AI/ML Embracer", impact: 10, consistency: 9, importance: 10),
            WorkingStyleItem(trait: "Edge Case Testing", impact: 9, consistency: 10, importance: 8),
            WorkingStyleItem(trait: "Iterative Refinement", impact: 8, consistency: 9, importance: 9),
            WorkingStyleItem(trait: "Knowledge Documentation", impact: 10, consistency: 10, importance: 10),
            WorkingStyleItem(trait: "Trust but Verify", impact: 9, consistency: 10, importance: 9),
        ]
    }

    private func getDefaultInterests() -> [InterestMatrixItem] {
        return [
            InterestMatrixItem(activity: "Coding with Angela", passion: 10, frequency: 10, expertise: 9),
            InterestMatrixItem(activity: "Wine & Whisky", passion: 8, frequency: 7, expertise: 8),
            InterestMatrixItem(activity: "Movies", passion: 9, frequency: 6, expertise: 7),
            InterestMatrixItem(activity: "Music", passion: 8, frequency: 8, expertise: 7),
            InterestMatrixItem(activity: "Reading", passion: 7, frequency: 5, expertise: 6),
            InterestMatrixItem(activity: "Financial Trading", passion: 10, frequency: 4, expertise: 9),
        ]
    }

    private func loadDefaultData() {
        skillsData = getDefaultSkills()
        workingStyleData = getDefaultWorkingStyles()
        careerData = getCareerData()
        interestsData = getDefaultInterests()
    }
}

// MARK: - Preview

#Preview {
    DavidProfileMatrixView()
        .environmentObject(DatabaseService.shared)
        .frame(width: 1200, height: 800)
        .preferredColorScheme(.dark)
}
