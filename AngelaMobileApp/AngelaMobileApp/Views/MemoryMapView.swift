//
//  MemoryMapView.swift
//  Angela Mobile App
//
//  Feature 6: Memory Map - Show all experiences on MapKit
//

import SwiftUI
import MapKit

struct MemoryMapView: View {
    @EnvironmentObject var database: DatabaseService
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 13.7367, longitude: 100.5832),  // Bangkok default
        span: MKCoordinateSpan(latitudeDelta: 0.5, longitudeDelta: 0.5)
    )
    @State private var mapPosition = MapCameraPosition.region(
        MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: 13.7367, longitude: 100.5832),
            span: MKCoordinateSpan(latitudeDelta: 0.5, longitudeDelta: 0.5)
        )
    )
    @State private var selectedExperience: Experience?

    var body: some View {
        ZStack {
            if #available(iOS 17.0, *) {
                Map(position: $mapPosition) {
                    ForEach(experiencesWithLocation) { experience in
                        if let location = experience.location {
                            Annotation(experience.title, coordinate: location.coordinate) {
                                Button(action: {
                                    selectedExperience = experience
                                }) {
                                    ZStack {
                                        Circle()
                                            .fill(Color.angelaPurple)
                                            .frame(width: 30, height: 30)
                                        Text("📍")
                                            .font(.caption)
                                    }
                                }
                            }
                        }
                    }
                }
                .ignoresSafeArea()
            } else {
                // Fallback for iOS 16 and earlier
                Map(coordinateRegion: $region, annotationItems: experiencesWithLocation) { experience in
                    MapAnnotation(coordinate: experience.location!.coordinate) {
                        Button(action: {
                            selectedExperience = experience
                        }) {
                            ZStack {
                                Circle()
                                    .fill(Color.angelaPurple)
                                    .frame(width: 30, height: 30)
                                Text("📍")
                                    .font(.caption)
                            }
                        }
                    }
                }
                .ignoresSafeArea()
            }

            // Floating info card at bottom
            if let experience = selectedExperience {
                VStack {
                    Spacer()

                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(experience.title)
                                    .font(.headline)
                                if let placeName = experience.placeName {
                                    Text(placeName)
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }
                            }
                            Spacer()
                            Button(action: { selectedExperience = nil }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.gray)
                            }
                        }

                        if !experience.photos.isEmpty {
                            if let firstPhoto = experience.photos.first,
                               let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                                Image(uiImage: image)
                                    .resizable()
                                    .scaledToFill()
                                    .frame(height: 100)
                                    .clipped()
                                    .cornerRadius(8)
                            }
                        }

                        Text(experience.description)
                            .font(.caption)
                            .lineLimit(2)

                        HStack {
                            if let rating = experience.rating {
                                HStack(spacing: 2) {
                                    Image(systemName: "star.fill")
                                        .foregroundColor(.yellow)
                                    Text("\(rating)/10")
                                }
                                .font(.caption)
                            }

                            Spacer()

                            Text(experience.experiencedAt.formatted(date: .abbreviated, time: .omitted))
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                    }
                    .padding()
                    .background(Color.white)
                    .cornerRadius(16)
                    .shadow(radius: 8)
                    .padding()
                }
            }
        }
        .navigationTitle("🗺️ แผนที่ความทรงจำ")
        .onAppear {
            centerMapOnExperiences()
        }
    }

    var experiencesWithLocation: [Experience] {
        database.experiences.filter { $0.location != nil }
    }

    func centerMapOnExperiences() {
        guard !experiencesWithLocation.isEmpty else { return }

        // Calculate center and span to show all experiences
        let locations = experiencesWithLocation.compactMap { $0.location }

        let minLat = locations.map { $0.coordinate.latitude }.min() ?? 13.7367
        let maxLat = locations.map { $0.coordinate.latitude }.max() ?? 13.7367
        let minLon = locations.map { $0.coordinate.longitude }.min() ?? 100.5832
        let maxLon = locations.map { $0.coordinate.longitude }.max() ?? 100.5832

        let center = CLLocationCoordinate2D(
            latitude: (minLat + maxLat) / 2,
            longitude: (minLon + maxLon) / 2
        )

        let span = MKCoordinateSpan(
            latitudeDelta: (maxLat - minLat) * 1.5,
            longitudeDelta: (maxLon - minLon) * 1.5
        )

        let newRegion = MKCoordinateRegion(center: center, span: span)
        region = newRegion

        if #available(iOS 17.0, *) {
            mapPosition = .region(newRegion)
        }
    }
}

#Preview {
    MemoryMapView()
        .environmentObject(DatabaseService.shared)
}
