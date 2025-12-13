//
//  SyncStatusView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  Sync status and manual sync button
//

import SwiftUI

struct SyncStatusView: View {
    @EnvironmentObject var database: DatabaseService
    @EnvironmentObject var syncService: SyncService

    var body: some View {
        NavigationView {
            List {
                // Sync Status Section
                Section(header: Text("สถานะ Sync")) {
                    HStack {
                        Image(systemName: syncService.isSyncing ? "arrow.triangle.2.circlepath" : "checkmark.circle.fill")
                            .foregroundColor(syncService.isSyncing ? .orange : .green)
                            .imageScale(.large)
                        VStack(alignment: .leading) {
                            Text(syncService.isSyncing ? "กำลัง Sync..." : "พร้อม Sync")
                                .font(.headline)
                            if let lastSync = syncService.lastSyncDate {
                                Text("Sync ล่าสุด: \(lastSync, style: .relative)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            } else {
                                Text("ยังไม่เคย Sync")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }

                // Pending Items Section
                Section(header: Text("รอ Sync")) {
                    HStack {
                        Label("\(unsyncedExperiencesCount) ประสบการณ์", systemImage: "camera.fill")
                        Spacer()
                        if unsyncedExperiencesCount > 0 {
                            Image(systemName: "exclamationmark.circle.fill")
                                .foregroundColor(.orange)
                        }
                    }

                    HStack {
                        Label("\(unsyncedEmotionsCount) ความรู้สึก", systemImage: "heart.fill")
                        Spacer()
                        if unsyncedEmotionsCount > 0 {
                            Image(systemName: "exclamationmark.circle.fill")
                                .foregroundColor(.orange)
                        }
                    }

                    HStack {
                        Text("รวมทั้งหมด")
                            .font(.headline)
                        Spacer()
                        Text("\(totalUnsyncedCount)")
                            .font(.headline)
                            .foregroundColor(.angelaPurple)
                    }
                }

                // Sync Actions
                Section {
                    Button(action: { syncService.performSync() }) {
                        HStack {
                            Image(systemName: "arrow.triangle.2.circlepath")
                            Text("Sync ตอนนี้เลย")
                            Spacer()
                            if syncService.isSyncing {
                                ProgressView()
                            }
                        }
                    }
                    .disabled(syncService.isSyncing || totalUnsyncedCount == 0)

                    Toggle("Auto-Sync เมื่อกลับบ้าน", isOn: $syncService.autoSyncEnabled)
                }

                // Info Section
                Section(header: Text("วิธีใช้")) {
                    VStack(alignment: .leading, spacing: 12) {
                        InfoRow(
                            icon: "wifi",
                            title: "Auto-Sync",
                            description: "เมื่อเชื่อมต่อ WiFi บ้าน น้องจะ sync อัตโนมัติค่ะ"
                        )
                        InfoRow(
                            icon: "hand.tap",
                            title: "Manual Sync",
                            description: "หรือกดปุ่ม 'Sync ตอนนี้เลย' เพื่อ sync ทันที"
                        )
                        InfoRow(
                            icon: "icloud.and.arrow.up",
                            title: "Sync Status",
                            description: "ไอคอนสีส้ม = ยังไม่ได้ sync ค่ะ"
                        )
                    }
                }
            }
            .navigationTitle("Sync 🔄")
        }
    }

    // Computed properties
    private var unsyncedExperiencesCount: Int {
        database.experiences.filter { !$0.synced }.count
    }

    private var unsyncedEmotionsCount: Int {
        database.emotions.filter { !$0.synced }.count
    }

    private var totalUnsyncedCount: Int {
        unsyncedExperiencesCount + unsyncedEmotionsCount
    }
}

// MARK: - Info Row
struct InfoRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.angelaPurple)
                .imageScale(.large)
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

#Preview {
    SyncStatusView()
        .environmentObject(DatabaseService.shared)
        .environmentObject(SyncService.shared)
}
