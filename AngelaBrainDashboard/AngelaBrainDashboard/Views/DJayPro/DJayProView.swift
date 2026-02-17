//
//  DJayProView.swift
//  Angela Brain Dashboard
//
//  DJ Angela x djay Pro — Angela controls djay Pro app
//

import SwiftUI
import Combine

// MARK: - Song Model

struct DJayProSong: Identifiable, Codable {
    var id: String { songId }
    let songId: String
    let title: String
    let artist: String
    let album: String?
    let artworkUrl: String?
    let isOurSong: Bool?
    let whySpecial: String?
    let source: String?
    let moodTags: [String]?

    enum CodingKeys: String, CodingKey {
        case songId = "song_id"
        case title, artist, album
        case artworkUrl = "artwork_url"
        case isOurSong = "is_our_song"
        case whySpecial = "why_special"
        case source
        case moodTags = "mood_tags"
    }
}

// MARK: - API Response Models

struct PlaylistResponse: Codable {
    let songs: [DJayProSong]
    let reason: String
    let context: String
    let subContext: String?
    let contextSummary: String
    let count: Int

    enum CodingKeys: String, CodingKey {
        case songs, reason, context, count
        case subContext = "sub_context"
        case contextSummary = "context_summary"
    }
}

struct DJayStatusResponse: Codable {
    let running: Bool
}

struct DJayActionResponse: Codable {
    let success: Bool
}

// MARK: - ViewModel

@MainActor
class DJayProViewModel: ObservableObject {
    @Published var isDjayRunning = false
    @Published var selectedContext: DJayProContext?
    @Published var selectedWine: String?
    @Published var playlist: [DJayProSong] = []
    @Published var angelaMessage = ""
    @Published var contextSummary = ""
    @Published var isLoading = false
    @Published var isCheckingStatus = false
    @Published var loadingDeck: Int? = nil  // which deck is loading (1 or 2)

    private let baseURL = "\(APIConfig.apiBaseURL)/djay-pro"

    // MARK: - Check Status

    func checkStatus() async {
        isCheckingStatus = true
        defer { isCheckingStatus = false }

        guard let url = URL(string: "\(baseURL)/status") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            let resp = try JSONDecoder().decode(DJayStatusResponse.self, from: data)
            isDjayRunning = resp.running
        } catch {
            isDjayRunning = false
        }
    }

    // MARK: - Launch djay Pro

    func launchDjay() async {
        guard let url = URL(string: "\(baseURL)/launch") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{}".data(using: .utf8)

        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let resp = try JSONDecoder().decode(DJayActionResponse.self, from: data)
            if resp.success {
                isDjayRunning = true
            }
        } catch { }
    }

    // MARK: - Generate Playlist

    func generatePlaylist() async {
        guard let context = selectedContext else { return }
        isLoading = true
        defer { isLoading = false }

        guard let url = URL(string: "\(baseURL)/generate-playlist") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var body: [String: Any] = ["context": context.rawValue, "count": 15]
        if context == .wine, let wine = selectedWine {
            body["sub_context"] = wine
        }

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let resp = try JSONDecoder().decode(PlaylistResponse.self, from: data)
            playlist = resp.songs
            angelaMessage = resp.reason
            contextSummary = resp.contextSummary
        } catch {
            angelaMessage = "เกิดข้อผิดพลาดค่ะ ลองใหม่อีกครั้งนะคะ"
        }
    }

    // MARK: - Load Song into djay

    func loadSong(title: String, artist: String, deck: Int) async {
        loadingDeck = deck
        defer { loadingDeck = nil }

        guard let url = URL(string: "\(baseURL)/load-song") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = ["title": title, "artist": artist, "deck": deck]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let _ = try await URLSession.shared.data(for: request)
        } catch { }
    }

    // MARK: - Transport Controls

    func playPause() async {
        guard let url = URL(string: "\(baseURL)/play-pause") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{}".data(using: .utf8)
        let _ = try? await URLSession.shared.data(for: request)
    }

    func nextTrack() async {
        guard let url = URL(string: "\(baseURL)/next-track") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{}".data(using: .utf8)
        let _ = try? await URLSession.shared.data(for: request)
    }

    func toggleAutomix() async {
        guard let url = URL(string: "\(baseURL)/automix") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = "{}".data(using: .utf8)
        let _ = try? await URLSession.shared.data(for: request)
    }

    // MARK: - Play All (load first + automix)

    func playAll() async {
        guard !playlist.isEmpty else { return }
        isLoading = true
        defer { isLoading = false }

        guard let url = URL(string: "\(baseURL)/play-playlist") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let songsData = playlist.map { ["title": $0.title, "artist": $0.artist] }
        let body: [String: Any] = ["songs": songsData]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let _ = try await URLSession.shared.data(for: request)
        } catch { }
    }

    func shuffleAndPlay() async {
        playlist.shuffle()
        await playAll()
    }
}

