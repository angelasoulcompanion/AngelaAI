//
//  ExperienceDetailView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  Detailed view of a single experience with photos, GPS, and all metadata
//

import SwiftUI
import MapKit

struct ExperienceDetailView: View {
    let experience: Experience

    @State private var selectedPhotoIndex = 0
    @State private var region = MKCoordinateRegion()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Photo Gallery
                if !experience.photos.isEmpty {
                    TabView(selection: $selectedPhotoIndex) {
                        ForEach(experience.photos.indices, id: \.self) { index in
                            if let image = PhotoManager.shared.loadPhoto(experience.photos[index]) {
                                Image(uiImage: image)
                                    .resizable()
                                    .scaledToFill()
                                    .frame(height: 300)
                                    .clipped()
                                    .tag(index)
                            } else {
                                Rectangle()
                                    .fill(Color.gray.opacity(0.2))
                                    .frame(height: 300)
                                    .overlay(
                                        VStack {
                                            Image(systemName: "photo")
                                                .font(.system(size: 50))
                                                .foregroundColor(.gray)
                                            Text("ไม่สามารถโหลดรูปภาพได้")
                                                .font(.caption)
                                                .foregroundColor(.gray)
                                        }
                                    )
                                    .tag(index)
                            }
                        }
                    }
                    .frame(height: 300)
                    .tabViewStyle(.page)

                    // Photo counter
                    if experience.photos.count > 1 {
                        Text("\(selectedPhotoIndex + 1) / \(experience.photos.count)")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                }

                VStack(alignment: .leading, spacing: 16) {
                    // Title
                    Text(experience.title)
                        .font(.title)
                        .fontWeight(.bold)

                    // Ratings
                    HStack(spacing: 20) {
                        if let rating = experience.rating {
                            HStack {
                                Image(systemName: "star.fill")
                                    .foregroundColor(.yellow)
                                Text("\(rating)/10")
                                    .font(.headline)
                            }
                        }

                        if let intensity = experience.emotionalIntensity {
                            HStack {
                                Image(systemName: "heart.fill")
                                    .foregroundColor(.pink)
                                Text("\(intensity)/10")
                                    .font(.headline)
                            }
                        }

                        Spacer()

                        // Sync status
                        if !experience.synced {
                            HStack {
                                Image(systemName: "icloud.and.arrow.up")
                                    .foregroundColor(.orange)
                                Text("รอ sync")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        } else {
                            HStack {
                                Image(systemName: "checkmark.icloud.fill")
                                    .foregroundColor(.green)
                                Text("synced")
                                    .font(.caption)
                                    .foregroundColor(.green)
                            }
                        }
                    }

                    Divider()

                    // Description
                    VStack(alignment: .leading, spacing: 8) {
                        Text("รายละเอียด")
                            .font(.headline)
                        Text(experience.description)
                            .font(.body)
                    }

                    Divider()

                    // GPS Location
                    if let latitude = experience.latitude,
                       let longitude = experience.longitude {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("📍 ตำแหน่ง")
                                .font(.headline)

                            // Place name
                            if let placeName = experience.placeName {
                                Text(placeName)
                                    .font(.body)
                            }

                            // Area
                            if let area = experience.area {
                                Text(area)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }

                            // Coordinates
                            Text(String(format: "%.6f, %.6f", latitude, longitude))
                                .font(.caption)
                                .foregroundColor(.gray)

                            // Mini Map
                            Map {
                                Marker("", coordinate: CLLocationCoordinate2D(latitude: latitude, longitude: longitude))
                                    .tint(.red)
                            }
                            .mapStyle(.standard)
                            .frame(height: 200)
                            .cornerRadius(12)
                        }

                        Divider()
                    }

                    // Timestamp
                    VStack(alignment: .leading, spacing: 8) {
                        Text("🕐 เวลา")
                            .font(.headline)
                        Text(experience.experiencedAt, style: .date)
                            .font(.body)
                        Text(experience.experiencedAt, style: .time)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Divider()

                    // Created timestamp
                    Text("บันทึกเมื่อ: \(experience.createdAt, style: .relative)")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                .padding()
            }
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}

// Helper struct for map pins
struct MapPin: Identifiable {
    let id = UUID()
    let coordinate: CLLocationCoordinate2D
}

#Preview {
    NavigationView {
        ExperienceDetailView(experience: Experience(
            title: "Breakfast at Thonglor",
            description: "Had an amazing breakfast with Angela",
            photos: [],
            latitude: 13.7367,
            longitude: 100.5774,
            placeName: "Thonglor Cafe",
            area: "Thonglor, Bangkok",
            rating: 9,
            emotionalIntensity: 8
        ))
    }
}
