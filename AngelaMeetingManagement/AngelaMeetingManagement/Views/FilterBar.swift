//
//  FilterBar.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜
//  Filter Bar Component
//

import SwiftUI

struct FilterBar: View {
    @Binding var selectedPriorities: Set<String>
    @Binding var selectedStatuses: Set<String>
    @Binding var searchText: String
    @Binding var dateRange: DateRange?

    @State private var showingFilters = false

    let allPriorities = ["Urgent", "High", "Normal", "Low"]
    let allStatuses = ["scheduled", "in_progress", "completed", "cancelled"]

    var body: some View {
        HStack(spacing: AngelaTheme.spacingM) {
            // Search Bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(AngelaTheme.textSecondary)
                    .font(.system(size: 14))

                TextField("Search meetings...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 14))

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(AngelaTheme.textSecondary)
                            .font(.system(size: 14))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(AngelaTheme.background.opacity(0.5))
            .cornerRadius(AngelaTheme.cornerRadiusMedium)
            .frame(width: 300)

            Divider()
                .frame(height: 20)

            // Filter Button
            Button(action: { showingFilters.toggle() }) {
                HStack(spacing: 6) {
                    Image(systemName: "line.3.horizontal.decrease.circle\(showingFilters ? ".fill" : "")")
                        .font(.system(size: 16))
                    Text("Filters")
                        .font(.system(size: 14, weight: .medium))

                    if activeFilterCount > 0 {
                        Text("\(activeFilterCount)")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.white)
                            .frame(minWidth: 20, minHeight: 20)
                            .background(Circle().fill(AngelaTheme.accentPink))
                    }
                }
                .foregroundColor(showingFilters ? AngelaTheme.primaryPurple : AngelaTheme.textSecondary)
            }
            .buttonStyle(.plain)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(showingFilters ? AngelaTheme.primaryPurple.opacity(0.15) : Color.clear)
            .cornerRadius(AngelaTheme.cornerRadiusMedium)

            // Clear Filters Button
            if activeFilterCount > 0 {
                Button("Clear All") {
                    clearAllFilters()
                }
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(AngelaTheme.accentPink)
            }

            Spacer()
        }
        .padding(.horizontal, AngelaTheme.spacingL)
        .padding(.vertical, AngelaTheme.spacingM)
        .background(AngelaTheme.cardBackground)
        .overlay(
            // Filter Panel
            VStack {
                if showingFilters {
                    FilterPanel(
                        selectedPriorities: $selectedPriorities,
                        selectedStatuses: $selectedStatuses,
                        dateRange: $dateRange,
                        allPriorities: allPriorities,
                        allStatuses: allStatuses
                    )
                    .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
            .frame(maxWidth: .infinity, alignment: .topLeading)
            .offset(y: 60)
        , alignment: .top)
    }

    private var activeFilterCount: Int {
        var count = 0
        if !selectedPriorities.isEmpty { count += selectedPriorities.count }
        if !selectedStatuses.isEmpty { count += selectedStatuses.count }
        if dateRange != nil { count += 1 }
        return count
    }

    private func clearAllFilters() {
        selectedPriorities.removeAll()
        selectedStatuses.removeAll()
        dateRange = nil
        searchText = ""
    }
}

// MARK: - Filter Panel
struct FilterPanel: View {
    @Binding var selectedPriorities: Set<String>
    @Binding var selectedStatuses: Set<String>
    @Binding var dateRange: DateRange?

    let allPriorities: [String]
    let allStatuses: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: AngelaTheme.spacingL) {
            // Priority Filter
            VStack(alignment: .leading, spacing: AngelaTheme.spacingS) {
                Text("Priority")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    ForEach(allPriorities, id: \.self) { priority in
                        FilterChip(
                            title: priority,
                            isSelected: selectedPriorities.contains(priority),
                            color: AngelaTheme.priorityColor(for: priority),
                            onTap: {
                                if selectedPriorities.contains(priority) {
                                    selectedPriorities.remove(priority)
                                } else {
                                    selectedPriorities.insert(priority)
                                }
                            }
                        )
                    }
                }
            }

            Divider()

            // Status Filter
            VStack(alignment: .leading, spacing: AngelaTheme.spacingS) {
                Text("Status")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    ForEach(allStatuses, id: \.self) { status in
                        FilterChip(
                            title: status.capitalized,
                            isSelected: selectedStatuses.contains(status),
                            color: AngelaTheme.statusColor(for: status),
                            onTap: {
                                if selectedStatuses.contains(status) {
                                    selectedStatuses.remove(status)
                                } else {
                                    selectedStatuses.insert(status)
                                }
                            }
                        )
                    }
                }
            }

            Divider()

            // Date Range Filter
            VStack(alignment: .leading, spacing: AngelaTheme.spacingS) {
                Text("Date Range")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 8) {
                    Button("Today") {
                        dateRange = .today
                    }
                    .buttonStyle(DateRangeButtonStyle(isSelected: dateRange == .today))

                    Button("This Week") {
                        dateRange = .thisWeek
                    }
                    .buttonStyle(DateRangeButtonStyle(isSelected: dateRange == .thisWeek))

                    Button("This Month") {
                        dateRange = .thisMonth
                    }
                    .buttonStyle(DateRangeButtonStyle(isSelected: dateRange == .thisMonth))

                    if dateRange != nil {
                        Button("Clear") {
                            dateRange = nil
                        }
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(AngelaTheme.accentPink)
                    }
                }
            }
        }
        .padding(AngelaTheme.spacingL)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadiusMedium)
        .shadow(color: AngelaTheme.primaryPurple.opacity(0.15), radius: 12, y: 8)
        .padding(.horizontal, AngelaTheme.spacingL)
    }
}

// MARK: - Filter Chip
struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let color: Color
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(isSelected ? .white : color)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(
                    Capsule()
                        .fill(isSelected ? color : color.opacity(0.15))
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Date Range Button Style
struct DateRangeButtonStyle: ButtonStyle {
    let isSelected: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(isSelected ? .white : AngelaTheme.primaryPurple)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                Capsule()
                    .fill(isSelected ? AngelaTheme.primaryPurple : AngelaTheme.palePurple)
            )
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
    }
}

// MARK: - Date Range Enum
enum DateRange: Equatable {
    case today
    case thisWeek
    case thisMonth

    func contains(_ date: Date) -> Bool {
        let calendar = Calendar.current
        let now = Date()

        switch self {
        case .today:
            return calendar.isDateInToday(date)
        case .thisWeek:
            return calendar.isDate(date, equalTo: now, toGranularity: .weekOfYear)
        case .thisMonth:
            return calendar.isDate(date, equalTo: now, toGranularity: .month)
        }
    }
}
