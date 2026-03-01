//
//  MPTView.swift
//  Pythia — Modern Portfolio Theory Optimization
//

import SwiftUI
import Charts

struct MPTView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var portfolios: [Portfolio] = []
    @State private var selectedPortfolioId: String?
    @State private var optimizationType = "max_sharpe"
    @State private var result: OptimizationResponse?
    @State private var frontier: EfficientFrontierResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let optimizationTypes = [
        ("max_sharpe", "Max Sharpe"),
        ("min_volatility", "Min Volatility"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                // Header
                Text("MPT Optimization")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                controlsCard

                if isLoading {
                    LoadingView("Optimizing portfolio...")
                } else if let error = errorMessage {
                    Text(error)
                        .foregroundColor(PythiaTheme.errorRed)
                        .padding()
                }

                // Results
                if let result = result {
                    optimizationResultCard(result)
                }

                // Efficient Frontier
                if let frontier = frontier, !frontier.points.isEmpty {
                    efficientFrontierChart(frontier)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadPortfolios() }
    }

    // MARK: - Controls

    private var controlsCard: some View {
        HStack(spacing: PythiaTheme.spacing) {
            Picker("Portfolio", selection: Binding(
                get: { selectedPortfolioId ?? "" },
                set: { selectedPortfolioId = $0.isEmpty ? nil : $0 }
            )) {
                Text("Select Portfolio").tag("")
                ForEach(portfolios) { p in
                    Text(p.name).tag(p.portfolioId)
                }
            }
            .frame(width: 200)

            Picker("Type", selection: $optimizationType) {
                ForEach(optimizationTypes, id: \.0) { val, label in
                    Text(label).tag(val)
                }
            }
            .frame(width: 160)

            Button("Optimize") {
                Task { await runOptimization() }
            }
            .pythiaPrimaryButton()
            .disabled(selectedPortfolioId == nil)

            Spacer()
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Result Card

    private func optimizationResultCard(_ r: OptimizationResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text("Optimal Allocation")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if r.success {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(PythiaTheme.profit)
                }
            }

            // KPI row
            HStack(spacing: PythiaTheme.largeSpacing) {
                metricBox("Expected Return", PythiaTheme.formatPercent(r.expectedReturn), PythiaTheme.profit)
                metricBox("Volatility", PythiaTheme.formatPercent(r.volatility), PythiaTheme.accentGold)
                metricBox("Sharpe Ratio", String(format: "%.3f", r.sharpeRatio), PythiaTheme.secondaryBlue)
            }

            Divider().background(PythiaTheme.textTertiary)

            // Weights table
            Text("Optimal Weights")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.fixed(100), alignment: .trailing),
                GridItem(.fixed(200)),
            ], spacing: 8) {
                Text("Symbol").font(PythiaTheme.caption()).foregroundColor(PythiaTheme.textTertiary)
                Text("Weight").font(PythiaTheme.caption()).foregroundColor(PythiaTheme.textTertiary)
                Text("").font(PythiaTheme.caption())

                ForEach(r.weights.sorted(by: { $0.value > $1.value }), id: \.key) { symbol, weight in
                    Text(symbol)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(PythiaTheme.formatPercent(weight))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.accentGold)
                    ProgressView(value: weight)
                        .tint(PythiaTheme.secondaryBlue)
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Efficient Frontier

    private func efficientFrontierChart(_ f: EfficientFrontierResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Efficient Frontier")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart {
                ForEach(f.points) { point in
                    PointMark(
                        x: .value("Risk", point.risk * 100),
                        y: .value("Return", point.returnValue * 100)
                    )
                    .foregroundStyle(PythiaTheme.secondaryBlue)
                    .symbolSize(30)
                }

                ForEach(f.points) { point in
                    LineMark(
                        x: .value("Risk", point.risk * 100),
                        y: .value("Return", point.returnValue * 100)
                    )
                    .foregroundStyle(PythiaTheme.accentGold.opacity(0.6))
                    .lineStyle(StrokeStyle(lineWidth: 2))
                }
            }
            .chartXAxisLabel("Risk (Volatility %)")
            .chartYAxisLabel("Expected Return %")
            .chartXAxis {
                AxisMarks { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    AxisValueLabel()
                        .foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .chartYAxis {
                AxisMarks { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                        .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    AxisValueLabel()
                        .foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .frame(height: 350)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Helpers

    private func metricBox(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(minWidth: 120)
    }

    // MARK: - Data

    private func loadPortfolios() async {
        do { portfolios = try await db.fetchPortfolios() } catch {}
    }

    private func runOptimization() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true
        errorMessage = nil
        do {
            result = try await db.optimizePortfolio(portfolioId: pid, type: optimizationType)
            if !(result?.success ?? false) {
                errorMessage = result?.message
            }
            frontier = try await db.fetchEfficientFrontier(portfolioId: pid)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
