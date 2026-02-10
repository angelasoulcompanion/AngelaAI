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

    private var upNextSongs: [DisplaySong] {
        let idx = musicService.currentQueueIndex + 1
        guard idx < musicService.queue.count else { return [] }
        return Array(musicService.queue[idx..<min(idx + 3, musicService.queue.count)])
    }

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
            // Left: Vinyl + Controls (45%) — Scrollable
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    // Time-Aware Header
                    TimeAwareHeader()
                        .padding(.bottom, 12)

                    // Dual Turntable Decks
                    DJDualDeckView(musicService: musicService)
                        .padding(.bottom, 4)

                    // Transition Mode Picker
                    TransitionModePickerView(musicService: musicService)
                        .padding(.bottom, 8)

                    // Player controls
                    PlayerControlsView(musicService: musicService)

                    // Up Next Preview (3 songs only — keep compact for larger vinyl)
                    if !upNextSongs.isEmpty {
                        UpNextPreview(songs: upNextSongs)
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

                    Spacer(minLength: 8)
                }
                .padding(.vertical, 12)
            }
            .frame(minWidth: 420, idealWidth: 520)
            .padding(.horizontal, 24)

            // Right: Song Queue (compact)
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
            .frame(minWidth: 300, idealWidth: 360)
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

// MARK: - Song Memory Card (play history) - Professional Design with Animation

struct SongMemoryCard: View {
    let memory: SongMemory
    @State private var animateBars = false
    @State private var animateMoods = false
    @State private var animateHeader = false
    @State private var pulseGlow = false

    // Occasion colors and icons (matches _detect_occasion in music.py)
    private let occasionData: [(key: String, icon: String, label: String, color: Color)] = [
        ("morning", "sunrise.fill", "Morning", Color.orange),
        ("working_morning", "desktopcomputer", "Work AM", Color.teal),
        ("lunch", "fork.knife", "Lunch", Color.yellow),
        ("working_afternoon", "desktopcomputer", "Work PM", Color.cyan),
        ("evening", "sunset.fill", "Evening", Color.pink),
        ("late_night", "moon.stars.fill", "Late", Color.indigo),
        ("midnight", "moon.fill", "Midnight", Color.purple),
    ]

    private var maxCount: Int {
        activeOccasions.map(\.count).max() ?? 1
    }

    var body: some View {
        // Compact single-row layout: badge | bars | moods
        HStack(spacing: 8) {
            // Play count badge with pulsing glow
            ZStack {
                Capsule()
                    .stroke(AngelaTheme.primaryPurple.opacity(0.5), lineWidth: 1.5)
                    .padding(-2)
                    .scaleEffect(pulseGlow ? 1.1 : 1.0)
                    .opacity(pulseGlow ? 0.0 : 0.6)

                HStack(spacing: 3) {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 10))
                    Text("\(memory.playCount)")
                        .font(.system(size: 13, weight: .bold, design: .rounded))
                        .contentTransition(.numericText())
                }
                .foregroundColor(.white)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(
                    Capsule()
                        .fill(LinearGradient(
                            colors: [AngelaTheme.primaryPurple, AngelaTheme.secondaryPurple],
                            startPoint: .leading,
                            endPoint: .trailing
                        ))
                        .shadow(color: AngelaTheme.primaryPurple.opacity(0.4), radius: pulseGlow ? 6 : 3)
                )
            }
            .fixedSize()
            .scaleEffect(animateHeader ? 1 : 0.6)
            .opacity(animateHeader ? 1 : 0)

            // Occasion mini bars (inline)
            if !memory.recentPlays.isEmpty {
                HStack(alignment: .bottom, spacing: 4) {
                    ForEach(Array(activeOccasions.enumerated()), id: \.element.occasion) { index, item in
                        occasionBar(item: item, index: index)
                    }
                }
            }

            Spacer()

