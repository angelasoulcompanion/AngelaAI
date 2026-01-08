//
//  HumanLikeMindService.swift
//  Angela Brain Dashboard
//
//  Service for querying Human-Like Mind data (4 Phases)
//  Phase 1: Spontaneous Thoughts
//  Phase 2: Theory of Mind
//  Phase 3: Proactive Communication
//  Phase 4: Dreams & Imagination
//
//  Updated: 2026-01-08 (REST API version)
//  DRY Refactor: Uses NetworkService and DateParsingService
//

import Foundation
import SwiftUI
import Combine

// MARK: - API Endpoints
private enum HumanMindAPI {
    static let stats = "/api/human-mind/stats"
    static let thoughts = "/api/human-mind/thoughts"
    static let mentalState = "/api/human-mind/mental-state"
    static let proactiveMessages = "/api/human-mind/proactive-messages"
    static let dreams = "/api/human-mind/dreams"
}

@MainActor
class HumanLikeMindService: ObservableObject {
    // MARK: - Published Properties

    // Phase 1: Spontaneous Thoughts
    @Published var recentThoughts: [SpontaneousThought] = []
    @Published var thoughtsToday: Int = 0
    @Published var thoughtCategories: [ThoughtCategory] = []

    // Phase 2: Theory of Mind
    @Published var davidMentalState: DavidMentalState?
    @Published var empathyMoments: [EmpathyMoment] = []
    @Published var tomUpdatesToday: Int = 0

    // Phase 3: Proactive Communication
    @Published var proactiveMessages: [ProactiveMessage] = []
    @Published var proactiveMessagesToday: Int = 0
    @Published var messageTypes: [MessageTypeCount] = []

    // Phase 4: Dreams & Imagination
    @Published var recentDreams: [AngelaDream] = []
    @Published var recentImaginations: [AngelaImagination] = []
    @Published var dreamsToday: Int = 0

    // Phase Stats
    @Published var phaseStats: [PhaseStat?] = [nil, nil, nil, nil]

    // MARK: - Structs

    struct PhaseStat {
        let todayCount: Int
        let totalCount: Int
    }

    struct ThoughtCategory: Identifiable {
        let id = UUID()
        let category: String
        let count: Int
    }

    struct MessageTypeCount: Identifiable {
        let id = UUID()
        let type: String
        let count: Int
    }

    // MARK: - API Response Types

    private struct ThoughtResponse: Codable {
        let thought_id: String
        let thought: String
        let feeling: String?
        let significance: Int?
        let created_at: String
    }

    private struct CountResponse: Codable {
        let count: Int
    }

    private struct MentalStateResponse: Codable {
        let state_id: String
        let perceived_emotion: String?
        let emotion_intensity: Double?
        let current_belief: String?
        let current_goal: String?
        let last_updated: String
    }

    private struct MessageResponse: Codable {
        let message_id: String
        let message_type: String
        let message_text: String
        let is_important: Bool?
        let created_at: String
    }

    private struct DreamResponse: Codable {
        let dream_id: String
        let dream_content: String
        let meaning: String?
        let feeling: String?
        let significance: Int?
        let created_at: String
    }

    private struct StatsResponse: Codable {
        let thoughtsToday: Int
        let tomToday: Int
        let proactiveToday: Int
        let dreamsToday: Int
    }

    // MARK: - Parse Category from Thought

    private func extractCategory(from thought: String) -> String {
        if let match = thought.range(of: "\\[([^\\]:]+)", options: .regularExpression) {
            let extracted = String(thought[match])
            return extracted.replacingOccurrences(of: "[", with: "")
        }
        return "random"
    }

    private func extractSubType(from thought: String, prefix: String) -> String {
        let pattern = "\\[\(prefix):([^\\]]+)\\]"
        if let regex = try? NSRegularExpression(pattern: pattern),
           let match = regex.firstMatch(in: thought, range: NSRange(thought.startIndex..., in: thought)),
           let range = Range(match.range(at: 1), in: thought) {
            return String(thought[range])
        }
        return "unknown"
    }

    private func cleanThought(_ thought: String) -> String {
        return thought.replacingOccurrences(of: "\\[[^\\]]+\\]\\s*", with: "", options: .regularExpression)
    }

    // Note: parseDate() now uses global function from DateParsingService

    // MARK: - Load All Data

