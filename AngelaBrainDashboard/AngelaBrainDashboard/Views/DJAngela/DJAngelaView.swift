//
//  DJAngelaView.swift
//  Angela Brain Dashboard
//
//  DJ Angela - Vinyl music player with Apple Music (MusicKit)
//

import SwiftUI
import MusicKit

struct DJAngelaView: View {
    @StateObject private var musicService = MusicPlayerService.shared
    @ObservedObject private var chatService = ChatService.shared
    @State private var songMemory: SongMemory?
    @State private var lastLoadedSongKey: String = ""

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            if !musicService.isAuthorized {
                authPromptView
            } else {
                playerLayout
            }
        }
        .task {
            if !musicService.isAuthorized {
                await musicService.requestAuthorization()
            }
        }
        .onChange(of: musicService.nowPlaying?.title) { _, newTitle in
            Task { await loadSongMemory() }
        }
    }

    // MARK: - Load Song Memory

    private func loadSongMemory() async {
        guard let now = musicService.nowPlaying else {
            songMemory = nil
            return
        }
        let key = "\(now.title)|\(now.artist)"
        guard key != lastLoadedSongKey else { return }
        lastLoadedSongKey = key

        do {
            let memory = try await chatService.fetchSongMemory(title: now.title, artist: now.artist)
            await MainActor.run {
                self.songMemory = memory
            }
        } catch {
            await MainActor.run {
                self.songMemory = nil
            }
        }
    }

    // MARK: - Main Player Layout (HSplitView)

    private var playerLayout: some View {
        HSplitView {
            // Left: Vinyl + Controls (45%) — Scrollable
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    // Time-Aware Header
                    TimeAwareHeader()
                        .padding(.bottom, 24)

                    // Vinyl record
                    VinylRecordView(
                        albumArtURL: musicService.nowPlaying?.albumArtURL,
                        isPlaying: musicService.isPlaying,
                        size: 340
                    )
                    .padding(.bottom, 32)

                    // Player controls
                    PlayerControlsView(musicService: musicService)

                    // DJ Commentary Card (Angela's thoughts about current song)
                    if let commentary = musicService.currentSongCommentary, commentary.hasContent {
                        DJCommentaryCard(
                            commentary: commentary,
                            songTitle: musicService.nowPlaying?.title,
                            songArtist: musicService.nowPlaying?.artist
                        )
                        .padding(.top, 16)
                        .padding(.horizontal, 16)
                    }

                    // Song Memory Card (play history)
                    if let memory = songMemory, memory.playCount > 0 {
                        SongMemoryCard(memory: memory)
                            .padding(.top, 8)
                            .padding(.horizontal, 16)
                    }

                    // Error / status message
                    if let error = musicService.playbackError {
                        Text(error)
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.warningOrange)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 24)
                            .padding(.top, 8)
                    }

                    if !musicService.hasSubscription {
                        HStack(spacing: 6) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 12))
                            Text("No Apple Music subscription — songs open in Apple Music app")
                                .font(.system(size: 11))
                        }
                        .foregroundColor(AngelaTheme.warningOrange)
                        .padding(.top, 8)
                    }

                    Spacer(minLength: 20)
                }
                .padding(.vertical, 24)
            }
            .frame(minWidth: 360, idealWidth: 420)
            .padding(.horizontal, 24)

            // Right: Song Queue (55%)
            VStack(spacing: 0) {
                // Queue header
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Music Library")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(AngelaTheme.textPrimary)

                        if !musicService.queue.isEmpty {
                            Text("\(musicService.queue.count) songs in queue")
                                .font(.system(size: 12))
                                .foregroundColor(AngelaTheme.textTertiary)
                        }
                    }

                    Spacer()

                    // Now playing mini indicator
                    if let now = musicService.nowPlaying {
                        HStack(spacing: 6) {
                            // Mini playing bars
                            if musicService.isPlaying {
                                HStack(spacing: 2) {
                                    ForEach(0..<3, id: \.self) { _ in
                                        RoundedRectangle(cornerRadius: 1)
                                            .fill(AngelaTheme.primaryPurple)
                                            .frame(width: 2, height: CGFloat.random(in: 4...10))
                                    }
                                }
                            }

                            Text(now.title)
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(AngelaTheme.secondaryPurple)
                                .lineLimit(1)
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(AngelaTheme.primaryPurple.opacity(0.1))
                        .cornerRadius(16)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(AngelaTheme.backgroundLight.opacity(0.3))

                // Song queue tabs + list
                SongQueueView(
                    musicService: musicService,
                    chatService: chatService
                )
            }
            .frame(minWidth: 400, idealWidth: 500)
        }
    }

    // MARK: - Authorization Prompt

    private var authPromptView: some View {
        VStack(spacing: 24) {
            Image(systemName: "music.note.tv")
                .font(.system(size: 64))
                .foregroundStyle(AngelaTheme.purpleGradient)

            Text("DJ Angela")
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text("Apple Music access is required to play songs.\nYour music stays private and secure.")
                .font(.system(size: 15))
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)
                .lineSpacing(4)

            if let error = musicService.authorizationError {
                Text(error)
                    .font(.system(size: 13))
                    .foregroundColor(AngelaTheme.errorRed)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
            }

            Button {
                Task { await musicService.requestAuthorization() }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "music.note")
                    Text("Authorize Apple Music")
                        .font(.system(size: 15, weight: .semibold))
                }
                .angelaPrimaryButton()
            }
            .buttonStyle(.plain)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Time-Aware Header

