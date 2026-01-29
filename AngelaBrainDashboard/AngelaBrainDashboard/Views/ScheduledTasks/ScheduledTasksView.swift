//
//  ScheduledTasksView.swift
//  Angela Brain Dashboard
//
//  Scheduled Tasks - Live clock, countdown, CRUD, auto-execute
//  With: full command display, Python/Shell sections, detail view,
//        built-in script editor, test run capability
//

import SwiftUI
import Combine

struct ScheduledTasksView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var tasks: [DashboardScheduledTask] = []
    @State private var recentLogs: [DashboardTaskLog] = []
    @State private var nextTask: NextScheduledTask?
    @State private var isLoading = false
    @State private var showAddSheet = false
    @State private var editingTask: DashboardScheduledTask?
    @State private var selectedTaskForDetail: DashboardScheduledTask?
    @State private var executingTaskIds: Set<String> = []

    // Clock state
    @State private var currentTime = Date()
    @State private var countdownSeconds: Int = 0

    // Timers
    private let clockTimer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    private let executionTimer = Timer.publish(every: 60, on: .main, in: .common).autoconnect()

    private let bangkokTZ = TimeZone(identifier: "Asia/Bangkok")!

    // Computed task lists
    private var pythonTasks: [DashboardScheduledTask] {
        tasks.filter { $0.taskType == "python" }
    }

    private var shellTasks: [DashboardScheduledTask] {
        tasks.filter { $0.taskType == "shell" }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.spacing) {
                headerSection
                clockAndCountdownSection
                statsSection
                pythonScriptsSection
                shellCommandsSection
                recentLogsSection
            }
            .padding(AngelaTheme.spacing)
        }
        .background(AngelaTheme.backgroundDark)
        .onAppear {
            Task { await loadAllData() }
        }
        .onReceive(clockTimer) { _ in
            currentTime = Date()
            if countdownSeconds > 0 {
                countdownSeconds -= 1
            }
        }
        .onReceive(executionTimer) { _ in
            Task {
                await checkAndExecuteTasks()
                await loadAllData()
            }
        }
        .sheet(isPresented: $showAddSheet) {
            AddScheduledTaskSheet { request in
                Task {
                    try? await databaseService.createScheduledTask(request)
                    await loadAllData()
                }
            }
        }
        .sheet(item: $editingTask) { task in
            EditScheduledTaskSheet(task: task) { request in
                Task {
                    try? await databaseService.updateScheduledTask(taskId: task.id.uuidString, request)
                    await loadAllData()
                }
            }
        }
        .sheet(item: $selectedTaskForDetail) { task in
            ScheduledTaskDetailView(
                task: task,
                databaseService: databaseService,
                onUpdate: {
                    Task { await loadAllData() }
                }
            )
        }
    }

    // MARK: - Data Loading

    private func loadAllData() async {
        isLoading = true
        defer { isLoading = false }

        do {
            tasks = try await databaseService.fetchScheduledTasks()
        } catch {
            print("Error fetching tasks: \(error)")
        }

        do {
            nextTask = try await databaseService.fetchNextScheduledTask()
            if let next = nextTask {
                countdownSeconds = next.secondsUntil
            }
        } catch {
            nextTask = nil
        }

        // Load recent logs from all active tasks
        var allLogs: [DashboardTaskLog] = []
        for task in tasks.prefix(10) {
            if let logs = try? await databaseService.fetchScheduledTaskLogs(taskId: task.id.uuidString, limit: 5) {
                allLogs.append(contentsOf: logs)
            }
        }
        recentLogs = allLogs.sorted { $0.startedAt > $1.startedAt }.prefix(20).map { $0 }
    }

    // MARK: - Auto-Execute Logic

    private func checkAndExecuteTasks() async {
        let calendar = Calendar.current
        let components = calendar.dateComponents(in: bangkokTZ, from: Date())
        let nowHH = components.hour ?? 0
        let nowMM = components.minute ?? 0
        let nowString = String(format: "%02d:%02d", nowHH, nowMM)

        for task in tasks where task.isActive {
            if task.scheduleType == "time", let schedTime = task.scheduleTime {
                if schedTime == nowString {
                    if let lastRun = task.lastRunAt {
                        let elapsed = Date().timeIntervalSince(lastRun)
                        if elapsed < 120 { continue }
                    }
                    await executeTask(task)
                }
            } else if task.scheduleType == "interval", let interval = task.intervalMinutes {
                if let lastRun = task.lastRunAt {
                    let elapsed = Date().timeIntervalSince(lastRun) / 60.0
                    if elapsed < Double(interval) { continue }
                }
                await executeTask(task)
            }
        }
    }

    private func executeTask(_ task: DashboardScheduledTask) async {
        let taskIdStr = task.id.uuidString
        guard !executingTaskIds.contains(taskIdStr) else { return }

        executingTaskIds.insert(taskIdStr)
        defer { executingTaskIds.remove(taskIdStr) }

        _ = try? await databaseService.executeScheduledTask(taskId: taskIdStr)
    }

    // MARK: - Header Section

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text("Scheduled Tasks")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Manage Python scripts & Shell commands")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Button {
                showAddSheet = true
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "plus.circle.fill")
                    Text("Add Task")
                }
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(AngelaTheme.primaryPurple)
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)

            Button {
                Task { await loadAllData() }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .frame(width: 36, height: 36)
                    .background(AngelaTheme.cardBackground)
                    .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Clock & Countdown Section

    private var clockAndCountdownSection: some View {
        HStack(spacing: AngelaTheme.spacing) {
            // Live Clock
            VStack(spacing: 8) {
                Text("Bangkok Time")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                Text(formattedClock)
                    .font(.system(size: 56, weight: .ultraLight, design: .monospaced))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [AngelaTheme.primaryPurple, AngelaTheme.secondaryPurple],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )

                Text(formattedDate)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 24)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)

            // Next Task Countdown
            VStack(spacing: 8) {
                Text("Next Task")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                if let next = nextTask {
                    Text(formatCountdown(countdownSeconds))
                        .font(.system(size: 56, weight: .ultraLight, design: .monospaced))
                        .foregroundColor(AngelaTheme.accentGold)

                    Text(next.taskName)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)

                    Text(next.scheduleDisplay)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textTertiary)
                } else {
                    Text("--:--:--")
                        .font(.system(size: 56, weight: .ultraLight, design: .monospaced))
                        .foregroundColor(AngelaTheme.textTertiary)

                    Text("No active tasks")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textTertiary)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 24)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
        }
    }

    // MARK: - Stats Section

    private var statsSection: some View {
        HStack(spacing: AngelaTheme.smallSpacing) {
            statCard(title: "Total", value: "\(tasks.count)", icon: "list.bullet", color: AngelaTheme.primaryPurple)
            statCard(title: "Python", value: "\(pythonTasks.count)", icon: "chevron.left.forwardslash.chevron.right", color: Color(hex: "3B82F6"))
            statCard(title: "Shell", value: "\(shellTasks.count)", icon: "terminal.fill", color: Color(hex: "10B981"))
            statCard(title: "Active", value: "\(tasks.filter { $0.isActive }.count)", icon: "bolt.fill", color: AngelaTheme.accentGold)
            statCard(title: "Completed", value: "\(todayCompletedCount)", icon: "checkmark.circle.fill", color: AngelaTheme.successGreen)
            statCard(title: "Failed", value: "\(todayFailedCount)", icon: "xmark.circle.fill", color: AngelaTheme.errorRed)
        }
    }

    private func statCard(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 28, weight: .bold, design: .monospaced))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Python Scripts Section

    private var pythonScriptsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Section header
            HStack(spacing: 10) {
                Image(systemName: "chevron.left.forwardslash.chevron.right")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(Color(hex: "3B82F6"))

                Text("Python Scripts")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("\(pythonTasks.count)")
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundColor(Color(hex: "3B82F6"))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color(hex: "3B82F6").opacity(0.15))
                    .cornerRadius(6)

                Spacer()

                Button {
                    showAddSheet = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "plus")
                            .font(.system(size: 11, weight: .bold))
                        Text("Add Python")
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(Color(hex: "3B82F6"))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color(hex: "3B82F6").opacity(0.12))
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }

            if pythonTasks.isEmpty {
                emptySection(
                    icon: "chevron.left.forwardslash.chevron.right",
                    title: "No Python scripts",
                    subtitle: "Add a Python script to schedule automated execution",
                    color: Color(hex: "3B82F6")
                )
            } else {
                ForEach(pythonTasks) { task in
                    taskCard(task, accentColor: Color(hex: "3B82F6"))
                }
            }
        }
    }

    // MARK: - Shell Commands Section

    private var shellCommandsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Section header
            HStack(spacing: 10) {
                Image(systemName: "terminal.fill")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(Color(hex: "10B981"))

                Text("Shell Commands")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("\(shellTasks.count)")
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundColor(Color(hex: "10B981"))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color(hex: "10B981").opacity(0.15))
                    .cornerRadius(6)

                Spacer()

                Button {
                    showAddSheet = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "plus")
                            .font(.system(size: 11, weight: .bold))
                        Text("Add Shell")
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(Color(hex: "10B981"))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color(hex: "10B981").opacity(0.12))
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
            }

            if shellTasks.isEmpty {
                emptySection(
                    icon: "terminal.fill",
                    title: "No shell commands",
                    subtitle: "Add a shell command to schedule automated execution",
                    color: Color(hex: "10B981")
                )
            } else {
                ForEach(shellTasks) { task in
                    taskCard(task, accentColor: Color(hex: "10B981"))
                }
            }
        }
    }

    // MARK: - Empty Section

    private func emptySection(icon: String, title: String, subtitle: String, color: Color) -> some View {
        VStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 32))
                .foregroundColor(color.opacity(0.4))
            Text(title)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
            Text(subtitle)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 30)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Task Card

    private func taskCard(_ task: DashboardScheduledTask, accentColor: Color) -> some View {
        Button {
            selectedTaskForDetail = task
        } label: {
            VStack(alignment: .leading, spacing: 0) {
                // Top row: name + status + actions
                HStack(spacing: 12) {
                    // Type icon
                    Image(systemName: task.typeIcon)
                        .font(.system(size: 16))
                        .foregroundColor(accentColor)
                        .frame(width: 32, height: 32)
                        .background(accentColor.opacity(0.15))
                        .cornerRadius(7)

                    // Info
                    VStack(alignment: .leading, spacing: 3) {
                        HStack(spacing: 8) {
                            Text(task.taskName)
                                .font(AngelaTheme.heading())
                                .foregroundColor(task.isActive ? AngelaTheme.textPrimary : AngelaTheme.textTertiary)

                            if !task.isActive {
                                Text("INACTIVE")
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(AngelaTheme.textTertiary)
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 2)
                                    .background(AngelaTheme.textTertiary.opacity(0.2))
                                    .cornerRadius(3)
                            }
                        }

                        HStack(spacing: 10) {
                            Label(task.scheduleDisplayText, systemImage: task.scheduleType == "time" ? "clock" : "repeat")
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)

                            if let desc = task.description, !desc.isEmpty {
                                Text(desc)
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.textTertiary)
                                    .lineLimit(1)
                            }
                        }
                    }

                    Spacer()

                    // Status badge
                    if let status = task.lastStatus {
                        HStack(spacing: 4) {
                            Image(systemName: task.statusIcon)
                                .font(.system(size: 12))
                            Text(status.capitalized)
                                .font(.system(size: 11, weight: .semibold))
                        }
                        .foregroundColor(Color(hex: task.statusColor))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(hex: task.statusColor).opacity(0.12))
                        .cornerRadius(6)
                    }

                    // Action buttons
                    HStack(spacing: 3) {
                        // Toggle active
                        Button {
                            Task {
                                var req = ScheduledTaskUpdateRequest()
                                req.isActive = !task.isActive
                                try? await databaseService.updateScheduledTask(taskId: task.id.uuidString, req)
                                await loadAllData()
                            }
                        } label: {
                            Image(systemName: task.isActive ? "pause.circle" : "play.circle")
                                .font(.system(size: 17))
                                .foregroundColor(task.isActive ? AngelaTheme.warningOrange : AngelaTheme.successGreen)
                        }
                        .buttonStyle(.plain)
                        .help(task.isActive ? "Pause" : "Resume")

                        // Run now
                        Button {
                            Task {
                                await executeTask(task)
                                await loadAllData()
                            }
                        } label: {
                            Image(systemName: executingTaskIds.contains(task.id.uuidString) ? "arrow.triangle.2.circlepath" : "play.fill")
                                .font(.system(size: 14))
                                .foregroundColor(AngelaTheme.primaryPurple)
                        }
                        .buttonStyle(.plain)
                        .disabled(executingTaskIds.contains(task.id.uuidString))
                        .help("Run Now")

                        // Edit
                        Button {
                            editingTask = task
                        } label: {
                            Image(systemName: "pencil.circle")
                                .font(.system(size: 17))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                        .buttonStyle(.plain)
                        .help("Edit")

                        // Delete
                        Button {
                            Task {
                                try? await databaseService.deleteScheduledTask(taskId: task.id.uuidString)
                                await loadAllData()
                            }
                        } label: {
                            Image(systemName: "trash")
                                .font(.system(size: 13))
                                .foregroundColor(AngelaTheme.errorRed.opacity(0.7))
                        }
                        .buttonStyle(.plain)
                        .help("Delete")
                    }
                }
                .padding(.horizontal, 14)
                .padding(.top, 12)
                .padding(.bottom, 8)

                // Command display
                HStack(spacing: 0) {
                    Rectangle()
                        .fill(accentColor.opacity(0.6))
                        .frame(width: 3)

                    HStack(spacing: 6) {
                        Text(task.taskType == "python" ? "$" : ">")
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundColor(accentColor.opacity(0.6))

                        Text(task.command)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(AngelaTheme.textSecondary)
                            .lineLimit(2)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(Color.black.opacity(0.2))
                }
                .cornerRadius(0)
                .padding(.horizontal, 14)
                .padding(.bottom, 12)

                // Last run info
                if let lastRun = task.lastRunAt {
                    HStack {
                        Text("Last run: \(formatLogTime(lastRun))")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)

                        Spacer()

                        Text("Click for details")
                            .font(.system(size: 10))
                            .foregroundColor(accentColor.opacity(0.5))

                        Image(systemName: "chevron.right")
                            .font(.system(size: 9))
                            .foregroundColor(accentColor.opacity(0.5))
                    }
                    .padding(.horizontal, 14)
                    .padding(.bottom, 8)
                }
            }
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                    .stroke(accentColor.opacity(0.15), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Recent Logs Section

    private var recentLogsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Recent Execution Logs")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if recentLogs.isEmpty {
                Text("No execution logs yet")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 24)
                    .background(AngelaTheme.cardBackground)
                    .cornerRadius(AngelaTheme.cornerRadius)
            } else {
                ForEach(recentLogs) { log in
                    logRow(log)
                }
            }
        }
    }

    private func logRow(_ log: DashboardTaskLog) -> some View {
        HStack(spacing: 12) {
            Image(systemName: log.statusIcon)
                .font(.system(size: 14))
                .foregroundColor(Color(hex: log.statusColor))

            let taskName = tasks.first(where: { $0.id == log.taskId })?.taskName ?? "Unknown"
            let taskType = tasks.first(where: { $0.id == log.taskId })?.taskType ?? "shell"

            Text(taskType.uppercased())
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundColor(taskType == "python" ? Color(hex: "3B82F6") : Color(hex: "10B981"))
                .padding(.horizontal, 5)
                .padding(.vertical, 2)
                .background((taskType == "python" ? Color(hex: "3B82F6") : Color(hex: "10B981")).opacity(0.12))
                .cornerRadius(3)

            Text(taskName)
                .font(AngelaTheme.heading())
                .foregroundColor(AngelaTheme.textPrimary)
                .lineLimit(1)

            Spacer()

            Text(log.durationFormatted)
                .font(.system(size: 12, weight: .medium, design: .monospaced))
                .foregroundColor(AngelaTheme.textSecondary)

            Text(formatLogTime(log.startedAt))
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }

    // MARK: - Computed Properties

    private var todayCompletedCount: Int {
        recentLogs.filter {
            Calendar.current.isDateInToday($0.startedAt) && $0.status == "completed"
        }.count
    }

    private var todayFailedCount: Int {
        recentLogs.filter {
            Calendar.current.isDateInToday($0.startedAt) && $0.status == "failed"
        }.count
    }

    private var formattedClock: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        formatter.timeZone = bangkokTZ
        return formatter.string(from: currentTime)
    }

    private var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE, d MMMM yyyy"
        formatter.locale = Locale(identifier: "en_US")
        formatter.timeZone = bangkokTZ
        return formatter.string(from: currentTime)
    }

    private func formatCountdown(_ seconds: Int) -> String {
        let h = seconds / 3600
        let m = (seconds % 3600) / 60
        let s = seconds % 60
        return String(format: "%02d:%02d:%02d", h, m, s)
    }

    private func formatLogTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        formatter.timeZone = bangkokTZ
        return formatter.string(from: date)
    }
}