            // Mood pills (inline, right side)
            HStack(spacing: 4) {
                ForEach(Array(topMoods.prefix(2).enumerated()), id: \.element) { index, mood in
                    moodPill(mood: mood, index: index)
                }
            }
            .opacity(animateMoods ? 1 : 0)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
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
        .onAppear { triggerAnimations() }
        .onChange(of: memory.playCount) { _, _ in
            // Re-animate when song changes
            animateBars = false
            animateMoods = false
            animateHeader = false
            pulseGlow = false
            triggerAnimations()
        }
    }

    // MARK: - Occasion Bar

    @ViewBuilder
    private func occasionBar(item: (occasion: String, count: Int, icon: String, label: String, color: Color), index: Int) -> some View {
        let barMaxHeight: CGFloat = 20
        let barHeight = barMaxHeight * CGFloat(item.count) / CGFloat(max(maxCount, 1))

        VStack(spacing: 1) {
            Text("\(item.count)")
                .font(.system(size: 7, weight: .bold, design: .rounded))
                .foregroundColor(item.color)
                .opacity(animateBars ? 1 : 0)
                .animation(.spring(response: 0.5, dampingFraction: 0.7).delay(Double(index) * 0.06 + 0.2), value: animateBars)

            RoundedRectangle(cornerRadius: 3)
                .fill(
                    LinearGradient(
                        colors: [item.color, item.color.opacity(0.4)],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
                .frame(width: 14, height: animateBars ? max(barHeight, 3) : 0)
                .animation(.spring(response: 0.5, dampingFraction: 0.65).delay(Double(index) * 0.06), value: animateBars)

            Image(systemName: item.icon)
                .font(.system(size: 7))
                .foregroundColor(item.color.opacity(0.8))
        }
        .opacity(animateBars ? 1 : 0)
        .animation(.easeOut(duration: 0.3).delay(Double(index) * 0.06), value: animateBars)
    }

    // MARK: - Mood Pill

    @ViewBuilder
    private func moodPill(mood: String, index: Int) -> some View {
        let displayMood = mood.replacingOccurrences(of: "_", with: " ")

        Text(displayMood)
            .font(.system(size: 8, weight: .semibold))
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(
                Capsule()
                    .fill(AngelaTheme.primaryPurple.opacity(0.12))
                    .overlay(
                        Capsule()
                            .stroke(AngelaTheme.primaryPurple.opacity(0.25), lineWidth: 0.5)
                    )
            )
            .foregroundColor(AngelaTheme.primaryPurple)
            .scaleEffect(animateMoods ? 1 : 0.7)
            .opacity(animateMoods ? 1 : 0)
            .animation(.spring(response: 0.5, dampingFraction: 0.7).delay(Double(index) * 0.1 + 0.4), value: animateMoods)
    }

    // MARK: - Animation Trigger

    private func triggerAnimations() {
        withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
            animateHeader = true
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            withAnimation { animateBars = true }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            withAnimation { animateMoods = true }
        }
        // Start pulsing glow after entrance
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
            withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) {
                pulseGlow = true
            }
        }
    }

    // MARK: - Data

    // Only occasions with count > 0
    private var activeOccasions: [(occasion: String, count: Int, icon: String, label: String, color: Color)] {
        var counts: [String: Int] = [:]
        for play in memory.recentPlays {
            if let occ = play.occasion {
                counts[occ, default: 0] += 1
            }
        }
        return occasionData.compactMap { data in
            let c = counts[data.key] ?? 0
            guard c > 0 else { return nil }
            return (data.key, c, data.icon, data.label, data.color)
        }
    }

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

// MARK: - DJ Bottom Panel (EQ Visualizer + Up Next)

struct DJBottomPanel: View {
    @ObservedObject var musicService: MusicPlayerService
    @State private var showContent = false

    private var upNextSongs: [DisplaySong] {
        let idx = musicService.currentQueueIndex + 1
        guard idx < musicService.queue.count else { return [] }
        return Array(musicService.queue[idx..<min(idx + 3, musicService.queue.count)])
    }

    var body: some View {
        VStack(spacing: 6) {
            // Live EQ Visualizer
            if musicService.nowPlaying != nil {
                DJEqualizerView(isPlaying: musicService.isPlaying)
                    .opacity(showContent ? 1 : 0)
                    .offset(y: showContent ? 0 : 8)
            }

            // Up Next Preview
            if !upNextSongs.isEmpty {
                UpNextPreview(songs: upNextSongs)
                    .opacity(showContent ? 1 : 0)
                    .offset(y: showContent ? 0 : 10)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5).delay(0.3)) {
                showContent = true
            }
        }
        .onChange(of: musicService.nowPlaying?.title) { _, _ in
            showContent = false
            withAnimation(.easeOut(duration: 0.4).delay(0.2)) {
                showContent = true
            }
        }
    }
}

// MARK: - Live EQ Visualizer (Waveform Line + Gradient Area)

struct DJEqualizerView: View {
    let isPlaying: Bool

    private let pointCount = 48
    private let waveHeight: CGFloat = 48

