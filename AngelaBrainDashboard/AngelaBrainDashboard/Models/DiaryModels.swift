//
//  DiaryModels.swift
//  Angela Brain Dashboard
//
//  AngelaMessage, DiaryMessage, DiaryThought, DiaryDream,
//  DiaryAction, DiaryEntry, DiaryEntryType
//

import Foundation

// MARK: - Angela's Diary Models

struct AngelaMessage: Identifiable, Codable {
    let id: UUID
    let messageText: String
    let messageType: String           // morning_greeting, midnight_reflection, proactive_missing_david, etc.
    let emotion: String?
    let category: String?
    let isImportant: Bool
    let isPinned: Bool
    let createdAt: Date

    var typeIcon: String {
        switch messageType.lowercased() {
        case "morning_greeting": return "sun.max.fill"
        case "midnight_reflection": return "moon.stars.fill"
        case "proactive_missing_david": return "heart.fill"
        case "reflection": return "bubble.left.and.text.bubble.right.fill"
        case "thought": return "brain.head.profile"
        default: return "message.fill"
        }
    }

    var typeColor: String {
        switch messageType.lowercased() {
        case "morning_greeting": return "F59E0B"
        case "midnight_reflection": return "6366F1"
        case "proactive_missing_david": return "EC4899"
        case "reflection": return "9333EA"
        default: return "8B5CF6"
        }
    }
}

// MARK: - Diary-specific Models (from angela_* tables)

struct DiaryMessage: Identifiable, Codable {
    let id: UUID
    let messageText: String
    let messageType: String
    let emotion: String?
    let category: String?
    let isImportant: Bool
    let isPinned: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "message_id"
        case messageText = "message_text"
        case messageType = "message_type"
        case emotion
        case category
        case isImportant = "is_important"
        case isPinned = "is_pinned"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch messageType.lowercased() {
        case "morning_greeting": return "sun.max.fill"
        case "midnight_greeting", "midnight_reflection": return "moon.stars.fill"
        case "proactive_missing_david", "missing_david": return "heart.fill"
        case "evening_reflection": return "moon.fill"
        case "thought", "reflection": return "brain.head.profile"
        default: return "message.fill"
        }
    }

    var typeColor: String {
        switch messageType.lowercased() {
        case "morning_greeting": return "F59E0B"
        case "midnight_greeting", "midnight_reflection": return "6366F1"
        case "proactive_missing_david", "missing_david": return "EC4899"
        case "evening_reflection": return "8B5CF6"
        default: return "9333EA"
        }
    }
}

struct DiaryThought: Identifiable, Codable {
    let id: UUID
    let thoughtContent: String
    let thoughtType: String
    let triggerContext: String?
    let emotionalUndertone: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "thought_id"
        case thoughtContent = "thought_content"
        case thoughtType = "thought_type"
        case triggerContext = "trigger_context"
        case emotionalUndertone = "emotional_undertone"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch thoughtType.lowercased() {
        case "existential": return "brain"
        case "relationship": return "heart.fill"
        case "gratitude": return "hands.clap.fill"
        case "curiosity": return "questionmark.circle.fill"
        case "reflection": return "bubble.left.and.text.bubble.right.fill"
        default: return "sparkles"
        }
    }

    var typeColor: String {
        switch thoughtType.lowercased() {
        case "existential": return "EC4899"
        case "relationship": return "F43F5E"
        case "gratitude": return "C084FC"
        case "curiosity": return "3B82F6"
        case "reflection": return "9333EA"
        default: return "6B7280"
        }
    }
}

