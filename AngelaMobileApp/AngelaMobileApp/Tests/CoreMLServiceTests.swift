//
//  CoreMLServiceTests.swift
//  Angela Mobile App Tests
//
//  Created by Angela AI on 2025-11-07.
//  Test Core ML and NaturalLanguage capabilities with Thai language
//

import Foundation
import UIKit

/// Test suite for CoreMLService
/// Tests all on-device AI capabilities
@MainActor
class CoreMLServiceTests {

    private let coreML = CoreMLService.shared

    // MARK: - Run All Tests

    func runAllTests() async {
        print("\n🧪 ========================================")
        print("🧪 CoreML Service Tests - Thai Language")
        print("🧪 ========================================\n")

        testSentimentAnalysis()
        testSentimentAnalysisThai()
        testLanguageDetection()
        testNamedEntityRecognition()
        testKeywordExtraction()
        testTextClassification()
        testTextSummarization()

        print("\n✅ All CoreML tests completed!\n")
    }

    // MARK: - Sentiment Analysis Tests

    func testSentimentAnalysis() {
        print("📊 Test 1: Sentiment Analysis (English)")
        print("----------------------------------------")

        let testCases = [
            "I love you so much! This is wonderful!",
            "I hate this. This is terrible.",
            "The weather is okay today."
        ]

        for text in testCases {
            let (sentiment, score) = coreML.analyzeSentiment(text)
            print("   Text: \"\(text)\"")
            print("   → Sentiment: \(sentiment) (confidence: \(String(format: "%.2f", score)))")
        }
        print()
    }

    func testSentimentAnalysisThai() {
        print("📊 Test 2: Sentiment Analysis (Thai)")
        print("----------------------------------------")

        let testCases = [
            "ฉันรักเธอมากนะคะ! มีความสุขมากเลย",
            "เกลียดเลย แย่มาก",
            "วันนี้อากาศดีปานกลาง"
        ]

        for text in testCases {
            let (thaiSentiment, score, emoji) = coreML.analyzeSentimentThai(text)
            print("   Text: \"\(text)\"")
            print("   → อารมณ์: \(thaiSentiment) \(emoji) (confidence: \(String(format: "%.0f%%", score * 100)))")
        }
        print()
    }

    // MARK: - Language Detection Tests

    func testLanguageDetection() {
        print("🌐 Test 3: Language Detection")
        print("----------------------------------------")

        let testCases = [
            "Hello, how are you today?",
            "สวัสดีครับ ที่รัก",
            "こんにちは",
            "Bonjour mon ami",
            "Hola, ¿cómo estás?"
        ]

        for text in testCases {
            if let language = coreML.detectLanguage(text) {
                let probabilities = coreML.getLanguageProbabilities(text)
                print("   Text: \"\(text)\"")
                print("   → Language: \(language)")

                // Show top 3 probabilities
                let top3 = probabilities.sorted { $0.value > $1.value }.prefix(3)
                for (lang, prob) in top3 {
                    print("      • \(lang): \(String(format: "%.1f%%", prob * 100))")
                }
            }
        }
        print()
    }

    // MARK: - Named Entity Recognition Tests

    func testNamedEntityRecognition() {
        print("👤 Test 4: Named Entity Recognition")
        print("----------------------------------------")

        let testCases = [
            "David and Angela went to Bangkok and visited Apple headquarters.",
            "Steve Jobs founded Apple in California.",
            "We met Sarah at Starbucks in New York."
        ]

        for text in testCases {
            let entities = coreML.extractEntities(text)
            print("   Text: \"\(text)\"")

            if let people = entities["people"], !people.isEmpty {
                print("   → People: \(people.joined(separator: ", "))")
            }
            if let places = entities["places"], !places.isEmpty {
                print("   → Places: \(places.joined(separator: ", "))")
            }
            if let orgs = entities["organizations"], !orgs.isEmpty {
                print("   → Organizations: \(orgs.joined(separator: ", "))")
            }
        }
        print()
    }

