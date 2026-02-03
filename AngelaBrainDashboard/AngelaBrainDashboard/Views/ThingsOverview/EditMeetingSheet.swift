//
//  EditMeetingSheet.swift
//  Angela Brain Dashboard
//
//  Sheet for editing an existing meeting with structured sections.
//

import SwiftUI

struct EditMeetingSheet: View {
    let databaseService: DatabaseService
    let meeting: MeetingNote
    let onUpdated: () -> Void
    @Environment(\.dismiss) private var dismiss

    // Basic fields
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

    // Structured note fields
    @State private var agenda: [String]
    @State private var keyPoints: [String]
    @State private var decisionsMade: [String]
    @State private var issuesRisks: [String]
    @State private var nextSteps: [String]
    @State private var personalNotes: String
    @State private var morningNotes: String
    @State private var afternoonNotes: String
    @State private var siteObservations: String

    @State private var isSaving = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSuccess = false

    @State private var savedLocations: [String] = []
    @State private var showLocationSuggestions = false

    // Section accent colors
    private let agendaColor = Color(hex: "3B82F6")       // blue
    private let keyPointsColor = Color(hex: "8B5CF6")     // purple
    private let decisionsColor = Color(hex: "10B981")     // green
    private let issuesColor = Color(hex: "EF4444")        // red
    private let nextStepsColor = Color(hex: "F59E0B")     // orange
    private let notesColor = Color(hex: "6B7280")         // gray
    private let morningColor = Color(hex: "F59E0B")       // orange
    private let afternoonColor = Color(hex: "3B82F6")     // blue
    private let observationsColor = Color(hex: "10B981")  // green

