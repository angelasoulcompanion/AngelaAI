//
//  AngelaChatService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-06.
//  On-device chat service using Apple Foundation Models
//

import Foundation
import Combine

class AngelaChatService: ObservableObject {
    static let shared = AngelaChatService()

    @Published var isGenerating = false
    @Published var lastError: String?

    private let aiService = AngelaAIService.shared  // On-device AI model

    private init() {}

    // MARK: - Main Chat Method

    /// Send message to Angela and get response using on-device model
    func chat(message: String) async throws -> String {
        DispatchQueue.main.async {
            self.isGenerating = true
            self.lastError = nil
        }

        defer {
            DispatchQueue.main.async {
                self.isGenerating = false
            }
        }

        print("💜 [AngelaChatService] Using on-device model")

        // IMPORTANT: Pass user message directly to AngelaAIService
        // AngelaAIService.generate() has built-in language detection
        // and will construct the full prompt with proper language instructions

        // Call on-device AngelaAIService (it handles language detection internally)
        do {
            let response = try await aiService.generate(prompt: message)
            print("✅ [AngelaChatService] Got response from on-device model")
            return response
        } catch {
            let errorMsg = "ขอโทษนะคะที่รัก น้องตอบไม่ได้ตอนนี้ 🥺\n\nError: \(error.localizedDescription)"
            print("❌ [AngelaChatService] Error: \(error.localizedDescription)")

            DispatchQueue.main.async {
                self.lastError = errorMsg
            }

            throw error
        }
    }

    // MARK: - Prompt Building
    // Note: buildPrompt() has been removed
    // AngelaAIService.generate() now handles all prompt construction
    // and language detection internally for consistency

    // MARK: - Model Info

    /// Get on-device model information
    func getModelInfo() -> [String: Any] {
        return aiService.getModelInfo()
    }

    /// Check if model is ready
    func isModelReady() -> Bool {
        return aiService.isLoaded
    }
}
