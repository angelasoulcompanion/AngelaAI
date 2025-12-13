//
//  NewsHistoryView.swift
//  Angela Brain Dashboard
//
//  💜 News History View - ดูข่าวที่ Angela ค้นหาย้อนหลัง 💜
//

import SwiftUI
import Combine

struct NewsHistoryView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = NewsHistoryViewModel()
    @State private var selectedTab: NewsViewTab = .byTopic
    @State private var selectedSearch: NewsSearch?

    var body: some View {
        VStack(spacing: 0) {
            // Header with stats and tab picker
            header

            // Content based on selected tab
            ScrollView {
                switch selectedTab {
                case .byTopic:
                    byTopicContent
                case .timeline:
                    timelineContent
                }
            }
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
        .sheet(item: $selectedSearch) { search in
            SearchArticlesSheet(search: search, databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: AngelaTheme.spacing) {
            // Title and stats
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("News History")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    HStack(spacing: 16) {
                        Label("\(viewModel.totalSearches) searches", systemImage: "magnifyingglass")
                        Label("\(viewModel.totalArticles) articles", systemImage: "newspaper")
                    }
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

            // Tab Picker
            Picker("View Mode", selection: $selectedTab) {
                ForEach(NewsViewTab.allCases, id: \.self) { tab in
                    Label(tab.title, systemImage: tab.icon)
                        .tag(tab)
                }
            }
            .pickerStyle(.segmented)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - By Topic View

    private var byTopicContent: some View {
        LazyVStack(spacing: AngelaTheme.spacing) {
            if viewModel.searches.isEmpty {
                emptyState(message: "No news searches yet", icon: "newspaper")
            } else {
                ForEach(viewModel.searches) { search in
                    SearchCard(search: search)
                        .onTapGesture {
                            selectedSearch = search
                        }
                }
            }
        }
        .padding(AngelaTheme.largeSpacing)
    }

    // MARK: - Timeline View

    private var timelineContent: some View {
        LazyVStack(spacing: AngelaTheme.spacing) {
            if viewModel.allArticles.isEmpty {
                emptyState(message: "No articles saved yet", icon: "doc.text")
            } else {
                ForEach(viewModel.allArticles) { article in
                    ArticleCard(article: article)
                }
            }
        }
        .padding(AngelaTheme.largeSpacing)
    }

    // MARK: - Empty State

    private func emptyState(message: String, icon: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(AngelaTheme.textTertiary)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)

            Text("Ask Angela for news to see it here!")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }
}

// MARK: - Tab Enum

enum NewsViewTab: String, CaseIterable {
    case byTopic = "By Topic"
    case timeline = "Timeline"

    var title: String { rawValue }

    var icon: String {
        switch self {
        case .byTopic: return "folder"
        case .timeline: return "clock"
        }
    }
}

// MARK: - Search Card Component

struct SearchCard: View {
    let search: NewsSearch

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                // Type icon
                ZStack {
                    Circle()
                        .fill(Color(hex: search.typeColor).opacity(0.2))
                        .frame(width: 40, height: 40)

                    Image(systemName: search.typeIcon)
                        .font(.system(size: 16))
                        .foregroundColor(Color(hex: search.typeColor))
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(search.searchQuery)
                        .font(AngelaTheme.body())
                        .fontWeight(.semibold)
                        .foregroundColor(AngelaTheme.textPrimary)
                        .lineLimit(1)

                    HStack(spacing: 8) {
                        Text(search.searchType.capitalized)
                            .font(AngelaTheme.caption())
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color(hex: search.typeColor).opacity(0.2))
                            .foregroundColor(Color(hex: search.typeColor))
                            .cornerRadius(4)

                        Text(search.language.uppercased())
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text("\(search.articlesCount)")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("articles")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            // Searched at
            HStack {
                Image(systemName: "clock")
                    .font(.system(size: 12))
                Text(search.searchedAt, style: .relative)
                    .font(AngelaTheme.caption())

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
            }
            .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

// MARK: - Article Card Component

struct ArticleCard: View {
    let article: NewsArticle

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Title
            Text(article.title)
                .font(AngelaTheme.body())
                .fontWeight(.semibold)
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(2)

            // Summary
            if let summary = article.summary, !summary.isEmpty {
                Text(summary)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(3)
            }

            // Metadata row
            HStack(spacing: 12) {
                // Source
                if let source = article.source {
                    HStack(spacing: 4) {
                        Image(systemName: article.sourceIcon)
                            .font(.system(size: 10))
                        Text(source)
                            .lineLimit(1)
                    }
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                }

                // Category
                if let category = article.category {
                    Text(category.capitalized)
                        .font(AngelaTheme.caption())
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color(hex: article.categoryColor).opacity(0.2))
                        .foregroundColor(Color(hex: article.categoryColor))
                        .cornerRadius(4)
                }

                Spacer()

                // Time
                if let publishedAt = article.publishedAt {
                    Text(publishedAt, style: .relative)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                } else {
                    Text(article.savedAt, style: .relative)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }

            // Open link button
            Link(destination: URL(string: article.url) ?? URL(string: "https://google.com")!) {
                HStack {
                    Image(systemName: "link")
                    Text("Read Article")
                    Spacer()
                    Image(systemName: "arrow.up.right")
                }
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.primaryPurple)
                .padding(10)
                .background(AngelaTheme.primaryPurple.opacity(0.1))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.cornerRadius)
    }
}

// MARK: - Search Articles Sheet

struct SearchArticlesSheet: View {
    let search: NewsSearch
    let databaseService: DatabaseService
    @State private var articles: [NewsArticle] = []
    @State private var isLoading = true
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(search.searchQuery)
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("\(articles.count) articles from \(search.searchedAt, style: .date)")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()

                Button {
                    dismiss()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .buttonStyle(.plain)
            }
            .padding(AngelaTheme.largeSpacing)
            .background(AngelaTheme.backgroundDark)

            // Articles list
            if isLoading {
                Spacer()
                ProgressView()
                    .scaleEffect(1.5)
                Spacer()
            } else {
                ScrollView {
                    LazyVStack(spacing: AngelaTheme.spacing) {
                        ForEach(articles) { article in
                            ArticleCard(article: article)
                        }
                    }
                    .padding(AngelaTheme.largeSpacing)
                }
            }
        }
        .frame(minWidth: 500, minHeight: 400)
        .background(AngelaTheme.backgroundDark)
        .task {
            await loadArticles()
        }
    }

    private func loadArticles() async {
        do {
            articles = try await databaseService.fetchNewsArticles(searchId: search.id)
        } catch {
            print("Error loading articles: \(error)")
        }
        isLoading = false
    }
}

// MARK: - ViewModel

@MainActor
class NewsHistoryViewModel: ObservableObject {
    @Published var searches: [NewsSearch] = []
    @Published var allArticles: [NewsArticle] = []
    @Published var totalSearches: Int = 0
    @Published var totalArticles: Int = 0
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            // Load searches and articles in parallel
            async let searchesTask = databaseService.fetchNewsSearches(limit: 50)
            async let articlesTask = databaseService.fetchAllNewsArticles(limit: 100)
            async let statsTask = databaseService.fetchNewsStatistics()

            searches = try await searchesTask
            allArticles = try await articlesTask

            let stats = try await statsTask
            totalSearches = stats.totalSearches
            totalArticles = stats.totalArticles
        } catch {
            print("Error loading news history: \(error)")
        }

        isLoading = false
    }
}
