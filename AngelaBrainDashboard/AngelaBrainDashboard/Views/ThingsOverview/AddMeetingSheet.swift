//
//  AddMeetingSheet.swift
//  Angela Brain Dashboard
//
//  Sheet for creating a new meeting.
//

import SwiftUI

struct AddMeetingSheet: View {
    let databaseService: DatabaseService
    let onCreated: () -> Void
    @Environment(\.dismiss) private var dismiss

    // Form State
    @State private var title = ""
    @State private var meetingType: MeetingType = .standard
    @State private var selectedDate = Date()
    @State private var startHour = 9
    @State private var startMinute = 0
    @State private var endHour = 10
    @State private var endMinute = 0
    @State private var location = ""
    @State private var projectName = ""
    @State private var attendeesText = ""

    @State private var isCreating = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSuccess = false

    // Location suggestions
    @State private var savedLocations: [String] = []
    @State private var showLocationSuggestions = false

    var body: some View {
        VStack(spacing: 0) {
            MeetingSheetHeader(title: "Create Meeting", dismiss: dismiss)

            Divider()

            // Form
            ScrollView {
                VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
                    // Title
                    MeetingFormField("Meeting Title", icon: "doc.text.fill") {
                        TextField("e.g. SRT + CI Meeting", text: $title)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
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

                    // Project (Optional)
                    MeetingFormField("Project (Optional)", icon: "folder.fill") {
                        TextField("e.g. EWG, WTU", text: $projectName)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Attendees (Optional)
                    MeetingFormField("Attendees (Optional)", icon: "person.2.fill") {
                        TextField("Name1, Name2, Name3", text: $attendeesText)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Template Preview
                    MeetingFormField("Template Sections", icon: "doc.badge.gearshape.fill") {
                        HStack(spacing: 4) {
                            ForEach(meetingType.templateSections, id: \.self) { section in
                                Text(section)
                                    .font(.system(size: 9))
                                    .foregroundColor(AngelaTheme.primaryPurple)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 3)
                                    .background(AngelaTheme.primaryPurple.opacity(0.12))
                                    .cornerRadius(4)
                            }
                        }
                    }
                }
                .padding()
            }

            Divider()

            MeetingSheetFooter(
                label: "Create Meeting",
                isLoading: isCreating,
                canSubmit: canCreate
            ) {
                Task { await createMeeting() }
            }
        }
        .frame(width: 500, height: 650)
        .background(AngelaTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
        .alert("Meeting Created", isPresented: $showSuccess) {
            Button("OK") {
                dismiss()
                onCreated()
            }
        } message: {
            Text("Meeting has been created in Things3 and database.")
        }
        .task {
            await loadLocations()
        }
    }

    // MARK: - Computed Properties

    private var canCreate: Bool {
        !title.isEmpty && !location.isEmpty
    }

    // MARK: - Actions

    private func loadLocations() async {
        do {
            savedLocations = try await databaseService.fetchMeetingLocations()
        } catch {
            print("Failed to load locations: \(error)")
        }
    }

    private func createMeeting() async {
        isCreating = true

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")
        let dateStr = dateFormatter.string(from: selectedDate)

        let startStr = String(format: "%02d:%02d", startHour, startMinute)
        let endStr = String(format: "%02d:%02d", endHour, endMinute)

        let attendees: [String]? = attendeesText.isEmpty ? nil : attendeesText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        let request = MeetingCreateRequest(
            title: title,
            location: location,
            meetingDate: dateStr,
            startTime: startStr,
            endTime: endStr,
            meetingType: meetingType.rawValue,
            attendees: attendees,
            projectName: projectName.isEmpty ? nil : projectName
        )

        do {
            let response = try await databaseService.createMeeting(request)
            isCreating = false

            if response.success {
                showSuccess = true
            } else {
                errorMessage = response.error ?? "Unknown error"
                showError = true
            }
        } catch {
            isCreating = false
            errorMessage = error.localizedDescription
            showError = true
        }
    }
}
