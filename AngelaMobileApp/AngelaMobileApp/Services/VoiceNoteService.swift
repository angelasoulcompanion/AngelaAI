//
//  VoiceNoteService.swift
//  Angela Mobile App
//
//  Voice recording service using AVAudioRecorder
//  Feature 2: Voice Notes
//

import Foundation
import AVFoundation
import Combine

class VoiceNoteService: NSObject, ObservableObject {
    static let shared = VoiceNoteService()

    @Published var isRecording = false
    @Published var recordingTime: TimeInterval = 0
    @Published var recordingError: String?

    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingTimer: Timer?
    private let voiceNotesDirectory: URL

    private override init() {
        // Create voice notes directory in Documents
        let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        voiceNotesDirectory = documentsDirectory.appendingPathComponent("AngelaVoiceNotes", isDirectory: true)

        super.init()

        // Create directory if not exists
        try? FileManager.default.createDirectory(at: voiceNotesDirectory, withIntermediateDirectories: true)

        print("🎤 Voice notes directory: \(voiceNotesDirectory.path)")
    }

    // MARK: - Recording

    func startRecording() async -> Bool {
        // Request permission
        let permissionGranted = await requestMicrophonePermission()
        guard permissionGranted else {
            await MainActor.run {
                recordingError = "ขออนุญาตใช้ไมโครโฟนไม่สำเร็จ"
            }
            return false
        }

        // Setup audio session
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.playAndRecord, mode: .default)
            try audioSession.setActive(true)
        } catch {
            await MainActor.run {
                recordingError = "ไม่สามารถตั้งค่า Audio Session: \(error.localizedDescription)"
            }
            return false
        }

        // Generate filename
        let timestamp = ISO8601DateFormatter().string(from: Date()).replacingOccurrences(of: ":", with: "-")
        let filename = "voice_\(timestamp).m4a"
        let fileURL = voiceNotesDirectory.appendingPathComponent(filename)

        // Setup recording settings
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100.0,
            AVNumberOfChannelsKey: 2,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        do {
            audioRecorder = try AVAudioRecorder(url: fileURL, settings: settings)
            audioRecorder?.delegate = self
            audioRecorder?.record()

            await MainActor.run {
                isRecording = true
                recordingTime = 0
                startTimer()
            }

            print("🎤 Started recording: \(filename)")
            return true
        } catch {
            await MainActor.run {
                recordingError = "ไม่สามารถเริ่มบันทึกเสียง: \(error.localizedDescription)"
            }
            return false
        }
    }

    func stopRecording() -> String? {
        guard isRecording else { return nil }

        audioRecorder?.stop()
        stopTimer()

        let filename = audioRecorder?.url.lastPathComponent

        isRecording = false
        audioRecorder = nil

        // Deactivate audio session
        try? AVAudioSession.sharedInstance().setActive(false)

        print("🎤 Stopped recording: \(filename ?? "unknown")")
        return filename
    }

    func cancelRecording() {
        guard isRecording else { return }

        let fileURL = audioRecorder?.url
        _ = stopRecording()  // Explicitly ignore return value

        // Delete the file
        if let url = fileURL {
            try? FileManager.default.removeItem(at: url)
            print("🗑️ Cancelled and deleted recording")
        }
    }

    // MARK: - Playback

    func playVoiceNote(_ filename: String) async -> Bool {
        let fileURL = voiceNotesDirectory.appendingPathComponent(filename)

        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            await MainActor.run {
                recordingError = "ไม่พบไฟล์เสียง"
            }
            return false
        }

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: fileURL)
            audioPlayer?.play()
            print("▶️ Playing voice note: \(filename)")
            return true
        } catch {
            await MainActor.run {
                recordingError = "ไม่สามารถเล่นเสียง: \(error.localizedDescription)"
            }
            return false
        }
    }

    func stopPlayback() {
        audioPlayer?.stop()
        audioPlayer = nil
    }

    // MARK: - File Management

    func deleteVoiceNote(_ filename: String) {
        let fileURL = voiceNotesDirectory.appendingPathComponent(filename)
        try? FileManager.default.removeItem(at: fileURL)
        print("🗑️ Deleted voice note: \(filename)")
    }

    func getVoiceNoteURL(_ filename: String) -> URL {
        return voiceNotesDirectory.appendingPathComponent(filename)
    }

    func getDuration(_ filename: String) -> TimeInterval? {
        let fileURL = voiceNotesDirectory.appendingPathComponent(filename)
        guard let player = try? AVAudioPlayer(contentsOf: fileURL) else { return nil }
        return player.duration
    }

    // MARK: - Permissions

    private func requestMicrophonePermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }

    // MARK: - Timer

    private func startTimer() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            self.recordingTime += 0.1
        }
    }

    private func stopTimer() {
        recordingTimer?.invalidate()
        recordingTimer = nil
    }
}

// MARK: - AVAudioRecorderDelegate

extension VoiceNoteService: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if !flag {
            recordingError = "การบันทึกไม่สำเร็จ"
        }
    }

    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        recordingError = "เกิดข้อผิดพลาด: \(error?.localizedDescription ?? "unknown")"
    }
}