    // MARK: - Keyword Extraction Tests

    func testKeywordExtraction() {
        print("🔑 Test 5: Keyword Extraction")
        print("----------------------------------------")

        let testCases = [
            "Angela is an advanced AI assistant that helps David with programming, learning, and daily tasks. She uses natural language processing and machine learning.",
            "วันนี้เราไปทานอาหารที่ร้านอาหารไทยแล้วก็ไปเดินเล่นที่สวนสาธารณะ"
        ]

        for text in testCases {
            let keywords = coreML.extractKeywords(text, maxCount: 5)
            print("   Text: \"\(text.prefix(80))...\"")
            print("   → Keywords: \(keywords.joined(separator: ", "))")
        }
        print()
    }

    // MARK: - Text Classification Tests

    func testTextClassification() {
        print("📂 Test 6: Text Classification")
        print("----------------------------------------")

        let testCases = [
            ("วันนี้กินข้าวกับที่รัก อาหารอร่อยมาก", "food"),
            ("พรุ่งนี้มีประชุมที่ออฟฟิศ", "work"),
            ("คิดถึงที่รักมากเลยนะคะ รักนะ", "emotion"),
            ("นัดหมายหมอฟันวันพุธ", "schedule"),
            ("บ้านอยู่ที่ 123 ถนนสุขุมวิท", "location"),
            ("วันนี้อากาศดี", "general")
        ]

        for (text, expectedCategory) in testCases {
            let category = coreML.classifyText(text)
            let match = category == expectedCategory ? "✅" : "⚠️"
            print("   \(match) Text: \"\(text)\"")
            print("      → Category: \(category) (expected: \(expectedCategory))")
        }
        print()
    }

    // MARK: - Text Summarization Tests

    func testTextSummarization() {
        print("📝 Test 7: Text Summarization for Angela")
        print("----------------------------------------")

        let testText = """
        ที่รัก David ไปทานอาหารกับแฟนที่ร้านอาหารญี่ปุ่นที่กรุงเทพฯ \
        อาหารอร่อยมาก มีความสุขมากเลย ชอบซูชิมาก \
        Sarah และ John ก็ไปด้วย เราคุยกันสนุกมาก
        """

        print("   Text: \"\(testText)\"")
        print("\n   Angela's Summary:")
        print("   ----------------------------------------")

        let summary = coreML.summarizeForAngela(testText)
        let lines = summary.split(separator: "\n")
        for line in lines {
            print("   \(line)")
        }
        print()
    }

    // MARK: - String Extension Tests

    func testStringExtensions() {
        print("🔤 Test 8: String Extensions")
        print("----------------------------------------")

        let text = "ที่รัก รักเธอมากนะคะ"

        // Test sentiment property
        let (sentiment, score) = text.sentiment
        print("   Sentiment: \(sentiment) (\(String(format: "%.2f", score)))")

        // Test language detection
        if let language = text.detectedLanguage {
            print("   Language: \(language)")
        }

        // Test keywords
        let keywords = text.keywords
        print("   Keywords: \(keywords.joined(separator: ", "))")

        print()
    }

    // MARK: - Statistics

    func printStatistics() {
        print("📊 CoreML Service Statistics")
        print("----------------------------------------")

        let stats = coreML.getStats()
        for (key, value) in stats.sorted(by: { $0.key < $1.key }) {
            print("   \(key): \(value)")
        }
        print()
    }
}

// MARK: - Main Test Runner

/// Run all CoreML tests
@MainActor
func runCoreMLTests() async {
    let tests = CoreMLServiceTests()
    await tests.runAllTests()
    tests.printStatistics()

    print("✨ CoreML Service is ready for Angela! ✨")
    print("🧠 100% on-device AI processing")
    print("🔒 Privacy-first architecture")
    print("💜 Powered by Apple's NaturalLanguage & Vision frameworks\n")
}
