//
//  BackendManager.swift
//  Pythia
//
//  Manages Python FastAPI backend lifecycle.
//  On launch: check if backend is already running → if not, find a free port and start it.
//

import Foundation
import Combine
import Network

class BackendManager: ObservableObject {
    static let shared = BackendManager()

    @Published var isRunning = false
    @Published var isConnected = false
    @Published var statusMessage = "Checking..."
    @Published var lastError: String?

    private var process: Process?
    private var healthCheckTimer: Timer?

    private init() {}

    // MARK: - Auto-Start (called from PythiaApp)

    /// Check if backend is already running on preferred port, if not start on a free port
    func autoStart() {
        statusMessage = "Checking backend..."

        // Try preferred port first
        checkBackendAt(port: APIConfig.preferredPort) { [weak self] alive in
            guard let self else { return }
            if alive {
                APIConfig.port = APIConfig.preferredPort
                DispatchQueue.main.async {
                    self.isRunning = true
                    self.isConnected = true
                    self.statusMessage = "Connected (port \(APIConfig.port))"
                }
            } else {
                // Find a free port and start server
                let freePort = self.findFreePort(startingFrom: APIConfig.preferredPort)
                APIConfig.port = freePort
                self.startServer(port: freePort)
            }
        }
    }

    // MARK: - Start Server

    private func startServer(port: Int) {
        let apiPath = findApiServerPath()
        guard !apiPath.isEmpty else {
            DispatchQueue.main.async {
                self.lastError = "Cannot find api_server.py"
                self.statusMessage = "Error: api_server.py not found"
            }
            return
        }

        DispatchQueue.main.async {
            self.statusMessage = "Starting on port \(port)..."
        }

        let pythonPaths = [
            "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
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

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: pythonPath)
        proc.arguments = [apiPath, "--port", String(port)]
        proc.currentDirectoryURL = URL(fileURLWithPath: (apiPath as NSString).deletingLastPathComponent)

        // Inherit environment so python can find packages
        var env = ProcessInfo.processInfo.environment
        env["PYTHONUNBUFFERED"] = "1"
        proc.environment = env

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        proc.standardOutput = outputPipe
        proc.standardError = errorPipe

        proc.terminationHandler = { [weak self] p in
            DispatchQueue.main.async {
                self?.isRunning = false
                self?.isConnected = false
                self?.statusMessage = "Stopped (exit: \(p.terminationStatus))"
                self?.stopHealthCheck()
            }
        }

        do {
            try proc.run()
            process = proc
            DispatchQueue.main.async {
                self.isRunning = true
                self.statusMessage = "Starting on port \(port)..."
            }

            // Wait for server to be ready, then health check
            DispatchQueue.global().asyncAfter(deadline: .now() + 2.0) { [weak self] in
                self?.waitForServer(port: port, attempts: 10)
            }
        } catch {
            DispatchQueue.main.async {
                self.lastError = error.localizedDescription
                self.statusMessage = "Failed: \(error.localizedDescription)"
            }
        }
    }

    /// Poll health endpoint until server responds (max attempts)
    private func waitForServer(port: Int, attempts: Int) {
        guard attempts > 0 else {
            DispatchQueue.main.async {
                self.statusMessage = "Server failed to start"
                self.isConnected = false
            }
            return
        }

        checkBackendAt(port: port) { [weak self] alive in
            if alive {
                DispatchQueue.main.async {
                    self?.isConnected = true
                    self?.statusMessage = "Connected (port \(port))"
                    self?.lastError = nil
                    self?.startHealthCheck()
                }
            } else {
                DispatchQueue.global().asyncAfter(deadline: .now() + 1.5) {
                    self?.waitForServer(port: port, attempts: attempts - 1)
                }
            }
        }
    }

    // MARK: - Stop Server

    func stopServer() {
        stopHealthCheck()
        guard let process = process, process.isRunning else { return }

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
        DispatchQueue.main.async {
            self.healthCheckTimer?.invalidate()
            self.healthCheckTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
                self?.checkHealth()
            }
        }
    }

    private func stopHealthCheck() {
        healthCheckTimer?.invalidate()
        healthCheckTimer = nil
    }

    func checkHealth() {
        checkBackendAt(port: APIConfig.port) { [weak self] alive in
            DispatchQueue.main.async {
                self?.isConnected = alive
                self?.statusMessage = alive ? "Connected (port \(APIConfig.port))" : "Connection lost"
            }
        }
    }

    // MARK: - Port Utilities

    /// Check if Pythia backend is responding at a given port
    private func checkBackendAt(port: Int, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "http://\(APIConfig.host):\(port)/api/health") else {
            completion(false)
            return
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 3.0

        URLSession.shared.dataTask(with: request) { data, response, error in
            guard error == nil,
                  let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                completion(false)
                return
            }
            completion(true)
        }.resume()
    }

    /// Find a free TCP port starting from the preferred port
    private func findFreePort(startingFrom start: Int) -> Int {
        for port in start...(start + 100) {
            if isPortAvailable(port) {
                return port
            }
        }
        return start // fallback
    }

    /// Check if a TCP port is available by attempting to bind
    private func isPortAvailable(_ port: Int) -> Bool {
        let socketFD = socket(AF_INET, SOCK_STREAM, 0)
        guard socketFD >= 0 else { return false }
        defer { close(socketFD) }

        var addr = sockaddr_in()
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_port = in_port_t(port).bigEndian
        addr.sin_addr.s_addr = inet_addr("127.0.0.1")

        var reuse: Int32 = 1
        setsockopt(socketFD, SOL_SOCKET, SO_REUSEADDR, &reuse, socklen_t(MemoryLayout<Int32>.size))

        let result = withUnsafePointer(to: &addr) { ptr in
            ptr.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockPtr in
                bind(socketFD, sockPtr, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        return result == 0
    }

    // MARK: - Find API Server Path

    private func findApiServerPath() -> String {
        // Dev path
        let devPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/MacOS/Pythia/api_server.py"
        if FileManager.default.fileExists(atPath: devPath) {
            return devPath
        }

        // Next to app bundle
        let bundlePath = Bundle.main.bundlePath
        let appDirectory = (bundlePath as NSString).deletingLastPathComponent
        let bundleApiPath = (appDirectory as NSString).appendingPathComponent("api_server.py")
        if FileManager.default.fileExists(atPath: bundleApiPath) {
            return bundleApiPath
        }

        // Bundle resource
        if let resourcePath = Bundle.main.path(forResource: "api_server", ofType: "py") {
            return resourcePath
        }

        return ""
    }

    deinit {
        stopServer()
    }
}
