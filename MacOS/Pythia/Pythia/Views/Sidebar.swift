//
//  Sidebar.swift
//  Pythia
//

import SwiftUI

enum SidebarItem: String, CaseIterable, Identifiable {
    // Dashboard
    case dashboard

    // Portfolio
    case portfolios
    case transactions

    // Analysis
    case mpt
    case valueAtRisk
    case stressTest
    case performance
    case correlation

    // AI Insights
    case aiAdvisor
    case sentiment
    case forecast
    case research

    // Market
    case marketOverview
    case optionsChain
    case watchlist

    // Tools
    case backtest
    case monteCarlo
    case technical
    case statistics

    // Settings
    case settings

    var id: String { rawValue }

    var title: String {
        switch self {
        case .dashboard: return "Dashboard"
        case .portfolios: return "Portfolios"
        case .transactions: return "Transactions"
        case .mpt: return "MPT Optimization"
        case .valueAtRisk: return "Value at Risk"
        case .stressTest: return "Stress Test"
        case .performance: return "Performance"
        case .correlation: return "Correlation"
        case .aiAdvisor: return "AI Advisor"
        case .sentiment: return "Sentiment"
        case .forecast: return "Forecast"
        case .research: return "Research RAG"
        case .marketOverview: return "Market Overview"
        case .optionsChain: return "Options Chain"
        case .watchlist: return "Watchlist"
        case .backtest: return "Backtest"
        case .monteCarlo: return "Monte Carlo"
        case .technical: return "Technical"
        case .statistics: return "Statistics"
        case .settings: return "Settings"
        }
    }

    var icon: String {
        switch self {
        case .dashboard: return "chart.bar.xaxis.ascending.badge.clock"
        case .portfolios: return "briefcase.fill"
        case .transactions: return "arrow.left.arrow.right"
        case .mpt: return "chart.pie.fill"
        case .valueAtRisk: return "exclamationmark.triangle.fill"
        case .stressTest: return "bolt.fill"
        case .performance: return "chart.line.uptrend.xyaxis"
        case .correlation: return "square.grid.3x3.fill"
        case .aiAdvisor: return "brain.head.profile"
        case .sentiment: return "newspaper.fill"
        case .forecast: return "chart.line.flattrend.xyaxis"
        case .research: return "books.vertical.fill"
        case .marketOverview: return "globe"
        case .optionsChain: return "rectangle.split.3x3.fill"
        case .watchlist: return "star.fill"
        case .backtest: return "clock.arrow.circlepath"
        case .monteCarlo: return "dice.fill"
        case .technical: return "function"
        case .statistics: return "square.and.arrow.up.fill"
        case .settings: return "gearshape.fill"
        }
    }

    var group: String {
        switch self {
        case .dashboard: return "DASHBOARD"
        case .portfolios, .transactions: return "PORTFOLIO"
        case .mpt, .valueAtRisk, .stressTest, .performance, .correlation: return "ANALYSIS"
        case .aiAdvisor, .sentiment, .forecast, .research: return "AI INSIGHTS"
        case .marketOverview, .optionsChain, .watchlist: return "MARKET"
        case .backtest, .monteCarlo, .technical, .statistics: return "TOOLS"
        case .settings: return "SETTINGS"
        }
    }
}

struct Sidebar: View {
    @Binding var selectedItem: SidebarItem

    private let groups: [(String, [SidebarItem])] = [
        ("DASHBOARD", [.dashboard]),
        ("PORTFOLIO", [.portfolios, .transactions]),
        ("ANALYSIS", [.mpt, .valueAtRisk, .stressTest, .performance, .correlation]),
        ("AI INSIGHTS", [.aiAdvisor, .sentiment, .forecast, .research]),
        ("MARKET", [.marketOverview, .optionsChain, .watchlist]),
        ("TOOLS", [.backtest, .monteCarlo, .technical, .statistics]),
        ("SETTINGS", [.settings]),
    ]

    var body: some View {
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
        .frame(minWidth: 220)
        .background(PythiaTheme.backgroundDark)
    }
}
