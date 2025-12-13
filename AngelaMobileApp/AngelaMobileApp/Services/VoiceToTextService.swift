//
//  VoiceToTextService.swift
//  Angela Mobile App
//
//  Voice-to-text transcription using Speech framework
//  Feature 30: Voice-to-Text Notes
//

import Foundation
import Speech
import AVFoundation
import Combine

class VoiceToTextService: NSObject, ObservableObject {
    static let shared = VoiceToTextService()

    @Published var isRecording = false
    @Published var transcribedText = ""
    @Published var recordingError: String?
    @Published var permissionStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined

    private var audioEngine: AVAudioEngine?
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?

    private override init() {
        super.init()

        // Initialize speech recognizer for Thai
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "th-TH"))

        // Fallback to English if Thai not available
        if speechRecognizer == nil {
            speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
            print("⚠️ Thai speech recognition not available, using English")
        }

        speechRecognizer?.delegate = self
    }

    // MARK: - Permission Request

    func requestPermissions() async -> Bool {
        // Request speech recognition permission
        let speechStatus = await requestSpeechRecognitionPermission()
        guard speechStatus == .authorized else {
            await MainActor.run {
                recordingError = "ไม่ได้รับอนุญาตใช้ Speech Recognition"
            }
            return false
        }

        // Request microphone permission
        let micStatus = await requestMicrophonePermission()
        guard micStatus else {
            await MainActor.run {
                recordingError = "ไม่ได้รับอนุญาตใช้ไมโครโฟน"
            }
            return false
        }

        return true
    }

    private func requestSpeechRecognitionPermission() async -> SFSpeechRecognizerAuthorizationStatus {
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status)
            }
        }
    }

    private func requestMicrophonePermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }

    // MARK: - Start Recording

    func startRecording() async throws {
        // Request permissions
        let hasPermission = await requestPermissions()
        guard hasPermission else {
            throw VoiceToTextError.permissionDenied
        }

        // Cancel previous task if exists
        recognitionTask?.cancel()
        recognitionTask = nil

        // Configure audio session
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)

        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw VoiceToTextError.recognitionNotAvailable
        }

        recognitionRequest.shouldReportPartialResults = true

        // iOS 13+ features
        if #available(iOS 13, *) {
            recognitionRequest.requiresOnDeviceRecognition = false
        }

        // Create audio engine
        audioEngine = AVAudioEngine()
        guard let audioEngine = audioEngine else {
            throw VoiceToTextError.audioEngineNotAvailable
        }

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        // Install tap on audio engine
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }

        audioEngine.prepare()
        try audioEngine.start()

        // Start recognition
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }

            var isFinal = false

            if let result = result {
                // Update transcribed text
                Task { @MainActor in
                    self.transcribedText = result.bestTranscription.formattedString
                }
                isFinal = result.isFinal
            }

            if error != nil || isFinal {
                // Stop audio engine
                audioEngine.stop()
                inputNode.removeTap(onBus: 0)

                self.recognitionRequest = nil
                self.recognitionTask = nil

                Task { @MainActor in
                    self.isRecording = false
                }
            }
        }

        await MainActor.run {
            isRecording = true
            transcribedText = ""
        }

        print("🎤 Voice-to-text recording started")
    }

    // MARK: - Stop Recording

    func stopRecording() {
        audioEngine?.stop()
        recognitionRequest?.endAudio()
        audioEngine?.inputNode.removeTap(onBus: 0)

        isRecording = false

        print("🛑 Voice-to-text recording stopped")
        print("📝 Transcribed: \(transcribedText)")
    }

    // MARK: - Transcribe Audio File

    func transcribeAudioFile(_ url: URL) async throws -> String {
        // Request permission
        let status = await requestSpeechRecognitionPermission()
        guard status == .authorized else {
            throw VoiceToTextError.permissionDenied
        }

        guard let recognizer = speechRecognizer else {
            throw VoiceToTextError.recognitionNotAvailable
        }

        let request = SFSpeechURLRecognitionRequest(url: url)
        request.shouldReportPartialResults = false

        return try await withCheckedThrowingContinuation { continuation in
            recognizer.recognitionTask(with: request) { result, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }

                if let result = result, result.isFinal {
                    continuation.resume(returning: result.bestTranscription.formattedString)
                }
            }
        }
    }

    // MARK: - Get Supported Languages

    func getSupportedLanguages() -> [String] {
        var languages: [String] = []

        // Check Thai
        if SFSpeechRecognizer(locale: Locale(identifier: "th-TH")) != nil {
            languages.append("ภาษาไทย (th-TH)")
        }

        // Check English
        if SFSpeechRecognizer(locale: Locale(identifier: "en-US")) != nil {
            languages.append("English (en-US)")
        }

        return languages
    }
}

// MARK: - SFSpeechRecognizerDelegate

extension VoiceToTextService: SFSpeechRecognizerDelegate {
    func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if !available {
            Task { @MainActor in
                recordingError = "Speech recognition ไม่พร้อมใช้งาน"
                isRecording = false
            }
        }
    }
}

// MARK: - Errors

enum VoiceToTextError: Error, LocalizedError {
    case permissionDenied
    case recognitionNotAvailable
    case audioEngineNotAvailable

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "ไม่ได้รับอนุญาตใช้ Speech Recognition"
        case .recognitionNotAvailable:
            return "Speech Recognition ไม่พร้อมใช้งาน"
        case .audioEngineNotAvailable:
            return "Audio Engine ไม่พร้อมใช้งาน"
        }
    }
}
