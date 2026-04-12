//
//  SettingsView.swift
//  AITop
//
//  Configuration panel
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var backendManager: BackendManager
    @EnvironmentObject var apiService: APIService
    @AppStorage("ollamaPort") private var ollamaPort = "11434"
    @AppStorage("defaultModel") private var defaultModel = ""
    @State private var localModels: [OllamaModel] = []
    @State private var settingsSaved = false

    // RAG folder
    @AppStorage("ragFolderPath") private var ragFolderPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/rag_docs"
    @State private var isIndexing = false
    @State private var indexResult: String?
    @State private var errorMessage: String?
    @State private var showError = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AITopTheme.largeSpacing) {
                Text("Settings")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)

                // Backend section
                VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                    Text("Backend")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    HStack {
                        Text("Status:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        Circle()
                            .fill(backendManager.isConnected ? AITopTheme.success : AITopTheme.error)
                            .frame(width: 8, height: 8)
                        Text(backendManager.statusMessage)
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textPrimary)
                    }

                    HStack {
                        Text("Port:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        Text("\(APIConfig.port)")
                            .font(AITopTheme.monospace())
                            .foregroundColor(AITopTheme.accentCyan)
                    }

                    HStack(spacing: 12) {
                        Button {
                            backendManager.stopServer()
                        } label: {
                            Text("Stop Backend")
                        }
                        .aiTopSecondaryButton()

                        Button {
                            backendManager.autoStart()
                        } label: {
                            Text("Restart Backend")
                        }
                        .aiTopPrimaryButton()
                    }
                }
                .padding(AITopTheme.spacing)
                .aiTopCard()

                // RAG Documents Folder
                VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                    Text("RAG Documents")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    HStack {
                        Text("Folder:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        TextField("Path to documents folder...", text: $ragFolderPath)
                            .textFieldStyle(.roundedBorder)
                            .font(AITopTheme.monospace())
                        Button("Browse") {
                            browseFolder()
                        }
                        .aiTopSecondaryButton()
                    }

                    Text(ragFolderPath)
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                        .lineLimit(1)
                        .truncationMode(.middle)

                    HStack(spacing: 12) {
                        Button {
                            indexFolder()
                        } label: {
                            HStack(spacing: 6) {
                                if isIndexing {
                                    ProgressView().scaleEffect(0.7)
                                }
                                Image(systemName: "doc.text.magnifyingglass")
                                Text("Index Folder")
                            }
                        }
                        .aiTopPrimaryButton()
                        .disabled(ragFolderPath.isEmpty || isIndexing)

                        if let result = indexResult {
                            Text(result)
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.success)
                        }
                    }

                    Text("Indexes all .txt, .md, .pdf, .py, .json, .csv files in the folder for RAG search.")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                }
                .padding(AITopTheme.spacing)
                .aiTopCard()

                // Ollama section
                VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                    Text("Ollama")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    HStack {
                        Text("API Port:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        TextField("Port", text: $ollamaPort)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 100)
                    }

                    HStack {
                        Text("Default Model:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        Picker("", selection: $defaultModel) {
                            Text("None").tag("")
                            ForEach(localModels) { model in
                                Text(model.name).tag(model.name)
                            }
                        }
                        .frame(width: 200)
                    }

                    HStack(spacing: 12) {
                        if settingsSaved {
                            Text("Saved")
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.success)
                        }
                    }
                }
                .padding(AITopTheme.spacing)
                .aiTopCard()

                // MLX section
                VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                    Text("MLX Fine-Tuning")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    HStack {
                        Text("Workspace:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        Text("~/.aitop/finetune/")
                            .font(AITopTheme.monospace())
                            .foregroundColor(AITopTheme.textTertiary)
                    }

                    HStack {
                        Text("Datasets:")
                            .font(AITopTheme.body())
                            .foregroundColor(AITopTheme.textSecondary)
                        Text("~/.aitop/finetune/datasets/")
                            .font(AITopTheme.monospace())
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                }
                .padding(AITopTheme.spacing)
                .aiTopCard()

                // About
                VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
                    Text("About AI TOP")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)

                    Text("Local AI Training & Inference Studio")
                        .font(AITopTheme.body())
                        .foregroundColor(AITopTheme.textSecondary)
                    Text("Apple Silicon native | MLX + Ollama")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                    Text("Version 1.0.0")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                }
                .padding(AITopTheme.spacing)
                .aiTopCard()

                Spacer()
            }
            .padding(AITopTheme.largeSpacing)
        }
        .background(AITopTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK") {}
        } message: {
            Text(errorMessage ?? "Unknown error")
        }
        .onAppear { loadModels() }
    }

    // MARK: - Actions

    private func loadModels() {
        Task {
            do {
                let resp: ModelsResponse = try await APIService.shared.getModels()
                await MainActor.run { localModels = resp.models }
            } catch {}
        }
    }

    private func browseFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url {
            ragFolderPath = url.path
        }
    }

    private func indexFolder() {
        isIndexing = true
        indexResult = nil
        Task {
            do {
                let resp = try await apiService.indexRAGFolder(path: ragFolderPath)
                await MainActor.run {
                    isIndexing = false
                    indexResult = "\(resp.totalIndexed) files indexed"
                    if resp.totalErrors > 0 {
                        indexResult! += ", \(resp.totalErrors) errors"
                    }
                }
            } catch {
                await MainActor.run {
                    isIndexing = false
                    errorMessage = error.localizedDescription
                    showError = true
                }
            }
        }
    }
}
