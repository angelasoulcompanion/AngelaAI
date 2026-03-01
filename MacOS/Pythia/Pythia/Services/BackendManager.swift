//
//  BackendManager.swift
//  Pythia
//
//  Manages Python FastAPI backend lifecycle (port 8766)
//

import Foundation
import Combine

class BackendManager: ObservableObject {
    static let shared = BackendManager()

    @Published var isRunning = false
    @Published var isConnected = false
    @Published var statusMessage = "Not started"
    @Published var lastError: String?

    private var process: Process?
    private var healthCheckTimer: Timer?
    private let baseURL = APIConfig.baseURL

    private init() {}

    // MARK: - Start Server

    func startServer() {
        guard !isRunning else { return }

        let apiPath = findApiServerPath()
        guard !apiPath.isEmpty else {
            lastError = "Cannot find api_server.py"
            statusMessage = "Error: api_server.py not found"
            return
        }

        statusMessage = "Starting..."

        let pythonPaths = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]

        var pythonPath = "/usr/bin/python3"
        for path in pythonPaths {
            if FileManager.default.fileExists(atPath: path) {
                pythonPath = path
                break
            }
        }

        process = Process()
        process?.executableURL = URL(fileURLWithPath: pythonPath)
        process?.arguments = [apiPath]
        process?.currentDirectoryURL = URL(fileURLWithPath: (apiPath as NSString).deletingLastPathComponent)

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process?.standardOutput = outputPipe
        process?.standardError = errorPipe

        process?.terminationHandler = { [weak self] process in
            DispatchQueue.main.async {
                self?.isRunning = false
                self?.isConnected = false
                self?.statusMessage = "Stopped (exit: \(process.terminationStatus))"
                self?.stopHealthCheck()
            }
        }

        do {
            try process?.run()
            isRunning = true
            statusMessage = "Starting backend..."

            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) { [weak self] in
                self?.checkHealth()
                self?.startHealthCheck()
            }
        } catch {
            lastError = error.localizedDescription
            statusMessage = "Failed to start: \(error.localizedDescription)"
        }
    }

    // MARK: - Stop Server

    func stopServer() {
        stopHealthCheck()
        guard let process = process, isRunning else { return }

        process.terminate()
        DispatchQueue.global().async {
            process.waitUntilExit()
            DispatchQueue.main.async {
                self.process = nil
                self.isRunning = false
                self.isConnected = false
                self.statusMessage = "Stopped"
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
                if error != nil {
                    self?.isConnected = false
                    self?.statusMessage = "Connection error"
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200 else {
                    self?.isConnected = false
                    self?.statusMessage = "Server not responding"
                    return
                }

                self?.isConnected = true
                self?.statusMessage = "Connected to Pythia"
                self?.lastError = nil
            }
        }.resume()
    }

    // MARK: - Find API Server Path

    private func findApiServerPath() -> String {
        let bundlePath = Bundle.main.bundlePath
        let appDirectory = (bundlePath as NSString).deletingLastPathComponent
        let bundleApiPath = (appDirectory as NSString).appendingPathComponent("api_server.py")

        if FileManager.default.fileExists(atPath: bundleApiPath) {
            return bundleApiPath
        }

        let devPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/MacOS/Pythia/api_server.py"
        if FileManager.default.fileExists(atPath: devPath) {
            return devPath
        }

        if let resourcePath = Bundle.main.path(forResource: "api_server", ofType: "py") {
            return resourcePath
        }

        return ""
    }

    deinit {
        stopServer()
    }
}
