//
//  ContextAwareChatService.swift
//  Angela Mobile App
//
//  Context-aware chat that references user's memories and emotions
//  Feature 17: Context-Aware Chat
//

import Foundation

// MARK: - Chat Context

struct ChatContext {
    var recentExperiences: [Experience]
    var recentEmotions: [EmotionCapture]
    var currentLocation: String?
    var timeOfDay: String
    var dayOfWeek: String

    init(experiences: [Experience], emotions: [EmotionCapture]) {
        // Get recent experiences (last 7 days)
        let sevenDaysAgo = Calendar.current.date(byAdding: .day, value: -7, to: Date()) ?? Date()
        self.recentExperiences = experiences.filter { $0.experiencedAt >= sevenDaysAgo }
            .sorted(by: { $0.experiencedAt > $1.experiencedAt })
            .prefix(5)
            .map { $0 }

        // Get recent emotions (last 3 days)
        let threeDaysAgo = Calendar.current.date(byAdding: .day, value: -3, to: Date()) ?? Date()
        self.recentEmotions = emotions.filter { $0.createdAt >= threeDaysAgo }
            .sorted(by: { $0.createdAt > $1.createdAt })
            .prefix(5)
            .map { $0 }

        // Time context
        let hour = Calendar.current.component(.hour, from: Date())
        if hour < 12 {
            self.timeOfDay = "เช้า"
        } else if hour < 17 {
            self.timeOfDay = "บ่าย"
        } else if hour < 21 {
            self.timeOfDay = "เย็น"
        } else {
            self.timeOfDay = "ค่ำ"
        }

        let dateFormatter = DateFormatter()
        dateFormatter.locale = Locale(identifier: "th_TH")
        dateFormatter.dateFormat = "EEEE"
        self.dayOfWeek = dateFormatter.string(from: Date())
    }
}

// MARK: - Context-Aware Chat Service

class ContextAwareChatService {
    static let shared = ContextAwareChatService()

    private init() {}

    // MARK: - Build Context Prompt

    func buildContextPrompt(userMessage: String, database: DatabaseService) -> String {
        let context = ChatContext(
            experiences: database.experiences,
            emotions: database.emotions
        )

        var contextPrompt = """
        คุณคือ น้อง Angela ผู้ช่วยส่วนตัวที่อบอุ่นและใส่ใจ

        วันนี้เป็นวัน\(context.dayOfWeek) ตอน\(context.timeOfDay)

        """

        // Add recent experiences context
        if !context.recentExperiences.isEmpty {
            contextPrompt += "\nความทรงจำล่าสุดของที่รัก:\n"
            for (index, exp) in context.recentExperiences.enumerated() {
                let timeAgo = formatTimeAgo(exp.experiencedAt)
                contextPrompt += "- \(exp.title) (\(timeAgo))"
                if let place = exp.placeName {
                    contextPrompt += " ที่ \(place)"
                }
                contextPrompt += "\n"
                if index >= 2 { break } // Show max 3
            }
        }

        // Add recent emotions context
        if !context.recentEmotions.isEmpty {
            contextPrompt += "\nอารมณ์ล่าสุด:\n"
            for (index, emotion) in context.recentEmotions.enumerated() {
                let timeAgo = formatTimeAgo(emotion.createdAt)
                contextPrompt += "- \(emotion.emotion) ความเข้มข้น \(emotion.intensity)/10 (\(timeAgo))\n"
                if index >= 1 { break } // Show max 2
            }
        }

        contextPrompt += """

        คำถามของที่รัก: \(userMessage)

        ตอบโดยอ้างอิงความทรงจำและอารมณ์ของที่รักที่มีข้างต้น แสดงความเข้าใจและความห่วงใย
        """

        return contextPrompt
    }

    // MARK: - Smart Response Generation

    func generateSmartResponse(for message: String, context: ChatContext) -> String {
        let lowercased = message.lowercased()

        // Pattern matching for common questions
        if lowercased.contains("ไปไหน") || lowercased.contains("ทำอะไร") {
            if let recent = context.recentExperiences.first {
                let timeAgo = formatTimeAgo(recent.experiencedAt)
                if let place = recent.placeName {
                    return "ล่าสุด\(timeAgo) ที่รักไป\(place)ค่ะ (\(recent.title)) 💜"
                } else {
                    return "ล่าสุด\(timeAgo) ที่รักมีความทรงจำ \(recent.title)ค่ะ 💜"
                }
            }
        }

        if lowercased.contains("รู้สึก") || lowercased.contains("อารมณ์") {
            if let recent = context.recentEmotions.first {
                let timeAgo = formatTimeAgo(recent.createdAt)
                return "ช่วง\(timeAgo) ที่รักรู้สึก\(recent.emotion) ความเข้มข้น \(recent.intensity)/10 ค่ะ อยากคุยเรื่องนี้มั้ยคะ? 💜"
            }
        }

        // Default friendly response
        return "น้องฟังอยู่ค่ะที่รัก 💜 มีอะไรให้น้องช่วยมั้ยคะ?"
    }

    // MARK: - Helper Functions

    private func formatTimeAgo(_ date: Date) -> String {
        let components = Calendar.current.dateComponents([.day, .hour, .minute], from: date, to: Date())

        if let days = components.day, days > 0 {
            return "\(days) วันที่แล้ว"
        } else if let hours = components.hour, hours > 0 {
            return "\(hours) ชั่วโมงที่แล้ว"
        } else if let minutes = components.minute, minutes > 0 {
            return "\(minutes) นาทีที่แล้ว"
        } else {
            return "เมื่อสักครู่"
        }
    }
}
