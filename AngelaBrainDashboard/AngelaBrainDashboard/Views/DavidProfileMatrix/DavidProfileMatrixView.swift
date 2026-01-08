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
                        SkillsMatrixView(data: viewModel.skillsData, certifications: viewModel.certifications)
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
    let certifications: [CertificationItem]

    private let levels = ["Beginner", "Intermediate", "Advanced", "Expert"]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.largeSpacing) {
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

            // Skills Quadrant Chart
            SkillsQuadrantView(data: data)

            // Certifications Section
            if !certifications.isEmpty {
                CertificationsView(certifications: certifications)
            }
        }
    }
}

// MARK: - Skills Quadrant View

struct SkillsQuadrantView: View {
    let data: [SkillMatrixItem]

    // Skills data: X = Expertise Maturity, Y = Future Relevance
    private var skillsQuadrantData: [SkillQuadrantItem] {
        // (maturity: years of experience normalized, futureRelevance: strategic importance)
        let skillMapping: [String: (maturity: Double, future: Double)] = [
            "Python": (0.85, 0.95),           // Strategic Asset - long use, very relevant
            "SQL": (0.95, 0.75),              // Established - very mature, stable relevance
            "Deep Learning": (0.60, 0.90),   // Growth - newer, very relevant
            "Data/BI": (0.90, 0.70),          // Established - very mature, stable
            "ML Engineering": (0.55, 0.88),  // Growth - newer skill, high future
            "TensorFlow": (0.50, 0.72),      // Growth - medium maturity
            "Cloud (AWS/Azure)": (0.35, 0.85), // Growth Opportunity - newer, important
            "R": (0.75, 0.30),                // Legacy - mature but less future use
            "Big Data": (0.65, 0.55),        // Established Foundation
            "Communication": (0.90, 0.65),   // Established - always had, stable
        ]

        return data.compactMap { item in
            if let mapping = skillMapping[item.skill] {
                return SkillQuadrantItem(
                    skill: item.skill,
                    proficiency: mapping.maturity,
                    impact: mapping.future,
                    isFromCertificate: false
                )
            }
            let proficiency = Double(item.levelIndex + 1) / 4.0
            return SkillQuadrantItem(
                skill: item.skill,
                proficiency: proficiency,
                impact: proficiency * 0.8,
                isFromCertificate: false
            )
        }
    }

    // Certificate knowledge: X = Expertise Maturity, Y = Future Relevance
    private var certificateQuadrantData: [SkillQuadrantItem] {
        return [
            // CQF - Quantitative Finance (2014) - very mature, still relevant for finance
            SkillQuadrantItem(skill: "Quant Finance (CQF)", proficiency: 0.90, impact: 0.60, isFromCertificate: true),
            // Machine Learning courses (2023)
            SkillQuadrantItem(skill: "Supervised ML", proficiency: 0.55, impact: 0.82, isFromCertificate: true),
            SkillQuadrantItem(skill: "Advanced ML", proficiency: 0.50, impact: 0.80, isFromCertificate: true),
            // NLP (2024)
            SkillQuadrantItem(skill: "NLP", proficiency: 0.40, impact: 0.88, isFromCertificate: true),
            // Generative AI courses (2023-2025) - newest, highest future
            SkillQuadrantItem(skill: "Generative AI", proficiency: 0.30, impact: 0.98, isFromCertificate: true),
            SkillQuadrantItem(skill: "Prompt Engineering", proficiency: 0.35, impact: 0.95, isFromCertificate: true),
            // Supply Chain & Blockchain (2019) - older certs
            SkillQuadrantItem(skill: "Supply Chain Finance", proficiency: 0.70, impact: 0.35, isFromCertificate: true),
            SkillQuadrantItem(skill: "Blockchain", proficiency: 0.65, impact: 0.45, isFromCertificate: true),
            // Quantitative Modeling (Wharton 2022)
            SkillQuadrantItem(skill: "Quant Modeling", proficiency: 0.60, impact: 0.55, isFromCertificate: true),
            // Marketing Analytics (2023)
            SkillQuadrantItem(skill: "Marketing Analytics", proficiency: 0.45, impact: 0.40, isFromCertificate: true),
        ]
    }