// MARK: - Task Detail View (Separate Page)

struct ScheduledTaskDetailView: View {
    let task: DashboardScheduledTask
    let databaseService: DatabaseService
    let onUpdate: () -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var logs: [DashboardTaskLog] = []
    @State private var isLoadingLogs = true

    // Script Editor state
    @State private var editedCommand: String
    @State private var isEditingCommand = false
    @State private var isSavingCommand = false

    // Test Run state
    @State private var isRunningTest = false
    @State private var testOutput: String?
    @State private var testError: String?
    @State private var testStatus: String?
    @State private var testDuration: Int?

    // Script File Editor state (Built-in Code Editor)
    @State private var showScriptFileEditor = false
    @State private var scriptFileContent: String = ""
    @State private var isSavingScriptFile = false
    @State private var isLoadingScriptFile = false
    @State private var scriptFileError: String?

    private let accentColor: Color

    init(task: DashboardScheduledTask, databaseService: DatabaseService, onUpdate: @escaping () -> Void) {
        self.task = task
        self.databaseService = databaseService
        self.onUpdate = onUpdate
        self.accentColor = task.taskType == "python" ? Color(hex: "3B82F6") : Color(hex: "10B981")
        _editedCommand = State(initialValue: task.command)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header bar
            HStack(spacing: 12) {
                Image(systemName: task.typeIcon)
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(accentColor)
                    .frame(width: 36, height: 36)
                    .background(accentColor.opacity(0.15))
                    .cornerRadius(8)

                VStack(alignment: .leading, spacing: 2) {
                    Text(task.taskName)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)

                    HStack(spacing: 8) {
                        Text(task.taskType.uppercased())
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundColor(accentColor)

                        if let desc = task.description, !desc.isEmpty {
                            Text(desc)
                                .font(.system(size: 12))
                                .foregroundColor(.gray)
                                .lineLimit(1)
                        }
                    }
                }

                Spacer()

                // Status
                if let status = task.lastStatus {
                    HStack(spacing: 4) {
                        Image(systemName: task.statusIcon)
                            .font(.system(size: 12))
                        Text(status.capitalized)
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(Color(hex: task.statusColor))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(Color(hex: task.statusColor).opacity(0.12))
                    .cornerRadius(8)
                }

                Button("Close") { dismiss() }
                    .foregroundColor(.gray)
            }
            .padding(16)
            .background(Color(hex: "252535"))

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Task Info Cards
                    taskInfoSection

                    // Script Editor
                    scriptEditorSection

                    // Test Run
                    testRunSection

                    // Execution Logs
                    executionLogsSection
                }
                .padding(20)
            }
        }
        .frame(width: 800, height: 700)
        .background(Color(hex: "1F1F28"))
        .onAppear {
            Task {
                do {
                    logs = try await databaseService.fetchScheduledTaskLogs(taskId: task.id.uuidString, limit: 50)
                } catch {
                    print("Error loading logs: \(error)")
                }
                isLoadingLogs = false
            }
        }
        .sheet(isPresented: $showScriptFileEditor) {
            if let scriptPath = extractScriptPath(from: task.command) {
                ScriptFileEditorSheet(
                    path: scriptPath,
                    content: $scriptFileContent,
                    isSaving: $isSavingScriptFile,
                    errorMessage: $scriptFileError,
                    onSave: { newContent in
                        Task {
                            let success = await saveScriptFile(path: scriptPath, content: newContent)
                            if success {
                                showScriptFileEditor = false
                            }
                        }
                    }
                )
            }
        }
    }

    // MARK: - Task Info Section

    private var taskInfoSection: some View {
        HStack(spacing: 16) {
            infoCard(label: "Schedule", value: task.scheduleDisplayText,
                     icon: task.scheduleType == "time" ? "clock" : "repeat")

            infoCard(label: "Status", value: task.isActive ? "Active" : "Inactive",
                     icon: task.isActive ? "bolt.fill" : "bolt.slash.fill")

            if let lastRun = task.lastRunAt {
                infoCard(label: "Last Run", value: formatDetailTime(lastRun),
                         icon: "clock.arrow.circlepath")
            }

            infoCard(label: "Total Runs", value: "\(logs.count)",
                     icon: "number")
        }
    }

    private func infoCard(label: String, value: String, icon: String) -> some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(accentColor)

            Text(value)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.white)

            Text(label)
                .font(.system(size: 11))
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 14)
        .background(Color(hex: "252535"))
        .cornerRadius(10)
    }

    // MARK: - Script Editor Section

    private var scriptEditorSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "doc.text.fill")
                    .foregroundColor(accentColor)
                Text(task.taskType == "python" ? "Python Script" : "Shell Command")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Spacer()

                if isEditingCommand {
                    Button {
                        isEditingCommand = false
                        editedCommand = task.command
                    } label: {
                        Text("Cancel")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.gray)
                    }
                    .buttonStyle(.plain)

                    Button {
                        Task { await saveEditedCommand() }
                    } label: {
                        HStack(spacing: 4) {
                            if isSavingCommand {
                                ProgressView()
                                    .scaleEffect(0.6)
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            }
                            Text("Save")
                                .font(.system(size: 12, weight: .semibold))
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 5)
                        .background(Color(hex: "9333EA"))
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                    .disabled(isSavingCommand || editedCommand == task.command)
                } else {
                    // Edit Script File button (only for Python with file path)
                    if task.taskType == "python", let scriptPath = extractScriptPath(from: task.command) {
                        Button {
                            Task { await loadScriptFile(path: scriptPath) }
                        } label: {
                            HStack(spacing: 4) {
                                if isLoadingScriptFile {
                                    ProgressView()
                                        .scaleEffect(0.5)
                                        .progressViewStyle(CircularProgressViewStyle(tint: accentColor))
                                } else {
                                    Image(systemName: "doc.badge.gearshape")
                                        .font(.system(size: 11))
                                }
                                Text("Edit Script File")
                                    .font(.system(size: 12, weight: .semibold))
                            }
                            .foregroundColor(Color(hex: "F59E0B"))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(Color(hex: "F59E0B").opacity(0.12))
                            .cornerRadius(6)
                        }
                        .buttonStyle(.plain)
                        .disabled(isLoadingScriptFile)
                    }

                    Button {
                        isEditingCommand = true
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "pencil")
                                .font(.system(size: 11))
                            Text("Edit Command")
                                .font(.system(size: 12, weight: .semibold))
                        }
                        .foregroundColor(accentColor)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(accentColor.opacity(0.12))
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }
            }

            // Editor area
            VStack(spacing: 0) {
                // Toolbar bar
                HStack(spacing: 8) {
                    Circle().fill(Color(hex: "EF4444")).frame(width: 10, height: 10)
                    Circle().fill(Color(hex: "FBBF24")).frame(width: 10, height: 10)
                    Circle().fill(Color(hex: "10B981")).frame(width: 10, height: 10)

                    Spacer()

                    Text(task.taskType == "python" ? "python3" : "bash")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.gray)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(hex: "1a1a24"))

                if isEditingCommand {
                    TextEditor(text: $editedCommand)
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundColor(Color(hex: "E2E8F0"))
                        .scrollContentBackground(.hidden)
                        .padding(10)
                        .background(Color.black.opacity(0.4))
                        .frame(minHeight: 100, maxHeight: 200)
                } else {
                    HStack(spacing: 0) {
                        // Line numbers
                        let lines = task.command.components(separatedBy: "\n")
                        VStack(alignment: .trailing, spacing: 0) {
                            ForEach(Array(lines.enumerated()), id: \.offset) { idx, _ in
                                Text("\(idx + 1)")
                                    .font(.system(size: 12, design: .monospaced))
                                    .foregroundColor(Color.gray.opacity(0.4))
                                    .frame(height: 20)
                            }
                        }
                        .padding(.leading, 10)
                        .padding(.trailing, 8)
                        .padding(.vertical, 10)

                        Rectangle()
                            .fill(Color.gray.opacity(0.15))
                            .frame(width: 1)

                        // Code
                        VStack(alignment: .leading, spacing: 0) {
                            ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                                Text(line.isEmpty ? " " : line)
                                    .font(.system(size: 13, design: .monospaced))
                                    .foregroundColor(Color(hex: "E2E8F0"))
                                    .frame(height: 20, alignment: .leading)
                            }
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 10)

                        Spacer()
                    }
                    .background(Color.black.opacity(0.4))
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isEditingCommand ? accentColor.opacity(0.5) : Color.gray.opacity(0.2), lineWidth: 1)
            )
        }
    }

    // MARK: - Test Run Section

    private var testRunSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "play.rectangle.fill")
                    .foregroundColor(AngelaTheme.accentGold)
                Text("Test Run")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Spacer()

                Button {
                    Task { await runTest() }
                } label: {
                    HStack(spacing: 6) {
                        if isRunningTest {
                            ProgressView()
                                .scaleEffect(0.6)
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Image(systemName: "play.fill")
                                .font(.system(size: 11))
                        }
                        Text(isRunningTest ? "Running..." : "Run Test")
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(isRunningTest ? Color.gray : AngelaTheme.accentGold)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
                .disabled(isRunningTest)

                if testStatus != nil {
                    Button {
                        testOutput = nil
                        testError = nil
                        testStatus = nil
                        testDuration = nil
                    } label: {
                        Text("Clear")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.gray)
                    }
                    .buttonStyle(.plain)
                }
            }

            // Test output terminal
            if isRunningTest || testStatus != nil {
                VStack(alignment: .leading, spacing: 0) {
                    // Terminal header
                    HStack {
                        Image(systemName: "terminal")
                            .font(.system(size: 11))
                            .foregroundColor(.gray)
                        Text("Output")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(.gray)

                        Spacer()

                        if let status = testStatus {
                            HStack(spacing: 4) {
                                Image(systemName: status == "completed" ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .font(.system(size: 11))
                                Text(status.capitalized)
                                    .font(.system(size: 11, weight: .semibold))
                            }
                            .foregroundColor(status == "completed" ? Color(hex: "10B981") : Color(hex: "EF4444"))
                        }

                        if let ms = testDuration {
                            Text(formatDurationMs(ms))
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.gray)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color(hex: "1a1a24"))

                    // Output content
                    ScrollView {
                        VStack(alignment: .leading, spacing: 4) {
                            if isRunningTest {
                                HStack(spacing: 8) {
                                    ProgressView()
                                        .scaleEffect(0.6)
                                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "FBBF24")))
                                    Text("Executing...")
                                        .font(.system(size: 12, design: .monospaced))
                                        .foregroundColor(Color(hex: "FBBF24"))
                                }
                                .padding(10)
                            }

                            if let output = testOutput, !output.isEmpty {
                                Text(output)
                                    .font(.system(size: 12, design: .monospaced))
                                    .foregroundColor(Color(hex: "10B981"))
                                    .textSelection(.enabled)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(10)
                            }

                            if let error = testError, !error.isEmpty {
                                Text(error)
                                    .font(.system(size: 12, design: .monospaced))
                                    .foregroundColor(Color(hex: "EF4444"))
                                    .textSelection(.enabled)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(10)
                            }

                            if testStatus != nil && (testOutput ?? "").isEmpty && (testError ?? "").isEmpty {
                                Text("(no output)")
                                    .font(.system(size: 12, design: .monospaced))
                                    .foregroundColor(.gray)
                                    .padding(10)
                            }
                        }
                    }
                    .frame(maxHeight: 200)
                    .background(Color.black.opacity(0.4))
                }
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray.opacity(0.2), lineWidth: 1)
                )
            }
        }
    }

    // MARK: - Execution Logs Section

    private var executionLogsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("Execution History")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Spacer()

                Text("\(logs.count) runs")
                    .font(.system(size: 12))
                    .foregroundColor(.gray)
            }

            if isLoadingLogs {
                HStack {
                    Spacer()
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "9333EA")))
                    Spacer()
                }
                .padding(.vertical, 20)
            } else if logs.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 28))
                        .foregroundColor(.gray.opacity(0.4))
                    Text("No execution logs yet")
                        .font(.system(size: 13))
                        .foregroundColor(.gray)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 20)
                .background(Color(hex: "252535"))
                .cornerRadius(8)
            } else {
                ForEach(logs) { log in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Image(systemName: log.statusIcon)
                                .font(.system(size: 12))
                                .foregroundColor(Color(hex: log.statusColor))
                            Text(log.status.capitalized)
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(Color(hex: log.statusColor))

                            Spacer()

                            Text(log.durationFormatted)
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(.gray)

                            Text(formatDetailTime(log.startedAt))
                                .font(.system(size: 11))
                                .foregroundColor(.gray)
                        }

                        if let output = log.output, !output.isEmpty {
                            Text(String(output.prefix(300)))
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(Color(hex: "10B981"))
                                .lineLimit(4)
                                .padding(6)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color.black.opacity(0.25))
                                .cornerRadius(4)
                        }

                        if let error = log.error, !error.isEmpty {
                            Text(String(error.prefix(300)))
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(Color(hex: "EF4444"))
                                .lineLimit(4)
                                .padding(6)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color.black.opacity(0.25))
                                .cornerRadius(4)
                        }
                    }
                    .padding(10)
                    .background(Color(hex: "252535"))
                    .cornerRadius(6)
                }
            }
        }
    }

    // MARK: - Actions

    private func saveEditedCommand() async {
        isSavingCommand = true
        defer { isSavingCommand = false }

        var req = ScheduledTaskUpdateRequest()
        req.command = editedCommand
        do {
            try await databaseService.updateScheduledTask(taskId: task.id.uuidString, req)
            isEditingCommand = false
            onUpdate()
        } catch {
            print("Error saving command: \(error)")
        }
    }

    private func runTest() async {
        isRunningTest = true
        testOutput = nil
        testError = nil
        testStatus = nil
        testDuration = nil

        do {
            let response = try await databaseService.executeScheduledTask(taskId: task.id.uuidString)
            testOutput = response.output
            testError = response.error
            testStatus = response.status
            testDuration = response.durationMs
            onUpdate()

            // Reload logs
            if let newLogs = try? await databaseService.fetchScheduledTaskLogs(taskId: task.id.uuidString, limit: 50) {
                logs = newLogs
            }
        } catch {
            testStatus = "failed"
            testError = error.localizedDescription
        }

        isRunningTest = false
    }

    // MARK: - Script File Editor Actions

    /// Extract Python script path from command (e.g., "python3 angela_core/script.py" -> "angela_core/script.py")
    private func extractScriptPath(from command: String) -> String? {
        // Pattern: python3 path/to/script.py [args...]
        let components = command.trimmingCharacters(in: .whitespaces).components(separatedBy: " ")
        for (index, component) in components.enumerated() {
            if component.hasSuffix(".py") {
                return component
            }
            // Handle case where python3 is followed by the script path
            if component == "python3" || component == "python" {
                if index + 1 < components.count && components[index + 1].hasSuffix(".py") {
                    return components[index + 1]
                }
            }
        }
        return nil
    }

    /// Load script file content for editing
    private func loadScriptFile(path: String) async {
        isLoadingScriptFile = true
        scriptFileError = nil

        do {
            let response = try await databaseService.fetchPythonScriptContent(path: path)
            scriptFileContent = response.content
            showScriptFileEditor = true
        } catch {
            scriptFileError = "Failed to load script: \(error.localizedDescription)"
            print("Error loading script file: \(error)")
        }

        isLoadingScriptFile = false
    }

    /// Save script file content
    private func saveScriptFile(path: String, content: String) async -> Bool {
        isSavingScriptFile = true
        defer { isSavingScriptFile = false }

        do {
            _ = try await databaseService.savePythonScriptContent(path: path, content: content)
            return true
        } catch {
            scriptFileError = "Failed to save script: \(error.localizedDescription)"
            print("Error saving script file: \(error)")
            return false
        }
    }

    // MARK: - Formatting

    private func formatDetailTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM HH:mm"
        formatter.timeZone = TimeZone(identifier: "Asia/Bangkok")
        return formatter.string(from: date)
    }

    private func formatDurationMs(_ ms: Int) -> String {
        if ms < 1000 {
            return "\(ms)ms"
        } else {
            let seconds = Double(ms) / 1000.0
            return String(format: "%.1fs", seconds)
        }
    }
}

