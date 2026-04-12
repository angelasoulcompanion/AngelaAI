//
//  FineTuneView.swift
//  AITop — Fine-Tune Studio: Tab Container
//  Training runs in backend subprocess — switching tabs does NOT stop training.
//

import SwiftUI

struct FineTuneView: View {
    @EnvironmentObject var apiService: APIService
    @State private var selectedTab = 0
    @State private var activeJob: FineTuneJob?
    @State private var pollTimer: Timer?

    var body: some View {
        VStack(spacing: 0) {
            // Tab Bar + Active Job Indicator
            HStack(spacing: 0) {
                tabButton("Train", icon: "play.circle", tag: 0)
                tabButton("Datasets", icon: "doc.text", tag: 1)
                tabButton("Models", icon: "tray.full", tag: 2)
                tabButton("Jobs", icon: "list.bullet.rectangle", tag: 3, badge: activeJob != nil)
            }
            .padding(.horizontal, 16)
            .padding(.top, 8)

            // Active training banner (visible on all tabs)
            if let job = activeJob {
                trainingBanner(job)
            }

            Divider()
                .background(Color(hex: "2A2A4A"))

            // Tab Content
            Group {
                switch selectedTab {
                case 0: TrainView()
                case 1: DatasetsView()
                case 2: ModelHubView()
                case 3: JobsView()
                default: TrainView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .background(Color(hex: "0A0A0F"))
        .onAppear { checkActiveJob() }
        .onDisappear { stopPolling() }
        .onReceive(NotificationCenter.default.publisher(for: .init("SwitchToJobsTab"))) { _ in
            selectedTab = 3
        }
        .onReceive(NotificationCenter.default.publisher(for: .init("TrainingStarted"))) { _ in
            startPolling()
        }
    }

    // MARK: - Training Banner (always visible)

    private func trainingBanner(_ job: FineTuneJob) -> some View {
        HStack(spacing: 12) {
            ProgressView()
                .scaleEffect(0.7)
                .tint(Color(hex: "FF6B00"))

            Text("Training: \(job.model)")
                .font(.caption.bold())
                .foregroundColor(.white)
                .lineLimit(1)

            if job.totalSteps > 0 {
                let pct = Double(job.currentStep) / Double(job.totalSteps) * 100
                Text(String(format: "%.0f%%", pct))
                    .font(.system(.caption, design: .monospaced).bold())
                    .foregroundColor(Color(hex: "FF6B00"))
            }

            if job.loss > 0 {
                Text(String(format: "Loss: %.4f", job.loss))
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(Color(hex: "9CA3AF"))
            }

            if let eta = job.etaSeconds {
                Text("ETA: \(formatDuration(eta))")
                    .font(.caption)
                    .foregroundColor(Color(hex: "9CA3AF"))
            }

            Spacer()

            Button {
                selectedTab = 3 // Go to Jobs tab
            } label: {
                Text("View")
                    .font(.caption.bold())
                    .foregroundColor(Color(hex: "00D4FF"))
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(Color(hex: "FF6B00").opacity(0.1))
    }

    // MARK: - Polling (at container level — survives tab switches)

    private func checkActiveJob() {
        Task {
            if let result = try? await apiService.getJobs() {
                activeJob = result.jobs.first { $0.status == "running" }
                if activeJob != nil {
                    startPolling()
                }
            }
        }
    }

    private func startPolling() {
        guard pollTimer == nil else { return }
        pollTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { _ in
            Task {
                if let result = try? await apiService.getJobs() {
                    await MainActor.run {
                        let running = result.jobs.first { $0.status == "running" }
                        activeJob = running
                        if running == nil {
                            stopPolling()
                        }
                    }
                }
            }
        }
    }

    private func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }

    private func formatDuration(_ seconds: Double) -> String {
        let h = Int(seconds) / 3600
        let m = (Int(seconds) % 3600) / 60
        let s = Int(seconds) % 60
        if h > 0 { return "\(h)h \(m)m" }
        if m > 0 { return "\(m)m \(s)s" }
        return "\(s)s"
    }

    // MARK: - Tab Button

    private func tabButton(_ title: String, icon: String, tag: Int, badge: Bool = false) -> some View {
        Button {
            selectedTab = tag
        } label: {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                Text(title)
                    .font(.system(size: 13, weight: .medium))
                if badge {
                    Circle()
                        .fill(Color(hex: "FF6B00"))
                        .frame(width: 6, height: 6)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(selectedTab == tag ? Color(hex: "FF6B00").opacity(0.15) : Color.clear)
            .foregroundColor(selectedTab == tag ? Color(hex: "FF6B00") : Color(hex: "9CA3AF"))
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }
}
