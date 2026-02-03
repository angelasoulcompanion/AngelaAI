//
//  MeetingComponents.swift
//  Angela Brain Dashboard
//
//  Shared components for meeting display (used by ThingsOverviewView)
//

import SwiftUI

// MARK: - Meeting Card Component

struct MeetingCard: View {
    let meeting: MeetingNote
    let isExpanded: Bool
    let onTap: () -> Void
    var onEdit: (() -> Void)? = nil
    var onDelete: (() -> Void)? = nil
    var onToggleStatus: (() -> Void)? = nil
    var databaseService: DatabaseService? = nil
    var onActionChanged: (() -> Void)? = nil

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

                // Prefer structured data; fall back to raw markdown
                if meetingHasStructuredData {
                    StructuredNotesDisplay(meeting: meeting)
                } else if let rawNotes = meeting.rawNotes, !rawNotes.isEmpty {
                    RawNotesView(text: rawNotes)
                }

                // Action Items Section (interactive CRUD)
                if let db = databaseService {
                    ActionItemsSection(
                        meetingId: meeting.id.uuidString,
                        databaseService: db,
                        onActionChanged: onActionChanged
                    )
                }

                // Project info (always shown)
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

                // Action buttons
                if onEdit != nil || onDelete != nil || onToggleStatus != nil {
                    Divider()
                        .background(AngelaTheme.textTertiary.opacity(0.3))
                        .padding(.top, 4)

                    HStack(spacing: 12) {
                        if let onToggleStatus {
                            Button {
                                onToggleStatus()
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: meeting.isOpen ? "checkmark.circle" : "arrow.uturn.backward")
                                        .font(.system(size: 11))
                                    Text(meeting.isOpen ? "Complete" : "Reopen")
                                        .font(.system(size: 11, weight: .medium))
                                }
                                .foregroundColor(Color(hex: meeting.isOpen ? "10B981" : "3B82F6"))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background(Color(hex: meeting.isOpen ? "10B981" : "3B82F6").opacity(0.12))
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                        }

                        if let onEdit {
                            Button {
                                onEdit()
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "pencil")
                                        .font(.system(size: 11))
                                    Text("Edit")
                                        .font(.system(size: 11, weight: .medium))
                                }
                                .foregroundColor(Color(hex: "3B82F6"))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background(Color(hex: "3B82F6").opacity(0.12))
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                        }

