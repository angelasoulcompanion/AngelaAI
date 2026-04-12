//
//  JobsView.swift
//  AITop — Fine-Tune Studio: Training Jobs Monitor & History
//

import SwiftUI
import Charts

struct JobsView: View {
    @EnvironmentObject var apiService: APIService

    @State private var jobs: [FineTuneJob] = []
    @State private var activeJob: FineTuneJob?
    @State private var pollTimer: Timer?
    @State private var expandedJobId: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack {
                    Text("Training Jobs")
                        .font(.title2.bold())
                        .foregroundColor(.white)
                    Spacer()
                    Button { loadJobs() } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(Color(hex: "9CA3AF"))
                    }
                    .buttonStyle(.plain)
                }

                // Active Job
                if let job = activeJob {
                    activeJobCard(job)
                }

                // Job History
                historySection
            }
            .padding(24)
        }
        .background(Color(hex: "0A0A0F"))
        .onAppear { loadJobs() }
        .onDisappear { stopPolling() }
        .onReceive(NotificationCenter.default.publisher(for: .init("SwitchToJobsTab"))) { _ in
            loadJobs()
        }
    }

    // MARK: - Active Job Card

    private func activeJobCard(_ job: FineTuneJob) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                statusBadge(job.status)
                Text(job.model)
                    .font(.headline.bold())
                    .foregroundColor(.white)
                if let method = job.trainingMethod {
                    Text(method.replacingOccurrences(of: "_", with: " ").uppercased())
                        .font(.system(size: 9).bold())
                        .padding(.horizontal, 5)
                        .padding(.vertical, 2)
                        .background(Color(hex: "FF6B00").opacity(0.3))
                        .foregroundColor(Color(hex: "FF6B00"))
                        .cornerRadius(4)
                }
                Spacer()
                if job.status == "running" {
                    Button("Cancel") {
                        Task { try? await apiService.cancelJob(id: job.id) }
                    }
                    .buttonStyle(.plain)
                    .font(.caption.bold())
                    .foregroundColor(.red)
                }
            }

            // Progress
            if job.totalSteps > 0 {
                let progress = Double(job.currentStep) / Double(job.totalSteps)
                VStack(alignment: .leading, spacing: 4) {
                    ProgressView(value: progress)
                        .tint(Color(hex: "FF6B00"))
                    HStack {
                        Text("Step \(job.currentStep)/\(job.totalSteps)")
                            .font(.caption)
                            .foregroundColor(Color(hex: "9CA3AF"))
                        Spacer()
                        if let eta = job.etaSeconds {
                            Text("ETA: \(formatDuration(eta))")
                                .font(.caption)
                                .foregroundColor(Color(hex: "9CA3AF"))
                        }
                    }
                }
            }

            // Stats Row
            HStack(spacing: 20) {
                statPill("Loss", value: String(format: "%.4f", job.loss))
                if let best = job.bestLoss {
                    statPill("Best", value: String(format: "%.4f", best))
                }
                if let elapsed = job.elapsedSeconds {
                    statPill("Elapsed", value: formatDuration(elapsed))
                }
                if let mem = job.memoryPeakGb {
                    statPill("RAM", value: String(format: "%.1fGB", mem))
                }
            }

            // Loss Chart
            if job.lossHistory.count > 1 {
                lossChart(job.lossHistory)
            }
        }
        .padding(16)
        .background(Color(hex: "1A1A2E"))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(hex: "FF6B00").opacity(0.5), lineWidth: 1)
        )
    }

    // MARK: - Loss Chart

    private func lossChart(_ history: [LossPoint]) -> some View {
        Chart {
            ForEach(Array(history.enumerated()), id: \.offset) { _, point in
                LineMark(
                    x: .value("Step", point.step),
                    y: .value("Loss", point.loss)
                )
                .foregroundStyle(Color(hex: "FF6B00"))
            }
        }
        .chartXAxisLabel("Step")
        .chartYAxisLabel("Loss")
        .frame(height: 150)
    }

    // MARK: - History Section

    private var historySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("JOB HISTORY")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            let pastJobs = jobs.filter { $0.status != "running" }.sorted {
                $0.finishedAt > $1.finishedAt
            }

            if pastJobs.isEmpty {
                Text("No completed jobs yet")
                    .font(.caption)
                    .foregroundColor(Color(hex: "6B7280"))
                    .padding(20)
            } else {
                ForEach(pastJobs) { job in
                    historyRow(job)
                }
            }
        }
    }

    private func historyRow(_ job: FineTuneJob) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                statusBadge(job.status)
                Text(job.model)
                    .font(.system(.body, design: .monospaced).bold())
                    .foregroundColor(.white)
                    .lineLimit(1)

                if let method = job.trainingMethod {
                    Text(method.replacingOccurrences(of: "_", with: " ").uppercased())
                        .font(.system(size: 8).bold())
                        .padding(.horizontal, 4)
                        .padding(.vertical, 1)
                        .background(Color.blue.opacity(0.3))
                        .cornerRadius(3)
                        .foregroundColor(.blue)
                }

                Spacer()

                Text(String(format: "Loss: %.4f", job.loss))
                    .font(.caption)
                    .foregroundColor(Color(hex: "9CA3AF"))

                if let elapsed = job.elapsedSeconds {
                    Text(formatDuration(elapsed))
                        .font(.caption)
                        .foregroundColor(Color(hex: "6B7280"))
                }

                Button {
                    expandedJobId = expandedJobId == job.id ? nil : job.id
                } label: {
                    Image(systemName: expandedJobId == job.id ? "chevron.up" : "chevron.down")
                        .foregroundColor(Color(hex: "9CA3AF"))
                }
                .buttonStyle(.plain)
            }
            .padding(12)

            // Expanded detail
            if expandedJobId == job.id {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 16) {
                        detailItem("Strategy", job.strategy)
                        detailItem("Epochs", "\(job.epochs)")
                        detailItem("LR", String(format: "%.1e", job.learningRate))
                        detailItem("Rank", "\(job.loraRank)")
                        detailItem("Batch", "\(job.batchSize)")
                    }

                    if !job.error.isEmpty {
                        Text("Error: \(job.error)")
                            .font(.caption)
                            .foregroundColor(.red)
                    }

                    if job.lossHistory.count > 1 {
                        lossChart(job.lossHistory)
                    }

                    // Deploy button for completed jobs
                    if job.status == "completed" && !job.outputDir.isEmpty {
                        Button {
                            // TODO: Deploy to Ollama
                        } label: {
                            HStack {
                                Image(systemName: "arrow.up.circle")
                                Text("Deploy to Ollama")
                            }
                            .font(.caption.bold())
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.green.opacity(0.2))
                            .foregroundColor(.green)
                            .cornerRadius(6)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.bottom, 12)
            }
        }
        .background(Color(hex: "12121F"))
        .cornerRadius(8)
    }

    // MARK: - Helpers

    private func statusBadge(_ status: String) -> some View {
        let (color, icon): (Color, String) = {
            switch status {
            case "running": return (.blue, "circle.fill")
            case "completed": return (.green, "checkmark.circle.fill")
            case "failed": return (.red, "xmark.circle.fill")
            case "cancelled": return (.orange, "minus.circle.fill")
            default: return (.gray, "circle")
            }
        }()

        return Image(systemName: icon)
            .foregroundColor(color)
            .font(.caption)
    }

    private func statPill(_ label: String, value: String) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(Color(hex: "9CA3AF"))
            Text(value)
                .font(.system(.caption, design: .monospaced).bold())
                .foregroundColor(.white)
        }
    }

    private func detailItem(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(Color(hex: "6B7280"))
            Text(value)
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))
        }
    }

    private func formatDuration(_ seconds: Double) -> String {
        let h = Int(seconds) / 3600
        let m = (Int(seconds) % 3600) / 60
        let s = Int(seconds) % 60
        if h > 0 { return "\(h)h \(m)m" }
        if m > 0 { return "\(m)m \(s)s" }
        return "\(s)s"
    }

    // MARK: - Data Loading

    private func loadJobs() {
        Task {
            if let result = try? await apiService.getJobs() {
                jobs = result.jobs
                activeJob = jobs.first { $0.status == "running" }
                if activeJob != nil {
                    startPolling()
                } else {
                    stopPolling()
                }
            }
        }
    }

    private func startPolling() {
        guard pollTimer == nil else { return }
        pollTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            loadJobs()
        }
    }

    private func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }
}
