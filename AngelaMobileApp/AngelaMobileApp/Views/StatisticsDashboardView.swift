//
//  StatisticsDashboardView.swift
//  Angela Mobile App
//
//  Feature 8: Statistics Dashboard - Overall stats
//

import SwiftUI

struct StatisticsDashboardView: View {
    @EnvironmentObject var database: DatabaseService

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Hero stats
                VStack(spacing: 16) {
                    StatCard(
                        title: "ความทรงจำทั้งหมด",
                        value: "\(database.experiences.count)",
                        icon: "photo.on.rectangle.angled",
                        color: .angelaPurple
                    )

                    HStack(spacing: 16) {
                        StatCard(
                            title: "รูปภาพ",
                            value: "\(totalPhotos)",
                            icon: "photo",
                            color: .blue,
                            compact: true
                        )
                        StatCard(
                            title: "เสียงบันทึก",
                            value: "\(totalVoiceNotes)",
                            icon: "mic",
                            color: .orange,
                            compact: true
                        )
                    }

                    HStack(spacing: 16) {
                        StatCard(
                            title: "วิดีโอ",
                            value: "\(totalVideos)",
                            icon: "video",
                            color: .red,
                            compact: true
                        )
                        StatCard(
                            title: "สถานที่",
                            value: "\(uniquePlaces)",
                            icon: "mappin.circle",
                            color: .green,
                            compact: true
                        )
                    }
                }
                .padding()

                // Rating stats
                VStack(alignment: .leading, spacing: 12) {
                    Text("⭐ คะแนนเฉลี่ย")
                        .font(.title2)
                        .fontWeight(.bold)

                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\(String(format: "%.1f", averageRating))/10")
                                .font(.system(size: 48, weight: .bold))
                                .foregroundColor(.angelaPurple)
                            Text("จาก \(experiencesWithRating) ครั้ง")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }

                        Spacer()

