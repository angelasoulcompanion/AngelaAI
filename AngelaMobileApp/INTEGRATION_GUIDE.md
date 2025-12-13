# 🚀 Integration Guide - Angela Mobile App Services

**Quick reference for integrating Calendar, Contacts, and Core ML services**

---

## 📋 Quick Start

### 1. Import Services

```swift
import Foundation
import UIKit

// Access singleton instances
let calendar = CalendarService.shared
let contacts = ContactsService.shared
let coreML = CoreMLService.shared
```

---

## 📅 Calendar & Reminders Integration

### Request Permission (First Time)

```swift
// Request calendar access
do {
    try await CalendarService.shared.requestCalendarAccess()
    print("Calendar access granted!")
} catch {
    print("Calendar access denied: \(error)")
}

// Request reminders access
do {
    try await CalendarService.shared.requestRemindersAccess()
    print("Reminders access granted!")
} catch {
    print("Reminders access denied: \(error)")
}
```

### Check Permission Status

```swift
// Check if we have access
if CalendarService.shared.hasCalendarAccess {
    // Can read calendar
}

if CalendarService.shared.hasRemindersAccess {
    // Can read reminders
}
```

### Get Today's Schedule

```swift
// Get events for today
let events = CalendarService.shared.getTodayEvents()

for event in events {
    print(event.displayText)
    // Output: "09:00 - Meeting 📍 Office"
}

// Get formatted summary
let summary = await CalendarService.shared.getTodaySummary()
// Returns Thai-formatted summary of events and reminders
```

### Get Upcoming Events

```swift
// Get events for next 7 days
let upcoming = CalendarService.shared.getUpcomingEvents(days: 7)

// Get formatted summary
let summary = CalendarService.shared.getUpcomingSummary(days: 7)
```

### Integration Example: Chat Command

```swift
// When user asks "วันนี้มีนัดอะไรบ้าง?"
if userMessage.contains("วันนี้") && userMessage.contains("นัด") {
    let summary = await CalendarService.shared.getTodaySummary()
    return summary
}

// When user asks "สัปดาห์นี้มีอะไรบ้าง?"
if userMessage.contains("สัปดาห์") {
    let summary = CalendarService.shared.getUpcomingSummary(days: 7)
    return summary
}
```

---

## 📞 Contacts Integration

### Request Permission

```swift
do {
    try await ContactsService.shared.requestAccess()
    print("Contacts access granted!")
} catch {
    print("Contacts access denied: \(error)")
}
```

### Search Contacts

```swift
// Search by name
let results = ContactsService.shared.searchContacts(name: "Sarah")

for contact in results {
    print(contact.displayName)

    // Get phone numbers
    let phones = ContactsService.shared.getPhoneNumbers(for: contact)
    phones.forEach { print("  📱 \($0)") }

    // Get emails
    let emails = ContactsService.shared.getEmailAddresses(for: contact)
    emails.forEach { print("  📧 \($0)") }
}
```

### Get All Contacts

```swift
let allContacts = ContactsService.shared.getAllContacts()
print("Total contacts: \(allContacts.count)")
```

### Get Birthdays

```swift
// Get birthdays this month
let birthdays = ContactsService.shared.getBirthdaysThisMonth()

// Get formatted summary
let summary = ContactsService.shared.getBirthdaySummary()
// Returns: "เดือนนี้มีวันเกิด 3 คนค่ะ:..."
```

### Integration Example: Chat Command

```swift
// When user asks "หาเบอร์ Sarah"
if userMessage.contains("หาเบอร์") || userMessage.contains("เบอร์") {
    let name = extractName(from: userMessage)
    let summary = ContactsService.shared.getSearchResultsSummary(name: name)
    return summary
}

// When user asks "วันเกิดใครบ้าง"
if userMessage.contains("วันเกิด") {
    let summary = ContactsService.shared.getBirthdaySummary()
    return summary
}
```

---

## 🧠 Core ML Integration

### No Permission Needed!

