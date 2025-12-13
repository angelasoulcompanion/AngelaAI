//
//  LocationService.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  GPS location tracking service
//

import Foundation
import CoreLocation
import MapKit
import Combine

class LocationService: NSObject, ObservableObject {
    static let shared = LocationService()

    @Published var currentLocation: CLLocation?
    @Published var locationStatus: CLAuthorizationStatus = .notDetermined
    @Published var currentPlacemark: CLPlacemark?

    private let locationManager = CLLocationManager()

    override init() {
        super.init()
        locationManager.delegate = self

        // IMPORTANT: Maximum accuracy settings for precise GPS
        locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation // Highest accuracy
        locationManager.distanceFilter = kCLDistanceFilterNone // Get all location updates
        locationManager.activityType = .fitness // Optimize for walking/stationary

        // Request full accuracy (iOS 14+)
        if #available(iOS 14.0, *) {
            locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        }

        // Allow background location updates if needed
        locationManager.allowsBackgroundLocationUpdates = false
        locationManager.pausesLocationUpdatesAutomatically = false
        locationManager.showsBackgroundLocationIndicator = false
    }

    // MARK: - Request Authorization

    func requestPermission() {
        locationManager.requestWhenInUseAuthorization()
    }

    // MARK: - Start/Stop Location Updates

    func startTracking() {
        guard locationStatus == .authorizedWhenInUse || locationStatus == .authorizedAlways else {
            print("⚠️ Location permission not granted (status: \(locationStatus.rawValue))")
            requestPermission()
            return
        }

        locationManager.startUpdatingLocation()
        print("📍 Started location tracking with permission")
    }

    func stopTracking() {
        locationManager.stopUpdatingLocation()
        print("📍 Stopped location tracking")
    }

    // MARK: - Get Current Location

    func getCurrentLocation() async -> CLLocation? {
        // If we already have a recent AND accurate location, return it
        if let location = currentLocation,
           location.timestamp.timeIntervalSinceNow > -30, // Less than 30 seconds old
           location.horizontalAccuracy >= 0,
           location.horizontalAccuracy < 20 { // Accuracy better than 20 meters
            print("📍 Using cached accurate location (accuracy: \(location.horizontalAccuracy)m)")
            return location
        }

        // Otherwise, request a new accurate location
        print("📍 Starting one-time location fetch...")
        startTracking()

        // Wait for accurate location update (max 15 seconds)
        for i in 0..<150 {
            if let location = currentLocation,
               location.horizontalAccuracy >= 0,
               location.horizontalAccuracy < 20 { // Wait for accuracy better than 20 meters
                print("📍 Got accurate location after \(Double(i) * 0.1)s (accuracy: \(location.horizontalAccuracy)m)")
                stopTracking()  // ✅ STOP tracking after getting location!
                return location
            }

            // After 5 seconds, accept lower accuracy if available
            if i >= 50,
               let location = currentLocation,
               location.horizontalAccuracy >= 0,
               location.horizontalAccuracy < 50 { // Accept 50m accuracy after 5 seconds
                print("⚠️ Using moderate accuracy location after 5s (accuracy: \(location.horizontalAccuracy)m)")
                stopTracking()  // ✅ STOP tracking after getting location!
                return location
            }

            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 second
        }

        // Last resort: return whatever we have
        stopTracking()  // ✅ STOP tracking even on timeout!
        if let location = currentLocation {
            print("⚠️ Timeout: returning location with accuracy \(location.horizontalAccuracy)m")
        }
        return currentLocation
    }

    // MARK: - Reverse Geocoding with MapKit

    func getPlaceName(from location: CLLocation) async -> String? {
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = "place"
        request.region = MKCoordinateRegion(
            center: location.coordinate,
            latitudinalMeters: 100,
            longitudinalMeters: 100
        )

        let search = MKLocalSearch(request: request)

        do {
            let response = try await search.start()

            if let firstItem = response.mapItems.first {
                // Use name from mapItem
                return firstItem.name
            }

            return nil

        } catch {
            print("❌ Reverse geocoding failed: \(error)")
            return nil
        }
    }

    func getArea(from location: CLLocation) async -> String? {
        // Note: CLGeocoder is deprecated in iOS 26.0 (not released yet as of 2025)
        // TODO: Migrate to MKReverseGeocodingRequest when iOS 26.0 is released
        // Suppressing warning since iOS 26.0 doesn't exist yet
        if #available(iOS 26.0, *) {
            // TODO: Use MKReverseGeocodingRequest here when iOS 26 is released
            return nil
        } else {
            let geocoder = CLGeocoder()

            do {
                let placemarks = try await geocoder.reverseGeocodeLocation(location)

            if let placemark = placemarks.first {
                // Build area name from available components
                var areaComponents: [String] = []

                // Priority: subLocality (ย่าน) > locality (เมือง) > administrativeArea (จังหวัด)
                if let subLocality = placemark.subLocality {
                    areaComponents.append(subLocality)
                }

                if let locality = placemark.locality {
                    // Only add locality if different from subLocality
                    if !areaComponents.contains(locality) {
                        areaComponents.append(locality)
                    }
                }

                if let administrativeArea = placemark.administrativeArea {
                    // Only add if not already in components
                    if !areaComponents.contains(administrativeArea) {
                        areaComponents.append(administrativeArea)
                    }
                }

                // Join components with ", "
                let areaString = areaComponents.joined(separator: ", ")

                if !areaString.isEmpty {
                    print("📍 Got area from geocoder: \(areaString)")
                    return areaString
                }
            }

                print("⚠️ No area information available from geocoder")
                return nil

            } catch {
                print("❌ Geocoding failed: \(error.localizedDescription)")
                return nil
            }
        }
    }

    // MARK: - Formatted Location String

    func formatLocation(_ location: CLLocation) -> String {
        let latitude = String(format: "%.6f", location.coordinate.latitude)
        let longitude = String(format: "%.6f", location.coordinate.longitude)
        return "\(latitude), \(longitude)"
    }

    // MARK: - Accuracy Helpers

    /// Get accuracy description for user display
    func getAccuracyDescription(_ location: CLLocation) -> String {
        let accuracy = location.horizontalAccuracy

        if accuracy < 0 {
            return "❌ Invalid"
        } else if accuracy < 5 {
            return "🎯 Excellent (<5m)"
        } else if accuracy < 10 {
            return "✅ Very Good (<10m)"
        } else if accuracy < 20 {
            return "✅ Good (<20m)"
        } else if accuracy < 50 {
            return "⚠️ Moderate (<50m)"
        } else if accuracy < 100 {
            return "⚠️ Fair (<100m)"
        } else {
            return "❌ Poor (>\(Int(accuracy))m)"
        }
    }

    /// Check if location is acceptable for saving
    func isLocationAcceptable(_ location: CLLocation) -> Bool {
        // Must be recent (within 30 seconds)
        guard location.timestamp.timeIntervalSinceNow > -30 else {
            return false
        }

        // Must have valid accuracy
        guard location.horizontalAccuracy >= 0 else {
            return false
        }

        // For saving experiences, require at least 50m accuracy
        return location.horizontalAccuracy < 50
    }
}

