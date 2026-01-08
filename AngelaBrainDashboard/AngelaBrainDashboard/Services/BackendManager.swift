//
//  BackendManager.swift
//  Angela Brain Dashboard
//
//  Manages Python FastAPI backend lifecycle
//  Automatically starts/stops with app
//
//  Created: 2026-01-08
//

import Foundation
import Combine

/// Manages the Python FastAPI backend process
class BackendManager: ObservableObject {
    static let shared = BackendManager()

    @Published var isRunning = false
    @Published var isConnected = false
    @Published var statusMessage = "Not started"
    @Published var lastError: String?

    private var process: Process?
    private var healthCheckTimer: Timer?
    private let baseURL = "http://127.0.0.1:8765"

    private init() {}

    // MARK: - Start Server

    func startServer() {
        guard !isRunning else {
            print("💜 Backend already running")
            return
        }

        // Find api_server.py path
        let apiPath = findApiServerPath()
        guard !apiPath.isEmpty else {
            lastError = "Cannot find api_server.py"
            statusMessage = "Error: api_server.py not found"
            print("❌ Cannot find api_server.py")
            print("   Searched paths:")
            print("   - Bundle: \(Bundle.main.bundlePath)")
            print("   - Dev: /Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaBrainDashboard/api_server.py")
            return
        }

        print("🚀 Starting backend from: \(apiPath)")
        statusMessage = "Starting..."

        // Find python3 - try multiple locations
        let pythonPaths = [
            "/opt/homebrew/bin/python3",  // Homebrew on Apple Silicon
            "/usr/local/bin/python3",      // Homebrew on Intel
            "/usr/bin/python3"             // System Python
        ]

        var pythonPath = "/usr/bin/python3"
        for path in pythonPaths {
            if FileManager.default.fileExists(atPath: path) {
                pythonPath = path
                break
            }
        }

        print("🐍 Using Python: \(pythonPath)")

        // Create and configure process
        process = Process()
        process?.executableURL = URL(fileURLWithPath: pythonPath)
        process?.arguments = [apiPath]
        process?.currentDirectoryURL = URL(fileURLWithPath: (apiPath as NSString).deletingLastPathComponent)

        // Capture output for debugging (can change to nullDevice in production)
        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process?.standardOutput = outputPipe
        process?.standardError = errorPipe

        // Handle termination
        process?.terminationHandler = { [weak self] process in
            DispatchQueue.main.async {
                self?.isRunning = false
                self?.isConnected = false
                self?.statusMessage = "Stopped (exit: \(process.terminationStatus))"
                self?.stopHealthCheck()
                print("🛑 Backend stopped with exit code: \(process.terminationStatus)")
            }
        }

        do {
            try process?.run()
            isRunning = true
            statusMessage = "Starting backend..."

            // Wait for server to be ready
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) { [weak self] in
                self?.checkHealth()
                self?.startHealthCheck()
            }

            print("✅ Backend process started (PID: \(process?.processIdentifier ?? 0))")
        } catch {
            lastError = error.localizedDescription
            statusMessage = "Failed to start: \(error.localizedDescription)"
            print("❌ Failed to start backend: \(error)")
        }
    }

    // MARK: - Stop Server

    func stopServer() {
        stopHealthCheck()

        guard let process = process, isRunning else {
            print("No backend process to stop")
            return
        }

        process.terminate()

        // Wait for graceful shutdown
        DispatchQueue.global().async {
            process.waitUntilExit()
            DispatchQueue.main.async {
                self.process = nil
                self.isRunning = false
                self.isConnected = false
                self.statusMessage = "Stopped"
                print("Backend stopped")
            }
        }
    }

    // MARK: - Health Check

    private func startHealthCheck() {
        healthCheckTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            self?.checkHealth()
        }
    }

    private func stopHealthCheck() {
        healthCheckTimer?.invalidate()
        healthCheckTimer = nil
    }

    func checkHealth() {
        guard let url = URL(string: "\(baseURL)/api/health") else { return }

        var request = URLRequest(url: url)
        request.timeoutInterval = 5.0

        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    self?.isConnected = false
                    self?.statusMessage = "Connection error"
                    self?.lastError = error.localizedDescription
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200 else {
                    self?.isConnected = false
                    self?.statusMessage = "Server not responding"
                    return
                }

                self?.isConnected = true
                self?.statusMessage = "Connected to Neon Cloud"
                self?.lastError = nil
            }
        }.resume()
    }

    // MARK: - Find API Server Path

    private func findApiServerPath() -> String {
        // 1. Try relative to app bundle (for deployed app)
        let bundlePath = Bundle.main.bundlePath
        let appDirectory = (bundlePath as NSString).deletingLastPathComponent
        let bundleApiPath = (appDirectory as NSString).appendingPathComponent("api_server.py")

        if FileManager.default.fileExists(atPath: bundleApiPath) {
            return bundleApiPath
        }

        // 2. Try development path
        let devPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/AngelaBrainDashboard/api_server.py"
        if FileManager.default.fileExists(atPath: devPath) {
            return devPath
        }

        // 3. Try inside Resources folder
        if let resourcePath = Bundle.main.path(forResource: "api_server", ofType: "py") {
            return resourcePath
        }

        return ""
    }

    // MARK: - Deinit

    deinit {
        stopServer()
    }
}

// MARK: - API Client Extension

extension BackendManager {

    /// Make a GET request to the API
    func get<T: Decodable>(_ endpoint: String) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw BackendError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 30.0

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw BackendError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw BackendError.httpError(statusCode: httpResponse.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        return try decoder.decode(T.self, from: data)
    }

    /// Make a GET request and return raw Data
    func getData(_ endpoint: String) async throws -> Data {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw BackendError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 30.0

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw BackendError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw BackendError.httpError(statusCode: httpResponse.statusCode)
        }

        return data
    }
}

// MARK: - Backend Errors

enum BackendError: Error, LocalizedError {
    case notRunning
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .notRunning:
            return "Backend is not running"
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        }
    }
}
