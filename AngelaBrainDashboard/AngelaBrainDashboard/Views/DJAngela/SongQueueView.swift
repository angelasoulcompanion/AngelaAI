//
//  SongQueueView.swift
//  Angela Brain Dashboard
//
//  Tabbed song list: Library, Playlists, Our Songs, For You, Search
//  All powered by Apple Music (MusicKit) + Angela DB
//

import SwiftUI
import MusicKit

struct SongQueueView: View {
    @ObservedObject var musicService: MusicPlayerService
    @ObservedObject var chatService: ChatService

    @State private var selectedTab: QueueTab = .library
    @State private var librarySongs: [MusicKit.Song] = []
    @State private var userPlaylists: [MusicKit.Playlist] = []
    @State private var playlistTracks: [MusicKit.Song] = []
    @State private var selectedPlaylist: MusicKit.Playlist?
    @State private var ourSongs: [DisplaySong] = []
    @State private var recommendation: SongRecommendation?
    @State private var recommendedDisplays: [DisplaySong] = []
    @State private var searchResults: [MusicKit.Song] = []
    @State private var searchQuery = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedMood: String?

    enum QueueTab: String, CaseIterable {
        case library = "Recent"
        case playlists = "Playlists"
        case ourSongs = "Our Songs"
        case forYou = "For You"
        case search = "Search"

        var icon: String {
            switch self {
            case .library: return "clock.arrow.circlepath"
            case .playlists: return "list.bullet.rectangle"
            case .ourSongs: return "heart.circle.fill"
            case .forYou: return "sparkles"
            case .search: return "magnifyingglass"
            }
        }

