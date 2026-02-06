//
//  SongQueueView.swift
//  Angela Brain Dashboard
//
//  Tabbed song list: Library, Playlists, Our Songs, For You, Search
//  All powered by Apple Music (MusicKit) + Angela DB
//

import SwiftUI
import MusicKit
import os.log

private let djLog = Logger(subsystem: "com.david.angela", category: "DJAngela")

struct SongQueueView: View {
    @ObservedObject var musicService: MusicPlayerService
    @ObservedObject var chatService: ChatService

    @State private var selectedTab: QueueTab = .liked
    @State private var likedSongs: [DisplaySong] = []
    @State private var userPlaylists: [MusicKit.Playlist] = []
    @State private var playlistTracks: [MusicKit.Song] = []
    @State private var selectedPlaylist: MusicKit.Playlist?
    @State private var ourSongs: [DisplaySong] = []
    @State private var recommendation: SongRecommendation?
    @State private var showMoodRadar = true
    @State private var recommendedDisplays: [DisplaySong] = []
    @State private var searchResults: [MusicKit.Song] = []
    @State private var searchQuery = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedMood: String?
    @State private var bedtimeDisplays: [DisplaySong] = []
    @State private var bedtimeRecommendation: SongRecommendation?
    /// Tracks which reaction was tapped — keyed by "pairing" or "title|artist", value is "up"/"down"/"love"
    @State private var wineReactions: [String: String] = [:]
    /// Wine selector popover in For You tab
    @State private var showWineSelector = false
    @State private var wineReactionCounts: [String: [String: Int]] = [:]
    /// Set of liked song keys (lowercase "title|artist") for quick lookup
    @State private var likedSongKeys: Set<String> = []

    enum QueueTab: String, CaseIterable {
        case liked = "Liked"
        case playlists = "Playlists"
        case ourSongs = "Our Songs"
        case queued = "Queued"
        case forYou = "For You"
        case bedtime = "Bedtime"
        case search = "Search"

        var icon: String {
            switch self {
            case .liked: return "heart.fill"
            case .playlists: return "list.bullet.rectangle"
            case .ourSongs: return "heart.circle.fill"
            case .queued: return "list.number"
            case .forYou: return "sparkles"
            case .bedtime: return "moon.zzz.fill"
            case .search: return "magnifyingglass"
            }
        }

        /// Source tab name sent to API for play logging
        var sourceKey: String {
            switch self {
            case .liked: return "liked"
            case .playlists: return "playlists"
            case .ourSongs: return "our_songs"
            case .queued: return "queued"
            case .forYou: return "for_you"
            case .bedtime: return "bedtime"
            case .search: return "search"
            }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            tabBar

            ScrollView {
                VStack(spacing: 12) {
                    switch selectedTab {
                    case .liked:
                        likedView
                    case .playlists:
                        playlistsView
                    case .ourSongs:
                        ourSongsView
                    case .queued:
                        queuedView
                    case .forYou:
                        recommendationView
                    case .bedtime:
                        bedtimeView
                    case .search:
                        searchView
                    }
                }
                .padding(16)
            }
        }
        .task {
            await loadInitialData()
        }
        .onChange(of: musicService.requestedMood) { oldValue, newValue in
            guard let mood = newValue else { return }
            // Switch to appropriate tab and load recommendations
            withAnimation(.easeInOut(duration: 0.2)) {
                if mood == "bedtime" {
                    selectedTab = .bedtime
                } else {
                    selectedTab = .forYou
                    selectedMood = mood
                }
            }
            Task {
                if mood == "bedtime" {
                    await loadBedtimeSongs()
                } else {
                    await loadRecommendation(mood: mood)
                }
                // Clear the request after handling
                musicService.requestedMood = nil
            }
        }
    }

    // MARK: - Tab Bar

    private var tabBar: some View {
        HStack(spacing: 2) {
            ForEach(QueueTab.allCases, id: \.rawValue) { tab in
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedTab = tab
                    }
                    Task { await onTabSelected(tab) }
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: tab.icon)
                            .font(.system(size: 11))
                        Text(tab.rawValue)
                            .font(.system(size: 12, weight: .medium))
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(
                        selectedTab == tab
                            ? AngelaTheme.primaryPurple.opacity(0.2)
                            : Color.clear
                    )
                    .foregroundColor(
                        selectedTab == tab
                            ? AngelaTheme.primaryPurple
                            : AngelaTheme.textSecondary
                    )
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
    }

    // MARK: - Liked Songs View

    private var likedView: some View {
        Group {
            if isLoading && likedSongs.isEmpty {
                LoadingStateView(message: "Loading...")
            } else if likedSongs.isEmpty {
                EmptyStateView(message: "No liked songs yet", icon: "heart")
            } else {
                playControlBar(
                    songCount: likedSongs.count,
                    onPlayAll: {
                        musicService.currentSourceTab = QueueTab.liked.sourceKey
                        musicService.setQueue(likedSongs)
                        Task { await musicService.playDisplaySong(likedSongs[0]) }
                    },
                    onShuffle: {
                        musicService.currentSourceTab = QueueTab.liked.sourceKey
                        let shuffled = likedSongs.shuffled()
                        musicService.setQueue(shuffled)
                        Task { await musicService.playDisplaySong(shuffled[0]) }
                    }
                )
                .padding(.bottom, 4)

                LazyVStack(spacing: 0) {
                    ForEach(likedSongs) { song in
                        displaySongRow(song, allSongs: likedSongs)
                    }
                }
            }
        }
    }

    // MARK: - Playlists View

    private var playlistsView: some View {
        Group {
            if let playlist = selectedPlaylist {
                // Playlist detail view
                playlistDetailView(playlist)
            } else if isLoading && userPlaylists.isEmpty {
                LoadingStateView(message: "Loading...")
            } else if userPlaylists.isEmpty {
                EmptyStateView(message: "No playlists found", icon: "list.bullet.rectangle")
            } else {
                LazyVStack(spacing: 8) {
                    ForEach(userPlaylists, id: \.id) { playlist in
                        playlistRow(playlist)
                    }
                }
            }
        }
    }

