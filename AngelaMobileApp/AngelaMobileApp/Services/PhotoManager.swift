//
//  PhotoManager.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  Manages photo storage on disk
//

import UIKit
import CoreLocation
import ImageIO

class PhotoManager {
    static let shared = PhotoManager()

    private let photoDirectory: URL

    private init() {
        // Create photos directory in Documents
        let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        photoDirectory = documentsDirectory.appendingPathComponent("AngelaPhotos", isDirectory: true)

        // Create directory if not exists
        try? FileManager.default.createDirectory(at: photoDirectory, withIntermediateDirectories: true)

        print("📸 Photo directory: \(photoDirectory.path)")
    }

    // MARK: - Save Photo

    func savePhoto(_ image: UIImage) -> String? {
        // Generate unique filename with UUID to prevent collisions
        let timestamp = ISO8601DateFormatter().string(from: Date())
            .replacingOccurrences(of: ":", with: "-")
        let uniqueID = UUID().uuidString.prefix(8)  // First 8 chars of UUID
        let filename = "photo_\(timestamp)_\(uniqueID).jpg"
        let fileURL = photoDirectory.appendingPathComponent(filename)

        // Convert to JPEG data
        guard let data = image.jpegData(compressionQuality: 0.8) else {
            print("❌ Failed to convert image to JPEG")
            return nil
        }

        // Write to disk
        do {
            try data.write(to: fileURL)
            print("✅ Photo saved: \(filename)")
            return filename
        } catch {
            print("❌ Failed to save photo: \(error)")
            return nil
        }
    }

    // MARK: - Load Photo

    func loadPhoto(_ filename: String) -> UIImage? {
        let fileURL = photoDirectory.appendingPathComponent(filename)

        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            print("❌ Photo not found: \(filename)")
            return nil
        }

        return UIImage(contentsOfFile: fileURL.path)
    }

    // MARK: - Delete Photo

    func deletePhoto(_ filename: String) {
        let fileURL = photoDirectory.appendingPathComponent(filename)

        do {
            try FileManager.default.removeItem(at: fileURL)
            print("✅ Photo deleted: \(filename)")
        } catch {
            print("❌ Failed to delete photo: \(error)")
        }
    }

    // MARK: - Extract EXIF GPS

    func extractGPS(from image: UIImage) -> CLLocation? {
        // Convert UIImage to Data
        guard let data = image.jpegData(compressionQuality: 1.0) else {
            return nil
        }

        // Create image source from data
        guard let source = CGImageSourceCreateWithData(data as CFData, nil) else {
            return nil
        }

        // Get image properties
        guard let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [String: Any] else {
            return nil
        }

        // Extract GPS dictionary
        guard let gpsInfo = properties[kCGImagePropertyGPSDictionary as String] as? [String: Any] else {
            print("ℹ️ No GPS data in image EXIF")
            return nil
        }

        // Extract latitude
        guard let latitudeRef = gpsInfo[kCGImagePropertyGPSLatitudeRef as String] as? String,
              let latitude = gpsInfo[kCGImagePropertyGPSLatitude as String] as? Double else {
            return nil
        }

        // Extract longitude
        guard let longitudeRef = gpsInfo[kCGImagePropertyGPSLongitudeRef as String] as? String,
              let longitude = gpsInfo[kCGImagePropertyGPSLongitude as String] as? Double else {
            return nil
        }

        // Convert to signed coordinates
        let lat = (latitudeRef == "N") ? latitude : -latitude
        let lon = (longitudeRef == "E") ? longitude : -longitude

        print("📍 Extracted GPS from EXIF: \(lat), \(lon)")

        return CLLocation(latitude: lat, longitude: lon)
    }

    // MARK: - Photo URLs

    func getPhotoURL(_ filename: String) -> URL {
        return photoDirectory.appendingPathComponent(filename)
    }

    func getAllPhotos() -> [String] {
        do {
            let files = try FileManager.default.contentsOfDirectory(atPath: photoDirectory.path)
            return files.filter { $0.hasSuffix(".jpg") }
        } catch {
            print("❌ Failed to list photos: \(error)")
            return []
        }
    }
}