    init(databaseService: DatabaseService, meeting: MeetingNote, onUpdated: @escaping () -> Void) {
        self.databaseService = databaseService
        self.meeting = meeting
        self.onUpdated = onUpdated

        // Pre-fill basic fields
        _title = State(initialValue: meeting.title)
        _location = State(initialValue: meeting.location ?? "")
        _projectName = State(initialValue: meeting.projectName ?? "")
        _attendeesText = State(initialValue: meeting.attendees?.joined(separator: ", ") ?? "")
        _status = State(initialValue: meeting.things3Status)
        _selectedDate = State(initialValue: meeting.meetingDate ?? Date())

        // Determine meeting type from stored value
        switch meeting.meetingType {
        case "site_visit":
            _meetingType = State(initialValue: .siteVisit)
        case "testing":
            _meetingType = State(initialValue: .testing)
        case "bod":
            _meetingType = State(initialValue: .bod)
        default:
            _meetingType = State(initialValue: .standard)
        }

        // Pre-fill structured note fields — parse from raw_notes if structured columns are empty
        let hasStructuredData = (meeting.agenda != nil && !(meeting.agenda?.isEmpty ?? true))
            || (meeting.keyPoints != nil && !(meeting.keyPoints?.isEmpty ?? true))
            || (meeting.decisionsMade != nil && !(meeting.decisionsMade?.isEmpty ?? true))
            || (meeting.nextSteps != nil && !(meeting.nextSteps?.isEmpty ?? true))
            || (meeting.personalNotes != nil && !(meeting.personalNotes?.isEmpty ?? true))
            || (meeting.morningNotes != nil && !(meeting.morningNotes?.isEmpty ?? true))

        if hasStructuredData {
            _agenda = State(initialValue: meeting.agenda ?? [])
            _keyPoints = State(initialValue: meeting.keyPoints ?? [])
            _decisionsMade = State(initialValue: meeting.decisionsMade ?? [])
            _issuesRisks = State(initialValue: meeting.issuesRisks ?? [])
            _nextSteps = State(initialValue: meeting.nextSteps ?? [])
            _personalNotes = State(initialValue: meeting.personalNotes ?? "")
            _morningNotes = State(initialValue: meeting.morningNotes ?? "")
            _afternoonNotes = State(initialValue: meeting.afternoonNotes ?? "")
            _siteObservations = State(initialValue: meeting.siteObservations ?? "")
        } else {
            // Parse raw_notes markdown into structured fields
            let parsed = EditMeetingSheet.parseRawNotes(meeting.rawNotes ?? "")
            _agenda = State(initialValue: parsed.agenda)
            _keyPoints = State(initialValue: parsed.keyPoints)
            _decisionsMade = State(initialValue: parsed.decisionsMade)
            _issuesRisks = State(initialValue: parsed.issuesRisks)
            _nextSteps = State(initialValue: parsed.nextSteps)
            _personalNotes = State(initialValue: parsed.personalNotes)
            _morningNotes = State(initialValue: parsed.morningNotes)
            _afternoonNotes = State(initialValue: parsed.afternoonNotes)
            _siteObservations = State(initialValue: parsed.siteObservations)
        }

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

                    // --- Structured Meeting Notes ---
                    Divider().padding(.vertical, 4)

                    Text("Meeting Notes")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(AngelaTheme.textPrimary)

                    structuredNoteSections
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
        .frame(width: 550, height: 900)
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

    // MARK: - Structured Note Sections (per meeting type)

    @ViewBuilder
    private var structuredNoteSections: some View {
        switch meetingType {
        case .standard:
            standardSections
        case .siteVisit:
            siteVisitSections
        case .testing:
            testingSections
        case .bod:
            bodSections
        }
    }

    private var standardSections: some View {
        VStack(alignment: .leading, spacing: 14) {
            BulletListEditor(
                label: "Agenda", icon: "list.clipboard.fill",
                placeholder: "Add agenda item...",
                accentColor: agendaColor, items: $agenda
            )
            BulletListEditor(
                label: "Key Points", icon: "key.fill",
                placeholder: "Add key point...",
                accentColor: keyPointsColor, items: $keyPoints
            )
            BulletListEditor(
                label: "Decisions Made", icon: "checkmark.seal.fill",
                placeholder: "Add decision...",
                accentColor: decisionsColor, items: $decisionsMade
            )
            BulletListEditor(
                label: "Issues / Risks", icon: "exclamationmark.triangle.fill",
                placeholder: "Add issue or risk...",
                accentColor: issuesColor, items: $issuesRisks
            )
            BulletListEditor(
                label: "Next Steps", icon: "arrow.right.circle.fill",
                placeholder: "Add next step...",
                accentColor: nextStepsColor, items: $nextSteps
            )
            NotesSectionCard(
                label: "Personal Notes", icon: "note.text",
                placeholder: "Private notes...",
                accentColor: notesColor, text: $personalNotes
            )
        }
    }

    private var siteVisitSections: some View {
        VStack(alignment: .leading, spacing: 14) {
            NotesSectionCard(
                label: "Morning Notes", icon: "sunrise.fill",
                placeholder: "Morning observations...",
                accentColor: morningColor, text: $morningNotes
            )
            NotesSectionCard(
                label: "Afternoon Notes", icon: "sunset.fill",
                placeholder: "Afternoon observations...",
                accentColor: afternoonColor, text: $afternoonNotes
            )
            NotesSectionCard(
                label: "Site Observations", icon: "eye.fill",
                placeholder: "Key findings from site...",
                accentColor: observationsColor, text: $siteObservations
            )
            BulletListEditor(
                label: "Key Points", icon: "key.fill",
                placeholder: "Add key point...",
                accentColor: keyPointsColor, items: $keyPoints
            )
            BulletListEditor(
                label: "Next Steps", icon: "arrow.right.circle.fill",
                placeholder: "Add next step...",
                accentColor: nextStepsColor, items: $nextSteps
            )
        }
    }

    private var testingSections: some View {
        VStack(alignment: .leading, spacing: 14) {
            BulletListEditor(
                label: "Test Scope", icon: "scope",
                placeholder: "Add test scope item...",
                accentColor: agendaColor, items: $agenda
            )
            BulletListEditor(
                label: "Results", icon: "chart.bar.fill",
                placeholder: "Add test result...",
                accentColor: keyPointsColor, items: $keyPoints
            )
            BulletListEditor(
                label: "Issues / Risks", icon: "exclamationmark.triangle.fill",
                placeholder: "Add issue found...",
                accentColor: issuesColor, items: $issuesRisks
            )
            BulletListEditor(
                label: "Next Steps", icon: "arrow.right.circle.fill",
                placeholder: "Add next step...",
                accentColor: nextStepsColor, items: $nextSteps
            )
        }
    }

    private var bodSections: some View {
        VStack(alignment: .leading, spacing: 14) {
            BulletListEditor(
                label: "Agenda", icon: "list.clipboard.fill",
                placeholder: "Add agenda item...",
                accentColor: agendaColor, items: $agenda
            )
            BulletListEditor(
                label: "Resolutions", icon: "checkmark.seal.fill",
                placeholder: "Add resolution...",
                accentColor: decisionsColor, items: $decisionsMade
            )
            BulletListEditor(
                label: "Action Items", icon: "arrow.right.circle.fill",
                placeholder: "Add action item...",
                accentColor: nextStepsColor, items: $nextSteps
            )
            NotesSectionCard(
                label: "Personal Notes", icon: "note.text",
                placeholder: "Private notes...",
                accentColor: notesColor, text: $personalNotes
            )
        }
    }

    // MARK: - Computed Properties

    private var canSave: Bool {
        !title.isEmpty && !location.isEmpty
    }

    // MARK: - Actions

    private func loadLocations() async {
        savedLocations = (try? await databaseService.fetchMeetingLocations()) ?? []
    }

    private func generateRawNotes() -> String {
        var sections: [String] = []

        func addList(_ header: String, _ items: [String]) {
            let nonEmpty = items.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
            guard !nonEmpty.isEmpty else { return }
            let lines = nonEmpty.map { item -> String in
                // Detect indent level from leading spaces
                let leadingSpaces = item.prefix(while: { $0 == " " }).count
                let level = leadingSpaces / 2
                let text = String(item.drop(while: { $0 == " " }))
                let mdIndent = String(repeating: "  ", count: level)
                return "\(mdIndent)- \(text)"
            }
            sections.append("## \(header)\n" + lines.joined(separator: "\n"))
        }

        func addText(_ header: String, _ text: String) {
            let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmed.isEmpty else { return }
            sections.append("## \(header)\n\(trimmed)")
        }

        switch meetingType {
        case .standard:
            addList("Agenda", agenda)
            addList("Key Points", keyPoints)
            addList("Decisions Made", decisionsMade)
            addList("Issues / Risks", issuesRisks)
            addList("Next Steps", nextSteps)
            addText("Personal Notes", personalNotes)
        case .siteVisit:
            addText("Morning Notes", morningNotes)
            addText("Afternoon Notes", afternoonNotes)
            addText("Site Observations", siteObservations)
            addList("Key Points", keyPoints)
            addList("Next Steps", nextSteps)
        case .testing:
            addList("Test Scope", agenda)
            addList("Results", keyPoints)
            addList("Issues / Risks", issuesRisks)
            addList("Next Steps", nextSteps)
        case .bod:
            addList("Agenda", agenda)
            addList("Resolutions", decisionsMade)
            addList("Action Items", nextSteps)
            addText("Personal Notes", personalNotes)
        }

        return sections.joined(separator: "\n\n")
    }

    // MARK: - Raw Notes Parser

    struct ParsedNotes {
        var agenda: [String] = []
        var keyPoints: [String] = []
        var decisionsMade: [String] = []
        var issuesRisks: [String] = []
        var nextSteps: [String] = []
        var personalNotes: String = ""
        var morningNotes: String = ""
        var afternoonNotes: String = ""
        var siteObservations: String = ""
    }

    /// Parse raw_notes markdown into structured fields.
    /// Handles headers like "## 📋 วาระการประชุม", "## Key Points", etc.
    static func parseRawNotes(_ rawNotes: String) -> ParsedNotes {
        var result = ParsedNotes()
        guard !rawNotes.isEmpty else { return result }

        // Split by ## headers
        let lines = rawNotes.components(separatedBy: "\n")
        var currentSection = ""
        var currentLines: [String] = []

        func flushSection() {
            guard !currentSection.isEmpty else { return }
            let key = normalizeHeader(currentSection)
            let bullets = extractBullets(from: currentLines)
            let textBlock = currentLines
                .filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
                .joined(separator: "\n")
                .trimmingCharacters(in: .whitespacesAndNewlines)

            switch key {
            case "agenda", "วาระ", "วาระการประชุม", "formal_agenda", "test_scope":
                result.agenda = bullets.isEmpty ? splitTextToItems(textBlock) : bullets
            case "key_points", "key_findings", "results", "test_results":
                result.keyPoints = bullets.isEmpty ? splitTextToItems(textBlock) : bullets
            case "decisions", "decisions_made", "resolutions":
                result.decisionsMade = bullets.isEmpty ? splitTextToItems(textBlock) : bullets
            case "issues", "issues_risks", "issues_found":
                result.issuesRisks = bullets.isEmpty ? splitTextToItems(textBlock) : bullets
            case "next_steps", "action_items":
                result.nextSteps = bullets.isEmpty ? splitTextToItems(textBlock) : bullets
            case "notes", "personal_notes":
                result.personalNotes = textBlock
            case "morning_notes", "morning":
                result.morningNotes = textBlock
            case "afternoon_notes", "afternoon":
                result.afternoonNotes = textBlock
            case "site_observations", "observations":
                result.siteObservations = textBlock
            case "ผู้เข้าร่วม", "attendees":
                break // skip — attendees handled separately
            default:
                break
            }
        }

        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)

            if trimmed.hasPrefix("## ") || trimmed.hasPrefix("# ") && !trimmed.hasPrefix("# ") {
                // Hit a new ## section
                flushSection()
                currentSection = String(trimmed.drop(while: { $0 == "#" || $0 == " " }))
                currentLines = []
            } else if trimmed.hasPrefix("# ") {
                // Top-level header (meeting title) — skip
                flushSection()
                currentSection = ""
                currentLines = []
            } else if trimmed == "---" {
                // Divider — skip
                continue
            } else {
                currentLines.append(line)
            }
        }
        flushSection()

