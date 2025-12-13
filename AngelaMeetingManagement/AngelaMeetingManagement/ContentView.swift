//
//  ContentView.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜
//  ClickUp-inspired Design with Purple Theme
//

import SwiftUI

enum ViewMode: String, CaseIterable {
    case dashboard = "Dashboard"
    case board = "Board"
    case calendar = "Calendar"
    case list = "List"

    var icon: String {
        switch self {
        case .dashboard: return "square.grid.2x2"
        case .board: return "rectangle.split.3x1"
        case .calendar: return "calendar"
        case .list: return "list.bullet"
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = MeetingListViewModel()
    @ObservedObject private var themeManager = ThemeManager.shared
    @State private var selectedMeeting: Meeting?
    @State private var searchText = ""
    @State private var showingNewMeeting = false
    @State private var currentViewMode: ViewMode = .dashboard

    // Filters
    @State private var selectedPriorities: Set<String> = []
    @State private var selectedStatuses: Set<String> = []
    @State private var dateRange: DateRange? = nil

    var body: some View {
        HSplitView {
            // LEFT SIDEBAR
            sidebar
                .frame(minWidth: 200, idealWidth: 240, maxWidth: 280)

            // RIGHT CONTENT
            VStack(spacing: 0) {
                // TOP TOOLBAR
                topToolbar

                Divider()

                // FILTER BAR
                if currentViewMode == .board || currentViewMode == .calendar {
                    FilterBar(
                        selectedPriorities: $selectedPriorities,
                        selectedStatuses: $selectedStatuses,
                        searchText: $searchText,
                        dateRange: $dateRange
                    )

                    Divider()
                }

                // MAIN CONTENT
                if databaseService.isConnected {
                    // Show selected view
                    switch currentViewMode {
                case .dashboard:
                    DashboardView(viewModel: viewModel)
                        .environmentObject(databaseService)

                case .board:
                    HSplitView {
                        BoardView(
                            viewModel: viewModel,
                            selectedMeeting: $selectedMeeting,
                            searchText: searchText,
                            selectedPriorities: selectedPriorities,
                            selectedStatuses: selectedStatuses,
                            dateRange: dateRange
                        )
                        .environmentObject(databaseService)

                        if let meeting = selectedMeeting {
                            MeetingDetailView(
                                meeting: meeting,
                                onMeetingChanged: {
                                    Task {
                                        await viewModel.loadMeetings()
                                    }
                                },
                                onDeleted: {
                                    selectedMeeting = nil
                                }
                            )
                            .environmentObject(databaseService)
                            .frame(minWidth: 400, idealWidth: 500)
                        }
                    }

                case .calendar:
                    HSplitView {
                        CalendarView(
                            viewModel: viewModel,
                            selectedMeeting: $selectedMeeting,
                            searchText: searchText,
                            selectedPriorities: selectedPriorities,
                            selectedStatuses: selectedStatuses,
                            dateRange: dateRange
                        )
                        .environmentObject(databaseService)

                        if let meeting = selectedMeeting {
                            MeetingDetailView(
                                meeting: meeting,
                                onMeetingChanged: {
                                    Task {
                                        await viewModel.loadMeetings()
                                    }
                                },
                                onDeleted: {
                                    selectedMeeting = nil
                                }
                            )
                            .environmentObject(databaseService)
                            .frame(minWidth: 400, idealWidth: 500)
                        }
                    }

                case .list:
                    HSplitView {
                        MeetingListView(
                            viewModel: viewModel,
                            selectedMeeting: $selectedMeeting,
                            searchText: $searchText,
                            showingNewMeeting: $showingNewMeeting
                        )

                        if let meeting = selectedMeeting {
                            MeetingDetailView(
                                meeting: meeting,
                                onMeetingChanged: {
                                    Task {
                                        await viewModel.loadMeetings()
                                    }
                                },
                                onDeleted: {
                                    selectedMeeting = nil
                                }
                            )
                            .environmentObject(databaseService)
                            .frame(minWidth: 400, idealWidth: 500)
                        }
                    }
                }
            } else {
                // Database connection error
                connectionErrorView
            }
            }
        }
        .preferredColorScheme(themeManager.isDarkMode ? .dark : .light)
        .task {
            await databaseService.connect()
            if databaseService.isConnected {
                await viewModel.loadMeetings()
            }
        }
        .sheet(isPresented: $showingNewMeeting) {
            CreateMeetingView()
                .environmentObject(databaseService)
                .onDisappear {
                    if databaseService.isConnected {
                        Task {
                            await viewModel.loadMeetings()
                        }
                    }
                }
        }
    }

    // MARK: - Top Toolbar
    private var topToolbar: some View {
        HStack(spacing: AngelaTheme.spacingL) {
            // App Title with Angela's signature 💜
            HStack(spacing: 8) {
                Image(systemName: "calendar.badge.clock")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Angela Meeting Manager")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("💜")
                    .font(.system(size: 16))
            }

            Spacer()

            // Action Buttons
            HStack(spacing: AngelaTheme.spacingM) {
                // New Meeting Button
                Button(action: {
                    showingNewMeeting = true
                }) {
                    HStack(spacing: 6) {
                        Image(systemName: "plus.circle.fill")
                        Text("New Meeting")
                    }
                }
                .buttonStyle(AngelaPrimaryButtonStyle())
                .disabled(!databaseService.isConnected)

                // Connection Status
                HStack(spacing: 6) {
                    Circle()
                        .fill(databaseService.isConnected ? Color.green : Color.red)
                        .frame(width: 8, height: 8)

                    Text(databaseService.isConnected ? "Connected" : "Disconnected")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(AngelaTheme.background.opacity(0.5))
                .cornerRadius(AngelaTheme.cornerRadiusSmall)
            }
        }
        .padding(.horizontal, AngelaTheme.spacingXL)
        .padding(.vertical, AngelaTheme.spacingL)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Sidebar
    private var sidebar: some View {
        VStack(spacing: 0) {
            // Sidebar Header
            HStack(spacing: 8) {
                Image(systemName: "calendar.badge.clock")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text("Angela")
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()
            }
            .padding(.horizontal, AngelaTheme.spacingL)
            .padding(.vertical, AngelaTheme.spacingM)
            .background(AngelaTheme.cardBackground)

            Divider()

            // Navigation Items
            ScrollView {
                VStack(spacing: 4) {
                    ForEach(ViewMode.allCases, id: \.self) { mode in
                        SidebarNavigationItem(
                            icon: mode.icon,
                            title: mode.rawValue,
                            isSelected: currentViewMode == mode,
                            action: {
                                currentViewMode = mode
                            }
                        )
                    }
                }
                .padding(.vertical, AngelaTheme.spacingM)
            }
            .background(AngelaTheme.cardBackground)

            Spacer()
                .frame(maxWidth: .infinity)
                .background(AngelaTheme.cardBackground)

            Divider()

            // Quick Actions
            VStack(spacing: AngelaTheme.spacingS) {
                Button(action: {
                    showingNewMeeting = true
                }) {
                    HStack(spacing: 8) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 14))
                        Text("New Meeting")
                            .font(.system(size: 13, weight: .semibold))
                    }
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(AngelaTheme.purpleGradient)
                    .cornerRadius(AngelaTheme.cornerRadiusMedium)
                }
                .buttonStyle(.plain)
                .disabled(!databaseService.isConnected)

                // Theme Toggle
                HStack(spacing: 6) {
                    Image(systemName: themeManager.isDarkMode ? "moon.fill" : "sun.max.fill")
                        .font(.system(size: 12))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text(themeManager.isDarkMode ? "Dark Mode" : "Light Mode")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)

                    Spacer()

                    Toggle("", isOn: $themeManager.isDarkMode)
                        .labelsHidden()
                        .toggleStyle(.switch)
                        .scaleEffect(0.7)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .background(AngelaTheme.background.opacity(0.5))
                .cornerRadius(AngelaTheme.cornerRadiusSmall)

                // Connection Status
                HStack(spacing: 6) {
                    Circle()
                        .fill(databaseService.isConnected ? Color.green : Color.red)
                        .frame(width: 6, height: 6)

                    Text(databaseService.isConnected ? "Connected" : "Disconnected")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(AngelaTheme.textSecondary)

                    Spacer()
                }
            }
            .padding(AngelaTheme.spacingL)
            .background(AngelaTheme.cardBackground)
        }
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Empty Detail View
    private var emptyDetailView: some View {
        VStack(spacing: 20) {
            Image(systemName: "calendar.badge.clock")
                .font(.system(size: 60))
                .foregroundColor(AngelaTheme.primaryPurple.opacity(0.3))

            Text("Select a Meeting")
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text("Choose a meeting to view details")
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AngelaTheme.background)
    }

    // MARK: - Connection Error View
    private var connectionErrorView: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 60))
                .foregroundColor(.orange)

