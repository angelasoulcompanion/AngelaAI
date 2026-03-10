//
//  DashboardModels.swift
//  AITop
//

import Foundation

struct DashboardResponse: Codable {
    let hardware: HardwareStats
    let ollama: OllamaStatus
    let runningModels: [RunningModel]
}

struct HardwareStats: Codable {
    let chip: ChipInfo
    let cpu: CPUInfo
    let gpu: GPUInfo
    let memory: MemoryInfo
    let disk: DiskInfo
    let neuralEngine: NeuralEngineInfo
    let thermalPressure: String
}

struct ChipInfo: Codable {
    let chipName: String
    let modelName: String
    let cpuCores: AnyCodableValue
    let memoryGb: Int
}

struct CPUInfo: Codable {
    let percent: Double
    let cores: Int
    let physicalCores: Int
    let freqMhz: Int
}

struct GPUInfo: Codable {
    let percent: Double
    let rendererPercent: Double?
    let tilerPercent: Double?
    let vramUsedMb: Int?
    let vramAllocMb: Int?
}

struct MemoryInfo: Codable {
    let totalGb: Double
    let usedGb: Double
    let availableGb: Double
    let percent: Double
}

struct DiskInfo: Codable {
    let totalGb: Double
    let usedGb: Double
    let freeGb: Double
    let percent: Double
}

struct NeuralEngineInfo: Codable {
    let cores: Int
    let available: Bool
    let usagePercent: Double
    let powerMw: Int?
    let active: Bool?
}

struct OllamaStatus: Codable {
    let running: Bool
    let modelCount: Int
}

struct RunningModel: Codable {
    let name: String?
    let model: String?
    let size: Int64?
}

// MARK: - AnyCodableValue for flexible types

enum AnyCodableValue: Codable {
    case int(Int)
    case string(String)

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let val = try? container.decode(Int.self) {
            self = .int(val)
        } else if let val = try? container.decode(String.self) {
            self = .string(val)
        } else {
            self = .string("Unknown")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .int(let val): try container.encode(val)
        case .string(let val): try container.encode(val)
        }
    }

    var displayString: String {
        switch self {
        case .int(let val): return "\(val)"
        case .string(let val): return val
        }
    }
}