    private func playlistRow(_ playlist: MusicKit.Playlist) -> some View {
        Button {
            selectedPlaylist = playlist
            Task { await loadPlaylistTracks(playlist) }
        } label: {
            HStack(spacing: 12) {
                // Playlist artwork
                if let artwork = playlist.artwork {
                    AsyncImage(url: artwork.url(width: 50, height: 50)) { image in
                        image.resizable().aspectRatio(contentMode: .fill)
                    } placeholder: {
                        playlistPlaceholder
                    }
                    .frame(width: 50, height: 50)
                    .cornerRadius(8)
                } else {
                    playlistPlaceholder
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(playlist.name)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(AngelaTheme.textPrimary)
                        .lineLimit(1)

                    if let description = playlist.standardDescription, !description.isEmpty {
                        Text(description)
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.textTertiary)
                            .lineLimit(1)
                    }
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(AngelaTheme.cardBackground.opacity(0.5))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }

    private var playlistPlaceholder: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(AngelaTheme.backgroundLight)
            Image(systemName: "music.note.list")
                .font(.system(size: 18))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(width: 50, height: 50)
    }

    private func playlistDetailView(_ playlist: MusicKit.Playlist) -> some View {
        VStack(spacing: 12) {
            // Back button + header
            HStack(spacing: 8) {
                Button {
                    selectedPlaylist = nil
                    playlistTracks = []
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 12, weight: .semibold))
                        Text("Playlists")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)

                Spacer()
            }

            // Playlist header card
            HStack(spacing: 14) {
                if let artwork = playlist.artwork {
                    AsyncImage(url: artwork.url(width: 80, height: 80)) { image in
                        image.resizable().aspectRatio(contentMode: .fill)
                    } placeholder: {
                        playlistPlaceholder
                    }
                    .frame(width: 80, height: 80)
                    .cornerRadius(10)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text(playlist.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)

                    if !playlistTracks.isEmpty {
                        Text("\(playlistTracks.count) tracks")
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }

                    playControlBar(
                        songCount: playlistTracks.count,
                        showCount: false,
                        compact: true,
                        onPlayAll: {
                            musicService.currentSourceTab = QueueTab.playlists.sourceKey
                            let display = playlistTracks.map { DisplaySong(from: $0) }
                            musicService.setQueue(display)
                            if let first = playlistTracks.first {
                                Task { await musicService.playSong(first) }
                            }
                        },
                        onShuffle: {
                            musicService.currentSourceTab = QueueTab.playlists.sourceKey
                            let shuffled = playlistTracks.shuffled()
                            let display = shuffled.map { DisplaySong(from: $0) }
                            musicService.setQueue(display)
                            if let first = shuffled.first {
                                Task { await musicService.playSong(first) }
                            }
                        }
                    )
                }

                Spacer()
            }
            .padding(12)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)