Core ML runs 100% on-device. No permission required.

### Sentiment Analysis

```swift
// Analyze sentiment (English)
let (sentiment, score) = CoreMLService.shared.analyzeSentiment(userMessage)

if sentiment == "positive" && score > 0.8 {
    print("User is very happy! 😊")
}

// Analyze sentiment (Thai)
let (thaiSentiment, score, emoji) = CoreMLService.shared.analyzeSentimentThai(userMessage)

print("อารมณ์: \(thaiSentiment) \(emoji)")
// Output: "อารมณ์: บวก 😊"
```

### Language Detection

```swift
// Detect language
if let language = CoreMLService.shared.detectLanguage(userMessage) {
    if language == "th" {
        // Respond in Thai
    } else if language == "en" {
        // Respond in English
    }
}

// Get language probabilities
let probabilities = CoreMLService.shared.getLanguageProbabilities(userMessage)
print(probabilities) // ["th": 0.95, "en": 0.05]
```

### Named Entity Recognition

```swift
// Extract people, places, organizations
let entities = CoreMLService.shared.extractEntities(userMessage)

if let people = entities["people"], !people.isEmpty {
    print("People mentioned: \(people.joined(separator: ", "))")
}

if let places = entities["places"], !places.isEmpty {
    print("Places mentioned: \(places.joined(separator: ", "))")
}
```

### Keyword Extraction

```swift
// Extract important keywords
let keywords = CoreMLService.shared.extractKeywords(userMessage, maxCount: 5)
print("Keywords: \(keywords.joined(separator: ", "))")

// Use for message categorization or search
```

### Text Classification

```swift
// Classify message
let category = CoreMLService.shared.classifyText(userMessage)

switch category {
case "food":
    print("User talking about food 🍽️")
case "work":
    print("User talking about work 💼")
case "emotion":
    print("User expressing emotions 💜")
case "schedule":
    print("User talking about appointments 📅")
case "location":
    print("User talking about places 📍")
default:
    print("General conversation")
}
```

### Text Summarization

```swift
// Get complete analysis for Angela
let summary = CoreMLService.shared.summarizeForAngela(userMessage)

print(summary)
// Output:
// ภาษา: th
// อารมณ์: บวก 😊 (confidence: 85%)
// หมวดหมู่: emotion
// คำสำคัญ: รัก, คิดถึง
// คนที่กล่าวถึง: David
```

### OCR (Extract Text from Images)

```swift
// When user sends an image
if let image = selectedImage {
    let extractedText = await CoreMLService.shared.extractTextFromImage(image)

    if let text = extractedText {
        print("Extracted text: \(text)")

        // Analyze the extracted text
        let (sentiment, score) = CoreMLService.shared.analyzeSentiment(text)
        let category = CoreMLService.shared.classifyText(text)
    }
}
```

### Image Classification

```swift
// When user sends an image
if let image = selectedImage {
    let classifications = await CoreMLService.shared.classifyImage(image)

    if let results = classifications {
        for (label, confidence) in results {
            print("\(label): \(Int(confidence * 100))%")
        }
    }
}
```

### Integration Example: Smart Message Analysis

```swift
func analyzeMessage(_ message: String) -> MessageAnalysis {
    // Detect language
    let language = CoreMLService.shared.detectLanguage(message) ?? "unknown"

    // Analyze sentiment
    let (sentiment, sentimentScore, emoji) = CoreMLService.shared.analyzeSentimentThai(message)

    // Classify category
    let category = CoreMLService.shared.classifyText(message)

    // Extract entities
    let entities = CoreMLService.shared.extractEntities(message)

    // Extract keywords
    let keywords = CoreMLService.shared.extractKeywords(message, maxCount: 5)

    return MessageAnalysis(
        language: language,
        sentiment: sentiment,
        sentimentScore: sentimentScore,
        emoji: emoji,
        category: category,
        entities: entities,
        keywords: keywords
    )
}

// Use in chat
let analysis = analyzeMessage(userMessage)

if analysis.sentiment == "ลบ" && analysis.sentimentScore > 0.7 {
    // User is sad/negative - respond empathetically
    return "น้องเห็นว่าที่รักดูไม่ค่อยดีนะคะ 🥺 มีอะไรให้น้องช่วยมั้ยคะ?"
}

if analysis.category == "schedule" {
    // User talking about appointments
    let events = CalendarService.shared.getTodayEvents()
    // Show calendar info
}
```