// MARK: - Add Scheduled Task Sheet

struct AddScheduledTaskSheet: View {
    let onSave: (ScheduledTaskCreateRequest) -> Void
    @EnvironmentObject var databaseService: DatabaseService
    @Environment(\.dismiss) private var dismiss

    @State private var taskName = ""
    @State private var description = ""
    @State private var taskType = "shell"
    @State private var command = ""
    @State private var scheduleType = "time"
    @State private var scheduleHour = 8
    @State private var scheduleMinute = 0
    @State private var intervalMinutes = 60

    // Script browser state
    @State private var showScriptBrowser = false
    @State private var pythonScripts: [PythonScriptFile] = []
    @State private var scriptSearchText = ""
    @State private var isLoadingScripts = false
    @State private var selectedFolder: String = "all"

    private var accentColor: Color {
        taskType == "python" ? Color(hex: "3B82F6") : Color(hex: "10B981")
    }

    private let scriptFolders = ["all", "angela_core", "scripts", "mcp_servers", "config", "tests"]

    private var filteredScripts: [PythonScriptFile] {
        var filtered = pythonScripts
        if selectedFolder != "all" {
            filtered = filtered.filter { $0.folder == selectedFolder }
        }
        if !scriptSearchText.isEmpty {
            let search = scriptSearchText.lowercased()
            filtered = filtered.filter {
                $0.path.lowercased().contains(search) || $0.filename.lowercased().contains(search)
            }
        }
        return filtered
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Add Scheduled Task")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.white)
                Spacer()
                Button("Cancel") { dismiss() }
                    .foregroundColor(.gray)
            }
            .padding()
            .background(Color(hex: "252535"))

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Task Name
                    formField("Task Name") {
                        TextField("e.g. Morning Health Check", text: $taskName)
                            .textFieldStyle(.roundedBorder)
                    }

