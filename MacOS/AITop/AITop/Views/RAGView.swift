//
//  RAGView.swift
//  AITop
//
//  Document-based Q&A with RAG
//

import SwiftUI

struct RAGView: View {
    @EnvironmentObject var apiService: APIService
    @State private var documents: [RAGDocument] = []
    @State private var localModels: [OllamaModel] = []
    @AppStorage("defaultModel") private var selectedModel = ""
    @State private var query = ""
    @State private var answer = ""
    @State private var chunks: [RAGChunk] = []
    @State private var isQuerying = false
    @State private var isUploading = false
    @State private var errorMessage: String?
    @State private var showError = false
    @State private var tokensPerSecond: Double = 0
    @State private var deleteTarget: RAGDocument?
    @State private var showDeleteConfirm = false

    var body: some View {
        HSplitView {
            // Main query area
            VStack(spacing: 0) {
                HStack {
                    Text("RAG")
                        .font(AITopTheme.title())
                        .foregroundColor(AITopTheme.textPrimary)
                    Spacer()
                    Picker("Model", selection: $selectedModel) {
                        Text("Select model...").tag("")
                        ForEach(localModels) { model in
                            Text(model.name).tag(model.name)
                        }
                    }
                    .frame(width: 200)
                }
                .padding(AITopTheme.spacing)

                AITopDivider()

                ScrollView {
                    VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                        // Query input
                        HStack {
                            TextField("Ask a question about your documents...", text: $query)
                                .textFieldStyle(.roundedBorder)
                                .onSubmit { performQuery() }

                            Button {
                                performQuery()
                            } label: {
                                HStack {
                                    if isQuerying {
                                        ProgressView().scaleEffect(0.7)
                                    }
                                    Text("Ask")
                                }
                            }
                            .aiTopPrimaryButton()
                            .disabled(query.isEmpty || selectedModel.isEmpty || isQuerying)
                        }

                        // Answer
                        if !answer.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text("Answer")
                                        .font(AITopTheme.heading())
                                        .foregroundColor(AITopTheme.textPrimary)
                                    Spacer()
                                    if tokensPerSecond > 0 {
                                        Text(String(format: "%.1f tok/s", tokensPerSecond))
                                            .font(AITopTheme.monospace())
                                            .foregroundColor(AITopTheme.accentCyan)
                                    }
                                }
                                Text(answer)
                                    .font(AITopTheme.body())
                                    .foregroundColor(AITopTheme.textPrimary)
                                    .textSelection(.enabled)
                            }
                            .padding(AITopTheme.spacing)
                            .aiTopCard()
                        }

                        // Retrieved chunks
                        if !chunks.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Retrieved Chunks (\(chunks.count))")
                                    .font(AITopTheme.heading())
                                    .foregroundColor(AITopTheme.textPrimary)

                                ForEach(chunks) { chunk in
                                    VStack(alignment: .leading, spacing: 4) {
                                        HStack {
                                            Text(chunk.docName)
                                                .font(AITopTheme.caption())
                                                .foregroundColor(AITopTheme.accentOrange)
                                            Spacer()
                                            Text(String(format: "Score: %.3f", chunk.score))
                                                .font(AITopTheme.monospace())
                                                .foregroundColor(AITopTheme.textTertiary)
                                        }
                                        Text(chunk.chunkText)
                                            .font(AITopTheme.caption())
                                            .foregroundColor(AITopTheme.textSecondary)
                                            .lineLimit(4)
                                    }
                                    .padding(AITopTheme.smallSpacing)
                                    .background(AITopTheme.surfaceBackground)
                                    .cornerRadius(6)
                                }
                            }
                            .padding(AITopTheme.spacing)
                            .aiTopCard()
                        }
                    }
                    .padding(AITopTheme.spacing)
                }
            }
            .frame(minWidth: 500)

            // Documents panel
            VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                HStack {
                    Text("Documents")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)
                    Spacer()
                    Button {
                        uploadDocument()
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .foregroundColor(AITopTheme.accentOrange)
                    }
                    .buttonStyle(.plain)
                }

                if documents.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "doc.text")
                            .font(.system(size: 32))
                            .foregroundColor(AITopTheme.textTertiary)
                        Text("No documents")
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textTertiary)
                        Text("Upload PDF, TXT, or MD files")
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(20)
                } else {
                    ForEach(documents) { doc in
                        HStack {
                            Image(systemName: "doc.text.fill")
                                .foregroundColor(AITopTheme.accentCyan)
                            VStack(alignment: .leading) {
                                Text(doc.filename)
                                    .font(AITopTheme.body())
                                    .foregroundColor(AITopTheme.textPrimary)
                                Text("\(doc.chunkCount) chunks")
                                    .font(AITopTheme.caption())
                                    .foregroundColor(AITopTheme.textTertiary)
                            }
                            Spacer()
                            if doc.indexed {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(AITopTheme.success)
                                    .font(.system(size: 12))
                            }
                            Button {
                                deleteTarget = doc
                                showDeleteConfirm = true
                            } label: {
                                Image(systemName: "trash")
                                    .foregroundColor(AITopTheme.error)
                                    .font(.system(size: 12))
                            }
                            .buttonStyle(.plain)
                        }
                        .padding(8)
                        .background(AITopTheme.surfaceBackground)
                        .cornerRadius(6)
                    }
                }

                Spacer()
            }
            .padding(AITopTheme.spacing)
            .frame(width: 250)
            .background(AITopTheme.backgroundMedium)
        }
        .background(AITopTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK") {}
        } message: {
            Text(errorMessage ?? "Unknown error")
        }
        .alert("Delete Document", isPresented: $showDeleteConfirm) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                if let doc = deleteTarget {
                    deleteDocument(doc)
                }
            }
        } message: {
            Text("Remove \"\(deleteTarget?.filename ?? "")\" from the index? This cannot be undone.")
        }
        .onAppear {
            loadDocuments()
            loadModels()
        }
    }

    // MARK: - Actions

    private func loadDocuments() {
        Task {
            do {
                let resp: DocumentsResponse = try await apiService.getDocuments()
                await MainActor.run { documents = resp.documents }
            } catch {
                showErrorAlert(error.localizedDescription)
            }
        }
    }

    private func loadModels() {
        Task {
            do {
                let resp: ModelsResponse = try await apiService.getModels()
                await MainActor.run {
                    localModels = resp.models
                }
            } catch {}
        }
    }

    private func performQuery() {
        guard !query.isEmpty, !selectedModel.isEmpty else { return }
        isQuerying = true
        Task {
            do {
                let result: RAGQueryResponse = try await apiService.queryRAG(
                    query: query, model: selectedModel
                )
                await MainActor.run {
                    answer = result.answer
                    chunks = result.chunks
                    tokensPerSecond = result.tokensPerSecond ?? 0
                    isQuerying = false
                }
            } catch {
                await MainActor.run {
                    answer = "Error: \(error.localizedDescription)"
                    isQuerying = false
                }
            }
        }
    }

    private func uploadDocument() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.plainText, .pdf]
        panel.allowsMultipleSelection = false

        if panel.runModal() == .OK, let url = panel.url {
            isUploading = true
            Task {
                do {
                    let boundary = UUID().uuidString
                    let fileData = try Data(contentsOf: url)
                    let filename = url.lastPathComponent

                    var body = Data()
                    body.append("--\(boundary)\r\n".data(using: .utf8)!)
                    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
                    body.append("Content-Type: application/octet-stream\r\n\r\n".data(using: .utf8)!)
                    body.append(fileData)
                    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

                    let apiURL = URL(string: "\(APIConfig.apiBaseURL)/rag/documents/upload")!
                    var request = URLRequest(url: apiURL)
                    request.httpMethod = "POST"
                    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
                    request.httpBody = body

                    let (_, _) = try await URLSession.shared.data(for: request)
                    await MainActor.run {
                        isUploading = false
                        loadDocuments()
                    }
                } catch {
                    await MainActor.run {
                        isUploading = false
                        showErrorAlert(error.localizedDescription)
                    }
                }
            }
        }
    }

    private func deleteDocument(_ doc: RAGDocument) {
        Task {
            do {
                try await apiService.deleteRAGDocument(id: doc.id)
                await MainActor.run {
                    loadDocuments()
                }
            } catch {
                await MainActor.run {
                    showErrorAlert(error.localizedDescription)
                }
            }
        }
    }

    private func showErrorAlert(_ message: String) {
        errorMessage = message
        showError = true
    }
}
