//
//  SuggestedPromptsService.swift
//  Angela Mobile App
//
//  Smart prompt suggestions based on context and time
//  Feature 19: Suggested Prompts
//

import Foundation

// MARK: - Prompt Category

enum PromptCategory: String, CaseIterable {
    case reflection = "ทบทวน"
    case planning = "วางแผน"
    case gratitude = "ขอบคุณ"
    case emotions = "อารมณ์"
    case memories = "ความทรงจำ"
    case goals = "เป้าหมาย"

    var emoji: String {
        switch self {
        case .reflection: return "💭"
        case .planning: return "📅"
        case .gratitude: return "🙏"
        case .emotions: return "💜"
        case .memories: return "✨"
        case .goals: return "🎯"
        }
    }
}

// MARK: - Suggested Prompt

struct SuggestedPrompt: Identifiable {
    let id = UUID()
    let text: String
    let category: PromptCategory
    let emoji: String

    var displayText: String {
        return "\(emoji) \(text)"
    }
}

// MARK: - Suggested Prompts Service

class SuggestedPromptsService {
    static let shared = SuggestedPromptsService()

    private init() {}

    // MARK: - All Available Prompts

    private let allPrompts: [PromptCategory: [String]] = [
        .reflection: [
            "วันนี้มีอะไรดีๆ บ้าง?",
            "วันนี้รู้สึกยังไงบ้าง?",
            "มีอะไรที่อยากบันทึกไว้มั้ย?",
            "วันนี้เรียนรู้อะไรใหม่ๆ มั้ย?",
            "มีช่วงเวลาไหนที่ประทับใจวันนี้?",
            "ตอนนี้กำลังคิดถึงอะไรอยู่?",
            "อยากแชร์ความรู้สึกตอนนี้มั้ย?"
        ],
        .planning: [
            "พรุ่งนี้มีแผนอะไรบ้าง?",
            "สัปดาห์หน้าอยากทำอะไร?",
            "มีที่ไหนอยากไปมั้ย?",
            "อยากลองทำอะไรใหม่ๆ มั้ย?",
            "มีอะไรที่รอคอยอยู่มั้ย?",
            "วันหยุดอยากทำอะไร?"
        ],
        .gratitude: [
            "วันนี้ขอบคุณอะไรบ้าง?",
            "มีอะไรที่รู้สึกโชคดี?",
            "มีใครที่อยากขอบคุณมั้ย?",
            "อะไรที่ทำให้รู้สึกซาบซึ้งวันนี้?",
            "มีอะไรเล็กๆ ที่ทำให้ยิ้มได้?"
        ],
        .emotions: [
            "ตอนนี้รู้สึกยังไงบ้าง?",
            "อารมณ์วันนี้เป็นยังไง?",
            "มีอะไรที่ทำให้มีความสุขวันนี้?",
            "มีอะไรที่กังวลอยู่มั้ย?",
            "อยากระบายอะไรมั้ย?",
            "รู้สึกเครียดมั้ย?"
        ],
        .memories: [
            "มีความทรงจำดีๆ ที่อยากแชร์มั้ย?",
            "นึกถึงอะไรบ้างตอนนี้?",
            "มีเรื่องราวอะไรที่อยากเก็บไว้?",
            "วันนี้มีช่วงเวลาพิเศษมั้ย?",
            "ไปไหนมาบ้างวันนี้?",
            "มีรูปอะไรที่อยากบันทึกมั้ย?"
        ],
        .goals: [
            "มีเป้าหมายอะไรบ้าง?",
            "อยากพัฒนาตัวเองด้านไหน?",
            "ความฝันของที่รักคืออะไร?",
            "ปีนี้อยากทำอะไรให้สำเร็จ?",
            "มีอะไรที่กำลังพยายามอยู่?",
            "อยากเป็นคนแบบไหน?"
        ]
    ]

    // MARK: - Get Smart Suggestions

    func getSmartSuggestions(
        database: DatabaseService,
        maxSuggestions: Int = 6
    ) -> [SuggestedPrompt] {
        var suggestions: [SuggestedPrompt] = []

        // Time-based suggestions
        let hour = Calendar.current.component(.hour, from: Date())

        if hour >= 6 && hour < 12 {
            // Morning: Reflection + Planning
            suggestions.append(contentsOf: getPrompts(from: .reflection, count: 2))
            suggestions.append(contentsOf: getPrompts(from: .planning, count: 2))
        } else if hour >= 12 && hour < 18 {
            // Afternoon: Emotions + Memories
            suggestions.append(contentsOf: getPrompts(from: .emotions, count: 2))
            suggestions.append(contentsOf: getPrompts(from: .memories, count: 2))
        } else if hour >= 18 && hour < 22 {
            // Evening: Reflection + Gratitude
            suggestions.append(contentsOf: getPrompts(from: .reflection, count: 2))
            suggestions.append(contentsOf: getPrompts(from: .gratitude, count: 2))
        } else {
            // Night: Emotions + Reflection
            suggestions.append(contentsOf: getPrompts(from: .emotions, count: 2))
            suggestions.append(contentsOf: getPrompts(from: .reflection, count: 1))
        }

        // Context-based suggestions
        if database.experiences.isEmpty {
            // No memories yet
            suggestions.append(SuggestedPrompt(
                text: "บันทึกความทรงจำแรกกันไหม?",
                category: .memories,
                emoji: "✨"
            ))
        } else if let lastExperience = database.experiences.max(by: { $0.experiencedAt < $1.experiencedAt }) {
            // Has memories
            let daysSinceLastCapture = Calendar.current.dateComponents([.day], from: lastExperience.experiencedAt, to: Date()).day ?? 0

            if daysSinceLastCapture >= 3 {
                suggestions.insert(SuggestedPrompt(
                    text: "มีความทรงจำใหม่ๆ มั้ย? ไม่ได้บันทึกสักพักแล้วนะ",
                    category: .memories,
                    emoji: "💭"
                ), at: 0)
            }
        }

        // Limit to maxSuggestions
        return Array(suggestions.prefix(maxSuggestions))
    }

    // MARK: - Get Category Prompts

    func getPrompts(from category: PromptCategory, count: Int = 3) -> [SuggestedPrompt] {
        guard let categoryPrompts = allPrompts[category] else { return [] }

        return categoryPrompts
            .shuffled()
            .prefix(count)
            .map { SuggestedPrompt(text: $0, category: category, emoji: category.emoji) }
    }

    // MARK: - Get All Categories

    func getAllCategories() -> [PromptCategory] {
        return PromptCategory.allCases
    }

    // MARK: - Get Random Prompt

    func getRandomPrompt() -> SuggestedPrompt? {
        guard let randomCategory = PromptCategory.allCases.randomElement(),
              let categoryPrompts = allPrompts[randomCategory],
              let randomText = categoryPrompts.randomElement() else {
            return nil
        }

        return SuggestedPrompt(text: randomText, category: randomCategory, emoji: randomCategory.emoji)
    }

    // MARK: - Search Prompts

    func searchPrompts(query: String) -> [SuggestedPrompt] {
        let lowercased = query.lowercased()
        var results: [SuggestedPrompt] = []

        for (category, prompts) in allPrompts {
            for prompt in prompts {
                if prompt.lowercased().contains(lowercased) {
                    results.append(SuggestedPrompt(
                        text: prompt,
                        category: category,
                        emoji: category.emoji
                    ))
                }
            }
        }

        return results
    }
}