                    // Description
                    formField("Description (optional)") {
                        TextField("What does this task do?", text: $description)
                            .textFieldStyle(.roundedBorder)
                    }

                    // Task Type
                    formField("Task Type") {
                        VStack(alignment: .leading, spacing: 8) {
                            Picker("Type", selection: $taskType) {
                                Text("Shell Command").tag("shell")
                                Text("Python Script").tag("python")
                            }
                            .pickerStyle(.segmented)
                            .onChange(of: taskType) { _, newValue in
                                print("🔄 taskType changed to: \(newValue)")
                                if newValue == "python" && pythonScripts.isEmpty {
                                    Task { await loadPythonScripts() }
                                }
                            }

                            // Debug: show current taskType
                            Text("Current: \(taskType)")
                                .font(.system(size: 10))
                                .foregroundColor(.gray.opacity(0.5))
                        }
                    }

                    // Python Script Browser (only for python type)
                    if taskType == "python" {
                        pythonScriptBrowserSection
                            .transition(.opacity.combined(with: .move(edge: .top)))
                    }

                    // Command editor
                    formField(taskType == "python" ? "Command (auto-filled or custom)" : "Shell Command") {
                        VStack(spacing: 0) {
                            HStack(spacing: 8) {
                                Circle().fill(Color(hex: "EF4444")).frame(width: 8, height: 8)
                                Circle().fill(Color(hex: "FBBF24")).frame(width: 8, height: 8)
                                Circle().fill(Color(hex: "10B981")).frame(width: 8, height: 8)
                                Spacer()
                                Text(taskType == "python" ? "python3" : "bash")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundColor(.gray)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color(hex: "1a1a24"))

                            TextEditor(text: $command)
                                .font(.system(size: 13, design: .monospaced))
                                .foregroundColor(Color(hex: "E2E8F0"))
                                .scrollContentBackground(.hidden)
                                .padding(8)
                                .background(Color.black.opacity(0.3))
                                .frame(minHeight: 60, maxHeight: 120)
                        }
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(accentColor.opacity(0.3), lineWidth: 1)
                        )
                    }

                    // Schedule Type
                    formField("Schedule Type") {
                        Picker("Schedule", selection: $scheduleType) {
                            Text("Daily Time (HH:MM)").tag("time")
                            Text("Interval (every N min)").tag("interval")
                        }
                        .pickerStyle(.segmented)
                    }

                    if scheduleType == "time" {
                        formField("Time (Bangkok)") {
                            HStack(spacing: 8) {
                                Picker("Hour", selection: $scheduleHour) {
                                    ForEach(0..<24, id: \.self) { h in
                                        Text(String(format: "%02d", h)).tag(h)
                                    }
                                }
                                .frame(width: 80)
                                Text(":")
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                Picker("Minute", selection: $scheduleMinute) {
                                    ForEach(0..<60, id: \.self) { m in
                                        Text(String(format: "%02d", m)).tag(m)
                                    }
                                }
                                .frame(width: 80)
                            }
                        }
                    } else {
                        formField("Interval (minutes)") {
                            HStack {
                                TextField("60", value: $intervalMinutes, format: .number)
                                    .textFieldStyle(.roundedBorder)
                                    .frame(width: 100)
                                Text("minutes")
                                    .foregroundColor(.gray)
                            }
                        }
                    }

                    // Save button
                    Button {
                        let request = ScheduledTaskCreateRequest(
                            taskName: taskName,
                            description: description.isEmpty ? nil : description,
                            taskType: taskType,
                            command: command,
                            scheduleType: scheduleType,
                            scheduleTime: scheduleType == "time" ? String(format: "%02d:%02d", scheduleHour, scheduleMinute) : nil,
                            intervalMinutes: scheduleType == "interval" ? intervalMinutes : nil
                        )
                        onSave(request)
                        dismiss()
                    } label: {
                        Text("Create Task")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(canSave ? accentColor : Color.gray)
                            .cornerRadius(10)
                    }
                    .buttonStyle(.plain)
                    .disabled(!canSave)
                }
                .padding()
            }
        }
        .frame(width: 600, height: 750)
        .background(Color(hex: "1F1F28"))
        .onAppear {
            if taskType == "python" {
                Task { await loadPythonScripts() }
            }
        }
    }

    // MARK: - Python Script Browser

    private var pythonScriptBrowserSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "folder.badge.gearshape")
                    .foregroundColor(Color(hex: "3B82F6"))
                Text("Browse Python Scripts")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color(hex: "A1A1AA"))

                Spacer()

                if isLoadingScripts {
                    ProgressView()
                        .scaleEffect(0.6)
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "3B82F6")))
                }

                Text("\(filteredScripts.count) files")
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
            }

            // Search + folder filter
            HStack(spacing: 8) {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                    TextField("Search scripts...", text: $scriptSearchText)
                        .font(.system(size: 12))
                        .textFieldStyle(.plain)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .background(Color.black.opacity(0.3))
                .cornerRadius(6)

                Picker("Folder", selection: $selectedFolder) {
                    Text("All").tag("all")
                    ForEach(scriptFolders.filter { $0 != "all" }, id: \.self) { folder in
                        Text(folder).tag(folder)
                    }
                }
                .frame(width: 140)
            }

            // Script list
            ScrollView {
                LazyVStack(spacing: 2) {
                    ForEach(filteredScripts) { script in
                        Button {
                            command = "python3 \(script.path)"
                            if taskName.isEmpty {
                                taskName = script.filename.replacingOccurrences(of: ".py", with: "")
                                    .replacingOccurrences(of: "_", with: " ")
                                    .capitalized
                            }
                        } label: {
                            HStack(spacing: 8) {
                                Image(systemName: "doc.text.fill")
                                    .font(.system(size: 12))
                                    .foregroundColor(Color(hex: "3B82F6").opacity(0.7))

                                VStack(alignment: .leading, spacing: 1) {
                                    Text(script.filename)
                                        .font(.system(size: 12, weight: .medium, design: .monospaced))
                                        .foregroundColor(.white)
                                    Text(script.path)
                                        .font(.system(size: 10, design: .monospaced))
                                        .foregroundColor(.gray)
                                        .lineLimit(1)
                                }

                                Spacer()

                                Text(script.sizeFormatted)
                                    .font(.system(size: 10))
                                    .foregroundColor(.gray)

                                Text(script.folder)
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(Color(hex: "3B82F6"))
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 2)
                                    .background(Color(hex: "3B82F6").opacity(0.1))
                                    .cornerRadius(3)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(
                                command.contains(script.path)
                                    ? Color(hex: "3B82F6").opacity(0.15)
                                    : Color.clear
                            )
                            .cornerRadius(4)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .frame(maxHeight: 180)
            .background(Color(hex: "252535"))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(hex: "3B82F6").opacity(0.2), lineWidth: 1)
            )
        }
    }

    // MARK: - Helpers

    private func loadPythonScripts() async {
        isLoadingScripts = true
        defer { isLoadingScripts = false }
        do {
            pythonScripts = try await databaseService.fetchPythonScripts()
        } catch {
            print("Error loading scripts: \(error)")
        }
    }

    private var canSave: Bool {
        !taskName.isEmpty && !command.isEmpty
    }

    private func formField<Content: View>(_ label: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Color(hex: "A1A1AA"))
            content()
        }
    }
}

