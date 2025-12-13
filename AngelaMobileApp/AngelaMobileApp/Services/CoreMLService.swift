//
//  CoreMLService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-07.
//  Core ML and NaturalLanguage processing (100% on-device)
//

import Foundation
import UIKit
import NaturalLanguage
import Vision
import CoreML

/// Service for Core ML and Natural Language Processing
/// 100% on-device AI - privacy-first, no data sent to servers
@MainActor
@Observable
class CoreMLService {

    // MARK: - Singleton
    static let shared = CoreMLService()

    // MARK: - Properties
    var isProcessing = false
    var lastError: String?

    // NaturalLanguage components
    private let languageRecognizer = NLLanguageRecognizer()
    private let tagger = NLTagger(tagSchemes: [.lexicalClass, .nameType, .lemma, .sentimentScore])

    // MARK: - Initialization

    private init() {
        print("🧠 [CoreMLService] Initialized")
        print("   Using NaturalLanguage framework for on-device AI")
    }

    // MARK: - Sentiment Analysis

    /// Analyze sentiment of text using NLTagger (with Thai keyword fallback)
    /// Returns: "positive", "negative", or "neutral"
    func analyzeSentiment(_ text: String) -> (sentiment: String, score: Double) {
        // Check if text is Thai
        let language = detectLanguage(text)

        if language == "th" {
            // Use keyword-based sentiment for Thai
            return analyzeSentimentThai_Keyword(text)
        }

        // Use NLTagger for other languages
        tagger.string = text
        let (sentiment, _) = tagger.tag(at: text.startIndex, unit: .paragraph, scheme: .sentimentScore)

        if let sentimentValue = sentiment?.rawValue, let score = Double(sentimentValue) {
            // Score ranges from -1.0 (negative) to 1.0 (positive)
            let sentimentLabel: String
            if score > 0.1 {
                sentimentLabel = "positive"
            } else if score < -0.1 {
                sentimentLabel = "negative"
            } else {
                sentimentLabel = "neutral"
            }

            let confidence = abs(score)
            print("😊 [CoreMLService] Sentiment: \(sentimentLabel) (score: \(String(format: "%.2f", score)), confidence: \(String(format: "%.2f", confidence)))")

            return (sentimentLabel, confidence)
        }

        print("⚠️ [CoreMLService] Could not analyze sentiment")
        return ("neutral", 0.0)
    }

    /// Keyword-based sentiment analysis for Thai text
    private func analyzeSentimentThai_Keyword(_ text: String) -> (sentiment: String, score: Double) {
        let lowercased = text.lowercased()

        // Positive keywords
        let positiveWords = ["รัก", "ชอบ", "สุข", "ดี", "เยี่ยม", "สนุก", "มีความสุข", "ดีใจ",
                             "อร่อย", "สวย", "งาม", "เก่ง", "เจ๋ง", "ว้าว", "ชื่นชม"]

        // Negative keywords
        let negativeWords = ["เกลียด", "แย่", "เศร้า", "เสียใจ", "เหนื่อย", "เบื่อ", "น่าเบื่อ",
                             "เจ็บ", "ปวด", "ไม่ดี", "แย่มาก", "เลว", "ร้าย", "โกรธ"]

        var positiveCount = 0
        var negativeCount = 0

        for word in positiveWords {
            if lowercased.contains(word) {
                positiveCount += 1
            }
        }

        for word in negativeWords {
            if lowercased.contains(word) {
                negativeCount += 1
            }
        }

        let sentiment: String
        let score: Double

        if positiveCount > negativeCount {
            sentiment = "positive"
            score = min(Double(positiveCount) * 0.3 + 0.5, 1.0)
        } else if negativeCount > positiveCount {
            sentiment = "negative"
            score = min(Double(negativeCount) * 0.3 + 0.5, 1.0)
        } else {
            sentiment = "neutral"
            score = 0.3
        }

        print("😊 [CoreMLService] Thai Sentiment: \(sentiment) (positive: \(positiveCount), negative: \(negativeCount), confidence: \(String(format: "%.2f", score)))")

        return (sentiment, score)
    }

