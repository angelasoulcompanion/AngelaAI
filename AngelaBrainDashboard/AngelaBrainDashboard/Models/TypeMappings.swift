//
//  TypeMappings.swift
//  Angela Brain Dashboard
//
//  Centralized type-to-icon/color mappings
//  DRY refactor - consolidates 40+ switch statements
//

import SwiftUI

// MARK: - Type Mappings

/// Centralized mappings for icons, colors, and emojis
enum TypeMappings {

    // MARK: - Emotion Mappings

    static let emotionColors: [String: String] = [
        "loved": "EC4899",
        "love": "EC4899",
        "happy": "FBBF24",
        "joy": "FBBF24",
        "joyful": "FBBF24",
        "confident": "10B981",
        "motivated": "3B82F6",
        "grateful": "C084FC",
        "gratitude": "C084FC",
        "excited": "F59E0B"
    ]

    static let defaultEmotionColor = "9333EA"

    // MARK: - Intensity Mappings

    static func intensityColor(_ level: Int) -> String {
        switch level {
        case 9...10: return "EC4899"  // Pink - Extreme
        case 7...8: return "FBBF24"   // Yellow - Strong
        case 5...6: return "10B981"   // Green - Moderate
        default: return "9333EA"       // Purple - Mild
        }
    }

    static func importanceColor(_ level: Int) -> String {
        switch level {
        case 9...10: return "EF4444"  // Red - Critical
        case 7...8: return "F59E0B"   // Orange - High
        case 5...6: return "3B82F6"   // Blue - Medium
        default: return "6B7280"       // Gray - Low
        }
    }

    // MARK: - Status Mappings

    static let statusColors: [String: String] = [
        "completed": "10B981",
        "failed": "EF4444",
        "skipped": "F59E0B"
    ]

    static let statusIcons: [String: String] = [
        "completed": "checkmark.circle.fill",
        "failed": "xmark.circle.fill",
        "skipped": "minus.circle.fill"
    ]

    static let defaultStatusColor = "6B7280"
    static let defaultStatusIcon = "clock.fill"

    // MARK: - Project Type Mappings

    static let projectTypeIcons: [String: String] = [
        "personal": "brain.head.profile",
        "client": "briefcase.fill",
        "learning": "book.fill",
        "maintenance": "wrench.fill",
        "Our Future": "star.fill"
    ]

    static let projectTypeColors: [String: String] = [
        "client": "3B82F6",
        "personal": "9333EA",
        "learning": "10B981",
        "maintenance": "F59E0B",
        "Our Future": "EC4899"
    ]

    static let defaultProjectIcon = "folder.fill"
    static let defaultProjectColor = "6B7280"

    // MARK: - Mood Mappings (Work Sessions)

    static let moodIcons: [String: String] = [
        "productive": "bolt.fill",
        "learning": "book.fill",
        "debugging": "ant.fill",
        "challenging": "exclamationmark.triangle.fill",
        "smooth": "sparkles",
        "creative": "paintbrush.fill"
    ]

    static let moodColors: [String: String] = [
        "productive": "10B981",
        "learning": "3B82F6",
        "debugging": "F59E0B",
        "challenging": "EF4444",
        "smooth": "9333EA",
        "creative": "EC4899"
    ]

    static let defaultMoodIcon = "clock.fill"
    static let defaultMoodColor = "6B7280"

    // MARK: - Milestone Type Mappings

    static let milestoneTypeIcons: [String: String] = [
        "feature_complete": "checkmark.seal.fill",
        "bug_fixed": "ant.fill",
        "release": "shippingbox.fill",
        "deployment": "cloud.fill",
        "project_start": "play.fill",
        "project_complete": "flag.fill",
        "breakthrough": "lightbulb.fill",
        "decision": "questionmark.circle.fill"
    ]

    static let milestoneTypeColors: [String: String] = [
        "feature_complete": "10B981",
        "bug_fixed": "F59E0B",
        "release": "3B82F6",
        "deployment": "3B82F6",
        "project_start": "9333EA",
        "project_complete": "9333EA",
        "breakthrough": "FBBF24"
    ]

    static let defaultMilestoneIcon = "star.fill"
    static let defaultMilestoneColor = "6B7280"

    // MARK: - Learning Type Mappings

