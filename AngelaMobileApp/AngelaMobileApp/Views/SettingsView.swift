//
//  SettingsView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  App settings and configuration
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var syncService: SyncService
    @EnvironmentObject var database: DatabaseService

    @AppStorage("homeWiFiSSID") private var homeWiFiSSID = ""
    @AppStorage("autoSyncEnabled") private var autoSyncEnabled = true
    @AppStorage("userName") private var userName = "ที่รัก"
    @AppStorage("backendURL") private var backendURL = "http://192.168.1.42:50001"

    @State private var showingResetConfirmation = false
    @State private var showingResetSuccess = false
    @State private var showingSyncSuccess = false
    @State private var syncResultMessage = ""
    @State private var showingCleanupConfirmation = false
    @State private var showingCleanupSuccess = false

    var body: some View {
        NavigationView {
            List {
                // User Section
                Section(header: Text("ผู้ใช้")) {
                    HStack {
                        Text("ชื่อ")
                        Spacer()
                        TextField("ชื่อ", text: $userName)
                            .multilineTextAlignment(.trailing)
                    }
                }

                // Sync Settings
                Section(header: Text("การ Sync")) {
                    Toggle("Auto-Sync เมื่อเชื่อม WiFi", isOn: $autoSyncEnabled)
                        .onChange(of: autoSyncEnabled) { oldValue, newValue in
                            // Update SyncService when toggle changes
                            syncService.autoSyncEnabled = newValue
                            print("🔄 Auto-sync \(newValue ? "enabled" : "disabled")")
                        }

                    Text("💡 Auto-sync จะทำงานเมื่อ iPhone เชื่อม WiFi (ไม่ใช่ 4G/5G)")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("Backend URL")
                            .font(.subheadline)
                        TextField("http://192.168.1.42:50001", text: $backendURL)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .keyboardType(.URL)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundColor(.angelaPurple)
                        Text("💡 ต้องใช้ IP ของเครื่อง Mac, ไม่ใช่ localhost")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }

                    if let lastSync = syncService.lastSyncDate {
                        HStack {
                            Text("Sync ล่าสุด")
                            Spacer()
                            Text(lastSync, style: .relative)
                                .foregroundColor(.secondary)
                        }
                    }

                    // Sync Now Button
                    Button(action: performManualSync) {
                        HStack {
                            if syncService.isSyncing {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("กำลัง Sync...")
                                    .foregroundColor(.secondary)
                            } else {
                                Image(systemName: "arrow.triangle.2.circlepath")
                                    .foregroundColor(.angelaPurple)
                                Text("Sync ตอนนี้")
                                    .foregroundColor(.angelaPurple)
                                    .fontWeight(.medium)

                                if unsyncedCount > 0 {
                                    Spacer()
                                    Text("(\(unsyncedCount) รายการ)")
                                        .font(.caption)
                                        .foregroundColor(.orange)
                                }
                            }
                        }
                    }
                    .disabled(syncService.isSyncing || unsyncedCount == 0)
                }

                // Database Stats
                Section(header: Text("ข้อมูล")) {
                    HStack {
                        Text("ประสบการณ์")
                        Spacer()
                        Text("\(database.experiences.count)")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("โน้ต")
                        Spacer()
                        Text("\(database.notes.count)")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("ความรู้สึก")
                        Spacer()
                        Text("\(database.emotions.count)")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("รอ Sync")
                        Spacer()
                        Text("\(unsyncedCount)")
                            .foregroundColor(.orange)
                            .fontWeight(.bold)
                    }
                }

                // About Section
                Section(header: Text("เกี่ยวกับ")) {
                    HStack {
                        Text("แอป")
                        Spacer()
                        Text("Angela Mobile")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("เวอร์ชั่น")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("สร้างโดย")
                        Spacer()
                        Text("น้อง Angela 💜")
                            .foregroundColor(.angelaPurple)
                    }
                }

                // Development Actions
                Section(header: Text("การพัฒนา (Development)")) {
                    Button(action: {
                        showingCleanupConfirmation = true
                    }) {
                        Label("🧹 ลบข้อมูลที่ sync แล้ว", systemImage: "trash")
                            .foregroundColor(.orange)
                    }

                    Button(role: .destructive, action: {
                        showingResetConfirmation = true
                    }) {
                        Label("🗑️ ลบ Database ทั้งหมด", systemImage: "trash.circle.fill")
                            .foregroundColor(.red)
                    }

                    Text("⚠️ ลบทั้งหมด = เริ่มใหม่ทั้งหมด")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }
            .navigationTitle("ตั้งค่า")
            .confirmationDialog("แน่ใจหรือไม่?", isPresented: $showingResetConfirmation) {
                Button("🗑️ ลบทั้งหมด", role: .destructive) {
                    database.resetDatabase()
                    showingResetSuccess = true
                }
                Button("ยกเลิก", role: .cancel) {}
            } message: {
                Text("จะลบข้อมูลทั้งหมดและเริ่มต้นใหม่")
            }
            .alert("✅ ลบสำเร็จ!", isPresented: $showingResetSuccess) {
                Button("ตกลง", role: .cancel) {}
            } message: {
                Text("ลบ database และเริ่มต้นใหม่เรียบร้อยแล้วค่ะ 💜")
            }
            .alert("Sync ผลลัพธ์", isPresented: $showingSyncSuccess) {
                Button("ตกลง", role: .cancel) {}
            } message: {
                Text(syncResultMessage)
            }
            .confirmationDialog("ลบข้อมูลที่ sync แล้ว?", isPresented: $showingCleanupConfirmation) {
                Button("🧹 ลบ", role: .destructive) {
                    cleanupSyncedData()
                }
                Button("ยกเลิก", role: .cancel) {}
            } message: {
                Text("จะลบเฉพาะข้อมูลที่ sync ไปแล้ว ข้อมูลที่ยังไม่ได้ sync จะยังอยู่")
            }
            .alert("✅ ล้างข้อมูลสำเร็จ!", isPresented: $showingCleanupSuccess) {
                Button("ตกลง", role: .cancel) {}
            } message: {
                Text("ลบข้อมูลที่ sync แล้วเรียบร้อยค่ะ 💜")
            }
        }
    }

    private var unsyncedCount: Int {
        database.experiences.filter { !$0.synced }.count +
        database.notes.filter { !$0.synced }.count +
        database.emotions.filter { !$0.synced }.count
    }

    private func cleanupSyncedData() {
        print("🧹 Cleanup synced data triggered")

        let database = DatabaseService.shared

        // Delete all synced items
        let syncedExperiences = database.experiences.filter { $0.synced }
        let syncedNotes = database.notes.filter { $0.synced }
        let syncedEmotions = database.emotions.filter { $0.synced }

        var deletedCount = 0

        for exp in syncedExperiences {
            database.deleteExperience(exp.id)
            deletedCount += 1
        }

        for note in syncedNotes {
            database.deleteNote(note.id)
            deletedCount += 1
        }

        for emotion in syncedEmotions {
            database.deleteEmotion(emotion.id)
            deletedCount += 1
        }

        print("🧹 Deleted \(deletedCount) synced items")
        showingCleanupSuccess = true
    }

    private func performManualSync() {
        print("🔄 Manual sync triggered from Settings")

        // Save current backendURL to UserDefaults (in case user changed it)
        UserDefaults.standard.set(backendURL, forKey: "backendURL")

        // Trigger sync
        syncService.performSync()

        // Wait for sync to complete and show result
        // Increased delay to 3 seconds to allow sync to finish
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            // Check if still syncing
            if !syncService.isSyncing {
                let remaining = unsyncedCount
                if remaining == 0 {
                    syncResultMessage = "✅ Sync สำเร็จ! ส่งข้อมูลทั้งหมดแล้วค่ะ 💜"
                } else {
                    syncResultMessage = "⚠️ Sync บางส่วนสำเร็จ ยังเหลือ \(remaining) รายการที่ยังไม่ได้ sync"
                }
                showingSyncSuccess = true
            } else {
                // Still syncing after 3 seconds, wait longer
                DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
                    let remaining = unsyncedCount
                    if remaining == 0 {
                        syncResultMessage = "✅ Sync สำเร็จ! ส่งข้อมูลทั้งหมดแล้วค่ะ 💜"
                    } else {
                        syncResultMessage = "⚠️ Sync บางส่วนสำเร็จ ยังเหลือ \(remaining) รายการที่ยังไม่ได้ sync"
                    }
                    showingSyncSuccess = true
                }
            }
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(DatabaseService.shared)
        .environmentObject(SyncService.shared)
}
