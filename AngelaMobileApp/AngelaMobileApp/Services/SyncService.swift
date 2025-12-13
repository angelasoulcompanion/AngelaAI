//
//  SyncService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  Handles sync between local SQLite and Angela backend
//

import Foundation
import Network
import Combine
import UIKit

class SyncService: ObservableObject {
    static let shared = SyncService()

    @Published var isSyncing = false
    @Published var lastSyncDate: Date?
    @Published var autoSyncEnabled = true

    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.angela.sync")

    private var syncFolderURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("AngelaSync", isDirectory: true)
    }

    private init() {
        // Create sync folder
        try? FileManager.default.createDirectory(at: syncFolderURL, withIntermediateDirectories: true)

        // Start network monitoring
        startNetworkMonitoring()

        // Load last sync date
        loadLastSyncDate()
    }

    // MARK: - Network Monitoring

    private func startNetworkMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            guard let self = self else { return }

            if path.status == .satisfied && self.autoSyncEnabled {
                // Check if connected to home WiFi
                if self.isConnectedToHomeWiFi() {
                    print("🏠 Connected to home WiFi - checking auto-sync")
                    self.checkAutoSync()
                }
            }
        }

        monitor.start(queue: queue)
    }

    private func isConnectedToHomeWiFi() -> Bool {
        // Check if connected via WiFi (not cellular)
        // iOS restricts SSID access, so we check network type instead

        // currentPath is not Optional in NWPathMonitor
        let path = monitor.currentPath

        // Check if WiFi interface is available
        let isWiFi = path.usesInterfaceType(.wifi)

        if isWiFi {
            print("🏠 Connected via WiFi - eligible for auto-sync")
        }

        return isWiFi
    }

    // MARK: - Sync Operations

    func checkAutoSync() {
        guard autoSyncEnabled else { return }

        // Check if there are unsynced items
        let database = DatabaseService.shared
        let unsyncedCount = database.experiences.filter { !$0.synced }.count +
                           database.emotions.filter { !$0.synced }.count +
                           database.chatMessages.filter { !$0.synced }.count +
                           database.getUnsyncedHealthEntries().count

        if unsyncedCount > 0 {
            print("📤 Auto-sync triggered: \(unsyncedCount) unsynced items")
            performSync()
        }
    }

    func performSync() {
        guard !isSyncing else {
            print("⚠️ Sync already in progress")
            return
        }

        DispatchQueue.main.async {
            self.isSyncing = true
        }

        Task {
            print("🔄 Starting sync...")

            let database = DatabaseService.shared
            let unsyncedExperiences = database.experiences.filter { !$0.synced }
            let unsyncedEmotions = database.emotions.filter { !$0.synced }
            let unsyncedChatMessages = database.chatMessages.filter { !$0.synced }

            var syncedExperiences = 0
            var syncedEmotions = 0
            var syncedChatMessages = 0

            // 1. Upload experiences
            if !unsyncedExperiences.isEmpty {
                print("📤 Syncing \(unsyncedExperiences.count) experiences...")
                for experience in unsyncedExperiences {
                    do {
                        let success = try await uploadExperience(experience)
                        if success {
                            syncedExperiences += 1
                            // Mark as synced but keep in local database (for Timeline view)
                            database.markExperienceAsSynced(experience.id)
                            print("✅ Marked experience as synced: \(experience.title)")
                        }
                    } catch {
                        print("❌ Failed to upload experience '\(experience.title)': \(error)")
                    }
                }
            }

            // 2. Upload emotions
            if !unsyncedEmotions.isEmpty {
                print("💭 Syncing \(unsyncedEmotions.count) emotions...")
                for emotion in unsyncedEmotions {
                    do {
                        let success = try await uploadEmotion(emotion)
                        if success {
                            syncedEmotions += 1
                            // Mark as synced but keep in local database (for history view)
                            database.markEmotionAsSynced(emotion.id)
                            print("✅ Marked emotion as synced: \(emotion.emotion)")
                        }
                    } catch {
                        print("❌ Failed to upload emotion: \(error)")
                    }
                }
            }

            // 3. Upload chat messages
            if !unsyncedChatMessages.isEmpty {
                print("💬 Syncing \(unsyncedChatMessages.count) chat messages...")
                for message in unsyncedChatMessages {
                    do {
                        let success = try await uploadChatMessage(message)
                        if success {
                            syncedChatMessages += 1
                            // Mark as synced but keep in local database (for chat history)
                            database.markChatMessageAsSynced(message.id)
                            print("✅ Marked chat message as synced")
                        }
                    } catch {
                        print("❌ Failed to upload chat message: \(error)")
                    }
                }
            }

            // 4. Upload health entries (NEW! 2025-12-11 💪)
            let unsyncedHealthEntries = database.getUnsyncedHealthEntries()
            var syncedHealthEntries = 0

            if !unsyncedHealthEntries.isEmpty {
                print("💪 Syncing \(unsyncedHealthEntries.count) health entries...")
                for healthEntry in unsyncedHealthEntries {
                    do {
                        let success = try await uploadHealthEntry(healthEntry)
                        if success {
                            syncedHealthEntries += 1
                            database.markHealthEntryAsSynced(healthEntry.id)
                            print("✅ Marked health entry as synced: \(healthEntry.formattedDate)")
                        }
                    } catch {
                        print("❌ Failed to upload health entry: \(error)")
                    }
                }
            }

            // Update last sync date
            DispatchQueue.main.async {
                self.lastSyncDate = Date()
                self.saveLastSyncDate()
                self.isSyncing = false
            }

            print("✅ Sync completed! \(syncedExperiences) experiences, \(syncedEmotions) emotions, \(syncedChatMessages) chat messages, \(syncedHealthEntries) health entries uploaded")
        }
    }

    // MARK: - Upload Experience to Backend

    private func uploadExperience(_ experience: Experience) async throws -> Bool {
        // Backend URL - Read from UserDefaults (configurable in Settings)
        // NOTE: Must use Mac's IP address, not localhost (iOS can't access localhost)
        let baseURL = UserDefaults.standard.string(forKey: "backendURL") ?? "http://192.168.1.42:50001"
        let uploadURL = URL(string: "\(baseURL)/api/experiences/upload")!

        print("🌐 Backend URL: \(baseURL)")
        print("📍 Upload URL: \(uploadURL.absoluteString)")

        // Create multipart form data
        var request = URLRequest(url: uploadURL)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Add form fields
        addFormField(name: "place_name", value: experience.placeName ?? "Unknown Place", to: &body, boundary: boundary)
        addFormField(name: "area", value: experience.area ?? "", to: &body, boundary: boundary)
        addFormField(name: "title", value: experience.title, to: &body, boundary: boundary)
        addFormField(name: "description", value: experience.description, to: &body, boundary: boundary)

        if let rating = experience.rating {
            addFormField(name: "overall_rating", value: "\(rating)", to: &body, boundary: boundary)
        }

        // ✅ Send emotion tag to backend (CRITICAL FOR ANGELA'S EMOTIONAL LEARNING!)
        if let emotion = experience.emotion {
            addFormField(name: "angela_emotion", value: emotion, to: &body, boundary: boundary)
            print("💜 Adding emotion: \(emotion)")
        }

        if let emotionalIntensity = experience.emotionalIntensity {
            addFormField(name: "emotional_intensity", value: "\(emotionalIntensity)", to: &body, boundary: boundary)
        }

        // ✅ NEW: David's mood (CRITICAL FOR UNDERSTANDING DAVID'S STATE!)
        if let davidMood = experience.davidMood {
            addFormField(name: "david_mood", value: davidMood, to: &body, boundary: boundary)
            print("😊 Adding David's mood: \(davidMood)")
        }

        // ✅ NEW: Importance level (1-10)
        if let importanceLevel = experience.importanceLevel {
            addFormField(name: "importance_level", value: "\(importanceLevel)", to: &body, boundary: boundary)
            print("⭐ Adding importance level: \(importanceLevel)")
        }

        // ✅ NEW: Memorable moments (what made this special)
        if let memorableMoments = experience.memorableMoments {
            addFormField(name: "memorable_moments", value: memorableMoments, to: &body, boundary: boundary)
            print("💭 Adding memorable moments: \(memorableMoments)")
        }

        // ✅ NEW: Image captions (comma-separated)
        if !experience.imageCaptions.isEmpty {
            let captionsString = experience.imageCaptions.joined(separator: ",")
            addFormField(name: "image_captions", value: captionsString, to: &body, boundary: boundary)
            print("🖼️ Adding image captions: \(experience.imageCaptions.count) captions")
        }

        // ✅ ADD GPS COORDINATES (CRITICAL FOR ANGELA'S LEARNING!)
        if let latitude = experience.latitude {
            addFormField(name: "latitude", value: "\(latitude)", to: &body, boundary: boundary)
            print("📍 Adding GPS latitude: \(latitude)")
        }

        if let longitude = experience.longitude {
            addFormField(name: "longitude", value: "\(longitude)", to: &body, boundary: boundary)
            print("📍 Adding GPS longitude: \(longitude)")
        }

        // Add experienced_at timestamp (with timezone!)
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.timeZone = TimeZone.current // Include timezone info
        let timestampString = dateFormatter.string(from: experience.experiencedAt)
        addFormField(name: "experienced_at", value: timestampString, to: &body, boundary: boundary)

        // Add images
        for photoFilename in experience.photos {
            if let image = PhotoManager.shared.loadPhoto(photoFilename),
               let imageData = image.jpegData(compressionQuality: 0.8) {
                addImageField(name: "images", filename: photoFilename, data: imageData, to: &body, boundary: boundary)
            }
        }

        // Add closing boundary
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        print("📤 Uploading '\(experience.title)' with \(experience.photos.count) photos...")
        print("📦 Request body size: \(body.count) bytes")

        // Send request
        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SyncError.syncFailed
        }

        print("📥 Response status: \(httpResponse.statusCode)")

        // Print response body for debugging
        if let responseString = String(data: data, encoding: .utf8) {
            print("📥 Response body: \(responseString)")
        }

        if httpResponse.statusCode == 200 {
            // Parse response
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let success = json["success"] as? Bool,
               success {
                print("✅ Upload successful!")
                return true
            }
        }

        return false
    }

    private func addFormField(name: String, value: String, to body: inout Data, boundary: String) {
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(value)\r\n".data(using: .utf8)!)
    }

    private func addImageField(name: String, filename: String, data: Data, to body: inout Data, boundary: String) {
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n".data(using: .utf8)!)
    }

    // MARK: - Upload Emotion to Backend

    private func uploadEmotion(_ emotion: EmotionCapture) async throws -> Bool {
        let baseURL = UserDefaults.standard.string(forKey: "backendURL") ?? "http://192.168.1.42:50001"
        let uploadURL = URL(string: "\(baseURL)/api/mobile/emotions")!

        var request = URLRequest(url: uploadURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Create JSON payload
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.timeZone = TimeZone.current

        let payload: [String: Any] = [
            "emotion": emotion.emotion,
            "intensity": emotion.intensity,
            "context": emotion.context as Any,
            "created_at": dateFormatter.string(from: emotion.createdAt)
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        print("💭 Uploading emotion: \(emotion.emotion) (\(emotion.intensity)/10)...")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SyncError.syncFailed
        }

        print("📥 Emotion response status: \(httpResponse.statusCode)")

        if let responseString = String(data: data, encoding: .utf8) {
            print("📥 Emotion response: \(responseString)")
        }

        return httpResponse.statusCode == 200
    }

    // MARK: - Upload Health Entry to Backend (NEW! 2025-12-11 💪)

    private func uploadHealthEntry(_ healthEntry: HealthEntry) async throws -> Bool {
        let baseURL = UserDefaults.standard.string(forKey: "backendURL") ?? "http://192.168.1.42:50001"
        let uploadURL = URL(string: "\(baseURL)/api/mobile/health")!

        var request = URLRequest(url: uploadURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Create JSON payload
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.timeZone = TimeZone.current

        let trackedDateFormatter = DateFormatter()
        trackedDateFormatter.dateFormat = "yyyy-MM-dd"

        var payload: [String: Any] = [
            "tracked_date": trackedDateFormatter.string(from: healthEntry.trackedDate),
            "alcohol_free": healthEntry.alcoholFree,
            "drinks_count": healthEntry.drinksCount,
            "exercised": healthEntry.exercised,
            "exercise_duration_minutes": healthEntry.exerciseDurationMinutes,
            "created_at": dateFormatter.string(from: healthEntry.createdAt)
        ]

        // Add optional fields
        if let drinkType = healthEntry.drinkType {
            payload["drink_type"] = drinkType
        }
        if let alcoholNotes = healthEntry.alcoholNotes {
            payload["alcohol_notes"] = alcoholNotes
        }
        if let exerciseType = healthEntry.exerciseType {
            payload["exercise_type"] = exerciseType
        }
        if let exerciseIntensity = healthEntry.exerciseIntensity {
            payload["exercise_intensity"] = exerciseIntensity.rawValue
        }
        if let exerciseNotes = healthEntry.exerciseNotes {
            payload["exercise_notes"] = exerciseNotes
        }
        if let mood = healthEntry.mood {
            payload["mood"] = mood
        }
        if let energyLevel = healthEntry.energyLevel {
            payload["energy_level"] = energyLevel
        }
        if let notes = healthEntry.notes {
            payload["notes"] = notes
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        print("💪 Uploading health entry for \(trackedDateFormatter.string(from: healthEntry.trackedDate))...")
        print("   - Alcohol-free: \(healthEntry.alcoholFree)")
        print("   - Exercised: \(healthEntry.exercised) (\(healthEntry.exerciseDurationMinutes) min)")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SyncError.syncFailed
        }

        print("📥 Health entry response status: \(httpResponse.statusCode)")

        if let responseString = String(data: data, encoding: .utf8) {
            print("📥 Health entry response: \(responseString)")
        }

        return httpResponse.statusCode == 200
    }

    // MARK: - Upload Chat Message to Backend

    private func uploadChatMessage(_ message: ChatMessage) async throws -> Bool {
        let baseURL = UserDefaults.standard.string(forKey: "backendURL") ?? "http://192.168.1.42:50001"
        let uploadURL = URL(string: "\(baseURL)/api/mobile/chat")!

        var request = URLRequest(url: uploadURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Create JSON payload
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.timeZone = TimeZone.current

        let payload: [String: Any] = [
            "speaker": message.speaker,
            "message": message.message,
            "emotion": message.emotion as Any,
            "timestamp": dateFormatter.string(from: message.timestamp)
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        print("💬 Uploading chat message from \(message.speaker)...")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SyncError.syncFailed
        }

        print("📥 Chat message response status: \(httpResponse.statusCode)")

        if let responseString = String(data: data, encoding: .utf8) {
            print("📥 Chat message response: \(responseString)")
        }

        return httpResponse.statusCode == 200
    }

    // MARK: - Export Data

    private func exportUnsyncedData() async throws -> SyncExportData {
        let database = DatabaseService.shared

        let unsyncedExperiences = database.experiences.filter { !$0.synced }
        let unsyncedEmotions = database.emotions.filter { !$0.synced }

        print("📤 Exporting:")
        print("   - \(unsyncedExperiences.count) experiences")
        print("   - \(unsyncedEmotions.count) emotions")

        return SyncExportData(
            exportedAt: Date(),
            experiences: unsyncedExperiences,
            emotions: unsyncedEmotions
        )
    }

    private func writeToSyncFolder(_ data: SyncExportData) async throws -> URL {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = .prettyPrinted

        let jsonData = try encoder.encode(data)

        let timestamp = ISO8601DateFormatter().string(from: Date())
            .replacingOccurrences(of: ":", with: "-")
        let filename = "angela_sync_\(timestamp).json"
        let fileURL = syncFolderURL.appendingPathComponent(filename)

        try jsonData.write(to: fileURL)

        print("💾 Sync file written: \(filename)")
        return fileURL
    }

    private func waitForSyncCompletion(syncFile: URL) async throws -> Bool {
        // Wait for Python script to create a .success file
        let successFile = syncFile.deletingPathExtension().appendingPathExtension("success")

        // Poll for up to 30 seconds
        for _ in 0..<30 {
            if FileManager.default.fileExists(atPath: successFile.path) {
                print("✅ Sync confirmation received")
                // Clean up
                try? FileManager.default.removeItem(at: syncFile)
                try? FileManager.default.removeItem(at: successFile)
                return true
            }

            try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        }

        return false
    }

    private func markItemsAsSynced() async throws {
        // TODO: Implement marking items as synced in SQLite
        // For now, just log
        print("✅ Items marked as synced")
    }

    // MARK: - Persistence

    private func loadLastSyncDate() {
        if let timestamp = UserDefaults.standard.object(forKey: "lastSyncDate") as? Date {
            lastSyncDate = timestamp
        }
    }

    private func saveLastSyncDate() {
        if let date = lastSyncDate {
            UserDefaults.standard.set(date, forKey: "lastSyncDate")
        }
    }

    deinit {
        monitor.cancel()
    }
}

// MARK: - Data Models

struct SyncExportData: Codable {
    let exportedAt: Date
    let experiences: [Experience]
    let emotions: [EmotionCapture]

    enum CodingKeys: String, CodingKey {
        case exportedAt = "exported_at"
        case experiences
        case emotions
    }
}

// MARK: - Errors

enum SyncError: Error {
    case exportFailed
    case syncFailed
    case noUnsyncedData
}