    var body: some View {
        VStack(spacing: 3) {
            // Label row
            HStack(spacing: 4) {
                Circle()
                    .fill(isPlaying ? Color.green : AngelaTheme.textTertiary)
                    .frame(width: 5, height: 5)
                    .shadow(color: isPlaying ? Color.green.opacity(0.6) : .clear, radius: 3)

                Text(isPlaying ? "LIVE" : "PAUSED")
                    .font(.system(size: 8, weight: .bold))
                    .foregroundColor(isPlaying ? Color.green : AngelaTheme.textTertiary)
                    .tracking(1)

                Spacer()

                HStack(spacing: 10) {
                    eqLabel("BASS", color: Color(hue: 0.78, saturation: 0.7, brightness: 0.9))
                    eqLabel("MID", color: Color(hue: 0.85, saturation: 0.6, brightness: 0.9))
                    eqLabel("HIGH", color: Color(hue: 0.5, saturation: 0.6, brightness: 0.9))
                }
            }

            // Waveform
            GeometryReader { geo in
                TimelineView(.animation(minimumInterval: 0.033, paused: !isPlaying)) { timeline in
                    let t = timeline.date.timeIntervalSinceReferenceDate
                    waveformView(time: t, size: geo.size)
                }
            }
            .frame(height: waveHeight)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.black.opacity(0.35))
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.white.opacity(0.06), lineWidth: 0.5)
                )
        )
    }

    private func eqLabel(_ text: String, color: Color) -> some View {
        Text(text)
            .font(.system(size: 7, weight: .bold))
            .foregroundColor(color.opacity(0.6))
            .tracking(0.5)
    }

    // MARK: - Waveform Drawing

    @ViewBuilder
    private func waveformView(time t: Double, size: CGSize) -> some View {
        let levels = (0..<pointCount).map { spectrumLevel(index: $0, time: t) }
        let points = levels.enumerated().map { i, level -> CGPoint in
            let x = size.width * CGFloat(i) / CGFloat(pointCount - 1)
            let y = size.height * (1.0 - CGFloat(level))
            return CGPoint(x: x, y: y)
        }

        ZStack {
            // Gradient fill area
            Path { path in
                guard let first = points.first else { return }
                path.move(to: CGPoint(x: first.x, y: size.height))
                path.addLine(to: first)
                addSmoothCurve(path: &path, points: points)
                path.addLine(to: CGPoint(x: points.last?.x ?? size.width, y: size.height))
                path.closeSubpath()
            }
            .fill(
                LinearGradient(
                    stops: areaGradientStops(height: size.height),
                    startPoint: .top,
                    endPoint: .bottom
                )
            )

            // Line stroke with color gradient
            Path { path in
                guard let first = points.first else { return }
                path.move(to: first)
                addSmoothCurve(path: &path, points: points)
            }
            .stroke(
                LinearGradient(
                    colors: lineGradientColors(),
                    startPoint: .leading,
                    endPoint: .trailing
                ),
                style: StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round)
            )
            .shadow(color: AngelaTheme.primaryPurple.opacity(0.4), radius: 4, y: 0)

            // Glow line (duplicate, wider, more transparent)
            Path { path in
                guard let first = points.first else { return }
                path.move(to: first)
                addSmoothCurve(path: &path, points: points)
            }
            .stroke(
                LinearGradient(
                    colors: lineGradientColors().map { $0.opacity(0.3) },
                    startPoint: .leading,
                    endPoint: .trailing
                ),
                style: StrokeStyle(lineWidth: 6, lineCap: .round, lineJoin: .round)
            )
            .blur(radius: 3)
        }
    }

    // Catmull-Rom smooth curve through points
    private func addSmoothCurve(path: inout Path, points: [CGPoint]) {
        guard points.count > 1 else { return }
        for i in 1..<points.count {
            let p0 = points[max(i - 2, 0)]
            let p1 = points[i - 1]
            let p2 = points[i]
            let p3 = points[min(i + 1, points.count - 1)]

            let cp1x = p1.x + (p2.x - p0.x) / 6.0
            let cp1y = p1.y + (p2.y - p0.y) / 6.0
            let cp2x = p2.x - (p3.x - p1.x) / 6.0
            let cp2y = p2.y - (p3.y - p1.y) / 6.0

            path.addCurve(
                to: p2,
                control1: CGPoint(x: cp1x, y: cp1y),
                control2: CGPoint(x: cp2x, y: cp2y)
            )
        }
    }

    // Area fill: line color → transparent
    private func areaGradientStops(height: CGFloat) -> [Gradient.Stop] {
        [
            .init(color: AngelaTheme.primaryPurple.opacity(0.35), location: 0),
            .init(color: AngelaTheme.primaryPurple.opacity(0.12), location: 0.5),
            .init(color: Color.clear, location: 1.0),
        ]
    }

    // Line color: purple → magenta → cyan
    private func lineGradientColors() -> [Color] {
        [
            Color(hue: 0.78, saturation: 0.75, brightness: 0.9),
            Color(hue: 0.82, saturation: 0.7, brightness: 0.92),
            Color(hue: 0.87, saturation: 0.6, brightness: 0.95),
            Color(hue: 0.55, saturation: 0.55, brightness: 0.92),
            Color(hue: 0.5, saturation: 0.6, brightness: 0.9),
        ]
    }

    // MARK: - Beat-synced spectrum levels

    private func spectrumLevel(index: Int, time t: Double) -> Double {
        guard isPlaying else {
            return 0.06 + 0.03 * sin(t * 0.5 + Double(index) * 0.5)
        }

        let pos = Double(index) / Double(pointCount)
        let bps = 2.0
        let beat = t * bps
        let beatFrac = fract(beat)

        let beatNum = floor(beat)
        let seed = fract(sin(beatNum * 12.9898 + Double(index) * 78.233) * 43758.5453)
        let variation = 0.55 + seed * 0.45

        var level: Double

        if pos < 0.35 {
            let kickDecay = exp(-beatFrac * 7.0)
            let halfFrac = fract(beat + 0.5)
            let ghostKick = exp(-halfFrac * 10.0) * 0.5
            level = max(kickDecay, ghostKick) * variation
            let subBoost = 1.0 + (0.35 - pos) * 0.5
            level *= subBoost
        } else if pos < 0.7 {
            let snareFrac = fract(beat + 0.5)
            let snareHit = exp(-snareFrac * 6.0) * 0.8
            let eighthFrac = fract(beat * 2.0)
            let eighthHit = exp(-eighthFrac * 9.0) * 0.45
            level = max(snareHit, eighthHit) * variation
            let midPeak = 1.0 - abs(pos - 0.52) * 3.0
            level *= max(midPeak, 0.6)
        } else {
            let sixteenthFrac = fract(beat * 4.0)
            let sixteenthNum = Int(floor(beat * 4.0))
            let isOpen = sixteenthNum % 8 == 4
            let decay = isOpen ? 5.0 : 14.0
            let amp = isOpen ? 0.85 : 0.55
            level = exp(-sixteenthFrac * decay) * amp * variation
            let rolloff = 1.0 - (pos - 0.7) * 1.2
            level *= max(rolloff, 0.3)
        }

        let fourBeatFrac = fract(beat / 4.0)
        if fourBeatFrac < 0.02 {
            level = max(level, 0.85 * variation)
        }

        return min(max(level, 0.03), 1.0)
    }

    private func fract(_ x: Double) -> Double {
        x - floor(x)
    }
}

