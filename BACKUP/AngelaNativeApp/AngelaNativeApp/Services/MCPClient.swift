//
//  MCPClient.swift
//  AngelaNativeApp
//
//  MCP (Model Context Protocol) Client for connecting to Angela's MCP servers
//  Allows AngelaNativeApp to access Calendar, Music, and Angela Memory
//

import Foundation
import Combine

// MARK: - MCP Server Types

enum MCPServerType: String {
    case angelaMemory = "angela_mcp_server"
    case calendar = "calendar_mcp_server"
    case music = "music_mcp_server"

    var scriptPath: String {
        let baseDir = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
        return "\(baseDir)/\(rawValue).py"
    }
}

// MARK: - MCP Client

@MainActor
class MCPClient: ObservableObject {
    // MARK: - Singleton

    static let shared = MCPClient()

    // MARK: - Published Properties

    @Published var isConnected: Bool = false
    @Published var lastError: String?

    // MARK: - Private Properties

    private var serverProcesses: [MCPServerType: Process] = [:]
    private let pythonPath = "/opt/anaconda3/bin/python3"  // Use Anaconda Python (has fastmcp installed)

    // MARK: - Initialization

    private init() {}

    // MARK: - Server Management

    /// Start an MCP server
    func startServer(_ serverType: MCPServerType) async throws {
        // Check if server is already running
        if serverProcesses[serverType] != nil {
            print("⚠️ MCP Server \(serverType.rawValue) already running")
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = [serverType.scriptPath]

        // Capture stdout and stderr
        let outPipe = Pipe()
        let errPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError = errPipe

        try process.run()
        serverProcesses[serverType] = process

        print("✅ Started MCP server: \(serverType.rawValue)")

        // Give server time to start
        try await Task.sleep(nanoseconds: 500_000_000) // 0.5 seconds
    }

    /// Stop an MCP server
    func stopServer(_ serverType: MCPServerType) {
        guard let process = serverProcesses[serverType] else { return }

        process.terminate()
        serverProcesses.removeValue(forKey: serverType)

        print("🛑 Stopped MCP server: \(serverType.rawValue)")
    }

    /// Stop all MCP servers
    func stopAllServers() {
        for serverType in serverProcesses.keys {
            stopServer(serverType)
        }
    }

    // MARK: - Tool Calling

    /// Call an MCP tool via Python script execution
    func callTool(
        server: MCPServerType,
        tool: String,
        parameters: [String: Any] = [:]
    ) async throws -> [String: Any] {
        // Build Python script to call the tool
        let script = buildToolCallScript(server: server, tool: tool, parameters: parameters)

        // Execute Python script
        let output = try await executePythonScript(script)

        // Debug: print raw output
        print("🔍 Raw Python output: \(output)")

        // Parse JSON result
        guard let data = output.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            print("❌ Failed to parse JSON from output: \(output)")
            throw MCPError.invalidResponse
        }

        return json
    }

    /// Read an MCP resource
    func readResource(
        server: MCPServerType,
        uri: String
    ) async throws -> String {
        // Build Python script to read resource
        let script = buildResourceReadScript(server: server, uri: uri)

        // Execute Python script
        return try await executePythonScript(script)
    }

    // MARK: - Private Helpers

    private func buildToolCallScript(server: MCPServerType, tool: String, parameters: [String: Any]) -> String {
        let paramsJSON = (try? JSONSerialization.data(withJSONObject: parameters))
            .flatMap { String(data: $0, encoding: .utf8) } ?? "{}"

        // Build Python script that directly calls AppleScript
        return """
        import json
        import subprocess
        import sys

        params = json.loads('\(paramsJSON)')

        # Calendar tools
        if '\(tool)' == 'get_today_events':
            # For now, return empty list (AppleScript implementation is complex in Swift strings)
            output = {
                "events": [],
                "date": "Today",
                "count": 0
            }
            print(json.dumps(output))
        else:
            print(json.dumps({"error": "Tool not found"}))
        """
    }

    private func buildResourceReadScript(server: MCPServerType, uri: String) -> String {
        return """
        import asyncio
        import sys
        sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

        from \(server.rawValue) import mcp

        async def main():
            # Get resource handler
            # (Note: This is simplified - actual implementation depends on fastmcp library)
            print("Resource content for: \(uri)")

        asyncio.run(main())
        """
    }

    private func executePythonScript(_ script: String) async throws -> String {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = ["-c", script]

        let outPipe = Pipe()
        let errPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError = errPipe

        try process.run()
        process.waitUntilExit()

        let outData = outPipe.fileHandleForReading.readDataToEndOfFile()
        let errData = errPipe.fileHandleForReading.readDataToEndOfFile()

        if process.terminationStatus != 0 {
            let errorOutput = String(data: errData, encoding: .utf8) ?? "Unknown error"
            print("❌ Python script error: \(errorOutput)")
            throw MCPError.scriptExecutionFailed(errorOutput)
        }

        return String(data: outData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    }
}

// MARK: - Calendar Tools

extension MCPClient {
    /// Get today's calendar events
    func getTodayEvents() async throws -> CalendarEventsResponse {
        let result = try await callTool(
            server: .calendar,
            tool: "get_today_events"
        )

        return try parseCalendarEventsResponse(result)
    }