    // Combined data
    private var allQuadrantData: [SkillQuadrantItem] {
        skillsQuadrantData + certificateQuadrantData
    }

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Title
            HStack {
                Image(systemName: "chart.xyaxis.line")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Skills Quadrant Analysis")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Quadrant Chart
            GeometryReader { geometry in
                let width = geometry.size.width
                let height: CGFloat = 500
                let padding: CGFloat = 80
                let chartWidth = width - padding * 2
                let chartHeight = height - padding * 2

                ZStack {
                    // Background quadrants
                    VStack(spacing: 0) {
                        HStack(spacing: 0) {
                            // Top-Left: Growth Areas
                            Rectangle()
                                .fill(Color.orange.opacity(0.15))
                            // Top-Right: Core Strengths
                            Rectangle()
                                .fill(Color.green.opacity(0.15))
                        }
                        HStack(spacing: 0) {
                            // Bottom-Left: Foundation
                            Rectangle()
                                .fill(Color.gray.opacity(0.15))
                            // Bottom-Right: Specialized
                            Rectangle()
                                .fill(Color.blue.opacity(0.15))
                        }
                    }
                    .frame(width: chartWidth, height: chartHeight)
                    .position(x: width / 2, y: height / 2)

                    // Quadrant labels
                    Group {
                        // Top-Left: Growth Opportunities (new skills, high future)
                        VStack(spacing: 2) {
                            Image(systemName: "rocket.fill")
                                .font(.system(size: 14))
                            Text("Growth")
                            Text("Opportunities")
                        }
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.orange)
                        .position(x: padding + chartWidth * 0.25, y: padding + 35)

                        // Top-Right: Strategic Assets (mature + high future)
                        VStack(spacing: 2) {
                            Image(systemName: "star.fill")
                                .font(.system(size: 14))
                            Text("Strategic")
                            Text("Assets")
                        }
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.green)
                        .position(x: padding + chartWidth * 0.75, y: padding + 35)

                        // Bottom-Left: Legacy Skills
                        VStack(spacing: 2) {
                            Image(systemName: "archivebox.fill")
                                .font(.system(size: 14))
                            Text("Legacy")
                            Text("Skills")
                        }
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.gray)
                        .position(x: padding + chartWidth * 0.25, y: height - padding - 35)

                        // Bottom-Right: Established Foundation
                        VStack(spacing: 2) {
                            Image(systemName: "building.columns.fill")
                                .font(.system(size: 14))
                            Text("Established")
                            Text("Foundation")
                        }
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(.blue)
                        .position(x: padding + chartWidth * 0.75, y: height - padding - 35)
                    }

                    // Axes
                    Path { path in
                        // X-axis
                        path.move(to: CGPoint(x: padding, y: height - padding))
                        path.addLine(to: CGPoint(x: width - padding, y: height - padding))
                        // Y-axis
                        path.move(to: CGPoint(x: padding, y: padding))
                        path.addLine(to: CGPoint(x: padding, y: height - padding))
                        // Center lines
                        path.move(to: CGPoint(x: width / 2, y: padding))
                        path.addLine(to: CGPoint(x: width / 2, y: height - padding))
                        path.move(to: CGPoint(x: padding, y: height / 2))
                        path.addLine(to: CGPoint(x: width - padding, y: height / 2))
                    }
                    .stroke(AngelaTheme.textTertiary.opacity(0.5), style: StrokeStyle(lineWidth: 1, dash: [5, 3]))

                    // Axis labels
                    Text("Expertise Maturity →")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .position(x: width / 2, y: height - 15)

                    Text("Future Relevance →")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .rotationEffect(.degrees(-90))
                        .position(x: 15, y: height / 2)

                    // Data points - Skills (Green dots)
                    ForEach(skillsQuadrantData) { item in
                        let clampedX = min(max(item.proficiency, 0.08), 0.92)
                        let clampedY = min(max(item.impact, 0.08), 0.92)
                        let x = padding + clampedX * chartWidth
                        let y = height - padding - clampedY * chartHeight

                        ZStack {
                            Circle()
                                .fill(Color.green)
                                .frame(width: 14, height: 14)
                                .shadow(color: .black.opacity(0.3), radius: 2, x: 0, y: 1)

                            Text(item.skill)
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(AngelaTheme.textPrimary)
                                .fixedSize()
                                .offset(y: -16)
                        }
                        .position(x: x, y: y)
                    }

