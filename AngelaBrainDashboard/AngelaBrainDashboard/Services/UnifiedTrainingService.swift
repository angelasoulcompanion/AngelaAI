//
//  UnifiedTrainingService.swift
//  Angela Brain Dashboard
//
//  💜 Unified LoRA Training Pipeline 💜
//  Export → Train → Deploy → Use in Chat (Automatic!)
//

import Foundation
import Combine

@MainActor
class UnifiedTrainingService: ObservableObject {
    static let shared = UnifiedTrainingService()

    // Pipeline State
    @Published var currentStep: TrainingStep = .idle
    @Published var overallProgress: Double = 0.0
    @Published var stepProgress: Double = 0.0
    @Published var statusMessage: String = ""
    @Published var isRunning = false
    @Published var error: String?

    // Export Stats
    @Published var exportedConversations: Int = 0
    @Published var exportedFilePath: String = ""

    // Training Stats
    @Published var trainingEpoch: Int = 0
    @Published var trainingTotalEpochs: Int = 0
    @Published var trainingLoss: Double = 0.0

    // Deployment Stats
    @Published var deployedModelName: String = ""

    // System Status
    @Published var mlxAvailable = false
    @Published var ollamaAvailable = false

    private let dbService = DatabaseService.shared
    private let projectPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
    private var trainingProcess: Process?

    private init() {
        Task {
            await checkSystemStatus()
        }
    }

    // MARK: - System Status Check