    /// Analyze sentiment in Thai
    func analyzeSentimentThai(_ text: String) -> (sentiment: String, score: Double, emoji: String) {
        let (sentiment, score) = analyzeSentiment(text)

        // Map to Thai
        let thaiSentiment: String
        let emoji: String

        switch sentiment.lowercased() {
        case "positive":
            thaiSentiment = "บวก"
            emoji = score > 0.8 ? "😊" : "🙂"
        case "negative":
            thaiSentiment = "ลบ"
            emoji = score > 0.8 ? "😢" : "😕"
        default:
            thaiSentiment = "กลางๆ"
            emoji = "😐"
        }

        return (thaiSentiment, score, emoji)
    }

    // MARK: - Language Detection

    /// Detect language of text
    func detectLanguage(_ text: String) -> String? {
        languageRecognizer.processString(text)

        guard let language = languageRecognizer.dominantLanguage else {
            return nil
        }

        print("🌐 [CoreMLService] Detected language: \(language.rawValue)")
        return language.rawValue
    }

    /// Get language probabilities
    func getLanguageProbabilities(_ text: String) -> [String: Double] {
        languageRecognizer.processString(text)

        var probabilities: [String: Double] = [:]

        languageRecognizer.languageHypotheses(withMaximum: 5).forEach { lang, prob in
            probabilities[lang.rawValue] = prob
        }

        return probabilities
    }

    // MARK: - Named Entity Recognition

