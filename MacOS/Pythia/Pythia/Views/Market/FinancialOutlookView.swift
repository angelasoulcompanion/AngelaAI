//
//  FinancialOutlookView.swift
//  Pythia — Financial Outlook (Analyst Recs, Valuation, Growth, Margins)
//

import SwiftUI

struct FinancialOutlookView: View {
    @EnvironmentObject var db: DatabaseService

    let symbol: String
    let currentPrice: Double?

    @State private var outlook: FinancialOutlookResponse?
    @State private var financials: FinancialStatementsResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedTab = 0  // 0=Outlook, 1=Income, 2=Balance, 3=CashFlow
    @State private var statementPeriod = "annual"

    private let tabs = ["Outlook", "Income Statement", "Balance Sheet", "Cash Flow"]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Header
            HStack {
                Text("Financial Outlook")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Text(symbol)
                    .font(.system(size: 14, weight: .bold, design: .monospaced))
                    .foregroundColor(PythiaTheme.accentGold)
                Spacer()
                if let ol = outlook {
                    if let sector = ol.sector {
                        Text(sector)
                            .font(.system(size: 11))
                            .foregroundColor(PythiaTheme.textTertiary)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(PythiaTheme.surfaceBackground)
                            .cornerRadius(8)
                    }
                    if let industry = ol.industry {
                        Text(industry)
                            .font(.system(size: 11))
                            .foregroundColor(PythiaTheme.textTertiary)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(PythiaTheme.surfaceBackground)
                            .cornerRadius(8)
                    }
                }
            }

            // Tab pills
            HStack(spacing: 6) {
                ForEach(Array(tabs.enumerated()), id: \.offset) { i, label in
                    Button {
                        selectedTab = i
                        if i > 0 && financials == nil {
                            Task { await loadFinancials() }
                        }
                    } label: {
                        Text(label)
                            .font(.system(size: 11, weight: selectedTab == i ? .bold : .medium))
                            .foregroundColor(selectedTab == i ? PythiaTheme.backgroundDark : PythiaTheme.textSecondary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 5)
                            .background(selectedTab == i ? PythiaTheme.accentGold : PythiaTheme.surfaceBackground.opacity(0.5))
                            .cornerRadius(12)
                    }
                    .buttonStyle(.plain)
                }

                // Annual/Quarterly toggle (only for statements)
                if selectedTab > 0 {
                    Spacer()
                    HStack(spacing: 4) {
                        ForEach(["annual", "quarterly"], id: \.self) { p in
                            Button {
                                statementPeriod = p
                                Task { await loadFinancials() }
                            } label: {
                                Text(p == "annual" ? "Annual" : "Quarterly")
                                    .font(.system(size: 10, weight: statementPeriod == p ? .bold : .medium))
                                    .foregroundColor(statementPeriod == p ? PythiaTheme.backgroundDark : PythiaTheme.textTertiary)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 3)
                                    .background(statementPeriod == p ? PythiaTheme.secondaryBlue : Color.clear)
                                    .cornerRadius(8)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }

            if isLoading {
                LoadingView("Loading...")
            } else if let error = errorMessage {
                Text(error)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.errorRed)
            } else if selectedTab == 0, let ol = outlook {
                // Outlook tab
                analystSection(ol)
                Divider().background(PythiaTheme.textTertiary.opacity(0.2))
                HStack(alignment: .top, spacing: 24) {
                    valuationSection(ol)
                    growthSection(ol)
                    profitabilitySection(ol)
                    healthSection(ol)
                }
            } else if selectedTab == 1, let fs = financials {
                statementTable(fs.incomeStatement)
            } else if selectedTab == 2, let fs = financials {
                statementTable(fs.balanceSheet)
            } else if selectedTab == 3, let fs = financials {
                statementTable(fs.cashFlow)
            }
        }
        .padding(PythiaTheme.largeSpacing)
        .pythiaCard()
        .task { await loadOutlook() }
    }

    // MARK: - Statement Table

