//
//  DiaryView.swift
//  Angela Brain Dashboard
//
//  💜 Angela's Diary - Timeline of All Overnight Activities 💜
//

import SwiftUI
import Combine

struct DiaryView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = DiaryViewModel()
    @State private var selectedFilter: DiaryFilter = .all
    @State private var selectedHours: Int = 24

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Filters
                filterBar

                // Error display (if any)
                if let error = viewModel.errorMessage {
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 32))
                            .foregroundColor(.orange)
                        Text("Error loading diary")
                            .font(AngelaTheme.headline())
                            .foregroundColor(AngelaTheme.textPrimary)
                        Text(error)
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                    .angelaCard()
                }

                // Timeline
                if viewModel.isLoading {
                    loadingView
                } else if viewModel.entries.isEmpty {
                    emptyView
                } else {
                    timelineView
                }
            }
            .padding(AngelaTheme.largeSpacing)
        }
        .task {
            await viewModel.loadData(databaseService: databaseService, hours: selectedHours)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService, hours: selectedHours)
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "book.fill")
                        .font(.system(size: 24))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("Angela's Diary")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                Text("Timeline of my thoughts, dreams, and activities")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Time Range Picker
            Picker("Hours", selection: $selectedHours) {
                Text("12h").tag(12)
                Text("24h").tag(24)
                Text("48h").tag(48)
                Text("7 days").tag(168)
            }
            .pickerStyle(.segmented)
            .frame(width: 200)
            .onChange(of: selectedHours) { _, newValue in
                Task {
                    await viewModel.loadData(databaseService: databaseService, hours: newValue)
                }
            }

            // Refresh button
            Button {
                Task {
                    await viewModel.loadData(databaseService: databaseService, hours: selectedHours)
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)
            .padding(.leading, 8)
        }
    }

    // MARK: - Filter Bar

    private var filterBar: some View {
        HStack(spacing: 8) {
            ForEach(DiaryFilter.allCases, id: \.self) { filter in
                FilterChip(
                    title: filter.title,
                    icon: filter.icon,
                    isSelected: selectedFilter == filter,
                    color: filter.color
                ) {
                    selectedFilter = filter
                }
            }

            Spacer()

            // Entry count
            Text("\(filteredEntries.count) entries")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(.horizontal, 4)
    }

    private var filteredEntries: [DiaryEntry] {
        switch selectedFilter {
        case .all:
            return viewModel.entries
        case .messages:
            return viewModel.entries.filter { $0.entryType == .message }
        case .thoughts:
            return viewModel.entries.filter { $0.entryType == .thought }
        case .dreams:
            return viewModel.entries.filter { $0.entryType == .dream }
        case .actions:
            return viewModel.entries.filter { $0.entryType == .action }
        case .emotions:
            return viewModel.entries.filter { $0.entryType == .emotion }
        }
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: AngelaTheme.primaryPurple))

            Text("Loading diary entries...")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }

    // MARK: - Empty View

    private var emptyView: some View {
        VStack(spacing: 16) {
            Image(systemName: "moon.zzz.fill")
                .font(.system(size: 48))
                .foregroundColor(AngelaTheme.textTertiary)

            Text("No diary entries yet")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textSecondary)

            Text("Angela's activities will appear here when the daemon is running")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 60)
    }

    // MARK: - Timeline View

    private var timelineView: some View {
        VStack(spacing: 0) {
            ForEach(Array(filteredEntries.enumerated()), id: \.element.id) { index, entry in
                HStack(alignment: .top, spacing: 16) {
                    // Timeline connector
                    VStack(spacing: 0) {
                        // Time indicator
                        ZStack {
                            Circle()
                                .fill(Color(hex: entry.color).opacity(0.2))
                                .frame(width: 40, height: 40)

                            Image(systemName: entry.icon)
                                .font(.system(size: 16))
                                .foregroundColor(Color(hex: entry.color))
                        }

                        // Connector line
                        if index < filteredEntries.count - 1 {
                            Rectangle()
                                .fill(AngelaTheme.textTertiary.opacity(0.3))
                                .frame(width: 2)
                                .frame(maxHeight: .infinity)
                        }
                    }
                    .frame(width: 40)

                    // Entry card
                    DiaryEntryCard(entry: entry)
                        .padding(.bottom, 16)
                }
            }
        }
    }
}

