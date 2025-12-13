//
//  ContactsService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-07.
//  Contacts access using Contacts framework (100% on-device)
//

import Foundation
@preconcurrency import Contacts
import Combine

/// Service for accessing Contacts
/// Uses Contacts framework - 100% on-device, privacy-first
@MainActor
@Observable
class ContactsService {

    // MARK: - Singleton
    static let shared = ContactsService()

    // MARK: - Properties
    private let contactStore = CNContactStore()

    var hasContactsAccess = false
    var isLoading = false
    var lastError: String?

    // MARK: - Initialization

    private init() {
        print("📞 [ContactsService] Initialized")
        Task {
            await checkPermission()
        }
    }

    // MARK: - Permission Management

    /// Check current permission status
    func checkPermission() async {
        let status = CNContactStore.authorizationStatus(for: .contacts)
        hasContactsAccess = (status == .authorized)
        print("📞 [ContactsService] Contacts access: \(hasContactsAccess)")
    }

    /// Request contacts access
    func requestAccess() async throws {
        print("📞 [ContactsService] Requesting contacts access...")

        let granted = try await contactStore.requestAccess(for: .contacts)
        hasContactsAccess = granted
        print(granted ? "✅ Contacts access granted" : "❌ Contacts access denied")
    }

    // MARK: - Fetch Contacts

    /// Get all contacts (async, runs on background thread)
    func getAllContacts() async -> [CNContact] {
        guard hasContactsAccess else {
            print("⚠️ [ContactsService] No contacts access")
            return []
        }

        // Capture contactStore before entering Task.detached
        let store = self.contactStore

        // Run on background thread to avoid main thread warning
        return await Task.detached(priority: .userInitiated) {
            let keysToFetch: [CNKeyDescriptor] = [
                CNContactGivenNameKey as CNKeyDescriptor,
                CNContactFamilyNameKey as CNKeyDescriptor,
                CNContactNicknameKey as CNKeyDescriptor,
                CNContactPhoneNumbersKey as CNKeyDescriptor,
                CNContactEmailAddressesKey as CNKeyDescriptor,
                CNContactPostalAddressesKey as CNKeyDescriptor,
                CNContactBirthdayKey as CNKeyDescriptor,
                CNContactImageDataKey as CNKeyDescriptor,
                CNContactOrganizationNameKey as CNKeyDescriptor,
                CNContactJobTitleKey as CNKeyDescriptor
                // CNContactNoteKey removed - iOS 26.1 doesn't allow access for privacy
            ]

            let request = CNContactFetchRequest(keysToFetch: keysToFetch)
            var contacts: [CNContact] = []

            do {
                try store.enumerateContacts(with: request) { contact, _ in
                    contacts.append(contact)
                }
                print("📞 [ContactsService] Found \(contacts.count) contacts")
            } catch {
                print("❌ [ContactsService] Error fetching contacts: \(error)")
            }

            return contacts.sorted { contact1, contact2 in
                let name1 = "\(contact1.givenName) \(contact1.familyName)"
                let name2 = "\(contact2.givenName) \(contact2.familyName)"
                return name1 < name2
            }
        }.value
    }

    /// Search contacts by name (async)
    func searchContacts(name: String) async -> [CNContact] {
        guard hasContactsAccess else {
            print("⚠️ [ContactsService] No contacts access")
            return []
        }

        let allContacts = await getAllContacts()
        let lowercasedName = name.lowercased()

        return allContacts.filter { contact in
            let fullName = "\(contact.givenName) \(contact.familyName)".lowercased()
            let nickname = contact.nickname.lowercased()

            return fullName.contains(lowercasedName) ||
                   nickname.contains(lowercasedName) ||
                   contact.givenName.lowercased().contains(lowercasedName) ||
                   contact.familyName.lowercased().contains(lowercasedName)
        }
    }

    /// Get contact by identifier (async)
    func getContact(identifier: String) async -> CNContact? {
        guard hasContactsAccess else {
            print("⚠️ [ContactsService] No contacts access")
            return nil
        }

        // Capture contactStore before Task
        let store = self.contactStore

        return await Task.detached(priority: .userInitiated) {
            let keysToFetch: [CNKeyDescriptor] = [
                CNContactGivenNameKey as CNKeyDescriptor,
                CNContactFamilyNameKey as CNKeyDescriptor,
                CNContactNicknameKey as CNKeyDescriptor,
                CNContactPhoneNumbersKey as CNKeyDescriptor,
                CNContactEmailAddressesKey as CNKeyDescriptor,
                CNContactPostalAddressesKey as CNKeyDescriptor,
                CNContactBirthdayKey as CNKeyDescriptor,
                CNContactImageDataKey as CNKeyDescriptor,
                CNContactOrganizationNameKey as CNKeyDescriptor,
                CNContactJobTitleKey as CNKeyDescriptor
                // CNContactNoteKey removed - iOS 26.1 doesn't allow access for privacy
            ]

            do {
                let contact = try store.unifiedContact(
                    withIdentifier: identifier,
                    keysToFetch: keysToFetch
                )
                return contact
            } catch {
                print("❌ [ContactsService] Error fetching contact: \(error)")
                return nil
            }
        }.value
    }

