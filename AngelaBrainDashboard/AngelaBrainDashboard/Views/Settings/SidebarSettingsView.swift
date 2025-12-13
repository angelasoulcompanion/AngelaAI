//
//  SidebarSettingsView.swift
//  Angela Brain Dashboard
//
//  💜 Configure Sidebar Menu Visibility 💜
//

import SwiftUI

struct SidebarSettingsView: View {
    @ObservedObject var settingsManager = SidebarSettingsManager.shared
    @Environment(\.dismiss) var dismiss

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header
                header

                // Settings content
                ScrollView {
                    VStack(spacing: AngelaTheme.spacing) {
                        ForEach(NavigationGroup.allCases, id: \.self) { group in
                            groupSettingsCard(for: group)
                        }

                        // Reset button
                        resetButton
                            .padding(.top, AngelaTheme.spacing)
                    }
                    .padding(AngelaTheme.spacing)
                }
            }
        }
        .frame(width: 500, height: 600)
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("Sidebar Settings")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Configure which menus and items to show")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 24))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
            .buttonStyle(.plain)
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Group Settings Card

    private func groupSettingsCard(for group: NavigationGroup) -> some View {
        VStack(alignment: .leading, spacing: AngelaTheme.smallSpacing) {
            // Group toggle header
            HStack {
                Image(systemName: group.icon)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .frame(width: 24)

                Text(group.rawValue)
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                // Group visibility toggle
                Toggle("", isOn: Binding(
                    get: { settingsManager.isGroupVisible(group) },
                    set: { settingsManager.setGroupVisible(group, visible: $0) }
                ))
                .toggleStyle(SwitchToggleStyle(tint: AngelaTheme.primaryPurple))
                .labelsHidden()
            }
            .padding(.bottom, AngelaTheme.smallSpacing)

            // Item toggles (only if group is visible)
            if settingsManager.isGroupVisible(group) {
                VStack(spacing: 8) {
                    ForEach(group.items, id: \.self) { item in
                        itemToggleRow(for: item)
                    }
                }
                .padding(.leading, 32)
            } else {
                Text("Group hidden - items not shown")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)
                    .italic()
                    .padding(.leading, 32)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Item Toggle Row

    private func itemToggleRow(for item: NavigationItem) -> some View {
        HStack {
            Image(systemName: item.icon)
                .font(.system(size: 14))
                .foregroundColor(settingsManager.isItemVisible(item) ? AngelaTheme.textSecondary : AngelaTheme.textTertiary)
                .frame(width: 20)

            Text(item.rawValue)
                .font(AngelaTheme.body())
                .foregroundColor(settingsManager.isItemVisible(item) ? AngelaTheme.textPrimary : AngelaTheme.textTertiary)

            Spacer()

            Toggle("", isOn: Binding(
                get: { settingsManager.isItemVisible(item) },
                set: { settingsManager.setItemVisible(item, visible: $0) }
            ))
            .toggleStyle(SwitchToggleStyle(tint: AngelaTheme.primaryPurple))
            .labelsHidden()
        }
        .padding(.vertical, 4)
    }

    // MARK: - Reset Button

    private var resetButton: some View {
        Button {
            withAnimation {
                settingsManager.resetToDefault()
            }
        } label: {
            HStack {
                Image(systemName: "arrow.counterclockwise")
                Text("Reset to Default")
            }
            .font(AngelaTheme.body())
            .foregroundColor(AngelaTheme.warningOrange)
            .padding(.horizontal, AngelaTheme.spacing)
            .padding(.vertical, 10)
            .background(AngelaTheme.warningOrange.opacity(0.1))
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

struct SidebarSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SidebarSettingsView()
    }
}
