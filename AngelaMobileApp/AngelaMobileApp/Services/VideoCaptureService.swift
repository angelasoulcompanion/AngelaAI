//
//  VideoCaptureService.swift
//  Angela Mobile App
//
//  Video capture service for short videos
//  Feature 3: Video Capture
//

import Foundation
import AVFoundation
import UIKit
import Combine

class VideoCaptureService: NSObject, ObservableObject {
    static let shared = VideoCaptureService()

    @Published var isRecording = false
    @Published var recordingDuration: TimeInterval = 0

    private let videoDirectory: URL
    private var recordingTimer: Timer?

    private override init() {
        // Create video directory in Documents
        let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        videoDirectory = documentsDirectory.appendingPathComponent("AngelaVideos", isDirectory: true)

        super.init()

        // Create directory if not exists
        try? FileManager.default.createDirectory(at: videoDirectory, withIntermediateDirectories: true)

        print("🎥 Video directory: \(videoDirectory.path)")
    }

    // MARK: - Save Video

    func saveVideo(from url: URL) -> String? {
        // Generate unique filename
        let timestamp = ISO8601DateFormatter().string(from: Date()).replacingOccurrences(of: ":", with: "-")
        let uniqueID = UUID().uuidString.prefix(8)
        let filename = "video_\(timestamp)_\(uniqueID).mov"
        let destinationURL = videoDirectory.appendingPathComponent(filename)

        do {
            // Copy video to app directory
            try FileManager.default.copyItem(at: url, to: destinationURL)
            print("✅ Video saved: \(filename)")
            return filename
        } catch {
            print("❌ Failed to save video: \(error)")
            return nil
        }
    }

    // MARK: - Load Video

    func getVideoURL(_ filename: String) -> URL {
        return videoDirectory.appendingPathComponent(filename)
    }

    func videoExists(_ filename: String) -> Bool {
        let fileURL = videoDirectory.appendingPathComponent(filename)
        return FileManager.default.fileExists(atPath: fileURL.path)
    }

    // MARK: - Delete Video

    func deleteVideo(_ filename: String) {
        let fileURL = videoDirectory.appendingPathComponent(filename)
        do {
            try FileManager.default.removeItem(at: fileURL)
            print("🗑️ Video deleted: \(filename)")
        } catch {
            print("❌ Failed to delete video: \(error)")
        }
    }

    // MARK: - Get Video Duration

    func getVideoDuration(_ filename: String) async -> TimeInterval? {
        let fileURL = videoDirectory.appendingPathComponent(filename)
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return nil }

        let asset = AVURLAsset(url: fileURL)
        do {
            let duration = try await asset.load(.duration)
            return duration.seconds
        } catch {
            print("❌ Failed to load video duration: \(error)")
            return nil
        }
    }

    // MARK: - Generate Thumbnail

    func generateThumbnail(_ filename: String) async -> UIImage? {
        let fileURL = videoDirectory.appendingPathComponent(filename)
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return nil }

        let asset = AVURLAsset(url: fileURL)
        let imageGenerator = AVAssetImageGenerator(asset: asset)
        imageGenerator.appliesPreferredTrackTransform = true

        let time = CMTime(seconds: 1, preferredTimescale: 60)

        return await withCheckedContinuation { continuation in
            imageGenerator.generateCGImageAsynchronously(for: time) { cgImage, actualTime, error in
                if let error = error {
                    print("❌ Failed to generate thumbnail: \(error)")
                    continuation.resume(returning: nil)
                } else if let cgImage = cgImage {
                    continuation.resume(returning: UIImage(cgImage: cgImage))
                } else {
                    continuation.resume(returning: nil)
                }
            }
        }
    }

    // MARK: - Get All Videos

    func getAllVideos() -> [String] {
        do {
            let files = try FileManager.default.contentsOfDirectory(atPath: videoDirectory.path)
            return files.filter { $0.hasSuffix(".mov") || $0.hasSuffix(".mp4") }
        } catch {
            print("❌ Failed to list videos: \(error)")
            return []
        }
    }
}