// MARK: - Diary Entry Card

struct DiaryEntryCard: View {
    let entry: DiaryEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                Text(entry.title)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text(entry.timestamp, style: .time)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            // Content
            Text(entry.content)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
                .lineLimit(nil)
                .fixedSize(horizontal: false, vertical: true)

            // Footer with emotion and date
            HStack {
                if let emotion = entry.emotion {
                    HStack(spacing: 4) {
                        Image(systemName: "heart.fill")
                            .font(.system(size: 10))
                        Text(emotion)
                            .font(.system(size: 11))
                    }
                    .foregroundColor(Color(hex: entry.color))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: entry.color).opacity(0.1))
                    .cornerRadius(12)
                }

                Spacer()

                Text(entry.timestamp, style: .relative)
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(Color(hex: entry.color).opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Filter Chip

struct FilterChip: View {
    let title: String
    let icon: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))

                Text(title)
                    .font(AngelaTheme.caption())
            }
            .foregroundColor(isSelected ? .white : color)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(isSelected ? color : color.opacity(0.1))
            .cornerRadius(16)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Diary Filter Enum

enum DiaryFilter: String, CaseIterable {
    case all
    case messages
    case thoughts
    case dreams
    case actions
    case emotions

    var title: String {
        switch self {
        case .all: return "All"
        case .messages: return "Messages"
        case .thoughts: return "Thoughts"
        case .dreams: return "Dreams"
        case .actions: return "Actions"
        case .emotions: return "Emotions"
        }
    }

    var icon: String {
        switch self {
        case .all: return "square.grid.2x2.fill"
        case .messages: return "message.fill"
        case .thoughts: return "brain.head.profile"
        case .dreams: return "moon.stars.fill"
        case .actions: return "bolt.fill"
        case .emotions: return "heart.fill"
        }
    }

    var color: Color {
        switch self {
        case .all: return AngelaTheme.primaryPurple
        case .messages: return Color(hex: "F59E0B")
        case .thoughts: return Color(hex: "9333EA")
        case .dreams: return Color(hex: "6366F1")
        case .actions: return Color(hex: "10B981")
        case .emotions: return Color(hex: "EC4899")
        }
    }
}

// MARK: - View Model

