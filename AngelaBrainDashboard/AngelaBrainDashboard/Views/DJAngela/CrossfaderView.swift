//
//  CrossfaderView.swift
//  Angela Brain Dashboard
//
//  Vertical crossfader between Deck A and Deck B
//

import SwiftUI

struct CrossfaderView: View {
    @ObservedObject var musicService: MusicPlayerService
    let height: CGFloat

    @State private var isDragging = false
    @State private var dragOffset: CGFloat = 0

    private let trackWidth: CGFloat = 6
    private let knobSize: CGFloat = 28
    private let threshold: Double = 0.85  // 85% = trigger transition

    var body: some View {
        VStack(spacing: 6) {
            // "A" indicator
            deckIndicator("A", isActive: musicService.activeDeck == .A)

            // Track + knob
            GeometryReader { geo in
                let trackHeight = geo.size.height
                let usableHeight = trackHeight - knobSize
                let knobY = usableHeight * musicService.crossfaderPosition

                ZStack(alignment: .top) {
                    // Track background
                    Capsule()
                        .fill(Color.white.opacity(0.08))
                        .frame(width: trackWidth, height: trackHeight)

                    // Glow track (shows proximity to threshold)
                    Capsule()
                        .fill(glowColor)
                        .frame(width: trackWidth, height: trackHeight)
                        .opacity(glowIntensity)

                    // Center line
                    Rectangle()
                        .fill(AngelaTheme.textTertiary.opacity(0.3))
                        .frame(width: 12, height: 1)
                        .offset(y: usableHeight / 2 + knobSize / 2)

                    // Knob
                    knobView
                        .offset(y: knobY)
                        .gesture(
                            DragGesture(minimumDistance: 0)
                                .onChanged { value in
                                    isDragging = true
                                    let newPos = min(max(value.location.y / usableHeight, 0), 1)
                                    musicService.crossfaderPosition = newPos
                                    checkThreshold(newPos)
                                }
                                .onEnded { _ in
                                    isDragging = false
                                    handleDragEnd()
                                }
                        )
                }
                .frame(width: knobSize, height: trackHeight)
            }
            .frame(width: knobSize, height: height)

            // "B" indicator
            deckIndicator("B", isActive: musicService.activeDeck == .B)
        }
    }

    // MARK: - Knob

    private var knobView: some View {
        ZStack {
            // Outer glow
            Circle()
                .fill(AngelaTheme.primaryPurple.opacity(0.3))
                .frame(width: knobSize + 8, height: knobSize + 8)
                .blur(radius: 4)
                .opacity(isDragging ? 1 : 0)

            // Knob body
            Circle()
                .fill(
                    RadialGradient(
                        colors: [
                            Color.white,
                            Color(hex: "C0C0C0")
                        ],
                        center: .center,
                        startRadius: 0,
                        endRadius: knobSize / 2
                    )
                )
                .frame(width: knobSize, height: knobSize)
                .shadow(color: Color.black.opacity(0.4), radius: 3, y: 2)

            // Center groove
            Circle()
                .fill(Color.gray.opacity(0.3))
                .frame(width: 6, height: 6)
        }
        .scaleEffect(isDragging ? 1.15 : 1.0)
        .animation(.spring(response: 0.2), value: isDragging)
    }

    // MARK: - Deck Indicator

    private func deckIndicator(_ label: String, isActive: Bool) -> some View {
        Text(label)
            .font(.system(size: 11, weight: .bold, design: .rounded))
            .foregroundColor(isActive ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary)
    }

    // MARK: - Threshold Logic

    private var glowIntensity: Double {
        let pos = musicService.crossfaderPosition
        // Glow when approaching either extreme
        let distFromCenter = abs(pos - 0.5) * 2  // 0 at center, 1 at edges
        return max(distFromCenter - 0.5, 0) * 2  // Start glowing past 75%
    }

    private var glowColor: Color {
        musicService.crossfaderPosition < 0.5
            ? Color.blue.opacity(0.4)
            : AngelaTheme.primaryPurple.opacity(0.4)
    }

    private func checkThreshold(_ position: Double) {
        guard !musicService.isTransitioning else { return }

        // Manual crossfader works in ALL modes (instant, smooth, autoMix).
        // The mode affects transition *style*, not whether manual control works.
        // Auto-mix also auto-triggers at 10s before song end (via updatePosition).
        if position <= (1.0 - threshold) && musicService.activeDeck == .B {
            Task { await musicService.performTransition(to: .A) }
        } else if position >= threshold && musicService.activeDeck == .A {
            Task { await musicService.performTransition(to: .B) }
        }
    }

    private func handleDragEnd() {
        // Snap back to center if no transition happened
        if !musicService.isTransitioning {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                musicService.crossfaderPosition = 0.5
            }
        }
    }
}