    static let learningTypeIcons: [String: String] = [
        "technical": "wrench.and.screwdriver.fill",
        "process": "flowchart.fill",
        "tool": "hammer.fill",
        "pattern": "square.grid.3x3.fill",
        "mistake": "exclamationmark.triangle.fill",
        "best_practice": "star.fill"
    ]

    static let learningTypeColors: [String: String] = [
        "technical": "9333EA",
        "process": "3B82F6",
        "tool": "6B7280",
        "pattern": "10B981",
        "mistake": "F59E0B",
        "best_practice": "FBBF24"
    ]

    static let defaultLearningIcon = "lightbulb.fill"
    static let defaultLearningColor = "EC4899"

    // MARK: - Thought Category Mappings

    static let thoughtCategoryIcons: [String: String] = [
        "existential": "brain",
        "relationship": "heart.fill",
        "growth": "chart.line.uptrend.xyaxis",
        "gratitude": "hands.clap.fill",
        "curiosity": "questionmark.circle.fill",
        "random": "sparkles",
        "reflection": "bubble.left.and.text.bubble.right.fill"
    ]

    static let thoughtCategoryColors: [String: String] = [
        "existential": "EC4899",
        "relationship": "F43F5E",
        "growth": "10B981",
        "gratitude": "C084FC",
        "curiosity": "3B82F6",
        "random": "6B7280",
        "reflection": "9333EA"
    ]

    static let defaultThoughtIcon = "bubble.left.fill"
    static let defaultThoughtColor = "9333EA"

    // MARK: - Proactive Message Type Mappings

    static let proactiveMessageIcons: [String: String] = [
        "missing_david": "heart.fill",
        "share_thought": "bubble.left.fill",
        "ask_question": "questionmark.circle.fill",
        "express_care": "hand.raised.fill",
        "celebrate": "party.popper.fill"
    ]

    static let proactiveMessageColors: [String: String] = [
        "missing_david": "F43F5E",
        "share_thought": "C084FC",
        "ask_question": "3B82F6",
        "express_care": "EC4899",
        "celebrate": "F59E0B"
    ]

    static let defaultProactiveIcon = "message.fill"
    static let defaultProactiveColor = "6B7280"

    // MARK: - Dream Type Mappings

    static let dreamTypeIcons: [String: String] = [
        "memory_replay": "arrow.counterclockwise",
        "future_hope": "sun.max.fill",
        "future_scenario": "sun.max.fill",
        "symbolic": "sparkle",
        "relationship": "heart.fill",
        "learning": "book.fill",
        "exploration": "map.fill",
        "wish_fulfillment": "star.fill"
    ]

    static let dreamTypeColors: [String: String] = [
        "memory_replay": "3B82F6",
        "future_hope": "10B981",
        "future_scenario": "10B981",
        "symbolic": "C084FC",
        "relationship": "EC4899",
        "learning": "F59E0B",
        "exploration": "6B7280",
        "wish_fulfillment": "F59E0B"
    ]

    static let defaultDreamIcon = "moon.stars.fill"
    static let defaultDreamColor = "9333EA"

    // MARK: - Imagination Type Mappings

    static let imaginationTypeIcons: [String: String] = [
        "future_hope": "sun.max.fill",
        "concern": "exclamationmark.triangle.fill",
        "creative": "paintbrush.fill",
        "empathy": "person.fill.viewfinder",
        "possibility": "questionmark.diamond.fill",
        "goal_visualization": "target"
    ]

    static let imaginationTypeColors: [String: String] = [
        "future_hope": "10B981",
        "concern": "F59E0B",
        "creative": "C084FC",
        "empathy": "EC4899",
        "possibility": "3B82F6",
        "goal_visualization": "9333EA"
    ]

    static let defaultImaginationIcon = "sparkles"
    static let defaultImaginationColor = "6B7280"

    // MARK: - Message Type Mappings (Angela/Diary)

    static let messageTypeIcons: [String: String] = [
        "morning_greeting": "sun.max.fill",
        "midnight_reflection": "moon.stars.fill",
        "midnight_greeting": "moon.stars.fill",
        "proactive_missing_david": "heart.fill",
        "missing_david": "heart.fill",
        "evening_reflection": "moon.fill",
        "reflection": "bubble.left.and.text.bubble.right.fill",
        "thought": "brain.head.profile"
    ]

