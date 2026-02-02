//
//  EditActionItemSheet.swift
//  Angela Brain Dashboard
//
//  Sheet for editing an existing action item.
//

import SwiftUI

struct EditActionItemSheet: View {
    let databaseService: DatabaseService
    let actionItem: MeetingActionItem
    let onUpdated: () -> Void
    @Environment(\.dismiss) private var dismiss

    @State private var actionText: String
    @State private var assignee: String
    @State private var hasDueDate: Bool
    @State private var dueDate: Date
    @State private var priority: ActionPriority
    @State private var isCompleted: Bool

    @State private var isSaving = false
    @State private var showError = false
    @State private var errorMessage = ""

    init(databaseService: DatabaseService, actionItem: MeetingActionItem, onUpdated: @escaping () -> Void) {
        self.databaseService = databaseService
        self.actionItem = actionItem
        self.onUpdated = onUpdated

        _actionText = State(initialValue: actionItem.actionText)
        _assignee = State(initialValue: actionItem.assignee ?? "")
        _hasDueDate = State(initialValue: actionItem.dueDate != nil)
        _dueDate = State(initialValue: actionItem.dueDate ?? Date())
        _priority = State(initialValue: ActionPriority.from(actionItem.priority))
        _isCompleted = State(initialValue: actionItem.isCompleted)
    }

    var body: some View {
        VStack(spacing: 0) {
            MeetingSheetHeader(title: "Edit Action Item", dismiss: dismiss)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: AngelaTheme.spacing) {
                    // Action text
                    MeetingFormField("Action", icon: "text.alignleft") {
                        TextField("What needs to be done?", text: $actionText)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Priority picker (3 buttons)
                    MeetingFormField("Priority", icon: "flag.fill") {
                        HStack(spacing: 8) {
                            ForEach(ActionPriority.allCases, id: \.rawValue) { p in
                                Button {
                                    priority = p
                                } label: {
                                    HStack(spacing: 4) {
                                        Image(systemName: p.icon)
                                            .font(.system(size: 10))
                                        Text(p.label)
                                            .font(.system(size: 11, weight: .medium))
                                    }
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(priority == p ? Color(hex: p.color) : AngelaTheme.backgroundLight)
                                    .foregroundColor(priority == p ? .white : AngelaTheme.textPrimary)
                                    .cornerRadius(6)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Assignee
                    MeetingFormField("Assignee (Optional)", icon: "person.fill") {
                        TextField("Who is responsible?", text: $assignee)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(AngelaTheme.backgroundLight)
                            .cornerRadius(8)
                    }

                    // Due date
                    MeetingFormField("Due Date", icon: "calendar") {
                        VStack(alignment: .leading, spacing: 6) {
                            Toggle("Set due date", isOn: $hasDueDate)
                                .toggleStyle(.switch)
                                .font(.system(size: 12))

                            if hasDueDate {
                                DatePicker("", selection: $dueDate, displayedComponents: .date)
                                    .datePickerStyle(.compact)
                                    .labelsHidden()
                            }
                        }
                    }

                    // Status toggle
                    MeetingFormField("Status", icon: "circle.badge.checkmark.fill") {
                        HStack(spacing: 8) {
                            Button {
                                isCompleted = false
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "circle")
                                        .font(.system(size: 10))
                                    Text("Open")
                                        .font(.system(size: 11, weight: .medium))
                                }
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(!isCompleted ? Color(hex: "F59E0B") : AngelaTheme.backgroundLight)
                                .foregroundColor(!isCompleted ? .white : AngelaTheme.textPrimary)
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)

                            Button {
                                isCompleted = true
                            } label: {
                                HStack(spacing: 4) {
                                    Image(systemName: "checkmark.circle.fill")
                                        .font(.system(size: 10))
                                    Text("Completed")
                                        .font(.system(size: 11, weight: .medium))
                                }
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(isCompleted ? Color(hex: "10B981") : AngelaTheme.backgroundLight)
                                .foregroundColor(isCompleted ? .white : AngelaTheme.textPrimary)
                                .cornerRadius(6)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding()
            }

            Divider()

            MeetingSheetFooter(
                label: "Save Changes",
                isLoading: isSaving,
                canSubmit: !actionText.trimmingCharacters(in: .whitespaces).isEmpty
            ) {
                Task { await saveItem() }
            }
        }
        .frame(width: 450, height: 500)
        .background(AngelaTheme.backgroundDark)
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMessage)
        }
    }

    private func saveItem() async {
        isSaving = true

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.calendar = Calendar(identifier: .gregorian)
        dateFormatter.locale = Locale(identifier: "en_US_POSIX")

        let request = ActionItemUpdateRequest(
            actionText: actionText.trimmingCharacters(in: .whitespaces),
            assignee: assignee.isEmpty ? nil : assignee,
            dueDate: hasDueDate ? dateFormatter.string(from: dueDate) : nil,
            priority: priority.rawValue,
            isCompleted: isCompleted
        )

        do {
            let response = try await databaseService.updateActionItem(
                actionId: actionItem.id.uuidString, request
            )
            isSaving = false
            if response.success {
                dismiss()
                onUpdated()
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
