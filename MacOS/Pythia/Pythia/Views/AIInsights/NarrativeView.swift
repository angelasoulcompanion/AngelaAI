//
//  NarrativeView.swift
//  Pythia — Market Narrative Engine (Phase 8.4)
//

import SwiftUI

struct NarrativeView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var narrative: NarrativeResponse?
    @State private var isLoading = false
    @State private var selectedType = "daily"

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Market Narrative")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    ForEach(["daily", "weekly"], id: \.self) { type in
                        Button(type.capitalized) { selectedType = type }
                            .buttonStyle(.plain)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 7)
                            .background(selectedType == type ? PythiaTheme.accentGold.opacity(0.2) : PythiaTheme.surfaceBackground)
                            .foregroundColor(selectedType == type ? PythiaTheme.accentGold : PythiaTheme.textSecondary)
                            .cornerRadius(8)
                    }

                    Button("Generate") { Task { await generate() } }
                        .pythiaPrimaryButton()

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Generating narrative...") }

                if let n = narrative, n.success {
                    // Headline
                    if let headline = n.headline, !headline.isEmpty {
                        Text(headline)
                            .font(.system(size: 22, weight: .bold))
                            .foregroundColor(PythiaTheme.accentGold)
                            .padding()
                            .pythiaCard()
                    }

                    // Summary
                    if let summary = n.summary, !summary.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Summary")
                                .font(PythiaTheme.heading())
                                .foregroundColor(PythiaTheme.textPrimary)
                            Text(summary)
                                .font(PythiaTheme.body())
                                .foregroundColor(PythiaTheme.textSecondary)
                                .lineSpacing(4)
                        }
                        .padding()
                        .pythiaCard()
                    }

                    // Three columns: themes, risks, opportunities
                    HStack(alignment: .top, spacing: PythiaTheme.spacing) {
                        listSection("Key Themes", n.keyThemes, "lightbulb.fill", PythiaTheme.accentGold)
                        listSection("Risk Factors", n.riskFactors, "exclamationmark.triangle.fill", PythiaTheme.loss)
                        listSection("Opportunities", n.opportunities, "arrow.up.right.circle.fill", PythiaTheme.profit)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func listSection(_ title: String, _ items: [String]?, _ icon: String, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .foregroundColor(color)
                Text(title)
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            if let items = items, !items.isEmpty {
                ForEach(items, id: \.self) { item in
                    HStack(alignment: .top, spacing: 6) {
                        Circle()
                            .fill(color)
                            .frame(width: 6, height: 6)
                            .padding(.top, 6)
                        Text(item)
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textSecondary)
                    }
                }
            } else {
                Text("—")
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .pythiaCard()
    }

    private func generate() async {
        isLoading = true; defer { isLoading = false }
        do { narrative = try await db.get("/narrative/\(selectedType)", timeout: 120.0) }
        catch { narrative = nil }
    }
}
