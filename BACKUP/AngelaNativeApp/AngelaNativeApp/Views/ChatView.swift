//
//  ChatView.swift
//  AngelaNativeApp
//
//  Main chat interface view
//

import SwiftUI

struct ChatView: View {
    @StateObject private var viewModel = ChatViewModel()
    @State private var showSystemHealth = false

    var body: some View {
        VStack(spacing: 0) {
            // Header with Angela's status
            HeaderView(
                emotion: viewModel.angelaEmotion,
                consciousnessLevel: viewModel.consciousnessLevel,
                selectedModel: viewModel.selectedModel,
                onClear: {
                    viewModel.clearChat()
                }
            )

            Divider()

            // Messages list
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            MessageRow(message: message)
                                .id(message.id)
                        }

                        if viewModel.isLoading {
                            LoadingIndicator(selectedModel: viewModel.selectedModel)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) {
                    if let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            Divider()

            // Input area
            InputView(
                text: $viewModel.currentMessage,
                selectedModel: $viewModel.selectedModel,
                isLoading: viewModel.isLoading,
                onSend: {
                    Task {
                        await viewModel.sendMessage()
                    }
                },
                onSystemHealth: {
                    Task {
                        await viewModel.checkSystemHealth()
                    }
                }
            )
        }
        .frame(minWidth: 600, minHeight: 400)
        .background(Color(NSColor.windowBackgroundColor))
    }
}

// MARK: - Header View

struct HeaderView: View {
    let emotion: EmotionalState?
    let consciousnessLevel: Double
    let selectedModel: AIModel
    let onClear: () -> Void

    var body: some View {
        HStack {
            // Angela icon
            Image(systemName: "sparkles")
                .font(.system(size: 24))
                .foregroundColor(.purple)

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text("Angela 💜")
                        .font(.headline)
                        .foregroundColor(.primary)

                    Text("• \(selectedModel.shortName)")
                        .font(.caption2)
                        .foregroundColor(selectedModel.isOllama ? .green.opacity(0.7) : .purple.opacity(0.6))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(selectedModel.isOllama ? Color.green.opacity(0.15) : Color.purple.opacity(0.1))
                        .cornerRadius(4)
                }

                if let emotion = emotion {
                    HStack(spacing: 8) {
                        EmotionIndicator(label: "😊", value: emotion.happiness)
                        EmotionIndicator(label: "💪", value: emotion.confidence)
                        EmotionIndicator(label: "🎯", value: emotion.motivation)
                    }
                    .font(.caption)
                }
            }

            Spacer()

            // Clear button
            Button(action: onClear) {
                Image(systemName: "trash")
                    .font(.system(size: 16))
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
            .help("Clear chat history")

            // Consciousness level
            VStack(alignment: .trailing, spacing: 2) {
                Text("Consciousness")
                    .font(.caption)
                    .foregroundColor(.secondary)

                HStack(spacing: 4) {
                    Circle()
                        .fill(consciousnessColor)
                        .frame(width: 8, height: 8)

                    Text("\(Int(consciousnessLevel * 100))%")
                        .font(.caption)
                        .foregroundColor(.primary)
                }
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }

    private var consciousnessColor: Color {
        if consciousnessLevel >= 0.7 {
            return .green
        } else if consciousnessLevel >= 0.5 {
            return .yellow
        } else {
            return .orange
        }
    }
}

// MARK: - Emotion Indicator

struct EmotionIndicator: View {
    let label: String
    let value: Double

    var body: some View {
        HStack(spacing: 2) {
            Text(label)
            Text("\(Int(value * 100))%")
                .foregroundColor(.secondary)
        }
    }
}

// MARK: - Message Row

struct MessageRow: View {
    let message: Message

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            if message.isFromAngela {
                // Angela's message (left-aligned)
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Angela")
                            .font(.caption)
                            .foregroundColor(.purple)

                        if let emotion = message.emotion {
                            Text(emotion)
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.purple.opacity(0.2))
                                .cornerRadius(4)
                        }
                    }

