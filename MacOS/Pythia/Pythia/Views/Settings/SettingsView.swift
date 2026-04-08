//
//  SettingsView.swift
//  Pythia
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var db: DatabaseService
    @EnvironmentObject var backend: BackendManager
    @EnvironmentObject var pageVisibility: PageVisibilityManager
    @State private var settings: [AppSetting] = []
    @State private var isLoading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                Text("Settings")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Connection Status
                VStack(alignment: .leading, spacing: 12) {
                    Text("Connection")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)

                    HStack(spacing: 16) {
                        StatusRow(label: "Backend", isConnected: backend.isRunning, detail: backend.statusMessage)
                        StatusRow(label: "Database", isConnected: db.isConnected, detail: db.isConnected ? "Neon Cloud (Singapore)" : "Disconnected")
                    }
                }
                .padding()
                .pythiaCard()

                // App Info
                VStack(alignment: .leading, spacing: 12) {
                    Text("About")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)

                    HStack {
                        Image(systemName: "building.columns.fill")
                            .font(.system(size: 32))
                            .foregroundColor(PythiaTheme.accentGold)
                        VStack(alignment: .leading) {
                            Text("Pythia")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(PythiaTheme.textPrimary)
                            Text("Quantitative Finance + AI Analysis Platform")
                                .font(PythiaTheme.body())
                                .foregroundColor(PythiaTheme.textSecondary)
                            Text("Version 1.0.0 · Port 8766")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textTertiary)
                        }
                    }
                }
                .padding()
                .pythiaCard()

                // Page Manager
                pageManagerSection

                // Database Settings
                if !settings.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Database Settings")
                            .font(PythiaTheme.headline())
                            .foregroundColor(PythiaTheme.textPrimary)

                        ForEach(settings) { setting in
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(setting.settingKey)
                                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                                        .foregroundColor(PythiaTheme.textPrimary)
                                    if let desc = setting.description {
                                        Text(desc)
                                            .font(PythiaTheme.caption())
                                            .foregroundColor(PythiaTheme.textTertiary)
                                    }
                                }
                                Spacer()
                                Text(setting.settingValue ?? "—")
                                    .font(.system(size: 13, design: .monospaced))
                                    .foregroundColor(PythiaTheme.accentGold)
                                if let cat = setting.category {
                                    Text(cat)
                                        .font(.system(size: 10))
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(PythiaTheme.surfaceBackground)
                                        .cornerRadius(4)
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .pythiaCard()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            do {
                settings = try await db.fetchSettings()
            } catch { }
            isLoading = false
        }
    }

    // MARK: - Page Manager

    private let pageGroups: [(String, [SidebarItem])] = [
        ("DASHBOARD", [.globalMonitor, .marketOverview, .marketBreadth, .earningsCalendar, .dashboard, .alerts]),
        ("PORTFOLIO", [.portfolios, .transactions, .rebalance]),
        ("ANALYSIS", [.mpt, .regime, .factors, .riskBudget, .valueAtRisk, .stressTest, .performance, .correlation, .optionsChain, .optionStrategy]),
        ("TRADING", [.signalDashboard, .alphaML, .alphaIdeas, .strategyBuilder, .screener, .tradePlans, .patterns, .events]),
        ("AI INSIGHTS", [.aiAdvisor, .sentiment, .forecast, .research, .narrative]),
        ("TOOLS", [.backtest, .monteCarlo, .technical, .statistics]),
    ]

    private var pageManagerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Page Manager")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("\(visibleCount)/\(totalCount) visible")
                    .font(.system(size: 11))
                    .foregroundColor(PythiaTheme.textTertiary)
                Button("Show All") { pageVisibility.showAll() }
                    .buttonStyle(.plain)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(PythiaTheme.accentGold)
            }

            Text("Toggle pages on/off in the sidebar")
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)

            ForEach(pageGroups, id: \.0) { group, items in
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(group)
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(PythiaTheme.textSecondary)
                        Spacer()
                        groupToggleButtons(group: group, items: items)
                    }
                    .padding(.top, 6)

                    LazyVGrid(columns: [
                        GridItem(.flexible(), spacing: 8),
                        GridItem(.flexible(), spacing: 8),
                        GridItem(.flexible(), spacing: 8),
                    ], spacing: 6) {
                        ForEach(items) { item in
                            pageToggleRow(item)
                        }
                    }
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func groupToggleButtons(group: String, items: [SidebarItem]) -> some View {
        HStack(spacing: 8) {
            Button("All") {
                for item in items { pageVisibility.setVisible(item, visible: true) }
            }
            .buttonStyle(.plain)
            .font(.system(size: 10, weight: .medium))
            .foregroundColor(PythiaTheme.profit)

            Button("None") {
                for item in items { pageVisibility.setVisible(item, visible: false) }
            }
            .buttonStyle(.plain)
            .font(.system(size: 10, weight: .medium))
            .foregroundColor(PythiaTheme.loss)
        }
    }

    private func pageToggleRow(_ item: SidebarItem) -> some View {
        let visible = pageVisibility.isVisible(item)
        return Button {
            pageVisibility.toggle(item)
        } label: {
            HStack(spacing: 6) {
                Image(systemName: item.icon)
                    .font(.system(size: 11))
                    .frame(width: 16)
                    .foregroundColor(visible ? PythiaTheme.accentGold : PythiaTheme.textTertiary.opacity(0.4))
                Text(item.title)
                    .font(.system(size: 11))
                    .foregroundColor(visible ? PythiaTheme.textPrimary : PythiaTheme.textTertiary.opacity(0.4))
                    .lineLimit(1)
                Spacer()
                Image(systemName: visible ? "eye.fill" : "eye.slash")
                    .font(.system(size: 10))
                    .foregroundColor(visible ? PythiaTheme.profit : PythiaTheme.textTertiary.opacity(0.3))
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 5)
            .background(visible ? PythiaTheme.surfaceBackground.opacity(0.4) : PythiaTheme.surfaceBackground.opacity(0.1))
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }

    private var visibleCount: Int {
        pageGroups.flatMap(\.1).filter { pageVisibility.isVisible($0) }.count
    }

    private var totalCount: Int {
        pageGroups.flatMap(\.1).count
    }
}

struct StatusRow: View {
    let label: String
    let isConnected: Bool
    let detail: String

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(isConnected ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                .frame(width: 10, height: 10)
            VStack(alignment: .leading) {
                Text(label)
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Text(detail)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(PythiaTheme.surfaceBackground.opacity(0.3))
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }
}
