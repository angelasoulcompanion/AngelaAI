//
//  MusicPlayerService.swift
//  Angela Brain Dashboard
//
//  MusicKit wrapper for DJ Angela vinyl player
//

import Foundation
import MusicKit
import Combine
import AppKit
import os.log

private let djLog = Logger(subsystem: "com.david.angela", category: "DJAngela")

@MainActor
final class MusicPlayerService: ObservableObject {

    static let shared = MusicPlayerService()

    // MARK: - Published State

    @Published var isAuthorized = false
    @Published var isPlaying = false
    @Published var nowPlaying: NowPlayingInfo?
    @Published var queue: [DisplaySong] = []
    @Published var currentQueueIndex: Int = 0
    @Published var authorizationError: String?
    @Published var playbackError: String?
    @Published var hasSubscription = true
    @Published var libraryLoaded = false
    @Published var playlists: [MusicKit.Playlist] = []

    /// Set by SongQueueView to track which tab the user played from
    @Published var currentSourceTab: String?

    /// User-selected activity (wine, working, relaxing, etc.) — overrides auto-detected occasion
    @Published var currentActivity: String? {
        didSet {
            // Clear wine type when switching away from wine activity
            if currentActivity != "wine" {
                currentWineType = nil
            }
        }
    }

    /// Selected wine varietal when activity is "wine"
    @Published var currentWineType: String?

    /// Whether the currently playing song is marked as "our song"
    @Published var currentSongIsOurSong = false

    // MARK: - Private

    private let player = ApplicationMusicPlayer.shared
    private var positionTimer: Timer?
    private var searchCache: [String: MusicKit.Song] = [:]
    private var currentListenId: String?

    private init() {
        checkAuthorizationStatus()
    }

    // MARK: - Authorization

    func checkAuthorizationStatus() {
        let status = MusicAuthorization.currentStatus
        isAuthorized = (status == .authorized)
    }

    func requestAuthorization() async {
        let status = await MusicAuthorization.request()
        isAuthorized = (status == .authorized)
        if status == .denied {
            authorizationError = "Apple Music access denied. Enable in System Settings > Privacy > Media & Apple Music."
        }
        if isAuthorized {
            await checkSubscription()
        }
    }

    private func checkSubscription() async {
        do {
            let subscription = try await MusicSubscription.current
            hasSubscription = subscription.canPlayCatalogContent
            if !hasSubscription {
                playbackError = "Apple Music subscription required to play songs. Opening in Apple Music app instead."
            }
        } catch {
            print("[MusicPlayerService] Subscription check error: \(error)")
        }
    }

    // MARK: - Search Apple Music

    func searchAppleMusic(title: String, artist: String?) async -> MusicKit.Song? {
        let query: String
        if let artist, !artist.isEmpty {
            query = "\(title) \(artist)"
        } else {
            query = title
        }

        // Check cache
        if let cached = searchCache[query] {
            return cached
        }

        do {
            var request = MusicCatalogSearchRequest(term: query, types: [MusicKit.Song.self])
            request.limit = 5
            let response = try await request.response()

            if let song = response.songs.first {
                searchCache[query] = song
                return song
            }

            // Fallback: search title only
            if artist != nil {
                var fallbackRequest = MusicCatalogSearchRequest(term: title, types: [MusicKit.Song.self])
                fallbackRequest.limit = 5
                let fallbackResponse = try await fallbackRequest.response()
                if let song = fallbackResponse.songs.first {
                    searchCache[query] = song
                    return song
                }
            }
            playbackError = "Song not found on Apple Music: \(query)"
        } catch {
            playbackError = "Search error: \(error.localizedDescription)"
            print("[MusicPlayerService] Search error: \(error)")
        }

        return nil
    }

    // MARK: - iTunes Search API (REST fallback for artwork)

    /// Artwork URL cache (iTunes API results)
    private var iTunesArtworkCache: [String: URL] = [:]