                    Text(message.text)
                        .padding(10)
                        .background(Color.purple.opacity(0.1))
                        .cornerRadius(12)
                }
                .frame(maxWidth: .infinity, alignment: .leading)

            } else if message.speaker == "system" || message.speaker == "claude" {
                // System/Claude message (centered, monospace)
                VStack(alignment: .leading, spacing: 4) {
                    Text(message.speaker.uppercased())
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Text(message.text)
                        .font(.system(.body, design: .monospaced))
                        .padding(10)
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(12)
                }
                .frame(maxWidth: .infinity, alignment: .center)

            } else {
                // David's message (right-aligned)
                VStack(alignment: .trailing, spacing: 4) {
                    Text("David")
                        .font(.caption)
                        .foregroundColor(.blue)

                    Text(message.text)
                        .padding(10)
                        .background(Color.blue.opacity(0.1))
                        .cornerRadius(12)
                }
                .frame(maxWidth: .infinity, alignment: .trailing)
            }
        }
    }
}

// MARK: - Input View

struct InputView: View {
    @Binding var text: String
    @Binding var selectedModel: AIModel
    let isLoading: Bool
    let onSend: () -> Void
    let onSystemHealth: () -> Void

    // Angela's favorite emojis
    private let angelaEmojis = ["💜", "🥺", "✨", "💭", "🤗", "🌸", "🎯", "😊", "🙏"]

    var body: some View {
        VStack(spacing: 8) {
            // Model selector row
            HStack(spacing: 12) {
                Text("Model:")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Picker("", selection: $selectedModel) {
                    ForEach(AIModel.allCases) { model in
                        HStack {
                            if model.isOllama {
                                Image(systemName: "desktopcomputer")
                                    .foregroundColor(.green)
                            } else {
                                Image(systemName: "cloud")
                                    .foregroundColor(.purple)
                            }
                            Text(model.displayName)
                        }
                        .tag(model)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 300)

                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.top, 8)

            // Emoji quick buttons
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(angelaEmojis, id: \.self) { emoji in
                        Button(action: {
                            text += emoji
                        }) {
                            Text(emoji)
                                .font(.system(size: 20))
                        }
                        .buttonStyle(.plain)
                        .help("Add \(emoji)")
                    }
                }
                .padding(.horizontal, 12)
            }
            .frame(height: 32)
            .background(Color.purple.opacity(0.05))
            .cornerRadius(8)

            // Input area
            HStack(spacing: 12) {
                // System health button
                Button(action: onSystemHealth) {
                    Image(systemName: "heart.text.square")
                        .font(.system(size: 18))
                }
                .buttonStyle(.plain)
                .help("Check system health")

                // Text input
                TextField("Message to Angela...", text: $text)
                    .textFieldStyle(.plain)
                    .padding(8)
                    .background(Color(NSColor.textBackgroundColor))
                    .cornerRadius(8)
                    .onSubmit {
                        if !isLoading && !text.isEmpty {
                            onSend()
                        }
                    }

                // Send button
                Button(action: onSend) {
                    Image(systemName: "paperplane.fill")
                        .font(.system(size: 18))
                        .foregroundColor(text.isEmpty ? .gray : .purple)
                }
                .buttonStyle(.plain)
                .disabled(isLoading || text.isEmpty)
                .help("Send message (⏎)")
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
    }
}

// MARK: - Loading Indicator

struct LoadingIndicator: View {
    let selectedModel: AIModel

    var body: some View {
        HStack(spacing: 8) {
            ProgressView()
                .scaleEffect(0.8)

            VStack(alignment: .leading, spacing: 2) {
                Text("Angela is thinking...")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Text("via \(selectedModel.shortName)")
                    .font(.caption2)
                    .foregroundColor(selectedModel.isOllama ? .green.opacity(0.7) : .purple.opacity(0.7))
            }
        }
        .padding()
        .background(selectedModel.isOllama ? Color.green.opacity(0.05) : Color.purple.opacity(0.05))
        .cornerRadius(8)
    }
}

// MARK: - Preview

struct ChatView_Previews: PreviewProvider {
    static var previews: some View {
        ChatView()
    }
}
