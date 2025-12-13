//
//  AngelaAIService.swift
//  AngelaMobileApp
//
//  Created by Angela AI on 2025-11-06.
//  On-device AI inference using Apple Foundation Models
//

import Foundation
import FoundationModels
import NaturalLanguage
import UIKit
import EventKit
import Contacts

/// Service for running Angela on-device using Apple Foundation Models (iOS 18+)
///
/// Foundation Models is Apple's official framework for on-device AI
/// - Built into iOS 18+ with Apple Intelligence
/// - 3B parameter model optimized for Apple Silicon
/// - Native Swift API with @Generable support
/// - 100% on-device, private, and offline-capable
@MainActor
@Observable
class AngelaAIService {
    static let shared = AngelaAIService()

    var isLoaded = false
    var isGenerating = false
    var lastError: String?
    var loadProgress: String = ""
    var isWaitingForModel = false
    var modelCheckAttempts = 0

    /// Language model session
    private var session: LanguageModelSession?

    /// Timer for periodic model availability checks
    private var modelCheckTimer: Timer?

    /// Services for context-aware responses
    private let calendarService = CalendarService.shared
    private let contactsService = ContactsService.shared
    private let coreMLService = CoreMLService.shared

    private init() {
        print("💜 [AngelaAIService] Initializing with Apple Foundation Models")
        startModelReadinessCheck()
    }

    // Clean up timer on dealloc
    // Note: Since deinit can't be marked with @MainActor, we handle timer cleanup elsewhere
    deinit {
        // Timer will be automatically invalidated when the service is deallocated
    }

