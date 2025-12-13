//
//  AdvancedSearchView.swift
//  Angela Mobile App
//
//  Feature 11: Advanced Search - Filter by date range, location, rating
//

import SwiftUI

struct AdvancedSearchView: View {
    @EnvironmentObject var database: DatabaseService
    @Environment(\.dismiss) var dismiss

    @State private var searchText = ""
    @State private var startDate = Calendar.current.date(byAdding: .month, value: -1, to: Date()) ?? Date()
    @State private var endDate = Date()
    @State private var minRating = 1
    @State private var selectedPlace: String?
    @State private var showDatePicker = false

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Search bar
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.gray)
                    TextField("ค้นหา...", text: $searchText)
                    if !searchText.isEmpty {
                        Button(action: { searchText = "" }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.gray)
                        }
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)
                .padding()

                // Filters
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Date range filter
                        VStack(alignment: .leading, spacing: 12) {
                            Text("📅 ช่วงเวลา")
                                .font(.headline)

                            HStack {
                                DatePicker("จาก", selection: $startDate, displayedComponents: .date)
                                    .datePickerStyle(.compact)
                            }

                            HStack {
                                DatePicker("ถึง", selection: $endDate, displayedComponents: .date)
                                    .datePickerStyle(.compact)
                            }
                        }
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                        .shadow(radius: 2)

                        // Rating filter
                        VStack(alignment: .leading, spacing: 12) {
                            Text("⭐ คะแนนขั้นต่ำ")
                                .font(.headline)

                            HStack {
                                Slider(value: Binding(
                                    get: { Double(minRating) },
                                    set: { minRating = Int($0) }
                                ), in: 1...10, step: 1)

                                Text("\(minRating)+")
                                    .font(.headline)
                                    .foregroundColor(.angelaPurple)
                                    .frame(width: 40)
                            }

                            HStack(spacing: 4) {
                                ForEach(1...10, id: \.self) { rating in
                                    Image(systemName: rating <= minRating ? "star.fill" : "star")
                                        .foregroundColor(rating <= minRating ? .yellow : .gray.opacity(0.3))
                                        .font(.caption)
                                }
                            }
                        }
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                        .shadow(radius: 2)

                        // Place filter
                        VStack(alignment: .leading, spacing: 12) {
                            Text("📍 สถานที่")
                                .font(.headline)

                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    Button(action: { selectedPlace = nil }) {
                                        Text("ทั้งหมด")
                                            .font(.caption)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(selectedPlace == nil ? Color.angelaPurple : Color.gray.opacity(0.2))
                                            .foregroundColor(selectedPlace == nil ? .white : .primary)
                                            .cornerRadius(16)
                                    }

                                    ForEach(availablePlaces, id: \.self) { place in
                                        Button(action: { selectedPlace = place }) {
                                            Text(place)
                                                .font(.caption)
                                                .padding(.horizontal, 12)
                                                .padding(.vertical, 6)
                                                .background(selectedPlace == place ? Color.angelaPurple : Color.gray.opacity(0.2))
                                                .foregroundColor(selectedPlace == place ? .white : .primary)
                                                .cornerRadius(16)
                                        }
                                    }
                                }
                            }
                        }
                        .padding()
                        .background(Color.white)
                        .cornerRadius(12)
                        .shadow(radius: 2)

                        // Results
                        VStack(alignment: .leading, spacing: 12) {
                            Text("📋 ผลการค้นหา (\(filteredExperiences.count))")
                                .font(.headline)

                            if filteredExperiences.isEmpty {
                                VStack(spacing: 12) {
                                    Image(systemName: "magnifyingglass")
                                        .font(.system(size: 48))
                                        .foregroundColor(.gray.opacity(0.5))
                                    Text("ไม่พบความทรงจำที่ตรงกัน")
                                        .foregroundColor(.gray)
                                }
                                .frame(maxWidth: .infinity)
                                .padding(40)
                            } else {
                                ForEach(filteredExperiences) { experience in
                                    NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                                        SearchResultCard(experience: experience)
                                    }
                                    .buttonStyle(PlainButtonStyle())
                                }
                            }
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("🔍 ค้นหาขั้นสูง")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("รีเซ็ต") {
                        resetFilters()
                    }
                    .foregroundColor(.angelaPurple)
                }
            }
        }
    }

    // MARK: - Data Processing

    var filteredExperiences: [Experience] {
        database.experiences.filter { experience in
            // Text search
            let matchesText = searchText.isEmpty ||
                experience.title.localizedCaseInsensitiveContains(searchText) ||
                experience.description.localizedCaseInsensitiveContains(searchText) ||
                (experience.placeName?.localizedCaseInsensitiveContains(searchText) ?? false)

            // Date range
            let matchesDate = experience.experiencedAt >= startDate && experience.experiencedAt <= endDate

            // Rating
            let matchesRating = (experience.rating ?? 0) >= minRating

            // Place
            let matchesPlace = selectedPlace == nil || experience.placeName == selectedPlace

            return matchesText && matchesDate && matchesRating && matchesPlace
        }
        .sorted { $0.experiencedAt > $1.experiencedAt }
    }

    var availablePlaces: [String] {
        Array(Set(database.experiences.compactMap { $0.placeName })).sorted()
    }

    func resetFilters() {
        searchText = ""
        startDate = Calendar.current.date(byAdding: .month, value: -1, to: Date()) ?? Date()
        endDate = Date()
        minRating = 1
        selectedPlace = nil
    }
}

struct SearchResultCard: View {
    let experience: Experience

    var body: some View {
        HStack(spacing: 12) {
            // Thumbnail
            if let firstPhoto = experience.photos.first,
               let image = PhotoManager.shared.loadPhoto(firstPhoto) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 60, height: 60)
                    .clipped()
                    .cornerRadius(8)
            } else {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.angelaPurpleLight.opacity(0.3))
                    .frame(width: 60, height: 60)
                    .overlay(
                        Image(systemName: "photo")
                            .foregroundColor(.gray)
                    )
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(experience.title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)
                    .lineLimit(1)

                if let placeName = experience.placeName {
                    Text(placeName)
                        .font(.caption)
                        .foregroundColor(.gray)
                }

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

                    Text(experience.experiencedAt.formatted(date: .abbreviated, time: .omitted))
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .foregroundColor(.gray.opacity(0.5))
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(radius: 1)
    }
}

#Preview {
    AdvancedSearchView()
        .environmentObject(DatabaseService.shared)
}