    /// Fetch album artwork URL via iTunes Search API (no MusicKit dependency).
    /// Uses standard URLSession — works even when MusicKit times out.
    func fetchArtworkFromiTunes(title: String, artist: String?) async -> URL? {
        var term = title
        if let artist, !artist.isEmpty {
            term += " \(artist)"
        }

        // Check cache
        if let cached = iTunesArtworkCache[term] { return cached }

        guard let encoded = term.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "https://itunes.apple.com/search?term=\(encoded)&media=music&entity=song&limit=1") else {
            return nil
        }

        djLog.notice("[iTunes-Art] Fetching artwork for: \(term)")
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let results = json["results"] as? [[String: Any]],
               let first = results.first,
               let artworkStr = first["artworkUrl100"] as? String {
                // Scale up: 100x100 → 300x300
                let scaled = artworkStr.replacingOccurrences(of: "100x100", with: "300x300")
                if let artURL = URL(string: scaled) {
                    iTunesArtworkCache[term] = artURL
                    djLog.notice("[iTunes-Art] Got artwork: \(artURL)")
                    return artURL
                }
            }
            djLog.notice("[iTunes-Art] No results for: \(term)")
        } catch {
            djLog.notice("[iTunes-Art] Error: \(error)")
        }

        return nil
    }

    // MARK: - iTunes Search API (catalog search — no MusicKit dependency)

    /// Search iTunes catalog via REST API. Returns songs with artwork.
    /// Use this when MusicKit catalog search times out.
    func searchiTunes(query: String, limit: Int = 25) async -> [(title: String, artist: String, album: String?, artworkURL: URL?, durationSeconds: TimeInterval?)] {
        guard let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "https://itunes.apple.com/search?term=\(encoded)&media=music&entity=song&limit=\(limit)") else {
            djLog.notice("[iTunes] Bad URL for query: \(query)")
            return []
        }

        djLog.notice("[iTunes] Searching: \(url.absoluteString)")
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let results = json["results"] as? [[String: Any]] else {
                djLog.notice("[iTunes] Bad JSON response")
                return []
            }

            let songs = results.compactMap { item -> (title: String, artist: String, album: String?, artworkURL: URL?, durationSeconds: TimeInterval?)? in
                guard let title = item["trackName"] as? String,
                      let artist = item["artistName"] as? String else { return nil }
                let album = item["collectionName"] as? String
                let artworkStr = (item["artworkUrl100"] as? String)?
                    .replacingOccurrences(of: "100x100", with: "300x300")
                let artworkURL = artworkStr.flatMap { URL(string: $0) }
                let durationMs = item["trackTimeMillis"] as? Int
                let durationSeconds = durationMs.map { TimeInterval($0) / 1000.0 }
                return (title: title, artist: artist, album: album, artworkURL: artworkURL, durationSeconds: durationSeconds)
            }
            djLog.notice("[iTunes] Found \(songs.count) songs for '\(query)'")
            return songs
        } catch {
            djLog.notice("[iTunes] Search error: \(error)")
            return []
        }
    }

    // MARK: - Play from Angela Song (DB -> Apple Music)

    func playFromAngelaSong(_ song: Song) async -> Bool {
        playbackError = nil

        if !isAuthorized {
            await requestAuthorization()
            guard isAuthorized else { return false }
        }

        // If no subscription, open in Apple Music app directly
        if !hasSubscription {
            openInAppleMusic(song)
            // Still update nowPlaying for UI display (without actual playback)
            nowPlaying = NowPlayingInfo(
                title: song.title,
                artist: song.artist ?? "Unknown Artist",
                albumArtURL: nil,
                duration: 0,
                currentTime: 0,
                angelaSong: song
            )
            return false
        }

        if let musicKitSong = await searchAppleMusic(title: song.title, artist: song.artist) {
            return await playSong(musicKitSong, angelaSong: song)
        }

        // Not found on Apple Music — open URL in browser if available
        openInAppleMusic(song)
        return false
    }

    private func openInAppleMusic(_ song: Song) {
        // Build Apple Music search URL as fallback
        let searchTerm = "\(song.title) \(song.artist ?? "")".addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        if let url = URL(string: "https://music.apple.com/search?term=\(searchTerm)") {
            NSWorkspace.shared.open(url)
        }
    }

    // MARK: - Play MusicKit Song

    @discardableResult
    func playSong(_ song: MusicKit.Song, angelaSong: Song? = nil) async -> Bool {
        // Finalize previous song if any
        if let prev = nowPlaying {
            let status = prev.duration > 0 && prev.currentTime >= prev.duration - 1 ? "completed" : "skipped"
            finalizeCurrentPlay(listenedSeconds: prev.currentTime, playStatus: status)
        }

        do {
            player.queue = [song]
            try await player.play()
            isPlaying = true
            playbackError = nil

            let artworkURL = song.artwork?.url(width: 500, height: 500)
            nowPlaying = NowPlayingInfo(
                title: song.title,
                artist: song.artistName,
                albumArtURL: artworkURL,
                duration: song.duration ?? 0,
                currentTime: 0,
                angelaSong: angelaSong
            )

            currentSongIsOurSong = angelaSong?.isOurSong ?? false

            startPositionTracking()

            // Log play started (captures listen_id for later update)
            logPlay(
                title: song.title,
                artist: song.artistName,
                album: song.albumTitle,
                appleMusicId: song.id.rawValue,
                sourceTab: currentSourceTab,
                durationSeconds: song.duration,
                listenedSeconds: nil,
                playStatus: "started"
            )

            return true
        } catch {
            playbackError = "Playback error: \(error.localizedDescription)"
            print("[MusicPlayerService] Play error: \(error)")

            // Still show the song info even if playback failed
            let artworkURL = song.artwork?.url(width: 500, height: 500)
            nowPlaying = NowPlayingInfo(
                title: song.title,
                artist: song.artistName,
                albumArtURL: artworkURL,
                duration: song.duration ?? 0,
                currentTime: 0,
                angelaSong: angelaSong
            )
            return false
        }
    }

    // MARK: - Playback Controls

    func pause() {
        player.pause()
        isPlaying = false
    }

    func resume() async {
        do {
            try await player.play()
            isPlaying = true
        } catch {
            playbackError = "Resume error: \(error.localizedDescription)"
            print("[MusicPlayerService] Resume error: \(error)")
        }
    }

    func togglePlayPause() async {
        if isPlaying {
            pause()
        } else {
            await resume()
        }
    }

    func skipToNext() async {
        // playSong() will finalize the current song automatically
        guard !queue.isEmpty else { return }
        let nextIndex = currentQueueIndex + 1
        guard nextIndex < queue.count else { return }
        currentQueueIndex = nextIndex
        await playDisplaySong(queue[nextIndex])
    }

    func skipToPrevious() async {
        guard !queue.isEmpty else { return }
        // If more than 3 seconds in, restart current song
        if let now = nowPlaying, now.currentTime > 3 {
            await seekTo(0)
            return
        }
        let prevIndex = currentQueueIndex - 1
        guard prevIndex >= 0 else { return }
        currentQueueIndex = prevIndex
        await playDisplaySong(queue[prevIndex])
    }

    func seekTo(_ time: TimeInterval) async {
        player.playbackTime = time
        nowPlaying?.currentTime = time
    }

    // MARK: - Play DisplaySong (unified entry point)

    @discardableResult
    func playDisplaySong(_ displaySong: DisplaySong) async -> Bool {
        // If we have a MusicKit song, play directly
        if let mkSong = displaySong.musicKitSong {
            return await playSong(mkSong, angelaSong: displaySong.angelaSong)
        }
        // Otherwise, it's an Angela song — search Apple Music first
        if let angela = displaySong.angelaSong {
            return await playFromAngelaSong(angela)
        }
        return false
    }

    // MARK: - Queue Management

    func setQueue(_ songs: [DisplaySong], startAt index: Int = 0) {
        queue = songs
        currentQueueIndex = index
    }

    /// Legacy overload for Angela Song arrays
    func setQueue(_ songs: [Song], startAt index: Int = 0) {
        queue = songs.map { DisplaySong(from: $0) }
        currentQueueIndex = index
    }

    func addToQueue(_ song: DisplaySong) {
        queue.append(song)
    }

    // MARK: - Apple Music Library

    /// Fetch user's recently played songs (most recent first)
    func fetchLibrarySongs(limit: Int = 50) async -> [MusicKit.Song] {
        guard isAuthorized else { return [] }
        do {
            var request = MusicLibraryRequest<MusicKit.Song>()
            request.sort(by: \.lastPlayedDate, ascending: false)
            request.limit = limit
            let response = try await request.response()
            libraryLoaded = true
            // Only include songs that have actually been played
            return Array(response.items).filter { $0.lastPlayedDate != nil }
        } catch {
            print("[MusicPlayerService] Recently played fetch error: \(error)")
            return []
        }
    }

    /// Fetch user's playlists
    func fetchUserPlaylists() async -> [MusicKit.Playlist] {
        guard isAuthorized else { return [] }
        do {
            var request = MusicLibraryRequest<MusicKit.Playlist>()
            request.limit = 50
            let response = try await request.response()
            playlists = Array(response.items)
            return playlists
        } catch {
            print("[MusicPlayerService] Playlists fetch error: \(error)")
            return []
        }
    }

    /// Fetch all tracks in a playlist (handles pagination for large playlists)
    func fetchPlaylistTracks(_ playlist: MusicKit.Playlist) async -> [MusicKit.Song] {
        do {
            let detailedPlaylist = try await playlist.with([.tracks])
            guard var tracks = detailedPlaylist.tracks else { return [] }

            var allSongs: [MusicKit.Song] = []

            // First batch — maintains Apple Music playlist order
            for track in tracks {
                if case .song(let song) = track {
                    allSongs.append(song)
                }
            }

            // Paginate remaining batches (large playlists like Favourite Songs)
            while tracks.hasNextBatch {
                guard let next = try await tracks.nextBatch() else { break }
                tracks = next
                for track in tracks {
                    if case .song(let song) = track {
                        allSongs.append(song)
                    }
                }
            }

            return allSongs
        } catch {
            print("[MusicPlayerService] Playlist tracks fetch error: \(error)")
            return []
        }
    }

    /// Search Apple Music catalog (returns songs with artwork)
    func searchCatalog(query: String, limit: Int = 25) async -> [MusicKit.Song] {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else { return [] }
        do {
            var request = MusicCatalogSearchRequest(term: query, types: [MusicKit.Song.self])
            request.limit = limit
            let response = try await request.response()
            return Array(response.songs)
        } catch {
            print("[MusicPlayerService] Catalog search error: \(error)")
            return []
        }
    }

    // MARK: - User Playlist Song Pool

    /// Cached pool of all songs from the user's Apple Music playlists.
    /// Grouped by playlist name for mood-based filtering.
    private var _playlistPool: [(name: String, songs: [MusicKit.Song])] = []
    private var _poolLoaded = false

    /// Load all songs from all user playlists (concurrent, cached after first call).
    /// Returns songs grouped by playlist name so callers can filter by playlist mood.
    func loadPlaylistSongPool() async -> [(name: String, songs: [MusicKit.Song])] {
        if _poolLoaded { return _playlistPool }

        let allPlaylists = await fetchUserPlaylists()
        var result: [(name: String, songs: [MusicKit.Song])] = Array(
            repeating: (name: "", songs: []), count: allPlaylists.count
        )

        // Load all playlists concurrently for speed
        await withTaskGroup(of: (Int, String, [MusicKit.Song]).self) { group in
            for (i, playlist) in allPlaylists.enumerated() {
                group.addTask {
                    let tracks = await self.fetchPlaylistTracks(playlist)
                    return (i, playlist.name, tracks)
                }
            }
            for await (i, name, tracks) in group {
                result[i] = (name: name, songs: tracks)
            }
        }

        // Remove empty playlists
        result = result.filter { !$0.songs.isEmpty }
        _playlistPool = result
        _poolLoaded = true
        print("[MusicPlayerService] Playlist pool loaded: \(result.count) playlists, \(result.map(\.songs.count).reduce(0, +)) songs total")
        return result
    }

    /// Invalidate the cached pool (e.g., after user modifies playlists).
    func invalidatePlaylistPool() {
        _poolLoaded = false
        _playlistPool = []
    }

    /// Set queue from MusicKit songs
    func setMusicKitQueue(_ songs: [MusicKit.Song], startAt index: Int = 0) {
        queue = songs.map { DisplaySong(from: $0) }
        currentQueueIndex = index
    }

    // MARK: - Position Tracking (every 0.5s)

    private func startPositionTracking() {
        stopPositionTracking()
        positionTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            guard let self else { return }
            Task { @MainActor [weak self] in
                self?.updatePosition()
            }
        }
    }

    private func stopPositionTracking() {
        positionTimer?.invalidate()
        positionTimer = nil
    }

    private func updatePosition() {
        guard isPlaying, nowPlaying != nil else { return }
        let currentTime = player.playbackTime
        nowPlaying?.currentTime = currentTime

        // Auto-advance when song ends
        if let duration = nowPlaying?.duration, duration > 0, currentTime >= duration - 0.5 {
            // Update the existing row to "completed"
            finalizeCurrentPlay(listenedSeconds: duration, playStatus: "completed")

            Task {
                await autoAdvanceToNext()
            }
        }
    }

    /// Advance to next song without logging a skip (used for auto-advance after completion).
    private func autoAdvanceToNext() async {
        guard !queue.isEmpty else { return }
        let nextIndex = currentQueueIndex + 1
        guard nextIndex < queue.count else { return }
        currentQueueIndex = nextIndex
        await playDisplaySong(queue[nextIndex])
    }

    // MARK: - Play Logging (fire-and-forget to API)

    private func logPlay(
        title: String,
        artist: String,
        album: String?,
        appleMusicId: String?,
        sourceTab: String?,
        durationSeconds: Double?,
        listenedSeconds: Double?,
        playStatus: String
    ) {
        let activity = currentActivity
        let wineType = currentWineType
        let capturedStatus = playStatus
        Task { @MainActor [weak self] in
            let body = PlayLogBody(
                title: title,
                artist: artist,
                album: album,
                appleMusicId: appleMusicId,
                sourceTab: sourceTab,
                durationSeconds: durationSeconds,
                listenedSeconds: listenedSeconds,
                playStatus: capturedStatus,
                activity: activity,
                wineType: wineType
            )
            let response: PlayLogResponse? = try? await NetworkService.shared.post("/api/music/log-play", body: body)
            if capturedStatus == "started", let id = response?.listenId {
                self?.currentListenId = id
            }
        }
    }

    /// Update the existing "started" row with final listened_seconds and play_status.
    private func finalizeCurrentPlay(listenedSeconds: Double, playStatus: String) {
        guard let listenId = currentListenId else { return }
        currentListenId = nil
        Task {
            let body = PlayLogUpdateBody(listenedSeconds: listenedSeconds, playStatus: playStatus)
            let _: PlayLogUpdateResponse? = try? await NetworkService.shared.post(
                "/api/music/log-play/\(listenId)/update", body: body
            )
        }
    }

    // MARK: - Our Song Toggle

    func toggleOurSong() {
        guard let now = nowPlaying else { return }
        let newValue = !currentSongIsOurSong
        currentSongIsOurSong = newValue
        Task {
            let body = MarkOurSongBody(title: now.title, artist: now.artist, isOurSong: newValue)
            let _: MarkOurSongResponse? = try? await NetworkService.shared.post(
                "/api/music/mark-our-song", body: body
            )
        }
    }

    // MARK: - Cleanup

    func stop() {
        // Finalize current song before stopping
        if let now = nowPlaying {
            finalizeCurrentPlay(listenedSeconds: now.currentTime, playStatus: "stopped")
        }
        player.pause()
        isPlaying = false
        nowPlaying = nil
        stopPositionTracking()
    }
}
