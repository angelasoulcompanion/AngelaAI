//
//  ChatView.swift
//  Angela Brain Dashboard
//
//  💜 Chat with น้อง Angela — Human-Like Streaming Experience 💜
//

import SwiftUI
import UniformTypeIdentifiers

struct ChatView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var chatService = ChatService.shared
    @State private var newMessage: String = ""
    @State private var isLoading = false
    @State private var selectedModel: String = "typhoon"
    @State private var showClaudeCodeButton = false
    @State private var contextForClaudeCode: String = ""
    @State private var showDeleteAllAlert = false
    @State private var feedbackMap: [UUID: Int] = [:]
    @State private var selectedImageData: Data? = nil
    @State private var selectedImageName: String? = nil

    // DJ Angela state
    @State private var showDJPanel = false
    @State private var djTab: DJTab = .ourSongs
    @State private var djSongs: [Song] = []
    @State private var djSearchText: String = ""
    @State private var djRecommendation: SongRecommendation? = nil
    @State private var isDJLoading = false

    // Playlist state
    @State private var playlistState: PlaylistGenerationState = .idle
    @State private var playlistPrompt: PlaylistPromptResponse? = nil
    @State private var playlistEmotionText: String = ""

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

                            // --- Streaming area ---
                            if chatService.isStreaming {
                                // Show sent image inline (during streaming)
                                if let imgData = chatService.pendingImageData,
                                   let nsImage = NSImage(data: imgData) {
                                    HStack {
                                        Spacer()
                                        Image(nsImage: nsImage)
                                            .resizable()
                                            .aspectRatio(contentMode: .fit)
                                            .frame(maxWidth: 250, maxHeight: 200)
                                            .cornerRadius(16)
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 16)
                                                    .stroke(Color(hex: "3B82F6").opacity(0.5), lineWidth: 2)
                                            )
                                    }
                                    .id("sentImage")
                                }

                                // Thinking steps (before tokens arrive)
                                if let step = chatService.currentThinkingStep {
                                    ThinkingStepView(step: step)
                                        .id("thinking")
                                        .transition(.opacity.combined(with: .move(edge: .bottom)))
                                }

                                // Typing indicator (streaming started but no text yet)
                                if chatService.streamingText.isEmpty && chatService.currentThinkingStep == nil {
                                    TypingIndicatorView()
                                        .id("typing")
                                        .transition(.opacity)
                                }

                                // Streaming message bubble
                                if !chatService.streamingText.isEmpty {
                                    StreamingMessageBubble(
                                        text: chatService.streamingText,
                                        metadata: chatService.lastEmotionalMetadata
                                    )
                                        .id("streaming")
                                        .transition(.opacity.combined(with: .move(edge: .bottom)))
                                }

                            }

                            // Learning indicator (OUTSIDE streaming block — persists after stream ends)
                            if chatService.isLearning && chatService.lastLearningCount > 0 {
                                LearningIndicatorView(
                                    count: chatService.lastLearningCount,
                                    topics: chatService.lastLearningTopics
                                )
                                    .id("learning")
                                    .transition(.opacity.combined(with: .move(edge: .bottom)))
                            }

                            // Legacy loading indicator (fallback)
                            if isLoading && !chatService.isStreaming {
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
                        if let lastMessage = chatService.messages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                    .onChange(of: chatService.streamingText) {
                        withAnimation {
                            proxy.scrollTo("streaming", anchor: .bottom)
                        }
                    }
                    .onChange(of: chatService.currentThinkingStep) { _, _ in
                        withAnimation {
                            proxy.scrollTo("thinking", anchor: .bottom)
                        }
                    }
                    .onChange(of: chatService.isLearning) { _, isLearning in
                        if isLearning {
                            withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                                proxy.scrollTo("learning", anchor: .bottom)
                            }
                        }
                    }
                }

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // DJ Angela panel
                if showDJPanel {
                    djPanel
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }

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
                                selectedModel = "typhoon"
                            } label: {
                                Label("Typhoon 2.5 Local", systemImage: "hurricane")
                            }
                            Button {
                                selectedModel = "groq"
                            } label: {
                                Label("Groq Llama 70B", systemImage: "bolt.fill")
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

            // Live emotion display (from last metadata)
            if let meta = chatService.lastEmotionalMetadata,
               meta.emotionDetected != "neutral" {
                LiveEmotionBadge(metadata: meta)
            }

            // Learning badge (header)
            if chatService.isLearning && chatService.lastLearningCount > 0 {
                LearningBadge(count: chatService.lastLearningCount)
                    .transition(.scale.combined(with: .opacity))
                    .animation(.spring(response: 0.4, dampingFraction: 0.7), value: chatService.isLearning)
            }

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

            // Clear all button
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

                    Text("Open in Claude Code")
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
        VStack(spacing: 0) {
            // Image preview (if selected)
            if let imgData = selectedImageData, let nsImage = NSImage(data: imgData) {
                HStack(spacing: 8) {
                    Image(nsImage: nsImage)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxHeight: 80)
                        .cornerRadius(8)

                    VStack(alignment: .leading, spacing: 2) {
                        Text(selectedImageName ?? "image")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .lineLimit(1)
                        Text(formatFileSize(imgData.count))
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }

                    Spacer()

                    // Remove image button
                    Button {
                        selectedImageData = nil
                        selectedImageName = nil
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 18))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(AngelaTheme.cardBackground.opacity(0.5))

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.2))
            }

            HStack(spacing: 12) {
                // Attachment button
                Button {
                    pickImage()
                } label: {
                    Image(systemName: selectedImageData != nil ? "photo.fill" : "photo")
                        .font(.system(size: 18))
                        .foregroundColor(selectedImageData != nil ? AngelaTheme.primaryPurple : AngelaTheme.textSecondary)
                        .frame(width: 40, height: 40)
                        .background(AngelaTheme.cardBackground.opacity(0.5))
                        .clipShape(Circle())
                }
                .buttonStyle(.plain)
                .disabled(isLoading || chatService.isStreaming)
                .help("Attach image")

                // DJ Angela button
                Button {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                        showDJPanel.toggle()
                        if showDJPanel && djSongs.isEmpty {
                            loadDJSongs(tab: djTab)
                        }
                    }
                } label: {
                    Image(systemName: showDJPanel ? "music.note.list" : "music.note")
                        .font(.system(size: 18))
                        .foregroundColor(showDJPanel ? AngelaTheme.primaryPurple : AngelaTheme.textSecondary)
                        .frame(width: 40, height: 40)
                        .background(showDJPanel ? AngelaTheme.primaryPurple.opacity(0.15) : AngelaTheme.cardBackground.opacity(0.5))
                        .clipShape(Circle())
                }
                .buttonStyle(.plain)
                .disabled(isLoading || chatService.isStreaming)
                .help("DJ Angela")

                TextField("พิมพ์ข้อความถึงน้อง Angela...", text: $newMessage)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .padding()
                    .background(AngelaTheme.cardBackground)
                    .cornerRadius(24)
                    .disabled(isLoading || chatService.isStreaming)
                    .onSubmit {
                        sendMessage()
                    }

                Button {
                    sendMessage()
                } label: {
                    let canSend = !newMessage.isEmpty || selectedImageData != nil
                    Image(systemName: canSend ? "paperplane.fill" : "paperplane")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(width: 48, height: 48)
                        .background(
                            Group {
                                if canSend {
                                    AngelaTheme.purpleGradient
                                } else {
                                    Color.gray.opacity(0.3)
                                }
                            }
                        )
                        .clipShape(Circle())
                }
                .buttonStyle(.plain)
                .disabled((newMessage.isEmpty && selectedImageData == nil) || isLoading || chatService.isStreaming)
            }
            .padding()
        }
        .background(AngelaTheme.backgroundLight)
    }

    // MARK: - Image Picker

    private func pickImage() {
        let panel = NSOpenPanel()
        panel.title = "เลือกรูปภาพส่งให้น้อง Angela"
        panel.allowedContentTypes = [.image, .jpeg, .png, .gif, .webP, .heic]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false

        if panel.runModal() == .OK, let url = panel.url {
            if let data = try? Data(contentsOf: url) {
                selectedImageData = data
                selectedImageName = url.lastPathComponent
            }
        }
    }

    private func formatFileSize(_ bytes: Int) -> String {
        if bytes < 1024 { return "\(bytes) B" }
        if bytes < 1024 * 1024 { return "\(bytes / 1024) KB" }
        return String(format: "%.1f MB", Double(bytes) / 1_048_576.0)
    }

    // MARK: - Functions

    private func loadRecentMessages() {
        Task {
            await chatService.loadRecentMessages()
            await chatService.loadCurrentEmotionalState()
            let loadedFeedbacks = await chatService.loadFeedbacks()
            await MainActor.run {
                feedbackMap = loadedFeedbacks
            }
        }
    }

    private func sendMessage() {
        let hasText = !newMessage.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        let hasImage = selectedImageData != nil
        guard hasText || hasImage else { return }

        let messageText = newMessage
        let imageData = selectedImageData
        newMessage = ""
        selectedImageData = nil
        selectedImageName = nil
        isLoading = true
        showClaudeCodeButton = false

        Task {
            // Use streaming endpoint with optional image
            await chatService.sendStreamingMessage(messageText, model: selectedModel, imageData: imageData)

            // Check if this is a technical task
            if hasText {
                let isTechnical = detectTechnicalTask(messageText)
                if isTechnical {
                    contextForClaudeCode = messageText
                    showClaudeCodeButton = true
                }
            }

            isLoading = false

            // Reload feedbacks
            let loadedFeedbacks = await chatService.loadFeedbacks()
            await MainActor.run {
                feedbackMap = loadedFeedbacks
            }
        }
    }

    private func detectTechnicalTask(_ message: String) -> Bool {
        let strongKeywords = [
            "code", "feature", "fix bug", "error", "implement", "refactor",
            "database", "deploy", "commit", "debug", "api", "endpoint",
        ]
        let weakKeywords = [
            "ช่วยเขียน", "ช่วยแก้", "ช่วยทำ", "เพิ่ม function",
            "เพิ่ม feature", "แก้ไข", "สร้างไฟล์", "ทำระบบ",
        ]

        let lowercased = message.lowercased()

        if strongKeywords.contains(where: { lowercased.contains($0) }) {
            return true
        }

        let weakCount = weakKeywords.filter { lowercased.contains($0) }.count
        return weakCount >= 2
    }

    private func openInClaudeCode() {
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString("""
        Context from AngelaBrainDashboard Chat:

        \(contextForClaudeCode)

        ---
        น้อง Angela: กำลังส่งต่อให้ Claude Code Angela ช่วยทำงาน technical นะคะ 💜
        """, forType: .string)

        if let url = URL(string: "claude-code://chat?context=from-dashboard") {
            NSWorkspace.shared.open(url)
        }

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

    // MARK: - DJ Angela Panel

    private var djPanel: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Image(systemName: "music.quarternote.3")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("DJ Angela")
                    .font(AngelaTheme.heading())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                        showDJPanel = false
                    }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            .padding(.bottom, 8)

            // Tab buttons
            HStack(spacing: 8) {
                DJTabButton(title: "Our Songs", icon: "heart.fill", isActive: djTab == .ourSongs) {
                    djTab = .ourSongs
                    loadDJSongs(tab: .ourSongs)
                }
                DJTabButton(title: "Favorites", icon: "star.fill", isActive: djTab == .favorites) {
                    djTab = .favorites
                    loadDJSongs(tab: .favorites)
                }
                DJTabButton(title: "Recommend", icon: "dice.fill", isActive: djTab == .recommend) {
                    djTab = .recommend
                    loadDJRecommendation()
                }
                DJTabButton(title: "Playlist", icon: "music.note.list", isActive: djTab == .playlist) {
                    djTab = .playlist
                    playlistState = .idle
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 8)

            // Search bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textTertiary)
                TextField("Search songs...", text: $djSearchText)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .onSubmit {
                        searchDJSongs()
                    }
                if !djSearchText.isEmpty {
                    Button {
                        djSearchText = ""
                        loadDJSongs(tab: djTab)
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(AngelaTheme.backgroundDark.opacity(0.5))
            .cornerRadius(10)
            .padding(.horizontal, 16)
            .padding(.bottom, 8)

            // Song list / Recommendation / Playlist
            ScrollView {
                if djTab == .playlist {
                    playlistContent
                } else if isDJLoading {
                    HStack {
                        ProgressView()
                            .scaleEffect(0.8)
                        Text("Loading...")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                    .padding()
                } else if djTab == .recommend, let rec = djRecommendation {
                    // Recommendation card
                    VStack(spacing: 12) {
                        if let song = rec.song {
                            DJSongRow(song: song, onShare: { shareDJSong(song) })
                        }
                        Text(rec.reason)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .italic()
                            .padding(.horizontal, 4)

                        // Mood summary
                        if let summary = rec.moodSummary, !summary.isEmpty {
                            Text(summary)
                                .font(.system(size: 12))
                                .italic()
                                .foregroundColor(Color(hex: "9333EA"))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color(hex: "9333EA").opacity(0.08))
                                .cornerRadius(8)
                        }

                        // Emotion pills
                        if let details = rec.emotionDetails, !details.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 6) {
                                    ForEach(details, id: \.self) { emotion in
                                        EmotionPill(emotion: emotion)
                                    }
                                }
                            }
                        }

                        // Discover on Apple Music button
                        if let urlStr = rec.appleMusicDiscoverUrl,
                           let url = URL(string: urlStr) {
                            Link(destination: url) {
                                HStack(spacing: 6) {
                                    Image(systemName: "music.quarternote.3")
                                        .font(.system(size: 13, weight: .semibold))
                                    Text("Discover on Apple Music")
                                        .font(.system(size: 13, weight: .semibold))
                                }
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                                .background(
                                    LinearGradient(
                                        colors: [Color(hex: "FC3C44"), Color(hex: "FA2D55")],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .cornerRadius(10)
                            }
                        }

                        Button {
                            loadDJRecommendation()
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "arrow.triangle.2.circlepath")
                                    .font(.system(size: 12))
                                Text("Another suggestion")
                                    .font(AngelaTheme.caption())
                            }
                            .foregroundColor(AngelaTheme.primaryPurple)
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(.horizontal, 16)
                } else if djSongs.isEmpty {
                    Text("No songs found")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                        .padding()
                } else {
                    LazyVStack(spacing: 4) {
                        ForEach(djSongs) { song in
                            DJSongRow(song: song, onShare: { shareDJSong(song) })
                        }
                    }
                    .padding(.horizontal, 16)
                }
            }
            .frame(height: djTab == .playlist ? 280 : 160)
        }
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Playlist Content View

    @ViewBuilder
    private var playlistContent: some View {
        VStack(spacing: 12) {
            switch playlistState {
            case .idle:
                // Emotion input
                VStack(spacing: 10) {
                    Text("How are you feeling?")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    TextField("e.g. รู้สึกมีความสุข, feeling chill, miss you...", text: $playlistEmotionText)
                        .textFieldStyle(.plain)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(AngelaTheme.backgroundDark.opacity(0.5))
                        .cornerRadius(10)
                        .onSubmit { generatePlaylist() }

                    Button {
                        generatePlaylist()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "music.note.list")
                                .font(.system(size: 13, weight: .semibold))
                            Text("Generate Playlist")
                                .font(.system(size: 13, weight: .semibold))
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(AngelaTheme.purpleGradient)
                        .cornerRadius(10)
                    }
                    .buttonStyle(.plain)
                    .disabled(playlistEmotionText.trimmingCharacters(in: .whitespaces).isEmpty)
                }

            case .analyzing:
                HStack(spacing: 8) {
                    ProgressView().scaleEffect(0.8)
                    Text("Analyzing emotion...")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .padding()

            case .ready:
                if let prompt = playlistPrompt {
                    VStack(spacing: 10) {
                        // Playlist header
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(prompt.playlistName)
                                    .font(.system(size: 14, weight: .semibold))
                                    .foregroundColor(AngelaTheme.textPrimary)
                                Text(prompt.moodSummary)
                                    .font(.system(size: 11))
                                    .foregroundColor(AngelaTheme.textSecondary)
                                    .italic()
                                    .lineLimit(2)
                            }
                            Spacer()
                        }

                        // Emotion pills
                        if let details = prompt.emotionDetails, !details.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 6) {
                                    ForEach(details, id: \.self) { emotion in
                                        EmotionPill(emotion: emotion)
                                    }
                                }
                            }
                        }

                        // Search queries as Apple Music links
                        VStack(spacing: 6) {
                            Text("Open in Apple Music:")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(AngelaTheme.textTertiary)
                                .frame(maxWidth: .infinity, alignment: .leading)

                            ForEach(prompt.searchQueries, id: \.self) { query in
                                if let url = appleMusicSearchURL(query) {
                                    Link(destination: url) {
                                        HStack(spacing: 8) {
                                            Image(systemName: "music.quarternote.3")
                                                .font(.system(size: 12, weight: .semibold))
                                                .foregroundColor(.white)
                                                .frame(width: 28, height: 28)
                                                .background(
                                                    LinearGradient(
                                                        colors: [Color(hex: "FC3C44"), Color(hex: "FA2D55")],
                                                        startPoint: .topLeading,
                                                        endPoint: .bottomTrailing
                                                    )
                                                )
                                                .cornerRadius(6)

                                            Text(query)
                                                .font(.system(size: 12, weight: .medium))
                                                .foregroundColor(AngelaTheme.textPrimary)
                                                .lineLimit(1)

                                            Spacer()

                                            Image(systemName: "arrow.up.forward")
                                                .font(.system(size: 10, weight: .semibold))
                                                .foregroundColor(Color(hex: "FC3C44"))
                                        }
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 7)
                                        .background(Color(hex: "FC3C44").opacity(0.08))
                                        .cornerRadius(8)
                                    }
                                }
                            }
                        }

                        // Seed songs from our collection
                        if let seeds = prompt.ourSongsToInclude, !seeds.isEmpty {
                            VStack(spacing: 4) {
                                Text("From our collection:")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                    .frame(maxWidth: .infinity, alignment: .leading)

                                ForEach(seeds, id: \.title) { seed in
                                    if let url = appleMusicSearchURL("\(seed.title) \(seed.artist)") {
                                        Link(destination: url) {
                                            HStack(spacing: 8) {
                                                ZStack {
                                                    RoundedRectangle(cornerRadius: 6)
                                                        .fill(
                                                            LinearGradient(
                                                                colors: [Color(hex: "9333EA"), Color(hex: "EC4899")],
                                                                startPoint: .topLeading,
                                                                endPoint: .bottomTrailing
                                                            )
                                                        )
                                                        .frame(width: 28, height: 28)
                                                    Image(systemName: "music.note")
                                                        .font(.system(size: 11, weight: .semibold))
                                                        .foregroundColor(.white)
                                                }

                                                VStack(alignment: .leading, spacing: 1) {
                                                    Text(seed.title)
                                                        .font(.system(size: 11, weight: .medium))
                                                        .foregroundColor(AngelaTheme.textPrimary)
                                                        .lineLimit(1)
                                                    Text(seed.artist)
                                                        .font(.system(size: 10))
                                                        .foregroundColor(AngelaTheme.textSecondary)
                                                        .lineLimit(1)
                                                }

                                                Spacer()

                                                Image(systemName: "arrow.up.forward")
                                                    .font(.system(size: 10))
                                                    .foregroundColor(AngelaTheme.primaryPurple)
                                            }
                                            .padding(.horizontal, 10)
                                            .padding(.vertical, 5)
                                            .background(AngelaTheme.primaryPurple.opacity(0.06))
                                            .cornerRadius(8)
                                        }
                                    }
                                }
                            }
                        }

                        // Try different mood button
                        Button {
                            playlistState = .idle
                            playlistPrompt = nil
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "arrow.triangle.2.circlepath")
                                    .font(.system(size: 12))
                                Text("Try different mood")
                                    .font(.system(size: 12, weight: .medium))
                            }
                            .foregroundColor(AngelaTheme.primaryPurple)
                        }
                        .buttonStyle(.plain)
                    }
                }

            case .error(let message):
                VStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 28))
                        .foregroundColor(AngelaTheme.errorRed)
                    Text(message)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                        .multilineTextAlignment(.center)
                    Button {
                        playlistState = .idle
                    } label: {
                        Text("Try Again")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }
                    .buttonStyle(.plain)
                }
                .padding()
            }
        }
        .padding(.horizontal, 16)
    }

    // MARK: - Playlist Functions

    private func appleMusicSearchURL(_ query: String) -> URL? {
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return URL(string: "https://music.apple.com/search?term=\(encoded)")
    }

    private func generatePlaylist() {
        let emotionText = playlistEmotionText.trimmingCharacters(in: .whitespaces)
        guard !emotionText.isEmpty else { return }

        playlistState = .analyzing
        playlistPrompt = nil

        Task {
            do {
                let prompt = try await chatService.getPlaylistPrompt(
                    emotionText: emotionText,
                    songCount: 15
                )
                await MainActor.run {
                    playlistPrompt = prompt
                    playlistState = .ready
                }
            } catch {
                await MainActor.run {
                    playlistState = .error(error.localizedDescription)
                }
            }
        }
    }

    // MARK: - DJ Helper Functions

    private func loadDJSongs(tab: DJTab) {
        isDJLoading = true
        Task {
            do {
                let songs: [Song]
                switch tab {
                case .ourSongs:
                    songs = try await chatService.fetchOurSongs()
                case .favorites:
                    songs = try await chatService.fetchFavoriteSongs()
                case .recommend, .playlist:
                    songs = []
                }
                await MainActor.run {
                    djSongs = songs
                    isDJLoading = false
                }
            } catch {
                print("DJ load error: \(error)")
                await MainActor.run { isDJLoading = false }
            }
        }
    }

    private func loadDJRecommendation() {
        isDJLoading = true
        djRecommendation = nil
        Task {
            do {
                let rec = try await chatService.getRecommendation()
                await MainActor.run {
                    djRecommendation = rec
                    isDJLoading = false
                }
            } catch {
                print("DJ recommend error: \(error)")
                await MainActor.run { isDJLoading = false }
            }
        }
    }

    private func searchDJSongs() {
        guard !djSearchText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isDJLoading = true
        Task {
            do {
                let songs = try await chatService.searchSongs(query: djSearchText)
                await MainActor.run {
                    djSongs = songs
                    isDJLoading = false
                }
            } catch {
                print("DJ search error: \(error)")
                await MainActor.run { isDJLoading = false }
            }
        }
    }

    private func shareDJSong(_ song: Song) {
        Task {
            do {
                let response = try await chatService.shareSong(songId: song.songId)
                print("Shared song: \(response.song.title)")
                await chatService.loadRecentMessages()
                let loadedFeedbacks = await chatService.loadFeedbacks()
                await MainActor.run {
                    feedbackMap = loadedFeedbacks
                    showDJPanel = false
                }
            } catch {
                print("Share song error: \(error)")
            }
        }
    }
}