// MARK: - CLLocationManagerDelegate

extension LocationService: CLLocationManagerDelegate {
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        DispatchQueue.main.async {
            self.locationStatus = manager.authorizationStatus
            print("📍 Location authorization status: \(self.locationStatus.rawValue)")
        }

        // Auto-start tracking when authorized
        if manager.authorizationStatus == .authorizedWhenInUse ||
           manager.authorizationStatus == .authorizedAlways {
            startTracking()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }

        // Filter out invalid/inaccurate locations
        // 1. Check if location is recent (not cached from past)
        guard location.timestamp.timeIntervalSinceNow > -10 else {
            print("⚠️ Rejected old location (age: \(abs(location.timestamp.timeIntervalSinceNow))s)")
            return
        }

        // 2. Check horizontal accuracy (negative means invalid)
        guard location.horizontalAccuracy >= 0 else {
            print("⚠️ Rejected location with invalid accuracy")
            return
        }

        // 3. Only update if accuracy is improving or location changed significantly
        if let current = currentLocation {
            let distance = location.distance(from: current)

            // If new location is less accurate and very close, skip it
            if location.horizontalAccuracy > current.horizontalAccuracy,
               distance < 5 { // Less than 5 meters away
                print("⚠️ Rejected less accurate nearby location (accuracy: \(location.horizontalAccuracy)m vs \(current.horizontalAccuracy)m)")
                return
            }
        }

        DispatchQueue.main.async {
            self.currentLocation = location
            print("📍 Location updated: \(self.formatLocation(location)) (accuracy: \(location.horizontalAccuracy)m, altitude: \(location.altitude)m)")
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("❌ Location manager failed: \(error.localizedDescription)")
    }
}
