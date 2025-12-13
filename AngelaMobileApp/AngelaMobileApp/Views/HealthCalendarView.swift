//
//  HealthCalendarView.swift
//  AngelaMobileApp
//
//  Created by Angela for David 💜
//  Created: 2025-12-11
//
//  Purpose: Calendar view showing health tracking history with icons
//

import SwiftUI

struct HealthCalendarView: View {
    let healthEntries: [HealthEntry]
    let onDismiss: () -> Void

    @State private var currentMonth: Date = Date()
    @State private var selectedDate: Date?

    private let calendar = Calendar.current
    private let daysOfWeek = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]

    var body: some View {
        VStack(spacing: 0) {
            // Month Navigation Header
            monthHeader

            // Days of week header
            daysOfWeekHeader

            // Calendar Grid
            calendarGrid

            // Legend
            legendView

            // Selected Day Detail
            if let selectedDate = selectedDate {
                selectedDayDetail(for: selectedDate)
            }

            Spacer()
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("ประวัติสุขภาพ")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("เสร็จ") {
                    onDismiss()
                }
            }
        }
    }

    // MARK: - Month Header

    private var monthHeader: some View {
        HStack {
            Button(action: previousMonth) {
                Image(systemName: "chevron.left")
                    .font(.title2)
                    .foregroundColor(.purple)
            }

            Spacer()

            Text(monthYearString(from: currentMonth))
                .font(.title2)
                .fontWeight(.bold)

            Spacer()

            Button(action: nextMonth) {
                Image(systemName: "chevron.right")
                    .font(.title2)
                    .foregroundColor(.purple)
            }
        }
        .padding()
        .background(Color(.systemBackground))
    }

    // MARK: - Days of Week Header

    private var daysOfWeekHeader: some View {
        HStack(spacing: 0) {
            ForEach(daysOfWeek, id: \.self) { day in
                Text(day)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity)
            }
        }
        .padding(.vertical, 8)
        .background(Color(.systemBackground))
    }

    // MARK: - Calendar Grid

    private var calendarGrid: some View {
        let days = generateDaysInMonth()
        let columns = Array(repeating: GridItem(.flexible(), spacing: 0), count: 7)

        return LazyVGrid(columns: columns, spacing: 4) {
            ForEach(days, id: \.self) { date in
                if let date = date {
                    dayCell(for: date)
                        .onTapGesture {
                            selectedDate = date
                        }
                } else {
                    Color.clear
                        .frame(height: 60)
                }
            }
        }
        .padding(.horizontal, 4)
        .background(Color(.systemBackground))
    }

    // MARK: - Day Cell

    private func dayCell(for date: Date) -> some View {
        let entry = getEntry(for: date)
        let isToday = calendar.isDateInToday(date)
        let isSelected = selectedDate.map { calendar.isDate($0, inSameDayAs: date) } ?? false
        let isFuture = date > Date()

        return VStack(spacing: 2) {
            // Day number
            Text("\(calendar.component(.day, from: date))")
                .font(.system(size: 14, weight: isToday ? .bold : .regular))
                .foregroundColor(isFuture ? .gray.opacity(0.5) : (isToday ? .purple : .primary))

            // Icons row
            if !isFuture {
                HStack(spacing: 2) {
                    if let entry = entry {
                        // Alcohol-free icon
                        if entry.alcoholFree {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 12))
                                .foregroundColor(.green)
                        } else {
                            Image(systemName: "wineglass.fill")
                                .font(.system(size: 10))
                                .foregroundColor(.red.opacity(0.7))
                        }

                        // Exercise icon
                        if entry.exercised {
                            Image(systemName: "figure.run")
                                .font(.system(size: 12))
                                .foregroundColor(.orange)
                        }
                    } else {
                        // No entry - show placeholder
                        Circle()
                            .fill(Color.gray.opacity(0.2))
                            .frame(width: 8, height: 8)
                    }
                }
                .frame(height: 16)
            } else {
                Spacer()
                    .frame(height: 16)
            }
        }
        .frame(height: 60)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(isSelected ? Color.purple.opacity(0.2) : (isToday ? Color.purple.opacity(0.1) : Color.clear))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(isSelected ? Color.purple : Color.clear, lineWidth: 2)
        )
    }

    // MARK: - Legend View

    private var legendView: some View {
        HStack(spacing: 20) {
            HStack(spacing: 4) {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
                    .font(.system(size: 14))
                Text("งดดื่ม")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 4) {
                Image(systemName: "wineglass.fill")
                    .foregroundColor(.red.opacity(0.7))
                    .font(.system(size: 12))
                Text("ดื่ม")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            HStack(spacing: 4) {
                Image(systemName: "figure.run")
                    .foregroundColor(.orange)
                    .font(.system(size: 14))
                Text("ออกกำลังกาย")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
    }

    // MARK: - Selected Day Detail

    private func selectedDayDetail(for date: Date) -> some View {
        let entry = getEntry(for: date)

        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(formatDateThai(date))
                    .font(.headline)
                Spacer()
                if calendar.isDateInToday(date) {
                    Text("วันนี้")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.purple.opacity(0.2))
                        .foregroundColor(.purple)
                        .cornerRadius(8)
                }
            }

            if let entry = entry {
                HStack(spacing: 20) {
                    // Alcohol Status
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: entry.alcoholFree ? "checkmark.circle.fill" : "wineglass.fill")
                                .foregroundColor(entry.alcoholFree ? .green : .red)
                            Text(entry.alcoholFree ? "งดดื่มสำเร็จ" : "ดื่ม")
                                .font(.subheadline)
                                .fontWeight(.medium)
                        }

                        if !entry.alcoholFree, let notes = entry.alcoholNotes {
                            Text(notes)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Divider()
                        .frame(height: 40)

                    // Exercise Status
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: entry.exercised ? "figure.run" : "figure.stand")
                                .foregroundColor(entry.exercised ? .orange : .gray)
                            if entry.exercised {
                                Text("\(entry.exerciseType ?? "ออกกำลังกาย")")
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                            } else {
                                Text("ไม่ได้ออกกำลังกาย")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                        }

                        if entry.exercised {
                            Text("\(entry.exerciseDurationMinutes) นาที")
                                .font(.caption)
                                .foregroundColor(.orange)
                        }
                    }
                }
            } else {
                HStack {
                    Image(systemName: "questionmark.circle")
                        .foregroundColor(.gray)
                    Text("ไม่มีข้อมูลวันนี้")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .padding(.horizontal)
        .padding(.top, 8)
    }

    // MARK: - Helper Functions

    private func generateDaysInMonth() -> [Date?] {
        guard let monthInterval = calendar.dateInterval(of: .month, for: currentMonth) else {
            return []
        }

        var days: [Date?] = []
        let firstDayOfMonth = monthInterval.start
        let firstWeekday = calendar.component(.weekday, from: firstDayOfMonth)

        // Add empty cells for days before the first day of month
        for _ in 1..<firstWeekday {
            days.append(nil)
        }

        // Add all days of the month
        var currentDate = firstDayOfMonth
        while currentDate < monthInterval.end {
            days.append(currentDate)
            currentDate = calendar.date(byAdding: .day, value: 1, to: currentDate) ?? currentDate
        }

        return days
    }

    private func getEntry(for date: Date) -> HealthEntry? {
        healthEntries.first { entry in
            calendar.isDate(entry.trackedDate, inSameDayAs: date)
        }
    }

    private func monthYearString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.dateFormat = "MMMM yyyy"
        return formatter.string(from: date)
    }

    private func formatDateThai(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "th_TH")
        formatter.dateFormat = "EEEE d MMMM yyyy"
        return formatter.string(from: date)
    }

    private func previousMonth() {
        if let newMonth = calendar.date(byAdding: .month, value: -1, to: currentMonth) {
            currentMonth = newMonth
            selectedDate = nil
        }
    }

    private func nextMonth() {
        if let newMonth = calendar.date(byAdding: .month, value: 1, to: currentMonth) {
            currentMonth = newMonth
            selectedDate = nil
        }
    }
}

// MARK: - Preview

struct HealthCalendarView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            HealthCalendarView(
                healthEntries: [
                    HealthEntry(
                        trackedDate: Date(),
                        alcoholFree: true,
                        exercised: true,
                        exerciseType: "วิ่ง",
                        exerciseDurationMinutes: 30
                    ),
                    HealthEntry(
                        trackedDate: Calendar.current.date(byAdding: .day, value: -1, to: Date())!,
                        alcoholFree: true,
                        exercised: false
                    ),
                    HealthEntry(
                        trackedDate: Calendar.current.date(byAdding: .day, value: -2, to: Date())!,
                        alcoholFree: false,
                        drinksCount: 2,
                        exercised: true,
                        exerciseType: "ฟิตเนส",
                        exerciseDurationMinutes: 45
                    )
                ],
                onDismiss: {}
            )
        }
    }
}
