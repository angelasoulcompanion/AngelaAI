//
//  SidebarView.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//

import SwiftUI

struct SidebarView: View {
    @Binding var selectedMeeting: Meeting?
    @State private var selectedSection: SidebarSection = .calendar

    enum SidebarSection: String, CaseIterable {
        case calendar = "Calendar"
        case all = "All Meetings"
        case starred = "Starred"
        case tags = "Tags"
        case people = "People"
        case search = "Search"
    }

    var body: some View {
        List(selection: $selectedSection) {
            // Main sections
            Section("Navigate") {
                ForEach(SidebarSection.allCases, id: \.self) { section in
                    Label(section.rawValue, systemImage: iconFor(section))
                        .tag(section)
                }
            }

            // Tags
            Section("Tags") {
                TagRowView(name: "Planning", color: .blue, count: 0)
                TagRowView(name: "Review", color: .green, count: 0)
                TagRowView(name: "Standup", color: .orange, count: 0)
                TagRowView(name: "1-on-1", color: .purple, count: 0)
            }

            // Recent people
            Section("People") {
                PersonRowView(name: "David Samanyaporn", meetingCount: 0)
            }

            // Quick filters
            Section("Quick") {
                Label("Today", systemImage: "calendar.badge.clock")
                    .badge(0)
                Label("This Week", systemImage: "calendar")
                    .badge(0)
                Label("Pending Actions", systemImage: "checklist")
                    .badge(0)
                    .foregroundColor(.orange)
            }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 200)
    }

    private func iconFor(_ section: SidebarSection) -> String {
        switch section {
        case .calendar: return "calendar"
        case .all: return "list.bullet"
        case .starred: return "star.fill"
        case .tags: return "tag.fill"
        case .people: return "person.2.fill"
        case .search: return "magnifyingglass"
        }
    }
}

struct TagRowView: View {
    let name: String
    let color: Color
    let count: Int

    var body: some View {
        HStack {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(name)
            Spacer()
            if count > 0 {
                Text("\(count)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct PersonRowView: View {
    let name: String
    let meetingCount: Int

    var body: some View {
        HStack {
            Image(systemName: "person.circle.fill")
                .foregroundColor(.blue)
            Text(name)
            Spacer()
            if meetingCount > 0 {
                Text("\(meetingCount)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

#Preview {
    SidebarView(selectedMeeting: .constant(nil))
        .frame(width: 250)
}
