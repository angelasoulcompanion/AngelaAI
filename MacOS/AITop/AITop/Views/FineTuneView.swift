//
//  FineTuneView.swift
//  AITop
//
//  MLX LoRA fine-tuning wizard with progress monitoring
//

import SwiftUI
import Charts

struct FineTuneView: View {
    @EnvironmentObject var apiService: APIService
    @State private var strategies: [FineTuneStrategy] = []
    @State private var jobs: [FineTuneJob] = []
    @State private var localModels: [OllamaModel] = []

    // Job creation
    @State private var selectedModel = ""
    @State private var selectedStrategy = "standard"
    @State private var datasetPath = ""
    @State private var isCreating = false
    @State private var error: String?

    // Monitoring
    @State private var activeJob: FineTuneJob?
    @State private var pollTimer: Timer?

    var body: some View {
        ScrollView {
            VStack(spacing: AITopTheme.spacing) {
                // Header
                HStack {
                    Text("Fine-Tune")
                        .font(AITopTheme.title())
                        .foregroundColor(AITopTheme.textPrimary)
                    Spacer()
                    Button {
                        loadJobs()
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(AITopTheme.accentOrange)
                    }
                    .buttonStyle(.plain)
                }

                // Active job progress
                if let job = activeJob {
                    activeJobSection(job)
                }

                // New job form
                newJobSection

                // Past jobs
                if !jobs.isEmpty {
                    pastJobsSection
                }
            }
            .padding(AITopTheme.largeSpacing)
        }
        .background(AITopTheme.backgroundDark)
        .onAppear {
            loadStrategies()
            loadJobs()
            loadModels()
        }
        .onDisappear {
            pollTimer?.invalidate()
        }
    }

    // MARK: - Active Job

    private func activeJobSection(_ job: FineTuneJob) -> some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            HStack {
                Text("Training: \(job.model)")
                    .font(AITopTheme.heading())
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                statusBadge(job.status)
            }

            // Progress
            if job.status == "running" {
                HStack {
                    Text("Step \(job.currentStep)")
                        .font(AITopTheme.monospace())
                        .foregroundColor(AITopTheme.accentCyan)
                    Spacer()
                    if let eta = job.etaSeconds {
                        Text("ETA: \(formatDuration(eta))")
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textSecondary)
                    }
                }

                // Loss value
                HStack {
                    Text("Loss:")
                        .font(AITopTheme.body())
                        .foregroundColor(AITopTheme.textSecondary)
                    Text(String(format: "%.4f", job.loss))
                        .font(AITopTheme.monospace())
                        .foregroundColor(AITopTheme.accentOrange)
                }