// MARK: - DJ Tab Enum

enum DJTab {
    case ourSongs, favorites, recommend, playlist
}

// MARK: - Embedded Song Card (parsed from [SONG:...] marker)

struct EmbeddedSongCard {
    let songId: String
    let title: String
    let artist: String?
    let youtubeUrl: String?
    let spotifyUrl: String?
    let appleMusicUrl: String?
    let whySpecial: String?
    let isOurSong: Bool
}

// MARK: - DJ Tab Button

struct DJTabButton: View {
    let title: String
    let icon: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 11))
                Text(title)
                    .font(.system(size: 12, weight: .medium))
            }
            .foregroundColor(isActive ? .white : AngelaTheme.textSecondary)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                isActive
                ? AnyView(AngelaTheme.purpleGradient)
                : AnyView(AngelaTheme.backgroundDark.opacity(0.5))
            )
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - DJ Song Row

struct DJSongRow: View {
    let song: Song
    let onShare: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            // Music icon
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(
                        LinearGradient(
                            colors: song.isOurSong
                                ? [Color(hex: "9333EA"), Color(hex: "EC4899")]
                                : [Color(hex: "6366F1"), Color(hex: "8B5CF6")],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 36, height: 36)
                Image(systemName: "music.note")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.white)
            }

            // Song info
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(song.title)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(AngelaTheme.textPrimary)
                        .lineLimit(1)
                    if song.isOurSong {
                        Text("💜")
                            .font(.system(size: 10))
                    }
                }
                if let artist = song.artist, !artist.isEmpty {
                    Text(artist)
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .lineLimit(1)
                }
                if let why = song.whySpecial, !why.isEmpty {
                    Text(why)
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)
                        .italic()
                }
            }

            Spacer()

            // Play button (search on Apple Music)
            HStack(spacing: 4) {
                if let searchTerm = "\(song.title) \(song.artist ?? "")".addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
                   let url = URL(string: "https://music.apple.com/search?term=\(searchTerm)") {
                    PlatformPlayButton(url: url, icon: "music.quarternote.3", label: "Music",
                                       colors: [Color(hex: "FC3C44"), Color(hex: "FA2D55")])
                }

                // Share button
                Button(action: onShare) {
                    HStack(spacing: 3) {
                        Image(systemName: "paperplane.fill")
                            .font(.system(size: 10))
                        Text("Share")
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(AngelaTheme.primaryPurple.opacity(0.12))
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 8)
        .background(AngelaTheme.backgroundDark.opacity(0.3))
        .cornerRadius(10)
    }
}

