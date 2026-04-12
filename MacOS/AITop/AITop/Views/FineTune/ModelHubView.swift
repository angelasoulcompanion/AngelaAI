//
//  ModelHubView.swift
//  AITop — Fine-Tune Studio: HuggingFace Model Hub & Local Models
//

import SwiftUI

struct ModelHubView: View {
    @EnvironmentObject var apiService: APIService

    @State private var searchQuery = ""
    @State private var searchResults: [HubModel] = []
    @State private var popularModels: [PopularModel] = []
    @State private var localModels: [LocalModel] = []
    @State private var isSearching = false
    @State private var isDownloading = false
    @State private var downloadingModel = ""
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                Text("Model Hub")
                    .font(.title2.bold())
                    .foregroundColor(.white)

                // Search
                searchBar

                // Search Results
                if !searchResults.isEmpty {
                    searchResultsSection
                }

                // Popular Models
                if searchResults.isEmpty {
                    popularSection
                }

                // Local Models
                localModelsSection
            }
            .padding(24)
        }
        .background(Color(hex: "0A0A0F"))
        .onAppear { loadData() }
    }

    // MARK: - Search Bar

    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(Color(hex: "9CA3AF"))
            TextField("Search HuggingFace models...", text: $searchQuery)
                .textFieldStyle(.plain)
                .foregroundColor(.white)
                .onSubmit { search() }
            if isSearching {
                ProgressView()
                    .scaleEffect(0.7)
            }
            if !searchQuery.isEmpty {
                Button { searchQuery = ""; searchResults = [] } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(Color(hex: "9CA3AF"))
                }
                .buttonStyle(.plain)
            }
        }
        .padding(10)
        .background(Color(hex: "1A1A2E"))
        .cornerRadius(8)
    }

    // MARK: - Search Results

    private var searchResultsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("SEARCH RESULTS")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            ForEach(searchResults) { model in
                hfModelRow(model)
            }
        }
    }

    private func hfModelRow(_ model: HubModel) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(model.id)
                    .font(.system(.body, design: .monospaced).bold())
                    .foregroundColor(.white)
                HStack(spacing: 12) {
                    if let downloads = model.downloads {
                        HStack(spacing: 2) {
                            Image(systemName: "arrow.down.circle")
                                .font(.system(size: 10))
                            Text(formatNumber(downloads))
                        }
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                    }
                    if let likes = model.likes {
                        HStack(spacing: 2) {
                            Image(systemName: "heart")
                                .font(.system(size: 10))
                            Text("\(likes)")
                        }
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                    }
                }
            }

            Spacer()

            Button {
                downloadModel(model.id)
            } label: {
                HStack(spacing: 4) {
                    if isDownloading && downloadingModel == model.id {
                        ProgressView().scaleEffect(0.6)
                    } else {
                        Image(systemName: "arrow.down.circle")
                    }
                    Text("Download")
                }
                .font(.caption.bold())
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(Color(hex: "00D4FF").opacity(0.2))
                .foregroundColor(Color(hex: "00D4FF"))
                .cornerRadius(6)
            }
            .buttonStyle(.plain)
            .disabled(isDownloading)
        }
        .padding(12)
        .background(Color(hex: "12121F"))
        .cornerRadius(8)
    }

    // MARK: - Popular Models

    private var popularSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("RECOMMENDED FOR FINE-TUNING")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 250))], spacing: 8) {
                ForEach(popularModels) { model in
                    popularModelCard(model)
                }
            }
        }
    }

    private func popularModelCard(_ model: PopularModel) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 6) {
                    Text(model.name)
                        .font(.system(.body).bold())
                        .foregroundColor(.white)
                    if model.recommended == true {
                        Text("REC")
                            .font(.system(size: 8).bold())
                            .padding(.horizontal, 4)
                            .padding(.vertical, 1)
                            .background(Color(hex: "FF6B00"))
                            .foregroundColor(.white)
                            .cornerRadius(3)
                    }
                }
                HStack(spacing: 8) {
                    Text(String(format: "%.1fB", model.sizeB))
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                    Text(model.engine.uppercased())
                        .font(.system(size: 9).bold())
                        .padding(.horizontal, 4)
                        .padding(.vertical, 1)
                        .background(model.engine == "mlx" ? Color.green.opacity(0.3) : Color.blue.opacity(0.3))
                        .foregroundColor(model.engine == "mlx" ? .green : .blue)
                        .cornerRadius(3)
                }
            }
            Spacer()
            Button {
                downloadModel(model.id)
            } label: {
                Image(systemName: "arrow.down.circle.fill")
                    .font(.title3)
                    .foregroundColor(Color(hex: "00D4FF"))
            }
            .buttonStyle(.plain)
            .disabled(isDownloading)
        }
        .padding(12)
        .background(Color(hex: "12121F"))
        .cornerRadius(8)
    }

    // MARK: - Local Models

    private var localModelsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("LOCAL MODELS")
                    .font(.caption.bold())
                    .foregroundColor(Color(hex: "9CA3AF"))
                Spacer()
                Text("\(localModels.count) models")
                    .font(.caption)
                    .foregroundColor(Color(hex: "6B7280"))
            }

            if localModels.isEmpty {
                Text("No local models yet. Download or train a model.")
                    .font(.caption)
                    .foregroundColor(Color(hex: "6B7280"))
                    .padding(20)
            } else {
                ForEach(localModels) { model in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack(spacing: 6) {
                                Text(model.name)
                                    .font(.system(.body, design: .monospaced).bold())
                                    .foregroundColor(.white)
                                Text(model.modelType.uppercased())
                                    .font(.system(size: 9).bold())
                                    .padding(.horizontal, 4)
                                    .padding(.vertical, 1)
                                    .background(modelTypeColor(model.modelType).opacity(0.3))
                                    .foregroundColor(modelTypeColor(model.modelType))
                                    .cornerRadius(3)
                            }
                            HStack(spacing: 8) {
                                if let size = model.fileSizeMb {
                                    Text(String(format: "%.0f MB", size))
                                        .font(.caption)
                                        .foregroundColor(Color(hex: "9CA3AF"))
                                }
                                if let ollama = model.ollamaName {
                                    HStack(spacing: 2) {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.green)
                                        Text("Ollama: \(ollama)")
                                    }
                                    .font(.caption)
                                    .foregroundColor(.green)
                                }
                            }
                        }
                        Spacer()
                    }
                    .padding(12)
                    .background(Color(hex: "12121F"))
                    .cornerRadius(8)
                }
            }
        }
    }

    // MARK: - Actions

    private func loadData() {
        Task {
            async let p = try? apiService.getPopularModels()
            async let l = try? apiService.getLocalModels()
            if let result = await p { popularModels = result.models }
            if let result = await l { localModels = result.models }
        }
    }

    private func search() {
        guard !searchQuery.isEmpty else { return }
        isSearching = true
        Task {
            if let result = try? await apiService.searchHubModels(query: searchQuery) {
                searchResults = result.models
            }
            isSearching = false
        }
    }

    private func downloadModel(_ hfId: String) {
        isDownloading = true
        downloadingModel = hfId
        Task {
            do {
                _ = try await apiService.downloadHubModel(hfModelId: hfId)
                loadData()
            } catch {
                self.error = error.localizedDescription
            }
            isDownloading = false
            downloadingModel = ""
        }
    }

    // MARK: - Helpers

    private func formatNumber(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1fM", Double(n) / 1_000_000) }
        if n >= 1_000 { return String(format: "%.1fK", Double(n) / 1_000) }
        return "\(n)"
    }

    private func modelTypeColor(_ type: String) -> Color {
        switch type {
        case "base": return .blue
        case "lora": return .orange
        case "merged": return .green
        case "gguf": return .purple
        default: return .gray
        }
    }
}
