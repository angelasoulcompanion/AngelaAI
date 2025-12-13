//
//  EmotionTrendsView.swift
//  Angela Mobile App
//
//  Feature 7: Emotion Trends - Bar chart showing last 7 days emotions
//

import SwiftUI
import Charts

struct EmotionTrendsView: View {
    @EnvironmentObject var database: DatabaseService

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Last 7 days emotion chart
                VStack(alignment: .leading, spacing: 12) {
                    Text("📊 อารมณ์ 7 วันที่ผ่านมา")
                        .font(.title2)
                        .fontWeight(.bold)

                    if #available(iOS 16.0, *) {
                        Chart(emotionData) { item in
                            BarMark(
                                x: .value("วัน", item.dayName),
                                y: .value("ความเข้มข้น", item.averageIntensity)
                            )
                            .foregroundStyle(Color.angelaPurple.gradient)
                        }
                        .frame(height: 200)
                    } else {
                        // Fallback for iOS 15
                        SimpleBarChart(data: emotionData)
                            .frame(height: 200)
                    }
                }
                .padding()
                .background(Color.angelaPurpleLight.opacity(0.1))
                .cornerRadius(12)

                // Emotion breakdown
                VStack(alignment: .leading, spacing: 12) {
                    Text("💭 อารมณ์แต่ละประเภท")
                        .font(.title2)
                        .fontWeight(.bold)

                    ForEach(emotionBreakdown, id: \.name) { emotion in
                        HStack {
                            Text(emotion.emoji)
                                .font(.title3)
                            VStack(alignment: .leading, spacing: 4) {
                                Text(emotion.name)
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                                Text("\(emotion.count) ครั้ง • เฉลี่ย \(String(format: "%.1f", emotion.averageIntensity))/10")
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            Spacer()

                            // Progress bar
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(Color.gray.opacity(0.2))
                                    .frame(width: 100, height: 8)
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(emotionColor(emotion.name))
                                    .frame(width: CGFloat(emotion.count) / CGFloat(max(1, maxEmotionCount)) * 100, height: 8)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
                .padding()
                .background(Color.white)
                .cornerRadius(12)
                .shadow(radius: 2)

                // Recent emotions
                VStack(alignment: .leading, spacing: 12) {
                    Text("🕐 อารมณ์ล่าสุด")
                        .font(.title2)
                        .fontWeight(.bold)

                    ForEach(recentEmotions.prefix(10)) { emotion in
                        HStack {
                            Text(EmotionType(rawValue: emotion.emotion)?.emoji ?? "💜")
                                .font(.title3)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(EmotionType(rawValue: emotion.emotion)?.displayName ?? emotion.emotion)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                                if let context = emotion.context {
                                    Text(context)
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                        .lineLimit(1)
                                }
                            }
                            Spacer()
                            Text("\(emotion.intensity)/10")
                                .font(.caption)
                                .foregroundColor(.angelaPurple)
                                .fontWeight(.semibold)
                        }
                        .padding()
                        .background(Color.gray.opacity(0.05))
                        .cornerRadius(8)
                    }
                }
                .padding()
            }
            .padding()
        }
        .navigationTitle("📈 แนวโน้มอารมณ์")
    }

    // MARK: - Data Processing

    struct DayEmotion: Identifiable {
        let id = UUID()
        let dayName: String
        let averageIntensity: Double
        let date: Date
    }

    var emotionData: [DayEmotion] {
        let calendar = Calendar.current
        let today = Date()
        var result: [DayEmotion] = []

        for i in 0..<7 {
            guard let date = calendar.date(byAdding: .day, value: -i, to: today) else { continue }
            let dayName = formatDayName(date, daysAgo: i)

            // Filter emotions for this day
            let dayEmotions = database.emotions.filter { emotion in
                calendar.isDate(emotion.createdAt, inSameDayAs: date)
            }

            let averageIntensity = dayEmotions.isEmpty
                ? 0
                : Double(dayEmotions.map { $0.intensity }.reduce(0, +)) / Double(dayEmotions.count)

            result.append(DayEmotion(dayName: dayName, averageIntensity: averageIntensity, date: date))
        }

        return result.reversed()  // Oldest to newest
    }

    struct EmotionSummary {
        let name: String
        let emoji: String
        let count: Int
        let averageIntensity: Double
    }

    var emotionBreakdown: [EmotionSummary] {
        let grouped = Dictionary(grouping: database.emotions) { $0.emotion }
        return grouped.map { key, emotions in
            let emotionType = EmotionType(rawValue: key)
            return EmotionSummary(
                name: emotionType?.displayName ?? key,
                emoji: emotionType?.emoji ?? "💜",
                count: emotions.count,
                averageIntensity: Double(emotions.map { $0.intensity }.reduce(0, +)) / Double(emotions.count)
            )
        }.sorted { $0.count > $1.count }
    }

    var maxEmotionCount: Int {
        emotionBreakdown.map { $0.count }.max() ?? 1
    }

    var recentEmotions: [EmotionCapture] {
        database.emotions.sorted { $0.createdAt > $1.createdAt }
    }

    func formatDayName(_ date: Date, daysAgo: Int) -> String {
        if daysAgo == 0 { return "วันนี้" }
        if daysAgo == 1 { return "เมื่อวาน" }

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.dateFormat = "EEE"
        return formatter.string(from: date)
    }

    func emotionColor(_ emotionName: String) -> Color {
        switch emotionName.lowercased() {
        case "มีความสุข", "happy": return .green
        case "เศร้า", "sad": return .blue
        case "โกรธ", "angry": return .red
        case "ตื่นเต้น", "excited": return .orange
        case "กังวล", "anxious": return .purple
        default: return .angelaPurple
        }
    }
}

// Fallback simple bar chart for iOS 15
struct SimpleBarChart: View {
    let data: [EmotionTrendsView.DayEmotion]

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            ForEach(data) { item in
                VStack(spacing: 4) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color.angelaPurple)
                        .frame(width: 40, height: CGFloat(item.averageIntensity) * 20)
                    Text(item.dayName)
                        .font(.caption2)
                        .lineLimit(1)
                }
            }
        }
        .padding()
    }
}

#Preview {
    EmotionTrendsView()
        .environmentObject(DatabaseService.shared)
}
