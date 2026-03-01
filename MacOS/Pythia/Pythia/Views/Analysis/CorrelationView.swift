//
//  CorrelationView.swift
//  Pythia — Asset Correlation Matrix
//

import SwiftUI

struct CorrelationView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var portfolios: [Portfolio] = []
    @State private var selectedPortfolioId: String?
    @State private var correlation: CorrelationResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var days = 365

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Correlation Matrix")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
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

                    Picker("Period", selection: $days) {
                        Text("90 Days").tag(90)
                        Text("1 Year").tag(365)
                        Text("3 Years").tag(1095)
                    }
                    .frame(width: 120)

                    Button("Calculate") {
                        Task { await loadCorrelation() }
                    }
                    .pythiaPrimaryButton()
                    .disabled(selectedPortfolioId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading {
                    LoadingView("Computing correlation matrix...")
                }

                if let corr = correlation {
                    correlationHeatmap(corr)
                    correlationTable(corr)
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadPortfolios() }
    }

    // MARK: - Heatmap

    private func correlationHeatmap(_ corr: CorrelationResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Correlation Heatmap")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            let n = corr.symbols.count
            let cellSize: CGFloat = min(60, 500 / CGFloat(n))

            VStack(spacing: 1) {
                // Header row
                HStack(spacing: 1) {
                    Text("")
                        .frame(width: 60, height: cellSize)

                    ForEach(corr.symbols, id: \.self) { sym in
                        Text(sym)
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: cellSize, height: cellSize)
                            .rotationEffect(.degrees(-45))
                    }
                }

                // Matrix rows
                ForEach(0..<n, id: \.self) { i in
                    HStack(spacing: 1) {
                        Text(corr.symbols[i])
                            .font(PythiaTheme.caption())
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 60, alignment: .trailing)

                        ForEach(0..<n, id: \.self) { j in
                            let val = corr.correlationMatrix[i][j]
                            Text(String(format: "%.2f", val))
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .foregroundColor(.white)
                                .frame(width: cellSize, height: cellSize)
                                .background(correlationColor(val))
                        }
                    }
                }
            }

            // Legend
            HStack(spacing: 4) {
                Text("-1.0")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
                LinearGradient(
                    colors: [PythiaTheme.loss, PythiaTheme.surfaceBackground, PythiaTheme.profit],
                    startPoint: .leading,
                    endPoint: .trailing
                )
                .frame(height: 12)
                .cornerRadius(4)
                Text("1.0")
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
            .frame(width: 200)
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Table

    private func correlationTable(_ corr: CorrelationResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Correlation Pairs")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            let pairs = extractPairs(corr)

            ForEach(pairs, id: \.label) { pair in
                HStack {
                    Text(pair.label)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                        .frame(width: 150, alignment: .leading)

                    ProgressView(value: (pair.value + 1) / 2) // normalize -1..1 to 0..1
                        .tint(correlationColor(pair.value))
                        .frame(width: 200)

                    Text(String(format: "%.4f", pair.value))
                        .font(PythiaTheme.monospace())
                        .foregroundColor(correlationTextColor(pair.value))
                        .frame(width: 80, alignment: .trailing)

                    Text(pair.interpretation)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                        .frame(width: 120)

                    Spacer()
                }
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Helpers

    private func correlationColor(_ value: Double) -> Color {
        if value > 0.5 { return PythiaTheme.profit.opacity(0.3 + abs(value) * 0.7) }
        if value < -0.5 { return PythiaTheme.loss.opacity(0.3 + abs(value) * 0.7) }
        if value > 0 { return PythiaTheme.profit.opacity(0.15 + value * 0.35) }
        if value < 0 { return PythiaTheme.loss.opacity(0.15 + abs(value) * 0.35) }
        return PythiaTheme.surfaceBackground
    }

    private func correlationTextColor(_ value: Double) -> Color {
        if abs(value) > 0.7 { return value > 0 ? PythiaTheme.profit : PythiaTheme.loss }
        return PythiaTheme.textSecondary
    }

    private struct CorrPair {
        let label: String
        let value: Double
        let interpretation: String
    }

    private func extractPairs(_ corr: CorrelationResponse) -> [CorrPair] {
        var pairs: [CorrPair] = []
        let n = corr.symbols.count
        for i in 0..<n {
            for j in (i+1)..<n {
                let val = corr.correlationMatrix[i][j]
                let interp: String
                let absVal = abs(val)
                if absVal > 0.8 { interp = "Very Strong" }
                else if absVal > 0.6 { interp = "Strong" }
                else if absVal > 0.4 { interp = "Moderate" }
                else if absVal > 0.2 { interp = "Weak" }
                else { interp = "Very Weak" }

                pairs.append(CorrPair(
                    label: "\(corr.symbols[i]) / \(corr.symbols[j])",
                    value: val,
                    interpretation: interp
                ))
            }
        }
        return pairs.sorted { abs($0.value) > abs($1.value) }
    }

    private func loadPortfolios() async {
        do { portfolios = try await db.fetchPortfolios() } catch {}
    }

    private func loadCorrelation() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true; errorMessage = nil
        do {
            correlation = try await db.fetchCorrelationMatrix(portfolioId: pid, days: days)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
