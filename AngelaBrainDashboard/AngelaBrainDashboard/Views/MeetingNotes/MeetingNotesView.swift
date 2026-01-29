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

                // Raw notes from Things3 (original format)
                if let rawNotes = meeting.rawNotes, !rawNotes.isEmpty {
                    RawNotesView(text: rawNotes)
                } else {
                    // Fallback to parsed sections
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

                    if let points = meeting.keyPoints, !points.isEmpty {
                        sectionView(icon: "pin.fill", title: "Key Points", color: "3B82F6") {
                            VStack(alignment: .leading, spacing: 4) {
                                ForEach(points, id: \.self) { point in
                                    HStack(alignment: .top, spacing: 6) {
                                        Text("\u{2022}")
                                            .foregroundColor(Color(hex: "3B82F6"))
                                        Text(point)
                                            .font(AngelaTheme.caption())
                                            .foregroundColor(AngelaTheme.textPrimary)
                                    }
                                }
                            }
                        }
                    }

                    if let notes = meeting.personalNotes, !notes.isEmpty {
                        sectionView(icon: "lightbulb.fill", title: "Personal Notes", color: "F59E0B") {
                            Text(notes)
                                .font(AngelaTheme.caption())
                                .foregroundColor(AngelaTheme.textSecondary)
                                .italic()
                        }
                    }
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

                // Edit / Delete buttons
                if onEdit != nil || onDelete != nil {
                    Divider()
                        .background(AngelaTheme.textTertiary.opacity(0.3))
                        .padding(.top, 4)

                    HStack(spacing: 12) {
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