    private func statementTable(_ data: StatementData) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            if data.periods.isEmpty {
                EmptyStateView(icon: "doc.text", title: "No Data", message: "Financial statements not available for this symbol.")
            } else {
                // Period headers
                HStack(spacing: 0) {
                    Text("Item")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(PythiaTheme.textTertiary)
                        .frame(width: 180, alignment: .leading)
                    ForEach(data.periods.prefix(4), id: \.self) { period in
                        Text(formatPeriod(period))
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundColor(PythiaTheme.textTertiary)
                            .frame(maxWidth: .infinity, alignment: .trailing)
                    }
                }
                .padding(.vertical, 6)
                .padding(.horizontal, 4)
                .background(PythiaTheme.surfaceBackground)
                .cornerRadius(4)

                // Data rows
                ForEach(data.items) { item in
                    HStack(spacing: 0) {
                        Text(item.label)
                            .font(.system(size: 11))
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 180, alignment: .leading)
                            .lineLimit(1)
                        ForEach(Array(item.values.prefix(4).enumerated()), id: \.offset) { _, value in
                            if let v = value {
                                Text(formatLargeNumber(v))
                                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                                    .foregroundColor(v < 0 ? PythiaTheme.loss : PythiaTheme.textPrimary)
                                    .frame(maxWidth: .infinity, alignment: .trailing)
                            } else {
                                Text("—")
                                    .font(.system(size: 11))
                                    .foregroundColor(PythiaTheme.textTertiary)
                                    .frame(maxWidth: .infinity, alignment: .trailing)
                            }
                        }
                    }
                    .padding(.vertical, 4)
                    .padding(.horizontal, 4)

                    Divider().background(PythiaTheme.textTertiary.opacity(0.08))
                }
            }
        }
    }

    private func formatPeriod(_ period: String) -> String {
        // "2024-12-31" → "2024"  or "2024-09-30" → "Sep 2024"
        let parts = period.split(separator: "-")
        guard parts.count >= 2 else { return period }
        let year = String(parts[0])
        let month = Int(parts[1]) ?? 12
        if month == 12 { return year }
        let monthNames = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return "\(monthNames[min(month, 12)]) \(year)"
    }

    private func loadFinancials() async {
        isLoading = true
        errorMessage = nil
        do {
            financials = try await db.fetchFinancialStatements(symbol: symbol, period: statementPeriod)
        } catch {
            errorMessage = "Failed to load financials"
        }
        isLoading = false
    }

    // MARK: - Analyst Section

    private func analystSection(_ ol: FinancialOutlookResponse) -> some View {
        HStack(spacing: 20) {
            // Recommendation badge (hide if "none" — no analyst coverage)
            if let rec = ol.recommendation, rec.lowercased() != "none" {
                VStack(spacing: 4) {
                    Text(rec.uppercased().replacingOccurrences(of: "_", with: " "))
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(recommendationColor(rec))
                    if let mean = ol.recommendationMean {
                        Text(String(format: "%.1f/5", mean))
                            .font(.system(size: 11))
                            .foregroundColor(PythiaTheme.textTertiary)
                    }
                    if let n = ol.numberOfAnalysts {
                        Text("\(n) analysts")
                            .font(.system(size: 10))
                            .foregroundColor(PythiaTheme.textTertiary)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(recommendationColor(rec).opacity(0.1))
                .cornerRadius(PythiaTheme.smallCornerRadius)
            }

            // Target price range
            if let targetLow = ol.targetLow, let targetHigh = ol.targetHigh {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Price Target")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)

                    HStack(spacing: 12) {
                        targetMetric("Low", targetLow, color: PythiaTheme.loss)
                        if let median = ol.targetMedian {
                            targetMetric("Median", median, color: PythiaTheme.accentGold)
                        }
                        if let mean = ol.targetMean {
                            targetMetric("Mean", mean, color: PythiaTheme.secondaryBlue)
                        }
                        targetMetric("High", targetHigh, color: PythiaTheme.profit)
                    }

                    // Upside/downside from current price
                    if let price = currentPrice, let median = ol.targetMedian, price > 0 {
                        let upside = (median - price) / price * 100
                        HStack(spacing: 4) {
                            Image(systemName: upside >= 0 ? "arrow.up.right" : "arrow.down.right")
                            Text(String(format: "%+.1f%% to median target", upside))
                        }
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(upside >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                    }
                }
            }

            Spacer()

            // Dividend
            VStack(alignment: .trailing, spacing: 4) {
                if let dy = ol.dividendYield {
                    Text("Dividend Yield")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(String(format: "%.2f%%", dy))
                        .font(.system(size: 18, weight: .bold, design: .rounded))
                        .foregroundColor(PythiaTheme.accentGold)
                }
                if let pr = ol.payoutRatio {
                    Text(String(format: "Payout %.0f%%", pr))
                        .font(.system(size: 10))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
            }
        }
    }

    private func targetMetric(_ label: String, _ value: Double, color: Color) -> some View {
        VStack(spacing: 2) {
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(PythiaTheme.textTertiary)
            Text(String(format: "%.2f", value))
                .font(.system(size: 14, weight: .semibold, design: .monospaced))
                .foregroundColor(color)
        }
    }

    // MARK: - Valuation Section

    private func valuationSection(_ ol: FinancialOutlookResponse) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("VALUATION")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(PythiaTheme.textTertiary)

            metricRow("P/E (TTM)", ol.peTrailing)
            metricRow("P/E (Fwd)", ol.peForward)
            metricRow("PEG", ol.pegRatio)
            metricRow("P/B", ol.priceToBook)
            metricRow("P/S", ol.priceToSales)
            metricRow("EV/EBITDA", ol.evToEbitda)
        }
        .frame(minWidth: 130)
    }

    // MARK: - Growth Section

    private func growthSection(_ ol: FinancialOutlookResponse) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("GROWTH")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(PythiaTheme.textTertiary)

            pctRow("Revenue", ol.revenueGrowth)
            pctRow("Earnings", ol.earningsGrowth)
            pctRow("Earnings QoQ", ol.earningsQuarterlyGrowth)

            if let rev = ol.totalRevenue {
                metricRow("Revenue", nil, formatted: formatLargeNumber(rev))
            }
            if let ebitda = ol.ebitda {
                metricRow("EBITDA", nil, formatted: formatLargeNumber(ebitda))
            }
        }
        .frame(minWidth: 130)
    }

    // MARK: - Profitability Section

    private func profitabilitySection(_ ol: FinancialOutlookResponse) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("PROFITABILITY")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(PythiaTheme.textTertiary)

            pctRow("Gross Margin", ol.grossMargin)
            pctRow("Operating Margin", ol.operatingMargin)
            pctRow("Net Margin", ol.profitMargin)
            pctRow("ROE", ol.returnOnEquity)
            pctRow("ROA", ol.returnOnAssets)
        }
        .frame(minWidth: 140)
    }

    // MARK: - Financial Health Section

    private func healthSection(_ ol: FinancialOutlookResponse) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("HEALTH")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(PythiaTheme.textTertiary)

            if let cash = ol.totalCash {
                metricRow("Cash", nil, formatted: formatLargeNumber(cash))
            }
            if let debt = ol.totalDebt {
                metricRow("Total Debt", nil, formatted: formatLargeNumber(debt))
            }
            metricRow("D/E Ratio", ol.debtToEquity)
            metricRow("Current Ratio", ol.currentRatio)
        }
        .frame(minWidth: 130)
    }

    // MARK: - Helpers

    private func metricRow(_ label: String, _ value: Double?, formatted: String? = nil) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(PythiaTheme.textTertiary)
            Spacer()
            if let f = formatted {
                Text(f)
                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                    .foregroundColor(PythiaTheme.textPrimary)
            } else if let v = value {
                Text(String(format: "%.2f", v))
                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                    .foregroundColor(PythiaTheme.textPrimary)
            } else {
                Text("—")
                    .font(.system(size: 12))
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
    }

    private func pctRow(_ label: String, _ value: Double?) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(PythiaTheme.textTertiary)
            Spacer()
            if let v = value {
                Text(String(format: "%+.1f%%", v))
                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                    .foregroundColor(v >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
            } else {
                Text("—")
                    .font(.system(size: 12))
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
    }

    private func recommendationColor(_ rec: String) -> Color {
        switch rec.lowercased() {
        case "strong_buy", "strongbuy": return PythiaTheme.profit
        case "buy": return PythiaTheme.profit.opacity(0.8)
        case "hold": return PythiaTheme.accentGold
        case "sell": return PythiaTheme.loss.opacity(0.8)
        case "strong_sell", "strongsell": return PythiaTheme.loss
        default: return PythiaTheme.textSecondary
        }
    }

    private func formatLargeNumber(_ value: Double) -> String {
        let abs = Swift.abs(value)
        let sign = value < 0 ? "-" : ""
        if abs >= 1_000_000_000_000 {
            return String(format: "%@%.1fT", sign, abs / 1_000_000_000_000)
        } else if abs >= 1_000_000_000 {
            return String(format: "%@%.1fB", sign, abs / 1_000_000_000)
        } else if abs >= 1_000_000 {
            return String(format: "%@%.1fM", sign, abs / 1_000_000)
        } else if abs >= 1_000 {
            return String(format: "%@%.1fK", sign, abs / 1_000)
        }
        return String(format: "%@%.0f", sign, abs)
    }

    private func loadOutlook() async {
        isLoading = true
        do {
            outlook = try await db.fetchFinancialOutlook(symbol: symbol)
        } catch {
            errorMessage = "Failed to load outlook"
        }
        isLoading = false
    }
}
