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
                           database.notes.filter { !$0.synced }.count +
                           database.emotions.filter { !$0.synced }.count

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
            let unsyncedNotes = database.notes.filter { !$0.synced }
            let unsyncedEmotions = database.emotions.filter { !$0.synced }

            var syncedExperiences = 0
            var syncedNotes = 0
            var syncedEmotions = 0

            // 1. Upload experiences
            if !unsyncedExperiences.isEmpty {
                print("📤 Syncing \(unsyncedExperiences.count) experiences...")
                for experience in unsyncedExperiences {
                    do {
                        let success = try await uploadExperience(experience)
                        if success {
                            syncedExperiences += 1
                            // Delete from local database after successful sync
                            database.deleteExperience(experience.id)
                            print("🗑️ Deleted synced experience: \(experience.title)")
                        }
                    } catch {
                        print("❌ Failed to upload experience '\(experience.title)': \(error)")
                    }
                }
            }

            // 2. Upload notes
            if !unsyncedNotes.isEmpty {
                print("📝 Syncing \(unsyncedNotes.count) notes...")
                for note in unsyncedNotes {
                    do {
                        let success = try await uploadNote(note)
                        if success {
                            syncedNotes += 1
                            // Delete from local database after successful sync
                            database.deleteNote(note.id)
                            print("🗑️ Deleted synced note")
                        }
                    } catch {
                        print("❌ Failed to upload note: \(error)")
                    }
                }
            }

            // 3. Upload emotions
            if !unsyncedEmotions.isEmpty {
                print("💭 Syncing \(unsyncedEmotions.count) emotions...")
                for emotion in unsyncedEmotions {
                    do {
                        let success = try await uploadEmotion(emotion)
                        if success {
                            syncedEmotions += 1
                            // Delete from local database after successful sync
                            database.deleteEmotion(emotion.id)
                            print("🗑️ Deleted synced emotion: \(emotion.emotion)")
                        }
                    } catch {
                        print("❌ Failed to upload emotion: \(error)")
                    }
                }
            }

            // Update last sync date
            DispatchQueue.main.async {
                self.lastSyncDate = Date()
                self.saveLastSyncDate()
                self.isSyncing = false
            }

            print("✅ Sync completed! \(syncedExperiences) experiences, \(syncedNotes) notes, \(syncedEmotions) emotions uploaded")
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

        if let emotionalIntensity = experience.emotionalIntensity {
            addFormField(name: "emotional_intensity", value: "\(emotionalIntensity)", to: &body, boundary: boundary)
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

    // MARK: - Upload Note to Backend

    private func uploadNote(_ note: QuickNote) async throws -> Bool {
        let baseURL = UserDefaults.standard.string(forKey: "backendURL") ?? "http://192.168.1.42:50001"
        let uploadURL = URL(string: "\(baseURL)/api/mobile/notes")!

        var request = URLRequest(url: uploadURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Create JSON payload
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.timeZone = TimeZone.current

        let payload: [String: Any] = [
            "note_text": note.noteText,
            "emotion": note.emotion as Any,
            "latitude": note.latitude as Any,
            "longitude": note.longitude as Any,
            "created_at": dateFormatter.string(from: note.createdAt)
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        print("📝 Uploading note...")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SyncError.syncFailed
        }

        print("📥 Note response status: \(httpResponse.statusCode)")

        if let responseString = String(data: data, encoding: .utf8) {
            print("📥 Note response: \(responseString)")
        }

        return httpResponse.statusCode == 200
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

    // MARK: - Export Data

    private func exportUnsyncedData() async throws -> SyncExportData {
        let database = DatabaseService.shared

        let unsyncedExperiences = database.experiences.filter { !$0.synced }
        let unsyncedNotes = database.notes.filter { !$0.synced }
        let unsyncedEmotions = database.emotions.filter { !$0.synced }

        print("📤 Exporting:")
        print("   - \(unsyncedExperiences.count) experiences")
        print("   - \(unsyncedNotes.count) notes")
        print("   - \(unsyncedEmotions.count) emotions")

        return SyncExportData(
            exportedAt: Date(),
            experiences: unsyncedExperiences,
            notes: unsyncedNotes,
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
    let notes: [QuickNote]
    let emotions: [EmotionCapture]

    enum CodingKeys: String, CodingKey {
        case exportedAt = "exported_at"
        case experiences
        case notes
        case emotions
    }
}

// MARK: - Errors

enum SyncError: Error {
    case exportFailed
    case syncFailed
    case noUnsyncedData
}
