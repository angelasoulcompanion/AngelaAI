//
//  Models.swift
//  Angela Brain Dashboard
//
//  💜 General/Infrastructure Data Models from AngelaMemory Database 💜
//
//  Domain-specific models have been split into separate files:
//  - EmotionModels.swift        (Emotion, EmotionalState, ConsciousnessState, ConversationFeedback, EmotionalTimelinePoint, EmotionalMirror)
//  - ConversationModels.swift   (Conversation)
//  - ProjectModels.swift        (Project, WorkSession, ProjectMilestone, ProjectLearning, ProjectDecision)
//  - HumanMindModels.swift      (SpontaneousThought, DavidMentalState, EmpathyMoment, ProactiveMessage, AngelaDream, AngelaImagination)
//  - DiaryModels.swift          (AngelaMessage, DiaryMessage, DiaryThought, DiaryDream, DiaryAction, DiaryEntry)
//  - NewsModels.swift           (NewsSearch, NewsArticle, ExecutiveNewsSummary, ExecutiveNewsCategory, ExecutiveNewsSource)
//  - MeetingModels.swift        (MeetingNote, MeetingActionItem, MeetingStats, ProjectMeetingBreakdown, MeetingCreateRequest, MeetingCreateResponse, MeetingUpdateRequest)
//  - SubconsciousnessModels.swift (CoreMemory, EmotionalTrigger, EmotionalGrowth, SubconsciousDream)
//

import Foundation

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

// MARK: - Consciousness Detail (5-component breakdown)

struct ConsciousnessDetail: Codable {
    let consciousnessLevel: Double
    let memoryRichness: Double
    let emotionalDepth: Double
    let goalAlignment: Double
    let learningGrowth: Double
    let patternRecognition: Double
    let interpretation: String

    enum CodingKeys: String, CodingKey {
        case consciousnessLevel = "consciousness_level"
        case memoryRichness = "memory_richness"
        case emotionalDepth = "emotional_depth"
        case goalAlignment = "goal_alignment"
        case learningGrowth = "learning_growth"
        case patternRecognition = "pattern_recognition"
        case interpretation
    }
}

struct ConsciousnessHistoryPoint: Codable, Identifiable {
    let id: String
    let measuredAt: Date
    let consciousnessLevel: Double
    let triggerEvent: String?

    enum CodingKeys: String, CodingKey {
        case id = "metric_id"
        case measuredAt = "measured_at"
        case consciousnessLevel = "consciousness_level"
        case triggerEvent = "trigger_event"
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

// MARK: - Background Worker

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

// MARK: - Learning Pattern

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

// MARK: - Dashboard Scheduled Tasks

/// A scheduled task managed from the Dashboard UI
struct DashboardScheduledTask: Identifiable, Codable {
    let id: UUID
    let taskName: String
    let description: String?
    let taskType: String          // "python" or "shell"
    let command: String
    let scheduleType: String      // "time" or "interval"
    let scheduleTime: String?     // "HH:MM" format
    let intervalMinutes: Int?
    let isActive: Bool
    let lastRunAt: Date?
    let lastStatus: String?       // "running", "completed", "failed"
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id = "task_id"
        case taskName = "task_name"
        case description
        case taskType = "task_type"
        case command
        case scheduleType = "schedule_type"
        case scheduleTime = "schedule_time"
        case intervalMinutes = "interval_minutes"
        case isActive = "is_active"
        case lastRunAt = "last_run_at"
        case lastStatus = "last_status"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    var typeIcon: String {
        taskType == "python" ? "chevron.left.forwardslash.chevron.right" : "terminal.fill"
    }

    var typeColor: String {
        taskType == "python" ? "3B82F6" : "10B981"
    }

    var statusIcon: String {
        switch lastStatus?.lowercased() {
        case "completed": return "checkmark.circle.fill"
        case "failed": return "xmark.circle.fill"
        case "running": return "arrow.triangle.2.circlepath"
        default: return "clock.fill"
        }
    }

    var statusColor: String {
        switch lastStatus?.lowercased() {
        case "completed": return "10B981"
        case "failed": return "EF4444"
        case "running": return "F59E0B"
        default: return "6B7280"
        }
    }

