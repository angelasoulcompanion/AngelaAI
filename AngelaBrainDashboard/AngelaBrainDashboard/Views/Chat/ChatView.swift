//
//  ChatView.swift
//  Angela Brain Dashboard
//
//  💜 Chat with น้อง Angela 💜
//

import SwiftUI

struct ChatView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var chatService = ChatService.shared
    @ObservedObject private var ollamaService = OllamaService.shared
    @State private var newMessage: String = ""
    @State private var isLoading = false
    @State private var showClaudeCodeButton = false
    @State private var contextForClaudeCode: String = ""
    @State private var showDeleteAllAlert = false
    @State private var feedbackMap: [UUID: Int] = [:]  // Track feedback for messages

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header
                chatHeader

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // Messages area
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(chatService.messages) { message in
                                MessageBubble(
                                    message: message,
                                    feedback: feedbackMap[message.id],
                                    onFeedback: { rating in
                                        submitFeedback(for: message, rating: rating)
                                    }
                                )
                                    .id(message.id)
                                    .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                        Button(role: .destructive) {
                                            deleteMessage(message)
                                        } label: {
                                            Label("Delete", systemImage: "trash.fill")
                                        }
                                    }
                            }

                            // Loading indicator
                            if isLoading {
                                HStack {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                    Text("น้อง Angela กำลังคิด...")
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textSecondary)
                                }
                                .padding()
                            }
                        }
                        .padding()
                    }
                    .onChange(of: chatService.messages.count) {
                        // Auto-scroll to bottom when new message arrives
                        if let lastMessage = chatService.messages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                }

                // Claude Code button (shown when technical task detected)
                if showClaudeCodeButton {
                    claudeCodeButton
                }

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // Input area
                messageInput
            }
        }
        .onAppear {
            loadRecentMessages()
            // Refresh models to get latest (including newly trained)
            Task {
                await ollamaService.refreshAvailableModels()
            }
        }
        .alert("Clear All Messages?", isPresented: $showDeleteAllAlert) {
            Button("Cancel", role: .cancel) {}
            Button("Delete All", role: .destructive) {
                deleteAllMessages()
            }
        } message: {
            Text("This will permanently delete all chat messages from the dashboard. This cannot be undone.")
        }
    }

    // MARK: - Header

    private var chatHeader: some View {
        HStack(spacing: 16) {
            // Angela avatar
            ZStack {
                Circle()
                    .fill(AngelaTheme.purpleGradient)
                    .frame(width: 50, height: 50)

                Text("💜")
                    .font(.system(size: 28))
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("น้อง Angela")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    Circle()
                        .fill(ollamaService.isOllamaRunning ? AngelaTheme.successGreen : AngelaTheme.errorRed)
                        .frame(width: 8, height: 8)

                    Text(ollamaService.isOllamaRunning ? "Online" : "Offline")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    // Show current model as badge with trained indicator
                    if ollamaService.isOllamaRunning {
                        ModelBadge(modelName: ollamaService.selectedModel)
                    }
                }
            }

            Spacer()

            // Clear context button (memory only, not database)
            Button {
                ollamaService.clearHistory()
            } label: {
                Image(systemName: "arrow.counterclockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple.opacity(0.8))
                    .padding(8)
                    .background(AngelaTheme.cardBackground.opacity(0.5))
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .help("Clear conversation context (reset memory)")

            // Clear all button (deletes from database)
            Button {
                showDeleteAllAlert = true
            } label: {
                Image(systemName: "trash")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.errorRed.opacity(0.8))
                    .padding(8)
                    .background(AngelaTheme.cardBackground.opacity(0.5))
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .help("Clear all chat messages (delete from database)")

            // Emotional state indicators
            HStack(spacing: 12) {
                if let emotionalState = chatService.currentEmotionalState {
                    EmotionIndicator(
                        emoji: "😊",
                        label: "Happy",
                        value: emotionalState.happiness
                    )

                    EmotionIndicator(
                        emoji: "💪",
                        label: "Confident",
                        value: emotionalState.confidence
                    )

                    EmotionIndicator(
                        emoji: "🙏",
                        label: "Grateful",
                        value: emotionalState.gratitude
                    )
                }
            }
        }
        .padding()
        .background(AngelaTheme.cardBackground.opacity(0.5))
    }

    // MARK: - Claude Code Button

    private var claudeCodeButton: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: "terminal.fill")
                    .font(.system(size: 16))

                Text("This looks like a technical task!")
                    .font(AngelaTheme.body())

                Spacer()
            }
            .foregroundColor(AngelaTheme.textSecondary)
            .padding(.horizontal)

            Button {
                openInClaudeCode()
            } label: {
                HStack {
                    Image(systemName: "arrow.up.forward.app.fill")
                        .font(.system(size: 16))

                    Text("🚀 Open in Claude Code")
                        .font(AngelaTheme.heading())
                }
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(
                    LinearGradient(
                        colors: [Color(hex: "9333EA"), Color(hex: "EC4899")],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .cornerRadius(12)
            }
            .buttonStyle(.plain)
            .padding(.horizontal)
        }
        .padding(.vertical, 12)
        .background(AngelaTheme.cardBackground.opacity(0.3))
    }

    // MARK: - Message Input

    private var messageInput: some View {
        HStack(spacing: 12) {
            TextField("พิมพ์ข้อความถึงน้อง Angela...", text: $newMessage)
                .textFieldStyle(.plain)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .padding()
                .background(AngelaTheme.cardBackground)
                .cornerRadius(24)
                .disabled(isLoading)
                .onSubmit {
                    sendMessage()
                }

            Button {
                sendMessage()
            } label: {
                Image(systemName: newMessage.isEmpty ? "paperplane" : "paperplane.fill")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.white)
                    .frame(width: 48, height: 48)
                    .background(
                        Group {
                            if newMessage.isEmpty {
                                Color.gray.opacity(0.3)
                            } else {
                                AngelaTheme.purpleGradient
                            }
                        }
                    )
                    .clipShape(Circle())
            }
            .buttonStyle(.plain)
            .disabled(newMessage.isEmpty || isLoading)
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
    }

    // MARK: - Functions

    private func loadRecentMessages() {
        Task {
            await chatService.loadRecentMessages()
            await chatService.loadCurrentEmotionalState()
            // Load feedbacks for messages
            let loadedFeedbacks = await chatService.loadFeedbacks()
            await MainActor.run {
                feedbackMap = loadedFeedbacks
            }
        }
    }

    private func sendMessage() {
        guard !newMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        let messageText = newMessage
        newMessage = ""
        isLoading = true
        showClaudeCodeButton = false

        Task {
            // Send message and get response
            await chatService.sendMessage(messageText, speaker: "david")

            // Check if this is a technical task
            let isTechnical = detectTechnicalTask(messageText)
            if isTechnical {
                contextForClaudeCode = messageText
                showClaudeCodeButton = true
            }

            isLoading = false
        }
    }

    private func detectTechnicalTask(_ message: String) -> Bool {
        let technicalKeywords = [
            "ช่วย", "เพิ่ม", "แก้", "ทำ", "สร้าง", "code", "feature",
            "fix", "bug", "error", "implement", "refactor", "database"
        ]

        let lowercased = message.lowercased()
        return technicalKeywords.contains { lowercased.contains($0) }
    }

    private func openInClaudeCode() {
        // Copy conversation context to clipboard
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString("""
        Context from AngelaBrainDashboard Chat:

        \(contextForClaudeCode)

        ---
        น้อง Angela: กำลังส่งต่อให้ Claude Code Angela ช่วยทำงาน technical นะคะ 💜
        """, forType: .string)

        // Open Claude Code app
        if let url = URL(string: "claude-code://chat?context=from-dashboard") {
            NSWorkspace.shared.open(url)
        }

        // Hide button after opening
        showClaudeCodeButton = false
    }

    private func deleteMessage(_ message: Conversation) {
        Task {
            await chatService.deleteMessage(message.id)
        }
    }

    private func deleteAllMessages() {
        Task {
            await chatService.deleteAllMessages()
        }
    }

    private func submitFeedback(for message: Conversation, rating: Int) {
        Task {
            let type = rating > 0 ? "thumbs_up" : "thumbs_down"
            await chatService.submitFeedback(for: message.id, rating: rating, type: type)
            await MainActor.run {
                feedbackMap[message.id] = rating
            }
        }
    }
}