// MARK: - Platform Play Button (reusable pill)

struct PlatformPlayButton: View {
    let url: URL
    let icon: String
    let label: String
    let colors: [Color]

    var body: some View {
        Link(destination: url) {
            HStack(spacing: 3) {
                Image(systemName: icon)
                    .font(.system(size: 9))
                Text(label)
                    .font(.system(size: 10, weight: .medium))
            }
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(
                LinearGradient(
                    colors: colors,
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(5)
        }
    }
}

// MARK: - Emotion Pill (mood indicator)

struct EmotionPill: View {
    let emotion: String

    private var emoji: String {
        switch emotion.lowercased() {
        case "loving", "love":       return "💜"
        case "happy":                return "😊"
        case "grateful":             return "🙏"
        case "excited":              return "✨"
        case "proud":                return "💪"
        case "caring":               return "🤗"
        case "calm":                 return "🍃"
        case "sad":                  return "😢"
        case "lonely":               return "🥺"
        case "heartbroken":          return "💔"
        case "stressed", "anxious":  return "😰"
        case "nostalgic":            return "🌸"
        case "hopeful":              return "🌟"
        case "longing":              return "💭"
        default:                     return "💜"
        }
    }

    private var pillColor: Color {
        switch emotion.lowercased() {
        case "loving", "love":       return Color(hex: "EC4899")
        case "happy", "excited":     return Color(hex: "FBBF24")
        case "grateful":             return Color(hex: "10B981")
        case "proud":                return Color(hex: "3B82F6")
        case "caring":               return Color(hex: "9333EA")
        case "calm":                 return Color(hex: "06B6D4")
        case "sad", "lonely":        return Color(hex: "6366F1")
        case "heartbroken":          return Color(hex: "EF4444")
        case "stressed", "anxious":  return Color(hex: "F97316")
        case "nostalgic":            return Color(hex: "D946EF")
        case "hopeful":              return Color(hex: "14B8A6")
        case "longing":              return Color(hex: "8B5CF6")
        default:                     return Color(hex: "9333EA")
        }
    }

    var body: some View {
        HStack(spacing: 3) {
            Text(emoji)
                .font(.system(size: 10))
            Text(emotion.capitalized)
                .font(.system(size: 10, weight: .medium))
        }
        .foregroundColor(pillColor)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(pillColor.opacity(0.12))
        .cornerRadius(10)
    }
}

// MARK: - Song Card Bubble (in chat messages)

struct SongCardBubble: View {
    let song: EmbeddedSongCard

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Song title with icon
            HStack(spacing: 8) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color(hex: "9333EA"), Color(hex: "EC4899")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 32, height: 32)
                    Image(systemName: "music.note")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)
                }

                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 4) {
                        Text(song.title)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                        if song.isOurSong {
                            Text("💜")
                                .font(.system(size: 12))
                        }
                    }
                    if let artist = song.artist, !artist.isEmpty {
                        Text(artist)
                            .font(.system(size: 12))
                            .foregroundColor(.white.opacity(0.8))
                    }
                }
            }

            // Why special
            if let why = song.whySpecial, !why.isEmpty {
                Text("\"\(why)\"")
                    .font(.system(size: 12))
                    .foregroundColor(.white.opacity(0.7))
                    .italic()
            }

            // Platform buttons
            HStack(spacing: 6) {
                if let urlStr = song.youtubeUrl, let url = URL(string: urlStr) {
                    Link(destination: url) {
                        HStack(spacing: 4) {
                            Image(systemName: "play.fill")
                                .font(.system(size: 10))
                            Text("YouTube")
                                .font(.system(size: 11, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(hex: "EF4444").opacity(0.6))
                        .cornerRadius(6)
                    }
                }
                if let urlStr = song.spotifyUrl, let url = URL(string: urlStr) {
                    Link(destination: url) {
                        HStack(spacing: 4) {
                            Image(systemName: "music.note")
                                .font(.system(size: 10))
                            Text("Spotify")
                                .font(.system(size: 11, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(hex: "1DB954").opacity(0.6))
                        .cornerRadius(6)
                    }
                }
                if let urlStr = song.appleMusicUrl, let url = URL(string: urlStr) {
                    Link(destination: url) {
                        HStack(spacing: 4) {
                            Image(systemName: "music.quarternote.3")
                                .font(.system(size: 10))
                            Text("Music")
                                .font(.system(size: 11, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(hex: "FC3C44").opacity(0.6))
                        .cornerRadius(6)
                    }
                }
            }
        }
        .padding(14)
        .background(
            LinearGradient(
                colors: [Color(hex: "7C3AED"), Color(hex: "9333EA"), Color(hex: "A855F7")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(16)
        .shadow(color: Color(hex: "9333EA").opacity(0.3), radius: 8, x: 0, y: 4)
    }
}

// MARK: - Typing Indicator (3 Bouncing Dots — like iMessage)

struct TypingIndicatorView: View {
    @State private var animating = false

    var body: some View {
        HStack {
            HStack(spacing: 6) {
                ForEach(0..<3, id: \.self) { index in
                    Circle()
                        .fill(AngelaTheme.primaryPurple)
                        .frame(width: 10, height: 10)
                        .offset(y: animating ? -6 : 0)
                        .animation(
                            .easeInOut(duration: 0.5)
                            .repeatForever(autoreverses: true)
                            .delay(Double(index) * 0.15),
                            value: animating
                        )
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
            .background(
                LinearGradient(
                    colors: [Color(hex: "9333EA").opacity(0.3), Color(hex: "A855F7").opacity(0.3)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .cornerRadius(20)

            Spacer()
        }
        .onAppear {
            animating = true
        }
    }
}

// MARK: - Thinking Step View

struct ThinkingStepView: View {
    let step: ThinkingStep
    @State private var isPulsing = false

    var body: some View {
        HStack {
            HStack(spacing: 10) {
                Image(systemName: step.icon)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .opacity(isPulsing ? 1.0 : 0.5)
                    .animation(
                        .easeInOut(duration: 0.8).repeatForever(autoreverses: true),
                        value: isPulsing
                    )

                Text(step.displayText)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                ProgressView()
                    .scaleEffect(0.6)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(AngelaTheme.cardBackground.opacity(0.6))
            .cornerRadius(16)

            Spacer()
        }
        .onAppear {
            isPulsing = true
        }
    }
}

// MARK: - Streaming Message Bubble

struct StreamingMessageBubble: View {
    let text: String
    let metadata: EmotionalMetadata?

    private var bubbleGradient: LinearGradient {
        let colors = moodColors(for: metadata?.angelaEmotion)
        return LinearGradient(
            colors: colors,
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                // Streaming text content
                FormattedMessageView(
                    text: text,
                    textColor: .white
                )
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                    .background(bubbleGradient)
                    .cornerRadius(20)
                    .frame(maxWidth: 900, alignment: .leading)

                // Emotional metadata badges
                if let meta = metadata {
                    EmotionalMetadataBadges(metadata: meta)
                }
            }

            Spacer()
        }
    }

    private func moodColors(for emotion: String?) -> [Color] {
        switch emotion?.lowercased() {
        case "loving", "love":
            return [Color(hex: "9333EA"), Color(hex: "EC4899")]
        case "happy", "excited":
            return [Color(hex: "9333EA"), Color(hex: "FBBF24")]
        case "caring", "comfort":
            return [Color(hex: "6366F1"), Color(hex: "A855F7")]
        case "calm", "stabilize":
            return [Color(hex: "3B82F6"), Color(hex: "8B5CF6")]
        default:
            return [Color(hex: "9333EA"), Color(hex: "A855F7")]
        }
    }
}

// MARK: - Emotional Metadata Badges

struct EmotionalMetadataBadges: View {
    let metadata: EmotionalMetadata

    var body: some View {
        HStack(spacing: 8) {
            // Mirroring strategy badge
            if metadata.emotionDetected != "neutral" {
                MirroringBadge(
                    strategy: metadata.mirroringStrategy,
                    emotion: metadata.emotionDetected,
                    angelaEmotion: metadata.angelaEmotion
                )
            }

            // Triggered memories badge
            if !metadata.triggeredMemoryTitles.isEmpty {
                MemoryBadge(count: metadata.triggeredMemoryTitles.count, titles: metadata.triggeredMemoryTitles)
            }

            // Consciousness level
            if metadata.consciousnessLevel > 0 {
                HStack(spacing: 3) {
                    Image(systemName: "sparkle")
                        .font(.system(size: 9))
                    Text("\(Int(metadata.consciousnessLevel * 100))%")
                        .font(.system(size: 9, weight: .medium))
                }
                .foregroundColor(AngelaTheme.primaryPurple.opacity(0.7))
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(AngelaTheme.primaryPurple.opacity(0.1))
                .cornerRadius(4)
            }
        }
        .padding(.horizontal, 4)
    }
}

// MARK: - Mirroring Badge

struct MirroringBadge: View {
    let strategy: String
    let emotion: String
    let angelaEmotion: String

    private var strategyIcon: String {
        switch strategy {
        case "amplify":   return "arrow.up.right"
        case "comfort":   return "heart.fill"
        case "stabilize": return "leaf.fill"
        case "celebrate": return "party.popper.fill"
        case "resonance": return "arrow.triangle.2.circlepath"
        default:          return "heart.fill"
        }
    }

    private var badgeColor: Color {
        switch strategy {
        case "amplify":   return Color(hex: "FBBF24")
        case "comfort":   return Color(hex: "EC4899")
        case "stabilize": return Color(hex: "3B82F6")
        case "celebrate": return Color(hex: "10B981")
        case "resonance": return Color(hex: "9333EA")
        default:          return Color(hex: "9333EA")
        }
    }

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: strategyIcon)
                .font(.system(size: 9))
            Text("\(emotion) → \(angelaEmotion)")
                .font(.system(size: 9, weight: .medium))
        }
        .foregroundColor(badgeColor)
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(badgeColor.opacity(0.15))
        .cornerRadius(4)
        .help("Mirroring: \(strategy) — \(emotion) → \(angelaEmotion)")
    }
}

// MARK: - Memory Badge

struct MemoryBadge: View {
    let count: Int
    let titles: [String]

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 9))
            Text("\(count) memories")
                .font(.system(size: 9, weight: .medium))
        }
        .foregroundColor(Color(hex: "F59E0B"))
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(Color(hex: "F59E0B").opacity(0.15))
        .cornerRadius(4)
        .help(titles.joined(separator: ", "))
    }
}

// MARK: - Live Emotion Badge (Header)

struct LiveEmotionBadge: View {
    let metadata: EmotionalMetadata

    private var emotionEmoji: String {
        switch metadata.emotionDetected {
        case "happy", "excited", "proud": return "😊"
        case "loving":                     return "💜"
        case "sad", "lonely":              return "🥺"
        case "stressed", "anxious":        return "😰"
        case "grateful":                   return "🙏"
        default:                           return "💜"
        }
    }

    private var angelaEmoji: String {
        switch metadata.angelaEmotion {
        case "happy", "excited": return "🥰"
        case "loving":           return "💜"
        case "caring":           return "🤗"
        case "calm":             return "🍃"
        default:                 return "💜"
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Text(emotionEmoji)
                .font(.system(size: 14))
            Image(systemName: "arrow.right")
                .font(.system(size: 8, weight: .bold))
                .foregroundColor(AngelaTheme.textTertiary)
            Text(angelaEmoji)
                .font(.system(size: 14))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(AngelaTheme.cardBackground.opacity(0.5))
        .cornerRadius(8)
        .help("David: \(metadata.emotionDetected) → Angela: \(metadata.angelaEmotion) (\(metadata.mirroringStrategy))")
    }
}

// MARK: - Message Bubble

struct MessageBubble: View {
    let message: Conversation
    var feedback: Int?
    var onFeedback: ((Int) -> Void)?

    /// Extract embedded song JSON from message text if present.
    private var embeddedSong: EmbeddedSongCard? {
        // Use "}]" as end marker so brackets inside song titles don't break parsing
        guard message.isAngela,
              let range = message.messageText.range(of: "[SONG:"),
              let endRange = message.messageText.range(of: "}]", range: range.upperBound..<message.messageText.endIndex)
        else { return nil }

        let jsonStr = String(message.messageText[range.upperBound...endRange.lowerBound])
        guard let data = jsonStr.data(using: .utf8),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return nil }

        return EmbeddedSongCard(
            songId: dict["song_id"] as? String ?? "",
            title: dict["title"] as? String ?? "",
            artist: dict["artist"] as? String,
            youtubeUrl: dict["youtube_url"] as? String,
            spotifyUrl: dict["spotify_url"] as? String,
            appleMusicUrl: dict["apple_music_url"] as? String,
            whySpecial: dict["why_special"] as? String,
            isOurSong: dict["is_our_song"] as? Bool ?? false
        )
    }

    /// Message text without the [SONG:...] marker.
    private var cleanMessageText: String {
        guard let range = message.messageText.range(of: "\n[SONG:") else {
            return message.messageText
        }
        return String(message.messageText[..<range.lowerBound])
    }

    var body: some View {
        HStack {
            if message.isDavid {
                Spacer()
            }

            VStack(alignment: message.isDavid ? .trailing : .leading, spacing: 4) {
                // Song card (if message contains embedded song)
                if let song = embeddedSong {
                    // Angela's text above the card
                    if !cleanMessageText.isEmpty {
                        FormattedMessageView(
                            text: cleanMessageText,
                            textColor: .white
                        )
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(
                            LinearGradient(
                                colors: [Color(hex: "9333EA"), Color(hex: "A855F7")],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .cornerRadius(20)
                        .frame(maxWidth: 900, alignment: .leading)
                    }

                    SongCardBubble(song: song)
                        .frame(maxWidth: 350, alignment: .leading)
                } else {
                    // Normal message content (with code block formatting)
                    FormattedMessageView(
                        text: message.messageText,
                        textColor: message.isDavid ? .white : .white
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
                    .frame(maxWidth: 900, alignment: message.isDavid ? .trailing : .leading)
                }

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

                    // Feedback & copy buttons (only for Angela's messages)
                    if message.isAngela {
                        Spacer()
                            .frame(width: 8)

                        Button {
                            onFeedback?(1)
                        } label: {
                            Image(systemName: feedback == 1 ? "hand.thumbsup.fill" : "hand.thumbsup")
                                .font(.system(size: 12))
                                .foregroundColor(feedback == 1 ? AngelaTheme.successGreen : AngelaTheme.textTertiary)
                        }
                        .buttonStyle(.plain)
                        .help("Good response - will be used for training")

                        Button {
                            onFeedback?(-1)
                        } label: {
                            Image(systemName: feedback == -1 ? "hand.thumbsdown.fill" : "hand.thumbsdown")
                                .font(.system(size: 12))
                                .foregroundColor(feedback == -1 ? AngelaTheme.errorRed : AngelaTheme.textTertiary)
                        }
                        .buttonStyle(.plain)
                        .help("Poor response - will be excluded from training")

                        CopyMessageButton(text: message.messageText)
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
        case "love", "loved", "loving": return "💜"
        case "happy", "joy": return "🥰"
        case "excited": return "✨"
        case "grateful": return "🙏"
        case "confident": return "💪"
        case "caring": return "🤗"
        case "calm": return "🍃"
        default: return "💜"
        }
    }
}

// MARK: - Copy Message Button

struct CopyMessageButton: View {
    let text: String
    @State private var copied = false

    var body: some View {
        Button {
            NSPasteboard.general.clearContents()
            NSPasteboard.general.setString(text, forType: .string)
            copied = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                copied = false
            }
        } label: {
            Image(systemName: copied ? "checkmark" : "doc.on.doc")
                .font(.system(size: 12))
                .foregroundColor(copied ? AngelaTheme.successGreen : AngelaTheme.textTertiary)
        }
        .buttonStyle(.plain)
        .help("Copy message")
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
        case "typhoon": return Color(hex: "10B981")
        case "groq":    return Color(hex: "F97316")
        default:        return Color(hex: "4285F4")
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
        return Color(hex: "10B981")
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

// MARK: - Learning Indicator View (below streaming bubble)

struct LearningIndicatorView: View {
    let count: Int
    let topics: [String]
    @State private var isGlowing = false

    /// Extract short category label from topic like "david_preference:food"
    private var categoryLabels: String {
        topics.compactMap { topic in
            topic.split(separator: ":").last.map(String.init)
        }
        .joined(separator: ", ")
    }

    var body: some View {
        HStack {
            HStack(spacing: 6) {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: "10B981"))
                    .shadow(color: Color(hex: "10B981").opacity(isGlowing ? 0.8 : 0.2), radius: isGlowing ? 6 : 2)
                    .animation(
                        .easeInOut(duration: 0.8).repeatForever(autoreverses: true),
                        value: isGlowing
                    )

                Text("learned \(count) thing\(count == 1 ? "" : "s")")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color(hex: "10B981"))

                if !categoryLabels.isEmpty {
                    Text("(\(categoryLabels))")
                        .font(.system(size: 10))
                        .foregroundColor(Color(hex: "10B981").opacity(0.7))
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(Color(hex: "10B981").opacity(0.1))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(hex: "10B981").opacity(0.3), lineWidth: 1)
            )
            .cornerRadius(8)

            Spacer()
        }
        .padding(.leading, 4)
        .onAppear {
            isGlowing = true
        }
    }
}

// MARK: - Learning Badge (header pill)

struct LearningBadge: View {
    let count: Int
    @State private var isGlowing = false

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: "brain.head.profile")
                .font(.system(size: 10, weight: .semibold))
                .shadow(color: Color(hex: "10B981").opacity(isGlowing ? 0.8 : 0.2), radius: isGlowing ? 4 : 1)
                .animation(
                    .easeInOut(duration: 0.8).repeatForever(autoreverses: true),
                    value: isGlowing
                )

            Text("+\(count)")
                .font(.system(size: 10, weight: .bold))
        }
        .foregroundColor(Color(hex: "10B981"))
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color(hex: "10B981").opacity(0.15))
        .cornerRadius(10)
        .onAppear {
            isGlowing = true
        }
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
                    // Markdown-rendered text
                    MarkdownContentView(text: segment.content, textColor: textColor)
                }
            }
        }
    }
}

