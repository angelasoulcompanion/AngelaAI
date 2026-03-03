//
//  VaRView.swift
//  Pythia — Value at Risk Analysis
//

import SwiftUI
import Charts

struct VaRView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedPortfolioId: String?
    @State private var method = "historical"
    @State private var confidence = 0.95
    @State private var holdingPeriod = 1

    @State private var varResult: VaRResponse?
    @State private var componentVaR: ComponentVaRResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let methods = [
        ("historical", "Historical"),
        ("parametric", "Parametric"),
        ("monte_carlo", "Monte Carlo"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Value at Risk")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                controlsCard

                if isLoading {
                    LoadingView("Calculating VaR...")
                } else if let error = errorMessage {
                    ErrorMessageView(message: error)
                }

                if let r = varResult, r.success {
                    varResultCard(r)
                }

                if let comp = componentVaR, let components = comp.components, !components.isEmpty {
                    componentVaRCard(comp.portfolioVarPct ?? 0, components)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private var controlsCard: some View {
        HStack(spacing: PythiaTheme.spacing) {
            PortfolioPickerView(selectedId: $selectedPortfolioId)

            Picker("Method", selection: $method) {
                ForEach(methods, id: \.0) { val, label in
                    Text(label).tag(val)
                }
            }
            .frame(width: 140)

            Picker("Confidence", selection: $confidence) {
                Text("95%").tag(0.95)
                Text("99%").tag(0.99)
            }
            .frame(width: 100)

            Button("Calculate") {
                Task { await calculate() }
            }
            .pythiaPrimaryButton()
            .disabled(selectedPortfolioId == nil)

            Spacer()
        }
        .padding()
        .pythiaCard()
    }

    private func varResultCard(_ r: VaRResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text("VaR Results — \(r.method.capitalized)")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text("\(Int(r.confidenceLevel * 100))% Confidence")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.accentGold)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(PythiaTheme.accentGold.opacity(0.15))
                    .cornerRadius(4)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Portfolio Value", PythiaTheme.formatCurrency(r.portfolioValue), PythiaTheme.textPrimary, size: .medium)
                MetricBox("VaR", PythiaTheme.formatCurrency(r.varValue), PythiaTheme.loss, size: .medium)
                MetricBox("VaR %", PythiaTheme.formatPercent(abs(r.varPercent)), PythiaTheme.loss, size: .medium)
                MetricBox("CVaR (ES)", PythiaTheme.formatCurrency(r.cvarValue), PythiaTheme.errorRed, size: .medium)
                MetricBox("CVaR %", PythiaTheme.formatPercent(abs(r.cvarPercent)), PythiaTheme.errorRed, size: .medium)
            }

            // Gauge visualization
            HStack(spacing: 20) {
                riskGauge("VaR", abs(r.varPercent), maxVal: 0.15)
                riskGauge("CVaR", abs(r.cvarPercent), maxVal: 0.20)
            }
            .padding(.top, 8)
        }
        .padding()
        .pythiaCard()
    }

    private func componentVaRCard(_ portfolioVaR: Double, _ components: [ComponentVaR]) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("Component VaR Decomposition")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Chart(components) { c in
                BarMark(
                    x: .value("Contribution", c.pctContribution),
                    y: .value("Asset", c.symbol)
                )
                .foregroundStyle(c.pctContribution >= 0 ? PythiaTheme.loss : PythiaTheme.profit)
            }
            .chartXAxisLabel("% Contribution to VaR")
            .chartXAxis {
                AxisMarks { _ in
                    AxisGridLine().foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .chartYAxis {
                AxisMarks { _ in
                    AxisValueLabel().foregroundStyle(PythiaTheme.textSecondary)
                }
            }
            .frame(height: CGFloat(components.count * 35 + 40))


            // Table
            ForEach(components) { c in
                HStack {
                    Text(c.symbol)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(width: 80, alignment: .leading)
                    Text(PythiaTheme.formatPercent(c.weight))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.textSecondary)
                        .frame(width: 80)
                    Text(String(format: "%.2f%%", c.pctContribution))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(PythiaTheme.accentGold)
                        .frame(width: 80)
                    Spacer()
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    private func riskGauge(_ label: String, _ value: Double, maxVal: Double) -> some View {
        VStack(spacing: 4) {
            Gauge(value: min(value, maxVal), in: 0...maxVal) {
                Text(label).font(PythiaTheme.caption())
            } currentValueLabel: {
                Text(PythiaTheme.formatPercent(value))
                    .font(PythiaTheme.monospace())
            }
            .gaugeStyle(.accessoryCircular)
            .tint(Gradient(colors: [PythiaTheme.profit, PythiaTheme.accentGold, PythiaTheme.loss]))
            .scaleEffect(1.5)
        }
        .frame(width: 100, height: 100)
    }

    private func calculate() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true
        errorMessage = nil
        do {
            varResult = try await db.calculateVaR(portfolioId: pid, method: method, confidence: confidence, holdingPeriod: holdingPeriod)
            if !(varResult?.success ?? false) { errorMessage = varResult?.message }
            componentVaR = try await db.fetchComponentVaR(portfolioId: pid)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
