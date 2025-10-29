//
//  LocationService.swift
//  AngelaNova
//
//  📍 Location Service - Read GPS location from macOS using CoreLocation
//

import Foundation
import Combine
import CoreLocation
import MapKit
import Contacts

class LocationService: NSObject, ObservableObject {
    @Published var currentLocation: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined
    @Published var locationError: String?

    private let locationManager = CLLocationManager()

    @Published var city: String = "Unknown"
    @Published var region: String = "Unknown"
    @Published var country: String = "Unknown"
    @Published var postalCode: String = ""

    override init() {
        super.init()
        setupLocationManager()
    }

    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBest
        locationManager.distanceFilter = 100 // Update every 100 meters
    }

    /// Request location permission (macOS doesn't require explicit permission request)
    func requestPermission() {
        // On macOS, location permission is handled automatically via entitlements
        // Just start updating location
        locationManager.startUpdatingLocation()
    }

    /// Start updating location
    func startUpdating() {
        // On macOS, we can start updating immediately if authorized
        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorized {
            locationManager.startUpdatingLocation()
        } else if authorizationStatus == .notDetermined {
            // Start updating to trigger permission prompt
            locationManager.startUpdatingLocation()
        }
    }

    /// Stop updating location
    func stopUpdating() {
        locationManager.stopUpdatingLocation()
    }

    /// Get current location info as dictionary
    func getCurrentLocationInfo() -> [String: Any] {
        guard let location = currentLocation else {
            return [
                "latitude": 0.0,
                "longitude": 0.0,
                "city": "Unknown",
                "region": "Unknown",
                "country": "Unknown",
                "location_string": "Location unavailable",
                "location_string_th": "ไม่สามารถระบุตำแหน่งได้",
                "postal": "",
                "authorized": false
            ]
        }

        return [
            "latitude": location.coordinate.latitude,
            "longitude": location.coordinate.longitude,
            "city": city,
            "region": region,
            "country": country,
            "location_string": "\(city), \(region), \(country)",
            "location_string_th": "\(city), \(region), \(country)",
            "postal": postalCode,
            "altitude": location.altitude,
            "accuracy": location.horizontalAccuracy,
            "authorized": true
        ]
    }

    /// Reverse geocode location to get address using MapKit
    /// Using MKMapItem properties (modern API without deprecated methods)
    private func reverseGeocodeLocation(_ location: CLLocation) {
        Task { @MainActor in
            do {
                let request = MKLocalSearch.Request()
                request.naturalLanguageQuery = "Current Location"
                request.region = MKCoordinateRegion(
                    center: location.coordinate,
                    span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
                )

                let search = MKLocalSearch(request: request)
                let response = try await search.start()

                if let mapItem = response.mapItems.first {
                    // Use MKMapItem properties directly (non-deprecated)
                    self.city = mapItem.name ?? "Unknown"

                    // For region/state and country, we need to parse from timeZone or use MKLocalSearch
                    // This is a workaround since Apple deprecated addressDictionary without clear replacement
                    if let timeZone = mapItem.timeZone?.identifier {
                        let components = timeZone.split(separator: "/")
                        if components.count > 1 {
                            self.region = String(components[1])
                            self.country = String(components[0])
                        } else {
                            self.region = "Unknown"
                            self.country = timeZone
                        }
                    } else {
                        self.region = "Unknown"
                        self.country = "Unknown"
                    }

                    // PostalCode not available in modern API, set to empty
                    self.postalCode = ""
                }
            } catch {
                self.locationError = error.localizedDescription
            }
        }
    }
}

// MARK: - CLLocationManagerDelegate
extension LocationService: CLLocationManagerDelegate {
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus

        switch authorizationStatus {
        case .authorizedAlways, .authorized:
            // macOS uses .authorized instead of .authorizedWhenInUse
            locationManager.startUpdatingLocation()
        case .denied, .restricted:
            locationError = "Location access denied"
            stopUpdating()
        case .notDetermined:
            // Start updating to trigger permission prompt
            locationManager.startUpdatingLocation()
        @unknown default:
            break
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }

        currentLocation = location
        locationError = nil

        // Reverse geocode to get address
        reverseGeocodeLocation(location)
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        locationError = error.localizedDescription
    }
}
