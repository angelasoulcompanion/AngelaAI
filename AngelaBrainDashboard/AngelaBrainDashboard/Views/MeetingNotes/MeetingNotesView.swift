//
//  MeetingNotesView.swift
//  Angela Brain Dashboard
//
//  Meeting Notes Tracker - Synced from Things3
//

import SwiftUI
import Combine

struct MeetingNotesView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = MeetingNotesViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.largeSpacing) {
                // Header
                header

                // Stats Row
                if let stats = viewModel.stats {
                    statsRow(stats)
                }

                // Open Action Items
                if !viewModel.openActions.isEmpty {
                    actionItemsCard
                }

                // Meetings List
                meetingsCard
            }
            .padding(AngelaTheme.largeSpacing)
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Meeting Notes")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Synced from Things3")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 28))
                .foregroundColor(AngelaTheme.primaryPurple)
        }
    }

    // MARK: - Stats Row

    private func statsRow(_ stats: MeetingStats) -> some View {
        HStack(spacing: AngelaTheme.spacing) {
            statCard(title: "Total", value: "\(stats.totalMeetings)", icon: "doc.text.fill", color: "3B82F6")
            statCard(title: "This Month", value: "\(stats.thisMonth)", icon: "calendar", color: "9333EA")
            statCard(title: "Open Actions", value: "\(stats.openActions)", icon: "exclamationmark.circle.fill", color: "F59E0B")
            statCard(title: "Completion", value: "\(Int(stats.completionRate))%", icon: "checkmark.circle.fill", color: "10B981")
        }
    }

    private func statCard(title: String, value: String, icon: String, color: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 22))
                .foregroundColor(Color(hex: color))

            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Action Items Card

    private var actionItemsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Image(systemName: "exclamationmark.circle.fill")
                    .foregroundColor(Color(hex: "F59E0B"))

                Text("Open Action Items")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(viewModel.openActions.count)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(Color(hex: "F59E0B"))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(hex: "F59E0B").opacity(0.15))
                    .cornerRadius(6)
            }

            VStack(spacing: AngelaTheme.smallSpacing) {
                ForEach(viewModel.openActions.prefix(10)) { action in
                    ActionItemRow(action: action)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }

    // MARK: - Meetings Card

    private var meetingsCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
            HStack {
                Text("All Meetings")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text("\(viewModel.meetings.count) meetings")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            if viewModel.meetings.isEmpty {
                EmptyStateView(
                    message: "No meeting notes synced yet",
                    icon: "doc.text.magnifyingglass"
                )
            } else {
                VStack(spacing: AngelaTheme.spacing) {
                    ForEach(viewModel.meetings) { meeting in
                        MeetingCard(meeting: meeting, isExpanded: viewModel.expandedMeetingId == meeting.id) {
                            withAnimation(.easeInOut(duration: 0.2)) {
                                if viewModel.expandedMeetingId == meeting.id {
                                    viewModel.expandedMeetingId = nil
                                } else {
                                    viewModel.expandedMeetingId = meeting.id
                                }
                            }
                        }
                    }
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .angelaCard()
    }
}

// MARK: - Meeting Card Component

struct MeetingCard: View {
    let meeting: MeetingNote
    let isExpanded: Bool
    let onTap: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header row
            HStack(spacing: 12) {
                // Type icon
                ZStack {
                    Circle()
                        .fill(Color(hex: meeting.typeColor).opacity(0.2))
                        .frame(width: 40, height: 40)

                    Image(systemName: meeting.typeIcon)
                        .font(.system(size: 16))
                        .foregroundColor(Color(hex: meeting.typeColor))
                }

                // Title & meta
                VStack(alignment: .leading, spacing: 4) {
                    Text(meeting.title)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .lineLimit(isExpanded ? nil : 2)

                    HStack(spacing: 8) {
                        if let _ = meeting.meetingDate {
                            Text(meeting.dateFormatted)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)
                        }

                        if let location = meeting.location, !location.isEmpty {
                            HStack(spacing: 2) {
                                Image(systemName: "mappin")
                                    .font(.system(size: 9))
                                Text(location)
                                    .lineLimit(1)
                            }
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                        }

                        if let time = meeting.timeRange, !time.isEmpty {
                            HStack(spacing: 2) {
                                Image(systemName: "clock")
                                    .font(.system(size: 9))
                                Text(time)
                            }
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)
                        }
                    }
                }

                Spacer()

                // Status + actions count
                VStack(alignment: .trailing, spacing: 4) {
                    if meeting.isOpen {
                        Text("Open")
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(Color(hex: "3B82F6"))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color(hex: "3B82F6").opacity(0.15))
                            .cornerRadius(4)
                    } else {
                        Text("Done")
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(Color(hex: "10B981"))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color(hex: "10B981").opacity(0.15))
                            .cornerRadius(4)
                    }

                    if let total = meeting.totalActions, total > 0 {
                        let completed = meeting.completedActions ?? 0
                        Text("\(completed)/\(total) actions")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }

                Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
            .contentShape(Rectangle())
            .onTapGesture { onTap() }

            // Expanded content
            if isExpanded {
                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // Attendees
                if let attendees = meeting.attendees, !attendees.isEmpty {
                    sectionView(icon: "person.2.fill", title: "Attendees", color: "8B5CF6") {
                        FlowLayout(spacing: 6) {
                            ForEach(attendees, id: \.self) { name in
                                Text(name)
                                    .font(.system(size: 11))
                                    .foregroundColor(Color(hex: "8B5CF6"))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color(hex: "8B5CF6").opacity(0.12))
                                    .cornerRadius(6)
                            }
                        }
                    }
                }

                // Key Points
                if let points = meeting.keyPoints, !points.isEmpty {
                    sectionView(icon: "pin.fill", title: "Key Points", color: "3B82F6") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(points, id: \.self) { point in
                                HStack(alignment: .top, spacing: 6) {
                                    Text("•")
                                        .foregroundColor(Color(hex: "3B82F6"))
                                    Text(point)
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textPrimary)
                                }
                            }
                        }
                    }
                }

                // Decisions
                if let decisions = meeting.decisionsMade, !decisions.isEmpty {
                    sectionView(icon: "checkmark.seal.fill", title: "Decisions", color: "10B981") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(decisions, id: \.self) { decision in
                                HStack(alignment: .top, spacing: 6) {
                                    Text("✓")
                                        .foregroundColor(Color(hex: "10B981"))
                                    Text(decision)
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textPrimary)
                                }
                            }
                        }
                    }
                }

                // Issues/Risks
                if let issues = meeting.issuesRisks, !issues.isEmpty {
                    sectionView(icon: "exclamationmark.triangle.fill", title: "Issues / Risks", color: "EF4444") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(issues, id: \.self) { issue in
                                HStack(alignment: .top, spacing: 6) {
                                    Text("!")
                                        .font(.system(size: 12, weight: .bold))
                                        .foregroundColor(Color(hex: "EF4444"))
                                    Text(issue)
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textPrimary)
                                }
                            }
                        }
                    }
                }

                // Next Steps
                if let nextSteps = meeting.nextSteps, !nextSteps.isEmpty {
                    sectionView(icon: "arrow.right.circle.fill", title: "Next Steps", color: "9333EA") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(nextSteps, id: \.self) { step in
                                HStack(alignment: .top, spacing: 6) {
                                    Text("→")
                                        .foregroundColor(Color(hex: "9333EA"))
                                    Text(step)
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(AngelaTheme.textPrimary)
                                }
                            }
                        }
                    }
                }

                // Personal Notes
                if let notes = meeting.personalNotes, !notes.isEmpty {
                    sectionView(icon: "lightbulb.fill", title: "Personal Notes", color: "F59E0B") {
                        Text(notes)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                            .italic()
                    }
                }

                // Site Visit specific sections
                if meeting.isSiteVisit {
                    if let morning = meeting.morningNotes, !morning.isEmpty {
                        sectionView(icon: "sun.max.fill", title: "Morning", color: "F59E0B") {
                            Text(morning)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textPrimary)
                        }
                    }

                    if let afternoon = meeting.afternoonNotes, !afternoon.isEmpty {
                        sectionView(icon: "sun.haze.fill", title: "Afternoon", color: "F97316") {
                            Text(afternoon)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textPrimary)
                        }
                    }

                    if let observations = meeting.siteObservations, !observations.isEmpty {
                        sectionView(icon: "eye.fill", title: "Observations", color: "6366F1") {
                            Text(observations)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textPrimary)
                        }
                    }
                }

                // Project info
                if let project = meeting.projectName, !project.isEmpty {
                    HStack {
                        Image(systemName: "folder.fill")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                        Text("Project: \(project)")
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .padding(.top, 4)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(
            LinearGradient(
                colors: [Color(hex: meeting.typeColor).opacity(0.03), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(Color(hex: meeting.typeColor).opacity(isExpanded ? 0.3 : 0.1), lineWidth: 1)
        )
    }

    @ViewBuilder
    private func sectionView<Content: View>(icon: String, title: String, color: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                    .foregroundColor(Color(hex: color))
                Text(title)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: color))
            }

            content()
        }
        .padding(.leading, 4)
    }
}

