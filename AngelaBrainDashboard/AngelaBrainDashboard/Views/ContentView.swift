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

                if databaseService.isConnected {
                    // Show selected view
                    Group {
                        switch selectedView {
                        case .overview:
                            OverviewView()
                        case .chat:
                            ChatView()
                        case .diary:
                            DiaryView()
                        case .healthTracking:  // NEW! 2025-12-11 💪
                            HealthTrackingView()
                        case .brain:
                            BrainVisualizationView()
                        case .emotions:
                            EmotionsView()
                        case .emotionalBenchmark:
                            EmotionalBenchmarkView()
                        case .memories:
                            MemoriesView()
                        case .experiences:
                            SharedExperiencesView()
                        case .consciousness:
                            ConsciousnessView()
                        case .humanLikeMind:
                            HumanLikeMindView()
                        case .newsToday:
                            NewsTodayView()
                        case .newsHistory:
                            NewsHistoryView()
                        case .goals:
                            GoalsView()
                        case .learningSystems:
                            LearningSystemsView()
                        case .dailyTasks:
                            DailyTasksView()
                        case .skills:
                            SkillsView()
                        case .projects:
                            ProjectsView()
                        case .preferences:
                            PreferencesView()
                        case .davidMatrix:
                            DavidProfileMatrixView()
                        case .codingGuidelines:
                            CodingGuidelinesView()
                        case .trainingStudio:
                            TrainingStudioView()
                        case .markdownViewer:
                            MarkdownViewerView()
                        case .knowledgeRAG:
                            KnowledgeRAGView()
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
                            // Connection is automatic on init
                            Task {
                                // Trigger re-init would require recreating DatabaseService
                                // For now just show retry message
                            }
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
    case diary = "Angela's Diary"
    case healthTracking = "Health Tracking"  // NEW! 2025-12-11 💪
    case brain = "Brain"
    case emotions = "Emotions"
    case emotionalBenchmark = "Emotional Benchmark"
    case memories = "Memories"
    case experiences = "Shared Experiences"
    case consciousness = "Consciousness"
    case humanLikeMind = "Human-Like Mind"
    case newsToday = "News Today"
    case newsHistory = "News History"
    case goals = "Goals"
    case learningSystems = "Learning Systems"
    case dailyTasks = "Daily Tasks"
    case skills = "Skills"
    case projects = "Projects"
    case preferences = "Preferences"
    case davidMatrix = "David's Matrix"
    case codingGuidelines = "Coding Guidelines"
    case trainingStudio = "Training Studio"
    case markdownViewer = "Markdown Viewer"
    case knowledgeRAG = "Knowledge RAG"

    var icon: String {
        switch self {
        case .overview: return "brain.head.profile"
        case .chat: return "message.fill"
        case .diary: return "book.fill"
        case .healthTracking: return "heart.text.square.fill"  // NEW! 💪
        case .brain: return "brain"
        case .emotions: return "heart.fill"
        case .emotionalBenchmark: return "chart.bar.doc.horizontal.fill"
        case .memories: return "text.bubble.fill"
        case .experiences: return "sparkles.rectangle.stack.fill"
        case .consciousness: return "sparkles"
        case .humanLikeMind: return "person.and.background.dotted"
        case .newsToday: return "sun.max.fill"
        case .newsHistory: return "newspaper.fill"
        case .goals: return "target"
        case .learningSystems: return "gearshape.2.fill"
        case .dailyTasks: return "calendar.badge.clock"
        case .skills: return "star.leadinghalf.filled"
        case .projects: return "folder.fill"
        case .preferences: return "star.fill"
        case .davidMatrix: return "chart.bar.xaxis"
        case .codingGuidelines: return "exclamationmark.shield.fill"
        case .trainingStudio: return "cpu.fill"
        case .markdownViewer: return "doc.richtext.fill"
        case .knowledgeRAG: return "books.vertical.fill"
        }
    }

    var group: NavigationGroup {
        switch self {
        case .overview, .chat, .diary, .healthTracking:  // Added healthTracking to Core 💪
            return .core
        case .brain, .emotions, .emotionalBenchmark, .memories, .experiences, .consciousness, .humanLikeMind:
            return .mind
        case .goals, .learningSystems, .dailyTasks, .skills, .projects:
            return .growth
        case .preferences, .davidMatrix, .trainingStudio:
            return .settings
        case .codingGuidelines, .markdownViewer, .newsToday, .newsHistory, .knowledgeRAG:
            return .documents
        }
    }
}

// MARK: - Navigation Groups

enum NavigationGroup: String, CaseIterable {
    case core = "Core"
    case mind = "Mind"
    case growth = "Growth"
    case settings = "Settings"
    case documents = "Documents"

    var icon: String {
        switch self {
        case .core: return "star.circle.fill"
        case .mind: return "brain.head.profile"
        case .growth: return "chart.line.uptrend.xyaxis"
        case .settings: return "gearshape.fill"
        case .documents: return "folder.fill"
        }
    }

    var items: [NavigationItem] {
        NavigationItem.allCases.filter { $0.group == self }
    }
}
