//
//  SettingsView.swift
//  AITop
//
//  Configuration panel
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var backendManager: BackendManager
    @State private var ollamaPort = "11434"
    @State private var backendPort = "8767"
    @State private var defaultModel = ""
    @State private var localModels: [OllamaModel] = []

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
        .onAppear { loadModels() }
    }

    private func loadModels() {
        Task {
            do {
                let resp: ModelsResponse = try await APIService.shared.getModels()
                await MainActor.run { localModels = resp.models }
            } catch {}
        }
    }
}
