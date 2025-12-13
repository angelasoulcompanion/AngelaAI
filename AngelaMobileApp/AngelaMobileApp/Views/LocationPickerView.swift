//
//  LocationPickerView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-16.
//  Map-based location picker for manual location selection
//

import SwiftUI
import MapKit

struct LocationPickerView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var locationService = LocationService.shared

    @Binding var selectedLocation: CLLocation?
    @Binding var placeName: String?
    @Binding var areaName: String?

    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 13.7563, longitude: 100.5018), // Bangkok default
        span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
    )

    @State private var selectedCoordinate: CLLocationCoordinate2D?
    @State private var isLoadingPlaceName = false
    @State private var tempPlaceName: String?
    @State private var tempAreaName: String?

    var body: some View {
        NavigationView {
            ZStack {
                // Map View (iOS 17+ compatible)
                InteractiveMapView(
                    selectedCoordinate: $selectedCoordinate,
                    region: $region,
                    onTap: { coordinate in
                        handleTapOnMap(coordinate: coordinate)
                    }
                )
                .ignoresSafeArea()

                // Center Pin (when no location selected)
                if selectedCoordinate == nil {
                    Image(systemName: "mappin.circle.fill")
                        .font(.system(size: 50))
                        .foregroundColor(.angelaPurple)
                        .shadow(radius: 5)
                }

                // Bottom Card with Location Info
                VStack {
                    Spacer()

                    VStack(spacing: 12) {
                        // Drag Handle
                        RoundedRectangle(cornerRadius: 3)
                            .fill(Color.gray.opacity(0.4))
                            .frame(width: 40, height: 5)
                            .padding(.top, 8)

                        if isLoadingPlaceName {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.9)
                                Text("กำลังโหลดข้อมูลตำแหน่ง...")
                                    .font(.subheadline)
                                    .foregroundColor(.gray)
                            }
                            .padding()
                        } else if let coordinate = selectedCoordinate {
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Image(systemName: "mappin.circle.fill")
                                        .foregroundColor(.angelaPurple)
                                    Text("ตำแหน่งที่เลือก")
                                        .font(.headline)
                                }

                                if let place = tempPlaceName {
                                    Text(place)
                                        .font(.subheadline)
                                        .foregroundColor(.primary)
                                }

                                if let area = tempAreaName {
                                    Text(area)
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }

                                Text(String(format: "%.6f, %.6f", coordinate.latitude, coordinate.longitude))
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding()
                        } else {
                            VStack(spacing: 8) {
                                Image(systemName: "hand.tap.fill")
                                    .font(.system(size: 30))
                                    .foregroundColor(.angelaPurple.opacity(0.6))
                                Text("แตะบน map เพื่อเลือกตำแหน่ง")
                                    .font(.subheadline)
                                    .foregroundColor(.gray)

                                Button(action: {
                                    useCurrentLocation()
                                }) {
                                    HStack {
                                        Image(systemName: "location.fill")
                                        Text("ใช้ตำแหน่งปัจจุบัน")
                                    }
                                    .font(.subheadline)
                                    .foregroundColor(.angelaPurple)
                                }
                                .padding(.top, 4)
                            }
                            .padding()
                        }

                        // Action Buttons
                        HStack(spacing: 12) {
                            Button(action: {
                                dismiss()
                            }) {
                                Text("ยกเลิก")
                                    .font(.headline)
                                    .foregroundColor(.red)
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(Color.red.opacity(0.1))
                                    .cornerRadius(12)
                            }

                            Button(action: {
                                confirmSelection()
                            }) {
                                Text("ยืนยันตำแหน่ง")
                                    .font(.headline)
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(selectedCoordinate != nil ? Color.angelaPurple : Color.gray)
                                    .cornerRadius(12)
                            }
                            .disabled(selectedCoordinate == nil)
                        }
                        .padding(.horizontal)
                        .padding(.bottom, 8)
                    }
                    .background(
                        RoundedRectangle(cornerRadius: 20)
                            .fill(Color(.systemBackground))
                            .shadow(radius: 10)
                    )
                    .padding(.horizontal)
                    .padding(.bottom)
                }

                // Current Location Button
                VStack {
                    HStack {
                        Spacer()
                        Button(action: {
                            useCurrentLocation()
                        }) {
                            Image(systemName: "location.fill")
                                .font(.system(size: 20))
                                .foregroundColor(.white)
                                .padding(12)
                                .background(Circle().fill(Color.angelaPurple))
                                .shadow(radius: 5)
                        }
                        .padding()
                    }
                    Spacer()
                }
            }
            .navigationTitle("เลือกตำแหน่ง")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("เสร็จ") {
                        confirmSelection()
                    }
                    .disabled(selectedCoordinate == nil)
                }
            }
        }
        .onAppear {
            // Center on current location if available
            if let location = selectedLocation {
                region.center = location.coordinate
                selectedCoordinate = location.coordinate
                tempPlaceName = placeName
                tempAreaName = areaName
            } else {
                useCurrentLocation()
            }
        }
    }

    // MARK: - Map Tap Handler

    private func handleTapOnMap(coordinate: CLLocationCoordinate2D) {
        print("🗺️ Map tapped at: \(coordinate.latitude), \(coordinate.longitude)")
        selectedCoordinate = coordinate

        // Also update region to center on selected location
        region.center = coordinate

        // Reverse geocode the selected coordinate
        Task {
            await reverseGeocode(coordinate: coordinate)
        }
    }

    // MARK: - Use Current Location

    private func useCurrentLocation() {
        Task {
            // Request permission if needed
            if locationService.locationStatus == .notDetermined {
                locationService.requestPermission()
                try? await Task.sleep(nanoseconds: 1_000_000_000) // Wait 1 second
            }

            // Get current location
            if let location = await locationService.getCurrentLocation() {
                await MainActor.run {
                    region.center = location.coordinate
                    selectedCoordinate = location.coordinate
                }

                // Reverse geocode
                await reverseGeocode(coordinate: location.coordinate)
            }
        }
    }

    // MARK: - Reverse Geocode

    private func reverseGeocode(coordinate: CLLocationCoordinate2D) async {
        print("🔄 Starting reverse geocode for: \(coordinate.latitude), \(coordinate.longitude)")

        await MainActor.run {
            isLoadingPlaceName = true
        }

        let location = CLLocation(latitude: coordinate.latitude, longitude: coordinate.longitude)

        // Get place name
        if let place = await locationService.getPlaceName(from: location) {
            print("📍 Got place name: \(place)")
            await MainActor.run {
                tempPlaceName = place
            }
        } else {
            print("⚠️ No place name found")
        }

        // Get area name
        if let area = await locationService.getArea(from: location) {
            print("📍 Got area name: \(area)")
            await MainActor.run {
                tempAreaName = area
            }
        } else {
            print("⚠️ No area name found")
        }

        await MainActor.run {
            isLoadingPlaceName = false
        }

        print("✅ Reverse geocode complete")
    }

    // MARK: - Confirm Selection

    private func confirmSelection() {
        guard let coordinate = selectedCoordinate else {
            print("❌ No coordinate selected")
            return
        }

        print("✅ Confirming selection:")
        print("   Coordinate: \(coordinate.latitude), \(coordinate.longitude)")
        print("   Place: \(tempPlaceName ?? "nil")")
        print("   Area: \(tempAreaName ?? "nil")")

        // Update binding values
        selectedLocation = CLLocation(latitude: coordinate.latitude, longitude: coordinate.longitude)
        placeName = tempPlaceName
        areaName = tempAreaName

        print("✅ Bindings updated, dismissing...")
        dismiss()
    }
}

