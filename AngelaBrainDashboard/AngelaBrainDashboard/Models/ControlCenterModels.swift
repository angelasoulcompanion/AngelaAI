//
//  ControlCenterModels.swift
//  Angela Brain Dashboard
//
//  Models for Control Center - Daemon Tasks & MCP Servers
//

import SwiftUI

// MARK: - Daemon Status

struct DaemonStatus: Identifiable, Codable {
    let label: String
    let name: String
    let description: String
    let schedule: String
    let category: String          // core, communication, consciousness, productivity
    let keepAlive: Bool
    let status: String            // running, idle, stopped, error
    let pid: Int?
    let lastExitStatus: Int?
    let lastLogLine: String?
    let logFile: String?

    var id: String { label }

    enum CodingKeys: String, CodingKey {
        case label, name, description, schedule, category
        case keepAlive = "keep_alive"
        case status, pid
        case lastExitStatus = "last_exit_status"
        case lastLogLine = "last_log_line"
        case logFile = "log_file"
    }

    var isRunning: Bool { status == "running" }

    var statusColor: Color {
        switch status {
        case "running": return .green
        case "idle": return .orange
        case "error": return .red
        case "stopped": return .gray
        default: return .gray
        }
    }

    var statusIcon: String {
        switch status {
        case "running": return "circle.fill"
        case "idle": return "circle.fill"
        case "error": return "exclamationmark.circle.fill"
        case "stopped": return "circle"
        default: return "questionmark.circle"
        }
    }

    var categoryIcon: String {
        switch category {
        case "core": return "cpu.fill"
        case "communication": return "envelope.fill"
        case "consciousness": return "sparkles"
        case "productivity": return "checklist"
        default: return "gearshape.fill"
        }
    }

    var categoryColor: Color {
        switch category {
        case "core": return Color(hex: "9333EA")          // Purple
        case "communication": return Color(hex: "3B82F6") // Blue
        case "consciousness": return Color(hex: "EC4899") // Pink
        case "productivity": return Color(hex: "10B981")  // Green
        default: return .gray
        }
    }
}

// MARK: - MCP Server Info

struct MCPServerInfo: Identifiable, Codable {
    let name: String
    let description: String
    let toolsCount: Int
    let icon: String              // SF Symbol name
    let enabled: Bool
    let command: String
    let scriptPath: String

    var id: String { name }

    enum CodingKeys: String, CodingKey {
        case name, description
        case toolsCount = "tools_count"
        case icon, enabled, command
        case scriptPath = "script_path"
    }
}

// MARK: - Response Models

struct DaemonLogResponse: Codable {
    let label: String
    let lines: [String]
    let logFile: String

    enum CodingKeys: String, CodingKey {
        case label, lines
        case logFile = "log_file"
    }
}

struct DaemonActionResponse: Codable {
    let success: Bool
    let label: String
    let action: String
    let message: String
}

struct MCPToggleRequest: Codable {
    let enabled: Bool
}

struct MCPToggleResponse: Codable {
    let name: String
    let enabled: Bool
}