    /// Get contacts with birthdays this month (async)
    func getBirthdaysThisMonth() async -> [(contact: CNContact, birthday: DateComponents)] {
        guard hasContactsAccess else {
            print("⚠️ [ContactsService] No contacts access")
            return []
        }

        let allContacts = await getAllContacts()
        let calendar = Calendar.current
        let currentMonth = calendar.component(.month, from: Date())

        var birthdayContacts: [(CNContact, DateComponents)] = []

        for contact in allContacts {
            if let birthday = contact.birthday,
               let month = birthday.month,
               month == currentMonth {
                birthdayContacts.append((contact, birthday))
            }
        }

        return birthdayContacts.sorted { contact1, contact2 in
            guard let day1 = contact1.1.day,
                  let day2 = contact2.1.day else {
                return false
            }
            return day1 < day2
        }
    }

    // MARK: - Helper Methods

    /// Format contact for display
    func formatContact(_ contact: CNContact, includeDetails: Bool = false) -> String {
        var result = ""

        // Name
        let fullName = "\(contact.givenName) \(contact.familyName)".trimmingCharacters(in: .whitespaces)
        result += fullName.isEmpty ? "ไม่มีชื่อ" : fullName

        if let nickname = contact.nickname as String?, !nickname.isEmpty {
            result += " (\(nickname))"
        }

        if includeDetails {
            // Phone numbers
            if !contact.phoneNumbers.isEmpty {
                result += "\n📱 เบอร์โทร:"
                for phoneNumber in contact.phoneNumbers {
                    let label = CNLabeledValue<CNPhoneNumber>.localizedString(forLabel: phoneNumber.label ?? "")
                    let number = phoneNumber.value.stringValue
                    result += "\n   • \(label): \(number)"
                }
            }

            // Email addresses
            if !contact.emailAddresses.isEmpty {
                result += "\n📧 อีเมล:"
                for email in contact.emailAddresses {
                    let label = CNLabeledValue<NSString>.localizedString(forLabel: email.label ?? "")
                    let address = email.value as String
                    result += "\n   • \(label): \(address)"
                }
            }

            // Organization
            if !contact.organizationName.isEmpty {
                result += "\n🏢 บริษัท: \(contact.organizationName)"
                if !contact.jobTitle.isEmpty {
                    result += " (\(contact.jobTitle))"
                }
            }

            // Birthday
            if let birthday = contact.birthday,
               let month = birthday.month,
               let day = birthday.day {
                result += "\n🎂 วันเกิด: \(day)/\(month)"
                if let year = birthday.year {
                    result += "/\(year)"
                }
            }

            // Address
            if !contact.postalAddresses.isEmpty {
                result += "\n📍 ที่อยู่:"
                for address in contact.postalAddresses {
                    let label = CNLabeledValue<CNPostalAddress>.localizedString(forLabel: address.label ?? "")
                    let addr = address.value
                    result += "\n   • \(label): \(CNPostalAddressFormatter.string(from: addr, style: .mailingAddress))"
                }
            }

            // Notes
            if !contact.note.isEmpty {
                result += "\n📝 บันทึก: \(contact.note)"
            }
        }

        return result
    }

    /// Get phone numbers for a contact
    func getPhoneNumbers(for contact: CNContact) -> [String] {
        return contact.phoneNumbers.map { $0.value.stringValue }
    }

    /// Get email addresses for a contact
    func getEmailAddresses(for contact: CNContact) -> [String] {
        return contact.emailAddresses.map { $0.value as String }
    }

    /// Get summary for Angela to speak (async)
    func getSearchResultsSummary(name: String) async -> String {
        let contacts = await searchContacts(name: name)

        if contacts.isEmpty {
            return "ไม่พบรายชื่อ '\(name)' ในสมุดโทรศัพท์ค่ะ 🔍"
        }

        if contacts.count == 1 {
            let contact = contacts[0]
            return "พบ 1 รายชื่อค่ะ:\n\n\(formatContact(contact, includeDetails: true))"
        }

        var summary = "พบ \(contacts.count) รายชื่อค่ะ:\n\n"
        for (index, contact) in contacts.enumerated() {
            summary += "\(index + 1). \(formatContact(contact, includeDetails: false))\n"
        }

        return summary
    }

    /// Get birthday summary for this month (async)
    func getBirthdaySummary() async -> String {
        let birthdays = await getBirthdaysThisMonth()

        if birthdays.isEmpty {
            return "เดือนนี้ไม่มีวันเกิดของใครค่ะ ✨"
        }

        var summary = "เดือนนี้มีวันเกิด \(birthdays.count) คนค่ะ:\n\n"

        for (contact, birthday) in birthdays {
            let name = "\(contact.givenName) \(contact.familyName)".trimmingCharacters(in: .whitespaces)
            if let day = birthday.day {
                summary += "🎂 วันที่ \(day): \(name)\n"
            }
        }

        return summary
    }

    // MARK: - Statistics

    func getStats() async -> [String: Any] {
        let totalContacts = hasContactsAccess ? await getAllContacts().count : 0
        let birthdaysCount = hasContactsAccess ? await getBirthdaysThisMonth().count : 0

        return [
            "has_access": hasContactsAccess,
            "total_contacts": totalContacts,
            "birthdays_this_month": birthdaysCount
        ]
    }
}

// MARK: - CNContact Extension

extension CNContact {
    var displayName: String {
        ContactsService.shared.formatContact(self, includeDetails: false)
    }

    var fullDetails: String {
        ContactsService.shared.formatContact(self, includeDetails: true)
    }
}