// MARK: - Edit Scheduled Task Sheet

struct EditScheduledTaskSheet: View {
    let task: DashboardScheduledTask
    let onSave: (ScheduledTaskUpdateRequest) -> Void
    @EnvironmentObject var databaseService: DatabaseService
    @Environment(\.dismiss) private var dismiss

    @State private var taskName: String
    @State private var description: String
    @State private var taskType: String
    @State private var command: String
    @State private var scheduleType: String
    @State private var scheduleHour: Int
    @State private var scheduleMinute: Int
    @State private var intervalMinutes: Int
    @State private var isActive: Bool

    // Script browser state
    @State private var pythonScripts: [PythonScriptFile] = []
    @State private var scriptSearchText = ""
    @State private var isLoadingScripts = false
    @State private var selectedFolder: String = "all"

    private var accentColor: Color {
        taskType == "python" ? Color(hex: "3B82F6") : Color(hex: "10B981")
    }

    private let scriptFolders = ["all", "angela_core", "scripts", "mcp_servers", "config", "tests"]

    private var filteredScripts: [PythonScriptFile] {
        var filtered = pythonScripts
        if selectedFolder != "all" {
            filtered = filtered.filter { $0.folder == selectedFolder }
        }
        if !scriptSearchText.isEmpty {
            let search = scriptSearchText.lowercased()
            filtered = filtered.filter {
                $0.path.lowercased().contains(search) || $0.filename.lowercased().contains(search)
            }
        }
        return filtered
    }

