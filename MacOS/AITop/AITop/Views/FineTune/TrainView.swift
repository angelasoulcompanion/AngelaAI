//
//  TrainView.swift
//  AITop — Fine-Tune Studio: Training Configuration & Launch
//

import SwiftUI

struct TrainView: View {
    @EnvironmentObject var apiService: APIService

    // Form state
    @State private var selectedMethod: TrainingMethodType = .mlxLora
    @State private var selectedModel = ""
    @State private var datasetPath = ""
    @State private var selectedStrategy: String? = "standard"

    // Advanced config
    @State private var showAdvanced = false
    @State private var epochs = 3
    @State private var learningRate = 1e-4
    @State private var loraRank = 4
    @State private var batchSize = 2
    @State private var maxSeqLength = 1024
    @State private var gradAccumulation = 4

    // Data
    @State private var strategies: [FineTuneStrategy] = []
    @State private var localModels: [String] = []
    @State private var datasets: [DatasetFile] = []
    @State private var batches: [ExportBatch] = []
    @State private var methods: [TrainingMethodInfo] = []
    @State private var estimate: EstimateResponse?

    // UI state
    @State private var isCreating = false
    @State private var error: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                Text("New Training Job")
                    .font(.title2.bold())
                    .foregroundColor(.white)

                // Step 1: Training Method
                methodPicker

                // Step 2: Model Selection
                modelPicker

                // Step 3: Dataset Selection
                datasetPicker

                // Step 4: Strategy Quick-Pick
                strategyPicker

                // Advanced Config (collapsible)
                advancedConfig

                // Estimation
                if let est = estimate {
                    estimationCard(est)
                }

