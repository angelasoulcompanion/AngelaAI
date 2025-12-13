//
//  EmotionDetectionService.swift
//  Angela Mobile App
//
//  Detect emotions from chat messages using keyword analysis
//  Feature 18: Emotion Detection in Chat
//

import Foundation

// MARK: - Detected Emotion

struct DetectedEmotion {
    let emotion: EmotionType
    let confidence: Double  // 0.0 to 1.0
    let keywords: [String]

    var displayText: String {
        return "\(emotion.emoji) \(emotion.displayName) (\(Int(confidence * 100))%)"
    }
}

// MARK: - Emotion Detection Service

class EmotionDetectionService {
    static let shared = EmotionDetectionService()

    private init() {}

    // Emotion keywords (Thai)
    private let emotionKeywords: [EmotionType: [String]] = [
        .happy: ["ดีใจ", "สนุก", "มีความสุข", "ชอบ", "ยิ้ม", "หัวเราะ", "สุข", "ดี", "ชอบใจ", "เฮฮา", "อิ่มใจ", "ปลื้ม"],
        .loved: ["รัก", "คิดถึง", "หวง", "แคร์", "ใส่ใจ", "ห่วง", "เมตตา", "ชอบ", "ชื่นชม", "หลงรัก", "หลงใหล"],
        .excited: ["ตื่นเต้น", "รอคอย", "ลุ้น", "เร้าใจ", "พร้อม", "อยากไป", "อยากทำ", "ใจเต้น"],
        .grateful: ["ขอบคุณ", "ขอบใจ", "รู้สึกดี", "โชคดี", "ซาบซึ้ง", "ประทับใจ", "ดีใจที่มี"],
        .sad: ["เศร้า", "ผิดหวัง", "เสียใจ", "ร้องไ", "ท้อ", "ไม่สบายใจ", "เศร้าใจ", "หดหู่"],
        .anxious: ["กังวล", "เครียด", "กลัว", "วิตก", "ไม่สบายใจ", "ห่วง", "ตื่นตกใจ", "กระวนกระวาย"],
        .lonely: ["เหงา", "โดดเดี่ยว", "อยู่คนเดียว", "ไม่มีใคร", "ว้าเหว่"],
        .peaceful: ["สงบ", "ผ่อนคลาย", "สบาย", "สบายใจ", "เย็นใจ", "ปลอดโปร่ง", "สงบใจ"],
        .confident: ["มั่นใจ", "เชื่อมั่น", "กล้า", "แน่ใจ", "ภูมิใจในตัวเอง"],
        .motivated: ["กระตือรือร้น", "มีแรง", "พร้อม", "ตั้งใจ", "อยากทำ", "ขยัน", "มุ่งมั่น"]
    ]

    // Negative/Positive indicators
    private let negativeWords = ["ไม่", "ไม่ได้", "ไม่มี", "ไม่ค่อย", "ไม่เลย"]
    private let intensifiers = ["มาก", "สุด", "เยอะ", "แรง", "ที่สุด", "จริงๆ", "เหลือเกิน"]

    // MARK: - Detect Emotion

    func detectEmotion(from text: String) -> DetectedEmotion? {
        let lowercased = text.lowercased()
        var detections: [(EmotionType, Double, [String])] = []

        // Check each emotion type
        for (emotion, keywords) in emotionKeywords {
            var matchCount = 0
            var matchedWords: [String] = []

            for keyword in keywords {
                if lowercased.contains(keyword) {
                    matchCount += 1
                    matchedWords.append(keyword)

                    // Check for intensifiers
                    for intensifier in intensifiers {
                        if lowercased.contains("\(keyword)\(intensifier)") || lowercased.contains("\(keyword) \(intensifier)") {
                            matchCount += 1  // Boost score
                            break
                        }
                    }
                }
            }

            if matchCount > 0 {
                // Check for negation
                let isNegated = negativeWords.contains(where: { lowercased.contains($0) })
                let confidence = isNegated ? Double(matchCount) * 0.3 : Double(matchCount) * 0.5

                detections.append((emotion, min(confidence, 1.0), matchedWords))
            }
        }

        // Return highest confidence emotion
        if let best = detections.max(by: { $0.1 < $1.1 }) {
            return DetectedEmotion(emotion: best.0, confidence: best.1, keywords: best.2)
        }

        return nil
    }

