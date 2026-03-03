//
//  ContentView.swift
//  Pythia
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @EnvironmentObject var backendManager: BackendManager
    @State private var selectedItem: SidebarItem = .marketOverview

    var body: some View {
        NavigationSplitView {
            Sidebar(selectedItem: $selectedItem)
        } detail: {
            Group {
                switch selectedItem {
                case .dashboard:
                    DashboardView()
                case .portfolios:
                    PortfolioListView()
                case .transactions:
                    TransactionsView()
                case .marketOverview:
                    MarketOverviewView()
                case .marketBreadth:
                    MarketBreadthView()
                case .watchlist:
                    WatchlistView()
                case .settings:
                    SettingsView()

                // Analysis
                case .mpt:
                    MPTView()
                case .valueAtRisk:
                    VaRView()
                case .stressTest:
                    StressTestView()
                case .performance:
                    PerformanceView()
                case .correlation:
                    CorrelationView()

                // Market / Tools
                case .optionsChain:
                    OptionsChainView()
                case .backtest:
                    BacktestView()
                case .monteCarlo:
                    MonteCarloView()
                case .technical:
                    TechnicalView()
                case .statistics:
                    StatisticsView()

                // AI Insights
                case .aiAdvisor:
                    AIAdvisorView()
                case .sentiment:
                    SentimentView()
                case .forecast:
                    ForecastView()
                case .research:
                    ResearchRAGView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(PythiaTheme.backgroundDark)
        }
        .navigationSplitViewStyle(.balanced)
        .onChange(of: backendManager.isConnected) { _, connected in
            if connected {
                Task { await databaseService.checkConnection() }
            }
        }
    }
}

// MARK: - Coming Soon Placeholder

struct ComingSoonView: View {
    let title: String
    let icon: String

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(PythiaTheme.accentGold)

            Text(title)
                .font(PythiaTheme.title())
                .foregroundColor(PythiaTheme.textPrimary)

            Text("Coming in a future phase")
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
