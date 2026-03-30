//
//  ScreenerView.swift
//  Pythia — Smart Screener (Phase 8.1)
//

import SwiftUI

struct ScreenerView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var query = ""
    @State private var result: ScreenerResponse?
    @State private var presets: [ScreenerPreset] = []
    @State private var isLoading = false
    @State private var errorText: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Smart Screener")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Search bar
                HStack(spacing: PythiaTheme.spacing) {
                    TextField("e.g. \"oversold stocks with high volume\"", text: $query)
                        .textFieldStyle(.roundedBorder)
                        .frame(minWidth: 300)

                    Button("Search") { Task { await search() } }
                        .pythiaPrimaryButton()
                        .disabled(query.isEmpty)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                // Preset buttons
                presetSection

                if isLoading { LoadingView("Scanning assets...") }

                // Error display
                if let err = errorText {
                    Text("Error: \(err)")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.errorRed)
                        .padding()
                        .pythiaCard()
                }

                // Results
                if let r = result, r.success, !r.results.isEmpty {
                    resultsTable(r)
                } else if let r = result, r.results.isEmpty {
                    Text("No results found for \"\(r.query)\"")
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textTertiary)
                        .padding()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadPresets() }
    }

    private var presetSection: some View {
        HStack(spacing: 8) {
            ForEach(presets) { preset in
                Button(preset.name) { Task { await runPreset(preset.key) } }
                    .buttonStyle(.plain)
                    .font(.system(size: 11, weight: .medium))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(PythiaTheme.surfaceBackground)
                    .foregroundColor(PythiaTheme.accentGold)
                    .cornerRadius(6)
            }
            Spacer()
        }
        .padding(.horizontal)

    }

    private func resultsTable(_ r: ScreenerResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Results (\(r.total))")
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Text(r.query)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }

            // Header
            HStack {
                Text("Symbol").frame(width: 80, alignment: .leading)
                Text("Price").frame(width: 80, alignment: .trailing)
                Text("RSI").frame(width: 50, alignment: .trailing)
                Text("Mom 20d").frame(width: 70, alignment: .trailing)
                Text("Vol Ratio").frame(width: 70, alignment: .trailing)
                Text("Ann Vol").frame(width: 70, alignment: .trailing)
                Text("Score").frame(width: 60, alignment: .trailing)
            }
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(PythiaTheme.textSecondary)
            .padding(.horizontal, 4)

            Divider().background(PythiaTheme.surfaceBackground)

            ForEach(r.results) { item in
                HStack {
                    Text(item.symbol)
                        .frame(width: 80, alignment: .leading)
                        .foregroundColor(PythiaTheme.accentGold)
                    Text(String(format: "%.2f", item.price))
                        .frame(width: 80, alignment: .trailing)
                    Text(String(format: "%.0f", item.rsi ?? 0))
                        .frame(width: 50, alignment: .trailing)
                        .foregroundColor(rsiColor(item.rsi ?? 50))
                    Text(String(format: "%+.1f%%", (item.momentum20d ?? 0) * 100))
                        .frame(width: 70, alignment: .trailing)
                        .foregroundColor((item.momentum20d ?? 0) >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                    Text(String(format: "%.1fx", item.volumeRatio ?? 1))
                        .frame(width: 70, alignment: .trailing)
                    Text(String(format: "%.0f%%", (item.annualVol ?? 0) * 100))
                        .frame(width: 70, alignment: .trailing)
                    Text(String(format: "%+.2f", item.compositeScore ?? 0))
                        .frame(width: 60, alignment: .trailing)
                        .foregroundColor(scoreColor(item.compositeScore ?? 0))
                }
                .font(.system(size: 11, design: .monospaced))
                .foregroundColor(PythiaTheme.textSecondary)
                .padding(.vertical, 3)
                .padding(.horizontal, 4)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func rsiColor(_ rsi: Double) -> Color {
        if rsi < 30 { return PythiaTheme.profit }
        if rsi > 70 { return PythiaTheme.loss }
        return PythiaTheme.textSecondary
    }

    private func scoreColor(_ score: Double) -> Color {
        if score > 0.2 { return PythiaTheme.profit }
        if score < -0.2 { return PythiaTheme.loss }
        return PythiaTheme.accentGold
    }

    private func search() async {
        isLoading = true; errorText = nil; defer { isLoading = false }
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        do { result = try await db.get("/screener/search?query=\(encoded)", timeout: 60.0) }
        catch { result = nil; errorText = "\(error)" }
    }

    private func runPreset(_ key: String) async {
        isLoading = true; errorText = nil; defer { isLoading = false }
        do { result = try await db.get("/screener/preset/\(key)", timeout: 60.0) }
        catch { result = nil; errorText = "\(error)" }
    }

    private func loadPresets() async {
        do { let r: ScreenerPresetResponse = try await db.get("/screener/presets"); presets = r.presets }
        catch { presets = [] }
    }
}
