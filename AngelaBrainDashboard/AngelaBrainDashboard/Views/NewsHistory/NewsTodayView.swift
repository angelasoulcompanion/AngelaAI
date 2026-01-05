//
//  NewsTodayView.swift
//  Angela Brain Dashboard
//
//  💜 News Today View - ข่าววันนี้สำหรับที่รัก David 💜
//  Tab-based view grouped by MCP search categories
//

import SwiftUI
import Combine

struct NewsTodayView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = NewsTodayViewModel()
    @State private var selectedSearchId: UUID? = nil

    var body: some View {
        VStack(spacing: 0) {
            // Header
            header

            // Tab Bar
            if !viewModel.todaySearches.isEmpty {
                tabBar
            }

            // Content
            ScrollView {
                if viewModel.isLoading {
                    loadingView
                } else if viewModel.todaySearches.isEmpty {
                    emptyState
                } else {
                    articlesContent
                }
            }
        }
        .task {
            await viewModel.loadTodayNews(databaseService: databaseService)
            // Select first tab by default
            if let first = viewModel.todaySearches.first {
                selectedSearchId = first.id
            }
        }
        .refreshable {
            await viewModel.loadTodayNews(databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "sun.max.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.orange)

                    Text("News Today")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                HStack(spacing: 16) {
                    Label(viewModel.todayDateString, systemImage: "calendar")
                    Label("\(viewModel.totalArticles) articles", systemImage: "newspaper")
                    Label("\(viewModel.todaySearches.count) categories", systemImage: "folder")
                }
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Refresh button
            Button {
                Task {
                    await viewModel.loadTodayNews(databaseService: databaseService)
                    if let first = viewModel.todaySearches.first {
                        selectedSearchId = first.id
                    }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                    Text("Refresh")
                }
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.primaryPurple)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(AngelaTheme.primaryPurple.opacity(0.1))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - Tab Bar

    private var tabBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(viewModel.todaySearches) { search in
                    NewsTabButton(
                        search: search,
                        count: viewModel.articles[search.id]?.count ?? 0,
                        isSelected: selectedSearchId == search.id
                    ) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selectedSearchId = search.id
                        }
                    }
                }
            }
            .padding(.horizontal, AngelaTheme.largeSpacing)
            .padding(.vertical, AngelaTheme.spacing)
        }
        .background(AngelaTheme.backgroundLight.opacity(0.5))
    }

    // MARK: - Articles Content

    private var articlesContent: some View {
        LazyVStack(spacing: AngelaTheme.spacing) {
            if let searchId = selectedSearchId,
               let articles = viewModel.articles[searchId],
               let search = viewModel.todaySearches.first(where: { $0.id == searchId }) {
                ForEach(articles) { article in
                    CompactArticleCard(article: article, accentColor: Color(hex: search.typeColor))
                }
            }
        }
        .padding(AngelaTheme.largeSpacing)
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("Loading today's news...")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 100)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: viewModel.errorMessage != nil ? "exclamationmark.triangle" : "newspaper")
                .font(.system(size: 60))
                .foregroundColor(viewModel.errorMessage != nil ? .red : AngelaTheme.textTertiary)

            Text(viewModel.errorMessage != nil ? "Error Loading News" : "No news for today yet")
                .font(AngelaTheme.title())
                .foregroundColor(viewModel.errorMessage != nil ? .red : AngelaTheme.textSecondary)

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(AngelaTheme.caption())
                    .foregroundColor(.red)
                    .padding()
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(8)
            } else {
                Text("Ask Angela for morning news to see articles here!")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .multilineTextAlignment(.center)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Quick Tip:")
                    .font(AngelaTheme.caption())
                    .fontWeight(.semibold)
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Run /angela in Claude Code to fetch morning news automatically!")
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
}

// MARK: - News Tab Button

