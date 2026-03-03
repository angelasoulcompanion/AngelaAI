//
//  ResearchRAGView.swift
//  Pythia — AI Research (Enhanced with Vector/Hybrid Search + Ask Mode)
//

import SwiftUI

struct ResearchRAGView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var searchQuery = ""
    @State private var searchMethod = "hybrid"
    @State private var result: ResearchSearchResponse?
    @State private var history: [ResearchDoc] = []
    @State private var isLoading = false
    // Ask mode
    @State private var isAskMode = false
    @State private var askResult: ResearchAskResponse?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Research")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    TextField(isAskMode ? "Ask a question..." : "Search research documents...", text: $searchQuery)
                        .textFieldStyle(.roundedBorder)
                        .frame(width: 400)
                        .onSubmit { Task { await performAction() } }

                    if !isAskMode {
                        Picker("Method", selection: $searchMethod) {
                            Text("Hybrid").tag("hybrid")
                            Text("Vector").tag("vector")
                            Text("Keyword").tag("keyword")
                        }
                        .frame(width: 120)
                    }

                    Toggle("Ask Mode", isOn: $isAskMode)
                        .toggleStyle(.switch)
                        .frame(width: 110)

                    Button(isAskMode ? "Ask" : "Search") { Task { await performAction() } }
                        .pythiaPrimaryButton()
                        .disabled(searchQuery.count < 2)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView(isAskMode ? "Thinking..." : "Searching...") }

                // Ask mode result
                if let ask = askResult {
                    askResultCard(ask)
                }

                // Search results
                if let r = result {
                    HStack {
                        Text(r.summary)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textSecondary)
                        Spacer()
                        if let method = r.searchMethod {
                            Text(method.uppercased())
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.secondaryBlue)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(PythiaTheme.secondaryBlue.opacity(0.15))
                                .cornerRadius(4)
                        }
                    }
                    .padding(.horizontal)

                    ForEach(r.results) { doc in
                        docCard(doc)
                    }
                }

                if result == nil && askResult == nil && !history.isEmpty {
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

    private func askResultCard(_ ask: ResearchAskResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("AI Answer")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if let p = ask.llmProvider {
                    Text(p.uppercased())
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(4)
                }
            }

            Text(ask.answer)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textPrimary)
                .lineSpacing(4)

            if !ask.sources.isEmpty {
                PythiaDivider()

                Text("Sources")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textSecondary)

                ForEach(ask.sources) { source in
                    HStack(spacing: 6) {
                        Image(systemName: "doc.text")
                            .foregroundColor(PythiaTheme.secondaryBlue)
                            .font(.caption)
                        Text(source.title)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textPrimary)
                        if let type = source.sourceType {
                            Text(type)
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textTertiary)
                        }
                    }
                }
            }
        }
        .padding()
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(PythiaTheme.accentGold.opacity(0.3), lineWidth: 1)
        )
        .pythiaCard()
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

    private func performAction() async {
        guard searchQuery.count >= 2 else { return }
        isLoading = true
        askResult = nil
        result = nil

        if isAskMode {
            do { askResult = try await db.askResearch(question: searchQuery) } catch {}
        } else {
            do { result = try await db.searchResearch(query: searchQuery, method: searchMethod) } catch {}
        }
        isLoading = false
    }
}