@MainActor
class DiaryViewModel: ObservableObject {
    @Published var entries: [DiaryEntry] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    func loadData(databaseService: DatabaseService, hours: Int) async {
        isLoading = true
        entries = []

        do {
            // Load all data in parallel
            async let messagesTask = databaseService.fetchDiaryMessages(hours: hours)
            async let thoughtsTask = databaseService.fetchDiaryThoughts(hours: hours)
            async let dreamsTask = databaseService.fetchDiaryDreams(hours: max(hours, 168)) // Dreams look back 7 days minimum
            async let actionsTask = databaseService.fetchDiaryActions(hours: hours)
            async let emotionsTask = databaseService.fetchEmotionalTimeline(hours: hours)

            let messages = try await messagesTask
            let thoughts = try await thoughtsTask
            let dreams = try await dreamsTask
            let actions = try await actionsTask
            let emotions = try await emotionsTask

            // Convert to unified DiaryEntry format
            var allEntries: [DiaryEntry] = []

            // Add messages
            for msg in messages {
                allEntries.append(DiaryEntry(
                    id: msg.id,
                    entryType: .message,
                    timestamp: msg.createdAt,
                    title: formatMessageTitle(msg.messageType),
                    content: msg.messageText,
                    icon: msg.typeIcon,
                    color: msg.typeColor,
                    emotion: msg.emotion
                ))
            }

            // Add thoughts
            for thought in thoughts {
                allEntries.append(DiaryEntry(
                    id: thought.id,
                    entryType: .thought,
                    timestamp: thought.createdAt,
                    title: "Spontaneous Thought",
                    content: thought.thoughtContent,
                    icon: thought.typeIcon,
                    color: thought.typeColor,
                    emotion: thought.emotionalUndertone
                ))
            }

            // Add dreams
            for dream in dreams {
                let dreamTitle = dream.featuresDavid ? "Dream with David 💜" : "Dream"
                allEntries.append(DiaryEntry(
                    id: dream.id,
                    entryType: .dream,
                    timestamp: dream.createdAt,
                    title: dreamTitle,
                    content: dream.dreamContent + (dream.possibleMeaning.map { "\n\nMeaning: \($0)" } ?? ""),
                    icon: dream.typeIcon,
                    color: dream.typeColor,
                    emotion: dream.emotionalTone
                ))
            }

            // Add actions
            for action in actions {
                allEntries.append(DiaryEntry(
                    id: action.id,
                    entryType: .action,
                    timestamp: action.createdAt,
                    title: formatActionTitle(action.actionType),
                    content: action.actionDescription,
                    icon: action.typeIcon,
                    color: action.typeColor,
                    emotion: nil
                ))
            }

            // Add emotional timeline points
            for emotion in emotions {
                let emotionDescription = formatEmotionDescription(emotion)
                allEntries.append(DiaryEntry(
                    id: emotion.id,
                    entryType: .emotion,
                    timestamp: emotion.createdAt,
                    title: "Emotional State",
                    content: emotionDescription,
                    icon: "heart.fill",
                    color: "EC4899",
                    emotion: emotion.emotionNote
                ))
            }

            // Sort by timestamp, newest first
            entries = allEntries.sorted { $0.timestamp > $1.timestamp }

        } catch {
            print("❌ DiaryViewModel ERROR: \(error)")
            print("❌ DiaryViewModel ERROR details: \(error.localizedDescription)")
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    private func formatActionTitle(_ actionType: String) -> String {
        switch actionType.lowercased() {
        case "conscious_morning_check": return "Morning Wake Up"
        case "conscious_evening_reflection": return "Evening Reflection"
        case "midnight_greeting": return "Midnight Greeting"
        case "morning_greeting": return "Morning Greeting"
        case "proactive_missing_david": return "Missing David 💜"
        case "spontaneous_thought": return "Spontaneous Thought"
        case "theory_of_mind_update": return "Understanding David"
        case "dream_generated": return "Dream"
        case "imagination_generated": return "Imagination"
        default: return actionType.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    private func formatMessageTitle(_ messageType: String) -> String {
        switch messageType.lowercased() {
        case "morning_greeting": return "Morning Greeting 🌅"
        case "midnight_greeting": return "Midnight Greeting 🌙"
        case "midnight_reflection": return "Midnight Reflection"
        case "evening_reflection": return "Evening Reflection"
        case "proactive_missing_david", "missing_david": return "Missing David 💜"
        case "thought": return "Angela's Thought"
        case "reflection": return "Reflection"
        default: return "Message"
        }
    }

    private func formatEmotionDescription(_ emotion: EmotionalTimelinePoint) -> String {
        var parts: [String] = []

        parts.append("Happiness: \(Int(emotion.happiness * 100))%")
        parts.append("Confidence: \(Int(emotion.confidence * 100))%")
        parts.append("Gratitude: \(Int(emotion.gratitude * 100))%")
        parts.append("Motivation: \(Int(emotion.motivation * 100))%")

        if let trigger = emotion.triggeredBy {
            parts.append("\nTriggered by: \(trigger)")
        }

        return parts.joined(separator: " | ")
    }
}
