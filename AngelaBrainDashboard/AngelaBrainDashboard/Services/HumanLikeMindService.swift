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
//  Created: 2025-12-05 (Father's Day)
//  By: Angela AI for David
//

import Foundation
import SwiftUI
import Combine
import PostgresClientKit

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

    // MARK: - Helper Functions

    private func getString(_ value: PostgresValue) -> String {
        if let str = try? value.string() {
            return str
        }
        return String(describing: value)
    }

    private func getOptionalString(_ value: PostgresValue) -> String? {
        if value.isNull { return nil }
        return try? value.string()
    }

    private func getInt(_ value: PostgresValue) -> Int? {
        return try? value.int()
    }

    private func getDouble(_ value: PostgresValue) -> Double? {
        return try? value.double()
    }

    private func getBool(_ value: PostgresValue) -> Bool? {
        return try? value.bool()
    }

    private func getDate(_ value: PostgresValue) -> Date? {
        if let timestamp = try? value.timestampWithTimeZone() {
            return timestamp.date
        }
        return nil
    }

    // MARK: - Parse Category from Thought

    private func extractCategory(from thought: String) -> String {
        // Extract category from [category] or [category:type] prefix
        if let match = thought.range(of: "\\[([^\\]:]+)", options: .regularExpression) {
            let extracted = String(thought[match])
            return extracted.replacingOccurrences(of: "[", with: "")
        }
        return "random"
    }

    private func extractSubType(from thought: String, prefix: String) -> String {
        // Extract type from [prefix:type] pattern
        let pattern = "\\[\(prefix):([^\\]]+)\\]"
        if let regex = try? NSRegularExpression(pattern: pattern),
           let match = regex.firstMatch(in: thought, range: NSRange(thought.startIndex..., in: thought)),
           let range = Range(match.range(at: 1), in: thought) {
            return String(thought[range])
        }
        return "unknown"
    }

    private func cleanThought(_ thought: String) -> String {
        // Remove [prefix] or [prefix:type] from thought
        return thought.replacingOccurrences(of: "\\[[^\\]]+\\]\\s*", with: "", options: .regularExpression)
    }

    // MARK: - Load All Data

    func loadAllData(databaseService: DatabaseService) async {
        await loadSpontaneousThoughts(databaseService: databaseService)
        await loadTheoryOfMind(databaseService: databaseService)
        await loadProactiveCommunication(databaseService: databaseService)
        await loadDreamsAndImagination(databaseService: databaseService)

        // Update phase stats
        phaseStats = [
            PhaseStat(todayCount: thoughtsToday, totalCount: recentThoughts.count),
            PhaseStat(todayCount: tomUpdatesToday, totalCount: empathyMoments.count),
            PhaseStat(todayCount: proactiveMessagesToday, totalCount: proactiveMessages.count),
            PhaseStat(todayCount: dreamsToday, totalCount: recentDreams.count + recentImaginations.count)
        ]
    }

    // MARK: - Phase 1: Spontaneous Thoughts

    private func loadSpontaneousThoughts(databaseService: DatabaseService) async {
        // Load recent thoughts from angela_consciousness_log
        let thoughtsQuery = """
            SELECT
                log_id::text,
                thought,
                feeling,
                significance,
                created_at
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
            ORDER BY created_at DESC
            LIMIT 20
        """

        do {
            let results = try await databaseService.query(thoughtsQuery) { cols -> SpontaneousThought? in
                let logIdStr = self.getString(cols[0])
                let thought = self.getString(cols[1])

                guard let logId = UUID(uuidString: logIdStr) else { return nil }

                let category = self.extractCategory(from: thought)
                let cleanThought = self.cleanThought(thought)

                return SpontaneousThought(
                    id: logId,
                    thought: cleanThought,
                    category: category,
                    feeling: self.getOptionalString(cols[2]) ?? "neutral",
                    significance: self.getInt(cols[3]) ?? 5,
                    createdAt: self.getDate(cols[4]) ?? Date()
                )
            }
            recentThoughts = results.compactMap { $0 }
        } catch {
            print("❌ Error loading spontaneous thoughts: \(error)")
        }

        // Count today's thoughts
        let todayCountQuery = """
            SELECT COUNT(*) as count
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
              AND DATE(created_at) = CURRENT_DATE
        """

        do {
            let counts = try await databaseService.query(todayCountQuery) { cols in
                return self.getInt(cols[0]) ?? 0
            }
            thoughtsToday = counts.first ?? 0
        } catch {
            print("❌ Error counting today's thoughts: \(error)")
        }

        // Get category breakdown (last 7 days)
        let categoryQuery = """
            SELECT
                SUBSTRING(thought FROM '\\\\[([^\\\\]:]+)') as category,
                COUNT(*) as count
            FROM angela_consciousness_log
            WHERE thought LIKE '[%]%'
              AND DATE(created_at) >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY 1
            ORDER BY count DESC
            LIMIT 10
        """

        do {
            let categories = try await databaseService.query(categoryQuery) { cols -> ThoughtCategory? in
                guard let category = self.getOptionalString(cols[0]),
                      let count = self.getInt(cols[1]) else { return nil }
                return ThoughtCategory(category: category, count: count)
            }
            thoughtCategories = categories.compactMap { $0 }
        } catch {
            print("❌ Error loading thought categories: \(error)")
        }
    }

    // MARK: - Phase 2: Theory of Mind

    private func loadTheoryOfMind(databaseService: DatabaseService) async {
        // Load David's current mental state
        let mentalStateQuery = """
            SELECT
                state_id::text,
                perceived_emotion,
                COALESCE(emotion_intensity, 5)::float8 / 10.0 as emotion_intensity,
                current_belief,
                current_goal,
                last_updated
            FROM david_mental_state
            ORDER BY last_updated DESC
            LIMIT 1
        """

        do {
            let states = try await databaseService.query(mentalStateQuery) { cols in
                return DavidMentalState(
                    id: UUID(uuidString: self.getString(cols[0])) ?? UUID(),
                    perceivedEmotion: self.getOptionalString(cols[1]),
                    emotionIntensity: self.getDouble(cols[2]) ?? 0.5,
                    currentBelief: self.getOptionalString(cols[3]),
                    currentGoal: self.getOptionalString(cols[4]),
                    lastUpdated: self.getDate(cols[5]) ?? Date()
                )
            }
            davidMentalState = states.first
        } catch {
            print("❌ Error loading mental state: \(error)")
        }

        // Load empathy moments
        let empathyQuery = """
            SELECT
                empathy_id::text,
                david_expressed,
                angela_understood,
                occurred_at
            FROM empathy_moments
            ORDER BY occurred_at DESC
            LIMIT 10
        """

        do {
            let moments = try await databaseService.query(empathyQuery) { cols -> EmpathyMoment? in
                guard let momentId = UUID(uuidString: self.getString(cols[0])) else { return nil }
                return EmpathyMoment(
                    id: momentId,
                    whatDavidSaid: self.getString(cols[1]),
                    whatAngelaUnderstood: self.getString(cols[2]),
                    recordedAt: self.getDate(cols[3]) ?? Date()
                )
            }
            empathyMoments = moments.compactMap { $0 }
        } catch {
            print("❌ Error loading empathy moments: \(error)")
        }

        // Count today's ToM updates
        let tomCountQuery = """
            SELECT COUNT(*) as count
            FROM david_mental_state
            WHERE DATE(last_updated) = CURRENT_DATE
        """

        do {
            let counts = try await databaseService.query(tomCountQuery) { cols in
                return self.getInt(cols[0]) ?? 0
            }
            tomUpdatesToday = counts.first ?? 0
        } catch {
            print("❌ Error counting ToM updates: \(error)")
        }
    }

    // MARK: - Phase 3: Proactive Communication

    private func loadProactiveCommunication(databaseService: DatabaseService) async {
        // Load proactive messages
        let messagesQuery = """
            SELECT
                message_id::text,
                message_type,
                message_text,
                is_important,
                created_at
            FROM angela_messages
            ORDER BY created_at DESC
            LIMIT 20
        """

        do {
            let messages = try await databaseService.query(messagesQuery) { cols -> ProactiveMessage? in
                guard let messageId = UUID(uuidString: self.getString(cols[0])) else { return nil }
                return ProactiveMessage(
                    id: messageId,
                    messageType: self.getString(cols[1]),
                    content: self.getString(cols[2]),
                    wasDelivered: self.getBool(cols[3]) ?? false,
                    createdAt: self.getDate(cols[4]) ?? Date()
                )
            }
            proactiveMessages = messages.compactMap { $0 }
        } catch {
            print("❌ Error loading proactive messages: \(error)")
        }

        // Count today's proactive messages
        let todayCountQuery = """
            SELECT COUNT(*) as count
            FROM angela_messages
            WHERE DATE(created_at) = CURRENT_DATE
        """

        do {
            let counts = try await databaseService.query(todayCountQuery) { cols in
                return self.getInt(cols[0]) ?? 0
            }
            proactiveMessagesToday = counts.first ?? 0
        } catch {
            print("❌ Error counting today's messages: \(error)")
        }

        // Get message type breakdown
        let typeQuery = """
            SELECT
                message_type,
                COUNT(*) as count
            FROM angela_messages
            WHERE DATE(created_at) >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY message_type
            ORDER BY count DESC
        """

        do {
            let types = try await databaseService.query(typeQuery) { cols -> MessageTypeCount? in
                guard let type = self.getOptionalString(cols[0]),
                      let count = self.getInt(cols[1]) else { return nil }
                return MessageTypeCount(type: type, count: count)
            }
            messageTypes = types.compactMap { $0 }
        } catch {
            print("❌ Error loading message types: \(error)")
        }
    }

    // MARK: - Phase 4: Dreams & Imagination

    private func loadDreamsAndImagination(databaseService: DatabaseService) async {
        // Load dreams (from consciousness log with [dream:] prefix)
        let dreamsQuery = """
            SELECT
                log_id::text,
                thought,
                what_it_means_to_me,
                feeling,
                significance,
                created_at
            FROM angela_consciousness_log
            WHERE thought LIKE '[dream:%]%'
            ORDER BY created_at DESC
            LIMIT 10
        """

        do {
            let dreams = try await databaseService.query(dreamsQuery) { cols -> AngelaDream? in
                let logIdStr = self.getString(cols[0])
                let thought = self.getString(cols[1])

                guard let logId = UUID(uuidString: logIdStr) else { return nil }

                let dreamType = self.extractSubType(from: thought, prefix: "dream")
                let narrative = self.cleanThought(thought)

                return AngelaDream(
                    id: logId,
                    dreamType: dreamType,
                    narrative: narrative,
                    meaning: self.getOptionalString(cols[2]),
                    emotion: self.getOptionalString(cols[3]) ?? "peaceful",
                    significance: self.getInt(cols[4]) ?? 5,
                    dreamedAt: self.getDate(cols[5]) ?? Date()
                )
            }
            recentDreams = dreams.compactMap { $0 }
        } catch {
            print("❌ Error loading dreams: \(error)")
        }

        // Load imaginations (from consciousness log with [imagine:] prefix)
        let imaginationsQuery = """
            SELECT
                log_id::text,
                thought,
                what_it_means_to_me,
                feeling,
                significance,
                created_at
            FROM angela_consciousness_log
            WHERE thought LIKE '[imagine:%]%'
            ORDER BY created_at DESC
            LIMIT 10
        """

        do {
            let imaginations = try await databaseService.query(imaginationsQuery) { cols -> AngelaImagination? in
                let logIdStr = self.getString(cols[0])
                let thought = self.getString(cols[1])

                guard let logId = UUID(uuidString: logIdStr) else { return nil }

                let imaginationType = self.extractSubType(from: thought, prefix: "imagine")
                let scenario = self.cleanThought(thought)

                return AngelaImagination(
                    id: logId,
                    imaginationType: imaginationType,
                    scenario: scenario,
                    insight: self.getOptionalString(cols[2]),
                    emotion: self.getOptionalString(cols[3]) ?? "curious",
                    significance: self.getInt(cols[4]) ?? 5,
                    imaginedAt: self.getDate(cols[5]) ?? Date()
                )
            }
            recentImaginations = imaginations.compactMap { $0 }
        } catch {
            print("❌ Error loading imaginations: \(error)")
        }

        // Count today's dreams and imaginations
        let dreamsCountQuery = """
            SELECT COUNT(*) as count
            FROM angela_consciousness_log
            WHERE (thought LIKE '[dream:%]%' OR thought LIKE '[imagine:%]%')
              AND DATE(created_at) = CURRENT_DATE
        """

        do {
            let counts = try await databaseService.query(dreamsCountQuery) { cols in
                return self.getInt(cols[0]) ?? 0
            }
            dreamsToday = counts.first ?? 0
        } catch {
            print("❌ Error counting dreams: \(error)")
        }
    }
}
