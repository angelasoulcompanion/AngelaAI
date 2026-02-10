//
//  DeckView.swift
//  Angela Brain Dashboard
//
//  Single turntable deck — vinyl + song info + active indicator
//

import SwiftUI

struct DeckView: View {
    let deck: DeckSide
    let state: DeckState
    let isPlaying: Bool
    let vinylSize: CGFloat

    @State private var pulseGlow = false
    @State private var loadFlash = false

    var body: some View {
        VStack(spacing: 8) {
            // Deck label
            deckLabel

            // Vinyl record with active glow
            ZStack {
                // Active glow ring (playing)
                if state.isActive {
                    Circle()
                        .stroke(
                            AngelaTheme.primaryPurple.opacity(pulseGlow ? 0.6 : 0.3),
                            lineWidth: 3
                        )
                        .frame(width: vinylSize + 10, height: vinylSize + 10)
                        .blur(radius: 4)
                        .animation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true), value: pulseGlow)
                }

                // Load flash ring (brief green flash when song is loaded)
                if loadFlash {
                    Circle()
                        .stroke(AngelaTheme.successGreen, lineWidth: 3)
                        .frame(width: vinylSize + 10, height: vinylSize + 10)
                        .blur(radius: 6)
                        .transition(.opacity)
                }

                VinylRecordView(
                    albumArtURL: state.song?.albumArtURL,
                    isPlaying: state.isActive && isPlaying,
                    size: vinylSize
                )
            }
            .opacity(state.song == nil ? 0.35 : 1.0)

            // Song info
            VStack(spacing: 2) {
                if let song = state.song {
                    Text(song.title)
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(state.isActive ? AngelaTheme.textPrimary : AngelaTheme.textSecondary)
                        .lineLimit(1)

                    Text(song.artist)
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)

                    // "READY" badge for loaded (not playing) songs
                    if state.playState == .loaded && !state.isActive {
                        Text("READY")
                            .font(.system(size: 8, weight: .bold))
                            .tracking(1)
                            .foregroundColor(AngelaTheme.successGreen)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(
                                Capsule()
                                    .fill(AngelaTheme.successGreen.opacity(0.15))
                            )
                            .padding(.top, 2)
                    }
                } else {
                    Text("Empty")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text("Load a song")
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary.opacity(0.6))
                }
            }
            .frame(maxWidth: vinylSize)
        }
        .onAppear {
            if state.isActive {
                pulseGlow = true
            }
        }
        .onChange(of: state.isActive) { _, newValue in
            pulseGlow = newValue
        }
        .onChange(of: state.song?.title) { _, newTitle in
            // Flash when a song is loaded to this deck (not active = newly loaded)
            if newTitle != nil && !state.isActive {
                triggerLoadFlash()
            }
        }
    }

    // MARK: - Deck Label

    private var deckLabel: some View {
        Text("DECK \(deck.rawValue)")
            .font(.system(size: 9, weight: .bold))
            .tracking(1.5)
            .foregroundColor(state.isActive ? .white : AngelaTheme.textTertiary)
            .padding(.horizontal, 10)
            .padding(.vertical, 3)
            .background(
                Capsule()
                    .fill(state.isActive ? AngelaTheme.primaryPurple : Color.white.opacity(0.08))
            )
    }

    // MARK: - Load Flash Animation

    private func triggerLoadFlash() {
        withAnimation(.easeIn(duration: 0.2)) {
            loadFlash = true
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
            withAnimation(.easeOut(duration: 0.4)) {
                loadFlash = false
            }
        }
    }
}
