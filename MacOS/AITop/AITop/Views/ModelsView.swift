//
//  ModelsView.swift
//  AITop
//
//  Model browser: local Ollama models + HuggingFace search
//

import SwiftUI

struct ModelsView: View {
    @EnvironmentObject var apiService: APIService
    @State private var localModels: [OllamaModel] = []
    @State private var hfModels: [HFModel] = []
    @State private var searchQuery = ""
    @State private var isLoadingLocal = true
    @State private var isSearchingHF = false
    @State private var pullModelName = ""
    @State private var isPulling = false
    @State private var pullStatus = ""
    @State private var error: String?
    @State private var selectedTab = 0

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Models")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                Button {
                    loadLocalModels()
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .foregroundColor(AITopTheme.accentOrange)
                }
                .buttonStyle(.plain)
            }
            .padding(AITopTheme.largeSpacing)

            // Tab picker
            Picker("", selection: $selectedTab) {
                Text("Local (\(localModels.count))").tag(0)
                Text("HuggingFace").tag(1)
                Text("Pull Model").tag(2)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, AITopTheme.largeSpacing)

            // Content
            ScrollView {
                VStack(spacing: AITopTheme.spacing) {
                    switch selectedTab {
                    case 0:
                        localModelsSection
                    case 1:
                        huggingFaceSection
                    case 2:
                        pullModelSection
                    default:
                        EmptyView()
                    }
                }
                .padding(AITopTheme.largeSpacing)
            }
        }
        .background(AITopTheme.backgroundDark)
        .onAppear { loadLocalModels() }
    }

    // MARK: - Local Models

    private var localModelsSection: some View {
        VStack(spacing: AITopTheme.smallSpacing) {
            if isLoadingLocal {
                ProgressView("Loading models...")
                    .foregroundColor(AITopTheme.textSecondary)
            } else if localModels.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "cpu")
                        .font(.system(size: 40))
                        .foregroundColor(AITopTheme.textTertiary)
                    Text("No local models")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textSecondary)
                    Text("Pull a model from the Pull Model tab")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                }
                .padding(40)
            } else {
                ForEach(localModels) { model in
                    localModelRow(model)
                }
            }
        }
    }

    private func localModelRow(_ model: OllamaModel) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "cpu.fill")
                .font(.system(size: 20))
                .foregroundColor(AITopTheme.accentOrange)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(model.name)
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
                HStack(spacing: 8) {
                    if !model.parameterSize.isEmpty {
                        Text(model.parameterSize)
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.accentCyan)
                    }
                    if !model.quantization.isEmpty {
                        Text(model.quantization)
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                    if !model.family.isEmpty {
                        Text(model.family)
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                }
            }

            Spacer()

            Text(String(format: "%.1f GB", model.sizeGb))
                .font(AITopTheme.body())
                .foregroundColor(AITopTheme.textSecondary)

            Button {
                deleteModel(model.name)
            } label: {
                Image(systemName: "trash")
                    .foregroundColor(AITopTheme.error)
            }
            .buttonStyle(.plain)
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - HuggingFace Search

    private var huggingFaceSection: some View {
        VStack(spacing: AITopTheme.spacing) {
            HStack {
                TextField("Search models...", text: $searchQuery)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { searchHF() }

                Button("Search") { searchHF() }
                    .aiTopPrimaryButton()
            }

            if isSearchingHF {
                ProgressView("Searching HuggingFace...")
                    .foregroundColor(AITopTheme.textSecondary)
            } else {
                ForEach(hfModels) { model in
                    hfModelRow(model)
                }
            }
        }
    }

    private func hfModelRow(_ model: HFModel) -> some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(model.id)
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
                HStack(spacing: 12) {
                    Label("\(model.downloads)", systemImage: "arrow.down.circle")
                    Label("\(model.likes)", systemImage: "heart")
                }
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textTertiary)
            }
            Spacer()
            if !model.pipelineTag.isEmpty {
                Text(model.pipelineTag)
                    .font(AITopTheme.caption())
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(AITopTheme.surfaceBackground)
                    .cornerRadius(4)
                    .foregroundColor(AITopTheme.accentCyan)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Pull Model

    private var pullModelSection: some View {
        VStack(spacing: AITopTheme.spacing) {
            VStack(alignment: .leading, spacing: 8) {
                Text("Pull Model from Ollama")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)

                Text("Enter model name (e.g., llama3.2:3b, mistral, phi3)")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)

                HStack {
                    TextField("Model name...", text: $pullModelName)
                        .textFieldStyle(.roundedBorder)

                    Button {
                        pullModel()
                    } label: {
                        HStack {
                            if isPulling {
                                ProgressView()
                                    .scaleEffect(0.7)
                            }
                            Text(isPulling ? "Pulling..." : "Pull")
                        }
                    }
                    .aiTopPrimaryButton()
                    .disabled(pullModelName.isEmpty || isPulling)
                }

                if !pullStatus.isEmpty {
                    Text(pullStatus)
                        .font(AITopTheme.monospace())
                        .foregroundColor(AITopTheme.accentCyan)
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(AITopTheme.surfaceBackground)
                        .cornerRadius(6)
                }
            }
            .padding(AITopTheme.spacing)
            .aiTopCard()

            // Quick picks
            VStack(alignment: .leading, spacing: 8) {
                Text("Popular Models")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)

                let popular = ["llama3.2:3b", "llama3.2:1b", "mistral:7b", "phi3:mini", "gemma2:2b", "qwen2.5:3b"]
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 8) {
                    ForEach(popular, id: \.self) { name in
                        Button {
                            pullModelName = name
                        } label: {
                            Text(name)
                                .font(AITopTheme.body())
                                .frame(maxWidth: .infinity)
                        }
                        .aiTopSecondaryButton()
                    }
                }
            }
            .padding(AITopTheme.spacing)
            .aiTopCard()
        }
    }

    // MARK: - Actions

    private func loadLocalModels() {
        isLoadingLocal = true
        Task {
            do {
                let resp: ModelsResponse = try await apiService.getModels()
                await MainActor.run {
                    localModels = resp.models
                    isLoadingLocal = false
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isLoadingLocal = false
                }
            }
        }
    }

    private func searchHF() {
        guard !searchQuery.isEmpty else { return }
        isSearchingHF = true
        Task {
            do {
                let resp: HFSearchResponse = try await apiService.searchHuggingFace(query: searchQuery)
                await MainActor.run {
                    hfModels = resp.models
                    isSearchingHF = false
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isSearchingHF = false
                }
            }
        }
    }

    private func pullModel() {
        guard !pullModelName.isEmpty else { return }
        isPulling = true
        pullStatus = "Starting pull..."
        // Non-streaming pull: just trigger and poll
        Task {
            do {
                // Use URLSession directly for streaming
                let url = URL(string: "\(APIConfig.apiBaseURL)/models/pull")!
                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                request.httpBody = try JSONEncoder().encode(["name": pullModelName])

                let (bytes, _) = try await URLSession.shared.bytes(for: request)
                for try await line in bytes.lines {
                    if let data = line.data(using: .utf8),
                       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        let status = json["status"] as? String ?? ""
                        let completed = json["completed"] as? Int64 ?? 0
                        let total = json["total"] as? Int64 ?? 0
                        await MainActor.run {
                            if total > 0 {
                                let pct = Double(completed) / Double(total) * 100
                                pullStatus = "\(status) — \(Int(pct))%"
                            } else {
                                pullStatus = status
                            }
                        }
                    }
                }
                await MainActor.run {
                    pullStatus = "Done! Model pulled successfully."
                    isPulling = false
                    pullModelName = ""
                    loadLocalModels()
                }
            } catch {
                await MainActor.run {
                    pullStatus = "Error: \(error.localizedDescription)"
                    isPulling = false
                }
            }
        }
    }

    private func deleteModel(_ name: String) {
        Task {
            do {
                let url = URL(string: "\(APIConfig.apiBaseURL)/models")!
                var request = URLRequest(url: url)
                request.httpMethod = "DELETE"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                request.httpBody = try JSONEncoder().encode(["name": name])
                let (_, _) = try await URLSession.shared.data(for: request)
                await MainActor.run { loadLocalModels() }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                }
            }
        }
    }
}
