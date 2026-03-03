//
//  DashboardView.swift
//  Pythia
//

import SwiftUI
import Charts

struct DashboardView: View {
    @EnvironmentObject var db: DatabaseService
    @EnvironmentObject var backendManager: BackendManager
    @State private var summary: DashboardSummary?
    @State private var breakdown: [AssetTypeBreakdown] = []
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Dashboard")
                            .font(PythiaTheme.title())
                            .foregroundColor(PythiaTheme.textPrimary)
                        Text("Pythia — Quantitative Finance Platform")
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                    Spacer()
                    // Connection status
                    HStack(spacing: 6) {
                        Circle()
                            .fill(db.isConnected ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                            .frame(width: 8, height: 8)
                        Text(db.isConnected ? "Connected" : "Disconnected")
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }

                if isLoading {
                    LoadingView("Loading dashboard...")
                        .frame(height: 300)
                } else if let summary = summary {
                    // KPI Cards
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                    ], spacing: PythiaTheme.spacing) {
                        StatCardView(
                            title: "Portfolios",
                            value: "\(summary.portfolioCount)",
                            icon: "briefcase.fill",
                            color: PythiaTheme.secondaryBlue
                        )
                        StatCardView(
                            title: "Total Value",
                            value: PythiaTheme.formatCurrency(summary.totalPortfolioValue),
                            icon: "banknote.fill",
                            color: PythiaTheme.accentGold
                        )
                        StatCardView(
                            title: "Assets Tracked",
                            value: "\(summary.assetCount)",
                            icon: "chart.bar.fill",
                            color: PythiaTheme.profit
                        )
                        StatCardView(
                            title: "Price Data Points",
                            value: formatNumber(summary.priceDataPoints),
                            icon: "chart.xyaxis.line",
                            color: PythiaTheme.accentBlue
                        )
                    }

                    // Second row
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                        GridItem(.flexible()),
                    ], spacing: PythiaTheme.spacing) {
                        StatCardView(
                            title: "Holdings",
                            value: "\(summary.holdingCount)",
                            icon: "list.bullet.rectangle",
                            color: PythiaTheme.darkGold
                        )
                        StatCardView(
                            title: "Recent Transactions",
                            value: "\(summary.recentTransactions)",
                            subtitle: "Last 30 days",
                            icon: "arrow.left.arrow.right",
                            color: PythiaTheme.infoBlue
                        )
                        StatCardView(
                            title: "Watchlists",
                            value: "\(summary.watchlistCount)",
                            icon: "star.fill",
                            color: PythiaTheme.warningOrange
                        )
                    }

                    // Asset Type Breakdown
                    if !breakdown.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Portfolio Allocation by Asset Type")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)

                            Chart(breakdown) { item in
                                BarMark(
                                    x: .value("Type", item.assetType.replacingOccurrences(of: "_", with: " ").capitalized),
                                    y: .value("Value", item.totalValue)
                                )
                                .foregroundStyle(PythiaTheme.secondaryBlue.gradient)
                                .cornerRadius(4)
                            }
                            .chartYAxis {
                                AxisMarks(position: .leading)
                            }
                            .frame(height: 200)
                        }
                        .padding()
                        .pythiaCard()
                    }
                } else if errorMessage != nil {
                    VStack(spacing: 16) {
                        EmptyStateView(
                            icon: "exclamationmark.triangle",
                            title: "Error Loading Dashboard",
                            message: "Could not connect to the server."
                        )
                        if !backendManager.isConnected {
                            Text("Starting backend...")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textTertiary)
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Button("Retry") { Task { await loadDashboard() } }
                                .pythiaPrimaryButton()
                        }
                    }
                } else {
                    EmptyStateView(
                        icon: "chart.bar.xaxis.ascending.badge.clock",
                        title: "Welcome to Pythia",
                        message: "Create your first portfolio to get started.",
                        actionTitle: "Create Portfolio"
                    )
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            await loadDashboard()
        }
        .onChange(of: backendManager.isConnected) { _, connected in
            if connected && summary == nil {
                Task { await loadDashboard() }
            }
        }
    }

    private func loadDashboard() async {
        isLoading = true
        do {
            summary = try await db.fetchDashboardSummary()
            breakdown = try await db.fetchPortfolioBreakdown()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func formatNumber(_ value: Int) -> String {
        if value >= 1_000_000 {
            return String(format: "%.1fM", Double(value) / 1_000_000)
        } else if value >= 1_000 {
            return String(format: "%.1fK", Double(value) / 1_000)
        }
        return "\(value)"
    }
}