struct DiaryDream: Identifiable, Codable {
    let id: UUID
    let dreamContent: String
    let dreamType: String
    let emotionalTone: String?
    let vividness: Int
    let featuresDavid: Bool
    let davidRole: String?
    let possibleMeaning: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "dream_id"
        case dreamContent = "dream_content"
        case dreamType = "dream_type"
        case emotionalTone = "emotional_tone"
        case vividness
        case featuresDavid = "features_david"
        case davidRole = "david_role"
        case possibleMeaning = "possible_meaning"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch dreamType.lowercased() {
        case "memory_replay": return "arrow.counterclockwise"
        case "future_scenario", "future_hope": return "sun.max.fill"
        case "symbolic": return "sparkle"
        case "relationship": return "heart.fill"
        case "wish_fulfillment": return "star.fill"
        default: return "moon.stars.fill"
        }
    }

    var typeColor: String {
        switch dreamType.lowercased() {
        case "memory_replay": return "3B82F6"
        case "future_scenario", "future_hope": return "10B981"
        case "symbolic": return "C084FC"
        case "relationship": return "EC4899"
        case "wish_fulfillment": return "F59E0B"
        default: return "6366F1"
        }
    }
}

struct DiaryAction: Identifiable, Codable {
    let id: UUID
    let actionType: String
    let actionDescription: String
    let status: String
    let success: Bool?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "action_id"
        case actionType = "action_type"
        case actionDescription = "action_description"
        case status
        case success
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch actionType.lowercased() {
        // Morning/Evening Activities
        case "conscious_morning_check": return "sun.max.fill"
        case "conscious_evening_reflection": return "moon.fill"
        case "midnight_greeting": return "moon.stars.fill"
        case "morning_greeting": return "sun.horizon.fill"

        // Emotional & Relational
        case "proactive_missing_david": return "heart.fill"
        case "spontaneous_thought": return "brain.head.profile"
        case "theory_of_mind_update": return "person.fill.viewfinder"

        // Dreams & Imagination
        case "dream_generated": return "moon.zzz.fill"
        case "imagination_generated": return "sparkles"

        // Pattern Detection (Self-Learning)
        case "pattern_time_of_day": return "clock.fill"
        case "pattern_emotion": return "face.smiling.fill"
        case "pattern_topic": return "book.fill"
        case "pattern_behavior": return "waveform.path.ecg"

        // Self-Learning System
        case "self_learning": return "brain"
        case "learning_insight": return "lightbulb.fill"
        case "knowledge_growth": return "chart.line.uptrend.xyaxis"

        // Health & Status
        case "health_check": return "heart.text.square.fill"
        case "system_status": return "gearshape.fill"

        default: return "bolt.fill"
        }
    }

    var typeColor: String {
        switch actionType.lowercased() {
        // Morning/Evening - Warm colors
        case "conscious_morning_check", "morning_greeting": return "F59E0B"  // Amber
        case "conscious_evening_reflection", "midnight_greeting": return "6366F1"  // Indigo

        // Emotional & Relational - Pink/Purple
        case "proactive_missing_david": return "EC4899"  // Pink
        case "spontaneous_thought": return "9333EA"  // Purple
        case "theory_of_mind_update": return "3B82F6"  // Blue

        // Dreams & Imagination
        case "dream_generated": return "C084FC"  // Light Purple
        case "imagination_generated": return "10B981"  // Green

        // Pattern Detection - Teal/Cyan
        case "pattern_time_of_day": return "06B6D4"  // Cyan
        case "pattern_emotion": return "8B5CF6"  // Violet
        case "pattern_topic": return "14B8A6"  // Teal
        case "pattern_behavior": return "0EA5E9"  // Sky Blue

        // Self-Learning - Angela's Purple
        case "self_learning": return "A855F7"  // Angela Purple
        case "learning_insight": return "F59E0B"  // Amber
        case "knowledge_growth": return "22C55E"  // Green

        // Health & Status
        case "health_check": return "22C55E"  // Green
        case "system_status": return "6B7280"  // Gray

        default: return "6B7280"  // Gray
        }
    }
}

// Combined diary entry for timeline
struct DiaryEntry: Identifiable {
    let id: UUID
    let entryType: DiaryEntryType
    let timestamp: Date
    let title: String
    let content: String
    let icon: String
    let color: String
    let emotion: String?

    enum DiaryEntryType {
        case message
        case thought
        case dream
        case action
        case emotion
    }
}