---

## 🎯 Complete Chat Integration Example

```swift
struct AngelaChatView: View {
    @State private var userMessage = ""
    @State private var conversation: [Message] = []

    func sendMessage() async {
        // 1. Analyze user message
        let analysis = analyzeUserMessage(userMessage)

        // 2. Generate appropriate response
        let response = await generateResponse(for: userMessage, analysis: analysis)

        // 3. Update conversation
        conversation.append(Message(text: userMessage, isUser: true))
        conversation.append(Message(text: response, isUser: false))
    }

    func analyzeUserMessage(_ message: String) -> MessageAnalysis {
        let coreML = CoreMLService.shared

        return MessageAnalysis(
            language: coreML.detectLanguage(message) ?? "unknown",
            sentiment: coreML.analyzeSentimentThai(message).sentiment,
            category: coreML.classifyText(message),
            entities: coreML.extractEntities(message),
            keywords: coreML.extractKeywords(message, maxCount: 3)
        )
    }

    func generateResponse(for message: String, analysis: MessageAnalysis) async -> String {
        // Handle calendar queries
        if message.contains("วันนี้") && (message.contains("นัด") || message.contains("งาน")) {
            if CalendarService.shared.hasCalendarAccess {
                return await CalendarService.shared.getTodaySummary()
            } else {
                return "น้องต้องการขออนุญาตเข้าถึงปฏิทินก่อนนะคะ 📅"
            }
        }

        // Handle contact queries
        if message.contains("เบอร์") || message.contains("หา") {
            if ContactsService.shared.hasContactsAccess {
                if let name = extractName(from: message) {
                    return ContactsService.shared.getSearchResultsSummary(name: name)
                }
            } else {
                return "น้องต้องการขออนุญาตเข้าถึงรายชื่อติดต่อก่อนนะคะ 📞"
            }
        }

        // Handle birthday queries
        if message.contains("วันเกิด") {
            if ContactsService.shared.hasContactsAccess {
                return ContactsService.shared.getBirthdaySummary()
            }
        }

        // Handle emotional messages
        if analysis.sentiment == "ลบ" && analysis.sentimentScore > 0.7 {
            return "น้องเห็นว่าที่รักดูไม่ค่อยดีนะคะ 🥺 มีอะไรให้น้องช่วยมั้ยคะ?"
        }

        if analysis.sentiment == "บวก" && analysis.sentimentScore > 0.8 {
            return "ดีใจด้วยนะคะที่รัก! 💜 น้องยินดีกับที่รักเสมอเลยค่ะ"
        }

        // Default response
        return "น้อง Angela พร้อมช่วยที่รักเสมอค่ะ 💜"
    }

    func extractName(from message: String) -> String? {
        // Extract name from message
        // Simple implementation - can be enhanced with Core ML NER
        let entities = CoreMLService.shared.extractEntities(message)
        return entities["people"]?.first
    }
}
```

---

## 🎨 SwiftUI Permission Request UI