                        if let onDelete {
                            Button {
                                onDelete()
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "trash")
                                        .font(.system(size: 11))
                                    Text("Delete")
                                        .font(.system(size: 11, weight: .medium))
                                }
                                .foregroundColor(Color(hex: "EF4444"))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background(Color(hex: "EF4444").opacity(0.12))
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                        }

                        Spacer()
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

    private var meetingHasStructuredData: Bool {
        !(meeting.agenda?.isEmpty ?? true)
            || !(meeting.keyPoints?.isEmpty ?? true)
            || !(meeting.decisionsMade?.isEmpty ?? true)
            || !(meeting.nextSteps?.isEmpty ?? true)
            || !(meeting.personalNotes?.isEmpty ?? true)
            || !(meeting.morningNotes?.isEmpty ?? true)
            || !(meeting.afternoonNotes?.isEmpty ?? true)
            || !(meeting.siteObservations?.isEmpty ?? true)
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

// MARK: - Structured Notes Display

struct StructuredNotesDisplay: View {
    let meeting: MeetingNote

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Attendees
            if let attendees = meeting.attendees, !attendees.isEmpty {
                notesSection(icon: "person.2.fill", title: "Attendees", color: "8B5CF6") {
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

            // Sections vary by meeting type
            if meeting.isSiteVisit {
                siteVisitSections
            } else {
                standardSections
            }
        }
    }

    // MARK: - Standard / Testing / BOD sections

    @ViewBuilder
    private var standardSections: some View {
        if let items = meeting.agenda, !items.isEmpty {
            notesSection(icon: "list.clipboard.fill", title: "Agenda", color: "3B82F6") {
                BulletItemsDisplay(items: items, color: "3B82F6")
            }
        }
        if let items = meeting.keyPoints, !items.isEmpty {
            notesSection(icon: "key.fill", title: "Key Points", color: "8B5CF6") {
                BulletItemsDisplay(items: items, color: "8B5CF6")
            }
        }
        if let items = meeting.decisionsMade, !items.isEmpty {
            notesSection(icon: "checkmark.seal.fill", title: "Decisions Made", color: "10B981") {
                BulletItemsDisplay(items: items, color: "10B981")
            }
        }
        if let items = meeting.issuesRisks, !items.isEmpty {
            notesSection(icon: "exclamationmark.triangle.fill", title: "Issues / Risks", color: "EF4444") {
                BulletItemsDisplay(items: items, color: "EF4444")
            }
        }
        if let items = meeting.nextSteps, !items.isEmpty {
            notesSection(icon: "arrow.right.circle.fill", title: "Next Steps", color: "F59E0B") {
                BulletItemsDisplay(items: items, color: "F59E0B")
            }
        }
        if let notes = meeting.personalNotes, !notes.isEmpty {
            notesSection(icon: "note.text", title: "Personal Notes", color: "6B7280") {
                Text(notes)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .italic()
            }
        }
    }

    // MARK: - Site Visit sections

    @ViewBuilder
    private var siteVisitSections: some View {
        if let notes = meeting.morningNotes, !notes.isEmpty {
            notesSection(icon: "sunrise.fill", title: "Morning Notes", color: "F59E0B") {
                Text(notes)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textPrimary)
            }
        }
        if let notes = meeting.afternoonNotes, !notes.isEmpty {
            notesSection(icon: "sunset.fill", title: "Afternoon Notes", color: "3B82F6") {
                Text(notes)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textPrimary)
            }
        }
        if let notes = meeting.siteObservations, !notes.isEmpty {
            notesSection(icon: "eye.fill", title: "Site Observations", color: "10B981") {
                Text(notes)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textPrimary)
            }
        }
        if let items = meeting.keyPoints, !items.isEmpty {
            notesSection(icon: "key.fill", title: "Key Points", color: "8B5CF6") {
                BulletItemsDisplay(items: items, color: "8B5CF6")
            }
        }
        if let items = meeting.nextSteps, !items.isEmpty {
            notesSection(icon: "arrow.right.circle.fill", title: "Next Steps", color: "F59E0B") {
                BulletItemsDisplay(items: items, color: "F59E0B")
            }
        }
    }

    // MARK: - Section wrapper

    @ViewBuilder
    private func notesSection<Content: View>(icon: String, title: String, color: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 11))
                    .foregroundColor(Color(hex: color))
                Text(title)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: color))
            }

            content()
                .padding(.leading, 4)
        }
    }
}

// MARK: - Bullet Items Display (read-only, with indent support)

struct BulletItemsDisplay: View {
    let items: [String]
    let color: String

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                let level = indentLevel(of: item)
                let text = displayText(of: item)

                HStack(alignment: .top, spacing: 6) {
                    if level > 0 {
                        Color.clear.frame(width: CGFloat(level) * 14)
                    }

                    // Bullet style per level
                    if level == 0 {
                        Text("\u{2022}")
                            .font(.system(size: 12))
                            .foregroundColor(Color(hex: color))
                    } else if level == 1 {
                        Text("\u{25E6}")  // ◦ hollow bullet
                            .font(.system(size: 10))
                            .foregroundColor(Color(hex: color).opacity(0.7))
                    } else {
                        Text("\u{2013}")  // – dash
                            .font(.system(size: 10))
                            .foregroundColor(Color(hex: color).opacity(0.5))
                    }

                    Text(text)
                        .font(.system(size: level == 0 ? 12 : 11))
                        .foregroundColor(level == 0 ? AngelaTheme.textPrimary : AngelaTheme.textSecondary)
                }
            }
        }
    }

    private func indentLevel(of item: String) -> Int {
        min(item.prefix(while: { $0 == " " }).count / 2, 3)
    }

    private func displayText(of item: String) -> String {
        String(item.drop(while: { $0 == " " }))
    }
}

// MARK: - Raw Notes View (Things3 original format)

struct RawNotesView: View {
    let text: String