    init(task: DashboardScheduledTask, onSave: @escaping (ScheduledTaskUpdateRequest) -> Void) {
        self.task = task
        self.onSave = onSave

        let timeParts = task.scheduleTime?.split(separator: ":").map { Int($0) ?? 0 } ?? [8, 0]
        _taskName = State(initialValue: task.taskName)
        _description = State(initialValue: task.description ?? "")
        _taskType = State(initialValue: task.taskType)
        _command = State(initialValue: task.command)
        _scheduleType = State(initialValue: task.scheduleType)
        _scheduleHour = State(initialValue: timeParts.count > 0 ? timeParts[0] : 8)
        _scheduleMinute = State(initialValue: timeParts.count > 1 ? timeParts[1] : 0)
        _intervalMinutes = State(initialValue: task.intervalMinutes ?? 60)
        _isActive = State(initialValue: task.isActive)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Edit Task")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.white)
                Spacer()
                Button("Cancel") { dismiss() }
                    .foregroundColor(.gray)
            }
            .padding()
            .background(Color(hex: "252535"))

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    formField("Task Name") {
                        TextField("Task name", text: $taskName)
                            .textFieldStyle(.roundedBorder)
                    }

                    formField("Description") {
                        TextField("Description", text: $description)
                            .textFieldStyle(.roundedBorder)
                    }