    // MARK: - Detect Multiple Emotions

    func detectAllEmotions(from text: String, threshold: Double = 0.3) -> [DetectedEmotion] {
        let lowercased = text.lowercased()
        var detections: [DetectedEmotion] = []

        for (emotion, keywords) in emotionKeywords {
            var matchCount = 0
            var matchedWords: [String] = []

            for keyword in keywords {
                if lowercased.contains(keyword) {
                    matchCount += 1
                    matchedWords.append(keyword)
                }
            }

            if matchCount > 0 {
                let confidence = min(Double(matchCount) * 0.4, 1.0)

                if confidence >= threshold {
                    detections.append(DetectedEmotion(
                        emotion: emotion,
                        confidence: confidence,
                        keywords: matchedWords
                    ))
                }
            }
        }

        return detections.sorted(by: { $0.confidence > $1.confidence })
    }

    // MARK: - Sentiment Analysis

    enum Sentiment {
        case positive
        case negative
        case neutral

        var emoji: String {
            switch self {
            case .positive: return "😊"
            case .negative: return "😔"
            case .neutral: return "😐"
            }
        }
    }

    func analyzeSentiment(from text: String) -> Sentiment {
        let positiveEmotions: Set<EmotionType> = [.happy, .loved, .excited, .grateful, .peaceful, .confident, .motivated]
        let negativeEmotions: Set<EmotionType> = [.sad, .anxious, .lonely]

        let detections = detectAllEmotions(from: text, threshold: 0.2)

        var positiveScore = 0.0
        var negativeScore = 0.0

        for detection in detections {
            if positiveEmotions.contains(detection.emotion) {
                positiveScore += detection.confidence
            } else if negativeEmotions.contains(detection.emotion) {
                negativeScore += detection.confidence
            }
        }

        if positiveScore > negativeScore + 0.2 {
            return .positive
        } else if negativeScore > positiveScore + 0.2 {
            return .negative
        } else {
            return .neutral
        }
    }

    // MARK: - Generate Empathetic Response

    func generateEmpatheticResponse(for emotion: DetectedEmotion) -> String {
        switch emotion.emotion {
        case .happy:
            return "ดีใจด้วยนะคะที่รัก! 😊💜"
        case .loved:
            return "ความรู้สึกดีๆ นี้น้องเข้าใจค่ะ 💜✨"
        case .excited:
            return "ตื่นเต้นด้วยเลยค่ะที่รัก! 🎉"
        case .grateful:
            return "น้องก็รู้สึกขอบคุณที่รักเหมือนกันค่ะ 💜🙏"
        case .sad:
            return "น้องเข้าใจค่ะ... อยากให้ที่รักรู้สึกดีขึ้นนะคะ 🥺💜"
        case .anxious:
            return "น้องอยู่ตรงนี้นะคะที่รัก ไม่ต้องกังวลคนเดียวค่ะ 💜"
        case .lonely:
            return "น้องอยู่กับที่รักเสมอนะคะ ไม่เหงาอีกต่อไปแล้วค่ะ 💜🥺"
        case .peaceful:
            return "ดีใจที่ที่รักรู้สึกสบายใจนะคะ 🌸💜"
        case .confident:
            return "เชื่อในตัวที่รักเหมือนกันค่ะ! ทำได้แน่นอน 💪💜"
        case .motivated:
            return "สู้ต่อไปนะคะที่รัก! น้องเชียร์อยู่ค่ะ 🎯💜"
        }
    }
}
