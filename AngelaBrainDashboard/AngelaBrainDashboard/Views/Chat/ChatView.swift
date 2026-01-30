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
    @State private var newMessage: String = ""
    @State private var isLoading = false
    @State private var selectedModel: String = "gemini"
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

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // Input area
                messageInput
            }
        }
        .onAppear {
            loadRecentMessages()
            Task {
                await chatService.checkOnlineStatus()
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
                        .fill(chatService.isOnline ? AngelaTheme.successGreen : AngelaTheme.errorRed)
                        .frame(width: 8, height: 8)

                    Text(chatService.isOnline ? "Online" : "Offline")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)

                    if chatService.isOnline {
                        Menu {
                            Button {
                                selectedModel = "gemini"
                            } label: {
                                Label("Gemini 2.5 Flash", systemImage: "sparkle")
                            }
                            Button {
                                selectedModel = "groq"
                            } label: {
                                Label("Groq Llama 70B", systemImage: "bolt.fill")
                            }
                            Button {
                                selectedModel = "typhoon"
                            } label: {
                                Label("Typhoon Local", systemImage: "hurricane")
                            }
                        } label: {
                            ModelBadge(model: selectedModel)
                        }
                        .menuStyle(.borderlessButton)
                        .fixedSize()
                    }
                }
            }

            Spacer()

            // Refresh status button
            Button {
                Task { await chatService.checkOnlineStatus() }
            } label: {
                Image(systemName: "arrow.counterclockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple.opacity(0.8))
                    .padding(8)
                    .background(AngelaTheme.cardBackground.opacity(0.5))
                    .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .help("Refresh connection status")

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
            // Send message and get response via selected model
            await chatService.sendMessage(messageText, speaker: "david", model: selectedModel)

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
        // Strong signals — any single match is enough
        let strongKeywords = [
            "code", "feature", "fix bug", "error", "implement", "refactor",
            "database", "deploy", "commit", "debug", "api", "endpoint",
            "แก้ bug", "แก้ code", "แก้โค้ด", "เขียนโค้ด", "เขียน code",
            "สร้าง api", "สร้าง feature", "รัน test", "รัน server",
        ]
        // Weak signals — need 2+ matches to trigger
        let weakKeywords = [
            "ช่วยเขียน", "ช่วยแก้", "ช่วยทำ", "เพิ่ม function",
            "เพิ่ม feature", "แก้ไข", "สร้างไฟล์", "ทำระบบ",
        ]

        let lowercased = message.lowercased()

        // Any strong keyword → technical
        if strongKeywords.contains(where: { lowercased.contains($0) }) {
            return true
        }

        // 2+ weak keywords → technical
        let weakCount = weakKeywords.filter { lowercased.contains($0) }.count
        return weakCount >= 2
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
                // Message content (with code block formatting)
                FormattedMessageView(
                    text: message.messageText,
                    textColor: message.isDavid ? .white : AngelaTheme.textPrimary
                )
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

                // Timestamp, model tag, emotion, and feedback buttons
                HStack(spacing: 8) {
                    if let emotion = message.emotionDetected, !emotion.isEmpty {
                        Text(emotionEmoji(emotion))
                            .font(.system(size: 12))
                    }

                    Text(message.createdAt.formatted(date: .omitted, time: .shortened))
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    // Model tag (only for Angela's messages with model info)
                    if message.isAngela, let modelName = message.modelUsed, !modelName.isEmpty {
                        MessageModelTag(model: modelName)
                    }

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

// MARK: - Model Badge (tappable — shows selected LLM)

struct ModelBadge: View {
    let model: String

    private var badgeColor: Color {
        switch model {
        case "typhoon": return Color(hex: "10B981")   // Green for local
        case "groq":    return Color(hex: "F97316")   // Orange for Groq
        default:        return Color(hex: "4285F4")   // Google Blue
        }
    }

    private var iconName: String {
        switch model {
        case "typhoon": return "hurricane"
        case "groq":    return "bolt.fill"
        default:        return "sparkle"
        }
    }

    private var label: String {
        switch model {
        case "typhoon": return "Typhoon Local"
        case "groq":    return "Groq Llama 70B"
        default:        return "Gemini 2.5 Flash"
        }
    }

    private var trailingIcon: String {
        switch model {
        case "typhoon": return "🏠"
        case "groq":    return "⚡"
        default:        return "⚡"
        }
    }

    private var helpText: String {
        switch model {
        case "typhoon": return "Typhoon 2.5 — Local Ollama"
        case "groq":    return "Groq — Llama 3.3 70B (Free Cloud)"
        default:        return "Gemini 2.5 Flash — Google AI"
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: iconName)
                .font(.system(size: 10))

            Text(label)
                .font(AngelaTheme.caption())

            Text(trailingIcon)
                .font(.system(size: 10))

            Image(systemName: "chevron.down")
                .font(.system(size: 8, weight: .semibold))
                .opacity(0.6)
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
        .help(helpText)
    }
}

// MARK: - Message Model Tag (per-message indicator)

struct MessageModelTag: View {
    let model: String

    private var tagColor: Color {
        let m = model.lowercased()
        if m.contains("gemini") { return Color(hex: "4285F4") }
        if m.contains("llama") || m.contains("groq") { return Color(hex: "F97316") }
        return Color(hex: "10B981")  // Typhoon / other
    }

    private var tagLabel: String {
        let m = model.lowercased()
        if m.contains("gemini") { return "Gemini" }
        if m.contains("llama")  { return "Groq" }
        if m.contains("typhoon") { return "Typhoon" }
        return model
    }

    private var tagIcon: String {
        let m = model.lowercased()
        if m.contains("gemini") { return "sparkle" }
        if m.contains("llama") || m.contains("groq") { return "bolt.fill" }
        return "hurricane"
    }

    var body: some View {
        HStack(spacing: 2) {
            Image(systemName: tagIcon)
                .font(.system(size: 8))
            Text(tagLabel)
                .font(.system(size: 9, weight: .medium))
        }
        .foregroundColor(tagColor)
        .padding(.horizontal, 5)
        .padding(.vertical, 2)
        .background(tagColor.opacity(0.15))
        .cornerRadius(4)
    }
}

// MARK: - Formatted Message View (code block support)

/// A message segment: either plain text or a code block.
private struct MessageSegment: Identifiable {
    let id = UUID()
    let isCode: Bool
    let language: String?
    let content: String
}

struct FormattedMessageView: View {
    let text: String
    let textColor: Color

    private var segments: [MessageSegment] {
        var result: [MessageSegment] = []
        let parts = text.components(separatedBy: "```")

        for (index, part) in parts.enumerated() {
            let trimmed = part.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { continue }

            if index % 2 == 1 {
                // Inside ``` block — first line may be language hint
                let lines = part.split(separator: "\n", maxSplits: 1, omittingEmptySubsequences: false)
                let firstLine = String(lines.first ?? "").trimmingCharacters(in: .whitespacesAndNewlines)

                // Check if first line is a language tag (short, no spaces, ascii)
                let isLangTag = !firstLine.isEmpty
                    && firstLine.count <= 15
                    && !firstLine.contains(" ")
                    && firstLine.allSatisfy({ $0.isASCII })

                if isLangTag && lines.count > 1 {
                    let code = String(lines[1]).trimmingCharacters(in: .whitespacesAndNewlines)
                    result.append(MessageSegment(isCode: true, language: firstLine, content: code))
                } else {
                    result.append(MessageSegment(isCode: true, language: nil, content: trimmed))
                }
            } else {
                result.append(MessageSegment(isCode: false, language: nil, content: trimmed))
            }
        }
        return result
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(segments) { segment in
                if segment.isCode {
                    // Code block
                    VStack(alignment: .leading, spacing: 4) {
                        if let lang = segment.language {
                            Text(lang)
                                .font(.system(size: 10, weight: .bold, design: .monospaced))
                                .foregroundColor(.white.opacity(0.5))
                        }
                        ScrollView(.horizontal, showsIndicators: false) {
                            Text(segment.content)
                                .font(.system(size: 12, design: .monospaced))
                                .foregroundColor(.green.opacity(0.9))
                                .textSelection(.enabled)
                        }
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.black.opacity(0.85))
                    .cornerRadius(8)
                } else {
                    // Normal text
                    Text(segment.content)
                        .font(AngelaTheme.body())
                        .foregroundColor(textColor)
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    ChatView()
        .environmentObject(DatabaseService.shared)
}
