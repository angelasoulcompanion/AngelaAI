//
//  PlayerControlsView.swift
//  Angela Brain Dashboard
//
//  Play/pause/skip controls + progress bar for DJ Angela
//

import SwiftUI

struct PlayerControlsView: View {
    @ObservedObject var musicService: MusicPlayerService
    @State private var isDragging = false
    @State private var dragProgress: Double = 0

    private let activities: [(key: String, emoji: String, label: String)] = [
        ("wine", "🍷", "Wine"),
        ("working", "💻", "Work"),
        ("relaxing", "😌", "Relax"),
        ("exercise", "🏋️", "Gym"),
        ("driving", "🚗", "Drive"),
        ("party", "🎉", "Party"),
        ("sleep", "😴", "Sleep"),
    ]

    var body: some View {
        VStack(spacing: 16) {
            // Song info
            songInfoSection

            // Progress bar
            progressSection

            // Controls
            controlsSection

            // Activity picker
            activityPickerSection
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
    }

    // MARK: - Song Info

    private var songInfoSection: some View {
        VStack(spacing: 4) {
            if let now = musicService.nowPlaying {
                Text(now.title)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                Text(now.artist)
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(1)
            } else {
                Text("No Song Playing")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(AngelaTheme.textTertiary)

                Text("Select a song to start")
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
    }

    // MARK: - Progress Bar

    private var progressSection: some View {
        VStack(spacing: 4) {
            // Draggable progress bar
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    // Track
                    Capsule()
                        .fill(Color.white.opacity(0.1))
                        .frame(height: 4)

                    // Filled portion
                    Capsule()
                        .fill(AngelaTheme.purpleGradient)
                        .frame(width: geo.size.width * currentProgress, height: 4)

                    // Drag handle (visible on hover/drag)
                    Circle()
                        .fill(Color.white)
                        .frame(width: 12, height: 12)
                        .offset(x: geo.size.width * currentProgress - 6)
                        .opacity(isDragging ? 1 : 0)
                }
                .frame(height: 12)
                .contentShape(Rectangle())
                .gesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { value in
                            isDragging = true
                            let progress = min(max(value.location.x / geo.size.width, 0), 1)
                            dragProgress = progress
                        }
                        .onEnded { value in
                            isDragging = false
                            let progress = min(max(value.location.x / geo.size.width, 0), 1)
                            if let duration = musicService.nowPlaying?.duration, duration > 0 {
                                Task {
                                    await musicService.seekTo(duration * progress)
                                }
                            }
                        }
                )
                .onHover { hovering in
                    if !isDragging && !hovering {
                        // Reset hover state
                    }
                }
            }
            .frame(height: 12)

            // Time labels
            HStack {
                Text(musicService.nowPlaying?.currentTimeFormatted ?? "0:00")
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundColor(AngelaTheme.textTertiary)

                Spacer()

                Text(musicService.nowPlaying?.durationFormatted ?? "0:00")
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
    }

    private var currentProgress: Double {
        if isDragging { return dragProgress }
        return musicService.nowPlaying?.progress ?? 0
    }

    // MARK: - Playback Controls

    private var controlsSection: some View {
        HStack(spacing: 32) {
            // Previous
            Button {
                Task { await musicService.skipToPrevious() }
            } label: {
                Image(systemName: "backward.fill")
                    .font(.system(size: 22))
                    .foregroundColor(musicService.queue.isEmpty ? AngelaTheme.textTertiary : AngelaTheme.textPrimary)
            }
            .buttonStyle(.plain)
            .disabled(musicService.queue.isEmpty)

            // Play / Pause
            Button {
                Task { await musicService.togglePlayPause() }
            } label: {
                ZStack {
                    Circle()
                        .fill(AngelaTheme.purpleGradient)
                        .frame(width: 52, height: 52)

                    Image(systemName: musicService.isPlaying ? "pause.fill" : "play.fill")
                        .font(.system(size: 22))
                        .foregroundColor(.white)
                        .offset(x: musicService.isPlaying ? 0 : 2)  // visual center for play icon
                }
            }
            .buttonStyle(.plain)
            .disabled(musicService.nowPlaying == nil && musicService.queue.isEmpty)

            // Next
            Button {
                Task { await musicService.skipToNext() }
            } label: {
                Image(systemName: "forward.fill")
                    .font(.system(size: 22))
                    .foregroundColor(musicService.queue.isEmpty ? AngelaTheme.textTertiary : AngelaTheme.textPrimary)
            }
            .buttonStyle(.plain)
            .disabled(musicService.queue.isEmpty)
        }
    }

    // MARK: - Activity Picker

    private var activityPickerSection: some View {
        let selected = musicService.currentActivity
        let isOurSong = musicService.currentSongIsOurSong

        return VStack(spacing: 6) {
            // Row 1: Our Song + first 4 activities
            HStack(spacing: 8) {
                // Our Song chip
                Button {
                    musicService.toggleOurSong()
                } label: {
                    chipLabel("💜", "Our Song", highlighted: isOurSong)
                }
                .buttonStyle(.plain)
                .disabled(musicService.nowPlaying == nil)

                ForEach(Array(activities.prefix(4)), id: \.key) { item in
                    Button {
                        musicService.currentActivity = (selected == item.key) ? nil : item.key
                    } label: {
                        chipLabel(item.emoji, item.label, highlighted: selected == item.key)
                    }
                    .buttonStyle(.plain)
                }
            }
            // Row 2: remaining activities
            HStack(spacing: 8) {
                ForEach(Array(activities.suffix(3)), id: \.key) { item in
                    Button {
                        musicService.currentActivity = (selected == item.key) ? nil : item.key
                    } label: {
                        chipLabel(item.emoji, item.label, highlighted: selected == item.key)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func chipLabel(_ emoji: String, _ label: String, highlighted: Bool) -> some View {
        HStack(spacing: 4) {
            Text(emoji)
                .font(.system(size: 12))
            Text(label)
                .font(.system(size: 11, weight: .medium))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(
            Capsule().fill(highlighted ? Color.purple : Color.white.opacity(0.08))
        )
        .foregroundColor(highlighted ? .white : AngelaTheme.textSecondary)
    }
}