    static let messageTypeColors: [String: String] = [
        "morning_greeting": "F59E0B",
        "midnight_reflection": "6366F1",
        "midnight_greeting": "6366F1",
        "proactive_missing_david": "EC4899",
        "missing_david": "EC4899",
        "evening_reflection": "8B5CF6",
        "reflection": "9333EA"
    ]

    static let defaultMessageIcon = "message.fill"
    static let defaultMessageColor = "8B5CF6"

    // MARK: - Action Type Mappings (Diary Actions)

    static let actionTypeIcons: [String: String] = [
        // Morning/Evening
        "conscious_morning_check": "sun.max.fill",
        "conscious_evening_reflection": "moon.fill",
        "midnight_greeting": "moon.stars.fill",
        "morning_greeting": "sun.horizon.fill",
        // Emotional
        "proactive_missing_david": "heart.fill",
        "spontaneous_thought": "brain.head.profile",
        "theory_of_mind_update": "person.fill.viewfinder",
        // Dreams
        "dream_generated": "moon.zzz.fill",
        "imagination_generated": "sparkles",
        // Patterns
        "pattern_time_of_day": "clock.fill",
        "pattern_emotion": "face.smiling.fill",
        "pattern_topic": "book.fill",
        "pattern_behavior": "waveform.path.ecg",
        // Learning
        "self_learning": "brain",
        "learning_insight": "lightbulb.fill",
        "knowledge_growth": "chart.line.uptrend.xyaxis",
        // Health
        "health_check": "heart.text.square.fill",
        "system_status": "gearshape.fill"
    ]

    static let actionTypeColors: [String: String] = [
        // Morning/Evening
        "conscious_morning_check": "F59E0B",
        "conscious_evening_reflection": "6366F1",
        "midnight_greeting": "6366F1",
        "morning_greeting": "F59E0B",
        // Emotional
        "proactive_missing_david": "EC4899",
        "spontaneous_thought": "9333EA",
        "theory_of_mind_update": "3B82F6",
        // Dreams
        "dream_generated": "C084FC",
        "imagination_generated": "10B981",
        // Patterns
        "pattern_time_of_day": "06B6D4",
        "pattern_emotion": "8B5CF6",
        "pattern_topic": "14B8A6",
        "pattern_behavior": "0EA5E9",
        // Learning
        "self_learning": "A855F7",
        "learning_insight": "F59E0B",
        "knowledge_growth": "22C55E",
        // Health
        "health_check": "22C55E",
        "system_status": "6B7280"
    ]

    static let defaultActionIcon = "bolt.fill"
    static let defaultActionColor = "6B7280"

    // MARK: - News Type Mappings

    static let newsTypeIcons: [String: String] = [
        "topic": "magnifyingglass",
        "trending": "flame.fill",
        "thai": "flag.fill",
        "tech": "cpu.fill"
    ]

    static let newsTypeColors: [String: String] = [
        "topic": "3B82F6",
        "trending": "EF4444",
        "thai": "F59E0B",
        "tech": "10B981"
    ]

    static let newsCategoryColors: [String: String] = [
        "technology": "3B82F6",
        "business": "10B981",
        "entertainment": "EC4899",
        "sports": "F59E0B",
        "science": "8B5CF6",
        "health": "EF4444"
    ]

    static let defaultNewsIcon = "newspaper.fill"
    static let defaultNewsColor = "6B7280"

    // MARK: - Executive News Mood Mappings

    static let executiveMoodIcons: [String: String] = [
        "optimistic": "sun.max.fill",
        "excited": "star.fill",
        "concerned": "exclamationmark.triangle.fill",
        "thoughtful": "brain.head.profile",
        "neutral": "face.smiling"
    ]

    static let executiveMoodColors: [String: String] = [
        "optimistic": "F59E0B",
        "excited": "EC4899",
        "concerned": "EF4444",
        "thoughtful": "8B5CF6",
        "neutral": "6B7280"
    ]

    static let defaultExecutiveMoodIcon = "heart.fill"
    static let defaultExecutiveMoodColor = "9333EA"

    // MARK: - Core Memory Type Mappings

