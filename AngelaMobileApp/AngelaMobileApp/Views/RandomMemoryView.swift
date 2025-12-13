//
//  RandomMemoryView.swift
//  Angela Mobile App
//
//  Feature 14: Random Memory - Show a random past experience
//

import SwiftUI

struct RandomMemoryView: View {
    @EnvironmentObject var database: DatabaseService
    @State private var randomExperience: Experience?
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 0) {
            if let experience = randomExperience {
                // Show the random experience
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Header
                        VStack(spacing: 8) {
                            Text("🎲 ความทรงจำสุ่ม")
                                .font(.title)
                                .fontWeight(.bold)
                            Text(daysAgoText(experience.experiencedAt))
                                .font(.subheadline)
                                .foregroundColor(.gray)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()

                        // Photo gallery
                        if !experience.photos.isEmpty {
                            TabView {
                                ForEach(experience.photos.indices, id: \.self) { index in
                                    if let image = PhotoManager.shared.loadPhoto(experience.photos[index]) {
                                        Image(uiImage: image)
                                            .resizable()
                                            .scaledToFill()
                                            .frame(height: 300)
                                            .clipped()
                                    }
                                }
                            }
                            .frame(height: 300)
                            .tabViewStyle(.page)
                        }

                        VStack(alignment: .leading, spacing: 16) {
                            // Title
                            Text(experience.title)
                                .font(.title2)
                                .fontWeight(.bold)

                            // Date and location
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Image(systemName: "calendar")
                                        .foregroundColor(.angelaPurple)
                                    Text(experience.experiencedAt.formatted(date: .long, time: .omitted))
                                }
                                .font(.subheadline)

                                if let placeName = experience.placeName {
                                    HStack {
                                        Image(systemName: "mappin.circle.fill")
                                            .foregroundColor(.angelaPurple)
                                        Text(placeName)
                                    }
                                    .font(.subheadline)
                                }
                            }
                            .padding()
                            .background(Color.angelaPurpleLight.opacity(0.1))
                            .cornerRadius(12)

                            // Description
                            Text(experience.description)
                                .font(.body)

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
                            }

                            // View full details button
                            NavigationLink(destination: ExperienceDetailView(experience: experience)) {
                                Text("ดูรายละเอียดเต็ม")
                                    .font(.headline)
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(Color.angelaPurple)
                                    .cornerRadius(12)
                            }
                        }
                        .padding()
                    }
                }

                // Bottom bar with shuffle button
                VStack {
                    Divider()
                    Button(action: loadRandomMemory) {
                        HStack {
                            Image(systemName: "shuffle")
                            Text("สุ่มความทรงจำอื่น")
                                .fontWeight(.semibold)
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.angelaPurple)
                        .cornerRadius(12)
                    }
                    .padding()
                }
            } else {
                // Empty state
                VStack(spacing: 20) {
                    if isLoading {
                        ProgressView()
                            .scaleEffect(1.5)
                    } else if database.experiences.isEmpty {
                        VStack(spacing: 12) {
                            Image(systemName: "photo.on.rectangle.angled")
                                .font(.system(size: 60))
                                .foregroundColor(.gray.opacity(0.5))
                            Text("ยังไม่มีความทรงจำ")
                                .font(.headline)
                                .foregroundColor(.gray)
                            Text("เริ่มบันทึกความทรงจำเพื่อใช้งานฟีเจอร์นี้")
                                .font(.caption)
                                .foregroundColor(.gray)
                                .multilineTextAlignment(.center)
                        }
                    } else {
                        VStack(spacing: 20) {
                            Image(systemName: "dice")
                                .font(.system(size: 80))
                                .foregroundColor(.angelaPurple)

                            Text("ค้นพบความทรงจำ")
                                .font(.title)
                                .fontWeight(.bold)

                            Text("กดปุ่มด้านล่างเพื่อสุ่มดูความทรงจำในอดีต")
                                .font(.subheadline)
                                .foregroundColor(.gray)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 40)

                            Button(action: loadRandomMemory) {
                                HStack {
                                    Image(systemName: "shuffle")
                                    Text("สุ่มความทรงจำ")
                                        .fontWeight(.semibold)
                                }
                                .foregroundColor(.white)
                                .padding(.horizontal, 32)
                                .padding(.vertical, 16)
                                .background(Color.angelaPurple)
                                .cornerRadius(25)
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .navigationTitle("ความทรงจำสุ่ม")
        .onAppear {
            if randomExperience == nil && !database.experiences.isEmpty {
                loadRandomMemory()
            }
        }
    }

    // MARK: - Functions

    func loadRandomMemory() {
        guard !database.experiences.isEmpty else { return }

        isLoading = true

        // Add slight delay for animation
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            randomExperience = database.experiences.randomElement()
            isLoading = false
        }
    }

    func daysAgoText(_ date: Date) -> String {
        let calendar = Calendar.current
        let days = calendar.dateComponents([.day], from: date, to: Date()).day ?? 0

        if days == 0 {
            return "วันนี้"
        } else if days == 1 {
            return "เมื่อวานนี้"
        } else if days < 7 {
            return "\(days) วันที่แล้ว"
        } else if days < 30 {
            let weeks = days / 7
            return "\(weeks) สัปดาห์ที่แล้ว"
        } else if days < 365 {
            let months = days / 30
            return "\(months) เดือนที่แล้ว"
        } else {
            let years = days / 365
            return "\(years) ปีที่แล้ว"
        }
    }
}

#Preview {
    RandomMemoryView()
        .environmentObject(DatabaseService.shared)
}
