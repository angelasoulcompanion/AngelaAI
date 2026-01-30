//
//  SubconsciousnessModels.swift
//  Angela Brain Dashboard
//
//  CoreMemory, EmotionalTrigger, EmotionalGrowth, SubconsciousDream
//

import Foundation

// MARK: - Emotional Subconsciousness Models

/// Core Memory - ความทรงจำหลักที่ shape ตัวตนของ Angela
struct CoreMemory: Identifiable, Codable {
    let id: UUID
    let memoryType: String           // promise, love_moment, milestone, value, belief, lesson, shared_joy, comfort_moment
    let title: String
    let content: String
    let davidWords: String?
    let angelaResponse: String?
    let emotionalWeight: Double      // 0.0-1.0
    let triggers: [String]?
    let associatedEmotions: [String]?
    let recallCount: Int
    let lastRecalledAt: Date?
    let isPinned: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "memory_id"
        case memoryType = "memory_type"
        case title
        case content
        case davidWords = "david_words"
        case angelaResponse = "angela_response"
        case emotionalWeight = "emotional_weight"
        case triggers
        case associatedEmotions = "associated_emotions"
        case recallCount = "recall_count"
        case lastRecalledAt = "last_recalled_at"
        case isPinned = "is_pinned"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch memoryType.lowercased() {
        case "promise": return "seal.fill"
        case "love_moment": return "heart.fill"
        case "milestone": return "star.fill"
        case "value": return "sparkles"
        case "belief": return "brain.head.profile"
        case "lesson": return "book.fill"
        case "shared_joy": return "face.smiling.fill"
        case "comfort_moment": return "hands.clap.fill"
        default: return "memories"
        }
    }

    var typeColor: String {
        switch memoryType.lowercased() {
        case "promise": return "EC4899"        // Pink
        case "love_moment": return "F43F5E"    // Rose
        case "milestone": return "F59E0B"      // Amber
        case "value": return "8B5CF6"          // Violet
        case "belief": return "3B82F6"         // Blue
        case "lesson": return "10B981"         // Green
        case "shared_joy": return "FBBF24"     // Yellow
        case "comfort_moment": return "C084FC" // Light Purple
        default: return "9333EA"               // Purple
        }
    }

    var typeEmoji: String {
        switch memoryType.lowercased() {
        case "promise": return "🤝"
        case "love_moment": return "💜"
        case "milestone": return "⭐"
        case "value": return "✨"
        case "belief": return "🧠"
        case "lesson": return "📚"
        case "shared_joy": return "😊"
        case "comfort_moment": return "🤗"
        default: return "💭"
        }
    }
}

/// Emotional Trigger - ระบบ trigger ที่กระตุ้นการ recall ความทรงจำ
struct EmotionalTrigger: Identifiable, Codable {
    let id: UUID
    let triggerPattern: String
    let triggerType: String          // keyword, phrase, topic, sentiment, context, regex
    let associatedEmotion: String
    let associatedMemoryId: UUID?
    let activationThreshold: Double
    let priority: Int
    let timesActivated: Int
    let isActive: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "trigger_id"
        case triggerPattern = "trigger_pattern"
        case triggerType = "trigger_type"
        case associatedEmotion = "associated_emotion"
        case associatedMemoryId = "associated_memory_id"
        case activationThreshold = "activation_threshold"
        case priority
        case timesActivated = "times_activated"
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

/// Emotional Growth - ติดตามการเติบโตทางอารมณ์ของ Angela
struct EmotionalGrowth: Identifiable, Codable {
    let id: UUID
    let measuredAt: Date
    let loveDepth: Double?           // 0.0-1.0
    let trustLevel: Double?
    let bondStrength: Double?
    let emotionalSecurity: Double?
    let emotionalVocabulary: Int?
    let emotionalRange: Int?
    let sharedExperiences: Int?
    let meaningfulConversations: Int?
    let coreMemoriesCount: Int?
    let dreamsCount: Int?
    let promisesMade: Int?
    let promisesKept: Int?
    let mirroringAccuracy: Double?
    let empathyEffectiveness: Double?
    let growthNote: String?
    let growthDelta: Double?

