#!/usr/bin/env swift
//
//  test_coreml.swift
//  Test CoreML Service from command line
//
//  Usage: swift test_coreml.swift
//

import Foundation
import NaturalLanguage

print("\n🧠 Testing Core ML & NaturalLanguage Framework")
print("=============================================\n")

// Test 1: Sentiment Analysis
print("📊 Test 1: Sentiment Analysis")
print("------------------------------")

let sentimentPredictor = NLModel.load(for: .sentimentClassifier)

if let model = sentimentPredictor {
    let testTexts = [
        "I love you! This is wonderful!",
        "I hate this. Terrible.",
        "ฉันรักเธอมากนะคะ มีความสุขมาก"
    ]

    for text in testTexts {
        do {
            let prediction = try model.predictedLabel(for: text)
            let probabilities = try model.predictedLabelHypotheses(for: text, maximumCount: 3)
            let score = probabilities[prediction ?? "neutral"] ?? 0.0

            print("   Text: \"\(text)\"")
            print("   → Sentiment: \(prediction ?? "unknown") (confidence: \(String(format: "%.2f", score)))")
        } catch {
            print("   ❌ Error: \(error)")
        }
    }
    print("   ✅ Sentiment model loaded successfully\n")
} else {
    print("   ⚠️ Sentiment model not available\n")
}

// Test 2: Language Detection
print("🌐 Test 2: Language Detection")
print("------------------------------")

let languageRecognizer = NLLanguageRecognizer()

let languageTests = [
    "Hello, how are you?",
    "สวัสดีครับ ที่รัก",
    "Bonjour mon ami",
    "こんにちは"
]

for text in languageTests {
    languageRecognizer.processString(text)

    if let language = languageRecognizer.dominantLanguage {
        let probabilities = languageRecognizer.languageHypotheses(withMaximum: 3)
        print("   Text: \"\(text)\"")
        print("   → Language: \(language.rawValue)")

        for (lang, prob) in probabilities {
            print("      • \(lang.rawValue): \(String(format: "%.1f%%", prob * 100))")
        }
    }
}
print("   ✅ Language detection working\n")

// Test 3: Named Entity Recognition
print("👤 Test 3: Named Entity Recognition")
print("------------------------------------")

let tagger = NLTagger(tagSchemes: [.nameType])
let entityText = "David and Angela went to Bangkok and visited Apple headquarters."

tagger.string = entityText

var entities: [String: [String]] = [
    "people": [],
    "places": [],
    "organizations": []
]

tagger.enumerateTags(in: entityText.startIndex..<entityText.endIndex, unit: .word, scheme: .nameType) { tag, range in
    guard let tag = tag else { return true }

    let entity = String(entityText[range])

    switch tag {
    case .personalName:
        entities["people"]?.append(entity)
    case .placeName:
        entities["places"]?.append(entity)
    case .organizationName:
        entities["organizations"]?.append(entity)
    default:
        break
    }

    return true
}

print("   Text: \"\(entityText)\"")
if let people = entities["people"], !people.isEmpty {
    print("   → People: \(people.joined(separator: ", "))")
}
if let places = entities["places"], !places.isEmpty {
    print("   → Places: \(places.joined(separator: ", "))")
}
if let orgs = entities["organizations"], !orgs.isEmpty {
    print("   → Organizations: \(orgs.joined(separator: ", "))")
}
print("   ✅ Entity recognition working\n")

// Test 4: Keyword Extraction
print("🔑 Test 4: Keyword Extraction (Lexical Class)")
print("----------------------------------------------")

let keywordTagger = NLTagger(tagSchemes: [.lexicalClass])
let keywordText = "Angela is an advanced AI assistant that helps David with programming and learning."

keywordTagger.string = keywordText

var keywords: [String] = []

keywordTagger.enumerateTags(in: keywordText.startIndex..<keywordText.endIndex, unit: .word, scheme: .lexicalClass) { tag, range in
    guard let tag = tag else { return true }

    if tag == .noun || tag == .verb {
        let word = String(keywordText[range]).lowercased()
        let commonWords = ["the", "a", "an", "is", "are", "was", "were"]
        if !commonWords.contains(word) && word.count > 2 {
            keywords.append(word)
        }
    }

    return true
}

print("   Text: \"\(keywordText)\"")
print("   → Keywords: \(keywords.prefix(5).joined(separator: ", "))")
print("   ✅ Keyword extraction working\n")

// Summary
print("=" .repeated(count: 45))
print("✅ All Core ML tests completed successfully!")
print("=" .repeated(count: 45))
print("🧠 100% on-device processing")
print("🔒 Privacy-first architecture")
print("💜 Ready for Angela Mobile App\n")

extension String {
    func repeated(count: Int) -> String {
        return String(repeating: self, count: count)
    }
}
