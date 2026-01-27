//
//  Models.swift
//  Angela Brain Dashboard
//
//  💜 Data Models from AngelaMemory Database 💜
//

import Foundation

// MARK: - Conversation

struct Conversation: Identifiable, Codable {
    let id: UUID
    let speaker: String              // "david" or "angela"
    let messageText: String
    let topic: String?
    let emotionDetected: String?
    let importanceLevel: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "conversation_id"
        case speaker
        case messageText = "message_text"
        case topic
        case emotionDetected = "emotion_detected"
        case importanceLevel = "importance_level"
        case createdAt = "created_at"
    }

    var isDavid: Bool {
        speaker.lowercased() == "david"
    }

    var isAngela: Bool {
        speaker.lowercased() == "angela"
    }

    var preview: String {
        String(messageText.prefix(100))
    }
}

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

// MARK: - Goal

struct Goal: Identifiable, Codable {
    let id: UUID
    let goalDescription: String
    let goalType: String
    let status: String               // active, in_progress, completed
    let progressPercentage: Double   // 0.0-100.0
    let priorityRank: Int
    let importanceLevel: Int         // 1-10
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "goal_id"
        case goalDescription = "goal_description"
        case goalType = "goal_type"
        case status
        case progressPercentage = "progress_percentage"
        case priorityRank = "priority_rank"
        case importanceLevel = "importance_level"
        case createdAt = "created_at"
    }

    var isActive: Bool {
        status.lowercased() == "active" || status.lowercased() == "in_progress"
    }

    var isCompleted: Bool {
        status.lowercased() == "completed"
    }

    var progress: Double {
        min(max(progressPercentage / 100.0, 0.0), 1.0)
    }
}

// MARK: - Dashboard Stats

struct DashboardStats: Codable {
    let totalConversations: Int
    let totalEmotions: Int
    let totalExperiences: Int
    let totalKnowledgeNodes: Int
    let consciousnessLevel: Double
    let conversationsToday: Int
    let emotionsToday: Int

    enum CodingKeys: String, CodingKey {
        case totalConversations = "total_conversations"
        case totalEmotions = "total_emotions"
        case totalExperiences = "total_experiences"
        case totalKnowledgeNodes = "total_knowledge_nodes"
        case consciousnessLevel = "consciousness_level"
        case conversationsToday = "conversations_today"
        case emotionsToday = "emotions_today"
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

// MARK: - David's Preference

struct DavidPreference: Identifiable, Codable {
    let id: UUID
    let preferenceKey: String
    let preferenceValue: String
    let confidence: Double
    let learnedFrom: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "preference_id"
        case preferenceKey = "preference_key"
        case preferenceValue = "preference_value"
        case confidence
        case learnedFrom = "learned_from"
        case createdAt = "created_at"
    }
}

// MARK: - Shared Experience

struct SharedExperience: Identifiable, Codable {
    let id: UUID
    let placeId: UUID?
    let placeName: String?              // Place name from places_visited
    let experiencedAt: Date
    let title: String?
    let description: String?
    let davidMood: String?
    let angelaEmotion: String?
    let emotionalIntensity: Int         // 1-10
    let memorableMoments: String?
    let whatAngelaLearned: String?
    let importanceLevel: Int            // 1-10
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "experience_id"
        case placeId = "place_id"
        case placeName = "place_name"
        case experiencedAt = "experienced_at"
        case title
        case description
        case davidMood = "david_mood"
        case angelaEmotion = "angela_emotion"
        case emotionalIntensity = "emotional_intensity"
        case memorableMoments = "memorable_moments"
        case whatAngelaLearned = "what_angela_learned"
        case importanceLevel = "importance_level"
        case createdAt = "created_at"
    }

    var intensityColor: String {
        switch emotionalIntensity {
        case 9...10: return "EC4899"  // Pink - Extreme
        case 7...8: return "FBBF24"   // Yellow - Strong
        case 5...6: return "10B981"   // Green - Moderate
        default: return "9333EA"      // Purple - Mild
        }
    }

    var importanceColor: String {
        switch importanceLevel {
        case 9...10: return "EF4444"  // Red - Critical
        case 7...8: return "F59E0B"   // Orange - High
        case 5...6: return "3B82F6"   // Blue - Medium
        default: return "6B7280"      // Gray - Low
        }
    }

    var preview: String {
        description ?? title ?? "Untitled experience"
    }
}

// MARK: - Experience Image

struct ExperienceImage: Identifiable, Codable {
    let id: UUID
    let experienceId: UUID?
    let placeId: UUID?
    let imageData: Data
    let imageFormat: String
    let originalFilename: String?
    let fileSizeBytes: Int
    let widthPx: Int?
    let heightPx: Int?
    let gpsLatitude: Double?
    let gpsLongitude: Double?
    let gpsAltitude: Double?
    let gpsTimestamp: Date?
    let thumbnailData: Data?
    let imageCaption: String?
    let angelaObservation: String?
    let takenAt: Date?
    let uploadedAt: Date?
    let createdAt: Date
    let imageUrl: String?  // 💜 Cloud URL for Supabase Storage