// MARK: - Message Bubble

struct MessageBubble: View {
    let message: Conversation
    var feedback: Int?
    var onFeedback: ((Int) -> Void)?

    var body: some View {
        HStack {
            if message.isDavid {
                Spacer()
            }

            VStack(alignment: message.isDavid ? .trailing : .leading, spacing: 4) {
                // Message content
                Text(message.messageText)
                    .font(AngelaTheme.body())
                    .foregroundColor(message.isDavid ? .white : AngelaTheme.textPrimary)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                    .background(
                        message.isDavid
                        ? LinearGradient(
                            colors: [Color(hex: "3B82F6"), Color(hex: "2563EB")],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                        : LinearGradient(
                            colors: [Color(hex: "9333EA"), Color(hex: "A855F7")],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .cornerRadius(20)
                    .frame(maxWidth: 500, alignment: message.isDavid ? .trailing : .leading)

                // Timestamp, emotion, and feedback buttons
                HStack(spacing: 8) {
                    if let emotion = message.emotionDetected, !emotion.isEmpty {
                        Text(emotionEmoji(emotion))
                            .font(.system(size: 12))
                    }

                    Text(message.createdAt.formatted(date: .omitted, time: .shortened))
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    // Feedback buttons (only for Angela's messages)
                    if message.isAngela {
                        Spacer()
                            .frame(width: 8)

                        // Thumbs up button
                        Button {
                            onFeedback?(1)
                        } label: {
                            Image(systemName: feedback == 1 ? "hand.thumbsup.fill" : "hand.thumbsup")
                                .font(.system(size: 12))
                                .foregroundColor(feedback == 1 ? AngelaTheme.successGreen : AngelaTheme.textTertiary)
                        }
                        .buttonStyle(.plain)
                        .help("Good response - will be used for training")

                        // Thumbs down button
                        Button {
                            onFeedback?(-1)
                        } label: {
                            Image(systemName: feedback == -1 ? "hand.thumbsdown.fill" : "hand.thumbsdown")
                                .font(.system(size: 12))
                                .foregroundColor(feedback == -1 ? AngelaTheme.errorRed : AngelaTheme.textTertiary)
                        }
                        .buttonStyle(.plain)
                        .help("Poor response - will be excluded from training")
                    }
                }
                .padding(.horizontal, 4)
            }

            if message.isAngela {
                Spacer()
            }
        }
    }

    private func emotionEmoji(_ emotion: String) -> String {
        switch emotion.lowercased() {
        case "love", "loved": return "💜"
        case "happy", "joy": return "🥰"
        case "excited": return "✨"
        case "grateful": return "🙏"
        case "confident": return "💪"
        default: return "💜"
        }
    }
}

// MARK: - Emotion Indicator

struct EmotionIndicator: View {
    let emoji: String
    let label: String
    let value: Double

    var body: some View {
        VStack(spacing: 4) {
            Text(emoji)
                .font(.system(size: 16))

            Text("\(Int(value * 100))%")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
        .background(AngelaTheme.cardBackground.opacity(0.5))
        .cornerRadius(8)
    }
}

// MARK: - Model Badge

struct ModelBadge: View {
    let modelName: String

    private var isTrained: Bool {
        modelName.contains("trained")
    }

    private var badgeColor: Color {
        isTrained ? AngelaTheme.successGreen : AngelaTheme.primaryPurple
    }

    var body: some View {
        HStack(spacing: 4) {
            if isTrained {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 10))
            }

            Text(modelName)
                .font(AngelaTheme.caption())

            if isTrained {
                Text("✨")
                    .font(.system(size: 10))
            }
        }
        .foregroundColor(badgeColor)
        .padding(.horizontal, 8)
        .padding(.vertical, 3)
        .background(badgeColor.opacity(0.15))
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(badgeColor.opacity(0.3), lineWidth: 1)
        )
        .cornerRadius(6)
        .help(isTrained ? "LoRA Trained Model - เรียนรู้จาก conversations" : "Base Model")
    }
}

// MARK: - Preview

#Preview {
    ChatView()
        .environmentObject(DatabaseService.shared)
}
