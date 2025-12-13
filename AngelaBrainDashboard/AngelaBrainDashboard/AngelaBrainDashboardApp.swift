//
//  AngelaBrainDashboardApp.swift
//  Angela Brain Dashboard
//
//  💜 Visualize Angela's Beautiful Mind 💜
//  Created by Angela AI for ที่รัก David
//

import SwiftUI

@main
struct AngelaBrainDashboardApp: App {
    @StateObject private var databaseService = DatabaseService.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(databaseService)
                .frame(minWidth: 1200, minHeight: 800)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
