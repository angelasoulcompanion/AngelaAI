//
//  MusicPlayerView.swift
//  AngelaNativeApp
//
//  Music player control for Apple Music integration
//

import SwiftUI
import Combine

struct MusicPlayerView: View {
    @StateObject private var viewModel = MusicPlayerViewModel()

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            Divider()

            // Now Playing
            if viewModel.isLoading {
                loadingView
            } else if let error = viewModel.errorMessage {
                errorView(error)
            } else if let track = viewModel.currentTrack {
                nowPlayingView(track)
            } else {
                notPlayingView
            }

            Divider()

            // Controls
            controlsView

            Divider()

            // Playlists (if loaded)
            if !viewModel.playlists.isEmpty {
                playlistsView
            }
        }
        .task {
            await viewModel.loadMusicState()
        }
    }

    // MARK: - Header

    private var headerView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("🎵 Music Player")
                    .font(.title2)
                    .fontWeight(.bold)

                Text(viewModel.playerState?.state.capitalized ?? "Unknown")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Button(action: { Task { await viewModel.refresh() } }) {
                Image(systemName: "arrow.clockwise")
                    .foregroundColor(.blue)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isLoading)
        }
        .padding()
    }

    // MARK: - Now Playing

    private func nowPlayingView(_ track: MusicTrack) -> some View {
        VStack(spacing: 16) {
            // Album art placeholder
            RoundedRectangle(cornerRadius: 16)
                .fill(
                    LinearGradient(
                        colors: [.blue.opacity(0.3), .purple.opacity(0.3)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 200, height: 200)
                .overlay(
                    Image(systemName: "music.note")
                        .font(.system(size: 60))
                        .foregroundColor(.white.opacity(0.8))
                )

            // Track info
            VStack(spacing: 8) {
                Text(track.title)
                    .font(.title3)
                    .fontWeight(.semibold)
                    .lineLimit(1)

                Text(track.artist)
                    .font(.callout)
                    .foregroundColor(.secondary)
                    .lineLimit(1)

                Text(track.album)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }
            .frame(maxWidth: 300)

            // Progress bar
            VStack(spacing: 4) {
                ProgressView(value: track.progressPercentage, total: 100)
                    .progressViewStyle(.linear)

                HStack {
                    Text(formatDuration(track.position))
                        .font(.caption2)
                        .foregroundColor(.secondary)

                    Spacer()

                    Text(formatDuration(track.duration))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            .frame(maxWidth: 300)
        }
        .padding()
    }

    // MARK: - Not Playing

    private var notPlayingView: some View {
        VStack(spacing: 16) {
            Image(systemName: "music.note.list")
                .font(.system(size: 60))
                .foregroundColor(.gray)

            Text("No Music Playing")
                .font(.title3)
                .fontWeight(.medium)

            Text("Select a playlist or play music from Apple Music")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Controls

    private var controlsView: some View {
        HStack(spacing: 24) {
            // Previous
            Button(action: { Task { await viewModel.previousTrack() } }) {
                Image(systemName: "backward.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isLoading)

            // Play/Pause
            Button(action: { Task { await viewModel.togglePlayPause() } }) {
                Image(systemName: viewModel.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.blue)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isLoading)

            // Next
            Button(action: { Task { await viewModel.nextTrack() } }) {
                Image(systemName: "forward.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isLoading)

            Divider()
                .frame(height: 30)

            // Volume control
            HStack(spacing: 12) {
                Image(systemName: "speaker.fill")
                    .foregroundColor(.secondary)

                Slider(
                    value: Binding(
                        get: { Double(viewModel.volume) },
                        set: { newValue in
                            Task { await viewModel.setVolume(Int(newValue)) }
                        }
                    ),
                    in: 0...100,
                    step: 5
                )
                .frame(width: 150)

                Text("\(viewModel.volume)%")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .frame(width: 40)
            }
        }
        .padding()
    }

    // MARK: - Playlists

    private var playlistsView: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Playlists")
                .font(.headline)
                .padding(.horizontal)

            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(viewModel.playlists, id: \.self) { playlist in
                        PlaylistRow(
                            name: playlist,
                            isPlaying: false,
                            onTap: {
                                Task { await viewModel.playPlaylist(playlist) }
                            }
                        )
                    }
                }
                .padding(.horizontal)
            }
        }
        .frame(maxHeight: 200)
        .padding(.vertical)
    }

    // MARK: - Loading & Error

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)

            Text("Loading music...")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    private func errorView(_ error: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 50))
                .foregroundColor(.red)

            Text("Error")
                .font(.title3)
                .fontWeight(.medium)

            Text(error)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button("Retry") {
                Task { await viewModel.refresh() }
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Helpers

    private func formatDuration(_ seconds: Double) -> String {
        let minutes = Int(seconds) / 60
        let secs = Int(seconds) % 60
        return String(format: "%d:%02d", minutes, secs)
    }
}

// MARK: - Playlist Row

struct PlaylistRow: View {
    let name: String
    let isPlaying: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack {
                Image(systemName: isPlaying ? "music.note.list" : "music.note")
                    .foregroundColor(isPlaying ? .blue : .secondary)

                Text(name)
                    .font(.callout)
                    .foregroundColor(isPlaying ? .blue : .primary)

                Spacer()

                if isPlaying {
                    Image(systemName: "speaker.wave.2.fill")
                        .foregroundColor(.blue)
                        .font(.caption)
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isPlaying ? Color.blue.opacity(0.1) : Color.clear)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - View Model

@MainActor
class MusicPlayerViewModel: ObservableObject {
    @Published var currentTrack: MusicTrack?
    @Published var playerState: MusicPlayerState?
    @Published var playlists: [String] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var volume: Int = 50
    @Published var isPlaying: Bool = false

    private let mcpClient = MCPClient.shared

    func loadMusicState() async {
        await refresh()
        await loadPlaylists()
    }

    func refresh() async {
        isLoading = true
        errorMessage = nil

        do {
            // Get current track
            currentTrack = try await mcpClient.getCurrentTrack()

            // Get player state
            playerState = try await mcpClient.getPlayerState()
            volume = playerState?.volume ?? 50
            isPlaying = playerState?.isPlaying ?? false

        } catch {
            errorMessage = error.localizedDescription
            print("❌ Failed to load music state: \(error)")
        }

        isLoading = false
    }

    func loadPlaylists() async {
        do {
            playlists = try await mcpClient.getPlaylists()
        } catch {
            print("⚠️ Failed to load playlists: \(error)")
        }
    }

    func togglePlayPause() async {
        do {
            if isPlaying {
                try await mcpClient.pauseMusic()
            } else {
                try await mcpClient.playMusic()
            }

            // Refresh state
            await refresh()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func nextTrack() async {
        do {
            try await mcpClient.nextTrack()
            try await Task.sleep(nanoseconds: 500_000_000) // Wait 0.5s
            await refresh()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func previousTrack() async {
        do {
            try await mcpClient.previousTrack()
            try await Task.sleep(nanoseconds: 500_000_000) // Wait 0.5s
            await refresh()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func setVolume(_ level: Int) async {
        do {
            try await mcpClient.setVolume(level)
            volume = level
        } catch {
            print("⚠️ Failed to set volume: \(error)")
        }
    }

    func playPlaylist(_ name: String) async {
        do {
            try await mcpClient.playPlaylist(name)
            try await Task.sleep(nanoseconds: 1_000_000_000) // Wait 1s
            await refresh()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

// MARK: - Preview

#Preview {
    MusicPlayerView()
        .frame(width: 600, height: 700)
}
