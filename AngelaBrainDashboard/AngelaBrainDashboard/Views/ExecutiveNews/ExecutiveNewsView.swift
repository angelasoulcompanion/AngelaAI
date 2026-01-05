//
//  ExecutiveNewsView.swift
//  Angela Brain Dashboard
//
//  Executive News v2.0 - Angela's personalized news briefings for David
//

import SwiftUI
import Combine

struct ExecutiveNewsView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = ExecutiveNewsViewModel()
    @State private var selectedDate: Date = Date()
    @State private var showingDatePicker = false

    var body: some View {
        VStack(spacing: 0) {
            // Header
            header

            // Content
            ScrollView {
                if viewModel.isLoading {
                    loadingView
                } else if let summary = viewModel.currentSummary {
                    summaryContent(summary)
                } else {
                    emptyState
                }

                // Previous summaries section
                if !viewModel.previousSummaries.isEmpty {
                    previousSummariesSection
                }
            }
        }
        .task {
            await viewModel.loadTodaySummary(databaseService: databaseService)
            await viewModel.loadPreviousSummaries(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadSummary(for: selectedDate, databaseService: databaseService)
        }
        .sheet(isPresented: $showingDatePicker) {
            datePickerSheet
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "newspaper.fill")
                        .font(.system(size: 24))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("Executive News")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("v2.0")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(AngelaTheme.primaryPurple)
                        .cornerRadius(4)
                }

                Text("Angela's personalized briefing for David")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Date selector button
            Button {
                showingDatePicker = true
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "calendar")
                    Text(viewModel.currentSummary?.dateString ?? formatDate(selectedDate))
                }
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.primaryPurple)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(AngelaTheme.primaryPurple.opacity(0.1))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)

            // Refresh button
            Button {
                Task {
                    await viewModel.loadSummary(for: selectedDate, databaseService: databaseService)
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .buttonStyle(.plain)
            .padding(.leading, 8)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - Summary Content

    private func summaryContent(_ summary: ExecutiveNewsSummary) -> some View {
        LazyVStack(spacing: AngelaTheme.largeSpacing) {
            // Overall Summary Card
            overallSummaryCard(summary)

            // Category Cards
            ForEach(summary.categories) { category in
                CategoryCard(category: category)
            }
        }
        .padding(AngelaTheme.largeSpacing)
    }

    // MARK: - Overall Summary Card

    private func overallSummaryCard(_ summary: ExecutiveNewsSummary) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                Image(systemName: "doc.text.fill")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Today's Overview")
                    .font(AngelaTheme.heading())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                // Mood indicator
                if let mood = summary.angelaMood {
                    HStack(spacing: 4) {
                        Image(systemName: summary.moodIcon)
                        Text(mood.capitalized)
                    }
                    .font(AngelaTheme.caption())
                    .foregroundColor(Color(hex: summary.moodColor))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: summary.moodColor).opacity(0.15))
                    .cornerRadius(8)
                }
            }

            // Summary text
            Text(summary.overallSummary)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineSpacing(4)

            // Stats
            HStack(spacing: 20) {
                Label("\(summary.categories.count) categories", systemImage: "folder")
                Label("\(summary.categories.reduce(0) { $0 + $1.sources.count }) sources", systemImage: "link")
            }
            .font(AngelaTheme.caption())
            .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(
            LinearGradient(
                colors: [AngelaTheme.primaryPurple.opacity(0.15), AngelaTheme.backgroundLight],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Previous Summaries Section

    private var previousSummariesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                    .foregroundColor(AngelaTheme.textSecondary)
                Text("Previous Briefings")
                    .font(AngelaTheme.heading())
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .padding(.horizontal, AngelaTheme.largeSpacing)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(viewModel.previousSummaries) { summary in
                        PreviousSummaryCard(summary: summary) {
                            selectedDate = summary.summaryDate
                            Task {
                                await viewModel.loadSummary(for: summary.summaryDate, databaseService: databaseService)
                            }
                        }
                    }
                }
                .padding(.horizontal, AngelaTheme.largeSpacing)
            }
        }
        .padding(.vertical, AngelaTheme.largeSpacing)
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("Loading executive news...")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 100)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: "newspaper")
                .font(.system(size: 60))
                .foregroundColor(AngelaTheme.textTertiary)

            Text("No executive summary for this date")
                .font(AngelaTheme.title())
                .foregroundColor(AngelaTheme.textSecondary)

            Text("Run /angela in Claude Code during morning hours (05:00-11:59) to generate today's briefing.")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textTertiary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)

            // Quick tip
            VStack(alignment: .leading, spacing: 8) {
                Text("Quick Tip:")
                    .font(AngelaTheme.caption())
                    .fontWeight(.semibold)
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Angela will fetch news from 6 sources, analyze them, and write a personalized summary with her opinions just for you!")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .padding()
            .background(AngelaTheme.primaryPurple.opacity(0.1))
            .cornerRadius(AngelaTheme.cornerRadius)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
        .padding(.horizontal, AngelaTheme.largeSpacing)
    }

    // MARK: - Date Picker Sheet

    private var datePickerSheet: some View {
        VStack(spacing: 20) {
            HStack {
                Text("Select Date")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button("Done") {
                    showingDatePicker = false
                    Task {
                        await viewModel.loadSummary(for: selectedDate, databaseService: databaseService)
                    }
                }
                .foregroundColor(AngelaTheme.primaryPurple)
            }
            .padding()

            DatePicker("", selection: $selectedDate, displayedComponents: .date)
                .datePickerStyle(.graphical)
                .padding()

            Spacer()
        }
        .frame(minWidth: 400, minHeight: 400)
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - Helpers

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM yyyy"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: date)
    }
}