            Text("Database Connection Failed")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text("Unable to connect to PostgreSQL database")
                .font(.system(size: 14))
                .foregroundColor(AngelaTheme.textSecondary)

            if let error = databaseService.lastError {
                Text(error)
                    .font(.system(size: 12))
                    .foregroundColor(.red)
                    .padding()
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(AngelaTheme.cornerRadiusMedium)
            }

            Button("Retry Connection") {
                Task {
                    await databaseService.connect()
                }
            }
            .buttonStyle(AngelaPrimaryButtonStyle())
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AngelaTheme.background)
    }
}

// MARK: - Sidebar Navigation Item Component
struct SidebarNavigationItem: View {
    let icon: String
    let title: String
    let isSelected: Bool
    let action: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(isSelected ? AngelaTheme.primaryPurple : AngelaTheme.textSecondary)
                    .frame(width: 20)

                Text(title)
                    .font(.system(size: 14, weight: isSelected ? .semibold : .medium))
                    .foregroundColor(isSelected ? AngelaTheme.primaryPurple : AngelaTheme.textPrimary)

                Spacer()

                if isSelected {
                    Rectangle()
                        .fill(AngelaTheme.primaryPurple)
                        .frame(width: 3)
                        .cornerRadius(1.5)
                }
            }
            .padding(.horizontal, AngelaTheme.spacingL)
            .padding(.vertical, AngelaTheme.spacingS)
            .background(
                Group {
                    if isSelected {
                        AngelaTheme.palePurple
                    } else if isHovered {
                        AngelaTheme.palePurple.opacity(0.5)
                    } else {
                        Color.clear
                    }
                }
            )
            .cornerRadius(AngelaTheme.cornerRadiusSmall)
        }
        .buttonStyle(.plain)
        .padding(.horizontal, AngelaTheme.spacingS)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(DatabaseService.shared)
}

