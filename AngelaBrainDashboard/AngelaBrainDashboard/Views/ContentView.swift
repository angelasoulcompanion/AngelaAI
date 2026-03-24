//
//  ContentView.swift
//  Angela Brain Dashboard
//
//  💜 Main Container View 💜
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @State private var selectedView: NavigationItem = .overview

    var body: some View {
        NavigationSplitView {
            // Sidebar
            Sidebar(selectedView: $selectedView)
        } detail: {
            // Main content area
            ZStack {
                AngelaTheme.backgroundDark
                    .ignoresSafeArea()

                if databaseService.isConnecting {
                    // Connecting state - show progress
                    VStack(spacing: 24) {
                        ProgressView()
                            .scaleEffect(1.5)
                            .progressViewStyle(CircularProgressViewStyle(tint: AngelaTheme.primaryPurple))

                        Text("Connecting to Supabase...")
                            .font(AngelaTheme.headline())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Text("Tokyo • Supabase")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textSecondary)
                    }
                } else if databaseService.isConnected {
                    // Show selected view
                    Group {
                        switch selectedView {
                        case .overview:
                            OverviewView()
                        case .chat:
                            ChatView()
                        case .claudeChat:
                            ClaudeChatView()
                        case .djAngela:
                            DJAngelaView()
                        case .djayPro:
                            DJayProView()
                        case .executiveNews:
                            ExecutiveNewsView()
                        case .learningSystems:
                            LearningSystemsView()
                        case .dailyTasks:
                            DailyTasksView()
                        case .scheduledTasks:
                            ScheduledTasksView()
                        case .skills:
                            SkillsView()
                        case .projects:
                            ProjectsView()
                        case .thingsOverview:
                            ThingsOverviewView()
                        case .preferences:
                            PreferencesView()
                        case .codingGuidelines:
                            CodingGuidelinesView()
                        case .codingTechniques:
                            Text("Coding Techniques").font(.title)
                        case .uiPatterns:
                            Text("UI/UX Patterns").font(.title)
                        case .openClaw:
                            OpenClawView()
                        case .controlCenter:
                            ControlCenterView()
                        case .trainingStudio:
                            TrainingStudioView()
                        case .markdownViewer:
                            MarkdownViewerView()
                        case .knowledgeRAG:
                            KnowledgeRAGView()
                        case .davidResume:
                            ResumeView()
                        }
                    }
                    .transition(.opacity)
                } else {
                    // Connection error state
                    VStack(spacing: 20) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.orange)

                        Text("Database Connection Error")
                            .font(AngelaTheme.title())
                            .foregroundColor(AngelaTheme.textPrimary)

                        if let error = databaseService.errorMessage {
                            Text(error)
                                .font(AngelaTheme.body())
                                .foregroundColor(AngelaTheme.textSecondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 40)
                        }

                        Button {
                            databaseService.retryConnection()
                        } label: {
                            Text("Retry Connection")
                                .angelaPrimaryButton()
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

// MARK: - Navigation Items

enum NavigationItem: String, CaseIterable {
    case overview = "Overview"
    case chat = "Chat with Angela"
    case claudeChat = "Claude Chat"
    case djAngela = "DJ Angela"
    case djayPro = "DJAY PRO"
    case thingsOverview = "Things"
    case projects = "Projects"
    case learningSystems = "Learning Systems"
    case codingTechniques = "Coding Techniques"
    case uiPatterns = "UI/UX Patterns"
    case codingGuidelines = "Coding Guidelines"
    case openClaw = "OpenClaw"
    case skills = "Skills"
    case knowledgeRAG = "Knowledge RAG"
    case executiveNews = "Executive News"
    case scheduledTasks = "Scheduled Tasks"
    case dailyTasks = "Daily Tasks"
    case preferences = "Preferences"
    case controlCenter = "Control Center"
    case trainingStudio = "Training Studio"
    case markdownViewer = "Markdown Viewer"
    case davidResume = "David's Resume"

    var icon: String {
        switch self {
        case .overview: return "brain.head.profile"
        case .chat: return "message.fill"
        case .claudeChat: return "bubble.left.and.text.bubble.right.fill"
        case .djAngela: return "music.note.tv"
        case .djayPro: return "dial.medium.fill"
        case .thingsOverview: return "checklist"
        case .projects: return "folder.fill"
        case .learningSystems: return "gearshape.2.fill"
        case .codingTechniques: return "chevron.left.forwardslash.chevron.right"
        case .uiPatterns: return "paintbrush.fill"
        case .codingGuidelines: return "exclamationmark.shield.fill"
        case .openClaw: return "hand.raised.fingers.spread.fill"
        case .skills: return "star.leadinghalf.filled"
        case .knowledgeRAG: return "books.vertical.fill"
        case .executiveNews: return "newspaper.fill"
        case .scheduledTasks: return "clock.badge.checkmark"
        case .dailyTasks: return "calendar.badge.clock"
        case .preferences: return "star.fill"
        case .controlCenter: return "gearshape.2.fill"
        case .trainingStudio: return "cpu.fill"
        case .markdownViewer: return "doc.richtext.fill"
        case .davidResume: return "doc.text.fill"
        }
    }

    var group: NavigationGroup {
        switch self {
        case .overview, .chat, .claudeChat, .djAngela, .djayPro, .thingsOverview:
            return .core
        case .projects, .learningSystems, .codingTechniques, .uiPatterns, .codingGuidelines:
            return .work
        case .openClaw, .skills, .knowledgeRAG, .executiveNews, .scheduledTasks, .dailyTasks:
            return .tools
        case .preferences, .controlCenter, .trainingStudio, .markdownViewer, .davidResume:
            return .settings
        }
    }
}

// MARK: - Navigation Groups

enum NavigationGroup: String, CaseIterable {
    case core = "Core"
    case work = "Work"
    case tools = "Tools"
    case settings = "Settings"

    var icon: String {
        switch self {
        case .core: return "star.circle.fill"
        case .work: return "hammer.fill"
        case .tools: return "wrench.and.screwdriver.fill"
        case .settings: return "gearshape.fill"
        }
    }

    var items: [NavigationItem] {
        NavigationItem.allCases.filter { $0.group == self }
    }
}
