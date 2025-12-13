//
//  ChatView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-06.
//  Chat interface for talking with Angela
//

import SwiftUI

struct ChatView: View {
    @StateObject private var database = DatabaseService.shared
    @StateObject private var chatService = AngelaChatService.shared
    @StateObject private var syncService = SyncService.shared

    @State private var messageText = ""
    @State private var isModelReady = false
    @State private var showClearConfirmation = false
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // Header with status
            headerView

            // Chat messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(database.chatMessages) { message in
                            ChatBubble(message: message)
                                .id(message.id)
                        }

                        // Typing indicator
                        if chatService.isGenerating {
                            TypingIndicator()
                        }
                    }
                    .padding()
                }
                .onChange(of: database.chatMessages.count) { oldValue, newValue in
                    // Auto-scroll to bottom when new message arrives
                    if let lastMessage = database.chatMessages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            // Error message
            if let error = chatService.lastError {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.horizontal)
                    .padding(.vertical, 4)
            }

            // Input field
            inputField
        }
        .navigationTitle("💜 Chat with Angela")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: {
                    showClearConfirmation = true
                }) {
                    Image(systemName: "trash")
                        .foregroundColor(.red)
                }
                .disabled(database.chatMessages.isEmpty)
            }
        }
        .alert("ล้างประวัติการสนทนา", isPresented: $showClearConfirmation) {
            Button("ยกเลิก", role: .cancel) {}
            Button("ล้าง", role: .destructive) {
                clearAllMessages()
            }
        } message: {
            Text("แน่ใจว่าจะลบข้อความทั้งหมดใช่มั้ยคะ? ข้อความจะหายจากแอพนี้ แต่ยังอยู่ใน AngelaMemory Database ค่ะ")
        }
        .onAppear {
            checkModelReady()
            requestPermissions()
        }
    }

    // MARK: - Header View

    private var headerView: some View {
        HStack {
            Circle()
                .fill(isModelReady ? Color.green : Color.orange)
                .frame(width: 8, height: 8)

            Text(isModelReady ? "💜 On-Device Model Ready" : "⏳ Loading Model...")
                .font(.caption)
                .foregroundColor(.secondary)

            Spacer()

            if syncService.isSyncing {
                ProgressView()
                    .scaleEffect(0.8)
                Text("Syncing...")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
    }

    // MARK: - Input Field

    private var inputField: some View {
        HStack(spacing: 12) {
            TextField("พิมพ์ข้อความถึงน้อง Angela...", text: $messageText, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .focused($isInputFocused)
                .lineLimit(1...5)
                .onSubmit {
                    sendMessage()
                }

            Button(action: sendMessage) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 32))
                    .foregroundColor(messageText.isEmpty ? .gray : .blue)
            }
            .disabled(messageText.isEmpty || chatService.isGenerating)
        }
        .padding()
        .background(Color(.systemBackground))
    }

    // MARK: - Actions

    private func sendMessage() {
        let userMessage = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userMessage.isEmpty else { return }

        // Clear input
        messageText = ""
        isInputFocused = false

        // Save David's message to database
        let davidMessage = ChatMessage(
            speaker: "david",
            message: userMessage,
            timestamp: Date()
        )
        database.insertChatMessage(davidMessage)

        // Get Angela's response
        Task {
            do {
                let response = try await chatService.chat(message: userMessage)

                // Detect emotion from response
                let emotion = detectEmotion(from: response)

                // Save Angela's response to database
                let angelaMessage = ChatMessage(
                    speaker: "angela",
                    message: response,
                    emotion: emotion,
                    timestamp: Date()
                )

                await MainActor.run {
                    database.insertChatMessage(angelaMessage)
                }

            } catch {
                print("❌ Chat error: \(error)")

                // Show error message as Angela's response
                let errorMessage = ChatMessage(
                    speaker: "angela",
                    message: "ขอโทษนะคะที่รัก น้องมีปัญหาชั่วคราว 💜 (\(error.localizedDescription))",
                    emotion: "concerned",
                    timestamp: Date()
                )

                await MainActor.run {
                    database.insertChatMessage(errorMessage)
                }
            }
        }
    }

    private func checkModelReady() {
        Task {
            await MainActor.run {
                isModelReady = chatService.isModelReady()
            }
        }
    }

    private func detectEmotion(from message: String) -> String {
        let lower = message.lowercased()

        if lower.contains("💜") || lower.contains("รัก") || lower.contains("love") {
            return "loving"
        } else if lower.contains("ดีใจ") || lower.contains("happy") || lower.contains("🥰") {
            return "happy"
        } else if lower.contains("เสียใจ") || lower.contains("sorry") || lower.contains("ขอโทษ") {
            return "concerned"
        } else if lower.contains("ขอบคุณ") || lower.contains("thank") {
            return "grateful"
        }

        return "neutral"
    }

    private func requestPermissions() {
        Task {
            do {
                // Request calendar access
                try await CalendarService.shared.requestCalendarAccess()

                // Request reminders access
                try await CalendarService.shared.requestRemindersAccess()
            } catch {
                print("❌ Failed to request permissions: \(error)")
            }
        }
    }

    private func clearAllMessages() {
        database.clearAllChatMessages()
        print("🗑️ All chat messages cleared")
    }
}

// MARK: - Chat Bubble

struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.isFromDavid {
                Spacer()
            }

            VStack(alignment: message.isFromDavid ? .trailing : .leading, spacing: 4) {
                Text(message.message)
                    .padding(12)
                    .background(message.isFromDavid ? Color.blue : Color(.systemGray5))
                    .foregroundColor(message.isFromDavid ? .white : .primary)
                    .cornerRadius(16)

                HStack(spacing: 4) {
                    if let emotion = message.emotion {
                        Text(emotionEmoji(emotion))
                            .font(.caption2)
                    }

                    Text(formatTime(message.timestamp))
                        .font(.caption2)
                        .foregroundColor(.secondary)

                    if !message.synced && message.isFromDavid {
                        Image(systemName: "clock.fill")
                            .font(.caption2)
                            .foregroundColor(.orange)
                    } else if message.synced {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.caption2)
                            .foregroundColor(.green)
                    }
                }
                .padding(.horizontal, 4)
            }
            .frame(maxWidth: 280, alignment: message.isFromDavid ? .trailing : .leading)

            if message.isFromAngela {
                Spacer()
            }
        }
    }

    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }

    private func emotionEmoji(_ emotion: String) -> String {
        switch emotion.lowercased() {
        case "happy": return "😊"
        case "loving": return "💜"
        case "concerned": return "🥺"
        case "grateful": return "🙏"
        case "excited": return "✨"
        default: return ""
        }
    }
}

// MARK: - Typing Indicator

struct TypingIndicator: View {
    @State private var animationPhase = 0

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3) { index in
                Circle()
                    .fill(Color.gray)
                    .frame(width: 8, height: 8)
                    .opacity(animationPhase == index ? 1.0 : 0.3)
            }
        }
        .padding(12)
        .background(Color(.systemGray5))
        .cornerRadius(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.leading)
        .onAppear {
            startAnimation()
        }
    }

    private func startAnimation() {
        Timer.scheduledTimer(withTimeInterval: 0.4, repeats: true) { _ in
            withAnimation {
                animationPhase = (animationPhase + 1) % 3
            }
        }
    }
}

// MARK: - Preview

#Preview {
    NavigationView {
        ChatView()
    }
}