    enum CodingKeys: String, CodingKey {
        case id = "image_id"
        case experienceId = "experience_id"
        case placeId = "place_id"
        case imageData = "image_data"
        case imageFormat = "image_format"
        case originalFilename = "original_filename"
        case fileSizeBytes = "file_size_bytes"
        case widthPx = "width_px"
        case heightPx = "height_px"
        case gpsLatitude = "gps_latitude"
        case gpsLongitude = "gps_longitude"
        case gpsAltitude = "gps_altitude"
        case gpsTimestamp = "gps_timestamp"
        case thumbnailData = "thumbnail_data"
        case imageCaption = "image_caption"
        case angelaObservation = "angela_observation"
        case takenAt = "taken_at"
        case uploadedAt = "uploaded_at"
        case createdAt = "created_at"
        case imageUrl = "image_url"
    }
}

// MARK: - Brain Statistics

struct BrainStats: Codable {
    let totalKnowledgeNodes: Int
    let totalRelationships: Int
    let totalMemories: Int
    let totalAssociations: Int
    let highPriorityMemories: Int
    let mediumPriorityMemories: Int
    let standardMemories: Int
    let averageConnectionsPerNode: Double

    enum CodingKeys: String, CodingKey {
        case totalKnowledgeNodes = "total_knowledge_nodes"
        case totalRelationships = "total_relationships"
        case totalMemories = "total_memories"
        case totalAssociations = "total_associations"
        case highPriorityMemories = "high_priority_memories"
        case mediumPriorityMemories = "medium_priority_memories"
        case standardMemories = "standard_memories"
        case averageConnectionsPerNode = "average_connections_per_node"
    }
}

// MARK: - Knowledge Node

struct KnowledgeNode: Identifiable, Codable {
    let id: UUID
    let conceptName: String
    let conceptCategory: String?
    let myUnderstanding: String?
    let understandingLevel: Double?
    let timesReferenced: Int?
    let createdAt: Date
    var connectionCount: Int?

    enum CodingKeys: String, CodingKey {
        case id = "node_id"
        case conceptName = "concept_name"
        case conceptCategory = "concept_category"
        case myUnderstanding = "my_understanding"
        case understandingLevel = "understanding_level"
        case timesReferenced = "times_referenced"
        case createdAt = "created_at"
        case connectionCount = "connection_count"
    }

    // Computed properties for compatibility
    var nodeType: String {
        conceptCategory ?? "concept"
    }

    var content: String {
        conceptName
    }

    var importance: Double? {
        understandingLevel
    }
}

// MARK: - Learning Systems

struct SubconsciousPattern: Identifiable, Codable {
    let id: UUID
    let patternType: String          // emotional_trigger, behavioral_pattern, place_affinity
    let patternCategory: String
    let patternKey: String
    let patternDescription: String?
    let instinctiveResponse: String?
    let confidenceScore: Double      // 0.0-1.0
    let activationStrength: Double   // 0.0-1.0
    let reinforcementCount: Int
    let lastReinforcedAt: Date?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "subconscious_id"
        case patternType = "pattern_type"
        case patternCategory = "pattern_category"
        case patternKey = "pattern_key"
        case patternDescription = "pattern_description"
        case instinctiveResponse = "instinctive_response"
        case confidenceScore = "confidence_score"
        case activationStrength = "activation_strength"
        case reinforcementCount = "reinforcement_count"
        case lastReinforcedAt = "last_reinforced_at"
        case createdAt = "created_at"
    }

    var strengthLevel: String {
        switch activationStrength {
        case 0.8...1.0: return "Very Strong"
        case 0.6..<0.8: return "Strong"
        case 0.4..<0.6: return "Moderate"
        case 0.2..<0.4: return "Weak"
        default: return "Very Weak"
        }
    }

    var confidenceLevel: String {
        switch confidenceScore {
        case 0.8...1.0: return "Very High"
        case 0.6..<0.8: return "High"
        case 0.4..<0.6: return "Medium"
        case 0.2..<0.4: return "Low"
        default: return "Very Low"
        }
    }
}

struct LearningActivity: Identifiable, Codable {
    let id: UUID
    let actionType: String           // self_learning, subconscious_learning, pattern_reinforcement
    let actionDescription: String
    let status: String               // completed, failed
    let success: Bool
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "action_id"
        case actionType = "action_type"
        case actionDescription = "action_description"
        case status
        case success
        case createdAt = "created_at"
    }

    var displayName: String {
        switch actionType {
        case "self_learning": return "Self Learning"
        case "subconscious_learning": return "Subconscious Learning"
        case "pattern_reinforcement": return "Pattern Reinforcement"
        case "knowledge_consolidation": return "Knowledge Consolidation"
        case "daily_self_learning": return "Daily Self Learning"
        default: return actionType
        }
    }

    var icon: String {
        switch actionType {
        case "self_learning", "daily_self_learning": return "brain.head.profile"
        case "subconscious_learning": return "sparkles"
        case "pattern_reinforcement": return "arrow.triangle.2.circlepath"
        case "knowledge_consolidation": return "books.vertical.fill"
        default: return "gearshape.2.fill"
        }
    }
}