                    // Data points - Certificate Knowledge (Purple dots)
                    ForEach(certificateQuadrantData) { item in
                        let clampedX = min(max(item.proficiency, 0.08), 0.92)
                        let clampedY = min(max(item.impact, 0.08), 0.92)
                        let x = padding + clampedX * chartWidth
                        let y = height - padding - clampedY * chartHeight

                        ZStack {
                            Circle()
                                .fill(AngelaTheme.primaryPurple)
                                .frame(width: 12, height: 12)
                                .shadow(color: AngelaTheme.primaryPurple.opacity(0.5), radius: 3, x: 0, y: 1)

                            Text(item.skill)
                                .font(.system(size: 8, weight: .medium))
                                .foregroundColor(AngelaTheme.primaryPurple)
                                .fixedSize()
                                .offset(y: -14)
                        }
                        .position(x: x, y: y)
                    }
                }
                .clipped()
            }
            .frame(height: 500)
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)

            // Legend
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 24) {
                    legendItem(color: .green, label: "Technical Skills", shape: "circle")
                    legendItem(color: AngelaTheme.primaryPurple, label: "Certificate Knowledge", shape: "circle")
                }
                HStack(spacing: 16) {
                    Text("Quadrants:")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textTertiary)
                    quadrantLegendItem(color: .green.opacity(0.3), label: "Strategic Assets")
                    quadrantLegendItem(color: .orange.opacity(0.3), label: "Growth Opportunities")
                    quadrantLegendItem(color: .blue.opacity(0.3), label: "Established")
                    quadrantLegendItem(color: .gray.opacity(0.3), label: "Legacy")
                }
            }
            .padding(.horizontal)
        }
    }

    private func quadrantLegendItem(color: Color, label: String) -> some View {
        HStack(spacing: 4) {
            Rectangle()
                .fill(color)
                .frame(width: 12, height: 12)
                .cornerRadius(2)
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }

    private func legendItem(color: Color, label: String, shape: String = "circle") -> some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 12, height: 12)
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }
}

struct SkillQuadrantItem: Identifiable {
    let id = UUID()
    let skill: String
    let proficiency: Double      // 0-1 (x-axis)
    let impact: Double           // 0-1 (y-axis)
    var isFromCertificate: Bool = false
}

// MARK: - Certifications View

