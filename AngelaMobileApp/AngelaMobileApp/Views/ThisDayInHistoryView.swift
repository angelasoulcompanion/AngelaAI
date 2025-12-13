//
//  ThisDayInHistoryView.swift
//  Angela Mobile App
//
//  Feature 9: This Day in History - Memories from same date in past years
//

import SwiftUI

struct ThisDayInHistoryView: View {
    @EnvironmentObject var database: DatabaseService
    @State private var selectedYear: Int?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    Text("📅 วันนี้ในอดีต")
                        .font(.title)
                        .fontWeight(.bold)

                    Text(currentDateString)
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                .padding()

                if memoriesByYear.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "calendar.badge.clock")
                            .font(.system(size: 60))
                            .foregroundColor(.gray.opacity(0.5))
                        Text("ยังไม่มีความทรงจำในวันนี้")
                            .font(.headline)
                            .foregroundColor(.gray)
                        Text("กลับมาดูในปีหน้านะคะ 💜")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                } else {
                    // Memories grouped by year
                    ForEach(memoriesByYear.sorted(by: { $0.key > $1.key }), id: \.key) { year, experiences in
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Text("\(yearsAgo(year)) ปีที่แล้ว")
                                    .font(.headline)
                                    .foregroundColor(.angelaPurple)
                                Spacer()
                                Text("พ.ศ. \(year + 543)")
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            .padding(.horizontal)

                            ForEach(experiences) { experience in
                                NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                                    ThisDayMemoryCard(experience: experience)
                                }
                                .buttonStyle(PlainButtonStyle())
                            }
                        }
                        .padding(.vertical, 8)
                    }
                }
            }
        }
        .navigationTitle("วันนี้ในอดีต")
    }

    // MARK: - Data Processing

    var currentDateString: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.dateFormat = "d MMMM"
        return formatter.string(from: Date())
    }

    var memoriesByYear: [Int: [Experience]] {
        let calendar = Calendar.current
        let today = Date()
        let currentDay = calendar.component(.day, from: today)
        let currentMonth = calendar.component(.month, from: today)

        // Filter experiences that match today's day and month (but different year)
        let matchingExperiences = database.experiences.filter { experience in
            let expDay = calendar.component(.day, from: experience.experiencedAt)
            let expMonth = calendar.component(.month, from: experience.experiencedAt)
            let expYear = calendar.component(.year, from: experience.experiencedAt)
            let currentYear = calendar.component(.year, from: today)

            return expDay == currentDay && expMonth == currentMonth && expYear != currentYear
        }

        // Group by year
        return Dictionary(grouping: matchingExperiences) { experience in
            calendar.component(.year, from: experience.experiencedAt)
        }
    }

    func yearsAgo(_ year: Int) -> Int {
        let currentYear = Calendar.current.component(.year, from: Date())
        return currentYear - year
    }
}

struct ThisDayMemoryCard: View {
    let experience: Experience

    var body: some View {
        HStack(spacing: 12) {
            // Photo thumbnail
            if let firstPhoto = experience.photos.first,
               let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 80, height: 80)
                    .clipped()
                    .cornerRadius(8)
            } else {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.angelaPurpleLight.opacity(0.3))
                    .frame(width: 80, height: 80)
                    .overlay(
                        Image(systemName: "photo")
                            .foregroundColor(.gray)
                    )
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(experience.title)
                    .font(.headline)
                    .foregroundColor(.primary)
                    .lineLimit(1)

                if let placeName = experience.placeName {
                    HStack(spacing: 4) {
                        Image(systemName: "mappin.circle.fill")
                            .font(.caption)
                        Text(placeName)
                            .font(.caption)
                    }
                    .foregroundColor(.gray)
                }

                Text(experience.description)
                    .font(.caption)
                    .foregroundColor(.gray)
                    .lineLimit(2)

                HStack {
                    if let rating = experience.rating {
                        HStack(spacing: 2) {
                            Image(systemName: "star.fill")
                                .font(.caption2)
                            Text("\(rating)/10")
                                .font(.caption2)
                        }
                        .foregroundColor(.yellow)
                    }

                    Spacer()

                    Text(formatYear(experience.experiencedAt))
                        .font(.caption2)
                        .foregroundColor(.angelaPurple)
                        .fontWeight(.semibold)
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

    func formatYear(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy"
        return formatter.string(from: date)
    }
}

#Preview {
    ThisDayInHistoryView()
        .environmentObject(DatabaseService.shared)
}
