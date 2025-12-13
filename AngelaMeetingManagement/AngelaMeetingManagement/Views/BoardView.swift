//
//  BoardView.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜
//  ClickUp-inspired Board View with Purple Theme
//

import SwiftUI
import UniformTypeIdentifiers

struct BoardView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @ObservedObject var viewModel: MeetingListViewModel
    @Binding var selectedMeeting: Meeting?

    // Filters
    let searchText: String
    let selectedPriorities: Set<String>
    let selectedStatuses: Set<String>
    let dateRange: DateRange?

    // Drag & Drop state
    @State private var draggingMeeting: Meeting?
    @State private var draggedOverColumn: String?

    // Board columns - mapped from Meeting status
    let columns: [(title: String, status: String)] = [
        ("SCHEDULED", "scheduled"),
        ("IN PROGRESS", "in_progress"),
        ("COMPLETED", "completed"),
        ("CANCELLED", "cancelled")
    ]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: AngelaTheme.spacingL) {
                ForEach(columns, id: \.title) { column in
                    BoardColumn(
                        title: column.title,
                        status: column.status,
                        meetings: filteredMeetings(for: column.status),
                        selectedMeeting: $selectedMeeting,
                        viewModel: viewModel,
                        draggingMeeting: $draggingMeeting,
                        draggedOverColumn: $draggedOverColumn,
                        onDrop: { meeting in
                            updateMeetingStatus(meeting: meeting, newStatus: column.status)
                        }
                    )
                }
            }
            .padding(AngelaTheme.spacingXL)
        }
        .background(AngelaTheme.background)
    }

    private func filteredMeetings(for status: String) -> [Meeting] {
        viewModel.meetings.filter { meeting in
            // Status filter (by column)
            guard meeting.status.rawValue == status else { return false }

            // Search filter
            if !searchText.isEmpty {
                let searchLower = searchText.lowercased()
                let matchesTitle = meeting.title.lowercased().contains(searchLower)
                let matchesDescription = (meeting.description ?? "").lowercased().contains(searchLower)
                guard matchesTitle || matchesDescription else { return false }
            }

            // Priority filter
            if !selectedPriorities.isEmpty {
                guard selectedPriorities.contains(meeting.priority ?? "Normal") else { return false }
            }

            // Status filter (from filter bar)
            if !selectedStatuses.isEmpty {
                guard selectedStatuses.contains(meeting.status.rawValue) else { return false }
            }

            // Date range filter
            if let range = dateRange {
                guard range.contains(meeting.meetingDate) else { return false }
            }

            return true
        }
    }

    private func updateMeetingStatus(meeting: Meeting, newStatus: String) {
        Task {
            // Update in database
            await viewModel.updateMeetingStatus(meetingId: meeting.id, newStatus: newStatus)
            // Reload meetings
            await viewModel.loadMeetings()
        }
    }
}

// MARK: - Board Column
struct BoardColumn: View {
    let title: String
    let status: String
    let meetings: [Meeting]
    @Binding var selectedMeeting: Meeting?
    @ObservedObject var viewModel: MeetingListViewModel
    @Binding var draggingMeeting: Meeting?
    @Binding var draggedOverColumn: String?
    let onDrop: (Meeting) -> Void

    @State private var isDropTarget = false

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            // Column Header
            HStack {
                Image(systemName: AngelaTheme.statusIcon(for: title))
                    .foregroundColor(AngelaTheme.statusColor(for: title))
                    .font(.system(size: 16, weight: .semibold))

                Text(title)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .textCase(.uppercase)

                Spacer()

                // Count badge
                Text("\(meetings.count)")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
                    .frame(minWidth: 24, minHeight: 24)
                    .background(
                        Circle()
                            .fill(AngelaTheme.statusColor(for: title))
                    )
            }
            .padding(.horizontal, AngelaTheme.spacingM)
            .padding(.vertical, AngelaTheme.spacingS)
            .background(AngelaTheme.background.opacity(0.5))
            .cornerRadius(AngelaTheme.cornerRadiusMedium)

