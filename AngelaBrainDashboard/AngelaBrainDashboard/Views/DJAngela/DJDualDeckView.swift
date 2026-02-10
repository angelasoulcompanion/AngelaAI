//
//  DJDualDeckView.swift
//  Angela Brain Dashboard
//
//  Container: Deck A + Crossfader + Deck B
//

import SwiftUI

struct DJDualDeckView: View {
    @ObservedObject var musicService: MusicPlayerService

    private let vinylSize: CGFloat = 200

    var body: some View {
        HStack(alignment: .center, spacing: 12) {
            // Deck A
            DeckView(
                deck: .A,
                state: musicService.deckA,
                isPlaying: musicService.isPlaying,
                vinylSize: vinylSize
            )

            // Crossfader
            CrossfaderView(
                musicService: musicService,
                height: vinylSize * 0.8
            )

            // Deck B
            DeckView(
                deck: .B,
                state: musicService.deckB,
                isPlaying: musicService.isPlaying,
                vinylSize: vinylSize
            )
        }
    }
}

// MARK: - Transition Mode Picker

struct TransitionModePickerView: View {
    @ObservedObject var musicService: MusicPlayerService

    var body: some View {
        HStack(spacing: 8) {
            ForEach(TransitionMode.allCases, id: \.rawValue) { mode in
                Button {
                    withAnimation(.spring(response: 0.3)) {
                        musicService.transitionMode = mode
                    }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: mode.icon)
                            .font(.system(size: 10))
                        Text(mode.label)
                            .font(.system(size: 10, weight: .medium))
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(
                        Capsule()
                            .fill(musicService.transitionMode == mode
                                  ? AngelaTheme.primaryPurple
                                  : Color.white.opacity(0.08))
                    )
                    .foregroundColor(musicService.transitionMode == mode
                                     ? .white
                                     : AngelaTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
        }
    }
}
