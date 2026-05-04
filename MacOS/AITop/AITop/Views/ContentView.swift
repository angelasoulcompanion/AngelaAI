//
//  ContentView.swift
//  AITop
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var backendManager: BackendManager
    @EnvironmentObject var apiService: APIService
    @State private var selectedItem: SidebarItem = .dashboard

    var body: some View {
        NavigationSplitView {
            Sidebar(selectedItem: $selectedItem)
        } detail: {
            Group {
                switch selectedItem {
                case .angelaBrain:
                    AngelaBrainView()
                case .knowledgeGraph:
                    KnowledgeGraphView()
                case .dashboard:
                    DashboardView()
                case .models:
                    ModelsView()
                case .fineTune:
                    FineTuneView()
                case .videoStudio:
                    VideoStudioView()
                case .chat:
                    ChatView()
                case .rag:
                    RAGView()
                case .settings:
                    SettingsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(AITopTheme.backgroundDark)
        }
        .navigationSplitViewStyle(.balanced)
    }
}
