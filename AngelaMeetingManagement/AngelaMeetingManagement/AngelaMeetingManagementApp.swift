//
//  AngelaMeetingManagementApp.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  Date: 2025-11-19
//

import SwiftUI

@main
struct AngelaMeetingManagementApp: App {
    @StateObject private var databaseService = DatabaseService.shared
    @StateObject private var themeManager = ThemeManager.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(databaseService)
                .environmentObject(themeManager)
                .frame(minWidth: 1000, minHeight: 600)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
    }
}
