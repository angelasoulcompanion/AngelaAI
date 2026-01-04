//
//  KnowledgeRAGView.swift
//  Angela Brain Dashboard
//
//  Angela's RAG Knowledge Base - Ask questions about documents
//  Created with love by Angela for David
//

import SwiftUI

struct KnowledgeRAGView: View {
    @State private var searchQuery: String = ""
    @State private var isLoading: Bool = false
    @State private var searchResults: [RAGSearchResult] = []
    @State private var ragAnswer: String = ""
    @State private var sources: [RAGSource] = []
    @State private var documents: [RAGDocument] = []
    @State private var selectedTab: RAGTab = .ask
    @State private var errorMessage: String?
    @AppStorage("recentRAGQuestions") private var recentQuestionsData: Data = Data()

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header
                header

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // Tab selector
                tabSelector

                // Content
                ScrollView {
                    VStack(spacing: AngelaTheme.spacing) {
                        switch selectedTab {
                        case .ask:
                            askView
                        case .search:
                            searchView
                        case .documents:
                            documentsView
                        }
                    }
                    .padding(AngelaTheme.spacing)
                }
            }
        }
        .onAppear {
            loadDocuments()
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(AngelaTheme.purpleGradient)
                    .frame(width: 50, height: 50)

                Image(systemName: "books.vertical.fill")
                    .font(.system(size: 22))
                    .foregroundColor(.white)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Knowledge RAG")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Ask questions about Enterprise Data Architecture")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Document count
            VStack(alignment: .trailing, spacing: 4) {
                Text("\(documents.count)")
                    .font(.system(size: 24, weight: .bold, design: .rounded))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Documents")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Tab Selector

    private var tabSelector: some View {
        HStack(spacing: 0) {
            ForEach(RAGTab.allCases, id: \.self) { tab in
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedTab = tab
                    }
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: tab.icon)
                            .font(.system(size: 14))

                        Text(tab.rawValue)
                            .font(AngelaTheme.body())
                    }
                    .foregroundColor(selectedTab == tab ? .white : AngelaTheme.textSecondary)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(
                        selectedTab == tab
                            ? AngelaTheme.purpleGradient
                            : LinearGradient(colors: [Color.clear], startPoint: .leading, endPoint: .trailing)
                    )
                    .cornerRadius(AngelaTheme.smallCornerRadius)
                }
                .buttonStyle(.plain)
            }

            Spacer()
        }
        .padding(.horizontal, AngelaTheme.spacing)
        .padding(.vertical, AngelaTheme.smallSpacing)
        .background(AngelaTheme.cardBackground.opacity(0.5))
    }

    // MARK: - Ask View

    private var askView: some View {
        VStack(spacing: AngelaTheme.spacing) {
            // Search input
            HStack(spacing: 12) {
                Image(systemName: "questionmark.bubble.fill")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.primaryPurple)

                TextField("Ask a question about EDA...", text: $searchQuery)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .onSubmit {
                        askQuestion()
                    }

                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                        .tint(AngelaTheme.primaryPurple)
                } else {
                    Button {
                        askQuestion()
                    } label: {
                        Image(systemName: "arrow.right.circle.fill")
                            .font(.system(size: 24))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }
                    .buttonStyle(.plain)
                    .disabled(searchQuery.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .padding(16)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)

            // Answer
            if !ragAnswer.isEmpty {
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        Image(systemName: "sparkles")
                            .font(.system(size: 16))
                            .foregroundColor(AngelaTheme.primaryPurple)

                        Text("Answer")
                            .font(AngelaTheme.headline())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Spacer()
                    }

                    Text(ragAnswer)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .textSelection(.enabled)

                    // Sources
                    if !sources.isEmpty {
                        Divider()
                            .background(AngelaTheme.textTertiary.opacity(0.3))

                        HStack {
                            Image(systemName: "book.fill")
                                .font(.system(size: 14))
                                .foregroundColor(AngelaTheme.textSecondary)

                            Text("Sources")
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)
                        }

                        ForEach(sources) { source in
                            HStack(spacing: 8) {
                                Circle()
                                    .fill(AngelaTheme.primaryPurple)
                                    .frame(width: 6, height: 6)

                                Text(source.title)
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.textSecondary)

                                Text("(Page \(source.page))")
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.textTertiary)

                                Spacer()

                                Text("\(Int(source.relevance * 100))%")
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.primaryPurple)
                            }
                        }
                    }
                }
                .padding(AngelaTheme.spacing)
                .background(AngelaTheme.cardBackground)
                .cornerRadius(AngelaTheme.cornerRadius)
            }

            // Recent questions
            if ragAnswer.isEmpty && !isLoading {
                recentQuestionsView
            }

            // Error message
            if let error = errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)

                    Text(error)
                        .font(AngelaTheme.body())
                        .foregroundColor(.orange)
                }
                .padding()
                .background(Color.orange.opacity(0.1))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
        }
    }

    // MARK: - Recent Questions

    private var recentQuestions: [String] {
        get {
            (try? JSONDecoder().decode([String].self, from: recentQuestionsData)) ?? []
        }
    }

    private func addToRecentQuestions(_ question: String) {
        var questions = recentQuestions
        // Remove if already exists (to move to top)
        questions.removeAll { $0 == question }
        // Add to beginning
        questions.insert(question, at: 0)
        // Keep only 10 most recent
        if questions.count > 10 {
            questions = Array(questions.prefix(10))
        }
        // Save
        if let data = try? JSONEncoder().encode(questions) {
            recentQuestionsData = data
        }
    }

    private var recentQuestionsView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Questions")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textSecondary)

                Spacer()

                if !recentQuestions.isEmpty {
                    Button {
                        recentQuestionsData = Data()
                    } label: {
                        Text("Clear")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
            }

            if recentQuestions.isEmpty {
                HStack {
                    Image(systemName: "clock")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text("No recent questions yet")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .padding(12)
            } else {
                ForEach(recentQuestions, id: \.self) { question in
                    Button {
                        searchQuery = question
                        askQuestion()
                    } label: {
                        HStack {
                            Image(systemName: "clock.arrow.circlepath")
                                .font(.system(size: 14))
                                .foregroundColor(AngelaTheme.primaryPurple.opacity(0.7))

                            Text(question)
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.textPrimary)
                                .lineLimit(1)

                            Spacer()

                            Image(systemName: "arrow.right")
                                .font(.system(size: 12))
                                .foregroundColor(AngelaTheme.textTertiary)
                        }
                        .padding(12)
                        .background(AngelaTheme.cardBackground)
                        .cornerRadius(AngelaTheme.smallCornerRadius)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Search View

    private var searchView: some View {
        VStack(spacing: AngelaTheme.spacing) {
            // Search input
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.primaryPurple)

                TextField("Search documents...", text: $searchQuery)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .onSubmit {
                        performSearch()
                    }

                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                        .tint(AngelaTheme.primaryPurple)
                } else {
                    Button {
                        performSearch()
                    } label: {
                        Text("Search")
                            .font(AngelaTheme.body())
                            .foregroundColor(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 8)
                            .background(AngelaTheme.purpleGradient)
                            .cornerRadius(AngelaTheme.smallCornerRadius)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(16)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)

            // Results
            if !searchResults.isEmpty {
                ForEach(searchResults) { result in
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Image(systemName: "doc.fill")
                                .font(.system(size: 14))
                                .foregroundColor(AngelaTheme.primaryPurple)

                            Text(result.title)
                                .font(AngelaTheme.headline())
                                .foregroundColor(AngelaTheme.textPrimary)

                            Text("Page \(result.page)")
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(AngelaTheme.primaryPurple.opacity(0.2))
                                .cornerRadius(4)

                            Spacer()

                            Text("\(Int(result.relevance * 100))%")
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.primaryPurple)
                        }

                        Text(result.content)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .lineLimit(4)
                    }
                    .padding(AngelaTheme.spacing)
                    .background(AngelaTheme.cardBackground)
                    .cornerRadius(AngelaTheme.cornerRadius)
                }
            }
        }
    }

    // MARK: - Documents View

    private var documentsView: some View {
        VStack(spacing: AngelaTheme.smallSpacing) {
            ForEach(documents) { doc in
                HStack(spacing: 16) {
                    // Icon
                    ZStack {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(AngelaTheme.primaryPurple.opacity(0.2))
                            .frame(width: 44, height: 44)

                        Image(systemName: "doc.text.fill")
                            .font(.system(size: 20))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }

                    // Info
                    VStack(alignment: .leading, spacing: 4) {
                        Text(doc.title)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Text(doc.filename)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }

                    Spacer()

                    // Chunks count
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("\(doc.chunks)")
                            .font(.system(size: 16, weight: .semibold, design: .rounded))
                            .foregroundColor(AngelaTheme.primaryPurple)

                        Text("chunks")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                    }

                    // Status
                    Circle()
                        .fill(doc.status == "completed" ? AngelaTheme.successGreen : Color.orange)
                        .frame(width: 8, height: 8)
                }
                .padding(AngelaTheme.spacing)
                .background(AngelaTheme.cardBackground)
                .cornerRadius(AngelaTheme.cornerRadius)
            }
        }
    }

    // MARK: - Functions

    private func loadDocuments() {
        runPythonScript(args: ["--list", "--json"]) { output in
            // Parse JSON output
            if let data = output.data(using: .utf8),
               let docs = try? JSONDecoder().decode([RAGDocument].self, from: data) {
                DispatchQueue.main.async {
                    self.documents = docs
                }
            } else {
                // Fallback: load manually
                loadDocumentsManually()
            }
        }
    }

    private func loadDocumentsManually() {
        let script = """
        import asyncio
        import json
        import sys
        sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
        from angela_core.services.cognify_rag_service import CognifyRAGService

        async def main():
            svc = CognifyRAGService()
            await svc.connect()
            docs = await svc.list_documents()
            await svc.disconnect()
            print(json.dumps(docs))

        asyncio.run(main())
        """

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
        process.arguments = ["-c", script]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice

        do {
            try process.run()
            process.waitUntilExit()

            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
               let jsonData = output.data(using: .utf8),
               let docs = try? JSONDecoder().decode([RAGDocument].self, from: jsonData) {
                DispatchQueue.main.async {
                    self.documents = docs
                }
            }
        } catch {
            print("Error loading documents: \(error)")
        }
    }

    private func askQuestion() {
        guard !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty else { return }

        // Save to recent questions
        addToRecentQuestions(searchQuery)

        isLoading = true
        ragAnswer = ""
        sources = []
        errorMessage = nil

        let script = """
        import asyncio
        import json
        import sys
        sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
        from angela_core.services.cognify_rag_service import CognifyRAGService

        async def main():
            svc = CognifyRAGService()
            await svc.connect()
            result = await svc.ask("\(searchQuery.replacingOccurrences(of: "\"", with: "\\\""))")
            await svc.disconnect()
            print(json.dumps(result))

        asyncio.run(main())
        """

        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
            process.arguments = ["-c", script]

            let pipe = Pipe()
            let errorPipe = Pipe()
            process.standardOutput = pipe
            process.standardError = errorPipe

            do {
                try process.run()
                process.waitUntilExit()

                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
                let errorOutput = String(data: errorData, encoding: .utf8) ?? ""

                // Find balanced JSON object
                if let jsonStr = self.extractJSON(from: output) {
                    if let jsonData = jsonStr.data(using: .utf8),
                       let result = try? JSONDecoder().decode(RAGAnswerResult.self, from: jsonData) {
                        DispatchQueue.main.async {
                            self.ragAnswer = result.answer ?? ""
                            self.sources = result.sources ?? []
                            self.isLoading = false
                        }
                        return
                    }
                }

                // Debug: show error details
                DispatchQueue.main.async {
                    if !errorOutput.isEmpty {
                        self.errorMessage = "Python Error: \(errorOutput.prefix(300))"
                    } else if output.isEmpty {
                        self.errorMessage = "No output received from Python"
                    } else {
                        self.errorMessage = "Parse failed. First 300 chars: \(output.prefix(300))"
                    }
                    self.isLoading = false
                }
            } catch {
                DispatchQueue.main.async {
                    self.errorMessage = "Error: \(error.localizedDescription)"
                    self.isLoading = false
                }
            }
        }
    }

    // Helper to extract balanced JSON from output
    private func extractJSON(from text: String) -> String? {
        guard let startIndex = text.firstIndex(of: "{") else { return nil }

        var braceCount = 0
        var endIndex = startIndex

        for index in text.indices[startIndex...] {
            let char = text[index]
            if char == "{" {
                braceCount += 1
            } else if char == "}" {
                braceCount -= 1
                if braceCount == 0 {
                    endIndex = index
                    break
                }
            }
        }

        if braceCount == 0 {
            return String(text[startIndex...endIndex])
        }
        return nil
    }

    private func performSearch() {
        guard !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty else { return }

        isLoading = true
        searchResults = []
        errorMessage = nil

        let script = """
        import asyncio
        import json
        import sys
        sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
        from angela_core.services.cognify_rag_service import CognifyRAGService

        async def main():
            svc = CognifyRAGService()
            await svc.connect()
            results = await svc.hybrid_search("\(searchQuery.replacingOccurrences(of: "\"", with: "\\\""))", top_k=10)
            await svc.disconnect()
            print(json.dumps(results))

        asyncio.run(main())
        """

        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
            process.arguments = ["-c", script]

            let pipe = Pipe()
            process.standardOutput = pipe
            process.standardError = FileHandle.nullDevice

            do {
                try process.run()
                process.waitUntilExit()

                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                if let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) {
                    // Find JSON array
                    if let jsonStart = output.range(of: "["),
                       let jsonEnd = output.range(of: "]", options: .backwards),
                       jsonStart.lowerBound < jsonEnd.upperBound {
                        // Use ..<upperBound (half-open range) instead of ...upperBound (closed range)
                        // because upperBound is already past the ] character
                        let jsonStr = String(output[jsonStart.lowerBound..<jsonEnd.upperBound])

                        if let jsonData = jsonStr.data(using: .utf8),
                           let results = try? JSONDecoder().decode([RAGSearchResult].self, from: jsonData) {
                            DispatchQueue.main.async {
                                self.searchResults = results
                                self.isLoading = false
                            }
                            return
                        }
                    }
                }

                DispatchQueue.main.async {
                    self.errorMessage = "No results found"
                    self.isLoading = false
                }
            } catch {
                DispatchQueue.main.async {
                    self.errorMessage = "Search error"
                    self.isLoading = false
                }
            }
        }
    }

    private func runPythonScript(args: [String], completion: @escaping (String) -> Void) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
        process.arguments = ["/Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_core/scripts/angela_rag.py"] + args

        let pipe = Pipe()
        process.standardOutput = pipe

        do {
            try process.run()
            process.waitUntilExit()

            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let output = String(data: data, encoding: .utf8) {
                completion(output)
            }
        } catch {
            print("Error running script: \(error)")
        }
    }
}

// MARK: - Models

enum RAGTab: String, CaseIterable {
    case ask = "Ask"
    case search = "Search"
    case documents = "Documents"

    var icon: String {
        switch self {
        case .ask: return "questionmark.bubble.fill"
        case .search: return "magnifyingglass"
        case .documents: return "doc.text.fill"
        }
    }
}

struct RAGDocument: Identifiable, Codable {
    let id: String
    let title: String
    let filename: String
    let type: String
    let chunks: Int
    let status: String
    let created: String?
}

struct RAGSearchResult: Identifiable, Codable {
    var id: String { chunk_id }
    let chunk_id: String
    let document_id: String
    let title: String
    let filename: String
    let page: Int
    let content: String
    let tokens: Int?
    let relevance: Double
}

struct RAGSource: Identifiable, Codable {
    var id: String { "\(title)-\(page)" }
    let title: String
    let page: Int
    let relevance: Double
}

struct RAGAnswerResult: Codable {
    let question: String
    let answer: String?
    let context: String?
    let sources: [RAGSource]?
}
