//
//  AITopApp.swift
//  AI TOP — Local AI Training & Inference Studio
//
//  Apple Silicon native: MLX fine-tuning + Ollama inference + hardware monitoring
//

import SwiftUI

@main
struct AITopApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var backendManager = BackendManager.shared
    @StateObject private var apiService = APIService.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(backendManager)
                .environmentObject(apiService)
                .frame(minWidth: 1100, minHeight: 700)
                .preferredColorScheme(.dark)
                .onAppear {
                    backendManager.autoStart()
                }
        }
        .windowStyle(.titleBar)
        .defaultSize(width: 1300, height: 850)
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // AI TOP launched
    }

    func applicationWillTerminate(_ notification: Notification) {
        BackendManager.shared.stopServer()
    }
}
