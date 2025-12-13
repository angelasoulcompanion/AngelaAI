//
//  MeetingDetailView.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  ClickUp-inspired Meeting Detail View with Edit & Delete
//

import SwiftUI

struct MeetingDetailView: View {
    let meeting: Meeting
    @EnvironmentObject var databaseService: DatabaseService
    @Environment(\.dismiss) var dismiss
    var onMeetingChanged: (() -> Void)? = nil // Callback for refresh
    var onDeleted: (() -> Void)? = nil // Callback for delete (clear selection)

    @State private var isEditMode = false
    @State private var showingDeleteAlert = false
    @State private var isDeleting = false

    var body: some View {
        VStack(spacing: 0) {
            if isEditMode {
                // EDIT MODE
                EditMeetingView(
                    meeting: meeting,
                    isEditMode: $isEditMode,
                    onSaved: {
                        onMeetingChanged?()
                    },
                    onDeleted: {
                        onDeleted?()
                    }
                )
            } else {
                // VIEW MODE
                viewModeContent
            }
        }
        .alert("Delete Meeting?", isPresented: $showingDeleteAlert) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                deleteMeeting()
            }
        } message: {
            Text("Are you sure you want to delete \"\(meeting.title)\"? This action cannot be undone.")
        }
    }

    // MARK: - View Mode Content
    private var viewModeContent: some View {
        VStack(spacing: 0) {
            // HEADER
            headerView

            Divider()

            // CONTENT
            ScrollView {
                VStack(spacing: AngelaTheme.spacingL) {
                    // Title & Status
                    titleSection

                    // Quick Info Cards
                    HStack(spacing: AngelaTheme.spacingM) {
                        dateTimeInfoCard
                        statusInfoCard
                    }

                    // Location
                    if meeting.location != nil || meeting.meetingLink != nil {
                        locationCard
                    }

                    // Description
                    if let description = meeting.description, !description.isEmpty {
                        infoCard(
                            icon: "text.alignleft",
                            title: "Description",
                            content: description
                        )
                    }

                    // Agenda
                    if let agenda = meeting.agenda, !agenda.isEmpty {
                        infoCard(
                            icon: "list.bullet.clipboard",
                            title: "Agenda",
                            content: agenda
                        )
                    }

                    // Objectives
                    if let objectives = meeting.objectives, !objectives.isEmpty {
                        infoCard(
                            icon: "target",
                            title: "Objectives",
                            content: objectives
                        )
                    }

                    Spacer(minLength: AngelaTheme.spacingXL)
                }
                .padding(AngelaTheme.spacingXL)
            }
            .background(AngelaTheme.background)

            Divider()

            // FOOTER ACTIONS
            footerActions
        }
    }

    // MARK: - Header
    private var headerView: some View {
        HStack {
            // Meeting Type Badge
            HStack(spacing: 6) {
                Image(systemName: "calendar.badge.clock")
                    .font(.system(size: 12))
                Text(meeting.meetingType?.capitalized ?? "Meeting")
                    .font(.system(size: 12, weight: .medium))
            }
            .foregroundColor(AngelaTheme.primaryPurple)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(AngelaTheme.palePurple)
            .cornerRadius(AngelaTheme.cornerRadiusSmall)

            Spacer()

            // Action Buttons
            HStack(spacing: AngelaTheme.spacingS) {
                // Edit Button
                Button(action: { isEditMode = true }) {
                    HStack(spacing: 4) {
                        Image(systemName: "pencil")
                            .font(.system(size: 14))
                        Text("Edit")
                            .font(.system(size: 13, weight: .medium))
                    }
                }
                .buttonStyle(AngelaSecondaryButtonStyle())

                // Delete Button
                Button(action: { showingDeleteAlert = true }) {
                    Image(systemName: "trash")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.accentPink)
                }
                .buttonStyle(.plain)
                .padding(8)
                .background(Circle().fill(AngelaTheme.accentPink.opacity(0.1)))
            }
        }
        .padding(.horizontal, AngelaTheme.spacingL)
        .padding(.vertical, AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Title Section
    private var titleSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            Text(meeting.title)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            // Badges
            HStack(spacing: 8) {
                // Priority Badge
                if let priority = meeting.priority {
                    HStack(spacing: 4) {
                        Image(systemName: AngelaTheme.priorityIcon(for: priority))
                            .font(.system(size: 11, weight: .bold))
                        Text(priority)
                            .font(.system(size: 12, weight: .semibold))
                    }
                    .foregroundColor(AngelaTheme.priorityColor(for: priority))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(AngelaTheme.priorityColor(for: priority).opacity(0.15))
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                }

                // Virtual Badge
                if meeting.isVirtual {
                    HStack(spacing: 4) {
                        Image(systemName: "video.fill")
                            .font(.system(size: 11))
                        Text("Virtual")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.accentBlue)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(AngelaTheme.accentBlue.opacity(0.15))
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                }

                // Recurring Badge
                if meeting.isRecurring {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 11))
                        Text("Recurring")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                }
            }
        }
    }

    // MARK: - Date/Time Info Card
    private var dateTimeInfoCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("When")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            // Date
            VStack(alignment: .leading, spacing: 4) {
                Text("DATE")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .textCase(.uppercase)

                Text(meeting.meetingDate, style: .date)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Time
            VStack(alignment: .leading, spacing: 4) {
                Text("TIME")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .textCase(.uppercase)

                HStack(spacing: 6) {
                    Text(meeting.startTime, style: .time)
                        .font(.system(size: 15, weight: .semibold))
                    Image(systemName: "arrow.right")
                        .font(.system(size: 10))
                        .foregroundColor(AngelaTheme.textSecondary)
                    if let endTime = meeting.endTime {
                        Text(endTime, style: .time)
                            .font(.system(size: 15, weight: .semibold))
                    }
                }
                .foregroundColor(AngelaTheme.textPrimary)
            }

            // Duration
            if let duration = meeting.durationMinutes {
                HStack(spacing: 4) {
                    Image(systemName: "clock")
                        .font(.system(size: 10))
                    Text("\(duration / 60)h \(duration % 60)m")
                        .font(.system(size: 11, weight: .medium))
                }
                .foregroundColor(AngelaTheme.textSecondary)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(AngelaTheme.palePurple)
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
            }
        }
        .padding(AngelaTheme.spacingM)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    // MARK: - Status Info Card
    private var statusInfoCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: AngelaTheme.statusIcon(for: meeting.status.rawValue))
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Status")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            // Current Status
            HStack(spacing: 8) {
                Circle()
                    .fill(AngelaTheme.statusColor(for: meeting.status.rawValue))
                    .frame(width: 12, height: 12)

                Text(meeting.status.rawValue.capitalized)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            // Timestamps
            VStack(alignment: .leading, spacing: 8) {
                timestampRow(icon: "plus.circle", label: "Created", date: meeting.createdAt)
                timestampRow(icon: "pencil.circle", label: "Updated", date: meeting.updatedAt)

                if let completedAt = meeting.completedAt {
                    timestampRow(icon: "checkmark.circle", label: "Completed", date: completedAt)
                }
            }
            .font(.system(size: 11))
            .foregroundColor(AngelaTheme.textSecondary)
        }
        .padding(AngelaTheme.spacingM)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    // MARK: - Location Card
    private var locationCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: meeting.isVirtual ? "video.fill" : "location.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Location")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            if let link = meeting.meetingLink {
                Link(destination: URL(string: link) ?? URL(string: "https://")!) {
                    HStack {
                        Text(link)
                            .font(.system(size: 14))
                            .foregroundColor(AngelaTheme.accentBlue)
                            .lineLimit(1)

                        Spacer()

                        Image(systemName: "arrow.up.right")
                            .font(.system(size: 12))
                            .foregroundColor(AngelaTheme.accentBlue)
                    }
                    .padding(AngelaTheme.spacingM)
                    .background(AngelaTheme.accentBlue.opacity(0.1))
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                }
            } else if let location = meeting.location {
                Text(location)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .padding(AngelaTheme.spacingM)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
            }
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    // MARK: - Info Card Helper
    private func infoCard(icon: String, title: String, content: String) -> some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text(title)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Text(content)
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textPrimary)
                .padding(AngelaTheme.spacingM)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(AngelaTheme.palePurple)
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    // MARK: - Timestamp Row Helper
    private func timestampRow(icon: String, label: String, date: Date) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 10))
            Text(label + ":")
                .fontWeight(.medium)
            Text(date, style: .date)
            Text(date, style: .time)
        }
    }

    // MARK: - Footer Actions
    private var footerActions: some View {
        HStack {
            Text("Last updated: \(meeting.updatedAt, style: .relative)")
                .font(.system(size: 11))
                .foregroundColor(AngelaTheme.textSecondary)

            Spacer()
        }
        .padding(.horizontal, AngelaTheme.spacingXL)
        .padding(.vertical, AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Delete Action
    private func deleteMeeting() {
        isDeleting = true
        Task {
            do {
                try await databaseService.deleteMeeting(id: meeting.id)
                await MainActor.run {
                    onDeleted?() // Clear selection first
                    onMeetingChanged?() // Then trigger refresh
                    isDeleting = false
                }
            } catch {
                print("❌ Error deleting meeting: \(error)")
                await MainActor.run {
                    isDeleting = false
                }
            }
        }
    }
}

// MARK: - Edit Meeting View
struct EditMeetingView: View {
    let meeting: Meeting
    @Binding var isEditMode: Bool
    @EnvironmentObject var databaseService: DatabaseService
    var onSaved: (() -> Void)? = nil // Callback for refresh
    var onDeleted: (() -> Void)? = nil // Callback to clear selection after save

    // Editable fields
    @State private var title: String
    @State private var description: String
    @State private var meetingDate: Date
    @State private var startTime: Date
    @State private var endTime: Date
    @State private var location: String
    @State private var isVirtual: Bool
    @State private var meetingLink: String
    @State private var priority: String
    @State private var meetingType: String
    @State private var agenda: String
    @State private var objectives: String

    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showError = false

    let priorities = ["Urgent", "High", "Normal", "Low"]
    let meetingTypes = ["Regular", "One-on-One", "Team Sync", "Planning", "Review"]

    init(meeting: Meeting, isEditMode: Binding<Bool>, onSaved: (() -> Void)? = nil, onDeleted: (() -> Void)? = nil) {
        self.meeting = meeting
        self._isEditMode = isEditMode
        self.onSaved = onSaved
        self.onDeleted = onDeleted

        // Initialize state from meeting
        _title = State(initialValue: meeting.title)
        _description = State(initialValue: meeting.description ?? "")
        _meetingDate = State(initialValue: meeting.meetingDate)
        _startTime = State(initialValue: meeting.startTime)
        _endTime = State(initialValue: meeting.endTime ?? Date())
        _location = State(initialValue: meeting.location ?? "")
        _isVirtual = State(initialValue: meeting.isVirtual)
        _meetingLink = State(initialValue: meeting.meetingLink ?? "")
        _priority = State(initialValue: meeting.priority ?? "Normal")
        _meetingType = State(initialValue: meeting.meetingType ?? "regular")
        _agenda = State(initialValue: meeting.agenda ?? "")
        _objectives = State(initialValue: meeting.objectives ?? "")
    }

    var body: some View {
        VStack(spacing: 0) {
            // HEADER
            HStack {
                Button("Cancel") {
                    isEditMode = false
                }
                .buttonStyle(AngelaSecondaryButtonStyle())

                Spacer()

                Text("Edit Meeting")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button(action: saveMeeting) {
                    HStack(spacing: 6) {
                        if isLoading {
                            ProgressView()
                                .scaleEffect(0.8)
                                .tint(.white)
                        } else {
                            Image(systemName: "checkmark")
                            Text("Save")
                        }
                    }
                }
                .buttonStyle(AngelaPrimaryButtonStyle())
                .disabled(title.isEmpty || isLoading)
            }
            .padding(.horizontal, AngelaTheme.spacingL)
            .padding(.vertical, AngelaTheme.spacingM)
            .background(AngelaTheme.cardBackground)

            Divider()

            // Same form as CreateMeetingView but with existing values
            ScrollView {
                VStack(spacing: AngelaTheme.spacingL) {
                    // Title
                    titleSection

                    // Date/Time and Priority Cards (Two Column)
                    HStack(alignment: .top, spacing: AngelaTheme.spacingL) {
                        dateTimeCard
                        priorityStatusCard
                    }

                    // Location
                    locationSection

                    // Description
                    descriptionSection

                    // Agenda
                    agendaSection

                    // Objectives
                    objectivesSection
                }
                .padding(AngelaTheme.spacingXL)
            }
            .background(AngelaTheme.background)
        }
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "Unknown error")
        }
    }

    // MARK: - View Sections

    private var titleSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingS) {
            Text("Meeting Title *")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(AngelaTheme.textPrimary)

            TextField("Enter meeting title...", text: $title)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(AngelaTheme.textPrimary)
                .textFieldStyle(.plain)
                .padding(AngelaTheme.spacingM)
                .background(AngelaTheme.cardBackground)
                .cornerRadius(AngelaTheme.cornerRadiusMedium)
                .overlay(
                    RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusMedium)
                        .stroke(title.isEmpty ? AngelaTheme.border : AngelaTheme.primaryPurple, lineWidth: title.isEmpty ? 1 : 2)
                )
        }
    }

    private var dateTimeCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("When")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            // Date Picker
            VStack(alignment: .leading, spacing: 4) {
                Text("Date")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .textCase(.uppercase)

                DatePicker("", selection: $meetingDate, displayedComponents: .date)
                    .datePickerStyle(.compact)
                    .labelsHidden()
                    .tint(AngelaTheme.primaryPurple)
                    .colorScheme(.light)
            }

            // Time Pickers
            HStack(spacing: AngelaTheme.spacingM) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Start")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .textCase(.uppercase)

                    DatePicker("", selection: $startTime, displayedComponents: .hourAndMinute)
                        .labelsHidden()
                        .frame(width: 90)
                        .tint(AngelaTheme.primaryPurple)
                        .colorScheme(.light)
                }

                Image(systemName: "arrow.right")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .padding(.top, 16)

                VStack(alignment: .leading, spacing: 4) {
                    Text("End")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)
                        .textCase(.uppercase)

                    DatePicker("", selection: $endTime, displayedComponents: .hourAndMinute)
                        .labelsHidden()
                        .frame(width: 90)
                        .tint(AngelaTheme.primaryPurple)
                        .colorScheme(.light)
                }
            }

            // Duration
            HStack(spacing: 4) {
                Image(systemName: "clock")
                    .font(.system(size: 10))
                Text(durationText)
                    .font(.system(size: 11, weight: .medium))
            }
            .foregroundColor(AngelaTheme.textSecondary)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(AngelaTheme.palePurple)
            .cornerRadius(AngelaTheme.cornerRadiusSmall)
        }
        .padding(AngelaTheme.spacingM)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    private var priorityStatusCard: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: "flag.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Priority & Status")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            // Priority
            VStack(alignment: .leading, spacing: 4) {
                Text("Priority")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .textCase(.uppercase)

                Menu {
                    ForEach(priorities, id: \.self) { p in
                        Button(action: { priority = p }) {
                            HStack {
                                Image(systemName: AngelaTheme.priorityIcon(for: p))
                                Text(p)
                                if priority == p {
                                    Spacer()
                                    Image(systemName: "checkmark")
                                }
                            }
                        }
                    }
                } label: {
                    HStack {
                        Image(systemName: AngelaTheme.priorityIcon(for: priority))
                            .font(.system(size: 12, weight: .semibold))
                        Text(priority)
                            .font(.system(size: 13, weight: .medium))
                        Spacer()
                        Image(systemName: "chevron.down")
                            .font(.system(size: 10))
                    }
                    .foregroundColor(AngelaTheme.priorityColor(for: priority))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(AngelaTheme.priorityColor(for: priority).opacity(0.15))
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                }
                .buttonStyle(.plain)
            }

            // Meeting Type
            VStack(alignment: .leading, spacing: 4) {
                Text("Type")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .textCase(.uppercase)

                Menu {
                    ForEach(meetingTypes, id: \.self) { type in
                        Button(action: { meetingType = type.lowercased() }) {
                            HStack {
                                Text(type)
                                if meetingType == type.lowercased() {
                                    Spacer()
                                    Image(systemName: "checkmark")
                                }
                            }
                        }
                    }
                } label: {
                    HStack {
                        Text(meetingType.capitalized)
                            .font(.system(size: 13, weight: .medium))
                        Spacer()
                        Image(systemName: "chevron.down")
                            .font(.system(size: 10))
                    }
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 8)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(AngelaTheme.spacingM)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    private var locationSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: isVirtual ? "video.fill" : "location.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Location")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                // Virtual Toggle
                Toggle("", isOn: $isVirtual)
                    .labelsHidden()
                    .toggleStyle(.switch)
                    .tint(AngelaTheme.primaryPurple)

                Text(isVirtual ? "Virtual" : "In-Person")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Divider()

            if isVirtual {
                TextField("Meeting Link (Zoom, Teams, etc.)", text: $meetingLink)
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .padding(AngelaTheme.spacingM)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
            } else {
                TextField("Location (Room, Building, Address)", text: $location)
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .padding(AngelaTheme.spacingM)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
            }
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    private var descriptionSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: "text.alignleft")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Description")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            TextEditor(text: $description)
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textPrimary)
                .frame(height: 100)
                .scrollContentBackground(.hidden)
                .padding(8)
                .background(AngelaTheme.palePurple)
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    private var agendaSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: "list.bullet.clipboard")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Agenda")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            TextEditor(text: $agenda)
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textPrimary)
                .frame(height: 120)
                .scrollContentBackground(.hidden)
                .padding(8)
                .background(AngelaTheme.palePurple)
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    private var objectivesSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
            HStack {
                Image(systemName: "target")
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .font(.system(size: 16))

                Text("Objectives")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)
            }

            Divider()

            TextEditor(text: $objectives)
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textPrimary)
                .frame(height: 100)
                .scrollContentBackground(.hidden)
                .padding(8)
                .background(AngelaTheme.palePurple)
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    private var durationText: String {
        let duration = endTime.timeIntervalSince(startTime)
        let hours = Int(duration) / 3600
        let minutes = Int(duration) % 3600 / 60

        if hours > 0 {
            return "\(hours)h \(minutes)m"
        } else {
            return "\(minutes)m"
        }
    }

    // MARK: - Actions

    private func saveMeeting() {
        guard !title.isEmpty else { return }
        isLoading = true

        Task {
            do {
                // Calculate duration
                let duration = Int(endTime.timeIntervalSince(startTime) / 60)

                // Create updated meeting object
                var updatedMeeting = meeting
                updatedMeeting.title = title
                updatedMeeting.description = description.isEmpty ? nil : description
                updatedMeeting.meetingDate = meetingDate
                updatedMeeting.startTime = startTime
                updatedMeeting.endTime = endTime
                updatedMeeting.durationMinutes = duration > 0 ? duration : nil
                updatedMeeting.location = location.isEmpty ? nil : location
                updatedMeeting.isVirtual = isVirtual
                updatedMeeting.meetingLink = meetingLink.isEmpty ? nil : meetingLink
                updatedMeeting.meetingType = meetingType
                updatedMeeting.priority = priority
                updatedMeeting.agenda = agenda.isEmpty ? nil : agenda
                updatedMeeting.objectives = objectives.isEmpty ? nil : objectives
                updatedMeeting.updatedAt = Date()

                // Update in database
                try await databaseService.updateMeeting(updatedMeeting)

                await MainActor.run {
                    onDeleted?() // Clear selection first - return to main
                    onSaved?() // Trigger refresh
                    isEditMode = false
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    showError = true
                    isLoading = false
                }
            }
        }
    }
}

// MARK: - Preview
#Preview {
    MeetingDetailView(
        meeting: Meeting(
            id: UUID(),
            title: "Team Sync Meeting",
            description: "Weekly sync with the development team",
            meetingDate: Date(),
            startTime: Date(),
            endTime: Date().addingTimeInterval(3600),
            durationMinutes: 60,
            priority: "High",
            agenda: "1. Sprint review\n2. Planning next sprint",
            objectives: "Align on priorities"
        )
    )
    .environmentObject(DatabaseService.shared)
}