    // Section header emojis from Things3 template
    private static let sectionEmojis: Set<Character> = [
        "\u{1F4CD}", // 📍
        "\u{1F4C5}", // 📅
        "\u{1F558}", "\u{1F550}", "\u{1F557}", "\u{1F559}", "\u{1F55B}", // 🕘🕐🕗🕙🕛
        "\u{1F465}", // 👥
        "\u{1F4CB}", // 📋
        "\u{1F4CC}", // 📌
        "\u{2705}",  // ✅
        "\u{1F4CA}", // 📊
        "\u{26A0}",  // ⚠️
        "\u{1F4A1}", // 💡
        "\u{1F539}", // 🔹
        "\u{1F440}", // 👀
    ]

    private func isSectionHeader(_ line: String) -> Bool {
        let trimmed = line.trimmingCharacters(in: .whitespaces)
        guard let first = trimmed.unicodeScalars.first else { return false }
        return RawNotesView.sectionEmojis.contains(Character(first))
    }

    private func isBulletLine(_ line: String) -> Bool {
        let trimmed = line.trimmingCharacters(in: .whitespaces)
        return trimmed.hasPrefix("- ") || trimmed.hasPrefix("• ")
    }

    private func isCheckboxLine(_ line: String) -> Bool {
        let trimmed = line.trimmingCharacters(in: .whitespaces)
        return trimmed.hasPrefix("- [ ]") || trimmed.hasPrefix("- [x]") || trimmed.hasPrefix("- [X]")
    }

    private func isDividerLine(_ line: String) -> Bool {
        let trimmed = line.trimmingCharacters(in: .whitespaces)
        return trimmed.allSatisfy({ $0 == "-" || $0 == "—" || $0 == "─" }) && trimmed.count >= 3
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(Array(text.components(separatedBy: "\n").enumerated()), id: \.offset) { _, line in
                let trimmed = line.trimmingCharacters(in: .whitespaces)

                if trimmed.isEmpty {
                    Spacer().frame(height: 4)
                } else if isDividerLine(trimmed) {
                    Divider()
                        .background(AngelaTheme.textTertiary.opacity(0.3))
                        .padding(.vertical, 2)
                } else if isSectionHeader(trimmed) {
                    Text(trimmed)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color(hex: "9333EA"))
                        .padding(.top, 6)
                } else if isCheckboxLine(trimmed) {
                    let isChecked = trimmed.contains("[x]") || trimmed.contains("[X]")
                    let content = trimmed
                        .replacingOccurrences(of: "- [x] ", with: "")
                        .replacingOccurrences(of: "- [X] ", with: "")
                        .replacingOccurrences(of: "- [ ] ", with: "")
                    HStack(alignment: .top, spacing: 6) {
                        Image(systemName: isChecked ? "checkmark.circle.fill" : "circle")
                            .font(.system(size: 12))
                            .foregroundColor(isChecked ? Color(hex: "10B981") : AngelaTheme.textTertiary)
                        Text(content)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textPrimary)
                            .strikethrough(isChecked)
                    }
                    .padding(.leading, 8)
                } else if isBulletLine(trimmed) {
                    let content = String(trimmed.dropFirst(2))
                    HStack(alignment: .top, spacing: 6) {
                        Text("\u{2022}")
                            .font(.system(size: 12))
                            .foregroundColor(Color(hex: "3B82F6"))
                        Text(content)
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textPrimary)
                    }
                    .padding(.leading, 8)
                } else {
                    Text(trimmed)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textPrimary)
                        .padding(.leading, 4)
                }
            }
        }
    }
}

// MARK: - Action Item Row Component (Interactive)

struct ActionItemRow: View {
    let action: MeetingActionItem
    var onToggle: (() -> Void)? = nil
    var onEdit: (() -> Void)? = nil
    var onDelete: (() -> Void)? = nil
    var showMeetingTitle: Bool = true