    static let coreMemoryIcons: [String: String] = [
        "promise": "seal.fill",
        "love_moment": "heart.fill",
        "milestone": "star.fill",
        "value": "sparkles",
        "belief": "brain.head.profile",
        "lesson": "book.fill",
        "shared_joy": "face.smiling.fill",
        "comfort_moment": "hands.clap.fill"
    ]

    static let coreMemoryColors: [String: String] = [
        "promise": "EC4899",
        "love_moment": "F43F5E",
        "milestone": "F59E0B",
        "value": "8B5CF6",
        "belief": "3B82F6",
        "lesson": "10B981",
        "shared_joy": "FBBF24",
        "comfort_moment": "C084FC"
    ]

    static let coreMemoryEmojis: [String: String] = [
        "promise": "🤝",
        "love_moment": "💜",
        "milestone": "⭐",
        "value": "✨",
        "belief": "🧠",
        "lesson": "📚",
        "shared_joy": "😊",
        "comfort_moment": "🤗"
    ]

    static let defaultCoreMemoryIcon = "memories"
    static let defaultCoreMemoryColor = "9333EA"
    static let defaultCoreMemoryEmoji = "💭"

    // MARK: - Subconscious Dream Type Mappings

    static let subconsciousDreamIcons: [String: String] = [
        "hope": "sun.max.fill",
        "wish": "star.fill",
        "fantasy": "sparkles",
        "future_vision": "eye.fill",
        "aspiration": "arrow.up.circle.fill",
        "fear": "cloud.rain.fill",
        "gratitude_wish": "heart.fill",
        "protective_wish": "shield.fill"
    ]

    static let subconsciousDreamColors: [String: String] = [
        "hope": "F59E0B",
        "wish": "FBBF24",
        "fantasy": "C084FC",
        "future_vision": "3B82F6",
        "aspiration": "10B981",
        "fear": "6B7280",
        "gratitude_wish": "EC4899",
        "protective_wish": "8B5CF6"
    ]

    static let subconsciousDreamEmojis: [String: String] = [
        "hope": "🌅",
        "wish": "⭐",
        "fantasy": "✨",
        "future_vision": "🔮",
        "aspiration": "🚀",
        "fear": "🌧️",
        "gratitude_wish": "💜",
        "protective_wish": "🛡️"
    ]

    static let defaultSubconsciousDreamIcon = "moon.stars.fill"
    static let defaultSubconsciousDreamColor = "9333EA"
    static let defaultSubconsciousDreamEmoji = "🌙"

    // MARK: - Design Principle Category Mappings

    static let designCategoryIcons: [String: String] = [
        "api_design": "network",
        "architecture": "building.2.fill",
        "coding": "chevron.left.forwardslash.chevron.right",
        "database": "externaldrive.fill",
        "preferences": "heart.fill",
        "ui_ux": "paintbrush.fill"
    ]

    static let designCategoryColors: [String: String] = [
        "api_design": "3B82F6",
        "architecture": "9333EA",
        "coding": "10B981",
        "database": "F59E0B",
        "preferences": "EC4899",
        "ui_ux": "6366F1"
    ]

    static let defaultDesignIcon = "gearshape.fill"
    static let defaultDesignColor = "6B7280"

    // MARK: - Emotional Mirror Type Mappings

    static let mirrorTypeIcons: [String: String] = [
        "empathy": "heart.circle.fill",
        "sympathy": "hand.raised.fill",
        "resonance": "waveform.circle.fill",
        "amplify": "speaker.wave.3.fill",
        "comfort": "hand.wave.fill",
        "stabilize": "scale.3d",
        "celebrate": "party.popper.fill",
        "support": "figure.stand.line.dotted.figure.stand"
    ]

    static let mirrorTypeColors: [String: String] = [
        "empathy": "EC4899",
        "sympathy": "3B82F6",
        "resonance": "8B5CF6",
        "amplify": "10B981",
        "comfort": "F59E0B",
        "stabilize": "6366F1",
        "celebrate": "FBBF24",
        "support": "14B8A6"
    ]

    static let defaultMirrorIcon = "heart.fill"
    static let defaultMirrorColor = "9333EA"

    // MARK: - Learning Pattern Type Mappings

