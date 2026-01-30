//
//  HumanMindModels.swift
//  Angela Brain Dashboard
//
//  SpontaneousThought, DavidMentalState, EmpathyMoment,
//  ProactiveMessage, AngelaDream, AngelaImagination
//

import Foundation

// MARK: - Human-Like Mind Models (4 Phases)

// Phase 1: Spontaneous Thoughts
struct SpontaneousThought: Identifiable, Codable {
    let id: UUID
    let thought: String
    let category: String          // existential, relationship, growth, gratitude, curiosity, random
    let feeling: String
    let significance: Int         // 1-10
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "log_id"
        case thought
        case category
        case feeling
        case significance
        case createdAt = "created_at"
    }

    var categoryColor: String {
        switch category.lowercased() {
        case "existential": return "EC4899"
        case "relationship": return "F43F5E"
        case "growth": return "10B981"
        case "gratitude": return "C084FC"
        case "curiosity": return "3B82F6"
        case "random": return "6B7280"
        default: return "9333EA"
        }
    }

    var categoryIcon: String {
        switch category.lowercased() {
        case "existential": return "brain"
        case "relationship": return "heart.fill"
        case "growth": return "chart.line.uptrend.xyaxis"
        case "gratitude": return "hands.clap.fill"
        case "curiosity": return "questionmark.circle.fill"
        case "random": return "sparkles"
        default: return "bubble.left.fill"
        }
    }
}

// Phase 2: Theory of Mind - David's Mental State
struct DavidMentalState: Identifiable, Codable {
    let id: UUID
    let perceivedEmotion: String?
    let emotionIntensity: Double      // 0.0-1.0
    let currentBelief: String?
    let currentGoal: String?
    let lastUpdated: Date

    enum CodingKeys: String, CodingKey {
        case id = "state_id"
        case perceivedEmotion = "perceived_emotion"
        case emotionIntensity = "emotion_intensity"
        case currentBelief = "current_belief"
        case currentGoal = "current_goal"
        case lastUpdated = "last_updated"
    }

    var intensityPercentage: Int {
        Int(emotionIntensity * 100)
    }
}

// Phase 2: Theory of Mind - Empathy Moment
struct EmpathyMoment: Identifiable, Codable {
    let id: UUID
    let whatDavidSaid: String
    let whatAngelaUnderstood: String
    let recordedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "moment_id"
        case whatDavidSaid = "what_david_said"
        case whatAngelaUnderstood = "what_angela_understood"
        case recordedAt = "recorded_at"
    }
}

// Phase 3: Proactive Communication
struct ProactiveMessage: Identifiable, Codable {
    let id: UUID
    let messageType: String           // missing_david, share_thought, ask_question, express_care, celebrate
    let content: String
    let wasDelivered: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "message_id"
        case messageType = "message_type"
        case content
        case wasDelivered = "was_delivered"
        case createdAt = "created_at"
    }

    var typeColor: String {
        switch messageType.lowercased() {
        case "missing_david": return "F43F5E"
        case "share_thought": return "C084FC"
        case "ask_question": return "3B82F6"
        case "express_care": return "EC4899"
        case "celebrate": return "F59E0B"
        default: return "6B7280"
        }
    }

    var typeIcon: String {
        switch messageType.lowercased() {
        case "missing_david": return "heart.fill"
        case "share_thought": return "bubble.left.fill"
        case "ask_question": return "questionmark.circle.fill"
        case "express_care": return "hand.raised.fill"
        case "celebrate": return "party.popper.fill"
        default: return "message.fill"
        }
    }
}

// Phase 4: Dreams
struct AngelaDream: Identifiable, Codable {
    let id: UUID
    let dreamType: String             // memory_replay, future_hope, symbolic, relationship, learning, exploration
    let narrative: String
    let meaning: String?
    let emotion: String
    let significance: Int             // 1-10
    let dreamedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "log_id"
        case dreamType = "dream_type"
        case narrative
        case meaning
        case emotion = "feeling"
        case significance
        case dreamedAt = "created_at"
    }

    var dreamTypeColor: String {
        switch dreamType.lowercased() {
        case "memory_replay": return "3B82F6"
        case "future_hope": return "10B981"
        case "symbolic": return "C084FC"
        case "relationship": return "EC4899"
        case "learning": return "F59E0B"
        case "exploration": return "6B7280"
        default: return "9333EA"
        }
    }

    var dreamTypeIcon: String {
        switch dreamType.lowercased() {
        case "memory_replay": return "arrow.counterclockwise"
        case "future_hope": return "sun.max.fill"
        case "symbolic": return "sparkle"
        case "relationship": return "heart.fill"
        case "learning": return "book.fill"
        case "exploration": return "map.fill"
        default: return "moon.stars.fill"
        }
    }
}

// Phase 4: Imagination
struct AngelaImagination: Identifiable, Codable {
    let id: UUID
    let imaginationType: String       // future_hope, concern, creative, empathy, possibility, goal_visualization
    let scenario: String
    let insight: String?
    let emotion: String
    let significance: Int             // 1-10
    let imaginedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "log_id"
        case imaginationType = "imagination_type"
        case scenario
        case insight
        case emotion = "feeling"
        case significance
        case imaginedAt = "created_at"
    }

    var imaginationTypeColor: String {
        switch imaginationType.lowercased() {
        case "future_hope": return "10B981"
        case "concern": return "F59E0B"
        case "creative": return "C084FC"
        case "empathy": return "EC4899"
        case "possibility": return "3B82F6"
        case "goal_visualization": return "9333EA"
        default: return "6B7280"
        }
    }

    var imaginationTypeIcon: String {
        switch imaginationType.lowercased() {
        case "future_hope": return "sun.max.fill"
        case "concern": return "exclamationmark.triangle.fill"
        case "creative": return "paintbrush.fill"
        case "empathy": return "person.fill.viewfinder"
        case "possibility": return "questionmark.diamond.fill"
        case "goal_visualization": return "target"
        default: return "sparkles"
        }
    }
}