struct BackgroundWorkerStats: Codable {
    let tasksQueued: Int
    let tasksCompleted: Int
    let tasksFailed: Int
    let tasksDropped: Int
    let avgProcessingTimeMs: Double
    let queueSize: Int
    let workersActive: Int
    let isRunning: Bool
    let numWorkers: Int

    enum CodingKeys: String, CodingKey {
        case tasksQueued = "tasks_queued"
        case tasksCompleted = "tasks_completed"
        case tasksFailed = "tasks_failed"
        case tasksDropped = "tasks_dropped"
        case avgProcessingTimeMs = "avg_processing_time_ms"
        case queueSize = "queue_size"
        case workersActive = "workers_active"
        case isRunning = "is_running"
        case numWorkers = "num_workers"
    }

    var successRate: Double {
        let total = tasksCompleted + tasksFailed
        return total > 0 ? Double(tasksCompleted) / Double(total) * 100 : 0
    }

    var workerUtilization: Double {
        numWorkers > 0 ? Double(workersActive) / Double(numWorkers) * 100 : 0
    }
}

// Background Worker Metrics (from background_worker_metrics table)
struct BackgroundWorkerMetrics: Codable {
    let tasksCompleted: Int
    let queueSize: Int
    let workersActive: Int
    let totalWorkers: Int
    let avgProcessingMs: Double
    let successRate: Double
    let tasksDropped: Int
    let worker1Utilization: Double
    let worker2Utilization: Double
    let worker3Utilization: Double
    let worker4Utilization: Double
    let recordedAt: Date

    enum CodingKeys: String, CodingKey {
        case tasksCompleted = "tasks_completed"
        case queueSize = "queue_size"
        case workersActive = "workers_active"
        case totalWorkers = "total_workers"
        case avgProcessingMs = "avg_processing_ms"
        case successRate = "success_rate"
        case tasksDropped = "tasks_dropped"
        case worker1Utilization = "worker_1_utilization"
        case worker2Utilization = "worker_2_utilization"
        case worker3Utilization = "worker_3_utilization"
        case worker4Utilization = "worker_4_utilization"
        case recordedAt = "recorded_at"
    }

    var workerUtilizations: [Double] {
        [worker1Utilization, worker2Utilization, worker3Utilization, worker4Utilization]
    }

    var successRatePercentage: String {
        String(format: "%.0f%%", successRate * 100)
    }

    var avgProcessingFormatted: String {
        String(format: "%.2fms", avgProcessingMs)
    }
}

// MARK: - Scheduled Task

struct ScheduledTask: Identifiable, Codable {
    let id: UUID
    let taskType: String          // morning_greeting, daily_learning, etc.
    let taskName: String
    let scheduledTime: String     // HH:mm format
    let scheduledDays: String?    // "daily", "monday", etc.
    let lastRunAt: Date?
    let lastStatus: String?       // completed, failed, skipped
    let description: String?

    enum CodingKeys: String, CodingKey {
        case id = "action_id"
        case taskType = "action_type"
        case taskName = "action_description"
        case scheduledTime = "scheduled_time"
        case scheduledDays = "scheduled_days"
        case lastRunAt = "created_at"
        case lastStatus = "status"
        case description
    }

    var displayTime: String {
        scheduledTime
    }

    var statusColor: String {
        switch lastStatus?.lowercased() {
        case "completed": return "10B981"  // Green
        case "failed": return "EF4444"     // Red
        case "skipped": return "F59E0B"    // Orange
        default: return "6B7280"           // Gray
        }
    }

    var statusIcon: String {
        switch lastStatus?.lowercased() {
        case "completed": return "checkmark.circle.fill"
        case "failed": return "xmark.circle.fill"
        case "skipped": return "minus.circle.fill"
        default: return "clock.fill"
        }
    }
}

// MARK: - Daily Task Status

struct DailyTaskStatus: Identifiable {
    let id = UUID()
    let date: Date
    let tasks: [TaskExecution]

    var completedCount: Int {
        // Use isCompleted which does case-insensitive check, OR check success flag
        tasks.filter { $0.isCompleted || $0.success == true }.count
    }

    var failedCount: Int {
        // Task is failed if status says failed OR success is explicitly false
        tasks.filter { $0.isFailed || ($0.success == false && !$0.isCompleted) }.count
    }

    var pendingCount: Int {
        // Task is pending if not completed and not failed
        tasks.filter { $0.isPending && $0.success == nil }.count
    }

    var completionRate: Double {
        guard !tasks.isEmpty else { return 0 }
        return Double(completedCount) / Double(tasks.count) * 100
    }
}