struct NewsTabButton: View {
    let search: NewsSearch
    let count: Int
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                // Icon
                Image(systemName: search.typeIcon)
                    .font(.system(size: 14))

                // Title
                Text(search.displayName)
                    .font(.system(size: 13, weight: .medium))
                    .lineLimit(1)

                // Count badge
                Text("\(count)")
                    .font(.system(size: 11, weight: .bold))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(isSelected ? Color.white.opacity(0.3) : Color(hex: search.typeColor).opacity(0.2))
                    .cornerRadius(8)
            }
            .foregroundColor(isSelected ? .white : Color(hex: search.typeColor))
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(isSelected ? Color(hex: search.typeColor) : Color(hex: search.typeColor).opacity(0.1))
            .cornerRadius(20)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Compact Article Card

struct CompactArticleCard: View {
    let article: NewsArticle
    let accentColor: Color
    @State private var isHovering = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header row
            HStack {
                // Source
                if let source = article.source {
                    HStack(spacing: 4) {
                        Image(systemName: article.sourceIcon)
                            .font(.system(size: 10))
                        Text(source)
                    }
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textTertiary)
                }

                Spacer()

                // Time
                if let publishedAt = article.publishedAt {
                    Text(publishedAt, style: .time)
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            // Title
            Text(article.title)
                .font(AngelaTheme.body())
                .fontWeight(.medium)
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(2)

            // Summary (if available and different from title)
            if let summary = article.summary,
               !summary.isEmpty,
               summary != article.title {
                Text(summary)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(2)
            }

            // Read link
            Link(destination: URL(string: article.url) ?? URL(string: "https://google.com")!) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.right.square")
                    Text("Read Full Article")
                    Spacer()
                    Image(systemName: "chevron.right")
                }
                .font(.system(size: 12))
                .foregroundColor(accentColor)
                .padding(10)
                .background(accentColor.opacity(isHovering ? 0.12 : 0.06))
                .cornerRadius(8)
            }
            .onHover { hovering in
                isHovering = hovering
            }
        }
        .padding(12)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - ViewModel

@MainActor
class NewsTodayViewModel: ObservableObject {
    @Published var todaySearches: [NewsSearch] = []
    @Published var articles: [UUID: [NewsArticle]] = [:]
    @Published var isLoading = false
    @Published var errorMessage: String? = nil

    var todayDateString: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE, d MMMM yyyy"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: Date())
    }

    var totalArticles: Int {
        articles.values.reduce(0) { $0 + $1.count }
    }

    func loadTodayNews(databaseService: DatabaseService) async {
        isLoading = true
        errorMessage = nil

        do {
            // Fetch today's searches
            todaySearches = try await databaseService.fetchTodayNewsSearches()

            // Fetch articles for each search
            var newArticles: [UUID: [NewsArticle]] = [:]
            for search in todaySearches {
                let searchArticles = try await databaseService.fetchNewsArticles(searchId: search.id)
                newArticles[search.id] = searchArticles
            }
            articles = newArticles

        } catch {
            errorMessage = "Error: \(error.localizedDescription)"
        }

        isLoading = false
    }
}

// MARK: - NewsSearch Extension for Display

extension NewsSearch {
    /// Friendly display name for the search (without emoji for tab)
    var displayName: String {
        switch searchType.lowercased() {
        case "tech":
            return "Tech News"
        case "thai":
            return "Thai News"
        case "trending":
            if searchQuery.contains("business") {
                return "Thai Business"
            }
            return "Trending"
        case "topic":
            if searchQuery.lowercased().contains("ai") || searchQuery.lowercased().contains("llm") {
                return "AI & LLM"
            } else if searchQuery.lowercased().contains("economy") || searchQuery.lowercased().contains("stock") {
                return "World Economy"
            } else if searchQuery.contains("เศรษฐกิจ") || searchQuery.contains("หุ้น") {
                return "Thai Finance"
            }
            return searchQuery
        default:
            return searchQuery
        }
    }
}
