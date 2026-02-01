//
//  VinylRecordView.swift
//  Angela Brain Dashboard
//
//  Spinning vinyl disc with album art + groove lines
//

import SwiftUI
import Combine

struct VinylRecordView: View {
    let albumArtURL: URL?
    let isPlaying: Bool
    let size: CGFloat

    // MARK: - Animation State

    @State private var rotationAngle: Double = 0
    @State private var angularVelocity: Double = 0  // degrees per frame
    private let targetSpeed: Double = 200.0 / 60.0  // 33.33 RPM = 200 deg/sec at 60fps
    private let timer = Timer.publish(every: 1.0 / 60.0, on: .main, in: .common).autoconnect()

    var body: some View {
        ZStack {
            // Ambient glow
            Circle()
                .fill(
                    RadialGradient(
                        colors: [
                            AngelaTheme.primaryPurple.opacity(isPlaying ? 0.3 : 0.1),
                            Color.clear
                        ],
                        center: .center,
                        startRadius: size * 0.4,
                        endRadius: size * 0.55
                    )
                )
                .frame(width: size * 1.1, height: size * 1.1)
                .animation(.easeInOut(duration: 0.8), value: isPlaying)

            // Vinyl disc (rotating)
            ZStack {
                // Base disc (dark)
                Circle()
                    .fill(Color(hex: "1A1A1A"))

                // Groove lines (concentric circles)
                ForEach(0..<20, id: \.self) { i in
                    let radius = size * 0.2 + (size * 0.25 * CGFloat(i) / 20.0)
                    Circle()
                        .stroke(
                            Color.white.opacity(Double.random(in: 0.03...0.08)),
                            lineWidth: 0.5
                        )
                        .frame(width: radius, height: radius)
                }

                // Outer edge highlight
                Circle()
                    .stroke(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.15),
                                Color.white.opacity(0.05),
                                Color.white.opacity(0.1)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 2
                    )

                // Vinyl sheen (subtle light reflection)
                Circle()
                    .fill(
                        AngularGradient(
                            colors: [
                                Color.white.opacity(0.0),
                                Color.white.opacity(0.04),
                                Color.white.opacity(0.0),
                                Color.white.opacity(0.03),
                                Color.white.opacity(0.0)
                            ],
                            center: .center
                        )
                    )
                    .padding(4)

                // Center label area
                Circle()
                    .fill(Color(hex: "252535"))
                    .frame(width: size * 0.42, height: size * 0.42)

                // Album art (center)
                albumArtView
                    .frame(width: size * 0.38, height: size * 0.38)
                    .clipShape(Circle())

                // Center spindle
                Circle()
                    .fill(Color(hex: "1A1A1A"))
                    .frame(width: size * 0.04, height: size * 0.04)

                Circle()
                    .fill(
                        RadialGradient(
                            colors: [Color.white.opacity(0.3), Color.white.opacity(0.05)],
                            center: .center,
                            startRadius: 0,
                            endRadius: size * 0.02
                        )
                    )
                    .frame(width: size * 0.04, height: size * 0.04)
            }
            .frame(width: size, height: size)
            .rotationEffect(.degrees(rotationAngle))
        }
        .onReceive(timer) { _ in
            updateRotation()
        }
    }

    // MARK: - Album Art

    @ViewBuilder
    private var albumArtView: some View {
        if let url = albumArtURL {
            AsyncImage(url: url) { phase in
                switch phase {
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                case .failure:
                    defaultArtView
                case .empty:
                    ProgressView()
                        .scaleEffect(0.8)
                @unknown default:
                    defaultArtView
                }
            }
        } else {
            defaultArtView
        }
    }

    private var defaultArtView: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [AngelaTheme.primaryPurple, AngelaTheme.secondaryPurple],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            Image(systemName: "music.note")
                .font(.system(size: size * 0.1, weight: .medium))
                .foregroundColor(.white.opacity(0.8))
        }
    }

    // MARK: - Rotation Animation (Timer-based)

    private func updateRotation() {
        if isPlaying {
            // Accelerate toward target speed
            if angularVelocity < targetSpeed {
                angularVelocity += targetSpeed / 30.0  // Reach full speed in ~0.5s
                if angularVelocity > targetSpeed {
                    angularVelocity = targetSpeed
                }
            }
        } else {
            // Decelerate smoothly
            if angularVelocity > 0.01 {
                angularVelocity *= 0.95
            } else {
                angularVelocity = 0
            }
        }

        rotationAngle += angularVelocity
        if rotationAngle >= 360 {
            rotationAngle -= 360
        }
    }
}