                        // Rating distribution
                        VStack(alignment: .trailing, spacing: 4) {
                            RatingBar(label: "9-10", count: (ratingDistribution[9] ?? 0) + (ratingDistribution[10] ?? 0), color: .green)
                            RatingBar(label: "7-8", count: (ratingDistribution[7] ?? 0) + (ratingDistribution[8] ?? 0), color: .blue)
                            RatingBar(label: "5-6", count: (ratingDistribution[5] ?? 0) + (ratingDistribution[6] ?? 0), color: .orange)
                            RatingBar(label: "1-4", count: (ratingDistribution[1] ?? 0) + (ratingDistribution[2] ?? 0) + (ratingDistribution[3] ?? 0) + (ratingDistribution[4] ?? 0), color: .red)
                        }
                    }
                }
                .padding()
                .background(Color.white)
                .cornerRadius(12)
                .shadow(radius: 2)

                // Emotion stats
                VStack(alignment: .leading, spacing: 12) {
                    Text("💭 อารมณ์ทั้งหมด")
                        .font(.title2)
                        .fontWeight(.bold)

                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\(database.emotions.count)")
                                .font(.system(size: 48, weight: .bold))
                                .foregroundColor(.angelaPurple)
                            Text("อารมณ์ที่บันทึก")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }

                        Spacer()

                        VStack(alignment: .trailing, spacing: 4) {
                            Text("เฉลี่ย \(String(format: "%.1f", averageEmotionIntensity))/10")
                                .font(.headline)
                            Text("ความเข้มข้น")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                    }
                }
                .padding()
                .background(Color.white)
                .cornerRadius(12)
                .shadow(radius: 2)

                // Time stats
                VStack(alignment: .leading, spacing: 12) {
                    Text("📅 เวลา")
                        .font(.title2)
                        .fontWeight(.bold)

                    HStack(spacing: 16) {
                        TimeStatBox(
                            title: "วันแรก",
                            value: oldestExperience?.experiencedAt.formatted(date: .abbreviated, time: .omitted) ?? "-"
                        )
                        TimeStatBox(
                            title: "ล่าสุด",
                            value: newestExperience?.experiencedAt.formatted(date: .abbreviated, time: .omitted) ?? "-"
                        )
                    }

                    Text("รวม \(totalDays) วัน")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                .padding()
                .background(Color.white)
                .cornerRadius(12)
                .shadow(radius: 2)

                // Favorite place
                if let favoritePlace = favoritePlace {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("❤️ สถานที่โปรด")
                            .font(.title2)
                            .fontWeight(.bold)

                        HStack {
                            Text(favoritePlace.name)
                                .font(.headline)
                            Spacer()
                            Text("\(favoritePlace.count) ครั้ง")
                                .font(.subheadline)
                                .foregroundColor(.gray)
                        }
                    }
                    .padding()
                    .background(Color.angelaPurpleLight.opacity(0.2))
                    .cornerRadius(12)
                }
            }
            .padding()
        }
        .navigationTitle("📊 สถิติ")
    }

    // MARK: - Computed Properties

    var totalPhotos: Int {
        database.experiences.reduce(0) { $0 + $1.photos.count }
    }

    var totalVoiceNotes: Int {
        database.experiences.reduce(0) { $0 + $1.voiceNotes.count }
    }

    var totalVideos: Int {
        database.experiences.reduce(0) { $0 + $1.videos.count }
    }

    var uniquePlaces: Int {
        Set(database.experiences.compactMap { $0.placeName }).count
    }

    var averageRating: Double {
        let ratings = database.experiences.compactMap { $0.rating }
        guard !ratings.isEmpty else { return 0 }
        return Double(ratings.reduce(0, +)) / Double(ratings.count)
    }

    var experiencesWithRating: Int {
        database.experiences.filter { $0.rating != nil }.count
    }

    var ratingDistribution: [Int: Int] {
        var distribution: [Int: Int] = [:]
        for i in 1...10 {
            distribution[i] = 0
        }
        for experience in database.experiences {
            if let rating = experience.rating {
                distribution[rating, default: 0] += 1
            }
        }
        return distribution
    }

    var averageEmotionIntensity: Double {
        guard !database.emotions.isEmpty else { return 0 }
        return Double(database.emotions.map { $0.intensity }.reduce(0, +)) / Double(database.emotions.count)
    }

    var oldestExperience: Experience? {
        database.experiences.sorted { $0.experiencedAt < $1.experiencedAt }.first
    }

    var newestExperience: Experience? {
        database.experiences.sorted { $0.experiencedAt > $1.experiencedAt }.first
    }

    var totalDays: Int {
        guard let oldest = oldestExperience, let newest = newestExperience else { return 0 }
        return Calendar.current.dateComponents([.day], from: oldest.experiencedAt, to: newest.experiencedAt).day ?? 0
    }

    struct PlaceCount {
        let name: String
        let count: Int
    }

    var favoritePlace: PlaceCount? {
        let places = database.experiences.compactMap { $0.placeName }
        guard !places.isEmpty else { return nil }

        let grouped = Dictionary(grouping: places) { $0 }
        let sorted = grouped.map { PlaceCount(name: $0.key, count: $0.value.count) }
            .sorted { $0.count > $1.count }

        return sorted.first
    }
}

// MARK: - Supporting Views

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    var compact: Bool = false

    var body: some View {
        VStack(spacing: compact ? 8 : 12) {
            Image(systemName: icon)
                .font(.system(size: compact ? 32 : 48))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: compact ? 28 : 42, weight: .bold))
                .foregroundColor(color)

            Text(title)
                .font(compact ? .caption : .subheadline)
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
        .padding(compact ? 12 : 20)
        .background(color.opacity(0.1))
        .cornerRadius(12)
    }
}

struct RatingBar: View {
    let label: String
    let count: Int
    let color: Color

    var body: some View {
        HStack(spacing: 8) {
            Text(label)
                .font(.caption)
                .frame(width: 40, alignment: .leading)

            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: 80, height: 12)

                RoundedRectangle(cornerRadius: 4)
                    .fill(color)
                    .frame(width: min(CGFloat(count) * 10, 80), height: 12)
            }

            Text("\(count)")
                .font(.caption2)
                .foregroundColor(.gray)
        }
    }
}

struct TimeStatBox: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.gray)
            Text(value)
                .font(.subheadline)
                .fontWeight(.semibold)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(8)
    }
}

#Preview {
    StatisticsDashboardView()
        .environmentObject(DatabaseService.shared)
}
