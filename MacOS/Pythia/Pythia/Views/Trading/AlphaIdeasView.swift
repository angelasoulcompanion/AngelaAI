//
//  AlphaIdeasView.swift
//  Pythia — Alpha Ideas (Factor Research Scanner) Phase 9
//

import SwiftUI
import Charts

struct AlphaIdeasView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var result: AlphaIdeasResponse?
    @State private var isLoading = false
    @State private var errorText: String?
    @State private var selectedTab = "overview"
    @State private var selectedMarket = "TH"  // TH or US

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                // Header
                headerSection

                if isLoading {
                    LoadingView("Scanning \(selectedMarket == "US" ? "US" : "Thai") stocks (7 alpha factors)...")
                }

                if let err = errorText {
                    Text("Error: \(err)")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.errorRed)
                        .padding()
                        .pythiaCard()
                }

                if let r = result, r.success {
                    tabPicker(r)

                    if selectedTab == "overview" {
                        overviewTab(r)
                    } else if let idea = r.ideas.first(where: { $0.ideaId == selectedTab }) {
                        ideaDetailTab(idea)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    // MARK: - Header

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Alpha Ideas")
                        .font(PythiaTheme.title())
                        .foregroundColor(PythiaTheme.textPrimary)

                    Text("Factor Research Scanner — 7 Academic Alpha Factors")
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textSecondary)
                }

                Spacer()

                // Market picker
                HStack(spacing: 4) {
                    marketButton("TH", flag: "🇹🇭")
                    marketButton("US", flag: "🇺🇸")
                }

                if let r = result, r.success {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("\(r.totalStocksScanned) stocks scanned")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(PythiaTheme.accentGold)
                        Text(String(format: "%.1fs", r.scanTimeSeconds))
                            .font(.system(size: 10))
                            .foregroundColor(PythiaTheme.textTertiary)
                    }
                }

                Button("Scan \(selectedMarket == "US" ? "US" : "Thai") Stocks") {
                    Task { await scan() }
                }
                    .pythiaPrimaryButton()
                    .disabled(isLoading)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func marketButton(_ market: String, flag: String) -> some View {
        Button {
            selectedMarket = market
            result = nil
            errorText = nil
            selectedTab = "overview"
        } label: {
            Text("\(flag) \(market)")
                .font(.system(size: 12, weight: selectedMarket == market ? .bold : .medium))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(selectedMarket == market ? PythiaTheme.accentGold : PythiaTheme.surfaceBackground)
                .foregroundColor(selectedMarket == market ? .black : PythiaTheme.textSecondary)
                .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Tab Picker

    private func tabPicker(_ r: AlphaIdeasResponse) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 6) {
                tabButton("overview", label: "Overview")
                ForEach(r.ideas) { idea in
                    tabButton(idea.ideaId, label: idea.name)
                }
            }
            .padding(.horizontal, 4)
        }
    }

    private func tabButton(_ id: String, label: String) -> some View {
        Button(label) { selectedTab = id }
            .buttonStyle(.plain)
            .font(.system(size: 11, weight: selectedTab == id ? .bold : .medium))
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(selectedTab == id ? PythiaTheme.accentGold : PythiaTheme.surfaceBackground)
            .foregroundColor(selectedTab == id ? .black : PythiaTheme.textSecondary)
            .cornerRadius(8)
    }

    // MARK: - Overview Tab

    private func overviewTab(_ r: AlphaIdeasResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            // Idea summary cards
            Text("7 Alpha Ideas")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)

            LazyVGrid(columns: [
                GridItem(.flexible(), spacing: 12),
                GridItem(.flexible(), spacing: 12),
            ], spacing: 12) {
                ForEach(r.ideas) { idea in
                    ideaSummaryCard(idea)
                }
            }

            // Composite ranking table
            Text("Composite Ranking")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textPrimary)
                .padding(.top, 8)

            compositeTable(r.compositeRanking)
        }
    }

    private func ideaSummaryCard(_ idea: AlphaIdeaItem) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(idea.name)
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(PythiaTheme.accentGold)
                Spacer()
                Image(systemName: iconForIdea(idea.ideaId))
                    .font(.system(size: 14))
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            Text(idea.description)
                .font(.system(size: 10))
                .foregroundColor(PythiaTheme.textSecondary)
                .lineLimit(3)

            Divider().background(PythiaTheme.textTertiary.opacity(0.3))

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("TOP LONG")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(PythiaTheme.profit)
                    if let top = idea.longCandidates.first {
                        Text(top.symbol)
                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                            .foregroundColor(PythiaTheme.textPrimary)
                    }
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("TOP SHORT")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(PythiaTheme.loss)
                    if let top = idea.shortCandidates.first {
                        Text(top.symbol)
                            .font(.system(size: 12, weight: .semibold, design: .monospaced))
                            .foregroundColor(PythiaTheme.textPrimary)
                    }
                }
                Spacer()
            }
        }
        .padding(12)
        .pythiaCard()
        .onTapGesture { selectedTab = idea.ideaId }
    }

    // MARK: - Composite Table

    private func compositeTable(_ stocks: [AlphaIdeaStock]) -> some View {
        VStack(spacing: 0) {
            // Header
            HStack(spacing: 0) {
                Text("#").frame(width: 30, alignment: .center)
                Text("Symbol").frame(width: 80, alignment: .leading)
                Text("Sector").frame(width: 90, alignment: .leading)
                Text("Price").frame(width: 70, alignment: .trailing)
                Text("Composite").frame(width: 75, alignment: .trailing)
                Text("BAB").frame(width: 50, alignment: .trailing)
                Text("Val").frame(width: 50, alignment: .trailing)
                Text("Size").frame(width: 50, alignment: .trailing)
                Text("STR").frame(width: 50, alignment: .trailing)
                Text("MOM").frame(width: 50, alignment: .trailing)
                Text("LTR").frame(width: 50, alignment: .trailing)
                Text("BAV").frame(width: 50, alignment: .trailing)
            }
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(PythiaTheme.textSecondary)
            .padding(.vertical, 8)
            .padding(.horizontal, 8)
            .background(PythiaTheme.surfaceBackground.opacity(0.5))

            ForEach(Array(stocks.enumerated()), id: \.element.id) { idx, stock in
                HStack(spacing: 0) {
                    Text("\(idx + 1)").frame(width: 30, alignment: .center)
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(stock.symbol).frame(width: 80, alignment: .leading)
                        .foregroundColor(PythiaTheme.accentGold)
                    Text(stock.sector ?? "-").frame(width: 90, alignment: .leading)
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(String(format: "%.2f", stock.price)).frame(width: 70, alignment: .trailing)
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(String(format: "%+.2f", stock.compositeScore)).frame(width: 75, alignment: .trailing)
                        .foregroundColor(stock.compositeScore > 0 ? PythiaTheme.profit : PythiaTheme.loss)
                        .fontWeight(.bold)
                    scoreCell(stock.babScore, width: 50)
                    scoreCell(stock.valueScore, width: 50)
                    scoreCell(stock.sizeScore, width: 50)
                    scoreCell(stock.strScore, width: 50)
                    scoreCell(stock.momScore, width: 50)
                    scoreCell(stock.ltrScore, width: 50)
                    scoreCell(stock.bavScore, width: 50)
                }
                .font(.system(size: 11, design: .monospaced))
                .padding(.vertical, 6)
                .padding(.horizontal, 8)
                .background(idx % 2 == 0 ? Color.clear : PythiaTheme.surfaceBackground.opacity(0.2))
            }
        }
        .pythiaCard()
    }

    private func scoreCell(_ score: Double?, width: CGFloat) -> some View {
        Group {
            if let s = score {
                Text(String(format: "%+.1f", s))
                    .foregroundColor(s > 0.5 ? PythiaTheme.profit : s < -0.5 ? PythiaTheme.loss : PythiaTheme.textTertiary)
            } else {
                Text("-")
                    .foregroundColor(PythiaTheme.textTertiary.opacity(0.4))
            }
        }
        .frame(width: width, alignment: .trailing)
    }

    // MARK: - Idea Detail Tab

    private func ideaDetailTab(_ idea: AlphaIdeaItem) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            // Description card
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Image(systemName: iconForIdea(idea.ideaId))
                        .font(.system(size: 20))
                        .foregroundColor(PythiaTheme.accentGold)
                    Text(idea.name)
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)
                }

                Text(idea.description)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textSecondary)

                Divider().background(PythiaTheme.textTertiary.opacity(0.3))

                HStack(spacing: PythiaTheme.largeSpacing) {
                    VStack(alignment: .leading, spacing: 4) {
                        Label("LONG", systemImage: "arrow.up.circle.fill")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(PythiaTheme.profit)
                        Text(idea.longRationale)
                            .font(.system(size: 12))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)

                    VStack(alignment: .leading, spacing: 4) {
                        Label("SHORT", systemImage: "arrow.down.circle.fill")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(PythiaTheme.loss)
                        Text(idea.shortRationale)
                            .font(.system(size: 12))
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding()
            .pythiaCard()

            // Long and Short tables side by side
            HStack(alignment: .top, spacing: PythiaTheme.spacing) {
                candidateTable(
                    title: "Long Candidates",
                    stocks: idea.longCandidates,
                    color: PythiaTheme.profit,
                    ideaId: idea.ideaId
                )
                candidateTable(
                    title: "Short Candidates",
                    stocks: idea.shortCandidates,
                    color: PythiaTheme.loss,
                    ideaId: idea.ideaId
                )
            }
        }
    }

    private func candidateTable(
        title: String,
        stocks: [AlphaIdeaStock],
        color: Color,
        ideaId: String
    ) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text(title)
                    .font(.system(size: 13, weight: .bold))
                    .foregroundColor(color)
                Spacer()
                Text("Top \(stocks.count)")
                    .font(.system(size: 10))
                    .foregroundColor(PythiaTheme.textTertiary)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(color.opacity(0.1))

            // Column headers
            HStack(spacing: 0) {
                Text("#").frame(width: 25, alignment: .center)
                Text("Symbol").frame(width: 75, alignment: .leading)
                Text("Price").frame(width: 65, alignment: .trailing)
                Text(metricLabel(ideaId)).frame(width: 75, alignment: .trailing)
                Text("Z-Score").frame(width: 60, alignment: .trailing)
            }
            .font(.system(size: 9, weight: .bold))
            .foregroundColor(PythiaTheme.textSecondary)
            .padding(.vertical, 6)
            .padding(.horizontal, 12)
            .background(PythiaTheme.surfaceBackground.opacity(0.3))

            ForEach(Array(stocks.enumerated()), id: \.element.id) { idx, stock in
                HStack(spacing: 0) {
                    Text("\(idx + 1)").frame(width: 25, alignment: .center)
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(stock.symbol).frame(width: 75, alignment: .leading)
                        .foregroundColor(PythiaTheme.accentGold)
                    Text(String(format: "%.2f", stock.price)).frame(width: 65, alignment: .trailing)
                        .foregroundColor(PythiaTheme.textPrimary)
                    Text(rawMetricText(stock, ideaId: ideaId)).frame(width: 75, alignment: .trailing)
                        .foregroundColor(PythiaTheme.textSecondary)
                    Text(zScoreText(stock, ideaId: ideaId)).frame(width: 60, alignment: .trailing)
                        .foregroundColor(color)
                        .fontWeight(.semibold)
                }
                .font(.system(size: 11, design: .monospaced))
                .padding(.vertical, 5)
                .padding(.horizontal, 12)
                .background(idx % 2 == 0 ? Color.clear : PythiaTheme.surfaceBackground.opacity(0.15))
            }
        }
        .pythiaCard()
    }

    // MARK: - Helpers

    private func metricLabel(_ ideaId: String) -> String {
        switch ideaId {
        case "bab": return "Beta"
        case "value": return "P/B"
        case "size": return "Mkt Cap"
        case "str": return "Ret 1W"
        case "mom": return "Ret 2-12M"
        case "ltr": return "Ret 3Y"
        case "bav": return "Vol (Ann)"
        default: return "Metric"
        }
    }

    private func rawMetricText(_ s: AlphaIdeaStock, ideaId: String) -> String {
        switch ideaId {
        case "bab": return s.beta.map { String(format: "%.2f", $0) } ?? "-"
        case "value": return s.pbRatio.map { String(format: "%.1f", $0) } ?? "-"
        case "size":
            guard let mc = s.marketCap else { return "-" }
            if mc >= 1_000_000_000 { return String(format: "%.1fB", mc / 1_000_000_000) }
            return String(format: "%.0fM", mc / 1_000_000)
        case "str": return s.return1w.map { String(format: "%+.1f%%", $0 * 100) } ?? "-"
        case "mom": return s.return12m.map { String(format: "%+.1f%%", $0 * 100) } ?? "-"
        case "ltr": return s.return3y.map { String(format: "%+.1f%%", $0 * 100) } ?? "-"
        case "bav": return s.annualVol.map { String(format: "%.1f%%", $0 * 100) } ?? "-"
        default: return "-"
        }
    }

    private func zScoreText(_ s: AlphaIdeaStock, ideaId: String) -> String {
        let score: Double? = {
            switch ideaId {
            case "bab": return s.babScore
            case "value": return s.valueScore
            case "size": return s.sizeScore
            case "str": return s.strScore
            case "mom": return s.momScore
            case "ltr": return s.ltrScore
            case "bav": return s.bavScore
            default: return nil
            }
        }()
        return score.map { String(format: "%+.2f", $0) } ?? "-"
    }

    private func iconForIdea(_ ideaId: String) -> String {
        switch ideaId {
        case "bab": return "gauge.with.dots.needle.33percent"
        case "value": return "banknote.fill"
        case "size": return "scalemass.fill"
        case "str": return "arrow.uturn.backward"
        case "mom": return "arrow.up.right"
        case "ltr": return "clock.arrow.2.circlepath"
        case "bav": return "waveform.path.ecg"
        default: return "lightbulb.fill"
        }
    }

    // MARK: - API Call

    private func scan() async {
        isLoading = true
        errorText = nil
        defer { isLoading = false }
        do {
            let r: AlphaIdeasResponse = try await db.get(
                "/alpha-ideas/scan?top_n=10&market=\(selectedMarket)",
                timeout: 180.0
            )
            result = r
            if !r.success { errorText = r.message }
        } catch {
            errorText = error.localizedDescription
        }
    }
}