    var body: some View {
        HStack(spacing: 10) {
            // Tappable toggle circle
            Button {
                onToggle?()
            } label: {
                Image(systemName: action.statusIcon)
                    .font(.system(size: 16))
                    .foregroundColor(Color(hex: action.statusColor))
            }
            .buttonStyle(.plain)
            .disabled(onToggle == nil)

            VStack(alignment: .leading, spacing: 2) {
                // Tappable text for edit
                Group {
                    if onEdit != nil {
                        Text(action.actionText)
                            .onTapGesture { onEdit?() }
                    } else {
                        Text(action.actionText)
                    }
                }
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .strikethrough(action.isCompleted)

                HStack(spacing: 6) {
                    if showMeetingTitle, let title = action.meetingTitle {
                        Text(title)
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                            .lineLimit(1)
                    }

                    if let assignee = action.assignee, !assignee.isEmpty {
                        HStack(spacing: 2) {
                            Image(systemName: "person.fill")
                                .font(.system(size: 8))
                            Text(assignee)
                        }
                        .font(.system(size: 10))
                        .foregroundColor(Color(hex: "8B5CF6"))
                    }

                    if let dueDate = action.dueDate {
                        HStack(spacing: 2) {
                            Image(systemName: "calendar")
                                .font(.system(size: 8))
                            Text(dueDateFormatted(dueDate))
                        }
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textTertiary)
                    }
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

            // Delete button
            if onDelete != nil {
                Button {
                    onDelete?()
                } label: {
                    Image(systemName: "trash")
                        .font(.system(size: 11))
                        .foregroundColor(Color(hex: "EF4444").opacity(0.6))
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 10)
        .background(AngelaTheme.backgroundLight.opacity(0.5))
        .cornerRadius(AngelaTheme.smallCornerRadius)
    }

    private func dueDateFormatted(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "d MMM"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter.string(from: date)
    }
}

// MARK: - Action Items Section (CRUD inside MeetingCard)

struct ActionItemsSection: View {
    let meetingId: String
    let databaseService: DatabaseService
    var onActionChanged: (() -> Void)? = nil

    @State private var actionItems: [MeetingActionItem] = []
    @State private var newActionText: String = ""
    @State private var isLoading = false
    @State private var editingItem: MeetingActionItem?

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack(spacing: 6) {
                Image(systemName: "checklist")
                    .font(.system(size: 12))
                    .foregroundColor(Color(hex: "F59E0B"))
                Text("Action Items")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: "F59E0B"))

                if !actionItems.isEmpty {
                    let completed = actionItems.filter(\.isCompleted).count
                    Text("\(completed)/\(actionItems.count)")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(Color(hex: "F59E0B"))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color(hex: "F59E0B").opacity(0.15))
                        .cornerRadius(4)
                }

                Spacer()

                if isLoading {
                    ProgressView()
                        .scaleEffect(0.5)
                }
            }

            // Action item list
            ForEach(actionItems) { item in
                ActionItemRow(
                    action: item,
                    onToggle: {
                        Task { await toggleItem(item) }
                    },
                    onEdit: {
                        editingItem = item
                    },
                    onDelete: {
                        Task { await deleteItem(item) }
                    },
                    showMeetingTitle: false
                )
            }

            // Inline add field
            HStack(spacing: 8) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "F59E0B").opacity(0.6))

                TextField("Add action item...", text: $newActionText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 12))
                    .onSubmit {
                        Task { await addItem() }
                    }

                if !newActionText.isEmpty {
                    Button {
                        Task { await addItem() }
                    } label: {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(Color(hex: "F59E0B"))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.vertical, 6)
            .padding(.horizontal, 10)
            .background(AngelaTheme.backgroundLight.opacity(0.3))
            .cornerRadius(AngelaTheme.smallCornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.smallCornerRadius)
                    .stroke(Color(hex: "F59E0B").opacity(0.2), lineWidth: 1)
            )
        }
        .padding(.leading, 4)
        .task { await loadItems() }
        .sheet(item: $editingItem) { item in
            EditActionItemSheet(
                databaseService: databaseService,
                actionItem: item
            ) {
                Task {
                    await loadItems()
                    onActionChanged?()
                }
            }
        }
    }

    // MARK: - Actions

    private func loadItems() async {
        isLoading = true
        actionItems = (try? await databaseService.fetchMeetingActionItems(meetingId: meetingId)) ?? []
        isLoading = false
    }

    private func addItem() async {
        let text = newActionText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }

        let request = ActionItemCreateRequest(
            meetingId: meetingId,
            actionText: text
        )
        _ = try? await databaseService.createActionItem(request)
        newActionText = ""
        await loadItems()
        onActionChanged?()
    }

    private func toggleItem(_ item: MeetingActionItem) async {
        _ = try? await databaseService.toggleActionItem(actionId: item.id.uuidString)
        await loadItems()
        onActionChanged?()
    }

    private func deleteItem(_ item: MeetingActionItem) async {
        _ = try? await databaseService.deleteActionItem(actionId: item.id.uuidString)
        await loadItems()
        onActionChanged?()
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