// MARK: - Action Item Row Component

struct ActionItemRow: View {
    let action: MeetingActionItem

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: action.statusIcon)
                .font(.system(size: 16))
                .foregroundColor(Color(hex: action.statusColor))

            VStack(alignment: .leading, spacing: 2) {
                Text(action.actionText)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)
                    .strikethrough(action.isCompleted)

                if let title = action.meetingTitle {
                    Text(title)
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                        .lineLimit(1)
                }
            }

            Spacer()

            // Priority badge
            Text(action.priorityLabel)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(Color(hex: action.priorityColor))
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color(hex: action.priorityColor).opacity(0.12))
                .cornerRadius(4)
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 10)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }
}

// MARK: - Flow Layout (for attendees tags)

struct FlowLayout: Layout {
    var spacing: CGFloat = 6

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = layout(proposal: proposal, subviews: subviews)
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = layout(proposal: proposal, subviews: subviews)
        for (index, position) in result.positions.enumerated() {
            subviews[index].place(at: CGPoint(x: bounds.minX + position.x, y: bounds.minY + position.y), proposal: .unspecified)
        }
    }

    private func layout(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        let maxWidth = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > maxWidth && x > 0 {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            positions.append(CGPoint(x: x, y: y))
            rowHeight = max(rowHeight, size.height)
            x += size.width + spacing
        }

        return (CGSize(width: maxWidth, height: y + rowHeight), positions)
    }
}

// MARK: - View Model

@MainActor
class MeetingNotesViewModel: ObservableObject {
    @Published var meetings: [MeetingNote] = []
    @Published var openActions: [MeetingActionItem] = []
    @Published var stats: MeetingStats?
    @Published var expandedMeetingId: UUID?
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        // Load stats, meetings, and actions in parallel
        async let fetchedStats = try? databaseService.fetchMeetingStats()
        async let fetchedMeetings = try? databaseService.fetchMeetings()
        async let fetchedActions = try? databaseService.fetchOpenActionItems()

        stats = await fetchedStats
        meetings = await fetchedMeetings ?? []
        openActions = await fetchedActions ?? []

        isLoading = false
    }
}
