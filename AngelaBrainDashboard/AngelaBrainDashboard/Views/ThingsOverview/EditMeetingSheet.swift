//
//  EditMeetingSheet.swift
//  Angela Brain Dashboard
//
//  Sheet for editing an existing meeting.
//

import SwiftUI

struct EditMeetingSheet: View {
    let databaseService: DatabaseService
    let meeting: MeetingNote
    let onUpdated: () -> Void
    @Environment(\.dismiss) private var dismiss

    @State private var title: String
    @State private var meetingType: MeetingType
    @State private var selectedDate: Date
    @State private var startHour: Int
    @State private var startMinute: Int
    @State private var endHour: Int
    @State private var endMinute: Int
    @State private var location: String
    @State private var projectName: String
    @State private var attendeesText: String
    @State private var status: String
    @State private var notes: String

    @State private var isSaving = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSuccess = false

    @State private var savedLocations: [String] = []
    @State private var showLocationSuggestions = false

    init(databaseService: DatabaseService, meeting: MeetingNote, onUpdated: @escaping () -> Void) {
        self.databaseService = databaseService
        self.meeting = meeting
        self.onUpdated = onUpdated

        // Pre-fill from meeting
        _title = State(initialValue: meeting.title)
        _meetingType = State(initialValue: meeting.isSiteVisit ? .siteVisit : .standard)
        _selectedDate = State(initialValue: meeting.meetingDate ?? Date())
        _location = State(initialValue: meeting.location ?? "")
        _projectName = State(initialValue: meeting.projectName ?? "")
        _attendeesText = State(initialValue: meeting.attendees?.joined(separator: ", ") ?? "")
        _status = State(initialValue: meeting.things3Status)
        _notes = State(initialValue: meeting.rawNotes ?? "")

        // Parse time range "HH:MM-HH:MM"
        if let timeRange = meeting.timeRange {
            let parts = timeRange.split(separator: "-")
            if parts.count == 2 {
                let startParts = parts[0].split(separator: ":")
                let endParts = parts[1].split(separator: ":")
                _startHour = State(initialValue: Int(startParts.first ?? "9") ?? 9)
                _startMinute = State(initialValue: Int(startParts.last ?? "0") ?? 0)
                _endHour = State(initialValue: Int(endParts.first ?? "10") ?? 10)
                _endMinute = State(initialValue: Int(endParts.last ?? "0") ?? 0)
            } else {
                _startHour = State(initialValue: 9)
                _startMinute = State(initialValue: 0)
                _endHour = State(initialValue: 10)
                _endMinute = State(initialValue: 0)
            }
        } else {
            _startHour = State(initialValue: 9)
            _startMinute = State(initialValue: 0)
            _endHour = State(initialValue: 10)
            _endMinute = State(initialValue: 0)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            MeetingSheetHeader(title: "Edit Meeting", dismiss: dismiss)

            Divider()

            // Form
            ScrollView {
                VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
                    // Title
                    MeetingFormField("Meeting Title", icon: "doc.text.fill") {
                        TextField("Title", text: $title)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Status
                    MeetingFormField("Status", icon: "circle.badge.checkmark.fill") {
                        HStack(spacing: 8) {
                            ForEach(["open", "completed"], id: \.self) { s in
                                Button {
                                    status = s
                                } label: {
                                    HStack(spacing: 4) {
                                        Image(systemName: s == "open" ? "circle" : "checkmark.circle.fill")
                                            .font(.system(size: 10))
                                        Text(s == "open" ? "Open" : "Completed")
                                            .font(.system(size: 11, weight: .medium))
                                    }
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(status == s ? (s == "open" ? Color(hex: "3B82F6") : Color(hex: "10B981")) : AngelaTheme.backgroundLight)
                                    .foregroundColor(status == s ? .white : AngelaTheme.textPrimary)
                                    .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Meeting Type
                    MeetingTypePicker(meetingType: $meetingType)

                    // Date
                    MeetingFormField("Date", icon: "calendar") {
                        DatePicker("", selection: $selectedDate, displayedComponents: .date)
                            .datePickerStyle(.compact)
                            .labelsHidden()

                        Text(thaiDateString(for: selectedDate))
                            .font(.system(size: 11))
                            .foregroundColor(AngelaTheme.primaryPurple)
                    }

                    // Time
                    MeetingTimePickerView(
                        startHour: $startHour,
                        startMinute: $startMinute,
                        endHour: $endHour,
                        endMinute: $endMinute
                    )

                    // Location
                    MeetingLocationField(
                        location: $location,
                        savedLocations: savedLocations,
                        showSuggestions: $showLocationSuggestions
                    )

                    // Project
                    MeetingFormField("Project (Optional)", icon: "folder.fill") {
                        TextField("e.g. EWG, WTU", text: $projectName)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Attendees
                    MeetingFormField("Attendees (Optional)", icon: "person.2.fill") {
                        TextField("Name1, Name2, Name3", text: $attendeesText)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Meeting Notes
                    MeetingFormField("Meeting Notes", icon: "note.text") {
                        TextEditor(text: $notes)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(AngelaTheme.textPrimary)
                            .scrollContentBackground(.hidden)
                            .padding(10)
                            .frame(minHeight: 200)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(AngelaTheme.textTertiary.opacity(0.3), lineWidth: 1)
                            )

                        Text("Markdown supported: ## headers, - bullets, - [ ] checklists")
                            .font(.system(size: 10))
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                }
                .padding()
            }

            Divider()

            MeetingSheetFooter(
                label: "Save Changes",
                isLoading: isSaving,
                canSubmit: canSave
            ) {
                Task { await saveMeeting() }
            }
        }
        .frame(width: 550, height: 800)
        .background(AngelaTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
        .alert("Meeting Updated", isPresented: $showSuccess) {
            Button("OK") { dismiss(); onUpdated() }
        } message: {
            Text("Meeting has been updated.")
        }
        .task { await loadLocations() }
    }

    // MARK: - Computed Properties

    private var canSave: Bool {
        !title.isEmpty && !location.isEmpty
    }

    // MARK: - Actions

    private func loadLocations() async {
        savedLocations = (try? await databaseService.fetchMeetingLocations()) ?? []
    }

    private func saveMeeting() async {
        isSaving = true

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")

        let attendees: [String]? = attendeesText.isEmpty ? nil : attendeesText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        let request = MeetingUpdateRequest(
            title: title,
            location: location,
            meetingDate: dateFormatter.string(from: selectedDate),
            startTime: String(format: "%02d:%02d", startHour, startMinute),
            endTime: String(format: "%02d:%02d", endHour, endMinute),
            meetingType: meetingType.rawValue,
            attendees: attendees,
            projectName: projectName.isEmpty ? nil : projectName,
            things3Status: status,
            notes: notes.isEmpty ? nil : notes
        )

        do {
            let response = try await databaseService.updateMeeting(meetingId: meeting.id.uuidString, request)
            isSaving = false
            if response.success {
                showSuccess = true
            } else {
                errorMessage = response.error ?? "Unknown error"
                showError = true
            }
        } catch {
            isSaving = false
            errorMessage = error.localizedDescription
            showError = true
        }
    }
}
