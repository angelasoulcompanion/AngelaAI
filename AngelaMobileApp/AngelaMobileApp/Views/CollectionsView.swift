//
//  CollectionsView.swift
//  Angela Mobile App
//
//  Feature 12: Collections - Album-like grouping of experiences
//

import SwiftUI

struct CollectionsView: View {
    @EnvironmentObject var database: DatabaseService
    @State private var showingCreateCollection = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack {
                    Text("📚 คอลเลกชัน")
                        .font(.title)
                        .fontWeight(.bold)
                    Spacer()
                    Button(action: { showingCreateCollection = true }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                            .foregroundColor(.angelaPurple)
                    }
                }
                .padding(.horizontal)

                // Quick collections
                VStack(alignment: .leading, spacing: 12) {
                    Text("เร็ว")
                        .font(.headline)
                        .padding(.horizontal)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 16) {
                            QuickCollectionCard(
                                title: "โปรด",
                                icon: "heart.fill",
                                color: .red,
                                count: favoriteExperiences.count
                            )

                            QuickCollectionCard(
                                title: "เดือนนี้",
                                icon: "calendar",
                                color: .blue,
                                count: thisMonthExperiences.count
                            )

                            QuickCollectionCard(
                                title: "ปีนี้",
                                icon: "calendar.badge.clock",
                                color: .green,
                                count: thisYearExperiences.count
                            )

                            QuickCollectionCard(
                                title: "มีวิดีโอ",
                                icon: "video.fill",
                                color: .purple,
                                count: videosExperiences.count
                            )

                            QuickCollectionCard(
                                title: "มีเสียง",
                                icon: "mic.fill",
                                color: .orange,
                                count: voiceExperiences.count
                            )
                        }
                        .padding(.horizontal)
                    }
                }

                // Collections by place
                VStack(alignment: .leading, spacing: 12) {
                    Text("📍 ตามสถานที่")
                        .font(.headline)
                        .padding(.horizontal)

                    if placeCollections.isEmpty {
                        Text("ยังไม่มีสถานที่")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .padding()
                    } else {
                        ForEach(placeCollections, id: \.name) { collection in
                            NavigationLink(destination: PlaceCollectionDetailView(
                                placeName: collection.name,
                                experiences: collection.experiences
                            )) {
                                PlaceCollectionCard(collection: collection)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                }

                // Collections by tag
                VStack(alignment: .leading, spacing: 12) {
                    Text("🏷️ ตามแท็ก")
                        .font(.headline)
                        .padding(.horizontal)

                    if tagCollections.isEmpty {
                        Text("ยังไม่มีแท็ก")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .padding()
                    } else {
                        ForEach(tagCollections, id: \.tag.id) { collection in
                            TagCollectionCard(collection: collection)
                        }
                    }
                }
            }
            .padding(.vertical)
        }
        .navigationTitle("คอลเลกชัน")
    }

    // MARK: - Quick Collections

    var favoriteExperiences: [Experience] {
        database.experiences.filter { $0.isFavorite }
    }

    var thisMonthExperiences: [Experience] {
        let calendar = Calendar.current
        let now = Date()
        return database.experiences.filter { experience in
            calendar.isDate(experience.experiencedAt, equalTo: now, toGranularity: .month)
        }
    }

    var thisYearExperiences: [Experience] {
        let calendar = Calendar.current
        let now = Date()
        return database.experiences.filter { experience in
            calendar.component(.year, from: experience.experiencedAt) == calendar.component(.year, from: now)
        }
    }

    var videosExperiences: [Experience] {
        database.experiences.filter { !$0.videos.isEmpty }
    }

    var voiceExperiences: [Experience] {
        database.experiences.filter { !$0.voiceNotes.isEmpty }
    }

    // MARK: - Place Collections

    struct PlaceCollection {
        let name: String
        let experiences: [Experience]
        var coverPhoto: String? {
            experiences.first?.photos.first
        }
    }

    var placeCollections: [PlaceCollection] {
        let grouped = Dictionary(grouping: database.experiences.filter { $0.placeName != nil }) {
            $0.placeName!
        }
        return grouped.map { PlaceCollection(name: $0.key, experiences: $0.value) }
            .sorted { $0.experiences.count > $1.experiences.count }
    }

    // MARK: - Tag Collections

    struct TagCollection {
        let tag: Tag
        let experienceCount: Int
    }

    var tagCollections: [TagCollection] {
        // This would need TagService integration
        // For now, return empty
        []
    }
}

// MARK: - Supporting Views

struct QuickCollectionCard: View {
    let title: String
    let icon: String
    let color: Color
    let count: Int

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.2))
                    .frame(width: 60, height: 60)
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
            }

            Text(title)
                .font(.caption)
                .fontWeight(.semibold)

            Text("\(count)")
                .font(.caption2)
                .foregroundColor(.gray)
        }
        .frame(width: 90)
    }
}

struct PlaceCollectionCard: View {
    let collection: CollectionsView.PlaceCollection

    var body: some View {
        HStack(spacing: 12) {
            // Cover photo
            if let coverPhoto = collection.coverPhoto,
               let image = PhotoManager.shared.loadPhoto(coverPhoto) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 80, height: 80)
                    .clipped()
                    .cornerRadius(12)
            } else {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.angelaPurpleLight.opacity(0.3))
                    .frame(width: 80, height: 80)
                    .overlay(
                        Image(systemName: "photo.stack")
                            .font(.title2)
                            .foregroundColor(.gray)
                    )
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(collection.name)
                    .font(.headline)
                    .foregroundColor(.primary)

                Text("\(collection.experiences.count) ความทรงจำ")
                    .font(.caption)
                    .foregroundColor(.gray)

                // Show first few photos
                HStack(spacing: 4) {
                    ForEach(collection.experiences.prefix(4)) { experience in
                        if let firstPhoto = experience.photos.first,
                           let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                            Image(uiImage: image)
                                .resizable()
                                .scaledToFill()
                                .frame(width: 30, height: 30)
                                .clipped()
                                .cornerRadius(4)
                        }
                    }
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .foregroundColor(.gray.opacity(0.5))
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(radius: 2)
        .padding(.horizontal)
    }
}

struct TagCollectionCard: View {
    let collection: CollectionsView.TagCollection

    var body: some View {
        HStack {
            Text(collection.tag.name)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(collection.tag.swiftUIColor)
                .cornerRadius(16)

            Spacer()

            Text("\(collection.experienceCount) ความทรงจำ")
                .font(.caption)
                .foregroundColor(.gray)

            Image(systemName: "chevron.right")
                .foregroundColor(.gray.opacity(0.5))
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(radius: 1)
        .padding(.horizontal)
    }
}

// Detail view for place collection
struct PlaceCollectionDetailView: View {
    let placeName: String
    let experiences: [Experience]

    var body: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                ForEach(experiences) { experience in
                    NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                        VStack(alignment: .leading, spacing: 4) {
                            if let firstPhoto = experience.photos.first,
                               let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                                Image(uiImage: image)
                                    .resizable()
                                    .scaledToFill()
                                    .frame(height: 150)
                                    .clipped()
                                    .cornerRadius(8)
                            }

                            Text(experience.title)
                                .font(.caption)
                                .fontWeight(.semibold)
                                .foregroundColor(.primary)
                                .lineLimit(1)
                        }
                    }
                }
            }
            .padding()
        }
        .navigationTitle(placeName)
    }
}

#Preview {
    CollectionsView()
        .environmentObject(DatabaseService.shared)
}
