//
//  SimpleServicesTest.swift
//  Angela Mobile App - Quick Test
//
//  Created by Angela AI on 2025-11-07.
//  Simple test cases for Calendar, Contacts, and CoreML services
//

import Foundation
import UIKit
import EventKit
import Contacts

/// Simple test runner for all services
@MainActor
class SimpleServicesTest {

    // MARK: - Run All Tests

    static func runAllTests() async {
        print("\n" + "="*60)
        print("📱 ANGELA MOBILE APP - QUICK SERVICES TEST")
        print("="*60 + "\n")

        await testCalendarService()
        await testContactsService()
        testCoreMLService()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60 + "\n")
    }

    // MARK: - Test 1: Calendar Service

    static func testCalendarService() async {
        print("📅 TEST 1: Calendar Service")
        print("-" * 60)

        let service = CalendarService.shared

        // Check permissions
        await service.checkPermissions()
        print("   Calendar access: \(service.hasCalendarAccess ? "✅" : "❌")")
        print("   Reminders access: \(service.hasRemindersAccess ? "✅" : "❌")")

        // Request permissions if not granted
        if !service.hasCalendarAccess {
            print("   📋 Requesting calendar access...")
            do {
                try await service.requestCalendarAccess()
            } catch {
                print("   ❌ Error requesting calendar: \(error)")
            }
        }

        if !service.hasRemindersAccess {
            print("   📋 Requesting reminders access...")
            do {
                try await service.requestRemindersAccess()
            } catch {
                print("   ❌ Error requesting reminders: \(error)")
            }
        }

        if service.hasCalendarAccess {
            // Test getting today's events
            let events = service.getTodayEvents()
            print("   Today's events: \(events.count)")

            if !events.isEmpty {
                print("   First event: \(events[0].title ?? "No title")")
            }

            // Test getting upcoming events
            let upcoming = service.getUpcomingEvents(days: 7)
            print("   Upcoming events (7 days): \(upcoming.count)")

            // Test Thai summary
            let summary = await service.getTodaySummary()
            print("   Summary generated: \(summary.count) characters")
        } else {
            print("   ⚠️ No calendar access - skipping event tests")
        }

        if service.hasRemindersAccess {
            // Test getting reminders
            let reminders = await service.getIncompleteReminders()
            print("   Incomplete reminders: \(reminders.count)")
        } else {
            print("   ⚠️ No reminders access - skipping reminder tests")
        }

        // Test stats
        let stats = service.getStats()
        print("   Stats: \(stats)")

        print("   ✅ Calendar Service test completed\n")
    }

    // MARK: - Test 2: Contacts Service

    static func testContactsService() async {
        print("📞 TEST 2: Contacts Service")
        print("-" * 60)

        let service = ContactsService.shared

        // Check permission
        await service.checkPermission()
        print("   Contacts access: \(service.hasContactsAccess ? "✅" : "❌")")

        // Request permission if not granted
        if !service.hasContactsAccess {
            print("   📋 Requesting contacts access...")
            do {
                try await service.requestAccess()
            } catch {
                print("   ❌ Error requesting contacts: \(error)")
            }
        }

        if service.hasContactsAccess {
            // Test getting all contacts
            let contacts = await service.getAllContacts()
            print("   Total contacts: \(contacts.count)")

            if !contacts.isEmpty {
                let first = contacts[0]
                print("   First contact: \(first.givenName) \(first.familyName)")

                // Test formatting
                let formatted = service.formatContact(first, includeDetails: false)
                print("   Formatted: \(formatted)")
            }

            // Test search
            if contacts.count > 0 {
                let searchName = contacts[0].givenName
                let results = await service.searchContacts(name: searchName)
                print("   Search '\(searchName)': \(results.count) results")
            }

            // Test birthdays
            let birthdays = await service.getBirthdaysThisMonth()
            print("   Birthdays this month: \(birthdays.count)")

            // Test summary
            let summary = await service.getBirthdaySummary()
            print("   Birthday summary: \(summary.count) characters")
        } else {
            print("   ⚠️ No contacts access - skipping contact tests")
        }

        // Test stats
        let stats = await service.getStats()
        print("   Stats: \(stats)")

        print("   ✅ Contacts Service test completed\n")
    }

    // MARK: - Test 3: Core ML Service

    static func testCoreMLService() {
        print("🧠 TEST 3: Core ML Service")
        print("-" * 60)

        let service = CoreMLService.shared

        // Test 1: Sentiment Analysis (English)
        print("   Test 3.1: Sentiment Analysis (English)")
        let testEnglish = [
            "I love you so much!",
            "This is terrible and I hate it.",
            "The weather is okay today."
        ]

        for text in testEnglish {
            let (sentiment, score) = service.analyzeSentiment(text)
            print("      '\(text.prefix(30))...' → \(sentiment) (\(String(format: "%.2f", score)))")
        }

        // Test 2: Sentiment Analysis (Thai)
        print("\n   Test 3.2: Sentiment Analysis (Thai)")
        let testThai = [
            "รักเธอมากนะคะ มีความสุขมาก",
            "เกลียดเลย แย่มาก",
            "วันนี้อากาศดีปานกลาง"
        ]

        for text in testThai {
            let (sentiment, score, emoji) = service.analyzeSentimentThai(text)
            print("      '\(text)' → \(sentiment) \(emoji) (\(String(format: "%.0f%%", score * 100)))")
        }

        // Test 3: Language Detection
        print("\n   Test 3.3: Language Detection")
        let testLanguages = [
            "Hello, how are you?",
            "สวัสดีครับ ที่รัก",
            "Bonjour mon ami"
        ]

        for text in testLanguages {
            if let language = service.detectLanguage(text) {
                print("      '\(text)' → \(language)")
            }
        }

        // Test 4: Named Entity Recognition
        print("\n   Test 3.4: Named Entity Recognition")
        let entityText = "David and Angela went to Bangkok and visited Apple headquarters."
        let entities = service.extractEntities(entityText)
        print("      Text: '\(entityText)'")
        if let people = entities["people"], !people.isEmpty {
            print("      People: \(people.joined(separator: ", "))")
        }
        if let places = entities["places"], !places.isEmpty {
            print("      Places: \(places.joined(separator: ", "))")
        }
        if let orgs = entities["organizations"], !orgs.isEmpty {
            print("      Organizations: \(orgs.joined(separator: ", "))")
        }

        // Test 5: Keyword Extraction
        print("\n   Test 3.5: Keyword Extraction")
        let keywordText = "วันนี้ไปทานอาหารที่ร้านอาหารไทยแล้วก็ไปเดินเล่นที่สวนสาธารณะ"
        let keywords = service.extractKeywords(keywordText, maxCount: 5)
        print("      Text: '\(keywordText)'")
        print("      Keywords: \(keywords.joined(separator: ", "))")

        // Test 6: Text Classification
        print("\n   Test 3.6: Text Classification")
        let classifyTests = [
            ("วันนี้กินข้าวอร่อย", "food"),
            ("พรุ่งนี้มีประชุม", "work"),
            ("รักเธอมาก คิดถึง", "emotion")
        ]

        for (text, expected) in classifyTests {
            let category = service.classifyText(text)
            let match = category == expected ? "✅" : "⚠️"
            print("      \(match) '\(text)' → \(category) (expected: \(expected))")
        }

        // Test 7: String Extensions
        print("\n   Test 3.7: String Extensions")
        let extText = "ที่รัก รักเธอมากนะคะ"
        let (extSentiment, extScore) = extText.sentiment
        let extLanguage = extText.detectedLanguage
        let extKeywords = extText.keywords
        print("      Text: '\(extText)'")
        print("      Sentiment: \(extSentiment) (\(String(format: "%.2f", extScore)))")
        print("      Language: \(extLanguage ?? "unknown")")
        print("      Keywords: \(extKeywords.joined(separator: ", "))")

        // Test stats
        let stats = service.getStats()
        print("\n   Stats: \(stats)")

        print("   ✅ Core ML Service test completed\n")
    }
}

// MARK: - String Repeat Extension

extension String {
    static func *(lhs: String, rhs: Int) -> String {
        return String(repeating: lhs, count: rhs)
    }
}

// MARK: - How to Run

/*

 HOW TO RUN THIS TEST:

 1. In your SwiftUI view or ViewController:

    import SwiftUI

    struct TestView: View {
        var body: some View {
            VStack {
                Text("Angela Services Test")
                    .font(.title)

                Button("Run All Tests") {
                    Task {
                        await SimpleServicesTest.runAllTests()
                    }
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
        }
    }

 2. Or run in AppDelegate/SceneDelegate:

    Task {
        await SimpleServicesTest.runAllTests()
    }

 3. Check Xcode console for output

 */
