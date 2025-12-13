//
//  MeetingListView.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
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
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                TextField("Search meetings...", text: $searchText)
                    .textFieldStyle(.plain)

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
            .background(Color(nsColor: .controlBackgroundColor))

            Divider()

            // Meetings list
            if viewModel.isLoading {
                ProgressView("Loading meetings...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.meetings.isEmpty {
                VStack(spacing: 20) {
                    Image(systemName: "calendar.badge.plus")
                        .font(.system(size: 60))
                        .foregroundColor(.secondary)

                    Text("No Meetings Yet")
                        .font(.title2)
                        .fontWeight(.semibold)

                    Text("Create your first meeting to get started")
                        .foregroundColor(.secondary)

                    Button("Create Meeting") {
                        showingNewMeeting = true
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 16) {
                        // Upcoming meetings
                        MeetingSectionView(
                            title: "Upcoming Meetings",
                            meetings: viewModel.upcomingMeetings,
                            selectedMeeting: $selectedMeeting
                        )

                        // Past meetings
                        if !viewModel.pastMeetings.isEmpty {
                            MeetingSectionView(
                                title: "Past Meetings",
                                meetings: viewModel.pastMeetings,
                                selectedMeeting: $selectedMeeting
                            )
                        }
                    }
                    .padding()
                }
            }
        }
        .sheet(isPresented: $showingNewMeeting) {
            Text("Create New Meeting Form")
                .frame(width: 600, height: 500)
        }
    }
}

struct MeetingSectionView: View {
    let title: String
    let meetings: [Meeting]
    @Binding var selectedMeeting: Meeting?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundColor(.secondary)

            ForEach(meetings) { meeting in
                MeetingCardView(meeting: meeting)
                    .onTapGesture {
                        selectedMeeting = meeting
                    }
            }
        }
    }
}

struct MeetingCardView: View {
    let meeting: Meeting

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Title
            Text(meeting.title)
                .font(.headline)

            // Date and time
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(.secondary)
                Text(meeting.formattedDate)

                Image(systemName: "clock")
                    .foregroundColor(.secondary)
                Text(meeting.formattedTime)
            }
            .font(.caption)
            .foregroundColor(.secondary)

            // Stats
            HStack(spacing: 16) {
                Label("\(meeting.participantCount ?? 0)", systemImage: "person.2")
                Label("\(meeting.documentCount ?? 0)", systemImage: "paperclip")
                Label("\(meeting.actionItemCount ?? 0)", systemImage: "checklist")
            }
            .font(.caption)
            .foregroundColor(.secondary)

            // Tags (if any)
            if !meeting.tags.isEmpty {
                HStack(spacing: 6) {
                    ForEach(meeting.tags.prefix(3)) { tag in
                        Text(tag.name)
                            .font(.caption2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(Color.blue.opacity(0.2))
                            .cornerRadius(4)
                    }

                    if meeting.tags.count > 3 {
                        Text("+\(meeting.tags.count - 3)")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
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