        /// Source tab name sent to API for play logging
        var sourceKey: String {
            switch self {
            case .library: return "library"
            case .playlists: return "playlists"
            case .ourSongs: return "our_songs"
            case .forYou: return "for_you"
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
                    case .library:
                        libraryView
                    case .playlists:
                        playlistsView
                    case .ourSongs:
                        ourSongsView
                    case .forYou:
                        recommendationView
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

    // MARK: - Recent Plays View

    private var libraryView: some View {
        Group {
            if isLoading && librarySongs.isEmpty {
                loadingView
            } else if librarySongs.isEmpty {
                emptyView(message: "No recent plays", icon: "clock.arrow.circlepath")
            } else {
                playControlBar(
                    songCount: librarySongs.count,
                    onPlayAll: {
                        musicService.currentSourceTab = QueueTab.library.sourceKey
                        let display = librarySongs.map { DisplaySong(from: $0) }
                        musicService.setQueue(display)
                        Task { await musicService.playSong(librarySongs[0]) }
                    },
                    onShuffle: {
                        musicService.currentSourceTab = QueueTab.library.sourceKey
                        let shuffled = librarySongs.shuffled()
                        let display = shuffled.map { DisplaySong(from: $0) }
                        musicService.setQueue(display)
                        Task { await musicService.playSong(shuffled[0]) }
                    }
                )
                .padding(.bottom, 4)

                LazyVStack(spacing: 0) {
                    ForEach(Array(librarySongs.enumerated()), id: \.element.id) { index, song in
                        musicKitSongRow(song, allSongs: librarySongs, index: index)
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
                loadingView
            } else if userPlaylists.isEmpty {
                emptyView(message: "No playlists found", icon: "list.bullet.rectangle")
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
                loadingView
            } else if playlistTracks.isEmpty {
                emptyView(message: "No tracks in playlist", icon: "music.note")
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
                loadingView
            } else if ourSongs.isEmpty {
                emptyView(message: "No songs yet", icon: "heart")
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

    // MARK: - Recommendation View (For You)

    private var recommendationView: some View {
        VStack(spacing: 16) {
            if isLoading {
                loadingView
            } else if let rec = recommendation {
                // Emotion card + mood picker
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "sparkles")
                            .font(.system(size: 16))
                            .foregroundColor(AngelaTheme.accentGold)

                        Text("Based on your emotions")
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

                    // Tappable mood pills
                    let moods = rec.availableMoods ?? ["happy", "loving", "calm", "excited", "grateful", "sad", "lonely", "stressed", "nostalgic", "hopeful"]
                    let current = selectedMood ?? rec.basedOnEmotion

                    moodPickerGrid(moods: moods, selected: current)
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

                    ForEach(recommendedDisplays) { song in
                        displaySongRow(song, allSongs: recommendedDisplays)
                    }
                } else if let songs = rec.songs, !songs.isEmpty {
                    let displays = songs.map { DisplaySong(from: $0) }
                    ForEach(displays) { song in
                        displaySongRow(song, allSongs: displays)
                    }
                } else if let song = rec.song {
                    let display = DisplaySong(from: song)
                    displaySongRow(display, allSongs: [display])
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
                emptyView(message: "Tap to get a recommendation", icon: "sparkles")

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
                loadingView
            } else if searchResults.isEmpty && !searchQuery.isEmpty {
                emptyView(message: "No results for \"\(searchQuery)\"", icon: "magnifyingglass")
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
        isCurrentSong: Bool,
        onPlay: @escaping () -> Void
    ) -> some View {
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

            // Our Song badge
            if isOurSong {
                Image(systemName: "heart.fill")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.emotionLoved)
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

            // Playing indicator or play button
            if isCurrentSong && musicService.isPlaying {
                playingBars
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
            isCurrentSong: isCurrent
        ) {
            musicService.currentSourceTab = selectedTab.sourceKey
            musicService.setMusicKitQueue(allSongs, startAt: index)
            Task { await musicService.playSong(song) }
        }
    }

    // MARK: - DisplaySong Row (Our Songs, For You)

    private func displaySongRow(_ song: DisplaySong, allSongs: [DisplaySong]) -> some View {
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
            isCurrentSong: isCurrent
        ) {
            musicService.currentSourceTab = selectedTab.sourceKey
            if let idx = allSongs.firstIndex(where: { $0.id == song.id }) {
                musicService.setQueue(allSongs, startAt: idx)
            }
            Task { await musicService.playDisplaySong(song) }
        }
    }

    // MARK: - Mood Picker

    private static let moodEmojis: [String: String] = [
        "happy": "😊", "loving": "💜", "calm": "🍃", "excited": "✨",
        "grateful": "🙏", "sad": "😢", "lonely": "🌙", "stressed": "😮‍💨",
        "nostalgic": "🌸", "hopeful": "🌅",
    ]

    @ViewBuilder
    private func moodPickerGrid(moods: [String], selected: String) -> some View {
        let columns = Array(repeating: GridItem(.flexible(), spacing: 6), count: 5)
        LazyVGrid(columns: columns, spacing: 6) {
            ForEach(moods, id: \.self) { mood in
                let isSelected = mood == selected
                Button {
                    selectedMood = mood
                    Task { await loadRecommendation(mood: mood) }
                } label: {
                    HStack(spacing: 3) {
                        Text(Self.moodEmojis[mood] ?? "🎵")
                            .font(.system(size: 11))
                        Text(mood.capitalized)
                            .font(.system(size: 10, weight: isSelected ? .semibold : .medium))
                            .lineLimit(1)
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 5)
                    .frame(maxWidth: .infinity)
                    .background(
                        Capsule().fill(
                            isSelected
                                ? AngelaTheme.primaryPurple
                                : AngelaTheme.backgroundLight.opacity(0.6)
                        )
                    )
                    .foregroundColor(isSelected ? .white : AngelaTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
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

    private var loadingView: some View {
        VStack(spacing: 12) {
            ProgressView()
                .scaleEffect(0.8)
                .progressViewStyle(CircularProgressViewStyle(tint: AngelaTheme.primaryPurple))
            Text("Loading...")
                .font(.system(size: 12))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    private func emptyView(message: String, icon: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 32))
                .foregroundColor(AngelaTheme.textTertiary.opacity(0.5))

            Text(message)
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Data Loading

    private func loadInitialData() async {
        isLoading = true
        defer { isLoading = false }

        // Load library and playlists in parallel
        async let lib = musicService.fetchLibrarySongs()
        async let pls = musicService.fetchUserPlaylists()
        async let songs = chatService.fetchOurSongs()

        let (libResult, plsResult, songsResult) = await (lib, pls, (try? songs) ?? [])
        librarySongs = libResult
        userPlaylists = plsResult

        // Convert Angela songs to DisplaySong, enriching with Apple Music art in background
        ourSongs = songsResult.map { DisplaySong(from: $0) }
        Task { await enrichOurSongsArtwork() }
    }

    private func onTabSelected(_ tab: QueueTab) async {
        switch tab {
        case .library:
            if librarySongs.isEmpty {
                isLoading = true
                librarySongs = await musicService.fetchLibrarySongs()
                isLoading = false
            }
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

    private func loadRecommendation(mood: String? = nil) async {
        isLoading = true
        defer { isLoading = false }
        recommendedDisplays = []

        do {
            recommendation = try await chatService.getRecommendation(mood: mood ?? selectedMood)

            // Build display list from songs array (or fallback to single song)
            let songList = recommendation?.songs ?? [recommendation?.song].compactMap { $0 }
            var displays = songList.map { DisplaySong(from: $0) }

            // Show immediately, then enrich artwork in background
            recommendedDisplays = displays

            // Enrich with Apple Music artwork
            for (index, song) in songList.enumerated() {
                if let mkSong = await musicService.searchAppleMusic(title: song.title, artist: song.artist) {
                    let artURL = mkSong.artwork?.url(width: 300, height: 300)
                    displays[index] = DisplaySong(from: song, artwork: artURL)
                    recommendedDisplays[index] = displays[index]
                }
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func performSearch() async {
        guard !searchQuery.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isLoading = true
        defer { isLoading = false }

        searchResults = await musicService.searchCatalog(query: searchQuery)
    }

    /// Enrich Our Songs with Apple Music album art (background)
    private func enrichOurSongsArtwork() async {
        for (index, song) in ourSongs.enumerated() {
            guard song.albumArtURL == nil, let angela = song.angelaSong else { continue }
            if let mkSong = await musicService.searchAppleMusic(title: angela.title, artist: angela.artist) {
                let artURL = mkSong.artwork?.url(width: 300, height: 300)
                ourSongs[index] = DisplaySong(from: angela, artwork: artURL)
            }
        }
    }
}
