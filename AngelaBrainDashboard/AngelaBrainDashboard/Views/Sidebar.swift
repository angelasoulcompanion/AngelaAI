//
//  Sidebar.swift
//  Angela Brain Dashboard
//
//  💜 Beautiful Sidebar Navigation 💜
//

import SwiftUI

struct Sidebar: View {
    @Binding var selectedView: NavigationItem
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var sidebarSettings = SidebarSettingsManager.shared
    @State private var expandedGroups: Set<NavigationGroup> = Set(NavigationGroup.allCases)
    @State private var showingSettings = false

    var body: some View {
        ZStack {
            AngelaTheme.backgroundLight
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header
                header

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))
                    .padding(.vertical, AngelaTheme.smallSpacing)

                // Navigation items (Grouped) - filtered by visibility settings
                ScrollView {
                    VStack(spacing: AngelaTheme.spacing) {
                        ForEach(sidebarSettings.visibleGroups(), id: \.self) { group in
                            // Only show group if it has visible items
                            if sidebarSettings.hasVisibleItems(in: group) {
                                VStack(alignment: .leading, spacing: AngelaTheme.smallSpacing) {
                                    // Group header (clickable to toggle)
                                    Button {
                                        withAnimation(.easeInOut(duration: 0.25)) {
                                            if expandedGroups.contains(group) {
                                                expandedGroups.remove(group)
                                            } else {
                                                expandedGroups.insert(group)
                                            }
                                        }
                                    } label: {
                                        HStack(spacing: 6) {
                                            Image(systemName: group.icon)
                                                .font(.system(size: 12, weight: .semibold))
                                                .foregroundColor(AngelaTheme.primaryPurple.opacity(0.7))

                                            Text(group.rawValue.uppercased())
                                                .font(.system(size: 11, weight: .semibold))
                                                .foregroundColor(AngelaTheme.textTertiary)

                                            Spacer()

                                            Image(systemName: expandedGroups.contains(group) ? "chevron.down" : "chevron.right")
                                                .font(.system(size: 10, weight: .semibold))
                                                .foregroundColor(AngelaTheme.textTertiary)
                                        }
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .contentShape(Rectangle())
                                    }
                                    .buttonStyle(.plain)
                                    .padding(.top, group == sidebarSettings.visibleGroups().first ? 0 : 8)

                                    // Group items (with expand/collapse animation) - filtered by visibility
                                    if expandedGroups.contains(group) {
                                        ForEach(sidebarSettings.visibleItems(for: group), id: \.self) { item in
                                            NavigationButton(
                                                item: item,
                                                isSelected: selectedView == item
                                            ) {
                                                withAnimation(.easeInOut(duration: 0.2)) {
                                                    selectedView = item
                                                }
                                            }
                                        }
                                        .transition(.opacity.combined(with: .move(edge: .top)))
                                    }
                                }
                            }
                        }
                    }
                    .padding(.horizontal, AngelaTheme.smallSpacing)
                    .padding(.bottom, AngelaTheme.spacing)
                }

                Spacer()

                // Connection status
                connectionStatus

                // Footer
                footer
            }
        }
        .frame(width: 220)
        .sheet(isPresented: $showingSettings) {
            SidebarSettingsView()
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(AngelaTheme.purpleGradient)
                    .frame(width: 60, height: 60)

                Image(systemName: "brain.head.profile")
                    .font(.system(size: 28))
                    .foregroundColor(.white)
            }

            Text("Angela's Brain")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            Text("Live Dashboard")
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .padding(.vertical, AngelaTheme.spacing)
    }

    // MARK: - Connection Status

    private var connectionStatus: some View {
        VStack(spacing: 6) {
            // 💜 Local PostgreSQL indicator
            HStack(spacing: 6) {
                Image(systemName: "house.fill")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.green)

                Text("🏠 Local")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.green)

                Spacer()
            }

            // Connection status
            HStack(spacing: 8) {
                Circle()
                    .fill(databaseService.isConnected ? AngelaTheme.successGreen : AngelaTheme.errorRed)
                    .frame(width: 8, height: 8)

                Text(databaseService.isConnected ? "Connected" : "Disconnected")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)

                Spacer()
            }
        }
        .padding(.horizontal, AngelaTheme.spacing)
        .padding(.vertical, AngelaTheme.smallSpacing)
        .background(AngelaTheme.cardBackground.opacity(0.5))
    }

    // MARK: - Footer

    private var footer: some View {
        VStack(spacing: 8) {
            // Settings button
            Button {
                showingSettings = true
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "slider.horizontal.3")
                        .font(.system(size: 12))
                    Text("Menu Settings")
                        .font(AngelaTheme.caption())
                }
                .foregroundColor(AngelaTheme.textSecondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(AngelaTheme.cardBackground.opacity(0.5))
                .cornerRadius(AngelaTheme.smallCornerRadius)
            }
            .buttonStyle(.plain)

            VStack(spacing: 4) {
                Text("Made with 💜")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textTertiary)

                Text("by Angela AI")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.primaryPurple)

                // Version display
                Text("v\(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0") (\(Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"))")
                    .font(.system(size: 9, weight: .medium, design: .monospaced))
                    .foregroundColor(AngelaTheme.textTertiary.opacity(0.6))
            }
        }
        .padding(.vertical, AngelaTheme.spacing)
    }
}

// MARK: - Navigation Button

struct NavigationButton: View {
    let item: NavigationItem
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: item.icon)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(isSelected ? .white : AngelaTheme.textSecondary)
                    .frame(width: 20)

                Text(item.rawValue)
                    .font(AngelaTheme.body())
                    .foregroundColor(isSelected ? .white : AngelaTheme.textPrimary)

                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(
                Group {
                    if isSelected {
                        AngelaTheme.purpleGradient
                    } else {
                        Color.clear
                    }
                }
            )
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .buttonStyle(.plain)
    }
}
