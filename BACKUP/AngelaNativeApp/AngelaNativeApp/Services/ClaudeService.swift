//
//  ClaudeService.swift
//  AngelaNativeApp
//
//  Service for executing terminal commands and communicating with Claude Code
//

import Foundation
import Combine

class ClaudeService: ObservableObject {
    static let shared = ClaudeService()

    private init() {}

    // MARK: - Terminal Command Execution

    /// Execute a shell command and return the output
    /// This gives Angela the ability to interact with the system like a terminal
    func executeCommand(_ command: String, arguments: [String] = []) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            let process = Process()
            let pipe = Pipe()
            let errorPipe = Pipe()

            process.executableURL = URL(fileURLWithPath: "/bin/bash")
            process.arguments = ["-c", command]
            process.standardOutput = pipe
            process.standardError = errorPipe

            do {
                try process.run()
                process.waitUntilExit()

                let outputData = pipe.fileHandleForReading.readDataToEndOfFile()
                let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()

                if process.terminationStatus == 0 {
                    let output = String(data: outputData, encoding: .utf8) ?? ""
                    continuation.resume(returning: output)
                } else {
                    let errorOutput = String(data: errorData, encoding: .utf8) ?? "Unknown error"
                    continuation.resume(throwing: CommandError.executionFailed(errorOutput))
                }
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }

    /// Execute Claude Code command
    func executeClaudeCode(_ prompt: String) async throws -> String {
        // Execute Claude Code CLI with the prompt
        let command = "claude \"\(prompt)\""
        return try await executeCommand(command)
    }

    /// Execute Python script
    func executePython(script: String, arguments: [String] = []) async throws -> String {
        let pythonPath = "/usr/local/bin/python3"
        let scriptPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/\(script)"
        let argsString = arguments.joined(separator: " ")
        let command = "\(pythonPath) \(scriptPath) \(argsString)"
        return try await executeCommand(command)
    }

    // MARK: - System Access

    /// Read file from file system
    func readFile(path: String) async throws -> String {
        let command = "cat \"\(path)\""
        return try await executeCommand(command)
    }

    /// Write to file
    func writeFile(path: String, content: String) async throws {
        let escapedContent = content.replacingOccurrences(of: "\"", with: "\\\"")
        let command = "echo \"\(escapedContent)\" > \"\(path)\""
        _ = try await executeCommand(command)
    }

    /// List files in directory
    func listFiles(directory: String) async throws -> [String] {
        let command = "ls -1 \"\(directory)\""
        let output = try await executeCommand(command)
        return output.components(separatedBy: "\n").filter { !$0.isEmpty }
    }

    /// Check PostgreSQL database status
    func checkDatabase() async throws -> String {
        let command = "psql -d AngelaMemory -c 'SELECT COUNT(*) FROM conversations;'"
        return try await executeCommand(command)
    }

    /// Check Ollama status
    func checkOllama() async throws -> Bool {
        do {
            let command = "curl -s http://localhost:11434"
            _ = try await executeCommand(command)
            return true
        } catch {
            return false
        }
    }

    /// Get system information
    func getSystemInfo() async throws -> SystemInfo {
        let cpuCommand = "sysctl -n machdep.cpu.brand_string"
        let memCommand = "sysctl -n hw.memsize"
        let diskCommand = "df -h / | tail -1 | awk '{print $5}'"

        let cpu = try await executeCommand(cpuCommand).trimmingCharacters(in: .whitespacesAndNewlines)
        let memBytes = try await executeCommand(memCommand).trimmingCharacters(in: .whitespacesAndNewlines)
        let diskUsage = try await executeCommand(diskCommand).trimmingCharacters(in: .whitespacesAndNewlines)

        let memGB = (Double(memBytes) ?? 0) / 1_073_741_824 // Convert bytes to GB

        return SystemInfo(
            cpu: cpu,
            memoryGB: memGB,
            diskUsage: diskUsage
        )
    }

    // MARK: - Interactive Process Management

    /// Run a long-running process (like a Python daemon)
    func startBackgroundProcess(command: String) async throws -> Process {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-c", command]

        try process.run()
        return process
    }
}

// MARK: - Supporting Types

enum CommandError: Error, LocalizedError {
    case executionFailed(String)
    case invalidPath
    case permissionDenied

    var errorDescription: String? {
        switch self {
        case .executionFailed(let message):
            return "Command execution failed: \(message)"
        case .invalidPath:
            return "Invalid file path"
        case .permissionDenied:
            return "Permission denied"
        }
    }
}

struct SystemInfo {
    let cpu: String
    let memoryGB: Double
    let diskUsage: String
}