                // Start Button
                startButton
            }
            .padding(24)
        }
        .background(Color(hex: "0A0A0F"))
        .onAppear { loadData() }
    }

    // MARK: - Method Picker

    private var methodPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("TRAINING METHOD")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            HStack(spacing: 8) {
                ForEach(TrainingMethodType.allCases, id: \.rawValue) { method in
                    Button {
                        selectedMethod = method
                        applyMethodDefaults(method)
                        updateEstimate()
                    } label: {
                        VStack(spacing: 4) {
                            Image(systemName: method.icon)
                                .font(.system(size: 16))
                            Text(method.displayName)
                                .font(.caption2.bold())
                            Text(method.engine.uppercased())
                                .font(.system(size: 8))
                                .padding(.horizontal, 4)
                                .padding(.vertical, 1)
                                .background(method.engine == "mlx" ? Color.green.opacity(0.3) : Color.blue.opacity(0.3))
                                .cornerRadius(3)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(selectedMethod == method ? Color(hex: "FF6B00").opacity(0.2) : Color(hex: "1A1A2E"))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(selectedMethod == method ? Color(hex: "FF6B00") : Color(hex: "2A2A4A"), lineWidth: 1)
                        )
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(selectedMethod == method ? Color(hex: "FF6B00") : Color(hex: "9CA3AF"))
                }
            }
        }
    }

    // MARK: - Model Picker

    private var modelPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("BASE MODEL")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            Picker("Model", selection: $selectedModel) {
                Text("Select model...").tag("")
                ForEach(localModels, id: \.self) { model in
                    Text(model).tag(model)
                }
            }
            .onChange(of: selectedModel) { updateEstimate() }
        }
    }

    // MARK: - Dataset Picker

    private var datasetPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("DATASET")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            HStack {
                TextField("Dataset path", text: $datasetPath)
                    .textFieldStyle(.roundedBorder)
                    .onChange(of: datasetPath) { updateEstimate() }

                Button("Browse") {
                    browseDataset()
                }
            }

            // Exported datasets (from Datasets tab)
            if !batches.isEmpty {
                Text("EXPORTED DATASETS")
                    .font(.system(size: 9).bold())
                    .foregroundColor(Color(hex: "6B7280"))
                    .padding(.top, 4)

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(batches) { batch in
                            if let path = batch.outputPath {
                                Button {
                                    datasetPath = path
                                    updateEstimate()
                                } label: {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(batch.batchName)
                                            .font(.caption.bold())
                                            .lineLimit(1)
                                        HStack(spacing: 4) {
                                            Text("\(batch.totalPairs) rows")
                                                .font(.system(size: 9).bold())
                                                .foregroundColor(Color(hex: "00D4FF"))
                                            if let q = batch.avgQuality {
                                                Text(String(format: "Q:%.1f", q))
                                                    .font(.system(size: 9))
                                            }
                                            Text(batch.exportType.uppercased())
                                                .font(.system(size: 8).bold())
                                                .padding(.horizontal, 3)
                                                .background(Color.green.opacity(0.3))
                                                .foregroundColor(.green)
                                                .cornerRadius(2)
                                        }
                                    }
                                    .padding(8)
                                    .background(datasetPath == path ? Color(hex: "FF6B00").opacity(0.15) : Color(hex: "1A1A2E"))
                                    .cornerRadius(6)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 6)
                                            .stroke(datasetPath == path ? Color(hex: "FF6B00") : Color.clear, lineWidth: 1)
                                    )
                                }
                                .buttonStyle(.plain)
                                .foregroundColor(.white)
                            }
                        }
                    }
                }
            }
        }
    }

    // MARK: - Strategy Picker

    private var strategyPicker: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("STRATEGY PRESET")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            HStack(spacing: 8) {
                ForEach(strategies) { strategy in
                    Button {
                        selectedStrategy = strategy.name
                        epochs = strategy.epochs
                        learningRate = strategy.learningRate
                        loraRank = strategy.loraRank
                        batchSize = strategy.batchSize
                        updateEstimate()
                    } label: {
                        VStack(spacing: 4) {
                            Text(strategy.name.replacingOccurrences(of: "_", with: " ").capitalized)
                                .font(.caption.bold())
                            Text("\(strategy.epochs) epochs")
                                .font(.system(size: 10))
                                .foregroundColor(Color(hex: "9CA3AF"))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(selectedStrategy == strategy.name ? Color(hex: "FF6B00").opacity(0.2) : Color(hex: "1A1A2E"))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(selectedStrategy == strategy.name ? Color(hex: "FF6B00") : Color(hex: "2A2A4A"), lineWidth: 1)
                        )
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(selectedStrategy == strategy.name ? Color(hex: "FF6B00") : .white)
                }
            }
        }
    }

    // MARK: - Advanced Config

    private var advancedConfig: some View {
        DisclosureGroup("Advanced Configuration", isExpanded: $showAdvanced) {
            VStack(spacing: 12) {
                HStack {
                    configField("Epochs", value: $epochs, range: 1...20)
                    configField("Batch Size", value: $batchSize, range: 1...16)
                    configField("LoRA Rank", value: $loraRank, range: 2...64)
                }
                HStack {
                    configField("Max Seq Length", value: $maxSeqLength, range: 256...4096)
                    configField("Grad Accum", value: $gradAccumulation, range: 1...16)
                }
                HStack {
                    VStack(alignment: .leading) {
                        Text("Learning Rate")
                            .font(.caption)
                            .foregroundColor(Color(hex: "9CA3AF"))
                        TextField("LR", value: $learningRate, format: .number)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 120)
                    }
                    Spacer()
                }
            }
            .padding(.top, 8)
        }
        .foregroundColor(.white)
        .onChange(of: epochs) { updateEstimate() }
        .onChange(of: batchSize) { updateEstimate() }
    }

    private func configField(_ label: String, value: Binding<Int>, range: ClosedRange<Int>) -> some View {
        VStack(alignment: .leading) {
            Text(label)
                .font(.caption)
                .foregroundColor(Color(hex: "9CA3AF"))
            Stepper("\(value.wrappedValue)", value: value, in: range)
                .frame(width: 120)
        }
    }

    // MARK: - Estimation Card

    private func estimationCard(_ est: EstimateResponse) -> some View {
        HStack(spacing: 20) {
            VStack(alignment: .leading, spacing: 4) {
                Text("ESTIMATED TIME")
                    .font(.system(size: 9).bold())
                    .foregroundColor(Color(hex: "9CA3AF"))
                Text(est.duration.formatted)
                    .font(.title3.bold())
                    .foregroundColor(.white)
                Text("\(est.duration.totalSteps) steps")
                    .font(.caption)
                    .foregroundColor(Color(hex: "9CA3AF"))
            }

            Divider().frame(height: 40)

            VStack(alignment: .leading, spacing: 4) {
                Text("ESTIMATED RAM")
                    .font(.system(size: 9).bold())
                    .foregroundColor(Color(hex: "9CA3AF"))
                Text(String(format: "%.1f GB", est.memory.recommendedGb))
                    .font(.title3.bold())
                    .foregroundColor(est.memory.fitsCurrentMachine ? .green : .orange)
                Text(est.memory.notes)
                    .font(.system(size: 9))
                    .foregroundColor(Color(hex: "9CA3AF"))
                    .lineLimit(2)
            }

            Spacer()
        }
        .padding(16)
        .background(Color(hex: "1A1A2E"))
        .cornerRadius(12)
    }

    // MARK: - Start Button

    private var startButton: some View {
        VStack(spacing: 8) {
            Button {
                Task { await createAndStart() }
            } label: {
                HStack {
                    if isCreating {
                        ProgressView()
                            .scaleEffect(0.8)
                            .tint(.white)
                    } else {
                        Image(systemName: "play.fill")
                    }
                    Text(isCreating ? "Creating..." : "Start Training")
                        .fontWeight(.semibold)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(canStart ? Color(hex: "FF6B00") : Color.gray.opacity(0.3))
                .foregroundColor(.white)
                .cornerRadius(10)
            }
            .buttonStyle(.plain)
            .disabled(!canStart || isCreating)

            if let error {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
            }
        }
    }

    private var canStart: Bool {
        !selectedModel.isEmpty && !datasetPath.isEmpty
    }

    // MARK: - Actions

    private func loadData() {
        Task {
            async let s = try? apiService.getStrategies()
            async let m = try? apiService.getModels()
            async let d = try? apiService.getDatasets()
            async let mt = try? apiService.getTrainingMethods()
            async let bt = try? apiService.getExportBatches()

            if let result = await s { strategies = result.strategies }
            if let result = await m { localModels = result.models.map(\.name) }
            if let result = await d { datasets = result.datasets }
            if let result = await mt { methods = result.methods }
            if let result = await bt { batches = result.batches }
        }
    }

    private func browseDataset() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.init(filenameExtension: "jsonl")!, .init(filenameExtension: "json")!,
                                     .init(filenameExtension: "csv")!, .init(filenameExtension: "txt")!]
        panel.allowsMultipleSelection = false
        // Default to exports directory
        let exportsDir = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".aitop/finetune/exports")
        if FileManager.default.fileExists(atPath: exportsDir.path) {
            panel.directoryURL = exportsDir
        }
        panel.treatsFilePackagesAsDirectories = true
        if panel.runModal() == .OK, let url = panel.url {
            datasetPath = url.path
            updateEstimate()
        }
    }

    private func applyMethodDefaults(_ method: TrainingMethodType) {
        switch method {
        case .mlxLora:
            learningRate = 1e-4; loraRank = 4; maxSeqLength = 1024
        case .mlxQlora:
            learningRate = 1e-4; loraRank = 8; maxSeqLength = 1024
        case .sft:
            learningRate = 2e-4; loraRank = 16; maxSeqLength = 2048
        case .dpo:
            learningRate = 5e-5; loraRank = 16; batchSize = 1; maxSeqLength = 4096
        case .orpo:
            learningRate = 8e-6; loraRank = 16; maxSeqLength = 2048
        }
    }

    private func updateEstimate() {
        guard !selectedModel.isEmpty, !datasetPath.isEmpty else { return }
        Task {
            estimate = try? await apiService.estimateTraining(
                model: selectedModel, datasetPath: datasetPath,
                method: selectedMethod.rawValue, epochs: epochs,
                batchSize: batchSize, gradAccumulation: gradAccumulation,
                maxSeqLength: maxSeqLength
            )
        }
    }

    private func createAndStart() async {
        isCreating = true
        error = nil
        do {
            let job = try await apiService.createJob(
                model: selectedModel, datasetPath: datasetPath,
                trainingMethod: selectedMethod.rawValue,
                strategy: selectedStrategy,
                epochs: epochs, learningRate: learningRate,
                loraRank: loraRank, batchSize: batchSize
            )
            _ = try await apiService.startJob(id: job.id)
            // Notify container to start polling + switch to Jobs
            NotificationCenter.default.post(name: .init("TrainingStarted"), object: nil)
            NotificationCenter.default.post(name: .init("SwitchToJobsTab"), object: nil)
        } catch {
            self.error = error.localizedDescription
        }
        isCreating = false
    }
}