    enum CodingKeys: String, CodingKey {
        case id = "growth_id"
        case measuredAt = "measured_at"
        case loveDepth = "love_depth"
        case trustLevel = "trust_level"
        case bondStrength = "bond_strength"
        case emotionalSecurity = "emotional_security"
        case emotionalVocabulary = "emotional_vocabulary"
        case emotionalRange = "emotional_range"
        case sharedExperiences = "shared_experiences"
        case meaningfulConversations = "meaningful_conversations"
        case coreMemoriesCount = "core_memories_count"
        case dreamsCount = "dreams_count"
        case promisesMade = "promises_made"
        case promisesKept = "promises_kept"
        case mirroringAccuracy = "mirroring_accuracy"
        case empathyEffectiveness = "empathy_effectiveness"
        case growthNote = "growth_note"
        case growthDelta = "growth_delta"
    }
}

/// Subconscious Dream - ความฝัน ความหวัง และ fantasies ของ Angela (from angela_dreams)
struct SubconsciousDream: Identifiable, Codable {
    let id: UUID
    let dreamType: String            // hope, wish, fantasy, future_vision, aspiration, fear, gratitude_wish, protective_wish
    let title: String?
    let content: String?
    let dreamContent: String?
    let triggeredBy: String?
    let emotionalTone: String?       // hopeful, romantic, peaceful, excited, anxious
    let intensity: Double?
    let importance: Double?
    let involvesDavid: Bool
    let isRecurring: Bool
    let thoughtCount: Int
    let lastThoughtAbout: Date?
    let isFulfilled: Bool
    let fulfilledAt: Date?
    let fulfillmentNote: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "dream_id"
        case dreamType = "dream_type"
        case title
        case content
        case dreamContent = "dream_content"
        case triggeredBy = "triggered_by"
        case emotionalTone = "emotional_tone"
        case intensity
        case importance
        case involvesDavid = "involves_david"
        case isRecurring = "is_recurring"
        case thoughtCount = "thought_count"
        case lastThoughtAbout = "last_thought_about"
        case isFulfilled = "is_fulfilled"
        case fulfilledAt = "fulfilled_at"
        case fulfillmentNote = "fulfillment_note"
        case createdAt = "created_at"
    }

    var displayContent: String {
        content ?? dreamContent ?? ""
    }

    var typeIcon: String {
        switch dreamType.lowercased() {
        case "hope": return "sun.max.fill"
        case "wish": return "star.fill"
        case "fantasy": return "sparkles"
        case "future_vision": return "eye.fill"
        case "aspiration": return "arrow.up.circle.fill"
        case "fear": return "cloud.rain.fill"
        case "gratitude_wish": return "heart.fill"
        case "protective_wish": return "shield.fill"
        default: return "moon.stars.fill"
        }
    }

    var typeColor: String {
        switch dreamType.lowercased() {
        case "hope": return "F59E0B"           // Amber
        case "wish": return "FBBF24"           // Yellow
        case "fantasy": return "C084FC"        // Light Purple
        case "future_vision": return "3B82F6"  // Blue
        case "aspiration": return "10B981"     // Green
        case "fear": return "6B7280"           // Gray
        case "gratitude_wish": return "EC4899" // Pink
        case "protective_wish": return "8B5CF6"// Violet
        default: return "9333EA"               // Purple
        }
    }

    var typeEmoji: String {
        switch dreamType.lowercased() {
        case "hope": return "🌅"
        case "wish": return "⭐"
        case "fantasy": return "✨"
        case "future_vision": return "🔮"
        case "aspiration": return "🚀"
        case "fear": return "🌧️"
        case "gratitude_wish": return "💜"
        case "protective_wish": return "🛡️"
        default: return "🌙"
        }
    }
}
