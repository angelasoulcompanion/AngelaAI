//
//  PatternView.swift
//  Pythia — Chart Pattern Recognition (Phase 8.5)
//

import SwiftUI
import Charts

struct PatternView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var result: PatternResponse?
    @State private var priceData: [HistoryBar] = []
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Pattern Recognition")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Controls
                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    Button("Detect Patterns") { Task { await detect() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Scanning for chart patterns...") }

                if let r = result, r.success {
                    // Summary
                    summaryCard(r)

                    // Price chart with pattern levels
                    if !priceData.isEmpty {
                        priceChartWithLevels(r)
                    }

                    // Pattern cards
                    ForEach(r.patterns) { pattern in
                        patternCard(pattern, currentPrice: r.currentPrice)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Price Chart with Pattern Levels

    private func priceChartWithLevels(_ r: PatternResponse) -> some View {
        let keyLevels = collectKeyLevels(r)
        let srPattern = r.patterns.first { $0.patternType == "support_resistance" }
        let supports = srPattern?.keyLevels?.filter { $0 < r.currentPrice } ?? []
        let resistances = srPattern?.keyLevels?.filter { $0 >= r.currentPrice } ?? []

        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Price Chart — \(r.symbol)")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(String(format: "%.2f", r.currentPrice))
                    .font(.system(size: 16, weight: .bold, design: .rounded))
                    .foregroundColor(PythiaTheme.accentGold)
            }

            Chart {
                // Price line
                ForEach(priceData) { bar in
                    LineMark(
                        x: .value("Date", bar.date),
                        y: .value("Price", bar.close)
                    )
                    .foregroundStyle(PythiaTheme.accentGold)
                    .lineStyle(StrokeStyle(lineWidth: 1.5))
                }

                // Support levels (green dashed)
                ForEach(supports, id: \.self) { level in
                    RuleMark(y: .value("Support", level))
                        .foregroundStyle(PythiaTheme.profit.opacity(0.6))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [6, 4]))
                        .annotation(position: .leading, alignment: .leading) {
                            Text(String(format: "S %.0f", level))
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(PythiaTheme.profit)
                        }
                }

                // Resistance levels (red dashed)
                ForEach(resistances, id: \.self) { level in
                    RuleMark(y: .value("Resistance", level))
                        .foregroundStyle(PythiaTheme.loss.opacity(0.6))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [6, 4]))
                        .annotation(position: .leading, alignment: .leading) {
                            Text(String(format: "R %.0f", level))
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(PythiaTheme.loss)
                        }
                }

                // Breakout levels (gold dotted)
                ForEach(breakoutLevels(r), id: \.self) { bp in
                    RuleMark(y: .value("Breakout", bp))
                        .foregroundStyle(PythiaTheme.accentGold.opacity(0.5))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
                }

                // Target levels (blue dotted)
                ForEach(targetLevels(r), id: \.self) { tp in
                    RuleMark(y: .value("Target", tp))
                        .foregroundStyle(PythiaTheme.secondaryBlue.opacity(0.5))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
                }

                // Current price line
                RuleMark(y: .value("Current", r.currentPrice))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.4))
                    .lineStyle(StrokeStyle(lineWidth: 0.5))
            }
            .chartYAxis {
                AxisMarks(position: .trailing) { value in
                    AxisValueLabel {
                        Text(String(format: "%.0f", value.as(Double.self) ?? 0))
                            .font(.system(size: 10))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            }
            .chartXAxis {
                AxisMarks(values: .automatic(desiredCount: 6)) { value in
                    AxisValueLabel {
                        if let dateStr = value.as(String.self) {
                            Text(String(dateStr.suffix(5)))
                                .font(.system(size: 9))
                                .foregroundColor(PythiaTheme.textTertiary)
                        }
                    }
                }
            }
            .frame(height: 300)

            // Legend
            HStack(spacing: 16) {
                legendItem("Support", PythiaTheme.profit)
                legendItem("Resistance", PythiaTheme.loss)
                legendItem("Breakout", PythiaTheme.accentGold)
                legendItem("Target", PythiaTheme.secondaryBlue)
            }
            .padding(.top, 4)
        }
        .padding()
        .pythiaCard()
    }

    private func legendItem(_ label: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Rectangle()
                .fill(color)
                .frame(width: 16, height: 2)
            Text(label)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textTertiary)
        }
    }

    private func collectKeyLevels(_ r: PatternResponse) -> [Double] {
        r.patterns.flatMap { $0.keyLevels ?? [] }
    }

    private func breakoutLevels(_ r: PatternResponse) -> [Double] {
        r.patterns.compactMap { p in
            guard p.patternType != "support_resistance", let bp = p.breakoutPrice, bp > 0 else { return nil }
            return bp
        }
    }

    private func targetLevels(_ r: PatternResponse) -> [Double] {
        r.patterns.compactMap { p in
            guard p.patternType != "support_resistance", let tp = p.targetPrice, tp > 0 else { return nil }
            return tp
        }
    }

    // MARK: - Summary

    private func summaryCard(_ r: PatternResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Text(r.symbol)
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(String(format: "$%.2f", r.currentPrice))
                    .font(.system(size: 18, weight: .bold, design: .rounded))
                    .foregroundColor(PythiaTheme.accentGold)
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Patterns", "\(r.patterns.filter { $0.patternType != "support_resistance" }.count)",
                          PythiaTheme.accentGold, size: .large)

                let bullish = r.patterns.filter { $0.direction == "bullish" }.count
                let bearish = r.patterns.filter { $0.direction == "bearish" }.count
                MetricBox("Bullish", "\(bullish)", PythiaTheme.profit, size: .large)
                MetricBox("Bearish", "\(bearish)", PythiaTheme.loss, size: .large)
            }
        }
        .padding()
        .pythiaCard()
    }

    // MARK: - Pattern Card

    private func patternCard(_ pattern: ChartPattern, currentPrice: Double) -> some View {
        let isSR = pattern.patternType == "support_resistance"

        return VStack(alignment: .leading, spacing: 10) {
            HStack {
                // Pattern type badge
                Text(formatPatternName(pattern.patternType))
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(PythiaTheme.textPrimary)

                Spacer()

                if !isSR {
                    // Direction badge
                    HStack(spacing: 4) {
                        Image(systemName: pattern.direction == "bullish" ? "arrow.up.right" : pattern.direction == "bearish" ? "arrow.down.right" : "minus")
                            .font(.system(size: 10, weight: .bold))
                        Text(pattern.direction.uppercased())
                            .font(.system(size: 11, weight: .bold))
                    }
                    .foregroundColor(directionColor(pattern.direction))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(directionColor(pattern.direction).opacity(0.15))
                    .cornerRadius(6)

                    // Confidence
                    Text(String(format: "%.0f%%", pattern.confidence * 100))
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(confidenceColor(pattern.confidence))
                }
            }

            if let desc = pattern.description, !desc.isEmpty {
                Text(desc)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textSecondary)
            }

            if !isSR {
                HStack(spacing: PythiaTheme.largeSpacing) {
                    if let bp = pattern.breakoutPrice, bp > 0 {
                        VStack(spacing: 2) {
                            Text(String(format: "%.2f", bp))
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundColor(PythiaTheme.accentGold)
                            Text("Breakout")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }

                    if let tp = pattern.targetPrice, tp > 0 {
                        VStack(spacing: 2) {
                            Text(String(format: "%.2f", tp))
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundColor(pattern.direction == "bullish" ? PythiaTheme.profit : PythiaTheme.loss)
                            Text("Target")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }

                    if let bp = pattern.breakoutPrice, let tp = pattern.targetPrice, bp > 0, currentPrice > 0 {
                        let rr = abs(tp - currentPrice) / abs(bp - currentPrice + 0.01)
                        VStack(spacing: 2) {
                            Text(String(format: "%.1f:1", rr))
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundColor(rr > 2 ? PythiaTheme.profit : PythiaTheme.warningOrange)
                            Text("Risk:Reward")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textSecondary)
                        }
                    }
                }
            }

            // Key levels
            if let levels = pattern.keyLevels, !levels.isEmpty {
                HStack(spacing: 8) {
                    Text("Key Levels:")
                        .font(.system(size: 11))
                        .foregroundColor(PythiaTheme.textTertiary)
                    ForEach(levels, id: \.self) { level in
                        Text(String(format: "%.2f", level))
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                            .foregroundColor(PythiaTheme.accentBlue)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(PythiaTheme.accentBlue.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
            }
        }
        .padding()
        .background(directionColor(pattern.direction).opacity(0.05))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(directionColor(pattern.direction).opacity(0.2), lineWidth: 1)
        )
        .cornerRadius(12)
        .pythiaCard()
    }

    // MARK: - Helpers

    private func formatPatternName(_ type: String) -> String {
        switch type {
        case "double_top": return "Double Top"
        case "double_bottom": return "Double Bottom"
        case "head_shoulders": return "Head & Shoulders"
        case "ascending_triangle": return "Ascending Triangle"
        case "descending_triangle": return "Descending Triangle"
        case "symmetric_triangle": return "Symmetric Triangle"
        case "support_resistance": return "Support & Resistance"
        default: return type.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    private func directionColor(_ direction: String) -> Color {
        switch direction {
        case "bullish": return PythiaTheme.profit
        case "bearish": return PythiaTheme.loss
        default: return PythiaTheme.accentGold
        }
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.7 { return PythiaTheme.profit }
        if confidence >= 0.5 { return PythiaTheme.accentGold }
        return PythiaTheme.textSecondary
    }

    // MARK: - API

    private func detect() async {
        guard let assetId = selectedAssetId else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            result = try await db.get("/patterns/\(assetId)?days=120", timeout: 60.0)

            // Fetch price history for chart
            if let r = result, r.success {
                let history: HistoryResponse = try await db.get("/market/history/\(r.symbol)?period=6mo")
                priceData = history.data
            }
        } catch {
            result = nil
        }
    }
}