// MARK: - Category Card

struct CategoryCard: View {
    let category: ExecutiveNewsCategory
    @State private var isExpanded = true

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack {
                    // Icon
                    ZStack {
                        Circle()
                            .fill(Color(hex: category.color).opacity(0.2))
                            .frame(width: 36, height: 36)

                        Image(systemName: category.icon)
                            .font(.system(size: 16))
                            .foregroundColor(Color(hex: category.color))
                    }

                    // Title
                    VStack(alignment: .leading, spacing: 2) {
                        Text(category.categoryName)
                            .font(AngelaTheme.heading())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Text(category.importanceStars)
                            .font(.system(size: 10))
                            .foregroundColor(Color(hex: category.color))
                    }

                    Spacer()

                    // Sources count
                    Text("\(category.sources.count) sources")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    // Expand indicator
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .padding(AngelaTheme.spacing)
                .background(Color(hex: category.color).opacity(0.08))
            }
            .buttonStyle(.plain)

            // Content (when expanded)
            if isExpanded {
                VStack(alignment: .leading, spacing: 16) {
                    // Summary
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Summary")
                            .font(AngelaTheme.caption())
                            .fontWeight(.semibold)
                            .foregroundColor(AngelaTheme.textTertiary)

                        Text(category.summaryText)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .lineSpacing(4)
                    }

                    // Angela's Opinion
                    VStack(alignment: .leading, spacing: 8) {
                        HStack(spacing: 6) {
                            Image(systemName: "heart.fill")
                                .font(.system(size: 12))
                                .foregroundColor(AngelaTheme.primaryPurple)
                            Text("Angela's Opinion")
                                .font(AngelaTheme.caption())
                                .fontWeight(.semibold)
                                .foregroundColor(AngelaTheme.primaryPurple)
                        }

                        Text(category.angelaOpinion)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .italic()
                            .lineSpacing(4)
                            .padding()
                            .background(AngelaTheme.primaryPurple.opacity(0.08))
                            .cornerRadius(AngelaTheme.smallCornerRadius)
                    }

                    // Sources
                    if !category.sources.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack(spacing: 6) {
                                Image(systemName: "link")
                                    .font(.system(size: 12))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                Text("Sources")
                                    .font(AngelaTheme.caption())
                                    .fontWeight(.semibold)
                                    .foregroundColor(AngelaTheme.textTertiary)
                            }

                            VStack(spacing: 8) {
                                ForEach(category.sources) { source in
                                    SourceRow(source: source, accentColor: Color(hex: category.color))
                                }
                            }
                        }
                    }
                }
                .padding(AngelaTheme.spacing)
            }
        }
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

