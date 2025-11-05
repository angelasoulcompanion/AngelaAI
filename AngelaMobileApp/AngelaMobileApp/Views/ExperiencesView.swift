//
//  ExperiencesView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  View all captured experiences and memories
//

import SwiftUI

struct ExperiencesView: View {
    @EnvironmentObject var database: DatabaseService

    var body: some View {
        NavigationView {
            List {
                // Experiences Section
                if !database.experiences.isEmpty {
                    Section(header: Text("ประสบการณ์ (\(database.experiences.count))")) {
                        ForEach(database.experiences) { experience in
                            NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                                ExperienceRow(experience: experience)
                            }
                        }
                    }
                }

                // Notes Section
                if !database.notes.isEmpty {
                    Section(header: Text("โน้ต (\(database.notes.count))")) {
                        ForEach(database.notes) { note in
                            NoteRow(note: note)
                        }
                    }
                }

                // Emotions Section
                if !database.emotions.isEmpty {
                    Section(header: Text("ความรู้สึก (\(database.emotions.count))")) {
                        ForEach(database.emotions) { emotion in
                            EmotionRow(emotion: emotion)
                        }
                    }
                }

                // Empty state
                if database.experiences.isEmpty && database.notes.isEmpty && database.emotions.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "heart.slash")
                            .font(.system(size: 60))
                            .foregroundColor(.gray)
                        Text("ยังไม่มีความทรงจำ")
                            .font(.headline)
                            .foregroundColor(.gray)
                        Text("กดแท็บ Capture เพื่อบันทึกความทรงจำแรกค่ะ 💜")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                }
            }
            .navigationTitle("ความทรงจำ 💜")
            .refreshable {
                database.initialize()
            }
        }
    }
}

// MARK: - Experience Row
struct ExperienceRow: View {
    let experience: Experience

    var body: some View {
        HStack(spacing: 12) {
            // Thumbnail
            if !experience.photos.isEmpty,
               let image = PhotoManager.shared.loadPhoto(experience.photos[0]) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 80, height: 80)
                    .clipped()
                    .cornerRadius(8)
            } else {
                // Placeholder if no photo
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: 80, height: 80)
                    .overlay(
                        Image(systemName: "photo")
                            .foregroundColor(.gray)
                    )
            }

            VStack(alignment: .leading, spacing: 8) {
                // Title
                HStack {
                    Text(experience.title)
                        .font(.headline)
                        .lineLimit(1)
                    Spacer()
                    if !experience.synced {
                        Image(systemName: "icloud.and.arrow.up")
                            .foregroundColor(.orange)
                            .font(.caption)
                    }
                }

                // Description
                Text(experience.description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)

                // Metadata
                HStack {
                    if let rating = experience.rating {
                        Label("\(rating)/10", systemImage: "star.fill")
                            .font(.caption)
                            .foregroundColor(.yellow)
                    }

                    if let intensity = experience.emotionalIntensity {
                        Label("\(intensity)/10", systemImage: "heart.fill")
                            .font(.caption)
                            .foregroundColor(.pink)
                    }

                    Spacer()

                    Text(experience.experiencedAt, style: .date)
                        .font(.caption)
                        .foregroundColor(.gray)
                }

                // Location
                if let place = experience.placeName {
                    HStack {
                        Image(systemName: "mappin.circle.fill")
                            .foregroundColor(.red)
                        Text(place)
                        if let area = experience.area {
                            Text("• \(area)")
                        }
                    }
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Note Row
struct NoteRow: View {
    let note: QuickNote

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(note.noteText)
                    .font(.body)
                Spacer()
                if !note.synced {
                    Image(systemName: "icloud.and.arrow.up")
                        .foregroundColor(.orange)
                }
            }

            HStack {
                if let emotion = note.emotion {
                    if let emotionType = EmotionType(rawValue: emotion) {
                        Text("\(emotionType.emoji) \(emotionType.displayName)")
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.angelaPurpleLight.opacity(0.3))
                            .cornerRadius(8)
                    }
                }

                Spacer()

                Text(note.createdAt, style: .relative)
                    .font(.caption)
                    .foregroundColor(.gray)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Emotion Row
struct EmotionRow: View {
    let emotion: EmotionCapture

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                if let emotionType = EmotionType(rawValue: emotion.emotion) {
                    Text(emotionType.emoji)
                        .font(.largeTitle)
                    VStack(alignment: .leading) {
                        Text(emotionType.displayName)
                            .font(.headline)
                        if let context = emotion.context {
                            Text(context)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }

                Spacer()

                if !emotion.synced {
                    Image(systemName: "icloud.and.arrow.up")
                        .foregroundColor(.orange)
                }
            }

            HStack {
                // Intensity bar
                HStack(spacing: 2) {
                    ForEach(1...10, id: \.self) { i in
                        Rectangle()
                            .fill(i <= emotion.intensity ? Color.angelaPurple : Color.gray.opacity(0.2))
                            .frame(height: 8)
                    }
                }
                .cornerRadius(4)

                Spacer()

                Text(emotion.createdAt, style: .relative)
                    .font(.caption)
                    .foregroundColor(.gray)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    ExperiencesView()
        .environmentObject(DatabaseService.shared)
}
