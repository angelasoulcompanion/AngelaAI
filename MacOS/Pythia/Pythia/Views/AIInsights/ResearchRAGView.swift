//
//  ResearchRAGView.swift
//  Pythia — AI Research Search
//

import SwiftUI

struct ResearchRAGView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var searchQuery = ""
    @State private var result: ResearchSearchResponse?
    @State private var history: [ResearchDoc] = []
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Research")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Search
                HStack(spacing: PythiaTheme.spacing) {
                    TextField("Search research documents...", text: $searchQuery)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 400)
                        .onSubmit { Task { await search() } }

                    Button("Search") { Task { await search() } }
                        .pythiaPrimaryButton()
                        .disabled(searchQuery.count < 2)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Searching...") }

                if let r = result {
                    Text(r.summary)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textSecondary)
                        .padding(.horizontal)

                    ForEach(r.results) { doc in
                        docCard(doc)
                    }
                }

                if result == nil && !history.isEmpty {
                    Text("Recent Documents")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)

                    ForEach(history) { doc in
                        docCard(doc)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { do { history = try await db.getResearchHistory() } catch {} }
    }

    private func docCard(_ doc: ResearchDoc) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "doc.text")
                    .foregroundColor(PythiaTheme.secondaryBlue)
                Text(doc.title)
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if let type = doc.sourceType {
                    Text(type)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(4)
                }
            }

            if let content = doc.content, !content.isEmpty {
                Text(content)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textSecondary)
                    .lineLimit(3)
            }

            if let date = doc.createdAt {
                Text(date)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func search() async {
        guard searchQuery.count >= 2 else { return }
        isLoading = true
        do { result = try await db.searchResearch(query: searchQuery) } catch {}
        isLoading = false
    }
}