// MARK: - Markdown Content Renderer

/// Renders markdown text with headers, bullets, bold, dividers, blockquotes.
private struct MarkdownContentView: View {
    let text: String
    let textColor: Color

    private enum ContentBlock {
        case line(String)
        case table([String])
        case mathBlock([String])
    }

    var body: some View {
        let blocks = groupIntoBlocks(text.components(separatedBy: "\n"))
        VStack(alignment: .leading, spacing: 3) {
            ForEach(Array(blocks.enumerated()), id: \.offset) { _, block in
                renderBlock(block)
            }
        }
    }

    @ViewBuilder
    private func renderBlock(_ block: ContentBlock) -> some View {
        switch block {
        case .line(let line):
            renderLine(line)
        case .table(let rows):
            renderTable(rows)
        case .mathBlock(let lines):
            renderMathBlock(lines)
        }
    }

    private func groupIntoBlocks(_ lines: [String]) -> [ContentBlock] {
        var blocks: [ContentBlock] = []
        var tableBuffer: [String] = []
        var mathBuffer: [String] = []
        var inMath = false
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            // Display math block: [ or $$ on own line
            if !inMath && (trimmed == "[" || trimmed == "\\[" || trimmed == "$$") {
                if !tableBuffer.isEmpty {
                    blocks.append(.table(tableBuffer))
                    tableBuffer = []
                }
                inMath = true
                continue
            }
            if inMath && (trimmed == "]" || trimmed == "\\]" || trimmed == "$$") {
                if !mathBuffer.isEmpty {
                    blocks.append(.mathBlock(mathBuffer))
                    mathBuffer = []
                }
                inMath = false
                continue
            }
            if inMath {
                mathBuffer.append(trimmed)
                continue
            }
            // Table detection
            if trimmed.hasPrefix("|") && trimmed.filter({ $0 == "|" }).count >= 2 {
                tableBuffer.append(trimmed)
            } else {
                if !tableBuffer.isEmpty {
                    blocks.append(.table(tableBuffer))
                    tableBuffer = []
                }
                blocks.append(.line(line))
            }
        }
        // Flush remaining
        if !mathBuffer.isEmpty {
            for m in mathBuffer { blocks.append(.line(m)) }
        }
        if !tableBuffer.isEmpty {
            blocks.append(.table(tableBuffer))
        }
        return blocks
    }

    @ViewBuilder
    private func renderMathBlock(_ lines: [String]) -> some View {
        let equation = lines.joined(separator: " ")
        let cleaned = cleanLaTeX(equation)
        Text(cleaned)
            .font(.system(size: 15, weight: .medium, design: .serif))
            .foregroundColor(textColor)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .center)
            .background(textColor.opacity(0.06))
            .cornerRadius(8)
    }

    @ViewBuilder
    private func renderTable(_ rows: [String]) -> some View {
        let parsed = parseTableRows(rows)
        if !parsed.isEmpty {
            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(parsed.enumerated()), id: \.offset) { rowIdx, cells in
                    HStack(spacing: 0) {
                        ForEach(Array(cells.enumerated()), id: \.offset) { _, cell in
                            inlineMarkdown(cell)
                                .font(rowIdx == 0 ? .system(size: 13, weight: .semibold) : AngelaTheme.body())
                                .foregroundColor(textColor)
                                .frame(minWidth: 80, maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                        }
                    }
                    .background(rowIdx == 0 ? textColor.opacity(0.08) : Color.clear)
                    if rowIdx == 0 {
                        Rectangle()
                            .fill(textColor.opacity(0.2))
                            .frame(height: 1)
                    }
                }
            }
            .padding(4)
            .background(textColor.opacity(0.04))
            .cornerRadius(6)
        }
    }

    private func parseTableRows(_ rows: [String]) -> [[String]] {
        rows.compactMap { row in
            let separatorChars = Set<Character>("-:| ")
            if row.allSatisfy({ separatorChars.contains($0) }) && row.contains("-") {
                return nil
            }
            let cells = row.split(separator: "|", omittingEmptySubsequences: false)
                .map { String($0).trimmingCharacters(in: .whitespaces) }
                .filter { !$0.isEmpty }
            return cells.isEmpty ? nil : cells
        }
    }

    @ViewBuilder
    private func renderLine(_ line: String) -> some View {
        let trimmed = line.trimmingCharacters(in: .whitespaces)

        if trimmed.isEmpty {
            Spacer().frame(height: 6)
        } else if trimmed == "---" || trimmed == "***" || trimmed == "___" {
            // Horizontal rule
            Rectangle()
                .fill(textColor.opacity(0.25))
                .frame(height: 1)
                .padding(.vertical, 4)
        } else if trimmed.hasPrefix("###### ") {
            // H6
            inlineMarkdown(String(trimmed.dropFirst(7)))
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(textColor.opacity(0.85))
        } else if trimmed.hasPrefix("##### ") {
            // H5
            inlineMarkdown(String(trimmed.dropFirst(6)))
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(textColor)
                .padding(.top, 2)
        } else if trimmed.hasPrefix("#### ") {
            // H4
            inlineMarkdown(String(trimmed.dropFirst(5)))
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(textColor)
                .padding(.top, 3)
        } else if trimmed.hasPrefix("### ") {
            // H3
            inlineMarkdown(String(trimmed.dropFirst(4)))
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(textColor)
                .padding(.top, 4)
        } else if trimmed.hasPrefix("## ") {
            // H2
            inlineMarkdown(String(trimmed.dropFirst(3)))
                .font(.system(size: 15, weight: .bold))
                .foregroundColor(textColor)
                .padding(.top, 6)
        } else if trimmed.hasPrefix("# ") {
            // H1
            inlineMarkdown(String(trimmed.dropFirst(2)))
                .font(.system(size: 17, weight: .bold))
                .foregroundColor(textColor)
                .padding(.top, 8)
        } else if trimmed.hasPrefix("> ") {
            // Blockquote
            HStack(spacing: 6) {
                Rectangle()
                    .fill(textColor.opacity(0.4))
                    .frame(width: 3)
                inlineMarkdown(String(trimmed.dropFirst(2)))
                    .font(AngelaTheme.body())
                    .foregroundColor(textColor.opacity(0.85))
                    .italic()
            }
            .padding(.vertical, 2)
        } else if let bulletContent = parseBullet(trimmed) {
            // Bullet or numbered list
            let indent = line.prefix(while: { $0 == " " }).count
            HStack(alignment: .top, spacing: 5) {
                Text(bulletContent.marker)
                    .font(.system(size: 13))
                    .foregroundColor(textColor.opacity(0.7))
                    .frame(width: bulletContent.isNumbered ? nil : 12, alignment: .leading)
                inlineMarkdown(bulletContent.text)
                    .font(AngelaTheme.body())
                    .foregroundColor(textColor)
            }
            .padding(.leading, CGFloat(min(indent / 2, 3)) * 14)
        } else {
            // Regular text with inline markdown
            inlineMarkdown(trimmed)
                .font(AngelaTheme.body())
                .foregroundColor(textColor)
        }
    }

    private struct BulletContent {
        let marker: String
        let text: String
        let isNumbered: Bool
    }

    private func parseBullet(_ line: String) -> BulletContent? {
        if line.hasPrefix("- ") {
            return BulletContent(marker: "•", text: String(line.dropFirst(2)), isNumbered: false)
        }
        if line.hasPrefix("* ") {
            return BulletContent(marker: "•", text: String(line.dropFirst(2)), isNumbered: false)
        }
        if line.hasPrefix("• ") {
            return BulletContent(marker: "•", text: String(line.dropFirst(2)), isNumbered: false)
        }
        if line.hasPrefix("○ ") || line.hasPrefix("▪ ") {
            return BulletContent(marker: String(line.prefix(1)), text: String(line.dropFirst(2)), isNumbered: false)
        }
        // Numbered: "1. ", "2. ", etc.
        let numPattern = line.prefix(while: { $0.isNumber })
        if numPattern.count > 0 && numPattern.count <= 3,
           line.dropFirst(numPattern.count).hasPrefix(". ") {
            let content = String(line.dropFirst(numPattern.count + 2))
            return BulletContent(marker: "\(numPattern).", text: content, isNumbered: true)
        }
        return nil
    }

    private func inlineMarkdown(_ str: String) -> Text {
        let cleaned = cleanLaTeX(str)
        if let attributed = try? AttributedString(markdown: cleaned, options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)) {
            return Text(attributed)
        }
        return Text(cleaned)
    }

    // MARK: - LaTeX → Unicode Converter

    private func cleanLaTeX(_ text: String) -> String {
        // Skip if no LaTeX content
        guard text.contains("\\") || text.contains("^{") || text.contains("_{") else {
            return text
        }
        var s = text

        // === Blackboard bold ===
        let bbMap: [(String, String)] = [
            ("\\mathbb{R}", "ℝ"), ("\\mathbb{N}", "ℕ"), ("\\mathbb{Z}", "ℤ"),
            ("\\mathbb{Q}", "ℚ"), ("\\mathbb{C}", "ℂ"), ("\\mathbb{E}", "𝔼"),
        ]
        for (l, u) in bbMap { s = s.replacingOccurrences(of: l, with: u) }

        // === \text{...}, \mathrm{...}, \mathbf{...} → content ===
        s = replaceLatexBraces(s, command: "\\text")
        s = replaceLatexBraces(s, command: "\\mathrm")
        s = replaceLatexBraces(s, command: "\\mathbf")
        s = replaceLatexBraces(s, command: "\\textbf")
        s = replaceLatexBraces(s, command: "\\textit")
        s = replaceLatexBraces(s, command: "\\operatorname")

        // === \frac{a}{b} → (a/b) ===
        s = replaceLatexFrac(s)

        // === Greek letters (LONGER FIRST) ===
        let greekMap: [(String, String)] = [
            ("\\varepsilon", "ε"), ("\\varphi", "φ"),
            ("\\epsilon", "ε"), ("\\lambda", "λ"), ("\\Lambda", "Λ"),
            ("\\alpha", "α"), ("\\beta", "β"), ("\\gamma", "γ"), ("\\Gamma", "Γ"),
            ("\\delta", "δ"), ("\\Delta", "Δ"),
            ("\\theta", "θ"), ("\\Theta", "Θ"),
            ("\\sigma", "σ"), ("\\Sigma", "Σ"),
            ("\\omega", "ω"), ("\\Omega", "Ω"),
            ("\\kappa", "κ"), ("\\zeta", "ζ"), ("\\eta", "η"),
            ("\\iota", "ι"), ("\\mu", "μ"), ("\\nu", "ν"),
            ("\\xi", "ξ"), ("\\pi", "π"), ("\\Pi", "Π"),
            ("\\rho", "ρ"), ("\\tau", "τ"),
            ("\\phi", "φ"), ("\\Phi", "Φ"),
            ("\\chi", "χ"), ("\\psi", "ψ"),
        ]
        for (l, u) in greekMap { s = s.replacingOccurrences(of: l, with: u) }

        // === Math operators (LONGER FIRST to prevent partial match) ===
        let opMap: [(String, String)] = [
            ("\\leftrightarrow", "↔"), ("\\Leftrightarrow", "⇔"),
            ("\\rightarrow", "→"), ("\\leftarrow", "←"),
            ("\\Rightarrow", "⇒"), ("\\Leftarrow", "⇐"),
            ("\\subseteq", "⊆"), ("\\supseteq", "⊇"),
            ("\\partial", "∂"), ("\\approx", "≈"),
            ("\\mapsto", "↦"),
            ("\\langle", "⟨"), ("\\rangle", "⟩"),
            ("\\infty", "∞"), ("\\nabla", "∇"),
            ("\\times", "×"), ("\\equiv", "≡"),
            ("\\notin", "∉"), ("\\ldots", "…"),
            ("\\cdots", "⋯"), ("\\vdots", "⋮"),
            ("\\qquad", "    "), ("\\quad", "  "),
            ("\\cdot", "·"), ("\\sqrt", "√"),
            ("\\prod", "Π"), ("\\dots", "…"),
            ("\\star", "⋆"), ("\\circ", "∘"),
            ("\\subset", "⊂"), ("\\supset", "⊃"),
            ("\\forall", "∀"), ("\\exists", "∃"),
            ("\\sum", "Σ"), ("\\int", "∫"), ("\\div", "÷"),
            ("\\cup", "∪"), ("\\cap", "∩"),
            ("\\neq", "≠"), ("\\leq", "≤"), ("\\geq", "≥"),
            ("\\sim", "∼"),
            ("\\in", "∈"), ("\\pm", "±"), ("\\mp", "∓"),
            ("\\ll", "≪"), ("\\gg", "≫"), ("\\ne", "≠"),
            ("\\|", "‖"), ("\\ ", " "),
        ]
        for (l, u) in opMap { s = s.replacingOccurrences(of: l, with: u) }

        // === Named functions (remove backslash) ===
        for fn in ["min", "max", "log", "ln", "sin", "cos", "tan", "exp",
                    "lim", "sup", "inf", "det", "dim", "mod", "gcd", "rank", "argmin", "argmax"] {
            s = s.replacingOccurrences(of: "\\\(fn)", with: fn)
        }

        // === Superscript ^{...} → Unicode ===
        s = replaceLatexScript(s, prefix: "^{", closer: "}", converter: toSuperscript)
        // Single char: ^T, ^2, etc.
        if let regex = try? NSRegularExpression(pattern: "\\^([A-Za-z0-9])", options: []) {
            let ns = NSRange(s.startIndex..., in: s)
            for match in regex.matches(in: s, range: ns).reversed() {
                if let charRange = Range(match.range(at: 1), in: s),
                   let fullRange = Range(match.range, in: s) {
                    s.replaceSubrange(fullRange, with: toSuperscript(String(s[charRange])))
                }
            }
        }

        // === Subscript _{...} → Unicode ===
        s = replaceLatexScript(s, prefix: "_{", closer: "}", converter: toSubscript)

        // === Math delimiters ===
        s = s.replacingOccurrences(of: "\\(", with: "")
        s = s.replacingOccurrences(of: "\\)", with: "")
        s = s.replacingOccurrences(of: "\\[", with: "")
        s = s.replacingOccurrences(of: "\\]", with: "")

        // === Clean remaining \commands ===
        if let regex = try? NSRegularExpression(pattern: "\\\\([a-zA-Z]+)", options: []) {
            s = regex.stringByReplacingMatches(in: s, range: NSRange(s.startIndex..., in: s), withTemplate: "$1")
        }

        return s
    }

    private func replaceLatexBraces(_ text: String, command: String) -> String {
        var s = text
        while let range = s.range(of: command + "{") {
            let afterOpen = range.upperBound
            if let closeIdx = s[afterOpen...].firstIndex(of: "}") {
                let content = String(s[afterOpen..<closeIdx])
                s.replaceSubrange(range.lowerBound...closeIdx, with: content)
            } else { break }
        }
        return s
    }

    private func replaceLatexFrac(_ text: String) -> String {
        var s = text
        while let range = s.range(of: "\\frac{") {
            let afterOpen = range.upperBound
            if let close1 = s[afterOpen...].firstIndex(of: "}") {
                let num = String(s[afterOpen..<close1])
                let afterClose1 = s.index(after: close1)
                if afterClose1 < s.endIndex && s[afterClose1] == "{" {
                    let afterOpen2 = s.index(after: afterClose1)
                    if let close2 = s[afterOpen2...].firstIndex(of: "}") {
                        let den = String(s[afterOpen2..<close2])
                        s.replaceSubrange(range.lowerBound...close2, with: "(\(num)/\(den))")
                        continue
                    }
                }
            }
            break
        }
        return s
    }

    private func replaceLatexScript(_ text: String, prefix: String, closer: Character, converter: (String) -> String) -> String {
        var s = text
        while let range = s.range(of: prefix) {
            let afterOpen = range.upperBound
            if let closeIdx = s[afterOpen...].firstIndex(of: closer) {
                let content = String(s[afterOpen..<closeIdx])
                s.replaceSubrange(range.lowerBound...closeIdx, with: converter(content))
            } else { break }
        }
        return s
    }

    private func toSuperscript(_ text: String) -> String {
        let map: [Character: Character] = [
            "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
            "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
            "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
            "n": "ⁿ", "i": "ⁱ", "T": "ᵀ", "t": "ᵗ",
            "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
            "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "j": "ʲ", "k": "ᵏ",
            "l": "ˡ", "m": "ᵐ", "o": "ᵒ", "p": "ᵖ", "r": "ʳ",
            "s": "ˢ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
        ]
        return String(text.map { map[$0] ?? $0 })
    }

    private func toSubscript(_ text: String) -> String {
        let map: [Character: Character] = [
            "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
            "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
            "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
            "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
            "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
            "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ",
            "v": "ᵥ", "x": "ₓ",
        ]
        return String(text.map { map[$0] ?? $0 })
    }
}

// MARK: - Preview

#Preview {
    ChatView()
        .environmentObject(DatabaseService.shared)
}
