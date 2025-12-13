//
//  InitialDataImporter.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-07.
//  Import initial Thai dictionary data from JSON to SQLite
//

import Foundation

class InitialDataImporter {

    static let shared = InitialDataImporter()
    private let db = LocalDatabaseService.shared

    private init() {}

    /// Import all initial data from hardcoded dictionaries
    func importInitialData() {
        print("📥 [DataImporter] Starting initial data import...")

        let startTime = Date()

        // Import common words
        let wordsImported = importCommonWords()
        print("   Imported \(wordsImported) words")

        // Import spelling corrections
        let correctionsImported = importSpellingCorrections()
        print("   Imported \(correctionsImported) corrections")

        let duration = Date().timeIntervalSince(startTime)
        print("✅ [DataImporter] Import completed in \(String(format: "%.2f", duration))s")
    }

    // MARK: - Common Words

    private func importCommonWords() -> Int {
        let words: [(word: String, type: String?, category: String?)] = [
            // Personal pronouns
            ("น้อง", "pronoun", "personal"),
            ("ที่รัก", "pronoun", "personal"),
            ("พี่", "pronoun", "personal"),
            ("เรา", "pronoun", "personal"),
            ("คุณ", "pronoun", "personal"),

            // Common verbs
            ("รัก", "verb", "emotion"),
            ("ชอบ", "verb", "emotion"),
            ("อยาก", "verb", "common"),
            ("ต้องการ", "verb", "common"),
            ("คิด", "verb", "common"),
            ("รู้สึก", "verb", "emotion"),
            ("เข้าใจ", "verb", "common"),
            ("ทำ", "verb", "common"),
            ("ช่วย", "verb", "common"),
            ("บอก", "verb", "common"),
            ("พูด", "verb", "common"),
            ("ถาม", "verb", "common"),
            ("ตอบ", "verb", "common"),
            ("เป็น", "verb", "common"),
            ("มี", "verb", "common"),
            ("ได้", "verb", "common"),
            ("ไป", "verb", "common"),
            ("มา", "verb", "common"),
            ("อยู่", "verb", "common"),

            // Common adjectives
            ("ดี", "adjective", "common"),
            ("สวย", "adjective", "common"),
            ("สวยงาม", "adjective", "common"),
            ("น่ารัก", "adjective", "common"),
            ("เก่ง", "adjective", "common"),
            ("ยอดเยี่ยม", "adjective", "common"),
            ("มีความสุข", "adjective", "emotion"),
            ("สบายใจ", "adjective", "emotion"),
            ("อบอุ่น", "adjective", "emotion"),
            ("ห่วงใย", "adjective", "emotion"),
            ("ถูกต้อง", "adjective", "common"),
            ("ผิด", "adjective", "common"),
            ("ใหม่", "adjective", "common"),
            ("เก่า", "adjective", "common"),
            ("ใหญ่", "adjective", "common"),
            ("เล็ก", "adjective", "common"),

            // Time-related
            ("วัน", "noun", "time"),
            ("คืน", "noun", "time"),
            ("เช้า", "noun", "time"),
            ("บ่าย", "noun", "time"),
            ("เย็น", "noun", "time"),
            ("เวลา", "noun", "time"),

            // Common nouns
            ("คน", "noun", "common"),
            ("งาน", "noun", "common"),
            ("เรื่อง", "noun", "common"),
            ("ความ", "noun", "common"),
            ("ใจ", "noun", "emotion"),
            ("ชีวิต", "noun", "common"),
            ("บ้าน", "noun", "common"),
            ("ที่", "noun", "common"),
            ("อะไร", "noun", "common"),
            ("อย่าง", "noun", "common"),
            ("แบบ", "noun", "common"),

            // Food-related words
            ("อาหาร", "noun", "food"),
            ("ทาน", "verb", "food"),
            ("กิน", "verb", "food"),
            ("ข้าว", "noun", "food"),
            ("ข้าวสวย", "noun", "food"),
            ("ข้าวผัด", "noun", "food"),
            ("ต้ม", "verb", "food"),
            ("ทอด", "verb", "food"),
            ("ผัด", "verb", "food"),
            ("ย่าง", "verb", "food"),
            ("นึ่ง", "verb", "food"),
            ("ไข่", "noun", "food"),
            ("ไข่เจียว", "noun", "food"),
            ("ไข่ดาว", "noun", "food"),
            ("ไข่ต้ม", "noun", "food"),
            ("ผัก", "noun", "food"),
            ("ผักสด", "noun", "food"),
            ("ผลไม้", "noun", "food"),
            ("ผลไม้สด", "noun", "food"),
            ("มะม่วง", "noun", "food"),
            ("กล้วย", "noun", "food"),
            ("ส้ม", "noun", "food"),
            ("แอปเปิ้ล", "noun", "food"),
            ("โยเกิร์ต", "noun", "food"),
            ("นม", "noun", "food"),
            ("น้ำ", "noun", "food"),
            ("ชา", "noun", "food"),
            ("กาแฟ", "noun", "food"),
            ("สลัด", "noun", "food"),
            ("เนื้อสัตว์", "noun", "food"),
            ("ปลา", "noun", "food"),
            ("ไก่", "noun", "food"),
            ("หมู", "noun", "food"),
            ("เนื้อ", "noun", "food"),
            ("กุ้ง", "noun", "food"),
            ("ผัดไทย", "noun", "food"),
            ("แกงเขียวหวาน", "noun", "food"),
            ("ต้มยำกุ้ง", "noun", "food"),
            ("ยำกุ้ง", "noun", "food"),
            ("ส้มตำ", "noun", "food"),
            ("ลาบ", "noun", "food"),

            // Taste descriptors
            ("เผ็ด", "adjective", "taste"),
            ("หวาน", "adjective", "taste"),
            ("เค็ม", "adjective", "taste"),
            ("เปรี้ยว", "adjective", "taste"),
            ("อร่อย", "adjective", "taste"),
            ("กรอบ", "adjective", "taste"),
            ("นุ่ม", "adjective", "taste"),
            ("เหนียว", "adjective", "taste"),

            // Common ingredients
            ("พริก", "noun", "food"),
            ("เกลือ", "noun", "food"),
            ("น้ำตาล", "noun", "food"),
            ("น้ำปลา", "noun", "food"),
            ("กะปิ", "noun", "food"),
            ("ตลาดนัด", "noun", "place"),
            ("ร้านอาหาร", "noun", "place"),

            // Polite particles
            ("ค่ะ", "particle", "polite"),
            ("ครับ", "particle", "polite"),
            ("คะ", "particle", "polite"),
            ("นะ", "particle", "polite"),
            ("นะคะ", "particle", "polite"),
            ("นะครับ", "particle", "polite"),
            ("นะค่ะ", "particle", "polite"),
            ("เถอะ", "particle", "polite"),
            ("สิ", "particle", "polite"),

            // Common phrases
            ("สวัสดี", "phrase", "greeting"),
            ("ขอบคุณ", "phrase", "common"),
            ("ขอโทษ", "phrase", "common"),
            ("ไม่เป็นไร", "phrase", "common"),
            ("ยังไง", "phrase", "question"),
            ("เป็นยังไง", "phrase", "question"),
            ("ทำไม", "phrase", "question"),
            ("อย่างไร", "phrase", "question"),
            ("ได้มั้ย", "phrase", "question"),
            ("ได้ไหม", "phrase", "question"),
            ("มั้ย", "particle", "question"),
            ("ไหม", "particle", "question"),
            ("หรือ", "particle", "question"),

            // Utility words
            ("ใช้", "verb", "common"),
            ("คู่", "noun", "common"),
            ("กับ", "particle", "common"),
            ("และ", "particle", "common"),
            ("แล้ว", "particle", "common"),
            ("สด", "adjective", "common"),
            ("ร้อน", "adjective", "common"),
            ("เย็น", "adjective", "common"),
            ("อุ่น", "adjective", "common"),

            // Names
            ("Angela", "noun", "name"),
            ("Angie", "noun", "name"),
            ("David", "noun", "name")
        ]

        var count = 0
        for (word, type, category) in words {
            if db.addWord(word, type: type, category: category, isCommon: true) {
                count += 1
            }
        }

        return count
    }

