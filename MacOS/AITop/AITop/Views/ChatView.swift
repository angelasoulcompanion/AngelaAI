//
//  ChatView.swift
//  AITop
//
//  Chat interface to test local models
//

import SwiftUI

struct ChatView: View {
    @EnvironmentObject var apiService: APIService
    @State private var messages: [ChatMessage] = []
    @State private var inputText = ""
    @State private var localModels: [OllamaModel] = []
    @AppStorage("defaultModel") private var selectedModel = "gemma3:12b"
    // Clean default — no Angela persona. This Chat view is for model evaluation only.
    @State private var systemPrompt = "กฎสำคัญ: ตอบเป็นภาษาไทยเท่านั้น ห้ามแปลเป็นภาษาอังกฤษ ห้ามตอบ 2 ภาษา\nตอบกระชับ ตรงประเด็น คิดเป็นขั้นตอน"
    @State private var temperature: Double = 0.7
    @State private var maxTokens: Double = 2048
    @State private var isGenerating = false
    @State private var lastStats = ""

    var body: some View {
        HSplitView {
            // Chat area
            VStack(spacing: 0) {
                // Model selector bar
                HStack(spacing: 12) {
                    Text("Chat")
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

                    Button {
                        exportToPDF()
                    } label: {
                        Image(systemName: "square.and.arrow.up")
                            .foregroundColor(messages.isEmpty ? AITopTheme.textTertiary.opacity(0.4) : AITopTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                    .disabled(messages.isEmpty)
                    .help("Export chat history to PDF")

                    Button {
                        messages = []
                        lastStats = ""
                    } label: {
                        Image(systemName: "trash")
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                    .help("Clear chat")
                }
                .padding(AITopTheme.spacing)

                AITopDivider()

                // Messages
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
                            ForEach(Array(messages.enumerated()), id: \.offset) { idx, message in
                                messageBubble(message, index: idx)
                            }

                            if isGenerating {
                                HStack(spacing: 8) {
                                    ProgressView()
                                        .scaleEffect(0.7)
                                    Text("Generating...")
                                        .font(AITopTheme.caption())
                                        .foregroundColor(AITopTheme.textTertiary)
                                }
                                .padding(.horizontal, AITopTheme.spacing)
                                .id("loading")
                            }
                        }
                        .padding(AITopTheme.spacing)
                    }
                    .onChange(of: messages.count) { _, _ in
                        withAnimation {
                            proxy.scrollTo("loading", anchor: .bottom)
                        }
                    }
                }

                // Stats bar
                if !lastStats.isEmpty {
                    HStack {
                        Text(lastStats)
                            .font(AITopTheme.monospace())
                            .foregroundColor(AITopTheme.accentCyan)
                    }
                    .padding(.horizontal, AITopTheme.spacing)
                    .padding(.vertical, 4)
                    .background(AITopTheme.surfaceBackground)
                }

                AITopDivider()

                // Input
                HStack(spacing: 8) {
                    TextField("Message...", text: $inputText, axis: .vertical)
                        .textFieldStyle(.plain)
                        .lineLimit(1...5)
                        .padding(8)
                        .background(AITopTheme.surfaceBackground)
                        .cornerRadius(8)
                        .foregroundColor(AITopTheme.textPrimary)
                        .onSubmit { sendMessage() }

                    Button {
                        sendMessage()
                    } label: {
                        Image(systemName: "paperplane.fill")
                            .font(.system(size: 16))
                    }
                    .aiTopPrimaryButton()
                    .disabled(inputText.isEmpty || selectedModel.isEmpty || isGenerating)
                }
                .padding(AITopTheme.spacing)
            }
            .frame(minWidth: 500)

            // Settings panel
            VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                Text("Settings")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)

                VStack(alignment: .leading, spacing: 4) {
                    Text("System Prompt")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textSecondary)
                    TextEditor(text: $systemPrompt)
                        .font(AITopTheme.body())
                        .frame(height: 100)
                        .padding(4)
                        .background(AITopTheme.surfaceBackground)
                        .cornerRadius(6)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Temperature: \(String(format: "%.1f", temperature))")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textSecondary)
                    Slider(value: $temperature, in: 0...2, step: 0.1)
                        .tint(AITopTheme.accentOrange)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Max Tokens: \(Int(maxTokens))")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textSecondary)
                    Slider(value: $maxTokens, in: 256...8192, step: 256)
                        .tint(AITopTheme.accentOrange)
                }

                Spacer()
            }
            .padding(AITopTheme.spacing)
            .frame(width: 250)
            .background(AITopTheme.backgroundMedium)
        }
        .background(AITopTheme.backgroundDark)
        .onAppear { loadModels() }
    }

    // MARK: - Message Bubble

    private func messageBubble(_ message: ChatMessage, index: Int) -> some View {
        let isUser = message.role == "user"
        return HStack {
            if isUser { Spacer(minLength: 60) }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(isUser ? "You" : (message.model ?? selectedModel))
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)

                Text(message.content)
                    .font(AITopTheme.body())
                    .foregroundColor(AITopTheme.textPrimary)
                    .padding(10)
                    .background(isUser ? AITopTheme.accentOrange.opacity(0.2) : AITopTheme.surfaceBackground)
                    .cornerRadius(12)
                    .textSelection(.enabled)
            }
            if !isUser { Spacer(minLength: 60) }
        }
        .id(index)
    }

    // MARK: - Actions

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

    private func exportToPDF() {
        guard !messages.isEmpty else { return }
        do {
            if let url = try ChatPDFExporter.promptAndExport(
                messages: messages,
                model: selectedModel,
                systemPrompt: systemPrompt
            ) {
                lastStats = "✓ Exported to \(url.lastPathComponent)"
                NSWorkspace.shared.activateFileViewerSelecting([url])
            }
        } catch {
            lastStats = "Export failed: \(error.localizedDescription)"
        }
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !selectedModel.isEmpty else { return }

        let userMsg = ChatMessage(role: "user", content: text)
        messages.append(userMsg)
        inputText = ""
        isGenerating = true

        Task {
            do {
                let result: ChatResponse = try await apiService.chat(
                    model: selectedModel,
                    messages: messages,
                    system: systemPrompt.isEmpty ? nil : systemPrompt,
                    temperature: temperature,
                    maxTokens: Int(maxTokens)
                )
                let assistantMsg = ChatMessage(role: "assistant", content: result.content, model: result.model)
                await MainActor.run {
                    messages.append(assistantMsg)
                    lastStats = "\(result.tokensPerSecond) tok/s | \(result.evalCount) tokens | \(Int(result.totalDurationMs))ms"
                    isGenerating = false
                }
            } catch {
                let errorMsg = ChatMessage(role: "assistant", content: "Error: \(error.localizedDescription)", model: selectedModel)
                await MainActor.run {
                    messages.append(errorMsg)
                    isGenerating = false
                }
            }
        }
    }
}
