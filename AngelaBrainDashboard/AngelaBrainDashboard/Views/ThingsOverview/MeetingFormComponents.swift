//
//  MeetingFormComponents.swift
//  Angela Brain Dashboard
//
//  Shared components for Add/Edit meeting sheets.
//

import SwiftUI

// MARK: - Meeting Type Enum (shared)

enum MeetingType: String, CaseIterable {
    case standard = "standard"
    case siteVisit = "site_visit"
    case testing = "testing"
    case bod = "bod"

    var displayName: String {
        switch self {
        case .standard: return "Standard"
        case .siteVisit: return "Site Visit"
        case .testing: return "Testing"
        case .bod: return "BOD"
        }
    }

    var icon: String {
        switch self {
        case .standard: return "person.3.fill"
        case .siteVisit: return "building.2.fill"
        case .testing: return "checkmark.seal.fill"
        case .bod: return "crown.fill"
        }
    }

    var templateSections: [String] {
        switch self {
        case .standard:
            return ["วาระ", "ผู้เข้าร่วม", "Key Points", "Next Steps"]
        case .siteVisit:
            return ["Morning", "Afternoon", "Observations", "Next Steps"]
        case .testing:
            return ["Test Scope", "Results", "Issues", "Next Steps"]
        case .bod:
            return ["Agenda", "Resolutions", "Actions", "Notes"]
        }
    }
}

// MARK: - Thai Date Helper

func thaiDateString(for date: Date) -> String {
    let formatter = DateFormatter()
    formatter.locale = Locale(identifier: "th_TH")
    formatter.calendar = Calendar(identifier: .buddhist)
    formatter.dateFormat = "วันEEEEที่ d MMMM yyyy"
    return formatter.string(from: date)
}

// MARK: - Meeting Form Field

struct MeetingFormField<Content: View>: View {
    let label: String
    let icon: String
    let content: () -> Content

    init(_ label: String, icon: String, @ViewBuilder content: @escaping () -> Content) {
        self.label = label
        self.icon = icon
        self.content = content
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Label(label, systemImage: icon)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
            content()
        }
    }
}

// MARK: - Meeting Time Picker

struct MeetingTimePickerView: View {
    @Binding var startHour: Int
    @Binding var startMinute: Int
    @Binding var endHour: Int
    @Binding var endMinute: Int

    var body: some View {
        MeetingFormField("Time", icon: "clock.fill") {
            HStack(spacing: 8) {
                // Start time
                HStack(spacing: 4) {
                    Picker("", selection: $startHour) {
                        ForEach(0..<24, id: \.self) { hour in
                            Text(String(format: "%02d", hour)).tag(hour)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 60)

                    Text(":")
                        .foregroundColor(AngelaTheme.textSecondary)

                    Picker("", selection: $startMinute) {
                        ForEach([0, 15, 30, 45], id: \.self) { min in
                            Text(String(format: "%02d", min)).tag(min)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 60)
                }

                Text("to")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                // End time
                HStack(spacing: 4) {
                    Picker("", selection: $endHour) {
                        ForEach(0..<24, id: \.self) { hour in
                            Text(String(format: "%02d", hour)).tag(hour)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 60)

                    Text(":")
                        .foregroundColor(AngelaTheme.textSecondary)

                    Picker("", selection: $endMinute) {
                        ForEach([0, 15, 30, 45], id: \.self) { min in
                            Text(String(format: "%02d", min)).tag(min)
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(width: 60)
                }
            }
        }
    }
}

// MARK: - Meeting Location Field (with suggestions dropdown)

struct MeetingLocationField: View {
    @Binding var location: String
    let savedLocations: [String]
    @Binding var showSuggestions: Bool

    private var filteredLocations: [String] {
        if location.isEmpty {
            return savedLocations
        }
        let filtered = savedLocations.filter { $0.localizedCaseInsensitiveContains(location) }
        return filtered.isEmpty ? savedLocations : filtered
    }

    var body: some View {
        MeetingFormField("Location", icon: "mappin.circle.fill") {
            VStack(spacing: 0) {
                HStack {
                    TextField("e.g. การรถไฟแห่งประเทศไทย", text: $location)
                        .textFieldStyle(.plain)

                    if !savedLocations.isEmpty {
                        Button {
                            showSuggestions.toggle()
                        } label: {
                            Image(systemName: showSuggestions ? "chevron.up" : "chevron.down")
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(10)
                .background(AngelaTheme.backgroundLight)
                .cornerRadius(8)

                if showSuggestions && !savedLocations.isEmpty {
                    VStack(spacing: 0) {
                        ForEach(filteredLocations, id: \.self) { loc in
                            Button {
                                location = loc
                                showSuggestions = false
                            } label: {
                                HStack {
                                    Image(systemName: "mappin")
                                        .font(.system(size: 10))
                                        .foregroundColor(AngelaTheme.primaryPurple)
                                    Text(loc)
                                        .font(.system(size: 12))
                                        .foregroundColor(AngelaTheme.textPrimary)
                                    Spacer()
                                }
                                .padding(.horizontal, 10)
                                .padding(.vertical, 8)
                            }
                            .buttonStyle(.plain)

                            if loc != filteredLocations.last {
                                Divider().opacity(0.3)
                            }
                        }
                    }
                    .background(AngelaTheme.backgroundLight.opacity(0.8))
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
                    )
                }
            }
        }
    }
}

// MARK: - Meeting Type Picker

struct MeetingTypePicker: View {
    @Binding var meetingType: MeetingType

    var body: some View {
        MeetingFormField("Meeting Type", icon: "tag.fill") {
            HStack(spacing: 8) {
                ForEach(MeetingType.allCases, id: \.self) { type in
                    Button {
                        meetingType = type
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: type.icon)
                                .font(.system(size: 10))
                            Text(type.displayName)
                                .font(.system(size: 11, weight: .medium))
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(meetingType == type ? AngelaTheme.primaryPurple : AngelaTheme.backgroundLight)
                        .foregroundColor(meetingType == type ? .white : AngelaTheme.textPrimary)
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

// MARK: - Sheet Header

struct MeetingSheetHeader: View {
    let title: String
    let dismiss: DismissAction

    var body: some View {
        HStack {
            Text(title)
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            Spacer()

            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .frame(width: 28, height: 28)
                    .background(AngelaTheme.backgroundLight)
                    .cornerRadius(6)
            }
            .buttonStyle(.plain)
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
    }
}

// MARK: - Sheet Footer Button

struct MeetingSheetFooter: View {
    let label: String
    let isLoading: Bool
    let canSubmit: Bool
    let action: () -> Void

    var body: some View {
        HStack {
            Spacer()

            Button {
                action()
            } label: {
                HStack(spacing: 6) {
                    if isLoading {
                        ProgressView()
                            .scaleEffect(0.7)
                    } else {
                        Image(systemName: "checkmark")
                    }
                    Text(label)
                }
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(canSubmit ? AngelaTheme.primaryPurple : Color.gray)
                .cornerRadius(8)
            }
            .buttonStyle(.plain)
            .disabled(!canSubmit || isLoading)
        }
        .padding()
        .background(AngelaTheme.backgroundLight)
    }
}
