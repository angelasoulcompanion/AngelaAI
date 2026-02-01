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
    }

    // MARK: - Main Player Layout (HSplitView)

    private var playerLayout: some View {
        HSplitView {
            // Left: Vinyl + Controls (45%)
            VStack(spacing: 0) {
                Spacer()

                // Header
                VStack(spacing: 4) {
                    Text("DJ Angela")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("Your personal music companion")
                        .font(.system(size: 13))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
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

                Spacer()
            }
            .frame(minWidth: 360, idealWidth: 420)
            .padding(24)

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