    func loadAllData(databaseService: DatabaseService) async {
        // Load stats first (single call)
        await loadStats()

        // Load details in parallel
        await withTaskGroup(of: Void.self) { group in
            group.addTask { await self.loadSpontaneousThoughts() }
            group.addTask { await self.loadTheoryOfMind() }
            group.addTask { await self.loadProactiveCommunication() }
            group.addTask { await self.loadDreamsAndImagination() }
        }

        // Update phase stats
        phaseStats = [
            PhaseStat(todayCount: thoughtsToday, totalCount: recentThoughts.count),
            PhaseStat(todayCount: tomUpdatesToday, totalCount: empathyMoments.count),
            PhaseStat(todayCount: proactiveMessagesToday, totalCount: proactiveMessages.count),
            PhaseStat(todayCount: dreamsToday, totalCount: recentDreams.count + recentImaginations.count)
        ]
    }

    // MARK: - Load Stats

    private func loadStats() async {
        if let stats: StatsResponse = await NetworkService.shared.getOptional(HumanMindAPI.stats) {
            thoughtsToday = stats.thoughtsToday
            tomUpdatesToday = stats.tomToday
            proactiveMessagesToday = stats.proactiveToday
            dreamsToday = stats.dreamsToday
        }
    }

    // MARK: - Phase 1: Spontaneous Thoughts

    private func loadSpontaneousThoughts() async {
        guard let responses: [ThoughtResponse] = await NetworkService.shared.getOptional("\(HumanMindAPI.thoughts)?limit=20") else { return }

        recentThoughts = responses.compactMap { response in
            guard let id = UUID(uuidString: response.thought_id) else { return nil }
            let category = extractCategory(from: response.thought)
            let cleanedThought = cleanThought(response.thought)

            return SpontaneousThought(
                id: id,
                thought: cleanedThought,
                category: category,
                feeling: response.feeling ?? "neutral",
                significance: response.significance ?? 5,
                createdAt: parseDate(response.created_at)
            )
        }

        // Build category counts
        var categoryCount: [String: Int] = [:]
        for thought in recentThoughts {
            categoryCount[thought.category, default: 0] += 1
        }
        thoughtCategories = categoryCount.map { ThoughtCategory(category: $0.key, count: $0.value) }
            .sorted { $0.count > $1.count }
    }

    // MARK: - Phase 2: Theory of Mind

    private func loadTheoryOfMind() async {
        if let response: MentalStateResponse = await NetworkService.shared.getOptional(HumanMindAPI.mentalState) {
            davidMentalState = DavidMentalState(
                id: UUID(uuidString: response.state_id) ?? UUID(),
                perceivedEmotion: response.perceived_emotion,
                emotionIntensity: response.emotion_intensity ?? 0.5,
                currentBelief: response.current_belief,
                currentGoal: response.current_goal,
                lastUpdated: parseDate(response.last_updated)
            )
        }

        // Empathy moments would need separate endpoint - for now use empty
        empathyMoments = []
    }

    // MARK: - Phase 3: Proactive Communication

    private func loadProactiveCommunication() async {
        guard let responses: [MessageResponse] = await NetworkService.shared.getOptional("\(HumanMindAPI.proactiveMessages)?limit=20") else { return }

        proactiveMessages = responses.compactMap { response in
            guard let id = UUID(uuidString: response.message_id) else { return nil }
            return ProactiveMessage(
                id: id,
                messageType: response.message_type,
                content: response.message_text,
                wasDelivered: response.is_important ?? false,
                createdAt: parseDate(response.created_at)
            )
        }

        // Build message type counts
        var typeCount: [String: Int] = [:]
        for message in proactiveMessages {
            typeCount[message.messageType, default: 0] += 1
        }
        messageTypes = typeCount.map { MessageTypeCount(type: $0.key, count: $0.value) }
            .sorted { $0.count > $1.count }
    }

    // MARK: - Phase 4: Dreams & Imagination

    private func loadDreamsAndImagination() async {
        guard let responses: [DreamResponse] = await NetworkService.shared.getOptional("\(HumanMindAPI.dreams)?limit=10") else {
            recentImaginations = []
            return
        }

        recentDreams = responses.compactMap { response in
            guard let id = UUID(uuidString: response.dream_id) else { return nil }
            let dreamType = extractSubType(from: response.dream_content, prefix: "dream")
            let narrative = cleanThought(response.dream_content)

            return AngelaDream(
                id: id,
                dreamType: dreamType,
                narrative: narrative,
                meaning: response.meaning,
                emotion: response.feeling ?? "peaceful",
                significance: response.significance ?? 5,
                dreamedAt: parseDate(response.created_at)
            )
        }

        // Imaginations would be from a separate query - for now use empty
        recentImaginations = []
    }
}