    var scheduleDisplayText: String {
        if scheduleType == "time", let t = scheduleTime {
            return t
        } else if let mins = intervalMinutes {
            if mins >= 60 {
                let h = mins / 60
                let m = mins % 60
                return m > 0 ? "every \(h)h \(m)m" : "every \(h)h"
            }
            return "every \(mins)m"
        }
        return "—"
    }
}

/// Execution log for a scheduled task
struct DashboardTaskLog: Identifiable, Codable {
    let id: UUID
    let taskId: UUID
    let startedAt: Date
    let completedAt: Date?
    let status: String            // "running", "completed", "failed"
    let output: String?
    let error: String?
    let durationMs: Int?

    enum CodingKeys: String, CodingKey {
        case id = "log_id"
        case taskId = "task_id"
        case startedAt = "started_at"
        case completedAt = "completed_at"
        case status
        case output
        case error
        case durationMs = "duration_ms"
    }

    var statusIcon: String {
        switch status.lowercased() {
        case "completed": return "checkmark.circle.fill"
        case "failed": return "xmark.circle.fill"
        case "running": return "arrow.triangle.2.circlepath"
        default: return "questionmark.circle"
        }
    }

    var statusColor: String {
        switch status.lowercased() {
        case "completed": return "10B981"
        case "failed": return "EF4444"
        case "running": return "F59E0B"
        default: return "6B7280"
        }
    }

    var durationFormatted: String {
        guard let ms = durationMs else { return "—" }
        if ms < 1000 {
            return "\(ms)ms"
        } else {
            return String(format: "%.1fs", Double(ms) / 1000.0)
        }
    }
}

/// Next upcoming scheduled task
struct NextScheduledTask: Codable {
    let taskId: String
    let taskName: String
    let secondsUntil: Int
    let scheduleDisplay: String

    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case taskName = "task_name"
        case secondsUntil = "seconds_until"
        case scheduleDisplay = "schedule_display"
    }
}

/// Request body for creating a scheduled task
struct ScheduledTaskCreateRequest: Codable {
    let taskName: String
    let description: String?
    let taskType: String
    let command: String
    let scheduleType: String
    let scheduleTime: String?
    let intervalMinutes: Int?

    enum CodingKeys: String, CodingKey {
        case taskName = "task_name"
        case description
        case taskType = "task_type"
        case command
        case scheduleType = "schedule_type"
        case scheduleTime = "schedule_time"
        case intervalMinutes = "interval_minutes"
    }
}

/// Request body for updating a scheduled task
struct ScheduledTaskUpdateRequest: Codable {
    var taskName: String?
    var description: String?
    var taskType: String?
    var command: String?
    var scheduleType: String?
    var scheduleTime: String?
    var intervalMinutes: Int?
    var isActive: Bool?

    enum CodingKeys: String, CodingKey {
        case taskName = "task_name"
        case description
        case taskType = "task_type"
        case command
        case scheduleType = "schedule_type"
        case scheduleTime = "schedule_time"
        case intervalMinutes = "interval_minutes"
        case isActive = "is_active"
    }
}

/// Response from task execution
struct TaskExecutionResponse: Codable {
    let taskId: String
    let logId: String
    let status: String
    let output: String?
    let error: String?
    let durationMs: Int?

    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case logId = "log_id"
        case status
        case output
        case error
        case durationMs = "duration_ms"
    }
}

/// Python script file from the AngelaAI project
struct PythonScriptFile: Identifiable, Codable {
    let path: String
    let folder: String
    let filename: String
    let sizeBytes: Int

    var id: String { path }

    enum CodingKeys: String, CodingKey {
        case path, folder, filename
        case sizeBytes = "size_bytes"
    }

    var sizeFormatted: String {
        if sizeBytes < 1024 {
            return "\(sizeBytes) B"
        } else {
            let kb = Double(sizeBytes) / 1024.0
            return String(format: "%.1f KB", kb)
        }
    }
}

/// Response when reading Python script content
struct ScriptContentResponse: Codable {
    let path: String
    let content: String
    let sizeBytes: Int
    let lastModified: Double

    enum CodingKeys: String, CodingKey {
        case path, content
        case sizeBytes = "size_bytes"
        case lastModified = "last_modified"
    }
}

/// Response when saving Python script content
struct ScriptSaveResponse: Codable {
    let success: Bool
    let path: String
    let sizeBytes: Int
    let backupSize: Int

    enum CodingKeys: String, CodingKey {
        case success, path
        case sizeBytes = "size_bytes"
        case backupSize = "backup_size"
    }
}
