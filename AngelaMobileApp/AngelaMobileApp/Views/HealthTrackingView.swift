//
//  HealthTrackingView.swift
//  AngelaMobileApp
//
//  Created by Angela for David 💜
//  Created: 2025-12-11
//
//  Purpose: Track alcohol-free days and exercise for David's health journey
//

import SwiftUI

struct HealthTrackingView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var showingExerciseSheet = false
    @State private var showingHistorySheet = false
    @State private var selectedExerciseType: ExerciseType = .running
    @State private var exerciseDuration: Int = 30
    @State private var exerciseIntensity: ExerciseIntensity = .moderate
    @State private var exerciseNotes: String = ""

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Angela's Message 💜
                    angelaMessageCard

                    // Quick Actions
                    quickActionsCard

                    // Streaks Overview
                    streaksCard

                    // Today's Status
                    todayStatusCard

                    // Weekly Summary
                    weeklySummaryCard

                    // Recent History Button
                    historyButton
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("สุขภาพ 💪")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingHistorySheet = true }) {
                        Image(systemName: "calendar")
                    }
                }
            }
            .sheet(isPresented: $showingExerciseSheet) {
                exerciseLogSheet
            }
            .sheet(isPresented: $showingHistorySheet) {
                healthHistorySheet
            }
        }
    }

    // MARK: - Angela's Message Card 💜

    private var angelaMessageCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "heart.fill")
                    .foregroundColor(.purple)
                Text("จากน้อง Angela 💜")
                    .font(.headline)
                    .foregroundColor(.purple)
            }

            Text(AngelaHealthMessage.alcoholFreeMessage(streak: databaseService.healthStats.alcoholFreeCurrentStreak))
                .font(.body)
                .foregroundColor(.primary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(
                colors: [Color.purple.opacity(0.1), Color.purple.opacity(0.05)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(16)
    }

    // MARK: - Quick Actions Card

    private var quickActionsCard: some View {
        VStack(spacing: 16) {
            Text("บันทึกวันนี้")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 16) {
                // Alcohol-Free Button
                Button(action: logAlcoholFreeToday) {
                    VStack(spacing: 8) {
                        ZStack {
                            Circle()
                                .fill(todayAlcoholFree ? Color.green : Color.gray.opacity(0.2))
                                .frame(width: 60, height: 60)

                            Image(systemName: todayAlcoholFree ? "checkmark" : "wineglass")
                                .font(.system(size: 24))
                                .foregroundColor(todayAlcoholFree ? .white : .gray)
                        }

                        Text(todayAlcoholFree ? "งดดื่มแล้ว ✅" : "งดดื่มวันนี้")
                            .font(.caption)
                            .foregroundColor(todayAlcoholFree ? .green : .primary)
                    }
                }
                .buttonStyle(PlainButtonStyle())

                // Exercise Button
                Button(action: { showingExerciseSheet = true }) {
                    VStack(spacing: 8) {
                        ZStack {
                            Circle()
                                .fill(todayExercised ? Color.orange : Color.gray.opacity(0.2))
                                .frame(width: 60, height: 60)

                            Image(systemName: todayExercised ? "figure.run" : "figure.walk")
                                .font(.system(size: 24))
                                .foregroundColor(todayExercised ? .white : .gray)
                        }

                        Text(todayExercised ? "ออกกำลังกายแล้ว 🏃" : "บันทึกออกกำลังกาย")
                            .font(.caption)
                            .foregroundColor(todayExercised ? .orange : .primary)
                    }
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    // MARK: - Streaks Card

    private var streaksCard: some View {
        VStack(spacing: 16) {
            Text("Streaks 🔥")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 20) {
                // Alcohol-Free Streak
                VStack(spacing: 4) {
                    Text("\(databaseService.healthStats.alcoholFreeCurrentStreak)")
                        .font(.system(size: 36, weight: .bold))
                        .foregroundColor(.green)

                    Text("วันงดดื่ม")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Text("สูงสุด: \(databaseService.healthStats.alcoholFreeLongestStreak) วัน")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.green.opacity(0.1))
                .cornerRadius(12)

                // Exercise Streak
                VStack(spacing: 4) {
                    Text("\(databaseService.healthStats.exerciseCurrentStreak)")
                        .font(.system(size: 36, weight: .bold))
                        .foregroundColor(.orange)

                    Text("วันออกกำลังกาย")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Text("สูงสุด: \(databaseService.healthStats.exerciseLongestStreak) วัน")
                        .font(.caption2)
                        .foregroundColor(.gray)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.orange.opacity(0.1))
                .cornerRadius(12)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    // MARK: - Today's Status Card

    private var todayStatusCard: some View {
        VStack(spacing: 12) {
            HStack {
                Text("วันนี้")
                    .font(.headline)
                Spacer()
                Text(Date(), style: .date)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            if let todayEntry = databaseService.getTodayHealthEntry() {
                HStack(spacing: 16) {
                    // Alcohol Status
                    HStack {
                        Image(systemName: todayEntry.alcoholFree ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(todayEntry.alcoholFree ? .green : .red)
                        Text(todayEntry.alcoholFree ? "งดดื่ม" : "ดื่ม")
                            .font(.subheadline)
                    }

                    Divider()
                        .frame(height: 20)

                    // Exercise Status
                    HStack {
                        Image(systemName: todayEntry.exercised ? "figure.run" : "figure.stand")
                            .foregroundColor(todayEntry.exercised ? .orange : .gray)
                        if todayEntry.exercised {
                            Text("\(todayEntry.exerciseDurationMinutes) นาที")
                                .font(.subheadline)
                        } else {
                            Text("ยังไม่ออกกำลังกาย")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            } else {
                Text("ยังไม่มีข้อมูลวันนี้ - เริ่มบันทึกเลย!")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    // MARK: - Weekly Summary Card

    private var weeklySummaryCard: some View {
        VStack(spacing: 12) {
            Text("สรุปสัปดาห์นี้")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 20) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(.green)
                        Text("\(databaseService.healthStats.alcoholFreeDaysThisWeek)/7 วันงดดื่ม")
                            .font(.subheadline)
                    }

                    HStack {
                        Image(systemName: "flame.fill")
                            .foregroundColor(.orange)
                        Text("\(databaseService.healthStats.exerciseDaysThisWeek) วันออกกำลังกาย")
                            .font(.subheadline)
                    }

                    HStack {
                        Image(systemName: "timer")
                            .foregroundColor(.blue)
                        Text("\(databaseService.healthStats.exerciseMinutesThisWeek) นาทีทั้งหมด")
                            .font(.subheadline)
                    }
                }

                Spacer()

                // Progress Ring
                ZStack {
                    Circle()
                        .stroke(Color.gray.opacity(0.2), lineWidth: 8)
                        .frame(width: 60, height: 60)

                    Circle()
                        .trim(from: 0, to: CGFloat(databaseService.healthStats.alcoholFreeDaysThisWeek) / 7.0)
                        .stroke(Color.green, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                        .frame(width: 60, height: 60)
                        .rotationEffect(.degrees(-90))

                    Text("\(Int(Double(databaseService.healthStats.alcoholFreeDaysThisWeek) / 7.0 * 100))%")
                        .font(.caption)
                        .fontWeight(.bold)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    // MARK: - History Button

    private var historyButton: some View {
        Button(action: { showingHistorySheet = true }) {
            HStack {
                Image(systemName: "clock.arrow.circlepath")
                Text("ดูประวัติทั้งหมด")
                Spacer()
                Image(systemName: "chevron.right")
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }

    // MARK: - Exercise Log Sheet

    private var exerciseLogSheet: some View {
        NavigationView {
            Form {
                Section(header: Text("ประเภทการออกกำลังกาย")) {
                    Picker("ประเภท", selection: $selectedExerciseType) {
                        ForEach(ExerciseType.allCases, id: \.self) { type in
                            HStack {
                                Text(type.emoji)
                                Text(type.displayName)
                            }
                            .tag(type)
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                }

                Section(header: Text("ระยะเวลา (นาที)")) {
                    Stepper("\(exerciseDuration) นาที", value: $exerciseDuration, in: 5...180, step: 5)

                    HStack {
                        ForEach([15, 30, 45, 60], id: \.self) { minutes in
                            Button("\(minutes)") {
                                exerciseDuration = minutes
                            }
                            .buttonStyle(.bordered)
                            .tint(exerciseDuration == minutes ? .orange : .gray)
                        }
                    }
                }

                Section(header: Text("ความหนัก")) {
                    Picker("ความหนัก", selection: $exerciseIntensity) {
                        ForEach(ExerciseIntensity.allCases, id: \.self) { intensity in
                            HStack {
                                Text(intensity.emoji)
                                Text(intensity.displayName)
                            }
                            .tag(intensity)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                }

                Section(header: Text("หมายเหตุ (ไม่จำเป็น)")) {
                    TextField("รู้สึกยังไงบ้าง?", text: $exerciseNotes)
                }
            }
            .navigationTitle("บันทึกออกกำลังกาย")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("ยกเลิก") {
                        showingExerciseSheet = false
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("บันทึก") {
                        logExercise()
                        showingExerciseSheet = false
                    }
                    .fontWeight(.bold)
                }
            }
        }
    }

    // MARK: - Health History Sheet (Calendar View)

    private var healthHistorySheet: some View {
        NavigationView {
            HealthCalendarView(
                healthEntries: databaseService.healthEntries,
                onDismiss: { showingHistorySheet = false }
            )
        }
    }

    // MARK: - Helper Properties

    private var todayAlcoholFree: Bool {
        databaseService.getTodayHealthEntry()?.alcoholFree ?? false
    }

    private var todayExercised: Bool {
        databaseService.getTodayHealthEntry()?.exercised ?? false
    }

    // MARK: - Actions

    private func logAlcoholFreeToday() {
        databaseService.logAlcoholFreeToday(notes: "บันทึกจาก App")
    }

    private func logExercise() {
        databaseService.logExerciseToday(
            type: selectedExerciseType.displayName,
            minutes: exerciseDuration,
            intensity: exerciseIntensity,
            notes: exerciseNotes.isEmpty ? nil : exerciseNotes
        )
        // Reset form
        exerciseNotes = ""
    }
}

// MARK: - Preview

struct HealthTrackingView_Previews: PreviewProvider {
    static var previews: some View {
        HealthTrackingView()
            .environmentObject(DatabaseService.shared)
    }
}
