//
//  TopMomentsView.swift
//  Angela Mobile App
//
//  Feature 10: Top Moments - Highest rated experiences
//

import SwiftUI

struct TopMomentsView: View {
    @EnvironmentObject var database: DatabaseService
    @State private var filterType: FilterType = .allTime

    enum FilterType: String, CaseIterable {
        case allTime = "ทั้งหมด"
        case thisYear = "ปีนี้"
        case thisMonth = "เดือนนี้"
    }

    var body: some View {
        VStack(spacing: 0) {
            // Filter picker
            Picker("ช่วงเวลา", selection: $filterType) {
                ForEach(FilterType.allCases, id: \.self) { type in
                    Text(type.rawValue).tag(type)
                }
            }
            .pickerStyle(.segmented)
            .padding()

            if filteredTopMoments.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "star.circle")
                        .font(.system(size: 60))
                        .foregroundColor(.gray.opacity(0.5))
                    Text("ยังไม่มีความทรงจำที่ให้คะแนน")
                        .font(.headline)
                        .foregroundColor(.gray)
                }
                .frame(maxHeight: .infinity)
            } else {
                ScrollView {
                    VStack(spacing: 16) {
                        ForEach(Array(filteredTopMoments.enumerated()), id: \.element.id) { index, experience in
                            NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                                TopMomentCard(experience: experience, rank: index + 1)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("⭐ ช่วงเวลาที่ดีที่สุด")
    }

    // MARK: - Data Processing

    var filteredTopMoments: [Experience] {
        let calendar = Calendar.current
        let now = Date()

        var experiences = database.experiences.filter { $0.rating != nil }

        switch filterType {
        case .allTime:
            break  // No filter
        case .thisYear:
            experiences = experiences.filter { experience in
                calendar.component(.year, from: experience.experiencedAt) == calendar.component(.year, from: now)
            }
        case .thisMonth:
            experiences = experiences.filter { experience in
                calendar.isDate(experience.experiencedAt, equalTo: now, toGranularity: .month)
            }
        }

        return experiences.sorted { ($0.rating ?? 0) > ($1.rating ?? 0) }
    }
}

struct TopMomentCard: View {
    let experience: Experience
    let rank: Int

    var body: some View {
        HStack(spacing: 16) {
            // Rank badge
            ZStack {
                Circle()
                    .fill(rankColor)
                    .frame(width: 50, height: 50)
                Text("#\(rank)")
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
            }

            // Photo
            if let firstPhoto = experience.photos.first,
               let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 100, height: 100)
                    .clipped()
                    .cornerRadius(12)
            } else {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.angelaPurpleLight.opacity(0.3))
                    .frame(width: 100, height: 100)
                    .overlay(
                        Image(systemName: "photo")
                            .font(.largeTitle)
                            .foregroundColor(.gray)
                    )
            }

            // Details
            VStack(alignment: .leading, spacing: 6) {
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

                HStack(spacing: 12) {
                    // Rating
                    HStack(spacing: 4) {
                        Image(systemName: "star.fill")
                            .foregroundColor(.yellow)
                        Text("\(experience.rating ?? 0)/10")
                            .fontWeight(.bold)
                    }
                    .font(.subheadline)

                    // Date
                    Text(experience.experiencedAt.formatted(date: .abbreviated, time: .omitted))
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .foregroundColor(.gray.opacity(0.5))
        }
        .padding()
        .background(Color.white)
        .cornerRadius(16)
        .shadow(radius: 3)
    }

    var rankColor: Color {
        switch rank {
        case 1: return Color(red: 1.0, green: 0.84, blue: 0.0)  // Gold
        case 2: return Color(red: 0.75, green: 0.75, blue: 0.75)  // Silver
        case 3: return Color(red: 0.8, green: 0.5, blue: 0.2)  // Bronze
        default: return .angelaPurple
        }
    }
}

#Preview {
    TopMomentsView()
        .environmentObject(DatabaseService.shared)
}
