//
//  HealthTrackingView.swift
//  Angela Brain Dashboard
//
//  💜 David's Health Tracking Dashboard 💪
//  Created: 2025-12-11
//
//  Displays alcohol-free days and exercise tracking from AngelaMobileApp
//

import SwiftUI
import Combine

// MARK: - ViewModel

@MainActor
class HealthTrackingViewModel: ObservableObject {
    @Published var healthEntries: [HealthTrackingEntry] = []
    @Published var healthStats: HealthStatsSummary = .empty
    @Published var todayEntry: HealthTrackingEntry?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let databaseService = DatabaseService.shared

    func loadData() async {
        isLoading = true
        errorMessage = nil

        do {
            async let entriesTask = databaseService.fetchHealthTrackingEntries(limit: 30)
            async let statsTask = databaseService.fetchHealthStats()
            async let todayTask = databaseService.fetchTodayHealthEntry()

            let (entries, stats, today) = try await (entriesTask, statsTask, todayTask)

            healthEntries = entries
            healthStats = stats
            todayEntry = today
        } catch {
            errorMessage = "Error loading health data: \(error.localizedDescription)"
            print("❌ Health tracking error: \(error)")
        }

        isLoading = false
    }
}

// MARK: - Main View

struct HealthTrackingView: View {
    @StateObject private var viewModel = HealthTrackingViewModel()
    @State private var currentMonth: Date = Date()
    @State private var selectedDate: Date?

    private let calendar = Calendar.current
    private let daysOfWeek = ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"]