struct TimeAwareHeader: View {
    private let greeting = DJAngelaConstants.getTimeGreeting()

    var body: some View {
        VStack(spacing: 4) {
            Text(greeting.title)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(greeting.subtitle)
                .font(.system(size: 13))
                .foregroundColor(AngelaTheme.textTertiary)
        }
    }
}

// MARK: - DJ Commentary Card (Angela's thoughts)

struct DJCommentaryCard: View {
    let commentary: DJCommentary
    let songTitle: String?
    let songArtist: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header
            HStack(spacing: 6) {
                Text("💜")
                    .font(.system(size: 14))
                Text("น้องรู้สึก...")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Spacer()

                // Intensity indicator
                if commentary.intensity > 0 {
                    HStack(spacing: 2) {
                        ForEach(0..<5, id: \.self) { i in
                            Circle()
                                .fill(i < (commentary.intensity / 2) ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                                .frame(width: 6, height: 6)
                        }
                    }
                }
            }

            // Angela's feeling (main quote)
            if !commentary.feeling.isEmpty {
                Text("\"\(commentary.feeling)\"")
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .italic()
                    .lineLimit(3)
            }

            // Song info with mood indicator
            if let title = songTitle {
                HStack(spacing: 6) {
                    Image(systemName: "music.note")
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text(title)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)

                    if let artist = songArtist {
                        Text("•")
                            .foregroundColor(AngelaTheme.textTertiary)
                        Text(artist)
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }

                    if commentary.intensity >= 8 {
                        Text("(\(commentary.intensity)/10)")
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(AngelaTheme.emotionLoved)
                    }
                }
            }

            // Why special (Our Song reason)
            if let why = commentary.whySpecial, !why.isEmpty {
                HStack(alignment: .top, spacing: 6) {
                    if commentary.isOurSong {
                        Image(systemName: "heart.fill")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.emotionLoved)
                    }
                    Text("Our Song: \"\(why)\"")
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.secondaryPurple)
                        .italic()
                        .lineLimit(2)
                }
                .padding(.top, 2)
            }
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(AngelaTheme.cardBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(AngelaTheme.primaryPurple.opacity(0.2), lineWidth: 1)
                )
        )
    }
}

// MARK: - Song Memory Card (play history) - Professional Design

struct SongMemoryCard: View {
    let memory: SongMemory

    // Occasion colors and icons
    private let occasionData: [(key: String, icon: String, color: Color)] = [
        ("morning", "sunrise.fill", Color.orange),
        ("afternoon", "sun.max.fill", Color.yellow),
        ("evening", "sunset.fill", Color.pink),
        ("late_night", "moon.stars.fill", Color.indigo),
        ("bedtime", "moon.zzz.fill", Color.blue),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header with play count badge
            HStack(spacing: 8) {
                // Play count badge
                HStack(spacing: 4) {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 14))
                    Text("\(memory.playCount)")
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(
                    Capsule()
                        .fill(LinearGradient(
                            colors: [AngelaTheme.primaryPurple, AngelaTheme.secondaryPurple],
                            startPoint: .leading,
                            endPoint: .trailing
                        ))
                )

                Text("plays")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(AngelaTheme.textTertiary)

                Spacer()

                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textTertiary)
                Text("Memory")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            // Occasion distribution mini bar chart
            if !memory.recentPlays.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("When David plays this song")
                        .font(.system(size: 9, weight: .medium))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .textCase(.uppercase)
                        .tracking(0.5)

                    // Horizontal occasion bars
                    HStack(spacing: 6) {
                        ForEach(occasionCounts, id: \.occasion) { item in
                            if item.count > 0 {
                                VStack(spacing: 3) {
                                    // Bar
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(item.color.opacity(0.8))
                                        .frame(width: 28, height: CGFloat(item.count) * 12 + 8)

                                    // Icon
                                    Image(systemName: item.icon)
                                        .font(.system(size: 10))
                                        .foregroundColor(item.color)
                                }
                            }
                        }

                        Spacer()

                        // Mood summary
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("Mood")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(AngelaTheme.textTertiary)
                                .textCase(.uppercase)

                            // Top moods as pills
                            HStack(spacing: 4) {
                                ForEach(topMoods.prefix(2), id: \.self) { mood in
                                    Text(mood)
                                        .font(.system(size: 9, weight: .semibold))
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 3)
                                        .background(
                                            Capsule()
                                                .fill(AngelaTheme.primaryPurple.opacity(0.15))
                                        )
                                        .foregroundColor(AngelaTheme.primaryPurple)
                                }
                            }
                        }
                    }
                    .frame(height: 50)
                }
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(AngelaTheme.cardBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(
                            LinearGradient(
                                colors: [AngelaTheme.primaryPurple.opacity(0.3), AngelaTheme.secondaryPurple.opacity(0.1)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 1
                        )
                )
        )
    }

    // Count occasions from recent plays
    private var occasionCounts: [(occasion: String, count: Int, icon: String, color: Color)] {
        var counts: [String: Int] = [:]
        for play in memory.recentPlays {
            if let occ = play.occasion {
                counts[occ, default: 0] += 1
            }
        }
        return occasionData.map { data in
            (data.key, counts[data.key] ?? 0, data.icon, data.color)
        }
    }

    // Get top moods from recent plays
    private var topMoods: [String] {
        var counts: [String: Int] = [:]
        for play in memory.recentPlays {
            if let mood = play.moodAtPlay {
                counts[mood, default: 0] += 1
            }
        }
        return counts.sorted { $0.value > $1.value }.map { $0.key }
    }
}