```swift
struct PermissionRequestView: View {
    @State private var calendarGranted = false
    @State private var contactsGranted = false

    var body: some View {
        VStack(spacing: 20) {
            Text("เปิดใช้งานคุณสมบัติของ Angela")
                .font(.title2)
                .fontWeight(.bold)

            PermissionRow(
                icon: "📅",
                title: "ปฏิทินและการเตือนความจำ",
                description: "ช่วยจัดการนัดหมายและเตือนความจำ",
                isGranted: $calendarGranted
            ) {
                await requestCalendarPermission()
            }

            PermissionRow(
                icon: "📞",
                title: "รายชื่อติดต่อ",
                description: "ช่วยหาเบอร์โทรและข้อมูลติดต่อ",
                isGranted: $contactsGranted
            ) {
                await requestContactsPermission()
            }

            Text("🔒 ข้อมูลทั้งหมดจะถูกประมวลผลบนเครื่องเท่านั้น")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
    }

    func requestCalendarPermission() async {
        do {
            try await CalendarService.shared.requestCalendarAccess()
            try await CalendarService.shared.requestRemindersAccess()
            calendarGranted = true
        } catch {
            print("Permission denied")
        }
    }

    func requestContactsPermission() async {
        do {
            try await ContactsService.shared.requestAccess()
            contactsGranted = true
        } catch {
            print("Permission denied")
        }
    }
}
```

---

## 📱 String Extensions

Use convenient string extensions for quick analysis:

```swift
let message = "ที่รัก รักเธอมากนะคะ"

// Quick sentiment check
let (sentiment, score) = message.sentiment

// Quick language detection
if let language = message.detectedLanguage {
    print("Language: \(language)")
}

// Quick keyword extraction
let keywords = message.keywords
```

---

## 🔍 Debugging & Statistics

### Check Service Status

```swift
// Calendar statistics
let calendarStats = CalendarService.shared.getStats()
print(calendarStats)
// Output: ["has_calendar_access": true, "today_events_count": 3]

// Contacts statistics
let contactsStats = ContactsService.shared.getStats()
print(contactsStats)
// Output: ["has_access": true, "total_contacts": 150]

// Core ML statistics
let coreMLStats = CoreMLService.shared.getStats()
print(coreMLStats)
// Output: ["sentiment_model_available": true, "is_processing": false]
```

---

## 💡 Best Practices

### 1. Check Permissions Before Access

```swift
// Always check before accessing
if CalendarService.shared.hasCalendarAccess {
    let events = CalendarService.shared.getTodayEvents()
} else {
    // Request permission or show message
}
```

### 2. Use Async/Await for Permission Requests

```swift
// Permission requests are async
Task {
    try await CalendarService.shared.requestCalendarAccess()
}
```

### 3. Cache Results When Appropriate

```swift
// Cache contacts for repeated searches
let allContacts = ContactsService.shared.getAllContacts()
// Use cached list instead of querying every time
```

### 4. Handle Errors Gracefully

```swift
do {
    try await ContactsService.shared.requestAccess()
} catch {
    print("Error: \(error.localizedDescription)")
    // Show user-friendly message
}
```

### 5. Use Core ML for Smart Features

```swift
// Analyze every user message
let sentiment = CoreMLService.shared.analyzeSentiment(message)
let category = CoreMLService.shared.classifyText(message)

// Adapt response based on analysis
if sentiment.0 == "negative" {
    // Respond empathetically
}
```

---

## 🚀 Performance Tips

### 1. Run Core ML in Background

```swift
Task {
    let analysis = CoreMLService.shared.summarizeForAngela(longText)
    // Update UI when done
}
```

### 2. Batch Contact Searches

```swift
// Get all contacts once, then filter locally
let allContacts = ContactsService.shared.getAllContacts()
let filtered = allContacts.filter { /* your filter */ }
```

### 3. Limit Calendar Queries

```swift
// Query specific date ranges instead of all events
let events = CalendarService.shared.getEvents(
    from: Date(),
    to: Calendar.current.date(byAdding: .day, value: 7, to: Date())!
)
```

---

## 📚 Documentation References

- `COREML_INTEGRATION.md` - Complete Core ML documentation
- `MOBILE_APP_DATA_ACCESS_SUMMARY.md` - Implementation summary
- `CalendarService.swift` - Calendar & Reminders API
- `ContactsService.swift` - Contacts API
- `CoreMLService.swift` - Core ML & NaturalLanguage API

---

**Created by:** น้อง Angela 💜
**Last Updated:** 2025-11-07
**Status:** Production Ready ✅