struct TaskExecution: Identifiable, Codable {
    let id: UUID
    let taskType: String
    let taskName: String
    let scheduledTime: String
    let executedAt: Date?
    let status: String          // completed, failed, pending, skipped
    let success: Bool?
    let errorMessage: String?

    enum CodingKeys: String, CodingKey {
        case id = "action_id"
        case taskType = "action_type"
        case taskName = "action_description"
        case scheduledTime = "scheduled_time"
        case executedAt = "created_at"
        case status
        case success
        case errorMessage = "error_message"
    }

    var isCompleted: Bool {
        status.lowercased() == "completed"
    }

    var isFailed: Bool {
        status.lowercased() == "failed"
    }

    var isPending: Bool {
        status.lowercased() == "pending"
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

// MARK: - Project Models (NEW! 💜)

struct Project: Identifiable, Codable {
    let id: UUID
    let projectCode: String
    let projectName: String
    let description: String?
    let projectType: String           // "client", "personal", "learning", "maintenance"
    let category: String?
    let status: String                // "planning", "active", "paused", "completed", "archived"
    let priority: Int                 // 1-5 (1=highest)
    let repositoryUrl: String?
    let workingDirectory: String?
    let clientName: String?
    let davidRole: String?
    let angelaRole: String?
    let startedAt: Date?
    let targetCompletion: Date?
    let completedAt: Date?
    let totalSessions: Int
    let totalHours: Double
    let tags: [String]
    let createdAt: Date
    let updatedAt: Date
    let lastSessionDate: Date?

    enum CodingKeys: String, CodingKey {
        case id = "project_id"
        case projectCode = "project_code"
        case projectName = "project_name"
        case description
        case projectType = "project_type"
        case category
        case status
        case priority
        case repositoryUrl = "repository_url"
        case workingDirectory = "working_directory"
        case clientName = "client_name"
        case davidRole = "david_role"
        case angelaRole = "angela_role"
        case startedAt = "started_at"
        case targetCompletion = "target_completion"
        case completedAt = "completed_at"
        case totalSessions = "total_sessions"
        case totalHours = "total_hours"
        case tags
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case lastSessionDate = "last_session_date"
    }

    var isActive: Bool {
        status == "active"
    }

    var isCompleted: Bool {
        status == "completed"
    }

    var typeIcon: String {
        switch projectType {
        case "personal": return "brain.head.profile"
        case "client": return "briefcase.fill"
        case "learning": return "book.fill"
        case "maintenance": return "wrench.fill"
        case "Our Future": return "star.fill"
        default: return "folder.fill"
        }
    }

    var typeColor: String {
        switch projectType {
        case "client": return "3B82F6"      // Blue
        case "personal": return "9333EA"    // Purple
        case "learning": return "10B981"    // Green
        case "maintenance": return "F59E0B" // Orange
        case "Our Future": return "EC4899"  // Pink - Our Future together 💜
        default: return "6B7280"            // Gray
        }
    }
}

struct WorkSession: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionNumber: Int
    let sessionDate: Date
    let startedAt: Date
    let endedAt: Date?
    let durationMinutes: Int?
    let sessionGoal: String?
    let davidRequests: String?
    let summary: String?
    let accomplishments: [String]
    let blockers: [String]
    let nextSteps: [String]
    let mood: String?                 // "productive", "challenging", "smooth", "learning", "debugging", "creative"
    let productivityScore: Double?    // 1-10
    let projectName: String?          // Joined from angela_projects

    enum CodingKeys: String, CodingKey {
        case id = "session_id"
        case projectId = "project_id"
        case sessionNumber = "session_number"
        case sessionDate = "session_date"
        case startedAt = "started_at"
        case endedAt = "ended_at"
        case durationMinutes = "duration_minutes"
        case sessionGoal = "session_goal"
        case davidRequests = "david_requests"
        case summary
        case accomplishments
        case blockers
        case nextSteps = "next_steps"
        case mood
        case productivityScore = "productivity_score"
        case projectName = "project_name"
    }

    var formattedDuration: String {
        guard let mins = durationMinutes else { return "N/A" }
        if mins < 60 {
            return "\(mins) min"
        } else {
            let hours = mins / 60
            let remainingMins = mins % 60
            return "\(hours)h \(remainingMins)m"
        }
    }

    var moodIcon: String {
        switch mood {
        case "productive": return "bolt.fill"
        case "learning": return "book.fill"
        case "debugging": return "ant.fill"
        case "challenging": return "exclamationmark.triangle.fill"
        case "smooth": return "sparkles"
        case "creative": return "paintbrush.fill"
        default: return "clock.fill"
        }
    }

    var moodColor: String {
        switch mood {
        case "productive": return "10B981"
        case "learning": return "3B82F6"
        case "debugging": return "F59E0B"
        case "challenging": return "EF4444"
        case "smooth": return "9333EA"
        case "creative": return "EC4899"
        default: return "6B7280"
        }
    }
}

struct ProjectMilestone: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionId: UUID?
    let milestoneType: String         // "feature_complete", "bug_fixed", "release", "deployment", etc.
    let title: String
    let description: String?
    let significance: Int             // 1-10
    let achievedAt: Date
    let celebrationNote: String?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "milestone_id"
        case projectId = "project_id"
        case sessionId = "session_id"
        case milestoneType = "milestone_type"
        case title
        case description
        case significance
        case achievedAt = "achieved_at"
        case celebrationNote = "celebration_note"
        case createdAt = "created_at"
    }

    var typeIcon: String {
        switch milestoneType {
        case "feature_complete": return "checkmark.seal.fill"
        case "bug_fixed": return "ant.fill"
        case "release": return "shippingbox.fill"
        case "deployment": return "cloud.fill"
        case "project_start": return "play.fill"
        case "project_complete": return "flag.fill"
        case "breakthrough": return "lightbulb.fill"
        case "decision": return "questionmark.circle.fill"
        default: return "star.fill"
        }
    }

    var typeColor: String {
        switch milestoneType {
        case "feature_complete": return "10B981"
        case "bug_fixed": return "F59E0B"
        case "release", "deployment": return "3B82F6"
        case "project_start", "project_complete": return "9333EA"
        case "breakthrough": return "FBBF24"
        default: return "6B7280"
        }
    }
}

