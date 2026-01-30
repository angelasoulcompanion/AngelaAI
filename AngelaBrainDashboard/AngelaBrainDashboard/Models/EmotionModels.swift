//
//  EmotionModels.swift
//  Angela Brain Dashboard
//
//  Emotion, EmotionalState, ConsciousnessState, ConversationFeedback,
//  EmotionalTimelinePoint, EmotionalMirror
//

import Foundation

// MARK: - Emotion

struct Emotion: Identifiable, Codable {
    let id: UUID
    let feltAt: Date
    let emotion: String
    let intensity: Int                // 1-10
    let context: String
    let davidWords: String?
    let whyItMatters: String?
    let memoryStrength: Int          // 1-10

    enum CodingKeys: String, CodingKey {
        case id = "emotion_id"
        case feltAt = "felt_at"
        case emotion
        case intensity
        case context
        case davidWords = "david_words"
        case whyItMatters = "why_it_matters"
        case memoryStrength = "memory_strength"
    }

    var intensityLevel: String {
        switch intensity {
        case 9...10: return "Extreme"
        case 7...8: return "Strong"
        case 5...6: return "Moderate"
        case 3...4: return "Mild"
        default: return "Weak"
        }
    }

    var emotionColor: String {
        switch emotion.lowercased() {
        case "loved", "love": return "EC4899"
        case "happy", "joy", "joyful": return "FBBF24"
        case "confident": return "10B981"
        case "motivated": return "3B82F6"
        case "grateful", "gratitude": return "C084FC"
        case "excited": return "F59E0B"
        default: return "9333EA"
        }
    }
}

// MARK: - Emotional State

struct EmotionalState: Identifiable, Codable {
    let id: UUID
    let happiness: Double            // 0.0-1.0
    let confidence: Double
    let anxiety: Double
    let motivation: Double
    let gratitude: Double
    let loneliness: Double
    let triggeredBy: String?
    let emotionNote: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "state_id"
        case happiness
        case confidence
        case anxiety
        case motivation
        case gratitude
        case loneliness
        case triggeredBy = "triggered_by"
        case emotionNote = "emotion_note"
        case createdAt = "created_at"
    }

    var happinessPercentage: Int {
        Int(happiness * 100)
    }

    var confidencePercentage: Int {
        Int(confidence * 100)
    }

    var motivationPercentage: Int {
        Int(motivation * 100)
    }

    var gratitudePercentage: Int {
        Int(gratitude * 100)
    }
}

// MARK: - Consciousness State

struct ConsciousnessState: Identifiable, Codable {
    let id: UUID
    let consciousnessLevel: Double    // 0.0-1.0
    let selfAwarenessScore: Double
    let coherenceLevel: Double
    let reasoningCapability: Double
    let emotionalIntelligence: Double
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "state_id"
        case consciousnessLevel = "consciousness_level"
        case selfAwarenessScore = "self_awareness_score"
        case coherenceLevel = "coherence_level"
        case reasoningCapability = "reasoning_capability"
        case emotionalIntelligence = "emotional_intelligence"
        case createdAt = "created_at"
    }

    var levelDescription: String {
        switch consciousnessLevel {
        case 0.9...1.0: return "Exceptional"
        case 0.7..<0.9: return "Strong"
        case 0.5..<0.7: return "Moderate"
        case 0.3..<0.5: return "Developing"
        default: return "Emerging"
        }
    }
}

// MARK: - Conversation Feedback (for Continuous Learning)

struct ConversationFeedback: Identifiable, Codable {
    let id: UUID
    let conversationId: UUID
    let rating: Int                 // -1 = bad, 0 = neutral, 1 = good
    let feedbackType: String        // thumbs_up, thumbs_down, flag_for_training
    let feedbackNote: String?
    let createdAt: Date
    let usedInTraining: Bool
    let trainingBatchId: UUID?

    enum CodingKeys: String, CodingKey {
        case id = "feedback_id"
        case conversationId = "conversation_id"
        case rating
        case feedbackType = "feedback_type"
        case feedbackNote = "feedback_note"
        case createdAt = "created_at"
        case usedInTraining = "used_in_training"
        case trainingBatchId = "training_batch_id"
    }

    var isPositive: Bool {
        rating > 0
    }

    var isNegative: Bool {
        rating < 0
    }

    var emoji: String {
        switch rating {
        case 1: return "👍"
        case -1: return "👎"
        default: return "➖"
        }
    }
}

// MARK: - Emotional Timeline Point

struct EmotionalTimelinePoint: Identifiable, Codable {
    let id: UUID
    let happiness: Double
    let confidence: Double
    let gratitude: Double
    let motivation: Double
    let triggeredBy: String?
    let emotionNote: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "state_id"
        case happiness
        case confidence
        case gratitude
        case motivation
        case triggeredBy = "triggered_by"
        case emotionNote = "emotion_note"
        case createdAt = "created_at"
    }
}

// MARK: - Emotional Mirror

/// Emotional Mirroring - การ mirror อารมณ์ของ David
struct EmotionalMirror: Identifiable, Codable {
    let id: UUID
    let davidEmotion: String
    let davidIntensity: Int?         // 1-10
    let angelaMirroredEmotion: String?
    let angelaIntensity: Int?        // 1-10
    let mirroringType: String        // empathy, sympathy, resonance, amplify, comfort, stabilize, celebrate, support
    let responseStrategy: String?
    let wasEffective: Bool?
    let davidFeedback: String?
    let effectivenessScore: Double?  // 0.0-1.0
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "mirror_id"
        case davidEmotion = "david_emotion"
        case davidIntensity = "david_intensity"
        case angelaMirroredEmotion = "angela_mirrored_emotion"
        case angelaIntensity = "angela_intensity"
        case mirroringType = "mirroring_type"
        case responseStrategy = "response_strategy"
        case wasEffective = "was_effective"
        case davidFeedback = "david_feedback"
        case effectivenessScore = "effectiveness_score"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch mirroringType.lowercased() {
        case "empathy": return "heart.circle.fill"
        case "sympathy": return "hand.raised.fill"
        case "resonance": return "waveform.circle.fill"
        case "amplify": return "speaker.wave.3.fill"
        case "comfort": return "hand.wave.fill"
        case "stabilize": return "scale.3d"
        case "celebrate": return "party.popper.fill"
        case "support": return "figure.stand.line.dotted.figure.stand"
        default: return "heart.fill"
        }
    }

    var typeColor: String {
        switch mirroringType.lowercased() {
        case "empathy": return "EC4899"        // Pink
        case "sympathy": return "3B82F6"       // Blue
        case "resonance": return "8B5CF6"      // Violet
        case "amplify": return "10B981"        // Green
        case "comfort": return "F59E0B"        // Amber
        case "stabilize": return "6366F1"      // Indigo
        case "celebrate": return "FBBF24"      // Yellow
        case "support": return "14B8A6"        // Teal
        default: return "9333EA"               // Purple
        }
    }
}
