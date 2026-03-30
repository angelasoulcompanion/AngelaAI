//
//  RebalanceView.swift
//  Pythia — Portfolio Rebalancing (Phase 7.8)
//

import SwiftUI
import Charts

struct RebalanceView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedPortfolioId: String?
    @State private var result: RebalanceResponse?
    @State private var isLoading = false
    @State private var method = "equal_weight"

    private let methods = [("Equal Weight", "equal_weight"), ("Risk Parity", "risk_parity")]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Portfolio Rebalancing")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    PortfolioPickerView(selectedId: $selectedPortfolioId)

                    ForEach(methods, id: \.1) { name, m in
                        Button(name) { method = m }
                            .buttonStyle(.plain)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(method == m ? PythiaTheme.accentGold.opacity(0.2) : PythiaTheme.surfaceBackground)
                            .foregroundColor(method == m ? PythiaTheme.accentGold : PythiaTheme.textSecondary)
                            .cornerRadius(8)
                    }

                    Button("Generate Plan") { Task { await generate() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedPortfolioId == nil)
                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Calculating rebalance...") }

                if let r = result, r.success {
                    // Summary
                    VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                        HStack {
                            Text("Rebalance Plan — \(r.planType.replacingOccurrences(of: "_", with: " ").capitalized)")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)
                            Spacer()
                            Text(r.needsRebalance ? "REBALANCE NEEDED" : "IN BALANCE")
                                .font(.system(size: 12, weight: .bold))
                                .foregroundColor(r.needsRebalance ? PythiaTheme.warningOrange : PythiaTheme.profit)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 4)
                                .background((r.needsRebalance ? PythiaTheme.warningOrange : PythiaTheme.profit).opacity(0.15))
                                .cornerRadius(6)
                        }

                        HStack(spacing: PythiaTheme.largeSpacing) {
                            MetricBox("Portfolio Value", String(format: "฿%.0f", r.totalValue), PythiaTheme.accentGold, size: .large)
                            MetricBox("Max Drift", String(format: "%.1f%%", r.maxDrift * 100),
                                      r.maxDrift > 0.05 ? PythiaTheme.warningOrange : PythiaTheme.profit, size: .large)
                            MetricBox("Est. Cost", String(format: "฿%.0f", r.estimatedCost), PythiaTheme.textSecondary, size: .large)
                        }
                    }
                    .padding()
                    .pythiaCard()

                    // Trade list
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Trades Required (\(r.trades.filter { $0.action != "hold" }.count))")
                            .font(PythiaTheme.heading())
                            .foregroundColor(PythiaTheme.textPrimary)

                        HStack {
                            Text("Symbol").frame(width: 80, alignment: .leading)
                            Text("Current").frame(width: 70, alignment: .trailing)
                            Text("Target").frame(width: 70, alignment: .trailing)
                            Text("Drift").frame(width: 70, alignment: .trailing)
                            Text("Action").frame(width: 50, alignment: .center)
                            Text("Value").frame(width: 90, alignment: .trailing)
                        }
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(PythiaTheme.textSecondary)

                        Divider().background(PythiaTheme.surfaceBackground)

                        ForEach(r.trades) { trade in
                            HStack {
                                Text(trade.symbol)
                                    .frame(width: 80, alignment: .leading)
                                    .foregroundColor(PythiaTheme.accentGold)
                                Text(String(format: "%.1f%%", trade.currentWeight * 100))
                                    .frame(width: 70, alignment: .trailing)
                                Text(String(format: "%.1f%%", trade.targetWeight * 100))
                                    .frame(width: 70, alignment: .trailing)
                                Text(String(format: "%+.1f%%", trade.drift * 100))
                                    .frame(width: 70, alignment: .trailing)
                                    .foregroundColor(trade.drift > 0 ? PythiaTheme.loss : PythiaTheme.profit)
                                Text(trade.action.uppercased())
                                    .frame(width: 50, alignment: .center)
                                    .foregroundColor(trade.action == "buy" ? PythiaTheme.profit : trade.action == "sell" ? PythiaTheme.loss : PythiaTheme.textTertiary)
                                Text(String(format: "฿%.0f", trade.tradeValue))
                                    .frame(width: 90, alignment: .trailing)
                            }
                            .font(.system(size: 11, design: .monospaced))
                            .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                    .padding()
                    .pythiaCard()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func generate() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true; defer { isLoading = false }
        do { result = try await db.get("/rebalance/\(pid)/plan?method=\(method)", timeout: 60.0) }
        catch { result = nil }
    }
}