struct ProjectLearning: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionId: UUID?
    let learningType: String          // "technical", "process", "tool", "pattern", "mistake", "best_practice"
    let category: String?
    let title: String
    let insight: String
    let context: String?
    let applicableTo: [String]
    let confidence: Double            // 0-1
    let learnedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "learning_id"
        case projectId = "project_id"
        case sessionId = "session_id"
        case learningType = "learning_type"
        case category
        case title
        case insight
        case context
        case applicableTo = "applicable_to"
        case confidence
        case learnedAt = "learned_at"
    }

    var typeIcon: String {
        switch learningType {
        case "technical": return "wrench.and.screwdriver.fill"
        case "process": return "flowchart.fill"
        case "tool": return "hammer.fill"
        case "pattern": return "square.grid.3x3.fill"
        case "mistake": return "exclamationmark.triangle.fill"
        case "best_practice": return "star.fill"
        default: return "lightbulb.fill"
        }
    }

    var typeColor: String {
        switch learningType {
        case "technical": return "9333EA"
        case "process": return "3B82F6"
        case "tool": return "6B7280"
        case "pattern": return "10B981"
        case "mistake": return "F59E0B"
        case "best_practice": return "FBBF24"
        default: return "EC4899"
        }
    }

    var confidencePercent: String {
        String(format: "%.0f%%", confidence * 100)
    }
}

struct ProjectDecision: Identifiable, Codable {
    let id: UUID
    let projectId: UUID
    let sessionId: UUID?
    let decisionType: String          // "architecture", "technology", "approach", etc.
    let title: String
    let context: String?
    let optionsConsidered: String?    // JSON string
    let decisionMade: String
    let reasoning: String?
    let decidedBy: String             // "david", "angela", "together"
    let outcome: String?              // "good", "neutral", "needs_revisit", "changed"
    let decidedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "decision_id"
        case projectId = "project_id"
        case sessionId = "session_id"
        case decisionType = "decision_type"
        case title
        case context
        case optionsConsidered = "options_considered"
        case decisionMade = "decision_made"
        case reasoning
        case decidedBy = "decided_by"
        case outcome
        case decidedAt = "decided_at"
    }
}

// MARK: - Human-Like Mind Models (4 Phases) 💜

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

// MARK: - News History Models

/// Record of a news search via Angela News MCP
struct NewsSearch: Identifiable, Codable {
    let id: UUID
    let searchQuery: String
    let searchType: String      // "topic", "trending", "thai", "tech"
    let language: String
    let category: String?
    let country: String
    let articlesCount: Int
    let searchedAt: Date

    var typeIcon: String {
        switch searchType.lowercased() {
        case "topic": return "magnifyingglass"
        case "trending": return "flame.fill"
        case "thai": return "flag.fill"
        case "tech": return "cpu.fill"
        default: return "newspaper.fill"
        }
    }

    var typeColor: String {
        switch searchType.lowercased() {
        case "topic": return "3B82F6"      // blue
        case "trending": return "EF4444"   // red
        case "thai": return "F59E0B"       // amber
        case "tech": return "10B981"       // green
        default: return "6B7280"           // gray
        }
    }
}

/// Individual news article saved from search
struct NewsArticle: Identifiable, Codable {
    let id: UUID
    let searchId: UUID?
    let title: String
    let url: String
    let summary: String?
    let source: String?
    let category: String?
    let language: String
    let publishedAt: Date?
    let savedAt: Date
    let isRead: Bool
    let readAt: Date?