    /// Extract named entities from text
    func extractEntities(_ text: String) -> [String: [String]] {
        tagger.string = text

        var entities: [String: [String]] = [
            "people": [],
            "places": [],
            "organizations": []
        ]

        tagger.enumerateTags(in: text.startIndex..<text.endIndex, unit: .word, scheme: .nameType) { tag, range in
            guard let tag = tag else { return true }

            let entity = String(text[range])

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

        print("👤 [CoreMLService] Entities: \(entities)")
        return entities
    }

    // MARK: - Text Classification

    /// Classify text into categories
    func classifyText(_ text: String) -> String {
        // Simple keyword-based classification
        // In production, use custom Core ML model

        let lowercased = text.lowercased()

        if lowercased.contains("อาหาร") || lowercased.contains("ทาน") || lowercased.contains("กิน") {
            return "food"
        } else if lowercased.contains("งาน") || lowercased.contains("ประชุม") || lowercased.contains("meeting") {
            return "work"
        } else if lowercased.contains("รัก") || lowercased.contains("คิดถึง") || lowercased.contains("love") {
            return "emotion"
        } else if lowercased.contains("นัดหมาย") || lowercased.contains("ปฏิทิน") || lowercased.contains("calendar") {
            return "schedule"
        } else if lowercased.contains("ที่อยู่") || lowercased.contains("สถานที่") || lowercased.contains("location") {
            return "location"
        } else {
            return "general"
        }
    }

    // MARK: - Keyword Extraction

    /// Extract important keywords from text
    func extractKeywords(_ text: String, maxCount: Int = 5) -> [String] {
        // Check if text is Thai - use tokenizer for Thai, tagger for English
        let language = detectLanguage(text)

        if language == "th" {
            return extractKeywordsThai(text, maxCount: maxCount)
        }

        // English keyword extraction using NLTagger
        tagger.string = text

        var keywords: [String: Int] = [:]

        tagger.enumerateTags(in: text.startIndex..<text.endIndex, unit: .word, scheme: .lexicalClass) { tag, range in
            guard let tag = tag else { return true }

            // Extract nouns and verbs
            if tag == .noun || tag == .verb {
                let word = String(text[range]).lowercased()

                // Filter out common words
                let commonWords = ["the", "a", "an", "is", "are", "was", "were"]
                if !commonWords.contains(word) && word.count > 2 {
                    keywords[word, default: 0] += 1
                }
            }

            return true
        }

        // Sort by frequency
        let sorted = keywords.sorted { $0.value > $1.value }
        let topKeywords = Array(sorted.prefix(maxCount)).map { $0.key }

        print("🔑 [CoreMLService] Keywords: \(topKeywords)")
        return topKeywords
    }

    /// Extract Thai keywords using NLTokenizer for word segmentation
    private func extractKeywordsThai(_ text: String, maxCount: Int) -> [String] {
        let tokenizer = NLTokenizer(unit: .word)
        tokenizer.string = text

        // Set language to Thai for better tokenization
        tokenizer.setLanguage(.thai)

        var keywords: [String: Int] = [:]

        tokenizer.enumerateTokens(in: text.startIndex..<text.endIndex) { tokenRange, _ in
            let word = String(text[tokenRange]).trimmingCharacters(in: .whitespacesAndNewlines)

            // Filter out common Thai words and short words
            let commonWords = ["ได้", "มี", "เป็น", "คือ", "ที่", "ใน", "จะ", "ของ", "และ",
                              "กับ", "ว่า", "ไป", "มา", "ให้", "แล้ว", "นี้", "นั้น", "ก็"]

            if !commonWords.contains(word) && word.count > 1 {
                keywords[word, default: 0] += 1
            }

            return true
        }

        // Sort by frequency and get top keywords
        let sorted = keywords.sorted { $0.value > $1.value }
        let topKeywords = Array(sorted.prefix(maxCount)).map { $0.key }

        print("🔑 [CoreMLService] Thai Keywords: \(topKeywords)")
        return topKeywords
    }

    // MARK: - Text Summarization

    /// Create summary of text for Angela
    func summarizeForAngela(_ text: String) -> String {
        var summary = ""

        // 1. Detect language
        if let language = detectLanguage(text) {
            summary += "ภาษา: \(language)\n"
        }

        // 2. Sentiment
        let (sentiment, score, emoji) = analyzeSentimentThai(text)
        summary += "อารมณ์: \(sentiment) \(emoji) (confidence: \(String(format: "%.0f%%", score * 100)))\n"

        // 3. Category
        let category = classifyText(text)
        summary += "หมวดหมู่: \(category)\n"

        // 4. Keywords
        let keywords = extractKeywords(text, maxCount: 3)
        if !keywords.isEmpty {
            summary += "คำสำคัญ: \(keywords.joined(separator: ", "))\n"
        }

        // 5. Entities
        let entities = extractEntities(text)
        if let people = entities["people"], !people.isEmpty {
            summary += "คนที่กล่าวถึง: \(people.joined(separator: ", "))\n"
        }
        if let places = entities["places"], !places.isEmpty {
            summary += "สถานที่: \(places.joined(separator: ", "))\n"
        }

        return summary
    }

    // MARK: - Image Analysis (Vision Framework)

    /// Analyze image and extract text (OCR)
    func extractTextFromImage(_ image: UIImage) async -> String? {
        guard let cgImage = image.cgImage else {
            print("❌ [CoreMLService] Cannot get CGImage")
            return nil
        }

        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["th", "en"] // Thai and English

        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

        do {
            try handler.perform([request])

            guard let observations = request.results else {
                return nil
            }

            let recognizedStrings = observations.compactMap { observation in
                observation.topCandidates(1).first?.string
            }

            let text = recognizedStrings.joined(separator: "\n")
            print("📝 [CoreMLService] Extracted text: \(text.prefix(100))...")

            return text
        } catch {
            print("❌ [CoreMLService] OCR error: \(error)")
            lastError = error.localizedDescription
            return nil
        }
    }

    /// Classify image content
    func classifyImage(_ image: UIImage) async -> [String: Double]? {
        guard let cgImage = image.cgImage else {
            print("❌ [CoreMLService] Cannot get CGImage")
            return nil
        }

        let request = VNClassifyImageRequest()

        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

        do {
            try handler.perform([request])

            guard let observations = request.results else {
                return nil
            }

            var classifications: [String: Double] = [:]
            for observation in observations.prefix(5) {
                classifications[observation.identifier] = Double(observation.confidence)
            }

            print("🖼️ [CoreMLService] Image classifications: \(classifications)")
            return classifications
        } catch {
            print("❌ [CoreMLService] Image classification error: \(error)")
            lastError = error.localizedDescription
            return nil
        }
    }

    // MARK: - Statistics

    func getStats() -> [String: Any] {
        return [
            "natural_language_available": true,
            "is_processing": isProcessing,
            "tag_schemes": ["sentimentScore", "lexicalClass", "nameType", "lemma"]
        ]
    }
}

// MARK: - String Extension

extension String {
    /// Analyze sentiment of this string
    var sentiment: (String, Double) {
        CoreMLService.shared.analyzeSentiment(self)
    }

    /// Detect language of this string
    var detectedLanguage: String? {
        CoreMLService.shared.detectLanguage(self)
    }

    /// Extract keywords from this string
    var keywords: [String] {
        CoreMLService.shared.extractKeywords(self)
    }
}
