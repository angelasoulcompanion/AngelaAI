//
//  AnimatedTimelineView.swift
//  Angela Mobile App
//
//  Animated timeline view with smooth transitions
//  Feature 28: Memory Timeline Animation
//

import SwiftUI

struct AnimatedTimelineView: View {
    @EnvironmentObject var database: DatabaseService
    @State private var selectedIndex: Int = 0
    @State private var isAnimating = false
    @State private var showDetails = false

    // Group experiences by month
    private var groupedExperiences: [(String, [Experience])] {
        let grouped = Dictionary(grouping: database.experiences.sorted(by: { $0.experiencedAt > $1.experiencedAt })) { experience in
            let formatter = DateFormatter()
            formatter.dateFormat = "MMMM yyyy"
            formatter.locale = Locale(identifier: "th_TH")
            return formatter.string(from: experience.experiencedAt)
        }

        return grouped.sorted { first, second in
            guard let date1 = first.value.first?.experiencedAt,
                  let date2 = second.value.first?.experiencedAt else {
                return false
            }
            return date1 > date2
        }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                ForEach(Array(groupedExperiences.enumerated()), id: \.offset) { monthIndex, monthData in
                    // Month header
                    MonthHeaderView(monthName: monthData.0)
                        .transition(.slide)
                        .animation(.easeInOut(duration: 0.3), value: isAnimating)

                    // Experiences in this month
                    ForEach(Array(monthData.1.enumerated()), id: \.element.id) { index, experience in
                        AnimatedMemoryCard(
                            experience: experience,
                            index: index,
                            isAnimating: $isAnimating
                        )
                        .transition(.asymmetric(
                            insertion: .move(edge: .trailing).combined(with: .opacity),
                            removal: .move(edge: .leading).combined(with: .opacity)
                        ))
                    }
                }
            }
            .padding()
        }
        .navigationTitle("🎬 Timeline แบบเคลื่อนไหว")
        .onAppear {
            withAnimation {
                isAnimating = true
            }
        }
    }
}

// MARK: - Month Header View

struct MonthHeaderView: View {
    let monthName: String

    var body: some View {
        HStack {
            Text(monthName)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.angelaPurple)

            Spacer()

            Circle()
                .fill(Color.angelaPurple.opacity(0.3))
                .frame(width: 12, height: 12)
        }
        .padding(.vertical, 12)
        .padding(.horizontal, 8)
    }
}

// MARK: - Animated Memory Card

struct AnimatedMemoryCard: View {
    let experience: Experience
    let index: Int
    @Binding var isAnimating: Bool

    @State private var appeared = false
    @State private var isExpanded = false

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Timeline line and dot
            VStack {
                Circle()
                    .fill(Color.angelaPurple)
                    .frame(width: 16, height: 16)
                    .scaleEffect(appeared ? 1.0 : 0.0)
                    .animation(.spring(response: 0.5, dampingFraction: 0.6).delay(Double(index) * 0.1), value: appeared)

                Rectangle()
                    .fill(Color.angelaPurple.opacity(0.3))
                    .frame(width: 2)
            }

            // Memory content
            VStack(alignment: .leading, spacing: 8) {
                // Title and date
                VStack(alignment: .leading, spacing: 4) {
                    Text(experience.title)
                        .font(.headline)
                        .foregroundColor(.primary)

                    Text(experience.experiencedAt.formatted(date: .abbreviated, time: .shortened))
                        .font(.caption)
                        .foregroundColor(.gray)
                }

                // Photo preview
                if !experience.photos.isEmpty, let firstPhoto = experience.photos.first {
                    if let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                        Image(uiImage: image)
                            .resizable()
                            .scaledToFill()
                            .frame(height: isExpanded ? 200 : 120)
                            .clipped()
                            .cornerRadius(12)
                            .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
                            .onTapGesture {
                                withAnimation(.spring(response: 0.4, dampingFraction: 0.75)) {
                                    isExpanded.toggle()
                                }
                            }
                    }
                }

                // Description
                if isExpanded {
                    Text(experience.description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .transition(.opacity.combined(with: .move(edge: .top)))
                }

                // Location
                if let placeName = experience.placeName {
                    HStack(spacing: 4) {
                        Image(systemName: "mappin.circle.fill")
                            .font(.caption)
                        Text(placeName)
                            .font(.caption)
                    }
                    .foregroundColor(.angelaPurple)
                }

                // Rating
                if let rating = experience.rating {
                    HStack(spacing: 2) {
                        Image(systemName: "star.fill")
                            .font(.caption)
                            .foregroundColor(.yellow)
                        Text("\(rating)/10")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
            }
            .padding()
            .background(Color.gray.opacity(0.05))
            .cornerRadius(12)
            .offset(x: appeared ? 0 : 50)
            .opacity(appeared ? 1 : 0)
            .animation(.easeOut(duration: 0.4).delay(Double(index) * 0.1), value: appeared)
        }
        .padding(.vertical, 8)
        .onAppear {
            appeared = true
        }
    }
}

#Preview {
    NavigationView {
        AnimatedTimelineView()
            .environmentObject(DatabaseService.shared)
    }
}
