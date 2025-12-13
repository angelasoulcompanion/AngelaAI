//
//  MeetingManagerApp.swift
//  MeetingManager
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  Date: 2025-11-19
//

import SwiftUI

@main
struct MeetingManagerApp: App {
    @StateObject private var databaseService = DatabaseService.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(databaseService)
                .frame(minWidth: 1000, minHeight: 600)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
    }
}