            // Track list
            if isLoading {
                LoadingStateView(message: "Loading...")
            } else if playlistTracks.isEmpty {
                EmptyStateView(message: "No tracks in playlist", icon: "music.note")
            } else {
                LazyVStack(spacing: 0) {
                    ForEach(Array(playlistTracks.enumerated()), id: \.element.id) { index, song in
                        musicKitSongRow(song, allSongs: playlistTracks, index: index)
                    }
                }
            }
        }
    }

    // MARK: - Our Songs View

    private var ourSongsView: some View {
        Group {
            if isLoading && ourSongs.isEmpty {
                LoadingStateView(message: "Loading...")
            } else if ourSongs.isEmpty {
                EmptyStateView(message: "No songs yet", icon: "heart")
            } else {
                playControlBar(
                    songCount: ourSongs.count,
                    showShuffle: false,
                    showCount: false,
                    onPlayAll: {
                        musicService.currentSourceTab = QueueTab.ourSongs.sourceKey
                        musicService.setQueue(ourSongs)
                        Task { await musicService.playDisplaySong(ourSongs[0]) }
                    }
                )
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, 4)

                ForEach(ourSongs) { song in
                    displaySongRow(song, allSongs: ourSongs)
                }
            }
        }
    }

    // MARK: - Queued View

    private var queuedView: some View {
        Group {
            if musicService.queue.isEmpty {
                EmptyStateView(message: "No songs in queue", icon: "list.number")
            } else {
                // Energy flow header
                if hasEnergyPhases {
                    HStack(spacing: 4) {
                        Text("Energy Flow 🎢")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(AngelaTheme.textSecondary)
                        Spacer()
                    }
                    .padding(.bottom, 4)
                }

                playControlBar(
                    songCount: musicService.queue.count,
                    showShuffle: false,
                    showCount: true,
                    onPlayAll: {
                        musicService.currentSourceTab = QueueTab.queued.sourceKey
                        if let first = musicService.queue.first {
                            musicService.currentQueueIndex = 0
                            Task { await musicService.playDisplaySong(first) }
                        }
                    }
                )
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, 4)

                // Group by energy phase
                ForEach(energyPhaseGroups, id: \.phase) { group in
                    if let phase = group.phase {
                        energyPhaseHeader(phase)
                    }
                    ForEach(group.songs) { song in
                        displaySongRow(song, allSongs: musicService.queue)
                    }
                }
            }
        }
    }

    // MARK: - Energy Phase Helpers

    private var hasEnergyPhases: Bool {
        musicService.queue.contains { $0.energyPhase != nil }
    }

    private struct EnergyPhaseGroup: Identifiable {
        let phase: String?
        let songs: [DisplaySong]
        var id: String { phase ?? "none" }
    }

    private var energyPhaseGroups: [EnergyPhaseGroup] {
        var groups: [EnergyPhaseGroup] = []
        var currentPhase: String? = nil
        var currentSongs: [DisplaySong] = []

        for song in musicService.queue {
            let phase = song.energyPhase
            if phase != currentPhase {
                if !currentSongs.isEmpty {
                    groups.append(EnergyPhaseGroup(phase: currentPhase, songs: currentSongs))
                }
                currentPhase = phase
                currentSongs = [song]
            } else {
                currentSongs.append(song)
            }
        }
        if !currentSongs.isEmpty {
            groups.append(EnergyPhaseGroup(phase: currentPhase, songs: currentSongs))
        }
        return groups
    }

    @ViewBuilder
    private func energyPhaseHeader(_ phase: String) -> some View {
        HStack(spacing: 6) {
            Circle()
                .fill(energyPhaseColor(phase))
                .frame(width: 8, height: 8)
            Text(energyPhaseLabel(phase))
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(energyPhaseColor(phase))
            Spacer()
        }
        .padding(.top, 8)
        .padding(.bottom, 2)
    }

    private func energyPhaseColor(_ phase: String) -> Color {
        switch phase.lowercased() {
        case "warmup": return .blue
        case "peak": return AngelaTheme.primaryPurple
        case "cooldown": return .teal
        default: return AngelaTheme.textTertiary
        }
    }

    private func energyPhaseLabel(_ phase: String) -> String {
        switch phase.lowercased() {
        case "warmup": return "🔵 Warmup"
        case "peak": return "🟣 Peak"
        case "cooldown": return "🔵 Cooldown"
        default: return phase.capitalized
        }
    }

    // MARK: - Recommendation View (For You)

    private var recommendationView: some View {
        VStack(spacing: 16) {
            if isLoading {
                LoadingStateView(message: "Loading...")
            } else if let rec = recommendation {
                // Mood Radar Card (collapsible)
                if let analysis = rec.moodAnalysis, showMoodRadar {
                    MoodRadarCard(analysis: analysis, onClose: { showMoodRadar = false })
                }

                // Emotion card + mood picker
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        if rec.wineMessage != nil {
                            Image(systemName: "wineglass.fill")
                                .font(.system(size: 16))
                                .foregroundColor(.purple)
                        } else {
                            Image(systemName: "sparkles")
                                .font(.system(size: 16))
                                .foregroundColor(AngelaTheme.accentGold)
                        }

                        Text(rec.wineMessage != nil ? "Wine Pairing" : "Based on your emotions")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(AngelaTheme.textPrimary)
                    }

                    Text(rec.reason)
                        .font(.system(size: 13))
                        .foregroundColor(AngelaTheme.textSecondary)

                    if let mood = rec.moodSummary {
                        Text(mood)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(AngelaTheme.secondaryPurple)
                            .italic()
                    }

                    // Wine profile sensory bars
                    if let profile = rec.wineProfile {
                        wineProfileCard(profile: profile, target: rec.targetProfile)
                    }

                    // Wine pairing reaction buttons
                    if rec.wineMessage != nil, let wineType = musicService.currentWineType {
                        wineReactionBar(wineType: wineType, targetType: "pairing")
                    }

                    // Tappable mood pills
                    let moods = rec.availableMoods ?? ["happy", "loving", "calm", "excited", "grateful", "sad", "lonely", "stressed", "nostalgic", "hopeful"]
                    let current = selectedMood ?? rec.basedOnEmotion

                    moodPickerGrid(moods: moods, selected: current)

                    // Wine Pairing selector (separate from activity chips)
                    Divider()
                        .background(AngelaTheme.textTertiary.opacity(0.3))

                    winePairingSection
                }
                .padding(16)
                .background(AngelaTheme.cardBackground)
                .cornerRadius(AngelaTheme.cornerRadius)

                // Recommended songs list
                if !recommendedDisplays.isEmpty {
                    playControlBar(
                        songCount: recommendedDisplays.count,
                        onPlayAll: {
                            musicService.currentSourceTab = QueueTab.forYou.sourceKey
                            musicService.setQueue(recommendedDisplays)
                            Task { await musicService.playDisplaySong(recommendedDisplays[0]) }
                        },
                        onShuffle: {
                            musicService.currentSourceTab = QueueTab.forYou.sourceKey
                            let shuffled = recommendedDisplays.shuffled()
                            musicService.setQueue(shuffled)
                            Task { await musicService.playDisplaySong(shuffled[0]) }
                        }
                    )

                    let wineActive = musicService.currentWineType != nil
                    ForEach(recommendedDisplays) { song in
                        displaySongRow(song, allSongs: recommendedDisplays, showWineReaction: wineActive)
                    }
                } else if let songs = rec.songs, !songs.isEmpty {
                    let displays = songs.map { DisplaySong(from: $0) }
                    let wineActive = musicService.currentWineType != nil
                    ForEach(displays) { song in
                        displaySongRow(song, allSongs: displays, showWineReaction: wineActive)
                    }
                } else if let song = rec.song {
                    let display = DisplaySong(from: song)
                    let wineActive = musicService.currentWineType != nil
                    displaySongRow(display, allSongs: [display], showWineReaction: wineActive)
                }

                // Refresh button
                Button {
                    Task { await loadRecommendation() }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12))
                        Text("Get New Recommendation")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .angelaSecondaryButton()
                }
                .buttonStyle(.plain)
            } else {
                EmptyStateView(message: "Tap to get a recommendation", icon: "sparkles")

                Button {
                    Task { await loadRecommendation() }
                } label: {
                    Text("Get Recommendation")
                        .font(.system(size: 14, weight: .semibold))
                        .angelaPrimaryButton()
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Bedtime View

    private var bedtimeView: some View {
        VStack(spacing: 16) {
            if isLoading {
                LoadingStateView(message: "Loading lullabies...")
            } else if !bedtimeDisplays.isEmpty {
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "moon.zzz.fill")
                            .font(.system(size: 16))
                            .foregroundColor(AngelaTheme.secondaryPurple)
                        Text("Bedtime Lullabies")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(AngelaTheme.textPrimary)
                    }

                    if let summary = bedtimeRecommendation?.moodSummary {
                        Text(summary)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(AngelaTheme.secondaryPurple)
                            .italic()
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(AngelaTheme.cardBackground.opacity(0.6))
                .cornerRadius(AngelaTheme.cornerRadius)

                playControlBar(
                    songCount: bedtimeDisplays.count,
                    onPlayAll: {
                        musicService.currentSourceTab = QueueTab.bedtime.sourceKey
                        musicService.setQueue(bedtimeDisplays)
                        Task { await musicService.playDisplaySong(bedtimeDisplays[0]) }
                    },
                    onShuffle: {
                        musicService.currentSourceTab = QueueTab.bedtime.sourceKey
                        let shuffled = bedtimeDisplays.shuffled()
                        musicService.setQueue(shuffled)
                        Task { await musicService.playDisplaySong(shuffled[0]) }
                    }
                )

                ForEach(bedtimeDisplays) { song in
                    displaySongRow(song, allSongs: bedtimeDisplays)
                }

                // Refresh
                Button {
                    Task { await loadBedtimeSongs() }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12))
                        Text("Refresh Lullabies")
                            .font(.system(size: 13, weight: .medium))
                    }
                    .angelaSecondaryButton()
                }
                .buttonStyle(.plain)
            } else {
                EmptyStateView(message: "Tap to load bedtime songs", icon: "moon.zzz.fill")

                Button {
                    Task { await loadBedtimeSongs() }
                } label: {
                    Text("Load Lullabies")
                        .font(.system(size: 14, weight: .semibold))
                        .angelaPrimaryButton()
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Search View (Apple Music Catalog)

    private var searchView: some View {
        VStack(spacing: 12) {
            // Search field
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textTertiary)

                TextField("Search Apple Music...", text: $searchQuery)
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .onSubmit {
                        Task { await performSearch() }
                    }

                if !searchQuery.isEmpty {
                    Button {
                        searchQuery = ""
                        searchResults = []
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 14))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(10)
            .background(AngelaTheme.backgroundLight)
            .cornerRadius(8)

            if isLoading {
                LoadingStateView(message: "Loading...")
            } else if searchResults.isEmpty && !searchQuery.isEmpty {
                EmptyStateView(message: "No results for \"\(searchQuery)\"", icon: "magnifyingglass")
            } else if !searchResults.isEmpty {
                Text("\(searchResults.count) results")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                LazyVStack(spacing: 0) {
                    ForEach(Array(searchResults.enumerated()), id: \.element.id) { index, song in
                        musicKitSongRow(song, allSongs: searchResults, index: index)
                    }
                }
            }
        }
    }

    // MARK: - Unified Song Row

    /// Single song-row layout shared by MusicKit songs and DisplaySongs.
    private func songRow(
        title: String,
        artist: String,
        album: String? = nil,
        artworkURL: URL? = nil,
        duration: TimeInterval? = nil,
        durationFormatted: String? = nil,
        moodTags: [String] = [],
        isOurSong: Bool = false,
        davidLiked: Bool = false,
        isCurrentSong: Bool,
        showWineReaction: Bool = false,
        angelaFeeling: String? = nil,
        onPlay: @escaping () -> Void,
        onLike: (() -> Void)? = nil
    ) -> some View {
        VStack(spacing: 0) {
        HStack(spacing: 12) {
            // Album art thumbnail
            if let url = artworkURL {
                AsyncImage(url: url) { image in
                    image.resizable().aspectRatio(contentMode: .fill)
                } placeholder: {
                    artPlaceholder
                }
                .frame(width: 40, height: 40)
                .cornerRadius(6)
            } else {
                artPlaceholder
            }

            // Song info
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.system(size: 14, weight: isCurrentSong ? .semibold : .regular))
                    .foregroundColor(isCurrentSong ? AngelaTheme.primaryPurple : AngelaTheme.textPrimary)
                    .lineLimit(1)

                HStack(spacing: 4) {
                    Text(artist)
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)

                    if let album, !album.isEmpty {
                        Text("\u{00B7}")
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.textTertiary)
                        Text(album)
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.textTertiary)
                            .lineLimit(1)
                    }
                }

                if let feeling = angelaFeeling {
                    Text("💜 \(feeling)")
                        .font(.system(size: 11))
                        .foregroundColor(AngelaTheme.secondaryPurple.opacity(0.8))
                        .italic()
                        .lineLimit(2)
                }
            }

            Spacer()

            // Mood tags
            if !moodTags.isEmpty {
                HStack(spacing: 4) {
                    ForEach(moodTags.prefix(2), id: \.self) { tag in
                        Text(tag)
                            .font(.system(size: 10, weight: .medium))
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(AngelaTheme.primaryPurple.opacity(0.15))
                            .foregroundColor(AngelaTheme.secondaryPurple)
                            .cornerRadius(4)
                    }
                }
            }

            // Like button - Angela's purple color 💜
            if let likeAction = onLike {
                Button {
                    likeAction()
                } label: {
                    Image(systemName: (isOurSong || davidLiked) ? "heart.fill" : "heart")
                        .font(.system(size: 16))
                        .foregroundColor((isOurSong || davidLiked) ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary)
                }
                .buttonStyle(.plain)
            } else if isOurSong || davidLiked {
                Image(systemName: "heart.fill")
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }

            // Duration
            if let dur = durationFormatted {
                Text(dur)
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(AngelaTheme.textTertiary)
            } else if let duration {
                let minutes = Int(duration) / 60
                let seconds = Int(duration) % 60
                Text(String(format: "%d:%02d", minutes, seconds))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(AngelaTheme.textTertiary)
            }

            // Playing indicator (with pause) or play button
            if isCurrentSong && musicService.isPlaying {
                Button {
                    Task { await musicService.togglePlayPause() }
                } label: {
                    ZStack {
                        playingBars
                        // Overlay pause icon on hover/tap
                        Image(systemName: "pause.circle.fill")
                            .font(.system(size: 24))
                            .foregroundColor(AngelaTheme.primaryPurple)
                            .opacity(0.01) // Nearly invisible but tappable
                    }
                }
                .buttonStyle(.plain)
                .help("Pause")
            } else if isCurrentSong {
                // Paused - show play button
                Button {
                    Task { await musicService.togglePlayPause() }
                } label: {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)
            } else {
                Button {
                    onPlay()
                } label: {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(AngelaTheme.primaryPurple.opacity(0.7))
                }
                .buttonStyle(.plain)
            }
        }
        // Song-level wine reaction icons
        if showWineReaction, let wineType = musicService.currentWineType {
            wineReactionBar(
                wineType: wineType,
                targetType: "song",
                songTitle: title,
                songArtist: artist
            )
            .padding(.leading, 52) // align with text (past artwork)
        }
        } // end VStack
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            isCurrentSong
                ? AngelaTheme.primaryPurple.opacity(0.08)
                : Color.clear
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(
                    isCurrentSong ? AngelaTheme.primaryPurple.opacity(0.3) : Color.clear,
                    lineWidth: 1
                )
        )
        .cornerRadius(8)
    }

    // MARK: - MusicKit Song Row (Library, Playlists, Search)

    private func musicKitSongRow(_ song: MusicKit.Song, allSongs: [MusicKit.Song], index: Int) -> some View {
        let isCurrent = musicService.nowPlaying?.title == song.title
            && musicService.nowPlaying?.artist == song.artistName
        return songRow(
            title: song.title,
            artist: song.artistName,
            album: song.albumTitle,
            artworkURL: song.artwork?.url(width: 80, height: 80),
            duration: song.duration,
            davidLiked: isLiked(title: song.title, artist: song.artistName),
            isCurrentSong: isCurrent,
            onPlay: {
                musicService.currentSourceTab = selectedTab.sourceKey
                musicService.setMusicKitQueue(allSongs, startAt: index)
                Task { await musicService.playSong(song) }
            },
            onLike: {
                // Optimistic UI update
                markAsLiked(title: song.title, artist: song.artistName)
                Task {
                    do {
                        let resp = try await ChatService.shared.likeSong(
                            title: song.title,
                            artist: song.artistName,
                            album: song.albumTitle,
                            appleMusicId: song.id.rawValue,
                            artworkUrl: song.artwork?.url(width: 300, height: 300)?.absoluteString,
                            sourceTab: selectedTab.sourceKey
                        )
                        print("💜 Liked: \(resp.title) - \(resp.action)")
                    } catch {
                        print("❌ Like error: \(error)")
                    }
                }
            }
        )
    }

    // MARK: - DisplaySong Row (Our Songs, For You)

    private func displaySongRow(_ song: DisplaySong, allSongs: [DisplaySong], showWineReaction: Bool = false) -> some View {
        let isCurrent: Bool = {
            if let angela = song.angelaSong {
                return musicService.nowPlaying?.angelaSong?.songId == angela.songId
            }
            return musicService.nowPlaying?.title == song.title
                && musicService.nowPlaying?.artist == song.artist
        }()
        return songRow(
            title: song.title,
            artist: song.artist,
            artworkURL: song.albumArtURL,
            durationFormatted: song.durationFormatted,
            moodTags: song.moodTags,
            isOurSong: song.isOurSong,
            davidLiked: isLiked(title: song.title, artist: song.artist),
            isCurrentSong: isCurrent,
            showWineReaction: showWineReaction,
            angelaFeeling: song.angelaFeeling,
            onPlay: {
                musicService.currentSourceTab = selectedTab.sourceKey
                if let idx = allSongs.firstIndex(where: { $0.id == song.id }) {
                    musicService.setQueue(allSongs, startAt: idx)
                }
                Task { await musicService.playDisplaySong(song) }
            },
            onLike: {
                // Optimistic UI update
                markAsLiked(title: song.title, artist: song.artist)
                Task {
                    do {
                        let resp = try await ChatService.shared.likeSong(
                            title: song.title,
                            artist: song.artist,
                            album: song.album,
                            appleMusicId: song.musicKitSong?.id.rawValue,
                            artworkUrl: song.albumArtURL?.absoluteString,
                            sourceTab: selectedTab.sourceKey
                        )
                        print("💜 Liked: \(resp.title) - \(resp.action)")
                    } catch {
                        print("❌ Like error: \(error)")
                    }
                }
            }
        )
    }

    // MARK: - Wine Reaction Bar

    /// Compact row of 👍👎❤️ buttons for wine pairing feedback.
    @ViewBuilder
    private func wineReactionBar(
        wineType: String,
        targetType: String,
        songTitle: String? = nil,
        songArtist: String? = nil
    ) -> some View {
        let key = targetType == "pairing" ? "pairing" : "\(songTitle ?? "")|\(songArtist ?? "")"
        let selected = wineReactions[key]

        HStack(spacing: 10) {
            ForEach(
                [("up", "👍"), ("down", "👎"), ("love", "❤️")],
                id: \.0
            ) { reaction, emoji in
                Button {
                    wineReactions[key] = reaction
                    djLog.notice("[WineReaction] Tapped \(reaction) for \(targetType) wine=\(wineType)")
                    Task {
                        do {
                            try await chatService.submitWineReaction(
                                wineType: wineType,
                                reaction: reaction,
                                targetType: targetType,
                                songTitle: songTitle,
                                songArtist: songArtist
                            )
                            djLog.notice("[WineReaction] Saved OK")
                        } catch {
                            djLog.notice("[WineReaction] ERROR: \(error)")
                        }
                    }
                } label: {
                    Text(emoji)
                        .font(.system(size: 14))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(
                            selected == reaction
                                ? AngelaTheme.primaryPurple.opacity(0.2)
                                : AngelaTheme.backgroundLight.opacity(0.5)
                        )
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(
                                    selected == reaction
                                        ? AngelaTheme.primaryPurple.opacity(0.5)
                                        : Color.clear,
                                    lineWidth: 1
                                )
                        )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.top, 4)
    }

    // MARK: - Wine Profile Card (Sensory Bars)

    @ViewBuilder
    private func wineProfileCard(profile: WineProfileData, target: TargetProfileData?) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Wine Profile")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(AngelaTheme.textTertiary)

            // Sensory dimension bars
            let dimensions: [(String, Double, Color)] = [
                ("Body", profile.body, .purple),
                ("Tannins", profile.tannins, .red),
                ("Acidity", profile.acidity, .orange),
                ("Sweet", profile.sweetness, .pink),
                ("Aroma", profile.aromaIntensity, .indigo),
            ]

            HStack(spacing: 6) {
                ForEach(dimensions, id: \.0) { name, value, color in
                    VStack(spacing: 3) {
                        // Vertical bar
                        ZStack(alignment: .bottom) {
                            RoundedRectangle(cornerRadius: 3)
                                .fill(color.opacity(0.15))
                                .frame(width: 20, height: 40)
                            RoundedRectangle(cornerRadius: 3)
                                .fill(color.opacity(0.7))
                                .frame(width: 20, height: CGFloat(value / 5.0) * 40)
                        }
                        Text(name)
                            .font(.system(size: 8, weight: .medium))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }

                // Music target info (if available)
                if let t = target {
                    Spacer()
                    VStack(alignment: .trailing, spacing: 3) {
                        if let energy = t.energy {
                            HStack(spacing: 3) {
                                Text("Energy")
                                    .font(.system(size: 9))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                Text("\(Int(energy * 100))%")
                                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                                    .foregroundColor(AngelaTheme.primaryPurple)
                            }
                        }
                        if let valence = t.valence {
                            HStack(spacing: 3) {
                                Text("Mood")
                                    .font(.system(size: 9))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                Text(valence > 0.6 ? "Bright" : valence > 0.4 ? "Warm" : "Dark")
                                    .font(.system(size: 10, weight: .semibold))
                                    .foregroundColor(valence > 0.6 ? .green : valence > 0.4 ? .orange : .purple)
                            }
                        }
                        if let key = t.keyPref {
                            HStack(spacing: 3) {
                                Text("Key")
                                    .font(.system(size: 9))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                Text(key.capitalized)
                                    .font(.system(size: 10, weight: .semibold))
                                    .foregroundColor(key == "minor" ? .purple : .blue)
                            }
                        }
                        if let tempo = t.tempoRange, tempo.count == 2 {
                            HStack(spacing: 3) {
                                Text("BPM")
                                    .font(.system(size: 9))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                Text("\(tempo[0])-\(tempo[1])")
                                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                                    .foregroundColor(AngelaTheme.textSecondary)
                            }
                        }
                    }
                }
            }
        }
        .padding(10)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(8)
    }

    // MARK: - Mood Picker

    @ViewBuilder
    private func moodPickerGrid(moods: [String], selected: String) -> some View {
        let columns = Array(repeating: GridItem(.flexible(), spacing: 6), count: 5)
        LazyVGrid(columns: columns, spacing: 6) {
            ForEach(moods, id: \.self) { mood in
                let isSelected = mood == selected
                Button {
                    selectedMood = mood
                    musicService.currentMood = mood     // pass to play logging
                    musicService.currentWineType = nil  // mood overrides wine
                    Task { await loadRecommendation(mood: mood) }
                } label: {
                    HStack(spacing: 3) {
                        Text(DJAngelaConstants.moodEmojis[mood] ?? "🎵")
                            .font(.system(size: 11))
                        Text(mood.capitalized)
                            .font(.system(size: 10, weight: isSelected ? .semibold : .medium))
                            .lineLimit(1)
                    }
                    .frame(maxWidth: .infinity)
                    .angelaChip(isSelected: isSelected)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Wine Pairing Section (For You tab)

    private var winePairingSection: some View {
        HStack(spacing: 8) {
            Button {
                if musicService.currentWineType != nil {
                    // Clear wine → revert to mood recommendation
                    musicService.currentWineType = nil
                    Task { await loadRecommendation() }
                } else {
                    showWineSelector = true
                }
            } label: {
                HStack(spacing: 4) {
                    Text("🍷")
                        .font(.system(size: 12))
                    if let wineType = musicService.currentWineType,
                       let name = DJAngelaConstants.wineDisplayNames[wineType] {
                        Text(name)
                            .font(.system(size: 11, weight: .semibold))
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 10))
                    } else {
                        Text("Wine Pairing")
                            .font(.system(size: 11, weight: .medium))
                    }
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(
                    Capsule().fill(
                        musicService.currentWineType != nil
                            ? Color.purple
                            : AngelaTheme.backgroundLight.opacity(0.6)
                    )
                )
                .foregroundColor(musicService.currentWineType != nil ? .white : AngelaTheme.textSecondary)
            }
            .buttonStyle(.plain)
            .popover(isPresented: $showWineSelector, arrowEdge: .bottom) {
                WineSelectorView(onSelect: { wineKey in
                    musicService.currentWineType = wineKey
                    selectedMood = nil              // wine overrides mood
                    musicService.currentMood = nil  // clear mood for play logging
                    showWineSelector = false
                    Task { await loadRecommendation() }
                }, reactions: wineReactionCounts)
            }
            .onChange(of: showWineSelector) { _, open in
                if open {
                    Task {
                        wineReactionCounts = (try? await chatService.fetchWineReactions()) ?? [:]
                    }
                }
            }

            Spacer()
        }
    }

    // MARK: - Play Control Bar

    /// Reusable Play All / Shuffle / count bar.
    /// `compact` uses smaller font/padding (for playlist detail header).
    @ViewBuilder
    private func playControlBar(
        songCount: Int,
        showShuffle: Bool = true,
        showCount: Bool = true,
        compact: Bool = false,
        onPlayAll: @escaping () -> Void,
        onShuffle: @escaping () -> Void = {}
    ) -> some View {
        let iconSize: CGFloat = compact ? 10 : 11
        let textSize: CGFloat = compact ? 12 : 13
        let hPad: CGFloat = compact ? 12 : 16
        let vPad: CGFloat = compact ? 6 : 8
        let radius: CGFloat = compact ? 16 : 20

        HStack(spacing: compact ? 8 : 10) {
            Button(action: onPlayAll) {
                HStack(spacing: compact ? 4 : 6) {
                    Image(systemName: "play.fill")
                        .font(.system(size: iconSize))
                    Text("Play All")
                        .font(.system(size: textSize, weight: .semibold))
                }
                .padding(.horizontal, hPad)
                .padding(.vertical, vPad)
                .background(AngelaTheme.purpleGradient)
                .foregroundColor(.white)
                .cornerRadius(radius)
            }
            .buttonStyle(.plain)

            if showShuffle {
                if compact {
                    Button(action: onShuffle) {
                        HStack(spacing: 4) {
                            Image(systemName: "shuffle")
                                .font(.system(size: iconSize))
                            Text("Shuffle")
                                .font(.system(size: textSize, weight: .medium))
                        }
                        .padding(.horizontal, hPad)
                        .padding(.vertical, vPad)
                        .background(AngelaTheme.backgroundLight)
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .cornerRadius(radius)
                        .overlay(
                            RoundedRectangle(cornerRadius: radius)
                                .stroke(AngelaTheme.primaryPurple.opacity(0.5), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                } else {
                    Button(action: onShuffle) {
                        HStack(spacing: 6) {
                            Image(systemName: "shuffle")
                                .font(.system(size: iconSize))
                            Text("Shuffle")
                                .font(.system(size: textSize, weight: .medium))
                        }
                        .angelaSecondaryButton()
                    }
                    .buttonStyle(.plain)
                }
            }

            if !compact {
                Spacer()
            }

            if showCount {
                Text("\(songCount) songs")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
    }

    // MARK: - Shared Components

    private var artPlaceholder: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 6)
                .fill(AngelaTheme.backgroundLight)
            Image(systemName: "music.note")
                .font(.system(size: 16))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(width: 40, height: 40)
    }

    private var playingBars: some View {
        HStack(spacing: 2) {
            ForEach(0..<3, id: \.self) { _ in
                RoundedRectangle(cornerRadius: 1)
                    .fill(AngelaTheme.primaryPurple)
                    .frame(width: 3, height: CGFloat.random(in: 6...14))
            }
        }
        .frame(width: 24, height: 24)
    }


    // MARK: - Data Loading

    private func loadInitialData() async {
        isLoading = true
        defer { isLoading = false }

        // Load playlists, our songs, and liked songs in parallel
        async let pls = musicService.fetchUserPlaylists()
        async let songs = chatService.fetchOurSongs()
        async let liked = loadLikedSongs()

        let (plsResult, songsResult, _) = await (pls, (try? songs) ?? [], liked)
        userPlaylists = plsResult

        // Convert Angela songs to DisplaySong, enriching with Apple Music art in background
        ourSongs = songsResult.map { DisplaySong(from: $0) }
        Task { await enrichOurSongsArtwork() }
    }

    /// Load liked songs from API and populate both likedSongs list and likedSongKeys set
    private func loadLikedSongs() async {
        do {
            let response = try await chatService.fetchLikedSongs()
            let keys = Set(response.songs.map { $0.matchKey })
            let songs = response.songs.map { DisplaySong(from: $0) }
            await MainActor.run {
                likedSongKeys = keys
                likedSongs = songs
            }
            djLog.debug("💜 Loaded \(keys.count) liked songs")
            // Enrich artwork in background
            Task { await enrichLikedSongsArtwork() }
        } catch {
            djLog.error("❌ Failed to load liked songs: \(error)")
        }
    }

    /// Check if a song is liked by David
    private func isLiked(title: String, artist: String) -> Bool {
        let key = "\(title.lowercased())|\(artist.lowercased())"
        return likedSongKeys.contains(key)
    }

    /// Add a song to liked set (optimistic update)
    private func markAsLiked(title: String, artist: String) {
        let key = "\(title.lowercased())|\(artist.lowercased())"
        likedSongKeys.insert(key)
    }

    private func onTabSelected(_ tab: QueueTab) async {
        switch tab {
        case .liked:
            // Refresh liked songs (may have changed from other tabs)
            await loadLikedSongs()
        case .playlists:
            if userPlaylists.isEmpty {
                isLoading = true
                userPlaylists = await musicService.fetchUserPlaylists()
                isLoading = false
            }
        case .ourSongs:
            if ourSongs.isEmpty {
                isLoading = true
                let songs = (try? await chatService.fetchOurSongs()) ?? []
                ourSongs = songs.map { DisplaySong(from: $0) }
                isLoading = false
                Task { await enrichOurSongsArtwork() }
            }
        case .queued:
            break  // Queue reads directly from musicService.queue
        case .forYou:
            if recommendation == nil {
                await loadRecommendation()
            }
        case .bedtime:
            if bedtimeDisplays.isEmpty {
                await loadBedtimeSongs()
            }
        default:
            break
        }
    }

    private func loadPlaylistTracks(_ playlist: MusicKit.Playlist) async {
        isLoading = true
        var tracks = await musicService.fetchPlaylistTracks(playlist)

        // Favourite Songs: Apple Music shows newest-added-first,
        // MusicKit returns oldest-added-first → reverse to match
        let name = playlist.name.lowercased()
        if name == "favourite songs" || name == "favorite songs" {
            tracks.reverse()
        }

        playlistTracks = tracks
        isLoading = false
    }

    /// Max angela_songs (DB) to include — playlists fill the rest.
    private static let maxAngelaSongs = 2
    private static let maxAngelaSongsWine = 5
    private static let recommendTargetCount = 6
    private static let wineRecommendTargetCount = 25

    private func loadRecommendation(mood: String? = nil) async {
        isLoading = true
        recommendedDisplays = []

        do {
            let wineType = musicService.currentWineType
            let isWine = wineType != nil
            let isBedtime = (mood ?? selectedMood) == "bedtime"
            let targetCount = isWine ? Self.wineRecommendTargetCount : (isBedtime ? 30 : Self.recommendTargetCount)
            recommendation = try await chatService.getRecommendation(
                mood: mood ?? selectedMood,
                wineType: wineType,
                count: (isWine || isBedtime) ? targetCount : nil
            )

            // --- 1. Angela DB songs (our songs) ---
            let songList = recommendation?.songs ?? [recommendation?.song].compactMap { $0 }
            let dbSongLimit = isWine ? Self.maxAngelaSongsWine : Self.maxAngelaSongs
            let usedList = Array(songList.prefix(dbSongLimit))
            var displays = usedList.map { DisplaySong(from: $0) }
            var seenKeys = Set(displays.map { "\($0.title.lowercased())|\($0.artist.lowercased())" })

            // --- 2. Fill from user's Apple Music playlists (primary source) ---
            if displays.count < targetCount {
                let detectedMood = recommendation?.basedOnEmotion ?? "happy"
                let pool = await musicService.loadPlaylistSongPool()

                let matched = pool.filter { DJAngelaConstants.playlistMatchesMood($0.name, mood: detectedMood) }
                let unmatched = pool.filter { !DJAngelaConstants.playlistMatchesMood($0.name, mood: detectedMood) }

                let orderedSongs = matched.flatMap(\.songs).shuffled()
                    + unmatched.flatMap(\.songs).shuffled()

                for mkSong in orderedSongs {
                    if displays.count >= targetCount { break }
                    let key = "\(mkSong.title.lowercased())|\(mkSong.artistName.lowercased())"
                    if seenKeys.insert(key).inserted {
                        displays.append(DisplaySong(from: mkSong))
                    }
                }
            }
            djLog.notice("[ForYou] After playlists: \(displays.count)/\(targetCount) isWine=\(isWine)")

            // --- 3. Fill remaining from Apple Music catalog (MusicKit) ---
            // Use dynamic search queries from backend (wine-music algorithm) when available
            if displays.count < targetCount {
                let queries: [String]
                if let dynamicQueries = recommendation?.searchQueries, !dynamicQueries.isEmpty {
                    queries = dynamicQueries
                    djLog.notice("[ForYou] Using dynamic searchQueries from backend: \(dynamicQueries)")
                } else if isWine, let wt = wineType, let term = DJAngelaConstants.wineSearchTerms[wt] {
                    queries = [term]
                } else {
                    let detectedMood = recommendation?.basedOnEmotion ?? "happy"
                    queries = [DJAngelaConstants.moodSearchTerms[detectedMood] ?? "love songs romantic"]
                }

                let remaining = targetCount - displays.count
                let perQuery = max(5, remaining / max(1, queries.count))
                for query in queries {
                    if displays.count >= targetCount { break }
                    djLog.notice("[ForYou] MusicKit catalog search: '\(query)' limit=\(perQuery)")
                    let catalogSongs = await musicService.searchCatalog(query: query, limit: perQuery)
                    djLog.notice("[ForYou] MusicKit returned \(catalogSongs.count) songs")
                    for mkSong in catalogSongs {
                        if displays.count >= targetCount { break }
                        let key = "\(mkSong.title.lowercased())|\(mkSong.artistName.lowercased())"
                        if seenKeys.insert(key).inserted {
                            displays.append(DisplaySong(from: mkSong))
                        }
                    }
                }
            }

            // Show songs immediately
            recommendedDisplays = displays
            isLoading = false

            // --- 4. Enrich DB songs (no artwork) via MusicKit search ---
            for (index, song) in displays.enumerated() {
                guard song.albumArtURL == nil, let angela = song.angelaSong else { continue }
                if let mkSong = await musicService.searchAppleMusic(title: angela.title, artist: angela.artist) {
                    let artURL = mkSong.artwork?.url(width: 300, height: 300)
                    if index < recommendedDisplays.count {
                        recommendedDisplays[index] = DisplaySong(from: angela, artwork: artURL)
                    }
                }
            }
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }

    private func loadBedtimeSongs() async {
        isLoading = true
        bedtimeDisplays = []

        do {
            let targetCount = 30
            bedtimeRecommendation = try await chatService.getRecommendation(
                mood: "bedtime", wineType: nil, count: targetCount
            )

            let songList = bedtimeRecommendation?.songs ?? [bedtimeRecommendation?.song].compactMap { $0 }
            var displays = Array(songList.prefix(2)).map { DisplaySong(from: $0) }
            var seenKeys = Set(displays.map { "\($0.title.lowercased())|\($0.artist.lowercased())" })

            // Fill from playlists
            if displays.count < targetCount {
                let pool = await musicService.loadPlaylistSongPool()
                let matched = pool.filter { DJAngelaConstants.playlistMatchesMood($0.name, mood: "bedtime") }
                let unmatched = pool.filter { !DJAngelaConstants.playlistMatchesMood($0.name, mood: "bedtime") }
                let orderedSongs = matched.flatMap(\.songs).shuffled() + unmatched.flatMap(\.songs).shuffled()
                for mkSong in orderedSongs {
                    if displays.count >= targetCount { break }
                    let key = "\(mkSong.title.lowercased())|\(mkSong.artistName.lowercased())"
                    if seenKeys.insert(key).inserted {
                        displays.append(DisplaySong(from: mkSong))
                    }
                }
            }

            // Fill from Apple Music catalog
            if displays.count < targetCount {
                let queries: [String]
                if let dq = bedtimeRecommendation?.searchQueries, !dq.isEmpty {
                    queries = dq
                } else {
                    queries = [DJAngelaConstants.moodSearchTerms["bedtime"] ?? "sleep music peaceful piano ambient"]
                }
                let remaining = targetCount - displays.count
                let perQuery = max(5, remaining / max(1, queries.count))
                for query in queries {
                    if displays.count >= targetCount { break }
                    let catalogSongs = await musicService.searchCatalog(query: query, limit: perQuery)
                    for mkSong in catalogSongs {
                        if displays.count >= targetCount { break }
                        let key = "\(mkSong.title.lowercased())|\(mkSong.artistName.lowercased())"
                        if seenKeys.insert(key).inserted {
                            displays.append(DisplaySong(from: mkSong))
                        }
                    }
                }
            }

            bedtimeDisplays = displays
            isLoading = false

            // Enrich artwork
            for (index, song) in displays.enumerated() {
                guard song.albumArtURL == nil, let angela = song.angelaSong else { continue }
                if let mkSong = await musicService.searchAppleMusic(title: angela.title, artist: angela.artist) {
                    let artURL = mkSong.artwork?.url(width: 300, height: 300)
                    if index < bedtimeDisplays.count {
                        bedtimeDisplays[index] = DisplaySong(from: angela, artwork: artURL)
                    }
                }
            }
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }

    private func performSearch() async {
        guard !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isLoading = true
        defer { isLoading = false }

        searchResults = await musicService.searchCatalog(query: searchQuery)
    }

    /// Enrich Our Songs with album art via iTunes Search API (REST, no MusicKit)
    private func enrichOurSongsArtwork() async {
        for (index, song) in ourSongs.enumerated() {
            guard song.albumArtURL == nil, let angela = song.angelaSong else { continue }
            if let mkSong = await musicService.searchAppleMusic(title: angela.title, artist: angela.artist) {
                let artURL = mkSong.artwork?.url(width: 300, height: 300)
                ourSongs[index] = DisplaySong(from: angela, artwork: artURL)
            }
        }
    }

    /// Enrich Liked Songs with album art via Apple Music search
    private func enrichLikedSongsArtwork() async {
        for (index, song) in likedSongs.enumerated() {
            guard song.albumArtURL == nil else { continue }
            if let mkSong = await musicService.searchAppleMusic(title: song.title, artist: song.artist) {
                let artURL = mkSong.artwork?.url(width: 300, height: 300)
                // Create new DisplaySong with artwork
                let enriched = DisplaySong(
                    title: song.title,
                    artist: song.artist,
                    album: song.album ?? mkSong.albumTitle,
                    artworkURL: artURL,
                    duration: mkSong.duration
                )
                await MainActor.run {
                    likedSongs[index] = enriched
                }
            }
        }
    }
}

// MARK: - Mood Radar Card (7-signal analysis visualization)

struct MoodRadarCard: View {
    let analysis: MoodAnalysis
    let onClose: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header with close button
            HStack {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Angela's Emotion Radar")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button {
                    onClose()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textTertiary)
                }
                .buttonStyle(.plain)
            }

            // Signal bars
            ForEach(analysis.signals.prefix(5)) { signal in
                signalBar(signal)
            }

            // Dominant mood indicator
            HStack(spacing: 6) {
                Text("💜")
                    .font(.system(size: 12))
                Text("Dominant:")
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textTertiary)
                Text(analysis.dominantMood.capitalized)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("(\(Int(analysis.confidence * 100))%)")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .padding(.top, 4)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(AngelaTheme.cardBackground)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(AngelaTheme.primaryPurple.opacity(0.15), lineWidth: 1)
                )
        )
    }

    @ViewBuilder
    private func signalBar(_ signal: MoodSignal) -> some View {
        HStack(spacing: 8) {
            // Signal strength dots (5 dots)
            HStack(spacing: 2) {
                ForEach(0..<5, id: \.self) { i in
                    Circle()
                        .fill(Double(i) < signal.weight * 5.0 ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                        .frame(width: 5, height: 5)
                }
            }
            .frame(width: 35)

            // Signal name
            Text(signal.displayName)
                .font(.system(size: 11))
                .foregroundColor(AngelaTheme.textSecondary)
                .frame(width: 60, alignment: .leading)

            // Detected mood
            Text(signal.mood)
                .font(.system(size: 10, weight: .medium))
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(AngelaTheme.primaryPurple.opacity(0.12))
                .foregroundColor(AngelaTheme.secondaryPurple)
                .cornerRadius(4)

            // Weight percentage
            Text("(\(Int(signal.weight * 100))%)")
                .font(.system(size: 9, design: .monospaced))
                .foregroundColor(AngelaTheme.textTertiary)
        }
    }
}