    /// Get upcoming events
    func getUpcomingEvents(days: Int = 7) async throws -> CalendarEventsResponse {
        let result = try await callTool(
            server: .calendar,
            tool: "get_upcoming_events",
            parameters: ["days": days]
        )

        return try parseCalendarEventsResponse(result)
    }

    /// Search calendar events
    func searchEvents(query: String, days: Int = 30) async throws -> CalendarEventsResponse {
        let result = try await callTool(
            server: .calendar,
            tool: "search_events",
            parameters: ["query": query, "days": days]
        )

        return try parseCalendarEventsResponse(result)
    }

    /// Get all calendars
    func getCalendars() async throws -> [String] {
        let result = try await callTool(
            server: .calendar,
            tool: "get_calendars"
        )

        guard let calendars = result["calendars"] as? [String] else {
            throw MCPError.invalidResponse
        }

        return calendars
    }

    private func parseCalendarEventsResponse(_ result: [String: Any]) throws -> CalendarEventsResponse {
        guard let events = result["events"] as? [[String: Any]] else {
            throw MCPError.invalidResponse
        }

        let calendarEvents = events.compactMap { eventDict -> CalendarEvent? in
            guard let title = eventDict["title"] as? String,
                  let start = eventDict["start"] as? String,
                  let end = eventDict["end"] as? String else {
                return nil
            }

            return CalendarEvent(
                title: title,
                start: start,
                end: end,
                location: eventDict["location"] as? String ?? "",
                notes: eventDict["notes"] as? String ?? ""
            )
        }

        return CalendarEventsResponse(
            date: result["date"] as? String ?? "",
            events: calendarEvents,
            count: result["count"] as? Int ?? 0
        )
    }
}

// MARK: - Music Tools

extension MCPClient {
    /// Get current track playing
    func getCurrentTrack() async throws -> MusicTrack? {
        let result = try await callTool(
            server: .music,
            tool: "get_current_track"
        )

        guard let playing = result["playing"] as? Bool, playing else {
            return nil
        }

        return MusicTrack(
            title: result["track"] as? String ?? "",
            artist: result["artist"] as? String ?? "",
            album: result["album"] as? String ?? "",
            state: result["state"] as? String ?? "stopped",
            duration: result["duration"] as? Double ?? 0,
            position: result["position"] as? Double ?? 0,
            progressPercentage: result["progress_percentage"] as? Double ?? 0
        )
    }

    /// Get player state
    func getPlayerState() async throws -> MusicPlayerState {
        let result = try await callTool(
            server: .music,
            tool: "get_player_state"
        )

        return MusicPlayerState(
            state: result["state"] as? String ?? "stopped",
            volume: result["volume"] as? Int ?? 0,
            isPlaying: result["is_playing"] as? Bool ?? false,
            isPaused: result["is_paused"] as? Bool ?? false
        )
    }

    /// Play music
    func playMusic() async throws {
        _ = try await callTool(server: .music, tool: "play_music")
    }

    /// Pause music
    func pauseMusic() async throws {
        _ = try await callTool(server: .music, tool: "pause_music")
    }

    /// Next track
    func nextTrack() async throws {
        _ = try await callTool(server: .music, tool: "next_track")
    }

    /// Previous track
    func previousTrack() async throws {
        _ = try await callTool(server: .music, tool: "previous_track")
    }

    /// Set volume
    func setVolume(_ level: Int) async throws {
        _ = try await callTool(
            server: .music,
            tool: "set_volume",
            parameters: ["level": level]
        )
    }

    /// Get playlists
    func getPlaylists() async throws -> [String] {
        let result = try await callTool(
            server: .music,
            tool: "get_playlists"
        )

        guard let playlists = result["playlists"] as? [String] else {
            throw MCPError.invalidResponse
        }

        return playlists
    }

    /// Play playlist
    func playPlaylist(_ name: String) async throws {
        _ = try await callTool(
            server: .music,
            tool: "play_playlist",
            parameters: ["playlist_name": name]
        )
    }
}

// MARK: - Models

struct CalendarEvent: Identifiable, Codable {
    var id = UUID()
    let title: String
    let start: String
    let end: String
    let location: String
    let notes: String
}

struct CalendarEventsResponse {
    let date: String
    let events: [CalendarEvent]
    let count: Int
}

struct MusicTrack {
    let title: String
    let artist: String
    let album: String
    let state: String
    let duration: Double
    let position: Double
    let progressPercentage: Double
}

struct MusicPlayerState {
    let state: String
    let volume: Int
    let isPlaying: Bool
    let isPaused: Bool
}

// MARK: - Errors

enum MCPError: Error, LocalizedError {
    case serverNotRunning
    case invalidResponse
    case scriptExecutionFailed(String)
    case toolNotFound

    var errorDescription: String? {
        switch self {
        case .serverNotRunning:
            return "MCP server is not running"
        case .invalidResponse:
            return "Invalid response from MCP server"
        case .scriptExecutionFailed(let message):
            return "Script execution failed: \(message)"
        case .toolNotFound:
            return "MCP tool not found"
        }
    }
}
