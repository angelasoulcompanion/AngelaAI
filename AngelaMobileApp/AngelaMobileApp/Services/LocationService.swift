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
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.distanceFilter = 10 // Update every 10 meters
    }

    // MARK: - Request Authorization

    func requestPermission() {
        locationManager.requestWhenInUseAuthorization()
    }

    // MARK: - Start/Stop Location Updates

    func startTracking() {
        guard locationStatus == .authorizedWhenInUse || locationStatus == .authorizedAlways else {
            print("⚠️ Location permission not granted")
            requestPermission()
            return
        }

        locationManager.startUpdatingLocation()
        print("📍 Started location tracking")
    }

    func stopTracking() {
        locationManager.stopUpdatingLocation()
        print("📍 Stopped location tracking")
    }

    // MARK: - Get Current Location

    func getCurrentLocation() async -> CLLocation? {
        // If we already have a recent location, return it
        if let location = currentLocation,
           location.timestamp.timeIntervalSinceNow > -60 { // Less than 1 minute old
            return location
        }

        // Otherwise, request a new location
        startTracking()

        // Wait for location update (max 5 seconds)
        for _ in 0..<50 {
            if let location = currentLocation {
                return location
            }
            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 second
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
        // Use MKLocalSearch to find nearby landmarks/areas
        let request = MKLocalSearch.Request()
        request.resultTypes = .pointOfInterest
        request.region = MKCoordinateRegion(
            center: location.coordinate,
            latitudinalMeters: 500,
            longitudinalMeters: 500
        )

        let search = MKLocalSearch(request: request)

        do {
            let response = try await search.start()

            // Get area name from first nearby point of interest
            if let firstItem = response.mapItems.first {
                // Try to extract area/locality from the name or use the name itself
                if let name = firstItem.name {
                    // Extract area part if available (e.g., "Cafe in Thonglor" -> "Thonglor")
                    let components = name.components(separatedBy: " in ")
                    if components.count > 1 {
                        return components[1]
                    }
                    return name
                }
            }

            return nil

        } catch {
            print("❌ Failed to get area: \(error)")
            return nil
        }
    }

    // MARK: - Formatted Location String

    func formatLocation(_ location: CLLocation) -> String {
        let latitude = String(format: "%.6f", location.coordinate.latitude)
        let longitude = String(format: "%.6f", location.coordinate.longitude)
        return "\(latitude), \(longitude)"
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

        DispatchQueue.main.async {
            self.currentLocation = location
            print("📍 Location updated: \(self.formatLocation(location))")
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("❌ Location manager failed: \(error.localizedDescription)")
    }
}