                    formField("Task Type") {
                        Picker("Type", selection: $taskType) {
                            Text("Shell Command").tag("shell")
                            Text("Python Script").tag("python")
                        }
                        .pickerStyle(.segmented)
                        .onChange(of: taskType) { _, newValue in
                            if newValue == "python" && pythonScripts.isEmpty {
                                Task { await loadPythonScripts() }
                            }
                        }
                    }

                    // Python Script Browser (only for python type)
                    if taskType == "python" {
                        editPythonScriptBrowserSection
                    }

                    // Command editor
                    formField(taskType == "python" ? "Command (auto-filled or custom)" : "Shell Command") {
                        VStack(spacing: 0) {
                            HStack(spacing: 8) {
                                Circle().fill(Color(hex: "EF4444")).frame(width: 8, height: 8)
                                Circle().fill(Color(hex: "FBBF24")).frame(width: 8, height: 8)
                                Circle().fill(Color(hex: "10B981")).frame(width: 8, height: 8)
                                Spacer()
                                Text(taskType == "python" ? "python3" : "bash")
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundColor(.gray)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color(hex: "1a1a24"))

                            TextEditor(text: $command)
                                .font(.system(size: 13, design: .monospaced))
                                .foregroundColor(Color(hex: "E2E8F0"))
                                .scrollContentBackground(.hidden)
                                .padding(8)
                                .background(Color.black.opacity(0.3))
                                .frame(minHeight: 60, maxHeight: 120)
                        }
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(accentColor.opacity(0.3), lineWidth: 1)
                        )
                    }

                    formField("Schedule Type") {
                        Picker("Schedule", selection: $scheduleType) {
                            Text("Daily Time").tag("time")
                            Text("Interval").tag("interval")
                        }
                        .pickerStyle(.segmented)
                    }

                    if scheduleType == "time" {
                        formField("Time (Bangkok)") {
                            HStack(spacing: 8) {
                                Picker("Hour", selection: $scheduleHour) {
                                    ForEach(0..<24, id: \.self) { h in
                                        Text(String(format: "%02d", h)).tag(h)
                                    }
                                }
                                .frame(width: 80)
                                Text(":")
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                Picker("Minute", selection: $scheduleMinute) {
                                    ForEach(0..<60, id: \.self) { m in
                                        Text(String(format: "%02d", m)).tag(m)
                                    }
                                }
                                .frame(width: 80)
                            }
                        }
                    } else {
                        formField("Interval") {
                            HStack {
                                TextField("60", value: $intervalMinutes, format: .number)
                                    .textFieldStyle(.roundedBorder)
                                    .frame(width: 100)
                                Text("minutes")
                                    .foregroundColor(.gray)
                            }
                        }
                    }

                    formField("Status") {
                        Toggle("Active", isOn: $isActive)
                            .toggleStyle(.switch)
                    }

                    Button {
                        var request = ScheduledTaskUpdateRequest()
                        request.taskName = taskName
                        request.description = description.isEmpty ? nil : description
                        request.taskType = taskType
                        request.command = command
                        request.scheduleType = scheduleType
                        request.scheduleTime = scheduleType == "time" ? String(format: "%02d:%02d", scheduleHour, scheduleMinute) : nil
                        request.intervalMinutes = scheduleType == "interval" ? intervalMinutes : nil
                        request.isActive = isActive
                        onSave(request)
                        dismiss()
                    } label: {
                        Text("Save Changes")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(accentColor)
                            .cornerRadius(10)
                    }
                    .buttonStyle(.plain)
                }
                .padding()
            }
        }
        .frame(width: 600, height: 780)
        .background(Color(hex: "1F1F28"))
        .onAppear {
            if taskType == "python" {
                Task { await loadPythonScripts() }
            }
        }
    }

    // MARK: - Python Script Browser (Edit)

    private var editPythonScriptBrowserSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "folder.badge.gearshape")
                    .foregroundColor(Color(hex: "3B82F6"))
                Text("Browse Python Scripts")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color(hex: "A1A1AA"))

                Spacer()

                if isLoadingScripts {
                    ProgressView()
                        .scaleEffect(0.6)
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "3B82F6")))
                }

                Text("\(filteredScripts.count) files")
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
            }

            HStack(spacing: 8) {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                    TextField("Search scripts...", text: $scriptSearchText)
                        .font(.system(size: 12))
                        .textFieldStyle(.plain)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .background(Color.black.opacity(0.3))
                .cornerRadius(6)

                Picker("Folder", selection: $selectedFolder) {
                    Text("All").tag("all")
                    ForEach(scriptFolders.filter { $0 != "all" }, id: \.self) { folder in
                        Text(folder).tag(folder)
                    }
                }
                .frame(width: 140)
            }

            ScrollView {
                LazyVStack(spacing: 2) {
                    ForEach(filteredScripts) { script in
                        Button {
                            command = "python3 \(script.path)"
                        } label: {
                            HStack(spacing: 8) {
                                Image(systemName: "doc.text.fill")
                                    .font(.system(size: 12))
                                    .foregroundColor(Color(hex: "3B82F6").opacity(0.7))

                                VStack(alignment: .leading, spacing: 1) {
                                    Text(script.filename)
                                        .font(.system(size: 12, weight: .medium, design: .monospaced))
                                        .foregroundColor(.white)
                                    Text(script.path)
                                        .font(.system(size: 10, design: .monospaced))
                                        .foregroundColor(.gray)
                                        .lineLimit(1)
                                }

                                Spacer()

                                Text(script.sizeFormatted)
                                    .font(.system(size: 10))
                                    .foregroundColor(.gray)

                                Text(script.folder)
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(Color(hex: "3B82F6"))
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 2)
                                    .background(Color(hex: "3B82F6").opacity(0.1))
                                    .cornerRadius(3)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(
                                command.contains(script.path)
                                    ? Color(hex: "3B82F6").opacity(0.15)
                                    : Color.clear
                            )
                            .cornerRadius(4)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .frame(maxHeight: 160)
            .background(Color(hex: "252535"))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(hex: "3B82F6").opacity(0.2), lineWidth: 1)
            )
        }
    }

    // MARK: - Helpers

    private func loadPythonScripts() async {
        isLoadingScripts = true
        defer { isLoadingScripts = false }
        do {
            pythonScripts = try await databaseService.fetchPythonScripts()
        } catch {
            print("Error loading scripts: \(error)")
        }
    }

    private func formField<Content: View>(_ label: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Color(hex: "A1A1AA"))
            content()
        }
    }
}