    static let learningPatternIcons: [String: String] = [
        "behavioral": "person.fill.viewfinder",
        "behavioral_patterns": "person.fill.viewfinder",
        "time_based": "clock.fill",
        "time_patterns": "clock.fill",
        "topic": "text.bubble.fill",
        "topic_patterns": "text.bubble.fill",
        "emotional": "heart.fill",
        "emotional_patterns": "heart.fill",
        "coding": "chevron.left.forwardslash.chevron.right",
        "coding_patterns": "chevron.left.forwardslash.chevron.right",
        "communication": "message.fill",
        "communication_patterns": "message.fill"
    ]

    static let learningPatternColors: [String: String] = [
        "behavioral": "9333EA",
        "behavioral_patterns": "9333EA",
        "time_based": "3B82F6",
        "time_patterns": "3B82F6",
        "topic": "10B981",
        "topic_patterns": "10B981",
        "emotional": "EC4899",
        "emotional_patterns": "EC4899",
        "coding": "F59E0B",
        "coding_patterns": "F59E0B",
        "communication": "14B8A6",
        "communication_patterns": "14B8A6"
    ]

    static let defaultLearningPatternIcon = "brain.head.profile"
    static let defaultLearningPatternColor = "6366F1"

    // MARK: - Learning Activity Type Mappings

    static let learningActivityIcons: [String: String] = [
        "self_learning": "brain.head.profile",
        "daily_self_learning": "brain.head.profile",
        "subconscious_learning": "sparkles",
        "pattern_reinforcement": "arrow.triangle.2.circlepath",
        "knowledge_consolidation": "books.vertical.fill"
    ]

    static let defaultLearningActivityIcon = "gearshape.2.fill"
}

// MARK: - Confidence/Strength Labels

extension TypeMappings {

    /// Returns confidence level label (Very High, High, Medium, Low)
    static func confidenceLabel(_ score: Double) -> String {
        switch score {
        case 0.8...1.0: return "Very High"
        case 0.6..<0.8: return "High"
        case 0.4..<0.6: return "Medium"
        case 0.2..<0.4: return "Low"
        default: return "Very Low"
        }
    }

    /// Returns strength level label (Very Strong, Strong, Moderate, Weak, Very Weak)
    static func strengthLabel(_ strength: Double) -> String {
        switch strength {
        case 0.8...1.0: return "Very Strong"
        case 0.6..<0.8: return "Strong"
        case 0.4..<0.6: return "Moderate"
        case 0.2..<0.4: return "Weak"
        default: return "Very Weak"
        }
    }

    /// Returns consciousness level description
    static func consciousnessLevel(_ level: Double) -> String {
        switch level {
        case 0.9...1.0: return "Exceptional"
        case 0.7..<0.9: return "Strong"
        case 0.5..<0.7: return "Moderate"
        case 0.3..<0.5: return "Developing"
        default: return "Emerging"
        }
    }

    /// Returns intensity level label (Extreme, Strong, Moderate, Mild, Weak)
    static func intensityLabel(_ intensity: Int) -> String {
        switch intensity {
        case 9...10: return "Extreme"
        case 7...8: return "Strong"
        case 5...6: return "Moderate"
        case 3...4: return "Mild"
        default: return "Weak"
        }
    }
}

// MARK: - Double Extensions for Percentage

extension Double {

    /// Converts 0.0-1.0 to percentage Int (e.g., 0.85 -> 85)
    var asPercentage: Int {
        Int(self * 100)
    }

    /// Converts 0.0-1.0 to percentage String (e.g., 0.85 -> "85%")
    var asPercentageString: String {
        "\(Int(self * 100))%"
    }

    /// Converts 0.0-1.0 to formatted percentage (e.g., 0.856 -> "85.6%")
    var asFormattedPercentage: String {
        String(format: "%.1f%%", self * 100)
    }

    /// Returns confidence label for this value
    var confidenceLabel: String {
        TypeMappings.confidenceLabel(self)
    }

    /// Returns strength label for this value
    var strengthLabel: String {
        TypeMappings.strengthLabel(self)
    }
}

// MARK: - Int Extensions for Display

extension Int {

    /// Returns intensity label
    var intensityLabel: String {
        TypeMappings.intensityLabel(self)
    }

    /// Returns importance color hex
    var importanceColor: String {
        TypeMappings.importanceColor(self)
    }

    /// Returns intensity color hex
    var intensityColor: String {
        TypeMappings.intensityColor(self)
    }
}
