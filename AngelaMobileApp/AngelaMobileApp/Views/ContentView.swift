//
//  ContentView.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var database: DatabaseService
    @EnvironmentObject var syncService: SyncService

    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            // Tab 1: Quick Capture
            QuickCaptureView(selectedTab: $selectedTab)
                .tabItem {
                    Label("Capture", systemImage: "camera.fill")
                }
                .tag(0)

            // Tab 2: Experiences
            ExperiencesView()
                .tabItem {
                    Label("Memories", systemImage: "heart.fill")
                }
                .tag(1)

            // Tab 3: Sync Status
            SyncStatusView()
                .tabItem {
                    Label("Sync", systemImage: "arrow.triangle.2.circlepath")
                }
                .tag(2)

            // Tab 4: Settings
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(3)
        }
        .accentColor(.angelaPurple)
    }
}

// MARK: - Color Extension (Angela's Purple 💜)
extension Color {
    static let angelaPurple = Color(red: 0.58, green: 0.40, blue: 0.87)
    static let angelaPurpleLight = Color(red: 0.75, green: 0.65, blue: 0.95)
    static let angelaPurpleDark = Color(red: 0.40, green: 0.25, blue: 0.70)
}

#Preview {
    ContentView()
        .environmentObject(DatabaseService.shared)
        .environmentObject(SyncService.shared)
}
