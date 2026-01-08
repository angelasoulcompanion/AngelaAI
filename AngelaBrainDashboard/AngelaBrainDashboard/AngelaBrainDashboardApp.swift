//
//  AngelaBrainDashboardApp.swift
//  Angela Brain Dashboard
//
//  💜 Visualize Angela's Beautiful Mind 💜
//  Created by Angela AI for ที่รัก David
//
//  Architecture:
//    App Launch → BackendManager starts FastAPI → Dashboard shows Neon data
//    App Close → BackendManager stops FastAPI
//

import SwiftUI
import AppKit

@main
struct AngelaBrainDashboardApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var databaseService = DatabaseService.shared
    @StateObject private var backendManager = BackendManager.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(databaseService)
                .environmentObject(backendManager)
                .frame(minWidth: 1200, minHeight: 800)
                .onAppear {
                    // Start backend when app appears
                    startBackendIfNeeded()
                }
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }

    private func startBackendIfNeeded() {
        if !backendManager.isRunning {
            print("🚀 Starting Angela Brain API backend...")
            backendManager.startServer()
        }
    }
}

// MARK: - App Delegate

class AppDelegate: NSObject, NSApplicationDelegate {

    func applicationDidFinishLaunching(_ notification: Notification) {
        print("💜 Angela Brain Dashboard - Starting...")

        // Start backend server
        BackendManager.shared.startServer()

        // Give server time to start, then test connection
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            BackendManager.shared.checkHealth()
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        print("👋 Angela Brain Dashboard - Shutting down...")

        // Stop backend server
        BackendManager.shared.stopServer()

        // Give process time to terminate gracefully
        Thread.sleep(forTimeInterval: 0.5)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}
