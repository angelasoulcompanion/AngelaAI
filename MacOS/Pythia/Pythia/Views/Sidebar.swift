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
    case regime
    case factors

    // Trading (Phase 7)
    case signalDashboard
    case strategyBuilder
    case screener
    case tradePlans
    case patterns

    // AI Insights
    case aiAdvisor
    case sentiment
    case forecast
    case research
    case narrative

    // Market
    case globalMonitor
    case marketOverview
    case marketBreadth
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
        case .regime: return "Regime Detection"
        case .factors: return "Factor Analysis"
        case .signalDashboard: return "Signal Dashboard"
        case .strategyBuilder: return "Strategy Builder"
        case .screener: return "Screener"
        case .tradePlans: return "Trade Plans"
        case .patterns: return "Patterns"
        case .aiAdvisor: return "AI Advisor"
        case .sentiment: return "Sentiment"
        case .forecast: return "Forecast"
        case .research: return "Research RAG"
        case .narrative: return "Market Narrative"
        case .globalMonitor: return "Global Monitor"
        case .marketOverview: return "Market Overview"
        case .marketBreadth: return "Market Breadth"
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
        case .regime: return "waveform.path.ecg"
        case .factors: return "chart.bar.fill"
        case .signalDashboard: return "antenna.radiowaves.left.and.right"
        case .strategyBuilder: return "gearshape.2.fill"
        case .screener: return "magnifyingglass"
        case .tradePlans: return "list.clipboard.fill"
        case .patterns: return "chart.xyaxis.line"
        case .aiAdvisor: return "brain.head.profile"
        case .sentiment: return "newspaper.fill"
        case .forecast: return "chart.line.flattrend.xyaxis"
        case .research: return "books.vertical.fill"
        case .narrative: return "doc.text.fill"
        case .globalMonitor: return "globe.americas.fill"
        case .marketOverview: return "globe"
        case .marketBreadth: return "chart.bar.doc.horizontal.fill"
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
        case .mpt, .valueAtRisk, .stressTest, .performance, .correlation, .regime, .factors: return "ANALYSIS"
        case .signalDashboard, .strategyBuilder, .screener, .tradePlans, .patterns: return "TRADING"
        case .aiAdvisor, .sentiment, .forecast, .research, .narrative: return "AI INSIGHTS"
        case .globalMonitor, .marketOverview, .marketBreadth, .optionsChain, .watchlist: return "MARKET"
        case .backtest, .monteCarlo, .technical, .statistics: return "TOOLS"
        case .settings: return "SETTINGS"
        }
    }
}

struct Sidebar: View {
    @Binding var selectedItem: SidebarItem
    @State private var collapsed: Set<String> = []

    private let groups: [(String, [SidebarItem])] = [
        ("DASHBOARD", [.globalMonitor, .marketOverview, .marketBreadth, .dashboard]),
        ("PORTFOLIO", [.portfolios, .transactions]),
        ("ANALYSIS", [.mpt, .regime, .factors, .valueAtRisk, .stressTest, .performance, .correlation, .optionsChain]),
        ("TRADING", [.signalDashboard, .strategyBuilder, .screener, .tradePlans, .patterns]),
        ("AI INSIGHTS", [.aiAdvisor, .sentiment, .forecast, .research, .narrative]),
        ("TOOLS", [.backtest, .monteCarlo, .technical, .statistics]),
        ("SETTINGS", [.watchlist, .settings]),
    ]

    var body: some View {
        List(selection: $selectedItem) {
            ForEach(groups, id: \.0) { group, items in
                Section {
                    if !collapsed.contains(group) {
                        ForEach(items) { item in
                            Label(item.title, systemImage: item.icon)
                                .tag(item)
                        }
                    }
                } header: {
                    Button {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            if collapsed.contains(group) {
                                collapsed.remove(group)
                            } else {
                                collapsed.insert(group)
                            }
                        }
                    } label: {
                        HStack {
                            Text(group)
                            Spacer()
                            Image(systemName: collapsed.contains(group) ? "chevron.right" : "chevron.down")
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(PythiaTheme.textTertiary)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 220)
        .background(PythiaTheme.backgroundDark)
    }
}