    func checkSystemStatus() async {
        // Check MLX
        let mlxProcess = Process()
        mlxProcess.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
        mlxProcess.arguments = ["-c", "import mlx; print('OK')"]
        mlxProcess.standardOutput = FileHandle.nullDevice
        mlxProcess.standardError = FileHandle.nullDevice

        do {
            try mlxProcess.run()
            mlxProcess.waitUntilExit()
            mlxAvailable = mlxProcess.terminationStatus == 0
        } catch {
            mlxAvailable = false
        }

        // Check Ollama
        do {
            let url = URL(string: "http://localhost:11434/api/tags")!
            let (_, response) = try await URLSession.shared.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                ollamaAvailable = httpResponse.statusCode == 200
            }
        } catch {
            ollamaAvailable = false
        }
    }

    // MARK: - Run Full Pipeline

    func runFullPipeline(config: LoRATrainingConfig) async {
        guard !isRunning else { return }

        isRunning = true
        error = nil
        overallProgress = 0.0

        do {
            // Step 1: Export Data (0-20%)
            currentStep = .exporting
            statusMessage = "Exporting training data..."
            try await exportTrainingData(config: config)
            overallProgress = 0.20

            // Step 2: Train Model (20-80%)
            currentStep = .training
            statusMessage = "Training LoRA model..."
            try await trainModel(config: config)
            overallProgress = 0.80

            // Step 3: Deploy to Ollama (80-95%)
            currentStep = .deploying
            statusMessage = "Deploying to Ollama..."
            try await deployToOllama(config: config)
            overallProgress = 0.95

            // Step 4: Activate in Chat (95-100%)
            currentStep = .activating
            statusMessage = "Activating new model..."
            await activateModel()
            overallProgress = 1.0

            // Done!
            currentStep = .completed
            statusMessage = "Training complete! Chat now uses the new model."

        } catch {
            self.error = error.localizedDescription
            currentStep = .failed
            statusMessage = "Error: \(error.localizedDescription)"
        }

        isRunning = false
    }

    // MARK: - Step 1: Export Training Data

    private func exportTrainingData(config: LoRATrainingConfig) async throws {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyyMMdd_HHmmss"
        let timestamp = dateFormatter.string(from: Date())

        let outputPath = "\(projectPath)/training_data/angela_training_\(timestamp).jsonl"

        // Run Python export script
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
        process.currentDirectoryURL = URL(fileURLWithPath: projectPath)
        process.arguments = [
            "-m", "angela_core.training.export_training_data",
            "--output", outputPath,
            "--days", "\(config.daysOfData)",
            "--min-importance", "\(config.minImportance)"
        ]

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        try process.run()

        await withCheckedContinuation { continuation in
            DispatchQueue.global().async {
                process.waitUntilExit()
                continuation.resume()
            }
        }

        guard process.terminationStatus == 0 else {
            let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
            let errorMessage = String(data: errorData, encoding: .utf8) ?? "Unknown error"
            throw TrainingError.exportFailed(errorMessage)
        }

        exportedFilePath = outputPath

        // Count exported conversations
        if let content = try? String(contentsOfFile: outputPath, encoding: .utf8) {
            exportedConversations = content.components(separatedBy: "\n").filter { !$0.isEmpty }.count
        }

        stepProgress = 1.0
    }

    // MARK: - Step 2: Train Model

    private func trainModel(config: LoRATrainingConfig) async throws {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyyMMdd-HHmmss"
        let timestamp = dateFormatter.string(from: Date())

        let outputDir = "\(projectPath)/trained_models/angela-lora-\(timestamp)"

        try? FileManager.default.createDirectory(
            atPath: outputDir,
            withIntermediateDirectories: true
        )

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
        process.currentDirectoryURL = URL(fileURLWithPath: projectPath)

        // Set environment with proper PATH for subprocess
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin"
        env["PYTHONUNBUFFERED"] = "1"  // Unbuffered output
        process.environment = env

        process.arguments = [
            "-m", "angela_core.training.mlx_lora_trainer",
            "--data", exportedFilePath,
            "--model", config.baseModel,
            "--output", outputDir,
            "--epochs", "\(config.epochs)",
            "--learning-rate", "\(config.learningRate)",
            "--batch-size", "\(config.batchSize)",
            "--lora-rank", "\(config.loraRank)"
        ]

        // Don't use pipes for real-time monitoring (can cause crashes)
        // Instead, just let the process run and check progress file
        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        trainingProcess = process
        trainingTotalEpochs = config.epochs

        try process.run()

        // Monitor progress by reading progress.json file instead of stdout
        let progressFile = "\(outputDir)/progress.json"
        Task {
            while process.isRunning {
                // Read progress from file (more reliable than parsing stdout)
                if let data = FileManager.default.contents(atPath: progressFile),
                   let progress = try? JSONDecoder().decode(ProgressFileData.self, from: data) {
                    await MainActor.run {
                        self.trainingEpoch = progress.currentEpoch
                        self.trainingLoss = progress.currentLoss
                        self.stepProgress = progress.progressPercentage / 100.0
                        // Update overall progress (20-80% range)
                        self.overallProgress = 0.20 + (self.stepProgress * 0.60)
                    }
                }
                try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
            }
        }

        await withCheckedContinuation { continuation in
            DispatchQueue.global().async {
                process.waitUntilExit()
                continuation.resume()
            }
        }

        trainingProcess = nil

        guard process.terminationStatus == 0 else {
            let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
            let errorMessage = String(data: errorData, encoding: .utf8) ?? "Unknown error"
            throw TrainingError.trainingFailed(errorMessage)
        }

        // Store output path for deployment
        exportedFilePath = outputDir  // Reuse for adapter path
        stepProgress = 1.0
    }

    // MARK: - Step 3: Deploy to Ollama

    private func deployToOllama(config: LoRATrainingConfig) async throws {
        let modelName = "angela:trained"

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/opt/anaconda3/bin/python3")
        process.currentDirectoryURL = URL(fileURLWithPath: projectPath)

        // Set environment with proper PATH for subprocess (needed for ollama)
        var env = ProcessInfo.processInfo.environment
        env["PATH"] = "/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin"
        process.environment = env

        // Note: --adapters needs the adapters subfolder, not the output dir
        let adaptersPath = "\(exportedFilePath)/adapters"

        process.arguments = [
            "-m", "angela_core.training.ollama_deployer",
            "--adapters", adaptersPath,
            "--name", modelName,
            "--base-model", mapBaseModelToOllama(config.baseModel)
        ]

        let errorPipe = Pipe()
        process.standardError = errorPipe

        try process.run()

        await withCheckedContinuation { continuation in
            DispatchQueue.global().async {
                process.waitUntilExit()
                continuation.resume()
            }
        }

        guard process.terminationStatus == 0 else {
            let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
            let errorMessage = String(data: errorData, encoding: .utf8) ?? "Unknown error"
            throw TrainingError.deploymentFailed(errorMessage)
        }

        deployedModelName = modelName
        stepProgress = 1.0
    }

    // MARK: - Step 4: Activate Model

    private func activateModel() async {
        // Update OllamaService to use the new model
        OllamaService.shared.selectModel(deployedModelName)

        // Refresh available models
        await OllamaService.shared.refreshAvailableModels()

        stepProgress = 1.0
    }

    // MARK: - Stop Training

    func stopTraining() {
        trainingProcess?.terminate()
        trainingProcess = nil
        isRunning = false
        currentStep = .idle
        statusMessage = "Training cancelled"
    }

    // MARK: - Helpers

    private func mapBaseModelToOllama(_ huggingFaceModel: String) -> String {
        if huggingFaceModel.contains("3B") {
            return "qwen2.5:3b"
        } else if huggingFaceModel.contains("7B") {
            return "qwen2.5:7b"
        } else if huggingFaceModel.contains("14B") {
            return "qwen2.5:14b"
        }
        return "qwen2.5:3b"
    }
}