        return result
    }

    /// Normalize a header string to a key: strip emojis, lowercase, replace spaces with _
    private static func normalizeHeader(_ header: String) -> String {
        // Remove emoji characters and common prefixes
        let stripped = header.unicodeScalars.filter { scalar in
            // Keep only letters, digits, spaces, underscores
            scalar.properties.isAlphabetic || scalar.properties.isWhitespace
                || scalar.value == 0x5F // underscore
                || (scalar.value >= 0x30 && scalar.value <= 0x39) // digits
                || scalar.value >= 0x0E00 && scalar.value <= 0x0E7F // Thai
        }
        let clean = String(String.UnicodeScalarView(stripped))
            .trimmingCharacters(in: .whitespaces)
            .lowercased()
            .replacingOccurrences(of: " ", with: "_")

        // Map known Thai/English headers to canonical keys
        let mappings: [String: String] = [
            "วาระการประชุม": "agenda",
            "วาระ": "agenda",
            "formal_agenda": "agenda",
            "agenda": "agenda",
            "test_scope": "test_scope",
            "key_points": "key_points",
            "key_findings": "key_findings",
            "results": "results",
            "test_results": "test_results",
            "decisions_made": "decisions_made",
            "decisions": "decisions",
            "resolutions": "resolutions",
            "issues_/_risks": "issues_risks",
            "issues_risks": "issues_risks",
            "issues_found": "issues_found",
            "issues": "issues",
            "next_steps": "next_steps",
            "action_items": "action_items",
            "notes": "notes",
            "personal_notes": "personal_notes",
            "morning_notes": "morning_notes",
            "morning": "morning",
            "afternoon_notes": "afternoon_notes",
            "afternoon": "afternoon",
            "site_observations": "site_observations",
            "observations": "observations",
            "ผู้เข้าร่วม": "ผู้เข้าร่วม",
            "attendees": "attendees",
        ]

        return mappings[clean] ?? clean
    }

    /// Extract bullet items from lines, preserving indent level via leading spaces.
    /// "- top" → "top", "  - sub" → "  sub", "    - deep" → "    deep"
    private static func extractBullets(from lines: [String]) -> [String] {
        var items: [String] = []
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            // Compute indent: count leading spaces before the bullet marker
            let leadingSpaces = line.prefix(while: { $0 == " " }).count
            let indentLevel = leadingSpaces / 2
            let prefix = String(repeating: "  ", count: indentLevel)

            if trimmed.hasPrefix("- ") {
                let text = String(trimmed.dropFirst(2)).trimmingCharacters(in: .whitespaces)
                if !text.isEmpty { items.append(prefix + text) }
            } else if trimmed.hasPrefix("* ") {
                let text = String(trimmed.dropFirst(2)).trimmingCharacters(in: .whitespaces)
                if !text.isEmpty { items.append(prefix + text) }
            } else if let dotIndex = trimmed.firstIndex(of: "."),
                      trimmed[trimmed.startIndex..<dotIndex].allSatisfy({ $0.isNumber }) {
                let afterDot = trimmed[trimmed.index(after: dotIndex)...]
                let text = String(afterDot).trimmingCharacters(in: .whitespaces)
                if !text.isEmpty { items.append(prefix + text) }
            }
        }
        return items
    }

    /// Split a text block into items by newlines (fallback when no bullets found)
    private static func splitTextToItems(_ text: String) -> [String] {
        guard !text.isEmpty else { return [] }
        return text.components(separatedBy: "\n")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty && $0 != "-" }
    }

    private func saveMeeting() async {
        isSaving = true

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")

        let attendees: [String]? = attendeesText.isEmpty ? nil : attendeesText.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        // Filter out empty strings
        let cleanAgenda = agenda.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
        let cleanKeyPoints = keyPoints.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
        let cleanDecisions = decisionsMade.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
        let cleanIssues = issuesRisks.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
        let cleanNextSteps = nextSteps.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }

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
            notes: generateRawNotes(),
            agenda: cleanAgenda.isEmpty ? nil : cleanAgenda,
            keyPoints: cleanKeyPoints.isEmpty ? nil : cleanKeyPoints,
            decisionsMade: cleanDecisions.isEmpty ? nil : cleanDecisions,
            issuesRisks: cleanIssues.isEmpty ? nil : cleanIssues,
            nextSteps: cleanNextSteps.isEmpty ? nil : cleanNextSteps,
            personalNotes: personalNotes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : personalNotes,
            morningNotes: morningNotes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : morningNotes,
            afternoonNotes: afternoonNotes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : afternoonNotes,
            siteObservations: siteObservations.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : siteObservations
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