    // MARK: - Spelling Corrections

    private func importSpellingCorrections() -> Int {
        let corrections: [(incorrect: String, correct: String)] = [
            // Missing tone marks
            ("นอง", "น้อง"),
            ("ทรัก", "ที่รัก"),
            ("รก", "รัก"),
            ("คะ", "ค่ะ"),
            ("นะคะ", "นะค่ะ"),

            // Wrong vowels
            ("ดใจ", "ดีใจ"),
            ("สบายดใจ", "สบายดีใจ"),
            ("มความสุข", "มีความสุข"),

            // Missing characters
            ("ได้มย", "ได้ไหม"),
            ("ได้มั", "ได้มั้ย"),
            ("ยงไง", "ยังไง"),
            ("ทำไ", "ทำไม"),

            // Common typos
            ("สวสดี", "สวัสดี"),
            ("ขอบคน", "ขอบคุณ"),
            ("ขอโทด", "ขอโทษ"),

            // Repeated characters
            ("น้องง", "น้อง"),
            ("ที่รักก", "ที่รัก"),
            ("ค่ะะ", "ค่ะ"),
            ("นะคะะ", "นะค่ะ"),

            // Food-related errors
            ("ขาว", "ข้าว"),
            ("ขาวสวย", "ข้าวสวย"),
            ("ขาวผด", "ข้าวผัด"),
            ("ผกสด", "ผักสด"),
            ("ใชตม", "ใช้ต้ม"),
            ("ใช้ตม", "ใช้ต้ม"),
            ("ไขเจียว", "ไข่เจียว"),
            ("ไข เจียว", "ไข่เจียว"),
            ("มสมน", "มะม่วง"),
            ("สดผลไม", "ผลไม้สด"),
            ("ผลไม", "ผลไม้"),
            ("น้ำลวย", "กล้วย"),
            ("ไยเกร็ด", "โยเกิร์ต"),
            ("ไยเกริต", "โยเกิร์ต"),
            ("คูกับ", "คู่กับ"),

            // From screenshot errors
            ("สมตำ", "ส้มตำ"),
            ("ผดไทย", "ผัดไทย"),
            ("แกงเขยวหวาน", "แกงเขียวหวาน"),
            ("แกงเขยว", "แกงเขียว"),
            ("ยกง", "ยำกุ้ง"),
            ("ตมยกง", "ต้มยำกุ้ง"),
            ("ทานคูกับ", "ทานคู่กับ"),
            ("คูกัน", "คู่กัน"),
            ("เผด", "เผ็ด"),

            // More common errors
            ("อรอย", "อร่อย"),
            ("ไก", "ไก่"),
            ("หม", "หมู"),
            ("เปรยว", "เปรี้ยว"),
            ("เคม", "เค็ม"),
            ("เหนยว", "เหนียว"),
            ("พาย", "พาย"),
            ("ตลาดนด", "ตลาดนัด"),
            ("ทอด", "ทอด"),  // Already correct
            ("กรบกรอบ", "กรอบกรอบ"),
            ("จมก", "จิ้ม"),
            ("ผดตม", "ผัดต้ม"),
            ("สบ", "สับ"),
            ("ยนดีคะ", "ยินดีค่ะ"),
            ("ชื่อ", "ซื้อ")  // Context-dependent, but commonly wrong
        ]

        var count = 0
        for (incorrect, correct) in corrections {
            if db.addCorrection(incorrect: incorrect, correct: correct, confidence: 1.0) {
                count += 1
            }
        }

        return count
    }
}