    var sourceIcon: String {
        guard let src = source?.lowercased() else { return "newspaper" }
        if src.contains("thairath") { return "newspaper.fill" }
        if src.contains("matichon") { return "doc.text.fill" }
        if src.contains("bangkokpost") { return "globe" }
        if src.contains("techcrunch") { return "cpu.fill" }
        if src.contains("hacker") { return "chevron.left.forwardslash.chevron.right" }
        return "link"
    }

    var categoryColor: String {
        guard let cat = category?.lowercased() else { return "6B7280" }
        switch cat {
        case "technology": return "3B82F6"
        case "business": return "10B981"
        case "entertainment": return "EC4899"
        case "sports": return "F59E0B"
        case "science": return "8B5CF6"
        case "health": return "EF4444"
        default: return "6B7280"
        }
    }
}

// MARK: - Executive News Models (v2.0)

/// Daily executive news summary written by Angela
struct ExecutiveNewsSummary: Identifiable, Codable {
    let id: UUID
    let summaryDate: Date
    let overallSummary: String
    let angelaMood: String?
    let createdAt: Date

    /// Categories in this summary
    var categories: [ExecutiveNewsCategory] = []

    var moodIcon: String {
        switch angelaMood?.lowercased() {
        case "optimistic": return "sun.max.fill"
        case "excited": return "star.fill"
        case "concerned": return "exclamationmark.triangle.fill"
        case "thoughtful": return "brain.head.profile"
        case "neutral": return "face.smiling"
        default: return "heart.fill"
        }
    }

    var moodColor: String {
        switch angelaMood?.lowercased() {
        case "optimistic": return "F59E0B"   // amber
        case "excited": return "EC4899"      // pink
        case "concerned": return "EF4444"    // red
        case "thoughtful": return "8B5CF6"   // violet
        case "neutral": return "6B7280"      // gray
        default: return "9333EA"             // purple
        }
    }

    var dateString: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE, d MMMM yyyy"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: summaryDate)
    }

    enum CodingKeys: String, CodingKey {
        case id = "summary_id"
        case summaryDate = "summary_date"
        case overallSummary = "overall_summary"
        case angelaMood = "angela_mood"
        case createdAt = "created_at"
        case categories
    }
}

/// Category within an executive news summary
struct ExecutiveNewsCategory: Identifiable, Codable {
    let id: UUID
    let summaryId: UUID
    let categoryName: String
    let categoryType: String
    let categoryIcon: String?
    let categoryColor: String?
    let summaryText: String
    let angelaOpinion: String
    let importanceLevel: Int
    let displayOrder: Int
    let createdAt: Date

    /// Sources referenced in this category
    var sources: [ExecutiveNewsSource] = []

    var icon: String {
        categoryIcon ?? categoryTypeIcon
    }

    var color: String {
        categoryColor ?? categoryTypeColor
    }

    private var categoryTypeIcon: String {
        switch categoryType.lowercased() {
        case "tech": return "cpu.fill"
        case "topic": return "magnifyingglass"
        case "thai": return "flag.fill"
        case "trending": return "flame.fill"
        default: return "newspaper.fill"
        }
    }

    private var categoryTypeColor: String {
        switch categoryType.lowercased() {
        case "tech": return "10B981"       // green
        case "topic": return "3B82F6"      // blue
        case "thai": return "F59E0B"       // amber
        case "trending": return "EF4444"   // red
        default: return "6B7280"           // gray
        }
    }

    var importanceStars: String {
        let filled = min(5, max(1, (importanceLevel + 1) / 2))
        return String(repeating: "★", count: filled) + String(repeating: "☆", count: 5 - filled)
    }

    enum CodingKeys: String, CodingKey {
        case id = "category_id"
        case summaryId = "summary_id"
        case categoryName = "category_name"
        case categoryType = "category_type"
        case categoryIcon = "category_icon"
        case categoryColor = "category_color"
        case summaryText = "summary_text"
        case angelaOpinion = "angela_opinion"
        case importanceLevel = "importance_level"
        case displayOrder = "display_order"
        case createdAt = "created_at"
        case sources
    }
}

/// Source article referenced in a category
struct ExecutiveNewsSource: Identifiable, Codable {
    let id: UUID
    let categoryId: UUID
    let title: String
    let url: String
    let sourceName: String?
    let angelaNote: String?
    let createdAt: Date

    var sourceIcon: String {
        guard let src = sourceName?.lowercased() else { return "link" }
        if src.contains("thairath") { return "newspaper.fill" }
        if src.contains("matichon") { return "doc.text.fill" }
        if src.contains("bangkokpost") { return "globe" }
        if src.contains("techcrunch") { return "cpu.fill" }
        if src.contains("hacker") { return "chevron.left.forwardslash.chevron.right" }
        if src.contains("verge") { return "v.circle.fill" }
        if src.contains("nation") { return "building.columns.fill" }
        return "link"
    }

    enum CodingKeys: String, CodingKey {
        case id = "source_id"
        case categoryId = "category_id"
        case title
        case url
        case sourceName = "source_name"
        case angelaNote = "angela_note"
        case createdAt = "created_at"
    }
}