            // Meeting Cards
            ScrollView(.vertical, showsIndicators: true) {
                VStack(spacing: AngelaTheme.spacingM) {
                    ForEach(meetings) { meeting in
                        MeetingBoardCard(
                            meeting: meeting,
                            isSelected: selectedMeeting?.id == meeting.id,
                            isDragging: draggingMeeting?.id == meeting.id,
                            onTap: {
                                selectedMeeting = meeting
                            },
                            onDragStart: {
                                draggingMeeting = meeting
                            },
                            onDragEnd: {
                                draggingMeeting = nil
                            }
                        )
                    }

                    if meetings.isEmpty {
                        EmptyColumnView()
                    }
                }
                .padding(.horizontal, AngelaTheme.spacingXS)
            }
            .frame(maxHeight: .infinity)
        }
        .frame(width: 320)
        .padding(AngelaTheme.spacingM)
        .background(isDropTarget ? AngelaTheme.primaryPurple.opacity(0.2) : AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusLarge)
        .shadow(color: Color.black.opacity(0.06), radius: 8, y: 4)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusLarge)
                .stroke(isDropTarget ? AngelaTheme.primaryPurple : Color.clear, lineWidth: 2)
        )
        .animation(.spring(response: 0.3), value: isDropTarget)
        .onDrop(of: [.text], isTargeted: $isDropTarget) { providers in
            if let meeting = draggingMeeting, meeting.status.rawValue != status {
                onDrop(meeting)
                return true
            }
            return false
        }
        .onChange(of: isDropTarget) { oldValue, newValue in
            draggedOverColumn = newValue ? status : nil
        }
    }
}

// MARK: - Meeting Board Card
struct MeetingBoardCard: View {
    let meeting: Meeting
    let isSelected: Bool
    let isDragging: Bool
    let onTap: () -> Void
    let onDragStart: () -> Void
    let onDragEnd: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
                // Title
                Text(meeting.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)

                // Description preview
                if let description = meeting.description, !description.isEmpty {
                    Text(description)
                        .font(.system(size: 13))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                }

                Divider()

                // Metadata
                HStack(spacing: AngelaTheme.spacingM) {
                    // Priority badge
                    let priority = meeting.priority ?? "Normal"
                    HStack(spacing: 4) {
                        Image(systemName: AngelaTheme.priorityIcon(for: priority))
                            .font(.system(size: 10, weight: .bold))
                        Text(priority)
                            .font(.system(size: 11, weight: .semibold))
                    }
                    .foregroundColor(AngelaTheme.priorityColor(for: priority))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(
                        AngelaTheme.priorityColor(for: priority).opacity(0.15)
                    )
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)

                    Spacer()

                    // Date
                    HStack(spacing: 4) {
                        Image(systemName: "calendar")
                            .font(.system(size: 10))
                        Text(meeting.scheduledDate, style: .date)
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.textSecondary)
                }

                // Tags (if any)
                if !meeting.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(meeting.tags) { tag in
                                Text(tag.name)
                                    .font(.system(size: 10, weight: .medium))
                                    .foregroundColor(AngelaTheme.primaryPurple)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(AngelaTheme.palePurple)
                                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                            }
                        }
                    }
                }
            }
            .padding(AngelaTheme.spacingM)
            .frame(maxWidth: .infinity, alignment: .leading)
            .angelaCard(isHovered: isHovered || isSelected)
            .opacity(isDragging ? 0.5 : 1.0)
            .scaleEffect(isDragging ? 0.95 : 1.0)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
        .onDrag {
            onDragStart()
            // Delay to allow drag to complete
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                onDragEnd()
            }
            return NSItemProvider(object: meeting.id.uuidString as NSString)
        }
    }
}

// MARK: - Empty Column View
struct EmptyColumnView: View {
    var body: some View {
        VStack(spacing: AngelaTheme.spacingS) {
            Image(systemName: "tray")
                .font(.system(size: 32))
                .foregroundColor(AngelaTheme.textSecondary.opacity(0.5))

            Text("No meetings")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(AngelaTheme.textSecondary.opacity(0.7))
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AngelaTheme.spacingXL * 2)
    }
}

// MARK: - Preview
#Preview {
    BoardView(
        viewModel: MeetingListViewModel(),
        selectedMeeting: .constant(nil),
        searchText: "",
        selectedPriorities: [],
        selectedStatuses: [],
        dateRange: nil
    )
    .environmentObject(DatabaseService.shared)
}