                // Loss chart
                if job.lossHistory.count > 1 {
                    Chart(job.lossHistory.indices, id: \.self) { i in
                        LineMark(
                            x: .value("Step", job.lossHistory[i].step),
                            y: .value("Loss", job.lossHistory[i].loss)
                        )
                        .foregroundStyle(AITopTheme.accentOrange)
                        .lineStyle(StrokeStyle(lineWidth: 2))
                    }
                    .frame(height: 150)
                    .chartYAxisLabel("Loss")
                    .chartXAxisLabel("Step")
                }
            }

            // Elapsed time
            if let elapsed = job.elapsedSeconds {
                Text("Elapsed: \(formatDuration(elapsed))")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - New Job Form

    private var newJobSection: some View {
        VStack(alignment: .leading, spacing: AITopTheme.spacing) {
            Text("New Fine-Tune Job")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            // Step 1: Model
            VStack(alignment: .leading, spacing: 4) {
                Text("Base Model")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                Picker("Model", selection: $selectedModel) {
                    Text("Select model...").tag("")
                    ForEach(localModels) { model in
                        Text(model.name).tag(model.name)
                    }
                }
                .pickerStyle(.menu)
            }

            // Step 2: Dataset
            VStack(alignment: .leading, spacing: 4) {
                Text("Dataset Path (JSONL)")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                TextField("Path to dataset.jsonl...", text: $datasetPath)
                    .textFieldStyle(.roundedBorder)
            }

            // Step 3: Strategy
            VStack(alignment: .leading, spacing: 4) {
                Text("Strategy")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                Picker("Strategy", selection: $selectedStrategy) {
                    ForEach(strategies) { s in
                        Text("\(s.name.capitalized) — \(s.description)").tag(s.name)
                    }
                }
                .pickerStyle(.radioGroup)
            }

            // Strategy details
            if let strategy = strategies.first(where: { $0.name == selectedStrategy }) {
                HStack(spacing: AITopTheme.largeSpacing) {
                    statPill("Epochs", "\(strategy.epochs)")
                    statPill("LR", String(format: "%.0e", strategy.learningRate))
                    statPill("LoRA Rank", "\(strategy.loraRank)")
                    statPill("Batch", "\(strategy.batchSize)")
                }
            }

            // Start button
            HStack {
                Spacer()
                Button {
                    createAndStartJob()
                } label: {
                    HStack {
                        if isCreating {
                            ProgressView().scaleEffect(0.7)
                        }
                        Image(systemName: "play.fill")
                        Text("Start Training")
                    }
                }
                .aiTopPrimaryButton()
                .disabled(selectedModel.isEmpty || datasetPath.isEmpty || isCreating)
            }

            if let error {
                Text(error)
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.error)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Past Jobs

    private var pastJobsSection: some View {
        VStack(alignment: .leading, spacing: AITopTheme.smallSpacing) {
            Text("Job History")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)

            ForEach(jobs) { job in
                HStack {
                    statusBadge(job.status)
                    Text(job.model)
                        .font(AITopTheme.body())
                        .foregroundColor(AITopTheme.textPrimary)
                    Text(job.strategy)
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                    Spacer()
                    if job.loss > 0 {
                        Text(String(format: "Loss: %.4f", job.loss))
                            .font(AITopTheme.monospace())
                            .foregroundColor(AITopTheme.textSecondary)
                    }
                    if let elapsed = job.elapsedSeconds {
                        Text(formatDuration(elapsed))
                            .font(AITopTheme.caption())
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                }
                .padding(AITopTheme.smallSpacing)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }

    // MARK: - Helpers

    private func statusBadge(_ status: String) -> some View {
        let color: Color = {
            switch status {
            case "running": return AITopTheme.info
            case "completed": return AITopTheme.success
            case "failed": return AITopTheme.error
            case "cancelled": return AITopTheme.warning
            default: return AITopTheme.textTertiary
            }
        }()

        return Text(status.uppercased())
            .font(.system(size: 10, weight: .bold))
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.2))
            .foregroundColor(color)
            .cornerRadius(4)
    }

    private func statPill(_ label: String, _ value: String) -> some View {
        VStack(spacing: 2) {
            Text(value)
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.accentOrange)
            Text(label)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(8)
        .background(AITopTheme.surfaceBackground)
        .cornerRadius(6)
    }

    private func formatDuration(_ seconds: Double) -> String {
        let h = Int(seconds) / 3600
        let m = (Int(seconds) % 3600) / 60
        let s = Int(seconds) % 60
        if h > 0 { return "\(h)h \(m)m" }
        if m > 0 { return "\(m)m \(s)s" }
        return "\(s)s"
    }

    // MARK: - Actions

    private func loadStrategies() {
        Task {
            do {
                let resp: StrategiesResponse = try await apiService.getStrategies()
                await MainActor.run { strategies = resp.strategies }
            } catch {}
        }
    }

    private func loadJobs() {
        Task {
            do {
                let resp: JobsResponse = try await apiService.getJobs()
                await MainActor.run {
                    jobs = resp.jobs
                    activeJob = resp.jobs.first(where: { $0.status == "running" })
                }
            } catch {}
        }
    }

    private func loadModels() {
        Task {
            do {
                let resp: ModelsResponse = try await apiService.getModels()
                await MainActor.run { localModels = resp.models }
            } catch {}
        }
    }

    private func createAndStartJob() {
        isCreating = true
        error = nil
        Task {
            do {
                let job: FineTuneJob = try await apiService.createJob(
                    model: selectedModel,
                    datasetPath: datasetPath,
                    strategy: selectedStrategy
                )
                let started: FineTuneJob = try await apiService.startJob(id: job.id)
                await MainActor.run {
                    activeJob = started
                    isCreating = false
                    startPolling(jobId: started.id)
                }
            } catch {
                await MainActor.run {
                    self.error = error.localizedDescription
                    isCreating = false
                }
            }
        }
    }

    private func startPolling(jobId: String) {
        pollTimer?.invalidate()
        pollTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            Task {
                do {
                    let job: FineTuneJob = try await apiService.getJobStatus(id: jobId)
                    await MainActor.run {
                        activeJob = job
                        if job.status != "running" {
                            pollTimer?.invalidate()
                            loadJobs()
                        }
                    }
                } catch {}
            }
        }
    }
}
