//
//  CreateMeetingView.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  ClickUp-inspired Create Meeting Form
//

import SwiftUI

struct CreateMeetingView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var databaseService: DatabaseService

    // Basic Info
    @State private var title: String = ""
    @State private var description: String = ""
    @State private var meetingDate = Date()
    @State private var startTime = Date()
    @State private var endTime = Date().addingTimeInterval(3600) // +1 hour
    @State private var location: String = ""
    @State private var isVirtual = false
    @State private var meetingLink: String = ""
    @State private var priority: String = "Normal"
    @State private var status: Meeting.MeetingStatus = .scheduled

    // Additional
    @State private var meetingType: String = "regular"
    @State private var agenda: String = ""
    @State private var objectives: String = ""

    // UI State
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showError = false

    let priorities = ["Urgent", "High", "Normal", "Low"]
    let meetingTypes = ["Regular", "One-on-One", "Team Sync", "Planning", "Review"]

    var body: some View {
        VStack(spacing: 0) {
            // HEADER
            headerView

            Divider()

            // FORM CONTENT
            ScrollView {
                VStack(spacing: AngelaTheme.spacingXL) {
                    // Title Section (Most Important!)
                    titleSection

                    // Quick Info Cards
                    HStack(spacing: AngelaTheme.spacingM) {
                        dateTimeCard
                        priorityStatusCard
                    }

                    // Location Section
                    locationSection

                    // Description & Details
                    descriptionSection

                    // Agenda & Objectives
                    agendaObjectivesSection

                    Spacer(minLength: AngelaTheme.spacingXL)
                }
                .padding(AngelaTheme.spacingXL)
            }
            .background(AngelaTheme.background)

            Divider()

            // FOOTER ACTIONS
            footerActions
        }
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage ?? "Unknown error")
        }
    }

    // MARK: - Header
    private var headerView: some View {
        HStack {
            Button(action: { dismiss() }) {
                Image(systemName: "xmark")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
            }
            .buttonStyle(.plain)
            .padding(8)
            .background(Circle().fill(Color.black.opacity(0.05)))

            Spacer()

            VStack(spacing: 2) {
                Text("New Meeting")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Fill in the details below")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Placeholder for symmetry
            Color.clear
                .frame(width: 40, height: 40)
        }
        .padding(.horizontal, AngelaTheme.spacingL)
        .padding(.vertical, AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Title Section
    private var titleSection: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingS) {
            HStack {
                Text("Meeting Title")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("*")
                    .foregroundColor(AngelaTheme.accentPink)
            }

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

    // MARK: - Date/Time Card
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

    // MARK: - Priority/Status Card
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

    // MARK: - Location Section
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

                Text("Virtual")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            if isVirtual {
                TextField("Meeting link (e.g., Zoom, Teams)...", text: $meetingLink)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .textFieldStyle(.plain)
                    .padding(AngelaTheme.spacingM)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
            } else {
                TextField("Enter location...", text: $location)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .textFieldStyle(.plain)
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

    // MARK: - Description Section
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

            TextEditor(text: $description)
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textPrimary)
                .frame(height: 100)
                .scrollContentBackground(.hidden)
                .padding(8)
                .background(AngelaTheme.palePurple)
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
                .overlay(
                    RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusSmall)
                        .stroke(AngelaTheme.border, lineWidth: 1)
                )
        }
        .padding(AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
    }

    // MARK: - Agenda & Objectives
    private var agendaObjectivesSection: some View {
        VStack(spacing: AngelaTheme.spacingM) {
            // Agenda
            VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
                HStack {
                    Image(systemName: "list.bullet.clipboard")
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .font(.system(size: 16))

                    Text("Agenda")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                TextEditor(text: $agenda)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .frame(height: 80)
                    .scrollContentBackground(.hidden)
                    .padding(8)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                    .overlay(
                        RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusSmall)
                            .stroke(AngelaTheme.border, lineWidth: 1)
                    )
            }
            .padding(AngelaTheme.spacingM)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadiusMedium)
            .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)

            // Objectives
            VStack(alignment: .leading, spacing: AngelaTheme.spacingM) {
                HStack {
                    Image(systemName: "target")
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .font(.system(size: 16))

                    Text("Objectives")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                TextEditor(text: $objectives)
                    .font(.system(size: 14))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .frame(height: 80)
                    .scrollContentBackground(.hidden)
                    .padding(8)
                    .background(AngelaTheme.palePurple)
                    .cornerRadius(AngelaTheme.cornerRadiusSmall)
                    .overlay(
                        RoundedRectangle(cornerRadius: AngelaTheme.cornerRadiusSmall)
                            .stroke(AngelaTheme.border, lineWidth: 1)
                    )
            }
            .padding(AngelaTheme.spacingM)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadiusMedium)
            .shadow(color: Color.black.opacity(0.05), radius: 6, y: 3)
        }
    }

    // MARK: - Footer Actions
    private var footerActions: some View {
        HStack(spacing: AngelaTheme.spacingM) {
            // Cancel Button
            Button("Cancel") {
                dismiss()
            }
            .buttonStyle(AngelaSecondaryButtonStyle())

            Spacer()

            // Create Button
            Button(action: createMeeting) {
                HStack(spacing: 8) {
                    if isLoading {
                        ProgressView()
                            .scaleEffect(0.8)
                            .tint(.white)
                    } else {
                        Image(systemName: "plus.circle.fill")
                        Text("Create Meeting")
                    }
                }
            }
            .buttonStyle(AngelaPrimaryButtonStyle())
            .disabled(title.isEmpty || isLoading)
            .opacity(title.isEmpty ? 0.5 : 1.0)
        }
        .padding(.horizontal, AngelaTheme.spacingXL)
        .padding(.vertical, AngelaTheme.spacingL)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Computed Properties
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
    private func createMeeting() {
        guard !title.isEmpty else { return }

        isLoading = true

        Task {
            do {
                let meeting = Meeting(
                    id: UUID(),
                    title: title,
                    description: description.isEmpty ? nil : description,
                    meetingDate: meetingDate,
                    startTime: startTime,
                    endTime: endTime,
                    durationMinutes: Int(endTime.timeIntervalSince(startTime) / 60),
                    timezone: TimeZone.current.identifier,
                    location: location.isEmpty ? nil : location,
                    isVirtual: isVirtual,
                    meetingLink: meetingLink.isEmpty ? nil : meetingLink,
                    meetingType: meetingType,
                    status: status,
                    priority: priority,
                    agenda: agenda.isEmpty ? nil : agenda,
                    objectives: objectives.isEmpty ? nil : objectives
                )

                _ = try await databaseService.createMeeting(meeting)
                await MainActor.run {
                    dismiss()
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
    CreateMeetingView()
        .environmentObject(DatabaseService.shared)
}
