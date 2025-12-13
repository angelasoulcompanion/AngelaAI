//
//  MemoriesView.swift
//  Angela Brain Dashboard
//
//  💜 Memories View - Beautiful Conversation Timeline 💜
//

import SwiftUI
import Combine

struct MemoriesView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = MemoriesViewModel()
    @State private var searchText = ""

    var body: some View {
        VStack(spacing: 0) {
            // Header with search
            header

            // Conversation list
            ScrollView {
                LazyVStack(spacing: AngelaTheme.spacing) {
                    ForEach(filteredConversations) { conversation in
                        ConversationBubble(conversation: conversation)
                    }
                }
                .padding(AngelaTheme.largeSpacing)
            }
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    private var filteredConversations: [Conversation] {
        if searchText.isEmpty {
            return viewModel.conversations
        }
        return viewModel.conversations.filter {
            $0.messageText.localizedCaseInsensitiveContains(searchText) ||
            $0.topic?.localizedCaseInsensitiveContains(searchText) ?? false
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: AngelaTheme.spacing) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Memories")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("\(viewModel.conversations.count) conversations")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()
            }

            // Search bar
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(AngelaTheme.textTertiary)

                TextField("Search conversations...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(12)
            .background(AngelaTheme.backgroundLight)
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }
}

// MARK: - Conversation Bubble Component

struct ConversationBubble: View {
    let conversation: Conversation

    private var speakerColor: Color {
        conversation.isDavid ? AngelaTheme.accentGold : AngelaTheme.primaryPurple
    }

    private var speakerIcon: String {
        conversation.isDavid ? "person.fill" : "brain.head.profile"
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Avatar
            ZStack {
                Circle()
                    .fill(speakerColor.opacity(0.2))
                    .frame(width: 40, height: 40)

                Image(systemName: speakerIcon)
                    .font(.system(size: 16))
                    .foregroundColor(speakerColor)
            }

            // Message content
            VStack(alignment: .leading, spacing: 8) {
                // Speaker name + time
                HStack {
                    Text(conversation.speaker.capitalized)
                        .font(AngelaTheme.body())
                        .fontWeight(.semibold)
                        .foregroundColor(speakerColor)

                    Text("•")
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text(conversation.createdAt, style: .relative)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    Spacer()

                    // Importance indicator
                    if conversation.importanceLevel >= 8 {
                        HStack(spacing: 2) {
                            ForEach(Array(0..<10).prefix(min(conversation.importanceLevel, 10)), id: \.self) { _ in
                                Image(systemName: "star.fill")
                                    .font(.system(size: 8))
                            }
                        }
                        .foregroundColor(AngelaTheme.accentGold)
                    }
                }

                // Message text
                Text(conversation.messageText)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .fixedSize(horizontal: false, vertical: true)

                // Topic + Emotion tags
                HStack(spacing: 8) {
                    if let topic = conversation.topic {
                        TagView(text: topic, color: AngelaTheme.primaryPurple)
                    }

                    if let emotion = conversation.emotionDetected {
                        TagView(text: emotion, color: AngelaTheme.emotionLoved)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(
            LinearGradient(
                colors: [speakerColor.opacity(0.05), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(speakerColor.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - Tag View Component

struct TagView: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text)
            .font(.system(size: 11, weight: .medium))
            .foregroundColor(color)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.15))
            .cornerRadius(6)
    }
}

// MARK: - View Model

@MainActor
class MemoriesViewModel: ObservableObject {
    @Published var conversations: [Conversation] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            conversations = try await databaseService.fetchRecentConversations(limit: 100)
        } catch {
            print("Error loading conversations: \(error)")
        }

        isLoading = false
    }
}
