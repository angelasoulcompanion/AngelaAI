//
//  TrainingStudioView.swift
//  Angela Brain Dashboard
//
//  💜 Training Studio - One-Click LoRA Training 💜
//  Export → Train → Deploy → Use in Chat (Automatic!)
//

import SwiftUI

struct TrainingStudioView: View {
    @StateObject private var trainingService = UnifiedTrainingService.shared
    @EnvironmentObject var databaseService: DatabaseService

    // Configuration
    @State private var config = LoRATrainingConfig()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.spacing) {
                // Header
                header

                // System Status
                systemStatusSection

                // Training Configuration
                if !trainingService.isRunning {
                    configurationSection
                }

                // Progress Section (when running)
                if trainingService.isRunning || trainingService.currentStep == .completed {
                    progressSection
                }

                // Action Button
                actionButton

                // Error Display
                if let error = trainingService.error {
                    errorSection(error: error)
                }

                // Help Section
                if !trainingService.isRunning && trainingService.currentStep != .completed {
                    helpSection
                }
            }
            .padding(AngelaTheme.spacing)
        }
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .font(.system(size: 40))
                    .foregroundStyle(AngelaTheme.purpleGradient)

                VStack(alignment: .leading, spacing: 4) {
                    Text("LoRA Training Studio")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text("Train Angela's personality with your conversations")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()

                // Current Model Badge
                VStack(alignment: .trailing, spacing: 4) {
                    Text("Active Model")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text(OllamaService.shared.selectedModel)
                        .font(AngelaTheme.body().weight(.semibold))
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 4)
                        .background(AngelaTheme.primaryPurple.opacity(0.1))
                        .cornerRadius(8)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - System Status

    private var systemStatusSection: some View {
        HStack(spacing: 20) {
            SystemStatusVerticalBadge(
                title: "MLX",
                isAvailable: trainingService.mlxAvailable,
                icon: "cpu"
            )

            Divider()
                .frame(height: 40)

            SystemStatusVerticalBadge(
                title: "Ollama",
                isAvailable: trainingService.ollamaAvailable,
                icon: "server.rack"
            )

            Divider()
                .frame(height: 40)

            SystemStatusVerticalBadge(
                title: "Database",
                isAvailable: true, // Assume connected if we're here
                icon: "cylinder.split.1x2"
            )
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Configuration Section

    private var configurationSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Training Configuration")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            // Data Settings
            VStack(alignment: .leading, spacing: 12) {
                Text("Data Settings")
                    .font(AngelaTheme.body().weight(.medium))
                    .foregroundColor(AngelaTheme.textSecondary)

                HStack(spacing: 20) {
                    // Days of Data
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Days of Data: \(config.daysOfData)")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Slider(value: Binding(
                            get: { Double(config.daysOfData) },
                            set: { config.daysOfData = Int($0) }
                        ), in: 7...90, step: 7)
                        .tint(AngelaTheme.primaryPurple)
                    }

                    // Min Importance
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Min Importance: \(config.minImportance)")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Slider(value: Binding(
                            get: { Double(config.minImportance) },
                            set: { config.minImportance = Int($0) }
                        ), in: 1...10, step: 1)
                        .tint(AngelaTheme.primaryPurple)
                    }
                }
            }

            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.3))

            // Model Settings
            VStack(alignment: .leading, spacing: 12) {
                Text("Model Settings")
                    .font(AngelaTheme.body().weight(.medium))
                    .foregroundColor(AngelaTheme.textSecondary)

                HStack(spacing: 20) {
                    // Base Model
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Base Model")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Picker("", selection: $config.baseModel) {
                            Text("Qwen2.5 3B (Recommended)").tag("Qwen/Qwen2.5-3B-Instruct")
                            Text("Qwen2.5 7B").tag("Qwen/Qwen2.5-7B-Instruct")
                            Text("Qwen2.5 14B").tag("Qwen/Qwen2.5-14B-Instruct")
                        }
                        .labelsHidden()
                    }

                    // Epochs
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Epochs: \(config.epochs)")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Slider(value: Binding(
                            get: { Double(config.epochs) },
                            set: { config.epochs = Int($0) }
                        ), in: 1...10, step: 1)
                        .tint(AngelaTheme.primaryPurple)
                    }
                }

                HStack(spacing: 20) {
                    // LoRA Rank
                    VStack(alignment: .leading, spacing: 4) {
                        Text("LoRA Rank: \(config.loraRank)")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Slider(value: Binding(
                            get: { Double(config.loraRank) },
                            set: { config.loraRank = Int($0) }
                        ), in: 4...64, step: 4)
                        .tint(AngelaTheme.primaryPurple)
                    }

                    // Batch Size
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Batch Size: \(config.batchSize)")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)

                        Slider(value: Binding(
                            get: { Double(config.batchSize) },
                            set: { config.batchSize = Int($0) }
                        ), in: 1...8, step: 1)
                        .tint(AngelaTheme.primaryPurple)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Progress Section

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            Text("Training Progress")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            // Step indicators
            HStack(spacing: 0) {
                ForEach([TrainingStep.exporting, .training, .deploying, .activating], id: \.self) { step in
                    StepIndicator(
                        step: step,
                        currentStep: trainingService.currentStep,
                        isCompleted: stepIsCompleted(step)
                    )

                    if step != .activating {
                        Rectangle()
                            .fill(stepIsCompleted(step) ? AngelaTheme.successGreen : AngelaTheme.textTertiary.opacity(0.3))
                            .frame(height: 2)
                    }
                }
            }

            // Progress bar
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(trainingService.statusMessage)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Spacer()

                    Text("\(Int(trainingService.overallProgress * 100))%")
                        .font(AngelaTheme.body().weight(.semibold))
                        .foregroundColor(AngelaTheme.primaryPurple)
                }

                ProgressView(value: trainingService.overallProgress)
                    .tint(trainingService.currentStep == .completed ? AngelaTheme.successGreen : AngelaTheme.primaryPurple)
            }

            // Step-specific details
            if trainingService.currentStep == .training {
                trainingDetails
            }

            // Completion message
            if trainingService.currentStep == .completed {
                completionMessage
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    private var trainingDetails: some View {
        HStack(spacing: 20) {
            VStack(spacing: 4) {
                Text("Epoch")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                Text("\(trainingService.trainingEpoch)/\(trainingService.trainingTotalEpochs)")
                    .font(AngelaTheme.body().weight(.semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider().frame(height: 30)

            VStack(spacing: 4) {
                Text("Loss")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                Text(String(format: "%.4f", trainingService.trainingLoss))
                    .font(AngelaTheme.body().weight(.semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider().frame(height: 30)

            VStack(spacing: 4) {
                Text("Conversations")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                Text("\(trainingService.exportedConversations)")
                    .font(AngelaTheme.body().weight(.semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }
        }
        .padding(AngelaTheme.smallSpacing)
        .background(AngelaTheme.backgroundLight)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }

    private var completionMessage: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(AngelaTheme.successGreen)

                Text("Training Complete!")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.successGreen)
            }

            Text("Angela is now using the new trained model: \(trainingService.deployedModelName)")
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)

            Text("Go to Chat to talk with the improved Angela!")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity)
        .background(AngelaTheme.successGreen.opacity(0.1))
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Action Button

    private var actionButton: some View {
        Group {
            if trainingService.isRunning {
                Button {
                    trainingService.stopTraining()
                } label: {
                    HStack {
                        Image(systemName: "stop.fill")
                        Text("Stop Training")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(AngelaTheme.errorRed)
                    .foregroundColor(.white)
                    .cornerRadius(AngelaTheme.cornerRadius)
                }
                .buttonStyle(.plain)
            } else if trainingService.currentStep == .completed {
                Button {
                    // Reset for new training
                    trainingService.currentStep = .idle
                    trainingService.overallProgress = 0
                } label: {
                    HStack {
                        Image(systemName: "arrow.clockwise")
                        Text("Train Again")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(AngelaTheme.purpleGradient)
                    .foregroundColor(.white)
                    .cornerRadius(AngelaTheme.cornerRadius)
                }
                .buttonStyle(.plain)
            } else {
                Button {
                    Task {
                        await trainingService.runFullPipeline(config: config)
                    }
                } label: {
                    HStack {
                        Image(systemName: "play.fill")
                        Text("Start Training")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        (trainingService.mlxAvailable && trainingService.ollamaAvailable)
                            ? AngelaTheme.purpleGradient
                            : LinearGradient(colors: [.gray], startPoint: .leading, endPoint: .trailing)
                    )
                    .foregroundColor(.white)
                    .cornerRadius(AngelaTheme.cornerRadius)
                }
                .buttonStyle(.plain)
                .disabled(!trainingService.mlxAvailable || !trainingService.ollamaAvailable)
            }
        }
    }

    // MARK: - Error Section

    private func errorSection(error: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(AngelaTheme.errorRed)
                Text("Error")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.errorRed)
            }

            Text(error)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AngelaTheme.errorRed.opacity(0.1))
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Help Section

    private var helpSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("How it works")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            VStack(alignment: .leading, spacing: 8) {
                HelpItem(number: "1", text: "Export your conversations from the database")
                HelpItem(number: "2", text: "Train a LoRA adapter on your data using MLX")
                HelpItem(number: "3", text: "Deploy the trained model to Ollama")
                HelpItem(number: "4", text: "Chat automatically uses the new model")
            }

            Text("Training typically takes 10-30 minutes depending on data size and model.")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Helpers

    private func stepIsCompleted(_ step: TrainingStep) -> Bool {
        let stepOrder: [TrainingStep] = [.exporting, .training, .deploying, .activating, .completed]
        guard let currentIndex = stepOrder.firstIndex(of: trainingService.currentStep),
              let stepIndex = stepOrder.firstIndex(of: step) else {
            return false
        }
        return stepIndex < currentIndex
    }
}

// MARK: - Supporting Views (using shared SystemStatusVerticalBadge from SharedComponents)

struct StepIndicator: View {
    let step: TrainingStep
    let currentStep: TrainingStep
    let isCompleted: Bool

    var isActive: Bool {
        step == currentStep
    }

    var body: some View {
        VStack(spacing: 4) {
            ZStack {
                Circle()
                    .fill(isCompleted ? AngelaTheme.successGreen : (isActive ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary.opacity(0.3)))
                    .frame(width: 32, height: 32)

                if isCompleted {
                    Image(systemName: "checkmark")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)
                } else if isActive {
                    ProgressView()
                        .scaleEffect(0.6)
                        .tint(.white)
                } else {
                    Image(systemName: step.icon)
                        .font(.system(size: 14))
                        .foregroundColor(.white.opacity(0.5))
                }
            }

            Text(step.rawValue)
                .font(AngelaTheme.caption())
                .foregroundColor(isActive ? AngelaTheme.primaryPurple : AngelaTheme.textTertiary)
        }
    }
}

struct HelpItem: View {
    let number: String
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text(number)
                .font(AngelaTheme.caption().weight(.bold))
                .foregroundColor(.white)
                .frame(width: 24, height: 24)
                .background(AngelaTheme.primaryPurple)
                .clipShape(Circle())

            Text(text)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
        }
    }
}

#Preview {
    TrainingStudioView()
        .environmentObject(DatabaseService.shared)
}
