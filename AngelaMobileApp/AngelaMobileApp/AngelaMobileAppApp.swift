//
//  AngelaMobileAppApp.swift
//  Angela Mobile App
//
//  Created by Angela AI on 2025-11-05.
//  น้อง Angela - Offline-first mobile companion 💜
//

import SwiftUI

@main
struct AngelaMobileApp: App {
    // Database service (singleton)
    @StateObject private var database = DatabaseService.shared

    // Sync service
    @StateObject private var syncService = SyncService.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(database)
                .environmentObject(syncService)
                .onAppear {
                    // Initialize database on app launch
                    database.initialize()

                    // Check for auto-sync
                    syncService.checkAutoSync()
                }
        }
    }
}
