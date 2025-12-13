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

    // Search & Filter states
    @State private var searchText = ""
    @State private var selectedViewMode: ViewMode = .list
    @State private var filterEmotion: EmotionType? = nil
    @State private var filterMinRating: Int = 0
    @State private var showingFilterSheet = false

    enum ViewMode {
        case list, timeline, gallery
    }

    // Computed filtered experiences
    private var filteredExperiences: [Experience] {
        var results = database.experiences

        // Search filter
        if !searchText.isEmpty {
            results = results.filter { exp in
                exp.title.localizedCaseInsensitiveContains(searchText) ||
                exp.description.localizedCaseInsensitiveContains(searchText) ||
                (exp.placeName?.localizedCaseInsensitiveContains(searchText) ?? false) ||
                (exp.area?.localizedCaseInsensitiveContains(searchText) ?? false)
            }
        }

        // Rating filter
        if filterMinRating > 0 {
            results = results.filter { ($0.rating ?? 0) >= filterMinRating }
        }

        return results.sorted { $0.experiencedAt > $1.experiencedAt }
    }

     // Computed filtered experiences for List View (exclude synced items)
    private var filteredExperiencesForList: [Experience] {
        filteredExperiences.filter { !$0.synced }
    }

    private var filteredEmotions: [EmotionCapture] {
        var results = database.emotions

        // Emotion type filter
        if let emotion = filterEmotion {
            results = results.filter { $0.emotion == emotion.rawValue }
        }

        return results.sorted { $0.createdAt > $1.createdAt }
    }

    // Computed filtered emotions for List View (exclude synced items)
    private var filteredEmotionsForList: [EmotionCapture] {
        filteredEmotions.filter { !$0.synced }
    }

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Search bar
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.gray)
                    TextField("ค้นหา...", text: $searchText)
                        .textFieldStyle(.plain)

                    if !searchText.isEmpty {
                        Button(action: { searchText = "" }) {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundColor(.gray)
                        }
                    }

                    Button(action: { showingFilterSheet = true }) {
                        Image(systemName: hasActiveFilters ? "line.3.horizontal.decrease.circle.fill" : "line.3.horizontal.decrease.circle")
                            .foregroundColor(hasActiveFilters ? .angelaPurple : .gray)
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
                .background(Color(.systemGray6))

                // View mode selector
                Picker("View Mode", selection: $selectedViewMode) {
                    Label("รายการ", systemImage: "list.bullet").tag(ViewMode.list)
                    Label("Timeline", systemImage: "calendar").tag(ViewMode.timeline)
                    Label("รูปภาพ", systemImage: "square.grid.2x2").tag(ViewMode.gallery)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)
                .padding(.vertical, 8)

                // Content based on view mode
                if selectedViewMode == .list {
                    listView
                } else if selectedViewMode == .timeline {
                    timelineView
                } else {
                    galleryView
                }
            }
            .navigationTitle("ความทรงจำ 💜")
            .sheet(isPresented: $showingFilterSheet) {
                filterSheet
            }
        }
    }

    // MARK: - List View
    private var listView: some View {
        List {
            // Experiences Section (only show unsynced items)
            if !filteredExperiencesForList.isEmpty {
                Section(header: Text("ประสบการณ์ (\(filteredExperiencesForList.count))")) {
                    ForEach(filteredExperiencesForList) { experience in
                        NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                            ExperienceRow(experience: experience)
                        }
                    }
                }
            }

            // Emotions Section (only show unsynced items)
            if !filteredEmotionsForList.isEmpty {
                Section(header: Text("ความรู้สึก (\(filteredEmotionsForList.count))")) {
                    ForEach(filteredEmotionsForList) { emotion in
                        EmotionRow(emotion: emotion)
                    }
                }
            }

            // Empty state
            if filteredExperiencesForList.isEmpty && filteredEmotionsForList.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: hasActiveFilters || !searchText.isEmpty ? "magnifyingglass" : "checkmark.circle.fill")
                        .font(.system(size: 60))
                        .foregroundColor(hasActiveFilters || !searchText.isEmpty ? .gray : .green)
                    Text(hasActiveFilters || !searchText.isEmpty ? "ไม่พบผลลัพธ์" : "ทุกอย่าง sync แล้วค่ะ ✅")
                        .font(.headline)
                        .foregroundColor(.gray)
                    Text(hasActiveFilters || !searchText.isEmpty ? "ลองค้นหาหรือกรองแบบอื่นค่ะ" : "ไปดูที่ Timeline เพื่อดูความทรงจำทั้งหมดค่ะ 💜")
                        .font(.caption)
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding()
            }
        }
        .refreshable {
            database.initialize()
        }
    }

    // MARK: - Timeline View
    private var timelineView: some View {
        ScrollView {
            LazyVStack(spacing: 16) {
                ForEach(groupedByDate.keys.sorted(by: >), id: \.self) { date in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(formatDate(date))
                            .font(.headline)
                            .foregroundColor(.angelaPurple)
                            .padding(.horizontal)

                        ForEach(groupedByDate[date] ?? []) { experience in
                            NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                                ExperienceRow(experience: experience)
                                    .padding(.horizontal)
                            }
                        }
                    }
                }
            }
            .padding(.vertical)
        }
    }

    // MARK: - Gallery View
    private var galleryView: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 100))], spacing: 8) {
                ForEach(filteredExperiences) { experience in
                    if !experience.photos.isEmpty,
                       let image = PhotoManager.shared.loadPhoto(experience.photos[0]) {
                        NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                            Image(uiImage: image)
                                .resizable()
                                .scaledToFill()
                                .frame(width: 100, height: 100)
                                .clipped()
                                .cornerRadius(8)
                        }
                    }
                }
            }
            .padding()
        }
    }

    // MARK: - Filter Sheet
    private var filterSheet: some View {
        NavigationView {
            Form {
                Section(header: Text("คะแนนขั้นต่ำ")) {
                    Picker("Rating", selection: $filterMinRating) {
                        Text("ทั้งหมด").tag(0)
                        ForEach(Array(1...10), id: \.self) { rating in
                            Text("\(rating)/10 ขึ้นไป").tag(rating)
                        }
                    }
                }

                Section(header: Text("ประเภทอารมณ์")) {
                    Picker("Emotion", selection: $filterEmotion) {
                        Text("ทั้งหมด").tag(nil as EmotionType?)
                        ForEach(EmotionType.allCases, id: \.self) { emotion in
                            Text("\(emotion.emoji) \(emotion.displayName)").tag(emotion as EmotionType?)
                        }
                    }
                }

                Section {
                    Button("รีเซ็ตฟิลเตอร์") {
                        filterMinRating = 0
                        filterEmotion = nil
                    }
                    .foregroundColor(.red)
                }
            }
            .navigationTitle("กรอง")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("เสร็จ") {
                        showingFilterSheet = false
                    }
                }
            }
        }
    }

    // MARK: - Helper Properties
    private var hasActiveFilters: Bool {
        filterMinRating > 0 || filterEmotion != nil
    }

    private var groupedByDate: [Date: [Experience]] {
        Dictionary(grouping: filteredExperiences) { experience in
            Calendar.current.startOfDay(for: experience.experiencedAt)
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.dateFormat = "d MMMM yyyy"
        return formatter.string(from: date)
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
                    ForEach(Array(1...10), id: \.self) { i in
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