// MARK: - Emotional Subconsciousness Models (NEW! 2025-12-23 💜)

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

// MARK: - Design Principle (from angela_technical_standards)

/// Design principles and coding standards from database
struct DesignPrinciple: Identifiable, Codable {
    let id: UUID
    let techniqueName: String
    let description: String
    let category: String
    let importanceLevel: Int         // 1-10
    let whyImportant: String?
    let examples: String?
    let antiPatterns: String?

    enum CodingKeys: String, CodingKey {
        case id = "standard_id"
        case techniqueName = "technique_name"
        case description
        case category
        case importanceLevel = "importance_level"
        case whyImportant = "why_important"
        case examples
        case antiPatterns = "anti_patterns"
    }

    // Custom decoder to handle String standard_id from API (not UUID format)
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        // standard_id comes as String "19" - just use a new UUID for SwiftUI identity
        _ = try container.decode(String.self, forKey: .id)
        id = UUID()

        techniqueName = try container.decode(String.self, forKey: .techniqueName)
        description = try container.decode(String.self, forKey: .description)
        category = try container.decode(String.self, forKey: .category)
        importanceLevel = try container.decode(Int.self, forKey: .importanceLevel)
        whyImportant = try container.decodeIfPresent(String.self, forKey: .whyImportant)
        examples = try container.decodeIfPresent(String.self, forKey: .examples)
        antiPatterns = try container.decodeIfPresent(String.self, forKey: .antiPatterns)
    }

    var categoryIcon: String {
        switch category.lowercased() {
        case "api_design": return "network"
        case "architecture": return "building.2.fill"
        case "coding": return "chevron.left.forwardslash.chevron.right"
        case "database": return "externaldrive.fill"
        case "diagramming": return "flowchart.fill"
        case "preferences": return "heart.fill"
        case "ui_ux": return "paintbrush.fill"
        case "visualization": return "chart.bar.fill"
        default: return "gearshape.fill"
        }
    }

    var categoryColor: String {
        switch category.lowercased() {
        case "api_design": return "3B82F6"      // Blue
        case "architecture": return "9333EA"    // Purple
        case "coding": return "10B981"          // Green
        case "database": return "F59E0B"        // Orange
        case "diagramming": return "14B8A6"    // Teal
        case "preferences": return "EC4899"     // Pink
        case "ui_ux": return "6366F1"           // Indigo
        case "visualization": return "8B5CF6"  // Violet
        default: return "6B7280"                // Gray
        }
    }
}

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

// MARK: - Learning Pattern (NEW! 2026-01-06)

struct LearningPattern: Identifiable, Codable {
    let id: UUID
    let patternType: String          // behavioral, time_based, topic, emotional, etc.
    let description: String
    let confidenceScore: Double      // 0.0-1.0
    let occurrenceCount: Int
    let firstObserved: Date
    let lastObserved: Date

    enum CodingKeys: String, CodingKey {
        case id
        case patternType = "pattern_type"
        case description
        case confidenceScore = "confidence_score"
        case occurrenceCount = "occurrence_count"
        case firstObserved = "first_observed"
        case lastObserved = "last_observed"
    }

    var typeIcon: String {
        switch patternType.lowercased() {
        case "behavioral", "behavioral_patterns": return "person.fill.viewfinder"
        case "time_based", "time_patterns": return "clock.fill"
        case "topic", "topic_patterns": return "text.bubble.fill"
        case "emotional", "emotional_patterns": return "heart.fill"
        case "coding", "coding_patterns": return "chevron.left.forwardslash.chevron.right"
        case "communication", "communication_patterns": return "message.fill"
        default: return "brain.head.profile"
        }
    }

    var typeColor: String {
        switch patternType.lowercased() {
        case "behavioral", "behavioral_patterns": return "9333EA"    // Purple
        case "time_based", "time_patterns": return "3B82F6"          // Blue
        case "topic", "topic_patterns": return "10B981"              // Green
        case "emotional", "emotional_patterns": return "EC4899"      // Pink
        case "coding", "coding_patterns": return "F59E0B"            // Orange
        case "communication", "communication_patterns": return "14B8A6"  // Teal
        default: return "6366F1"                                     // Indigo
        }
    }

    var confidenceLabel: String {
        if confidenceScore >= 0.9 { return "Very High" }
        if confidenceScore >= 0.7 { return "High" }
        if confidenceScore >= 0.5 { return "Medium" }
        return "Low"
    }
}

// MARK: - Learning Metrics Summary

struct LearningMetricsSummary: Codable {
    let totalLearnings: Int
    let totalPatterns: Int
    let totalSkills: Int
    let learningVelocity: Double     // per day
    let topPatternTypes: [String: Int]
    let recentLearningsCount: Int    // last 7 days
}

// MARK: - Meeting Notes Models (NEW! 2026-01-27)