// MARK: - Interactive Map (Better Tap Detection)

struct InteractiveMapView: UIViewRepresentable {
    @Binding var selectedCoordinate: CLLocationCoordinate2D?
    @Binding var region: MKCoordinateRegion
    var onTap: (CLLocationCoordinate2D) -> Void

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.delegate = context.coordinator
        mapView.setRegion(region, animated: false)

        // Add tap gesture
        let tapGesture = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.handleTap(_:)))
        mapView.addGestureRecognizer(tapGesture)

        return mapView
    }

    func updateUIView(_ mapView: MKMapView, context: Context) {
        // Update region
        if mapView.region.center.latitude != region.center.latitude ||
           mapView.region.center.longitude != region.center.longitude {
            mapView.setRegion(region, animated: true)
        }

        // Update annotation
        mapView.removeAnnotations(mapView.annotations)

        if let coordinate = selectedCoordinate {
            let annotation = MKPointAnnotation()
            annotation.coordinate = coordinate
            mapView.addAnnotation(annotation)
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    class Coordinator: NSObject, MKMapViewDelegate {
        let parent: InteractiveMapView

        init(parent: InteractiveMapView) {
            self.parent = parent
        }

        @objc func handleTap(_ gesture: UITapGestureRecognizer) {
            guard let mapView = gesture.view as? MKMapView else {
                print("❌ Cannot get mapView from gesture")
                return
            }

            let location = gesture.location(in: mapView)
            let coordinate = mapView.convert(location, toCoordinateFrom: mapView)

            print("👆 Tap gesture detected at screen point: \(location)")
            print("📍 Converted to coordinate: \(coordinate.latitude), \(coordinate.longitude)")

            DispatchQueue.main.async {
                self.parent.selectedCoordinate = coordinate
                self.parent.onTap(coordinate)
                print("✅ Coordinate set and onTap called")
            }
        }

        func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
            let identifier = "SelectedLocation"

            var annotationView = mapView.dequeueReusableAnnotationView(withIdentifier: identifier)

            if annotationView == nil {
                annotationView = MKMarkerAnnotationView(annotation: annotation, reuseIdentifier: identifier)
                annotationView?.canShowCallout = false
            } else {
                annotationView?.annotation = annotation
            }

            if let markerView = annotationView as? MKMarkerAnnotationView {
                markerView.markerTintColor = UIColor(named: "AngelaPurple") ?? .purple
            }

            return annotationView
        }

        func mapView(_ mapView: MKMapView, regionDidChangeAnimated animated: Bool) {
            DispatchQueue.main.async {
                self.parent.region = mapView.region
            }
        }
    }
}

#Preview {
    @Previewable @State var location: CLLocation? = nil
    @Previewable @State var placeName: String? = nil
    @Previewable @State var areaName: String? = nil

    LocationPickerView(
        selectedLocation: $location,
        placeName: $placeName,
        areaName: $areaName
    )
}