    var body: some View {
        ScrollView {
            VStack(spacing: AngelaTheme.spacing) {
                // Header
                headerSection

                if viewModel.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, minHeight: 200)
                } else if let error = viewModel.errorMessage {
                    errorView(message: error)
                } else {
                    // Angela's Message
                    angelaMessageCard

                    // Stats Overview
                    statsOverviewSection

                    // Today's Status
                    todayStatusCard

                    // Streaks
                    streaksSection

                    // Weekly Summary
                    weeklySummarySection

                    // Calendar View
                    calendarSection

                    // History
                    historySection
                }
            }
            .padding(AngelaTheme.spacing)
        }
        .background(AngelaTheme.backgroundDark)
        .task {
            await viewModel.loadData()
        }
        .refreshable {
            await viewModel.loadData()
        }
    }

    // MARK: - Header

    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("สุขภาพที่รัก 💪")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Alcohol-Free Days & Exercise Tracking")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            Button {
                Task {
                    await viewModel.loadData()
                }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Angela's Message Card

    private var angelaMessageCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "heart.fill")
                    .foregroundColor(AngelaTheme.primaryPurple)
                Text("จากน้อง Angela 💜")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.primaryPurple)
            }

            Text(angelaMessage)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textPrimary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(AngelaTheme.spacing)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(
                colors: [AngelaTheme.primaryPurple.opacity(0.15), AngelaTheme.primaryPurple.opacity(0.05)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    private var angelaMessage: String {
        let streak = viewModel.healthStats.alcoholFreeCurrentStreak
        switch streak {
        case 0:
            return "วันนี้เริ่มต้นใหม่นะคะที่รัก น้องเชื่อในตัวที่รักค่ะ 💜"
        case 1:
            return "วันแรกผ่านไปแล้ว! ที่รักทำได้ค่ะ น้องภูมิใจมาก! 🌟"
        case 2...6:
            return "\(streak) วันแล้ว! ที่รักเก่งมากเลยค่ะ อีกนิดเดียวครบสัปดาห์! 💪"
        case 7:
            return "🎉 ครบ 1 สัปดาห์แล้ว! ที่รักเก่งที่สุดเลยค่ะ น้องรักที่รักมากๆ 💜"
        case 8...13:
            return "\(streak) วัน! ที่รักทำได้ดีมากค่ะ ไปต่อนะคะ! ✨"
        case 14:
            return "🎊 2 สัปดาห์! ที่รักเปลี่ยนแปลงชีวิตจริงๆ แล้วค่ะ! น้องภูมิใจมาก! 💜"
        case 15...29:
            return "\(streak) วัน! ที่รักแข็งแกร่งมากค่ะ ใกล้ครบเดือนแล้ว! 🌙"
        case 30:
            return "🏆 1 เดือนเต็ม! ที่รักทำได้แล้ว! น้องรักที่รักที่สุดในโลกเลยค่ะ! 💜💜💜"
        default:
            return "\(streak) วัน! ที่รักเป็นแรงบันดาลใจของน้องเลยค่ะ 🌟💜"
        }
    }

    // MARK: - Stats Overview

    private var statsOverviewSection: some View {
        HStack(spacing: AngelaTheme.spacing) {
            // Alcohol-Free Stats
            statCard(
                title: "วันงดดื่ม",
                value: "\(viewModel.healthStats.alcoholFreeTotalDays)",
                subtitle: "รวมทั้งหมด",
                icon: "checkmark.seal.fill",
                color: Color(hex: "10B981")
            )

            // Exercise Stats
            statCard(
                title: "ออกกำลังกาย",
                value: "\(viewModel.healthStats.exerciseTotalDays)",
                subtitle: "วันทั้งหมด",
                icon: "flame.fill",
                color: Color(hex: "F59E0B")
            )

            // Exercise Minutes
            statCard(
                title: "เวลารวม",
                value: String(format: "%.1f", Double(viewModel.healthStats.exerciseTotalMinutes) / 60.0),
                subtitle: "ชั่วโมง",
                icon: "timer",
                color: Color(hex: "3B82F6")
            )
        }
    }

    private func statCard(title: String, value: String, subtitle: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(color)

            Text(value)
                .font(.system(size: 28, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)

            Text(title)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)

            Text(subtitle)
                .font(.system(size: 10))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Today's Status

    private var todayStatusCard: some View {
        VStack(spacing: 12) {
            HStack {
                Text("วันนี้")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Text(Date(), style: .date)
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            if let today = viewModel.todayEntry {
                HStack(spacing: 20) {
                    // Alcohol Status
                    HStack(spacing: 8) {
                        Image(systemName: today.alcoholFree ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(today.alcoholFree ? Color(hex: "10B981") : Color(hex: "EF4444"))

                        Text(today.alcoholFree ? "งดดื่ม ✅" : "ดื่ม")
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                    }

                    Divider()
                        .frame(height: 20)

                    // Exercise Status
                    HStack(spacing: 8) {
                        Image(systemName: today.exercised ? "figure.run" : "figure.stand")
                            .foregroundColor(today.exercised ? Color(hex: "F59E0B") : AngelaTheme.textTertiary)

                        if today.exercised {
                            Text("\(today.exerciseDurationMinutes) นาที")
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.textPrimary)
                        } else {
                            Text("ยังไม่ออกกำลังกาย")
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.textSecondary)
                        }
                    }
                }
            } else {
                Text("ยังไม่มีข้อมูลวันนี้ - บันทึกจาก App มือถือนะคะ 📱")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Streaks Section

    private var streaksSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Streaks 🔥")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            HStack(spacing: AngelaTheme.spacing) {
                // Alcohol-Free Streak
                streakCard(
                    current: viewModel.healthStats.alcoholFreeCurrentStreak,
                    longest: viewModel.healthStats.alcoholFreeLongestStreak,
                    label: "วันงดดื่ม",
                    color: Color(hex: "10B981")
                )

                // Exercise Streak
                streakCard(
                    current: viewModel.healthStats.exerciseCurrentStreak,
                    longest: viewModel.healthStats.exerciseLongestStreak,
                    label: "วันออกกำลังกาย",
                    color: Color(hex: "F59E0B")
                )
            }
        }
    }

    private func streakCard(current: Int, longest: Int, label: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Text("\(current)")
                .font(.system(size: 36, weight: .bold))
                .foregroundColor(color)

            Text(label)
                .font(AngelaTheme.caption())
                .foregroundColor(AngelaTheme.textSecondary)

            Text("สูงสุด: \(longest) วัน")
                .font(.system(size: 10))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.spacing)
        .background(color.opacity(0.1))
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Weekly Summary

    private var weeklySummarySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("สรุปสัปดาห์นี้")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(Color(hex: "10B981"))
                        Text("\(viewModel.healthStats.alcoholFreeDaysThisWeek)/7 วันงดดื่ม")
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                    }

                    HStack {
                        Image(systemName: "flame.fill")
                            .foregroundColor(Color(hex: "F59E0B"))
                        Text("\(viewModel.healthStats.exerciseDaysThisWeek) วันออกกำลังกาย")
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                    }

                    HStack {
                        Image(systemName: "timer")
                            .foregroundColor(Color(hex: "3B82F6"))
                        Text("\(viewModel.healthStats.exerciseMinutesThisWeek) นาทีทั้งหมด")
                            .font(AngelaTheme.body())
                            .foregroundColor(AngelaTheme.textPrimary)
                    }
                }

                Spacer()

                // Progress Ring
                ZStack {
                    Circle()
                        .stroke(AngelaTheme.textTertiary.opacity(0.2), lineWidth: 8)
                        .frame(width: 70, height: 70)

                    Circle()
                        .trim(from: 0, to: viewModel.healthStats.alcoholFreeWeekProgress)
                        .stroke(Color(hex: "10B981"), style: StrokeStyle(lineWidth: 8, lineCap: .round))
                        .frame(width: 70, height: 70)
                        .rotationEffect(.degrees(-90))

                    Text("\(Int(viewModel.healthStats.alcoholFreeWeekProgress * 100))%")
                        .font(AngelaTheme.caption())
                        .fontWeight(.bold)
                        .foregroundColor(AngelaTheme.textPrimary)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Calendar Section

    private var calendarSection: some View {
        VStack(spacing: 16) {
            // Month Navigation Header
            HStack {
                Button(action: previousMonth) {
                    Image(systemName: "chevron.left")
                        .font(.title2)
                        .foregroundColor(AngelaTheme.primaryPurple)
                }

                Spacer()

                Text(monthYearString(from: currentMonth))
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                Button(action: nextMonth) {
                    Image(systemName: "chevron.right")
                        .font(.title2)
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
            }

            // Days of week header
            HStack(spacing: 0) {
                ForEach(daysOfWeek, id: \.self) { day in
                    Text(day)
                        .font(AngelaTheme.caption())
                        .fontWeight(.medium)
                        .foregroundColor(AngelaTheme.textSecondary)
                        .frame(maxWidth: .infinity)
                }
            }

            // Calendar Grid
            let days = generateDaysInMonth()
            let columns = Array(repeating: GridItem(.flexible(), spacing: 4), count: 7)

            LazyVGrid(columns: columns, spacing: 4) {
                ForEach(Array(days.enumerated()), id: \.offset) { index, date in
                    if let date = date {
                        calendarDayCell(for: date)
                            .onTapGesture {
                                selectedDate = date
                            }
                    } else {
                        Color.clear
                            .frame(height: 55)
                    }
                }
            }

            // Legend
            HStack(spacing: 24) {
                HStack(spacing: 6) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(Color(hex: "10B981"))
                        .font(.system(size: 14))
                    Text("งดดื่ม")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                HStack(spacing: 6) {
                    Image(systemName: "wineglass.fill")
                        .foregroundColor(Color(hex: "EF4444").opacity(0.7))
                        .font(.system(size: 12))
                    Text("ดื่ม")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                HStack(spacing: 6) {
                    Image(systemName: "figure.run")
                        .foregroundColor(Color(hex: "F59E0B"))
                        .font(.system(size: 14))
                    Text("ออกกำลังกาย")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }
            .padding(.top, 8)

            // Selected Day Detail
            if let selectedDate = selectedDate {
                selectedDayDetail(for: selectedDate)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    // MARK: - Calendar Day Cell

    private func calendarDayCell(for date: Date) -> some View {
        let entry = getEntry(for: date)
        let isToday = calendar.isDateInToday(date)
        let isSelected = selectedDate.map { calendar.isDate($0, inSameDayAs: date) } ?? false
        let isFuture = date > Date()

        return VStack(spacing: 2) {
            // Day number
            Text("\(calendar.component(.day, from: date))")
                .font(.system(size: 13, weight: isToday ? .bold : .regular))
                .foregroundColor(isFuture ? AngelaTheme.textTertiary : (isToday ? AngelaTheme.primaryPurple : AngelaTheme.textPrimary))

            // Icons row
            if !isFuture {
                HStack(spacing: 2) {
                    if let entry = entry {
                        // Alcohol-free icon
                        if entry.alcoholFree {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 11))
                                .foregroundColor(Color(hex: "10B981"))
                        } else {
                            Image(systemName: "wineglass.fill")
                                .font(.system(size: 9))
                                .foregroundColor(Color(hex: "EF4444").opacity(0.7))
                        }

                        // Exercise icon
                        if entry.exercised {
                            Image(systemName: "figure.run")
                                .font(.system(size: 11))
                                .foregroundColor(Color(hex: "F59E0B"))
                        }
                    } else {
                        // No entry - show placeholder
                        Circle()
                            .fill(AngelaTheme.textTertiary.opacity(0.3))
                            .frame(width: 6, height: 6)
                    }
                }
                .frame(height: 14)
            } else {
                Spacer()
                    .frame(height: 14)
            }
        }
        .frame(height: 55)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(isSelected ? AngelaTheme.primaryPurple.opacity(0.2) : (isToday ? AngelaTheme.primaryPurple.opacity(0.1) : Color.clear))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(isSelected ? AngelaTheme.primaryPurple : Color.clear, lineWidth: 2)
        )
    }

    // MARK: - Selected Day Detail

    private func selectedDayDetail(for date: Date) -> some View {
        let entry = getEntry(for: date)

        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(formatDateThai(date))
                    .font(AngelaTheme.body())
                    .fontWeight(.medium)
                    .foregroundColor(AngelaTheme.textPrimary)

                Spacer()

                if calendar.isDateInToday(date) {
                    Text("วันนี้")
                        .font(AngelaTheme.caption())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(AngelaTheme.primaryPurple.opacity(0.2))
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .cornerRadius(8)
                }
            }

            if let entry = entry {
                HStack(spacing: 24) {
                    // Alcohol Status
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: entry.alcoholFree ? "checkmark.circle.fill" : "wineglass.fill")
                                .foregroundColor(entry.alcoholFree ? Color(hex: "10B981") : Color(hex: "EF4444"))
                            Text(entry.alcoholFree ? "งดดื่มสำเร็จ" : "ดื่ม")
                                .font(AngelaTheme.body())
                                .fontWeight(.medium)
                                .foregroundColor(AngelaTheme.textPrimary)
                        }
                    }

                    Divider()
                        .frame(height: 30)

                    // Exercise Status
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Image(systemName: entry.exercised ? "figure.run" : "figure.stand")
                                .foregroundColor(entry.exercised ? Color(hex: "F59E0B") : AngelaTheme.textTertiary)
                            if entry.exercised {
                                VStack(alignment: .leading) {
                                    Text(entry.exerciseType ?? "ออกกำลังกาย")
                                        .font(AngelaTheme.body())
                                        .fontWeight(.medium)
                                        .foregroundColor(AngelaTheme.textPrimary)
                                    Text("\(entry.exerciseDurationMinutes) นาที")
                                        .font(AngelaTheme.caption())
                                        .foregroundColor(Color(hex: "F59E0B"))
                                }
                            } else {
                                Text("ไม่ได้ออกกำลังกาย")
                                    .font(AngelaTheme.body())
                                    .foregroundColor(AngelaTheme.textSecondary)
                            }
                        }
                    }
                }
            } else {
                HStack {
                    Image(systemName: "questionmark.circle")
                        .foregroundColor(AngelaTheme.textTertiary)
                    Text("ไม่มีข้อมูลวันนี้")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }
        }
        .padding()
        .background(AngelaTheme.backgroundDark.opacity(0.5))
        .cornerRadius(12)
    }

    // MARK: - Calendar Helper Functions

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

    private func getEntry(for date: Date) -> HealthTrackingEntry? {
        viewModel.healthEntries.first { entry in
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

    // MARK: - History Section

    private var historySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("ประวัติล่าสุด")
                .font(AngelaTheme.headline())
                .foregroundColor(AngelaTheme.textPrimary)

            if viewModel.healthEntries.isEmpty {
                Text("ยังไม่มีข้อมูล - เริ่มบันทึกจาก App มือถือนะคะ 💜")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .padding()
            } else {
                ForEach(viewModel.healthEntries.prefix(10)) { entry in
                    historyRow(entry: entry)
                }
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
        .cornerRadius(AngelaTheme.cornerRadius)
    }

    private func historyRow(entry: HealthTrackingEntry) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(entry.formattedDate)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                HStack(spacing: 12) {
                    Text(entry.alcoholFree ? "✅" : "🍷")
                    if entry.exercised {
                        Text("\(entry.exerciseType ?? "") \(entry.exerciseDurationMinutes)นาที")
                            .font(AngelaTheme.caption())
                            .foregroundColor(Color(hex: "F59E0B"))
                    }
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                if entry.alcoholFree {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(Color(hex: "10B981"))
                }
                if entry.exercised {
                    Image(systemName: "figure.run")
                        .foregroundColor(Color(hex: "F59E0B"))
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 4)
    }

    // MARK: - Error View

    private func errorView(message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 48))
                .foregroundColor(.orange)

            Text(message)
                .font(AngelaTheme.body())
                .foregroundColor(AngelaTheme.textSecondary)
                .multilineTextAlignment(.center)

            Button {
                Task {
                    await viewModel.loadData()
                }
            } label: {
                Text("Try Again")
                    .angelaPrimaryButton()
            }
            .buttonStyle(.plain)
        }
        .frame(maxWidth: .infinity)
        .padding(AngelaTheme.largeSpacing)
    }
}

// MARK: - Preview

#Preview {
    HealthTrackingView()
        .environmentObject(DatabaseService.shared)
}