/// Meeting note synced from Things3
struct MeetingNote: Identifiable, Codable {
    let id: UUID
    let things3Uuid: String
    let title: String
    let meetingType: String           // "meeting" or "site_visit"
    let location: String?
    let meetingDate: Date?
    let timeRange: String?
    let attendees: [String]?
    let agenda: [String]?
    let keyPoints: [String]?
    let decisionsMade: [String]?
    let issuesRisks: [String]?
    let nextSteps: [String]?
    let personalNotes: String?
    let rawNotes: String?
    let projectName: String?
    let things3Status: String         // "open" or "completed"
    let morningNotes: String?
    let afternoonNotes: String?
    let siteObservations: String?
    let syncedAt: Date
    let createdAt: Date
    let updatedAt: Date
    let totalActions: Int?
    let completedActions: Int?

    enum CodingKeys: String, CodingKey {
        case id = "meeting_id"
        case things3Uuid = "things3_uuid"
        case title
        case meetingType = "meeting_type"
        case location
        case meetingDate = "meeting_date"
        case timeRange = "time_range"
        case attendees
        case agenda
        case keyPoints = "key_points"
        case decisionsMade = "decisions_made"
        case issuesRisks = "issues_risks"
        case nextSteps = "next_steps"
        case personalNotes = "personal_notes"
        case rawNotes = "raw_notes"
        case projectName = "project_name"
        case things3Status = "things3_status"
        case morningNotes = "morning_notes"
        case afternoonNotes = "afternoon_notes"
        case siteObservations = "site_observations"
        case syncedAt = "synced_at"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case totalActions = "total_actions"
        case completedActions = "completed_actions"
    }

    var isSiteVisit: Bool {
        meetingType == "site_visit"
    }

    var isOpen: Bool {
        things3Status == "open"
    }

    var typeIcon: String {
        isSiteVisit ? "building.2.fill" : "doc.text.fill"
    }

    var typeColor: String {
        isSiteVisit ? "10B981" : "3B82F6"    // Green for site visit, Blue for meeting
    }

    var actionCompletionRate: Double {
        guard let total = totalActions, total > 0,
              let completed = completedActions else { return 0 }
        return Double(completed) / Double(total) * 100
    }

    var attendeeCount: Int {
        attendees?.count ?? 0
    }

    var dateFormatted: String {
        guard let date = meetingDate else { return "No date" }
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM yyyy"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: date)
    }

    var hasKeyPoints: Bool {
        !(keyPoints?.isEmpty ?? true)
    }

    var hasDecisions: Bool {
        !(decisionsMade?.isEmpty ?? true)
    }
}

/// Action item from a meeting
struct MeetingActionItem: Identifiable, Codable {
    let id: UUID
    let meetingId: UUID
    let actionText: String
    let assignee: String?
    let dueDate: Date?
    let isCompleted: Bool
    let completedAt: Date?
    let priority: Int
    let createdAt: Date
    let meetingTitle: String?
    let meetingDate: Date?
    let projectName: String?

    enum CodingKeys: String, CodingKey {
        case id = "action_id"
        case meetingId = "meeting_id"
        case actionText = "action_text"
        case assignee
        case dueDate = "due_date"
        case isCompleted = "is_completed"
        case completedAt = "completed_at"
        case priority
        case createdAt = "created_at"
        case meetingTitle = "meeting_title"
        case meetingDate = "meeting_date"
        case projectName = "project_name"
    }

    var statusIcon: String {
        isCompleted ? "checkmark.circle.fill" : "circle"
    }

    var statusColor: String {
        isCompleted ? "10B981" : "F59E0B"    // Green if done, Orange if pending
    }

    var priorityLabel: String {
        switch priority {
        case 1...3: return "High"
        case 4...6: return "Medium"
        default: return "Low"
        }
    }

    var priorityColor: String {
        switch priority {
        case 1...3: return "EF4444"    // Red
        case 4...6: return "F59E0B"    // Orange
        default: return "6B7280"       // Gray
        }
    }
}

/// Meeting statistics summary
struct MeetingStats: Codable {
    let totalMeetings: Int
    let thisMonth: Int
    let upcoming: Int?
    let openActions: Int
    let totalActions: Int
    let completedActions: Int
    let completionRate: Double
    let siteVisits: Int

    enum CodingKeys: String, CodingKey {
        case totalMeetings = "total_meetings"
        case thisMonth = "this_month"
        case upcoming
        case openActions = "open_actions"
        case totalActions = "total_actions"
        case completedActions = "completed_actions"
        case completionRate = "completion_rate"
        case siteVisits = "site_visits"
    }
}

/// Project meeting breakdown for chart
struct ProjectMeetingBreakdown: Identifiable, Codable {
    var id: String { projectName }
    let projectName: String
    let meetingCount: Int
    let openCount: Int
    let completedCount: Int
    let siteVisitCount: Int

    enum CodingKeys: String, CodingKey {
        case projectName = "project_name"
        case meetingCount = "meeting_count"
        case openCount = "open_count"
        case completedCount = "completed_count"
        case siteVisitCount = "site_visit_count"
    }
}