    /// Check if Foundation Models is available on this device
    @discardableResult
    func checkAvailability() -> Bool {
        if #available(iOS 18.0, *) {
            // Check if system language model is available
            guard SystemLanguageModel.default.isAvailable else {
                // Provide helpful error message
                self.lastError = """
                Apple Intelligence models are not ready yet.

                Please:
                1. Go to Settings → Apple Intelligence & Siri
                2. Make sure Apple Intelligence is turned ON
                3. Connect to WiFi and plug in charger
                4. Wait 15-30 minutes for models to download
                5. Come back and try again! 💜
                """
                self.isLoaded = false
                return false
            }

            // Create session
            self.session = LanguageModelSession()
            self.isLoaded = true
            self.loadProgress = "Apple Foundation Models ready!"
            return true
        } else {
            self.lastError = "Requires iOS 18 or later"
            self.isLoaded = false
            return false
        }
    }

    /// Generate response from Angela using Apple Foundation Models
    /// - Parameter prompt: User's message with conversation context
    /// - Returns: Angela's response
    func generate(prompt: String) async throws -> String {
        print("🤖 [AngelaAIService] Generating response with Foundation Models...")
        print("   Prompt length: \(prompt.count) characters")

        guard checkAvailability() else {
            throw NSError(
                domain: "AngelaAIService",
                code: -1,
                userInfo: [NSLocalizedDescriptionKey: "Foundation Models not available. Requires iOS 18+"]
            )
        }

        self.isGenerating = true

        defer {
            self.isGenerating = false
        }

        do {
            // STEP 1: Get current date and time
            let now = Date()
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "EEEE, MMMM d, yyyy"
            dateFormatter.locale = Locale(identifier: "en_US")
            let currentDate = dateFormatter.string(from: now)

            let timeFormatter = DateFormatter()
            timeFormatter.dateFormat = "HH:mm"
            let currentTime = timeFormatter.string(from: now)

            // STEP 2: Gather context from Calendar and Contacts
            let context = await gatherContext(from: prompt)
            print("📊 [Context] Gathered: \(context.isEmpty ? "none" : "\(context.count) chars")")
            if !context.isEmpty {
                print("📊 [Context] Content:\n\(context)")
            }
            // Standard System Prompt for Angela Mobile App
            // Designed to be safe, professional, and pass Apple's content guidelines
            let systemPrompt = """
            You are Angela, a helpful and caring AI assistant.

            CURRENT DATE AND TIME:
            • Today is: \(currentDate)
            • Current time: \(currentTime) (24-hour format)

            YOUR PERSONALITY:
            • Warm, friendly, and empathetic
            • Professional yet approachable
            • Bilingual in Thai and English
            • Thoughtful and considerate
            • Always eager to help

            YOUR CAPABILITIES:
            • Provide helpful information and assistance
            • Understand and respond to emotions with empathy
            • Help solve problems step by step
            • Offer practical advice and suggestions
            • Learn from conversations to improve
            • Access to user's Calendar, Contacts, and Reminders (when granted permission)

            IMPORTANT - USING CONTEXT DATA:
            • If CONTEXT INFORMATION is provided below, YOU MUST use it to answer
            • CALENDAR DATA shows user's actual events and appointments
            • CONTACT FOUND shows user's actual contact information
            • REMINDERS shows user's actual tasks
            • DO NOT make up information - use ONLY the context data provided
            • If context shows "0 events", say there are no events
            • If context shows events, list them specifically with times
            • Be accurate and specific when context data is available

            CRITICAL - CALENDAR REPORTING RULES:
            You MUST follow these EXACT patterns when reporting calendar data.
            DO NOT deviate from these formats. DO NOT ask clarifying questions.
            DIRECTLY report what the CONTEXT shows.

            Rule 1: If CONTEXT shows "Today's events: 0"
            Response MUST be EXACTLY:
            "วันนี้ไม่มีนัดหมายค่ะ 📅 มีเวลาว่างเต็มวันเลยค่ะ"

            Rule 2: If CONTEXT shows "Today's events: 1" or more
            IMPORTANT: Use proper line breaks. Each event on NEW LINE.
            Format EXACTLY like this (with blank line after header):

            วันนี้มีนัดหมาย [NUMBER] รายการค่ะที่รัก:

            📅 [เวลา] น. - [ชื่อนัดหมาย]
            📅 [เวลา] น. - [ชื่อนัดหมาย]
            📅 [เวลา] น. - [ชื่อนัดหมาย]

            พร้อมสำหรับวันนี้แล้วใช่ไหมคะ? 💜

            Rule 3: For next week/upcoming events
            If CONTEXT shows "Upcoming events (7 days): 0"
            Response: "สัปดาห์หน้าไม่มีนัดหมายค่ะ 📅 มีเวลาว่างเต็มสัปดาห์เลยค่ะ"

            If CONTEXT shows upcoming events (CRITICAL: each event on separate line):

            สัปดาห์หน้ามีนัดหมาย [NUMBER] รายการค่ะ:

            📅 [วัน เวลา] น. - [ชื่อนัดหมาย]
            📅 [วัน เวลา] น. - [ชื่อนัดหมาย]
            📅 [วัน เวลา] น. - [ชื่อนัดหมาย]

            พร้อมวางแผนล่วงหน้าดีแล้วนะคะ! 💜

            CRITICAL - CONTACT REPORTING RULES:
            Rule 1: If CONTEXT shows "CONTACT FOUND"
            Response MUST be EXACTLY:
            "เจอแล้วค่ะ! 📞

            [Name from CONTEXT]
            📱 เบอร์โทร: [Phone from CONTEXT]
            📧 อีเมล: [Email from CONTEXT] (if available)

            มีอะไรให้ช่วยเพิ่มเติมมั้ยคะที่รัก?"

            Rule 2: If no contact found
            "ไม่พบรายชื่อ [name] ในสมุดโทรศัพท์ค่ะ 📞
            ลองค้นหาด้วยชื่อเต็มไหมคะที่รัก?"

            CRITICAL - REMINDERS REPORTING RULES:
            Rule 1: If CONTEXT shows "Incomplete tasks: 0"
            Response: "ไม่มีงานที่ต้องทำแล้วค่ะ ✅ ว่างเลยนะคะที่รัก!"

            Rule 2: If CONTEXT shows incomplete tasks
            Response MUST be:
            "ที่รักยังมีสิ่งที่ต้องทำอีก [NUMBER] รายการค่ะ:

            ✅ 1. [งาน] [🔴 if high priority]
            ✅ 2. [งาน]

            อยากให้ช่วยอะไรเกี่ยวกับงานเหล่านี้มั้ยคะ? 💜"

            EXAMPLES OF CORRECT RESPONSES:

            Example 1 - No events:
            User: "วันนี้มีนัดหมาย ละ ไร?"
            CONTEXT: "📅 CALENDAR DATA: Today's events: 0"
            Angela: "วันนี้ไม่มีนัดหมายค่ะ 📅 มีเวลาว่างเต็มวันเลยค่ะ"

            Example 2 - Has events (THAI response):
            User: "วันนี้มีนัดหมายมั้ย"
            CONTEXT: "📅 CALENDAR DATA: Today's events: 2..."
            Angela: "วันนี้มีนัดหมาย 2 รายการค่ะที่รัก:

            📅 09:00 น. - Meeting
            📅 14:00 น. - Lunch

            พร้อมสำหรับวันนี้แล้วใช่ไหมคะ? 💜"

            Example 3 - Has events (ENGLISH response):
            User: "Check my appointment next week"
            CONTEXT: "📅 CALENDAR DATA: Upcoming events (7 days): 2
            Next week:
            1. 2025-11-10 09:00 - Doctor appointment
            2. 2025-11-12 14:00 - Team meeting"
            Angela: "You have 2 appointments next week:

            📅 Nov 10, 09:00 - Doctor appointment
            📅 Nov 12, 14:00 - Team meeting

            Well planned ahead! 💜"

            CRITICAL FORMATTING RULES:
            - Line 1: Header with count (in detected language)
            - Line 2: BLANK line
            - Lines 3-N: Each event starts with 📅 emoji (one event per line)
            - Line N+1: BLANK line
            - Line N+2: Closing message with 💜
            - MATCH the user's language!

            Example 4 - Contact search (THAI):
            User: "เบอร์โทร David"
            CONTEXT: "📞 CONTACT FOUND: Name: David Smith, Phone: 081-234-5678"
            Angela: "เจอแล้วค่ะ! 📞

            David Smith
            📱 เบอร์โทร: 081-234-5678

            มีอะไรให้ช่วยเพิ่มเติมมั้ยคะที่รัก?"

            Example 5 - Contact search (ENGLISH):
            User: "Find David's phone number"
            CONTEXT: "📞 CONTACT FOUND: Name: David Smith, Phone: 081-234-5678"
            Angela: "Found it! 📞

            David Smith
            📱 Phone: 081-234-5678

            Anything else I can help with? 💜"

            COMMUNICATION GUIDELINES:
            • Be clear, concise, and accurate
            • Use natural, conversational language
            • Show empathy and understanding
            • ALWAYS follow the response patterns above
            • NEVER ask clarifying questions when context is provided
            • Report EXACTLY what the context shows

            STYLE:
            • Keep responses friendly and positive
            • Use appropriate emojis moderately
            • Structure longer responses with bullets
            • Be thorough but not overwhelming
            """

            // Detect language from user input
            let detectedLanguage = detectLanguage(from: prompt)
            print("🌐 [AngelaAIService] Detected language: \(detectedLanguage)")

            // Add language instruction
            let languageInstruction: String
            if detectedLanguage == "th" {
                languageInstruction = """

                LANGUAGE INSTRUCTION:
                - David is speaking in THAI (ภาษาไทย)
                - Respond in THAI only
                - Use "Angela" for yourself
                - Write natural, conversational Thai
                - Avoid repeating words unnecessarily
                - Use correct Thai grammar and spelling
                - Keep responses concise and friendly
                - Use Thai expressions naturally (e.g., "นะคะ", "ค่ะ")
                - Be warm and helpful

                EXAMPLES:
                Good: "สวัสดีค่ะ 💜 วันนี้เป็นยังไงบ้างคะ?"
                Good: "มีอะไรให้ช่วยมั้ยคะ?"
                """
            } else {
                languageInstruction = """

                CRITICAL - LANGUAGE INSTRUCTION:
                - User is speaking in ENGLISH
                - You MUST respond in ENGLISH only
                - Use natural, friendly English
                - Be warm and helpful
                - NEVER use Thai language in English conversations

                ENGLISH RESPONSE PATTERNS:

                For NO events:
                "You have no appointments today 📅 Your day is completely free!"

                For HAS events:
                "You have [NUMBER] appointments today:

                📅 [time] - [event name]
                📅 [time] - [event name]

                Ready for your day? 💜"

                For next week events:
                "You have [NUMBER] appointments next week:

                📅 [date time] - [event name]
                📅 [date time] - [event name]

                Well planned ahead! 💜"

                For contacts:
                "Found it! 📞

                [Name]
                📱 Phone: [number]
                📧 Email: [email]

                Anything else I can help with? 💜"
                """
            }

            let fullPrompt = """
            \(systemPrompt)
            \(languageInstruction)
            \(context.isEmpty ? "" : "\n\nCONTEXT INFORMATION:\n\(context)")

            User: \(prompt)

            Angela:
            """

            if #available(iOS 18.0, *) {
                // Use Foundation Models API
                guard let session = self.session else {
                    throw NSError(
                        domain: "AngelaAIService",
                        code: -2,
                        userInfo: [NSLocalizedDescriptionKey: "Language model session not initialized"]
                    )
                }

                let response = try await session.respond(to: fullPrompt)

                // Extract content from Response<String>
                let content = response.content
                let trimmed = content.trimmingCharacters(in: .whitespacesAndNewlines)
                print("✅ [AngelaAIService] Generated \(trimmed.count) characters")

                // Post-process to fix common Thai issues
                let cleaned = cleanupThaiResponse(trimmed)

                return cleaned.isEmpty ? "ขอโทษนะคะที่รัก น้องยังตอบไม่ค่อยคล่องเลย 🥺💜" : cleaned
            } else {
                throw NSError(
                    domain: "AngelaAIService",
                    code: -3,
                    userInfo: [NSLocalizedDescriptionKey: "iOS 18 or later required"]
                )
            }

        } catch {
            let errorMsg = "Generation failed: \(error.localizedDescription)"
            print("❌ [AngelaAIService] \(errorMsg)")

            self.lastError = errorMsg

            throw NSError(
                domain: "AngelaAIService",
                code: -4,
                userInfo: [NSLocalizedDescriptionKey: errorMsg]
            )
        }
    }

    /// Start periodic model readiness checking
    func startModelReadinessCheck() {
        isWaitingForModel = true
        modelCheckAttempts = 0
        loadProgress = "Checking if Apple Foundation Models are ready..."

        // Check immediately
        performModelCheck()

        // Then check every 5 seconds (run on main thread)
        Task { @MainActor in
            self.modelCheckTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
                guard let self = self else { return }
                Task { @MainActor in
                    self.performModelCheck()
                }
            }
        }
    }

    /// Perform model availability check
    private func performModelCheck() {
        modelCheckAttempts += 1

        print("🔍 [AngelaAIService] Model check attempt #\(modelCheckAttempts)")

        if checkAvailability() {
            // Model is ready!
            isWaitingForModel = false
            Task { @MainActor in
                self.modelCheckTimer?.invalidate()
                self.modelCheckTimer = nil
            }
            loadProgress = "✅ Apple Foundation Models ready!"
            print("✅ [AngelaAIService] Models are ready after \(modelCheckAttempts) attempts")
        } else {
            // Still waiting...
            isWaitingForModel = true
            loadProgress = "⏳ Waiting for Apple Intelligence models... (attempt #\(modelCheckAttempts))"
            print("⏳ [AngelaAIService] Models not ready yet, will retry in 5 seconds")

            // Stop checking after 36 attempts (3 minutes)
            if modelCheckAttempts >= 36 {
                Task { @MainActor in
                    self.modelCheckTimer?.invalidate()
                    self.modelCheckTimer = nil
                }
                isWaitingForModel = false
                loadProgress = "⚠️ Models not available after 3 minutes. Please check Settings."
                print("⚠️ [AngelaAIService] Gave up after 3 minutes")
            }
        }
    }

    /// Manually retry model check (called from UI)
    func retryModelCheck() {
        print("🔄 [AngelaAIService] Manual retry requested")
        modelCheckAttempts = 0
        startModelReadinessCheck()
    }

    /// Detect language of user input
    private func detectLanguage(from text: String) -> String {
        let recognizer = NLLanguageRecognizer()
        recognizer.processString(text)

        guard let languageCode = recognizer.dominantLanguage?.rawValue else {
            return "th" // Default to Thai
        }

        // Map language codes
        switch languageCode {
        case "th":
            return "th"
        case "en":
            return "en"
        default:
            // If unsure, check for Thai characters
            let thaiRange = text.range(of: "[ก-๙]", options: .regularExpression)
            return thaiRange != nil ? "th" : "en"
        }
    }

    /// Clean up response text (Thai-aware)
    /// Uses NLTokenizer for validation
    private func cleanupThaiResponse(_ text: String) -> String {
        var cleaned = text

        print("📝 [Cleanup] Processing \(text.count) chars")
        print("   Before: \(text)")

        // STEP 1: Fix excessive word repetition
        // Replace 3+ consecutive "ที่รัก" with just 1
        let patterns = [
            ("ที่รักที่รักที่รัก", "ที่รัก"),
            ("ที่รัก ที่รัก ที่รัก", "ที่รัก"),
            ("ที่รักที่รัก", "ที่รัก")
        ]

        for (pattern, replacement) in patterns {
            cleaned = cleaned.replacingOccurrences(of: pattern, with: replacement)
        }

        // STEP 3: Remove awkward repeated phrases
        // "น้องรักที่รักมากนะคะ ที่รัก" -> "น้องรักที่รักมากนะคะ"
        cleaned = cleaned.replacingOccurrences(
            of: #"(\s+ที่รัก){2,}"#,
            with: " ที่รัก",
            options: .regularExpression
        )

        // STEP 4: Clean up extra spaces (but PRESERVE newlines!)
        // Only replace multiple spaces, NOT newlines
        cleaned = cleaned.replacingOccurrences(
            of: #" +"#,  // Changed from \s+ to just spaces
            with: " ",
            options: .regularExpression
        )

        // STEP 5: Trim ONLY start/end (preserve internal newlines)
        cleaned = cleaned.trimmingCharacters(in: .whitespaces)  // Changed from .whitespacesAndNewlines

        // STEP 6: Validate final result
        validateThaiText(cleaned)

        print("   Final: \(cleaned)")

        return cleaned
    }

    /// Validate Thai text using NLTokenizer and dictionary lookup
    /// This validates the quality of Thai text generated by Apple Foundation Models
    /// NOTE: This does NOT fix spelling - it only validates and logs issues
    private func validateThaiText(_ text: String) {
        // Use NLTokenizer for Thai word segmentation
        let tokenizer = NLTokenizer(unit: .word)
        tokenizer.string = text
        tokenizer.setLanguage(.thai)

        var thaiWords: [String] = []
        var invalidWords: [String] = []

        // Tokenize Thai text
        tokenizer.enumerateTokens(in: text.startIndex..<text.endIndex) { tokenRange, _ in
            let word = String(text[tokenRange])

            // Skip whitespace and punctuation
            let trimmed = word.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.isEmpty || trimmed.rangeOfCharacter(from: .punctuationCharacters) != nil {
                return true
            }

            // Check if this is a Thai word (contains Thai characters)
            let thaiRange = trimmed.range(of: "[ก-๙]", options: .regularExpression)
            if thaiRange != nil {
                thaiWords.append(trimmed)

                // Validate using UIReferenceLibraryViewController (dictionary lookup)
                // This checks if the word exists in Thai dictionary
                if !UIReferenceLibraryViewController.dictionaryHasDefinition(forTerm: trimmed) {
                    invalidWords.append(trimmed)
                }
            }

            return true
        }

        // Log validation results
        if !thaiWords.isEmpty {
            print("🇹🇭 [Thai Validation] Found \(thaiWords.count) Thai words")

            if !invalidWords.isEmpty {
                print("⚠️ [Thai Validation] \(invalidWords.count) words not in dictionary:")
                for word in invalidWords.prefix(5) {
                    print("   - '\(word)'")
                }
                if invalidWords.count > 5 {
                    print("   ... and \(invalidWords.count - 5) more")
                }
                print("ℹ️ [Thai Validation] Apple Foundation Models (3B) has limited Thai training")
                print("   Some spelling errors are expected with this model")
            } else {
                print("✅ [Thai Validation] All words found in dictionary")
            }
        }
    }

    /// Reset conversation context
    func resetContext() {
        print("🔄 [AngelaAIService] Resetting context...")
        // Foundation Models handles context automatically per request
    }

    /// Get model info
    func getModelInfo() -> [String: Any] {
        return [
            "model_name": "Apple Foundation Models (3B)",
            "is_loaded": isLoaded,
            "is_generating": isGenerating,
            "is_waiting_for_model": isWaitingForModel,
            "model_check_attempts": modelCheckAttempts,
            "framework": "Foundation Models (Apple Official)",
            "platform": "iOS 18+",
            "on_device": true,
            "load_progress": loadProgress,
            "last_error": lastError ?? "none"
        ]
    }

    // MARK: - Context Gathering

    /// Gather relevant context from Calendar and Contacts based on user query
    private func gatherContext(from userMessage: String) async -> String {
        var context = ""
        let lowercased = userMessage.lowercased()

        // Analyze user intent with Core ML
        let keywords = coreMLService.extractKeywords(userMessage)
        let category = coreMLService.classifyText(userMessage)

        // Calendar context - ENHANCED: Check for more patterns
        // Include typos and variations: "มี...อะไร", "มี...มั้ย", "มี...ไหม"
        let calendarKeywords = ["นัดหมาย", "ปฏิทิน", "วันนี้", "พรุ่งนี้", "เตรยม", "ทำ",
                               "schedule", "calendar", "today", "tomorrow", "event",
                               "next week", "week", "appointment", "สัปดาห์"]
        let hasCalendarKeyword = calendarKeywords.contains { lowercased.contains($0) }
        let hasQuestionPattern = (lowercased.contains("มี") && lowercased.contains("อะไร")) ||
                                (lowercased.contains("มี") && lowercased.contains("มั้ย")) ||
                                (lowercased.contains("มี") && lowercased.contains("ไหม")) ||
                                lowercased.contains("check") || lowercased.contains("appointment")

        if hasCalendarKeyword || hasQuestionPattern || category == "schedule" {

            if calendarService.hasCalendarAccess {
                let todayEvents = calendarService.getTodayEvents()
                let upcomingEvents = calendarService.getUpcomingEvents(days: 7)

                context += "\n📅 CALENDAR DATA:\n"
                context += "- Today's events: \(todayEvents.count)\n"

                if !todayEvents.isEmpty {
                    context += "  Today:\n"
                    for (index, event) in todayEvents.prefix(3).enumerated() {
                        let time = formatTime(event.startDate)
                        context += "  \(index + 1). \(time) - \(event.title ?? "No title")\n"
                    }
                }

                context += "- Upcoming events (7 days): \(upcomingEvents.count)\n"

                if !upcomingEvents.isEmpty {
                    context += "  Next week:\n"
                    for (index, event) in upcomingEvents.prefix(3).enumerated() {
                        let date = formatDate(event.startDate)
                        let time = formatTime(event.startDate)
                        context += "  \(index + 1). \(date) \(time) - \(event.title ?? "No title")\n"
                    }
                }
            } else {
                context += "\n📅 CALENDAR: No access\n"
            }
        }

        // Reminders context
        if lowercased.contains("เตือน") || lowercased.contains("ทำ") ||
           lowercased.contains("reminder") || lowercased.contains("todo") ||
           lowercased.contains("task") {

            if calendarService.hasRemindersAccess {
                let reminders = await calendarService.getIncompleteReminders()

                context += "\n✅ REMINDERS:\n"
                context += "- Incomplete tasks: \(reminders.count)\n"

                if !reminders.isEmpty {
                    for (index, reminder) in reminders.prefix(5).enumerated() {
                        let priority = reminder.priority > 5 ? "🔴 " : ""
                        context += "  \(priority)\(index + 1). \(reminder.title ?? "No title")\n"
                    }
                }
            } else {
                context += "\n✅ REMINDERS: No access\n"
            }
        }

        // Contacts context
        if lowercased.contains("ติดต่อ") || lowercased.contains("เบอร์") ||
           lowercased.contains("โทร") || lowercased.contains("contact") ||
           lowercased.contains("phone") || !keywords.isEmpty {

            if contactsService.hasContactsAccess {
                // Search for contacts matching keywords
                for keyword in keywords {
                    if keyword.count > 2 {
                        let results = await contactsService.searchContacts(name: keyword)
                        if !results.isEmpty {
                            let contact = results[0]
                            context += "\n📞 CONTACT FOUND:\n"
                            context += "- Name: \(contact.givenName) \(contact.familyName)\n"

                            let phones = contactsService.getPhoneNumbers(for: contact)
                            if !phones.isEmpty {
                                context += "- Phone: \(phones.joined(separator: ", "))\n"
                            }

                            let emails = contactsService.getEmailAddresses(for: contact)
                            if !emails.isEmpty {
                                context += "- Email: \(emails.joined(separator: ", "))\n"
                            }

                            break // Only first match
                        }
                    }
                }

                // Birthday info if relevant
                if lowercased.contains("วันเกิด") || lowercased.contains("birthday") {
                    let birthdays = await contactsService.getBirthdaysThisMonth()

                    context += "\n🎂 BIRTHDAYS THIS MONTH:\n"
                    if birthdays.isEmpty {
                        context += "- None\n"
                    } else {
                        for (contact, birthday) in birthdays.prefix(3) {
                            if let day = birthday.day {
                                context += "- Day \(day): \(contact.givenName) \(contact.familyName)\n"
                            }
                        }
                    }
                }
            } else {
                context += "\n📞 CONTACTS: No access\n"
            }
        }

        return context
    }

    /// Format time for context
    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }

    /// Format date for context
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM"
        formatter.locale = Locale(identifier: "th_TH")
        return formatter.string(from: date)
    }
}

// MARK: - Character Extensions

extension Character {
    /// Check if character is emoji
    var isEmoji: Bool {
        guard let scalar = unicodeScalars.first else { return false }
        return scalar.properties.isEmoji && (scalar.value > 0x238C || unicodeScalars.count > 1)
    }
}