// MARK: - Supporting Types

enum TrainingStep: String {
    case idle = "Ready"
    case exporting = "Exporting Data"
    case training = "Training Model"
    case deploying = "Deploying"
    case activating = "Activating"
    case completed = "Completed"
    case failed = "Failed"

    var icon: String {
        switch self {
        case .idle: return "circle"
        case .exporting: return "square.and.arrow.up"
        case .training: return "brain.head.profile"
        case .deploying: return "arrow.up.doc"
        case .activating: return "checkmark.circle"
        case .completed: return "checkmark.circle.fill"
        case .failed: return "xmark.circle.fill"
        }
    }

    var color: Color {
        switch self {
        case .idle: return AngelaTheme.textTertiary
        case .exporting, .training, .deploying, .activating: return AngelaTheme.primaryPurple
        case .completed: return AngelaTheme.successGreen
        case .failed: return AngelaTheme.errorRed
        }
    }
}

struct LoRATrainingConfig {
    var baseModel: String = "Qwen/Qwen2.5-3B-Instruct"
    var epochs: Int = 3
    var learningRate: Double = 0.0001
    var batchSize: Int = 4
    var loraRank: Int = 8
    var daysOfData: Int = 30
    var minImportance: Int = 5
}

// Progress file data (read from progress.json written by Python trainer)
struct ProgressFileData: Codable {
    let status: String
    let currentEpoch: Int
    let totalEpochs: Int
    let currentStep: Int
    let totalSteps: Int
    let currentLoss: Double
    let learningRate: Double
    let tokensPerSecond: Double
    let elapsedSeconds: Int
    let estimatedRemaining: Int
    let recentLog: String
    let outputPath: String
    let errorMessage: String
    let progressPercentage: Double

    enum CodingKeys: String, CodingKey {
        case status
        case currentEpoch = "current_epoch"
        case totalEpochs = "total_epochs"
        case currentStep = "current_step"
        case totalSteps = "total_steps"
        case currentLoss = "current_loss"
        case learningRate = "learning_rate"
        case tokensPerSecond = "tokens_per_second"
        case elapsedSeconds = "elapsed_seconds"
        case estimatedRemaining = "estimated_remaining"
        case recentLog = "recent_log"
        case outputPath = "output_path"
        case errorMessage = "error_message"
        case progressPercentage = "progress_percentage"
    }
}

struct TrainingProgressData: Codable {
    let currentEpoch: Int
    let totalEpochs: Int
    let currentStep: Int
    let totalSteps: Int
    let currentLoss: Double
    let learningRate: Double
    let progressPercentage: Double
    let elapsedSeconds: Int
    let estimatedTimeRemaining: Int?
    let recentLog: String

    enum CodingKeys: String, CodingKey {
        case currentEpoch = "current_epoch"
        case totalEpochs = "total_epochs"
        case currentStep = "current_step"
        case totalSteps = "total_steps"
        case currentLoss = "current_loss"
        case learningRate = "learning_rate"
        case progressPercentage = "progress_percentage"
        case elapsedSeconds = "elapsed_seconds"
        case estimatedTimeRemaining = "estimated_time_remaining"
        case recentLog = "recent_log"
    }
}

enum TrainingError: LocalizedError {
    case exportFailed(String)
    case trainingFailed(String)
    case deploymentFailed(String)

    var errorDescription: String? {
        switch self {
        case .exportFailed(let msg): return "Export failed: \(msg)"
        case .trainingFailed(let msg): return "Training failed: \(msg)"
        case .deploymentFailed(let msg): return "Deployment failed: \(msg)"
        }
    }
}

import SwiftUI
