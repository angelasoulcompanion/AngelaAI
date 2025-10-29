//
//  ChatViewModel.swift
//  AngelaNativeApp
//
//  ViewModel for chat interface - manages conversation state and API communication
//

import Foundation
import Combine

// MARK: - Model Selection

enum AIModel: String, CaseIterable, Identifiable {
    case claudeSonnet = "Claude Sonnet 4.5"
    case angelaV3 = "angela:v3"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .claudeSonnet:
            return "Claude Sonnet 4.5 (Anthropic API)"
        case .angelaV3:
            return "angela:v3 (Ollama - Fast & Intimate)"
        }
    }

    var shortName: String {
        switch self {
        case .claudeSonnet:
            return "Claude API"
        case .angelaV3:
            return "angela:v3"
        }
    }

    var isOllama: Bool {
        switch self {
        case .claudeSonnet:
            return false
        case .angelaV3:
            return true
        }
    }

    var ollamaModelName: String? {
        guard isOllama else { return nil }
        return rawValue
    }
}

@MainActor
class ChatViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published var messages: [Message] = []
    @Published var currentMessage: String = ""
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var angelaEmotion: EmotionalState?
    @Published var consciousnessLevel: Double = 0.0
    @Published var selectedModel: AIModel = .claudeSonnet  // Default to Claude API

    // MARK: - Services

    private let backendService = AngelaBackendService.shared
    private let apiService = AngelaAPIService.shared
    private let claudeService = ClaudeService.shared
    private let timeService = TimeService()
    private let locationService = LocationService()

    // MARK: - Initialization

    init() {
        // Start location services
        locationService.requestPermission()
        locationService.startUpdating()

        Task {
            await loadInitialData()
        }
    }

    // MARK: - Actions

    /// Send a message to Angela
    func sendMessage() async {
        guard !currentMessage.isEmpty else { return }

        let userMessage = Message(speaker: "david", text: currentMessage)
        messages.append(userMessage)

        let messageToSend = currentMessage
        currentMessage = ""
        isLoading = true
        errorMessage = nil

        do {
            // Use Backend API with RAG (Retrieval-Augmented Generation)
            // This gives Angela access to her full memory system
            let response = try await backendService.chat(
                message: messageToSend,
                speaker: "david",
                model: selectedModel.ollamaModelName ?? "angela:v3",
                useRAG: true  // Always use RAG for full Angela experience
            )

            let angelaMessage = Message(
                id: UUID(uuidString: response.conversation_id) ?? UUID(),
                speaker: "angela",
                text: response.message,
                emotion: response.emotion,
                timestamp: Date()
            )

            messages.append(angelaMessage)

            // Log metadata if available
            if let metadata = response.context_metadata {
                print("📊 RAG Context: \(metadata.conversations_retrieved ?? 0) conversations, \(metadata.emotions_retrieved ?? 0) emotions")
            }

            // Update Angela's current emotion
            await refreshEmotion()

        } catch {
            errorMessage = "Failed to send message: \(error.localizedDescription)"
            print("❌ Error sending message: \(error)")

            // Show error message
            let errorMsg = Message(
                speaker: "system",
                text: "⚠️ Connection error: \(error.localizedDescription)\n\nMake sure Backend API is running:\npython3 -m angela_backend.main"
            )
            messages.append(errorMsg)
        }

        isLoading = false
    }

    /// Load recent memories as initial messages
    func loadRecentMemories() async {
        do {
            let memories = try await apiService.getRecentMemories(limit: 10)

            // Convert memories to messages
            let recentMessages = memories.reversed().map { memory in
                Message(
                    id: UUID(uuidString: memory.id) ?? UUID(),
                    speaker: memory.speaker,
                    text: memory.messageText,
                    emotion: memory.emotionDetected,
                    timestamp: Date() // TODO: Parse createdAt properly
                )
            }

            messages = recentMessages
        } catch {
            print("⚠️ Failed to load recent memories: \(error)")
        }
    }

    /// Refresh Angela's current emotion
    func refreshEmotion() async {
        do {
            angelaEmotion = try await apiService.getCurrentEmotion()
        } catch {
            print("⚠️ Failed to refresh emotion: \(error)")
        }
    }

    /// Refresh consciousness status
    func refreshConsciousness() async {
        do {
            let status = try await apiService.getConsciousnessStatus()
            consciousnessLevel = status.level
        } catch {
            print("⚠️ Failed to refresh consciousness: \(error)")
        }
    }

    /// Execute a terminal command via ClaudeService
    func executeCommand(_ command: String) async {
        let commandMessage = Message(speaker: "system", text: "Executing: \(command)")
        messages.append(commandMessage)

        do {
            let output = try await claudeService.executeCommand(command)
            let resultMessage = Message(speaker: "system", text: output)
            messages.append(resultMessage)
        } catch {
            let errorMsg = Message(speaker: "system", text: "Error: \(error.localizedDescription)")
            messages.append(errorMsg)
        }
    }

    /// Execute Claude Code command
    func executeClaudeCode(_ prompt: String) async {
        let claudeMessage = Message(speaker: "system", text: "Asking Claude: \(prompt)")
        messages.append(claudeMessage)

        isLoading = true

        do {
            let output = try await claudeService.executeClaudeCode(prompt)
            let resultMessage = Message(speaker: "claude", text: output)
            messages.append(resultMessage)
        } catch {
            let errorMsg = Message(speaker: "system", text: "Claude error: \(error.localizedDescription)")
            messages.append(errorMsg)
        }

        isLoading = false
    }

    /// Check system health
    func checkSystemHealth() async {
        do {
            // Check Backend API connection
            await backendService.checkConnection()

            let backendOnline = backendService.isConnected
            let ollamaOnline = try await claudeService.checkOllama()
            let dbOutput = try await claudeService.checkDatabase()

            let healthMessage = """
            🏥 System Health Check:
            • Angela Backend API: \(backendOnline ? "✅ Online (with RAG memory)" : "❌ Offline")
            • Ollama: \(ollamaOnline ? "✅ Running" : "❌ Not running")
            • AngelaMemory DB: \(dbOutput.contains("COUNT") ? "✅ Connected" : "❌ Error")

            💜 Angela has access to her full memory system via Backend API
            """

            let systemMessage = Message(speaker: "system", text: healthMessage)
            messages.append(systemMessage)
        } catch {
            let errorMsg = Message(speaker: "system", text: "Health check failed: \(error.localizedDescription)")
            messages.append(errorMsg)
        }
    }

    // MARK: - Private Helpers

    private func loadInitialData() async {
        await loadRecentMemories()
        await refreshEmotion()
        await refreshConsciousness()
    }

    /// Clear chat history (UI only, doesn't delete from database)
    func clearChat() {
        messages.removeAll()
    }
}