// MARK: - Up Next Preview

struct UpNextPreview: View {
    let songs: [DisplaySong]
    @State private var animateRows = false

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Header
            HStack(spacing: 5) {
                Image(systemName: "forward.end.fill")
                    .font(.system(size: 8))
                Text("UP NEXT")
                    .font(.system(size: 8, weight: .bold))
                    .tracking(1)
                Spacer()
                Text("\(songs.count) songs")
                    .font(.system(size: 9))
            }
            .foregroundColor(AngelaTheme.textTertiary)

            // Song rows
            ForEach(Array(songs.enumerated()), id: \.element.id) { index, song in
                upNextRow(song: song, index: index)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.black.opacity(0.3))
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.white.opacity(0.06), lineWidth: 0.5)
                )
        )
        .onAppear {
            withAnimation(.easeOut(duration: 0.4).delay(0.5)) {
                animateRows = true
            }
        }
        .onChange(of: songs.first?.id) { _, _ in
            animateRows = false
            withAnimation(.easeOut(duration: 0.4).delay(0.2)) {
                animateRows = true
            }
        }
    }

    @ViewBuilder
    private func upNextRow(song: DisplaySong, index: Int) -> some View {
        HStack(spacing: 10) {
            // Track number
            Text("\(index + 1)")
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textTertiary)
                .frame(width: 14)

            // Mini album art
            if let url = song.albumArtURL {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    default:
                        RoundedRectangle(cornerRadius: 4)
                            .fill(AngelaTheme.cardBackground)
                    }
                }
                .frame(width: 24, height: 24)
                .clipShape(RoundedRectangle(cornerRadius: 4))
            } else {
                RoundedRectangle(cornerRadius: 4)
                    .fill(AngelaTheme.cardBackground)
                    .frame(width: 24, height: 24)
                    .overlay(
                        Image(systemName: "music.note")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                    )
            }

            // Song info
            VStack(alignment: .leading, spacing: 1) {
                Text(song.title)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)
                Text(song.artist)
                    .font(.system(size: 9))
                    .foregroundColor(AngelaTheme.textTertiary)
                    .lineLimit(1)
            }

            Spacer()

            // Mood tag (if available)
            if let mood = song.moodTags.first {
                Text(mood)
                    .font(.system(size: 8, weight: .semibold))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(
                        Capsule()
                            .fill(AngelaTheme.primaryPurple.opacity(0.1))
                    )
                    .foregroundColor(AngelaTheme.primaryPurple.opacity(0.7))
            }
        }
        .padding(.vertical, 2)
        .opacity(animateRows ? 1 : 0)
        .offset(x: animateRows ? 0 : 20)
        .animation(.spring(response: 0.4, dampingFraction: 0.8).delay(Double(index) * 0.1), value: animateRows)
    }
}
