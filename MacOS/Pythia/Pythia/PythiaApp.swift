//
//  PythiaApp.swift
//  Pythia — Quantitative Finance + AI Analysis Platform
//
//  Created: 2026-03-01
//

import SwiftUI

@main
struct PythiaApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var databaseService = DatabaseService.shared
    @StateObject private var backendManager = BackendManager.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(databaseService)
                .environmentObject(backendManager)
                .frame(minWidth: 1200, minHeight: 800)
                .preferredColorScheme(.dark)
                .onAppear {
                    backendManager.autoStart()
                }
        }
        .windowStyle(.titleBar)
        .defaultSize(width: 1400, height: 900)
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Pythia app launched
    }

    func applicationWillTerminate(_ notification: Notification) {
        BackendManager.shared.stopServer()
    }
}