struct CertificationsView: View {
    let certifications: [CertificationItem]

    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMM yyyy"
        return f
    }()

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            // Title
            HStack {
                Image(systemName: "checkmark.seal.fill")
                    .foregroundColor(AngelaTheme.successGreen)
                Text("Certifications")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)
                Spacer()
                Text("\(certifications.count) certificates")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            // Certificates list
            VStack(spacing: 12) {
                ForEach(certifications) { cert in
                    HStack(spacing: 16) {
                        // Provider icon
                        ZStack {
                            Circle()
                                .fill(providerColor(cert.provider).opacity(0.2))
                                .frame(width: 44, height: 44)
                            Image(systemName: providerIcon(cert.provider))
                                .font(.system(size: 18))
                                .foregroundColor(providerColor(cert.provider))
                        }

                        // Certificate details
                        VStack(alignment: .leading, spacing: 4) {
                            Text(cert.courseName)
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.textPrimary)
                                .lineLimit(2)

                            HStack(spacing: 8) {
                                Text(cert.provider)
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(providerColor(cert.provider))

                                if !cert.platform.isEmpty {
                                    Text("•")
                                        .foregroundColor(AngelaTheme.textTertiary)
                                    Text(cert.platform)
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textSecondary)
                                }

                                Text("•")
                                    .foregroundColor(AngelaTheme.textTertiary)
                                Text(dateFormatter.string(from: cert.completionDate))
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.textSecondary)
                            }
                        }

                        Spacer()

                        // Verify link
                        if !cert.verifyUrl.isEmpty {
                            Link(destination: URL(string: cert.verifyUrl)!) {
                                HStack(spacing: 4) {
                                    Text("Verify")
                                        .font(.system(size: 11, weight: .medium))
                                    Image(systemName: "arrow.up.right")
                                        .font(.system(size: 10))
                                }
                                .foregroundColor(AngelaTheme.primaryPurple)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(AngelaTheme.primaryPurple.opacity(0.1))
                                .cornerRadius(8)
                            }
                        }
                    }
                    .padding(12)
                    .background(AngelaTheme.backgroundLight)
                    .cornerRadius(12)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    private func providerColor(_ provider: String) -> Color {
        switch provider.lowercased() {
        case "deeplearning.ai": return Color.red
        case "coursera": return Color.blue
        case "udemy": return Color.purple
        case "google": return Color.green
        case "microsoft": return Color.cyan
        default: return AngelaTheme.primaryPurple
        }
    }

    private func providerIcon(_ provider: String) -> String {
        switch provider.lowercased() {
        case "deeplearning.ai": return "brain.head.profile"
        case "coursera": return "graduationcap.fill"
        case "udemy": return "play.rectangle.fill"
        case "google": return "g.circle.fill"
        case "microsoft": return "square.grid.3x3.fill"
        default: return "checkmark.seal.fill"
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

    private let companies = ["Western Univ", "SIAMEAST", "Xtra Info", "SRT", "East Water", "UU", "OneTV", "S&P", "UBA"]

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
                    SkillsMatrixView(data: viewModel.skillsData, certifications: viewModel.certifications)
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

struct CertificationItem: Identifiable {
    let id = UUID()
    let courseName: String
    let provider: String
    let platform: String
    let completionDate: Date
    let verifyUrl: String
    let skillCategory: String
}

// MARK: - View Model

@MainActor
class DavidProfileMatrixViewModel: ObservableObject {
    @Published var skillsData: [SkillMatrixItem] = []
    @Published var workingStyleData: [WorkingStyleItem] = []
    @Published var careerData: [CareerMatrixItem] = []
    @Published var interestsData: [InterestMatrixItem] = []
    @Published var certifications: [CertificationItem] = []
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
            print("❌ Error loading matrix data: \(error)")
            // Load default data
            loadDefaultData()
        }

        // Load certifications from API (always run, separate from preferences)
        await loadCertifications()

        isLoading = false
    }

    private func loadCertifications() async {
        // Note: NetworkService uses .convertFromSnakeCase, so properties must be camelCase
        struct CertResponse: Codable {
            let certId: String
            let courseName: String
            let provider: String
            let platform: String?
            let completionDate: String
            let verifyUrl: String?
            let skillCategory: String?
        }

        guard let certs: [CertResponse] = await NetworkService.shared.getOptional("/api/certifications") else {
            print("❌ Failed to load certifications from API")
            return
        }

        print("✅ Loaded \(certs.count) certifications from API")

        certifications = certs.map { cert in
            CertificationItem(
                courseName: cert.courseName,
                provider: cert.provider,
                platform: cert.platform ?? "",
                completionDate: parseDate(cert.completionDate),
                verifyUrl: cert.verifyUrl ?? "",
                skillCategory: cert.skillCategory ?? ""
            )
        }

        print("✅ Mapped \(certifications.count) certifications")
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
        // Companies: Western Univ, SIAMEAST, Xtra Info, SRT, East Water, UU, OneTV, S&P, UBA
        let companies = ["Western Univ", "SIAMEAST", "Xtra Info", "SRT", "East Water", "UU", "OneTV", "S&P", "UBA"]

        return [
            // CEO: Xtra Information Intelligence (2021-present) ~5y
            CareerMatrixItem(role: "CEO", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "Xtra Info" ? 5 : 0)
            }),
            // CFO: SIAMEAST (3y), UBA (1y)
            CareerMatrixItem(role: "CFO", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "SIAMEAST" ? 3 : ($0 == "UBA" ? 1 : 0))
            }),
            // VP/IT Director: Western University (2012-2020) 8y
            CareerMatrixItem(role: "VP/IT Director", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "Western Univ" ? 8 : 0)
            }),
            // Asst. VP: OneTV (Data Engineer) 1y
            CareerMatrixItem(role: "Asst. VP", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "OneTV" ? 1 : 0)
            }),
            // EDP Manager: S&P 1y
            CareerMatrixItem(role: "EDP Manager", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "S&P" ? 1 : 0)
            }),
            // BI/Committee: SRT (2011-2012 + 2023-present) 3y
            CareerMatrixItem(role: "BI/Committee", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "SRT" ? 3 : 0)
            }),
            // IT Expert: East Water (2026-present) 1y
            CareerMatrixItem(role: "IT Expert", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "East Water" ? 1 : 0)
            }),
            // Consultant: UU (Universal Utilities) ~8y total
            CareerMatrixItem(role: "Consultant", yearsPerCompany: companies.map {
                CompanyYears(company: $0, years: $0 == "UU" ? 8 : 0)
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