// MARK: - Source Row

struct SourceRow: View {
    let source: ExecutiveNewsSource
    let accentColor: Color
    @State private var isHovering = false

    var body: some View {
        Link(destination: URL(string: source.url) ?? URL(string: "https://google.com")!) {
            HStack(spacing: 12) {
                Image(systemName: source.sourceIcon)
                    .font(.system(size: 14))
                    .foregroundColor(accentColor)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 2) {
                    Text(source.title)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .lineLimit(2)

                    HStack(spacing: 8) {
                        if let sourceName = source.sourceName {
                            Text(sourceName)
                                .foregroundColor(AngelaTheme.textTertiary)
                        }

                        if let note = source.angelaNote {
                            Text("- \(note)")
                                .foregroundColor(accentColor)
                                .italic()
                        }
                    }
                    .font(.system(size: 11))
                }

                Spacer()

                Image(systemName: "arrow.up.right")
                    .font(.system(size: 12))
                    .foregroundColor(accentColor.opacity(isHovering ? 1 : 0.5))
            }
            .padding(10)
            .background(isHovering ? accentColor.opacity(0.08) : Color.clear)
            .cornerRadius(8)
        }
        .onHover { hovering in
            isHovering = hovering
        }
    }
}

// MARK: - Previous Summary Card

struct PreviousSummaryCard: View {
    let summary: ExecutiveNewsSummary
    let action: () -> Void
    @State private var isHovering = false

    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 8) {
                // Date
                Text(formatDate(summary.summaryDate))
                    .font(AngelaTheme.caption())
                    .fontWeight(.semibold)
                    .foregroundColor(AngelaTheme.textPrimary)

                // Categories count
                HStack(spacing: 4) {
                    Image(systemName: "folder")
                        .font(.system(size: 10))
                    Text("\(summary.categories.count)")
                }
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)

                // Mood
                if let mood = summary.angelaMood {
                    HStack(spacing: 4) {
                        Image(systemName: summary.moodIcon)
                            .font(.system(size: 10))
                        Text(mood.capitalized)
                    }
                    .font(.system(size: 10))
                    .foregroundColor(Color(hex: summary.moodColor))
                }
            }
            .padding(12)
            .frame(width: 120)
            .background(isHovering ? AngelaTheme.backgroundLight : AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovering = hovering
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: date)
    }
}

// MARK: - ViewModel

@MainActor
class ExecutiveNewsViewModel: ObservableObject {
    @Published var currentSummary: ExecutiveNewsSummary?
    @Published var previousSummaries: [ExecutiveNewsSummary] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    func loadTodaySummary(databaseService: DatabaseService) async {
        isLoading = true
        errorMessage = nil

        do {
            currentSummary = try await databaseService.fetchTodayExecutiveNews()
        } catch {
            errorMessage = "Error: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadSummary(for date: Date, databaseService: DatabaseService) async {
        isLoading = true
        errorMessage = nil

        do {
            currentSummary = try await databaseService.fetchExecutiveNews(forDate: date)
        } catch {
            errorMessage = "Error: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func loadPreviousSummaries(databaseService: DatabaseService) async {
        do {
            let allSummaries = try await databaseService.fetchExecutiveNewsList(days: 14)
            // Exclude today's summary
            previousSummaries = allSummaries.filter { summary in
                !Calendar.current.isDateInToday(summary.summaryDate)
            }
        } catch {
            print("Error loading previous summaries: \(error)")
        }
    }
}