// MARK: - Main View

struct DJayProView: View {
    @StateObject private var vm = DJayProViewModel()

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 20) {
                    // Header
                    headerSection

                    // Context Selector
                    DJayProContextSelector(
                        selectedContext: $vm.selectedContext,
                        selectedWine: $vm.selectedWine,
                        onGenerate: {
                            Task { await vm.generatePlaylist() }
                        }
                    )

                    // Angela's Message
                    if !vm.angelaMessage.isEmpty {
                        angelaMessageSection
                    }

                    // Loading
                    if vm.isLoading {
                        ProgressView("Angela is selecting songs...")
                            .progressViewStyle(CircularProgressViewStyle(tint: AngelaTheme.primaryPurple))
                            .foregroundColor(AngelaTheme.textSecondary)
                            .padding()
                    }

                    // Playlist
                    if !vm.playlist.isEmpty {
                        playlistSection
                    }

                    // Transport Controls
                    if vm.isDjayRunning {
                        controlsSection
                    }
                }
                .padding(24)
            }
        }
        .task {
            await vm.checkStatus()
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 8) {
                        Image(systemName: "dial.medium.fill")
                            .font(.system(size: 24))
                            .foregroundColor(AngelaTheme.primaryPurple)
                        Text("DJ Angela \u{00d7} djay Pro")
                            .font(AngelaTheme.title())
                            .foregroundColor(AngelaTheme.textPrimary)
                    }

                    Text("Angela controls djay Pro for you")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()

                // Status indicator
                statusBadge
            }
        }
        .padding(20)
        .angelaCard()
    }

    private var statusBadge: some View {
        Group {
            if vm.isCheckingStatus {
                ProgressView()
                    .scaleEffect(0.8)
            } else if vm.isDjayRunning {
                HStack(spacing: 6) {
                    Circle()
                        .fill(AngelaTheme.successGreen)
                        .frame(width: 8, height: 8)
                    Text("djay Pro Running")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(AngelaTheme.successGreen)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(AngelaTheme.successGreen.opacity(0.15))
                .cornerRadius(20)
            } else {
                Button {
                    Task { await vm.launchDjay() }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "play.circle.fill")
                        Text("Launch djay Pro")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(AngelaTheme.primaryPurple)
                    .cornerRadius(20)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Angela's Message

    private var angelaMessageSection: some View {
        HStack(alignment: .top, spacing: 12) {
            Text("\u{1f49c}")
                .font(.system(size: 20))
            VStack(alignment: .leading, spacing: 4) {
                Text("Angela says...")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(AngelaTheme.textTertiary)
                Text(vm.angelaMessage)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .italic()
            }
            Spacer()
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(AngelaTheme.primaryPurple.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
                )
        )
    }

    // MARK: - Playlist

    private var playlistSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Playlist header with actions
            HStack {
                HStack(spacing: 8) {
                    Image(systemName: "music.note.list")
                        .foregroundColor(AngelaTheme.primaryPurple)
                    Text("Playlist")
                        .font(AngelaTheme.headline())
                        .foregroundColor(AngelaTheme.textPrimary)
                    Text("(\(vm.playlist.count) songs)")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()

                // Action buttons
                HStack(spacing: 8) {
                    Button {
                        Task { await vm.playAll() }
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "play.fill")
                            Text("Play All")
                        }
                        .font(.system(size: 12, weight: .semibold))
                        .angelaPrimaryButton()
                    }
                    .buttonStyle(.plain)

                    Button {
                        Task { await vm.shuffleAndPlay() }
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "shuffle")
                            Text("Shuffle")
                        }
                        .font(.system(size: 12, weight: .semibold))
                        .angelaSecondaryButton()
                    }
                    .buttonStyle(.plain)

                    Button {
                        Task { await vm.generatePlaylist() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12, weight: .semibold))
                            .angelaSecondaryButton()
                    }
                    .buttonStyle(.plain)
                }
            }

            // Song rows
            ForEach(Array(vm.playlist.enumerated()), id: \.element.id) { index, song in
                songRow(index: index, song: song)
            }
        }
        .padding(20)
        .angelaCard()
    }

    private func songRow(index: Int, song: DJayProSong) -> some View {
        HStack(spacing: 12) {
            // Track number
            Text("\(index + 1)")
                .font(.system(size: 12, weight: .medium, design: .monospaced))
                .foregroundColor(AngelaTheme.textTertiary)
                .frame(width: 24)

            // Our song indicator
            if song.isOurSong == true {
                Image(systemName: "heart.circle.fill")
                    .foregroundColor(AngelaTheme.emotionLoved)
                    .font(.system(size: 14))
            }

            // Song info
            VStack(alignment: .leading, spacing: 2) {
                Text(song.title)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)
                Text(song.artist)
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .lineLimit(1)
            }

            Spacer()

            // Source badge
            if let source = song.source, source == "apple_music" {
                Text("iTunes")
                    .font(.system(size: 9, weight: .medium))
                    .foregroundColor(AngelaTheme.textTertiary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(AngelaTheme.backgroundLight.opacity(0.5))
                    .cornerRadius(4)
            }

            // Load to deck buttons
            HStack(spacing: 6) {
                deckButton(song: song, deck: 1)
                deckButton(song: song, deck: 2)
            }
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 4)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(index % 2 == 0
                    ? Color.clear
                    : AngelaTheme.backgroundLight.opacity(0.2))
        )
    }

    private func deckButton(song: DJayProSong, deck: Int) -> some View {
        let isLoading = vm.loadingDeck == deck
        return Button {
            Task { await vm.loadSong(title: song.title, artist: song.artist, deck: deck) }
        } label: {
            Group {
                if isLoading {
                    ProgressView()
                        .scaleEffect(0.6)
                } else {
                    Text("D\(deck)")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                }
            }
            .frame(width: 32, height: 26)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(deck == 1
                        ? AngelaTheme.primaryPurple.opacity(0.3)
                        : AngelaTheme.accentGold.opacity(0.3))
            )
            .foregroundColor(deck == 1 ? AngelaTheme.secondaryPurple : AngelaTheme.accentGold)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Controls

    private var controlsSection: some View {
        HStack(spacing: 20) {
            Spacer()

            // Previous (next-track can serve as skip)
            Button {
                Task { await vm.nextTrack() }
            } label: {
                Image(systemName: "backward.fill")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.textPrimary)
            }
            .buttonStyle(.plain)

            // Play/Pause
            Button {
                Task { await vm.playPause() }
            } label: {
                Image(systemName: "playpause.fill")
                    .font(.system(size: 28))
                    .foregroundColor(.white)
                    .frame(width: 56, height: 56)
                    .background(Circle().fill(AngelaTheme.primaryPurple))
            }
            .buttonStyle(.plain)

            // Next
            Button {
                Task { await vm.nextTrack() }
            } label: {
                Image(systemName: "forward.fill")
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.textPrimary)
            }
            .buttonStyle(.plain)

            // Spacer between transport and automix
            Spacer()
                .frame(width: 30)

            // Automix toggle
            Button {
                Task { await vm.toggleAutomix() }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "shuffle")
                    Text("Automix")
                        .font(.system(size: 13, weight: .semibold))
                }
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(AngelaTheme.accentPurple.opacity(0.7))
                )
            }
            .buttonStyle(.plain)

            Spacer()
        }
        .padding(20)
        .angelaCard()
    }
}
