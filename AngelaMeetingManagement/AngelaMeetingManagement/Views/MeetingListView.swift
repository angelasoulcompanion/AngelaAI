//
//  MeetingListView.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  ClickUp-inspired List View with Purple Theme
//

import SwiftUI

struct MeetingListView: View {
    @ObservedObject var viewModel: MeetingListViewModel
    @Binding var selectedMeeting: Meeting?
    @Binding var searchText: String
    @Binding var showingNewMeeting: Bool

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(AngelaTheme.textSecondary)
                    .font(.system(size: 14))

                TextField("Search meetings...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(AngelaTheme.textSecondary)
                            .font(.system(size: 14))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(AngelaTheme.spacingL)
            .background(AngelaTheme.cardBackground)

            Divider()

            // Meetings list
            if viewModel.isLoading {
                ProgressView("Loading meetings...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(AngelaTheme.background)
            } else if viewModel.meetings.isEmpty {
                emptyStateView
            } else {
                ScrollView {
                    LazyVStack(spacing: AngelaTheme.spacingL) {
                        // Upcoming meetings
                        if !viewModel.upcomingMeetings.isEmpty {
                            MeetingSectionView(
                                title: "Upcoming Meetings",
                                meetings: viewModel.upcomingMeetings,
                                selectedMeeting: $selectedMeeting
                            )
                        }

                        // Past meetings
                        if !viewModel.pastMeetings.isEmpty {
                            MeetingSectionView(
                                title: "Past Meetings",
                                meetings: viewModel.pastMeetings,
                                selectedMeeting: $selectedMeeting
                            )
                        }
                    }
                    .padding(AngelaTheme.spacingXL)
                }
                .background(AngelaTheme.background)
            }
        }
        .background(AngelaTheme.background)
    }

    // MARK: - Empty State View
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "calendar.badge.plus")
                .font(.system(size: 60))
                .foregroundColor(AngelaTheme.primaryPurple.opacity(0.3))

            Text("No Meetings Yet")
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text("Create your first meeting to get started")
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textSecondary)

            Button("Create Meeting") {
                showingNewMeeting = true
            }
            .buttonStyle(AngelaPrimaryButtonStyle())
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AngelaTheme.background)
    }
}

// MARK: - Meeting Section View
struct MeetingSectionView: View {
    let title: String
    let meetings: [Meeting]
    @Binding var selectedMeeting: Meeting?

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            // Section Header
            Text(title)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(AngelaTheme.textSecondary)
                .textCase(.uppercase)
                .padding(.horizontal, AngelaTheme.spacingS)

            // Meeting Cards
            ForEach(meetings) { meeting in
                MeetingCardView(
                    meeting: meeting,
                    isSelected: selectedMeeting?.id == meeting.id
                )
                .onTapGesture {
                    selectedMeeting = meeting
                }
            }
        }
    }
}

// MARK: - Meeting Card View
struct MeetingCardView: View {
    let meeting: Meeting
    let isSelected: Bool

    @State private var isHovered = false

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            // Title & Status Row
            HStack {
                Text(meeting.title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .lineLimit(1)

                Spacer()

                // Status Badge
                HStack(spacing: 4) {
                    Circle()
                        .fill(AngelaTheme.statusColor(for: meeting.status.rawValue))
                        .frame(width: 8, height: 8)

                    Text(meeting.status.rawValue.capitalized)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(AngelaTheme.statusColor(for: meeting.status.rawValue))
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(AngelaTheme.statusColor(for: meeting.status.rawValue).opacity(0.1))
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
            }

            // Date and Time Row
            HStack(spacing: AngelaTheme.spacingL) {
                HStack(spacing: 6) {
                    Image(systemName: "calendar")
                        .font(.system(size: 12))
                    Text(meeting.scheduledDate, style: .date)
                        .font(.system(size: 13))
                }
                .foregroundColor(AngelaTheme.textSecondary)

                HStack(spacing: 6) {
                    Image(systemName: "clock")
                        .font(.system(size: 12))
                    Text(meeting.startTime, style: .time)
                        .font(.system(size: 13))
                }
                .foregroundColor(AngelaTheme.textSecondary)
            }

            // Priority & Stats Row
            HStack(spacing: AngelaTheme.spacingL) {
                // Priority
                if let priority = meeting.priority {
                    HStack(spacing: 4) {
                        Image(systemName: AngelaTheme.priorityIcon(for: priority))
                            .font(.system(size: 10))
                        Text(priority)
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.priorityColor(for: priority))
                }

                Spacer()

                // Stats
                HStack(spacing: AngelaTheme.spacingM) {
                    if let participantCount = meeting.participantCount, participantCount > 0 {
                        Label("\(participantCount)", systemImage: "person.2")
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.textSecondary)
                    }

                    if let documentCount = meeting.documentCount, documentCount > 0 {
                        Label("\(documentCount)", systemImage: "paperclip")
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.textSecondary)
                    }

                    if let actionItemCount = meeting.actionItemCount, actionItemCount > 0 {
                        Label("\(actionItemCount)", systemImage: "checklist")
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                }
            }

            // Tags (if any)
            if !meeting.tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(meeting.tags.prefix(5)) { tag in
                            Text(tag.name)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(AngelaTheme.primaryPurple)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(AngelaTheme.palePurple)
                                .cornerRadius(AngelaTheme.cornerRadiusSmall)
                        }

                        if meeting.tags.count > 5 {
                            Text("+\(meeting.tags.count - 5)")
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                    }
                }
            }
        }
        .padding(AngelaTheme.spacingM)
        .frame(maxWidth: .infinity, alignment: .leading)
        .angelaCard(isHovered: isHovered || isSelected)
        .overlay(
            Group {
                if isSelected {
                    RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                        .stroke(AngelaTheme.primaryPurple, lineWidth: 2)
                }
            }
        )
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

#Preview {
    MeetingListView(
        viewModel: MeetingListViewModel(),
        selectedMeeting: .constant(nil),
        searchText: .constant(""),
        showingNewMeeting: .constant(false)
    )
}