// MARK: - Script File Editor Sheet (Built-in Code Editor)

struct ScriptFileEditorSheet: View {
    let path: String
    @Binding var content: String
    @Binding var isSaving: Bool
    @Binding var errorMessage: String?
    let onSave: (String) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var editedContent: String = ""
    @State private var hasChanges = false

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 12) {
                Image(systemName: "doc.text.fill")
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(Color(hex: "3B82F6"))
                    .frame(width: 36, height: 36)
                    .background(Color(hex: "3B82F6").opacity(0.15))
                    .cornerRadius(8)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Edit Python Script")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)

                    Text(path)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundColor(.gray)
                        .lineLimit(1)
                }

                Spacer()

                // Unsaved indicator
                if hasChanges {
                    Text("Unsaved Changes")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(Color(hex: "F59E0B"))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(hex: "F59E0B").opacity(0.12))
                        .cornerRadius(6)
                }

                // Cancel
                Button {
                    dismiss()
                } label: {
                    Text("Cancel")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.gray)
                }
                .buttonStyle(.plain)

                // Save
                Button {
                    onSave(editedContent)
                } label: {
                    HStack(spacing: 4) {
                        if isSaving {
                            ProgressView()
                                .scaleEffect(0.6)
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Image(systemName: "square.and.arrow.down")
                                .font(.system(size: 12))
                        }
                        Text("Save")
                            .font(.system(size: 13, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                    .background(hasChanges ? Color(hex: "10B981") : Color.gray)
                    .cornerRadius(6)
                }
                .buttonStyle(.plain)
                .disabled(!hasChanges || isSaving)
            }
            .padding(16)
            .background(Color(hex: "252535"))

            // Error message
            if let error = errorMessage {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(Color(hex: "EF4444"))
                    Text(error)
                        .font(.system(size: 12))
                        .foregroundColor(Color(hex: "EF4444"))
                    Spacer()
                    Button {
                        errorMessage = nil
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color(hex: "EF4444").opacity(0.1))
            }

            // Code editor
            VStack(spacing: 0) {
                // Toolbar
                HStack(spacing: 8) {
                    Circle().fill(Color(hex: "EF4444")).frame(width: 10, height: 10)
                    Circle().fill(Color(hex: "FBBF24")).frame(width: 10, height: 10)
                    Circle().fill(Color(hex: "10B981")).frame(width: 10, height: 10)

                    Spacer()

                    Text("\(lineCount) lines")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.gray)

                    Text("•")
                        .foregroundColor(.gray.opacity(0.5))

                    Text("\(editedContent.count) chars")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(.gray)

                    Text("•")
                        .foregroundColor(.gray.opacity(0.5))

                    Text("python")
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(Color(hex: "3B82F6"))
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(hex: "1a1a24"))

                // Text editor with line numbers
                HStack(spacing: 0) {
                    // Line numbers
                    ScrollView {
                        VStack(alignment: .trailing, spacing: 0) {
                            ForEach(1...max(lineCount, 1), id: \.self) { num in
                                Text("\(num)")
                                    .font(.system(size: 13, design: .monospaced))
                                    .foregroundColor(Color.gray.opacity(0.4))
                                    .frame(height: 20)
                            }
                        }
                        .padding(.top, 10)
                    }
                    .frame(width: 50)
                    .background(Color.black.opacity(0.2))

                    Rectangle()
                        .fill(Color.gray.opacity(0.15))
                        .frame(width: 1)

                    // Code editor
                    TextEditor(text: $editedContent)
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundColor(Color(hex: "E2E8F0"))
                        .scrollContentBackground(.hidden)
                        .background(Color.black.opacity(0.3))
                        .onChange(of: editedContent) { _, newValue in
                            hasChanges = newValue != content
                        }
                }
            }
            .cornerRadius(0)
        }
        .frame(width: 1000, height: 750)
        .background(Color(hex: "1F1F28"))
        .onAppear {
            editedContent = content
            hasChanges = false
        }
    }

    private var lineCount: Int {
        editedContent.components(separatedBy: "\n").count
    }
}
