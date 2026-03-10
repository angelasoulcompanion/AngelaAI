//
//  Sidebar.swift
//  AITop
//

import SwiftUI

enum SidebarItem: String, CaseIterable, Identifiable {
    case dashboard
    case models
    case fineTune
    case chat
    case rag
    case settings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .dashboard: return "Dashboard"
        case .models: return "Models"
        case .fineTune: return "Fine-Tune"
        case .chat: return "Chat"
        case .rag: return "RAG"
        case .settings: return "Settings"
        }
    }

    var icon: String {
        switch self {
        case .dashboard: return "gauge.with.dots.needle.33percent"
        case .models: return "cpu.fill"
        case .fineTune: return "wand.and.stars"
        case .chat: return "bubble.left.and.bubble.right.fill"
        case .rag: return "doc.text.magnifyingglass"
        case .settings: return "gearshape.fill"
        }
    }

    var group: String {
        switch self {
        case .dashboard: return "MONITOR"
        case .models, .fineTune: return "AI STUDIO"
        case .chat, .rag: return "INFERENCE"
        case .settings: return "CONFIG"
        }
    }
}

struct Sidebar: View {
    @Binding var selectedItem: SidebarItem
    @EnvironmentObject var backendManager: BackendManager

    private let groups: [(String, [SidebarItem])] = [
        ("MONITOR", [.dashboard]),
        ("AI STUDIO", [.models, .fineTune]),
        ("INFERENCE", [.chat, .rag]),
        ("CONFIG", [.settings]),
    ]

    var body: some View {
        VStack(spacing: 0) {
            // App title
            HStack(spacing: 8) {
                Image(systemName: "brain.head.profile.fill")
                    .font(.system(size: 20))
                    .foregroundColor(AITopTheme.accentOrange)
                Text("AI TOP")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(AITopTheme.textPrimary)
            }
            .padding(.vertical, 16)

            AITopDivider()

            List(selection: $selectedItem) {
                ForEach(groups, id: \.0) { group, items in
                    Section(group) {
                        ForEach(items) { item in
                            Label(item.title, systemImage: item.icon)
                                .tag(item)
                        }
                    }
                }
            }
            .listStyle(.sidebar)

            AITopDivider()

            // Backend status
            HStack(spacing: 6) {
                Circle()
                    .fill(backendManager.isConnected ? AITopTheme.success : AITopTheme.error)
                    .frame(width: 8, height: 8)
                Text(backendManager.statusMessage)
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                    .lineLimit(1)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
        .frame(minWidth: 200)
        .background(AITopTheme.backgroundDark)
    }
}
