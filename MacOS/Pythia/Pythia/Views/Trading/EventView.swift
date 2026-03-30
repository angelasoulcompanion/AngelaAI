//
//  EventView.swift
//  Pythia — Event Impact Analyzer (Phase 8.7)
//

import SwiftUI

struct EventView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedAssetId: String?
    @State private var result: EventImpactResponse?
    @State private var isLoading = false
    @State private var eventType = "earnings"

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Event Impact Analyzer")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    AssetPickerView(selectedId: $selectedAssetId)

                    ForEach(["earnings", "dividend"], id: \.self) { type in
                        Button(type.capitalized) { eventType = type }
                            .buttonStyle(.plain)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(eventType == type ? PythiaTheme.accentGold.opacity(0.2) : PythiaTheme.surfaceBackground)
                            .foregroundColor(eventType == type ? PythiaTheme.accentGold : PythiaTheme.textSecondary)
                            .cornerRadius(8)
                    }

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedAssetId == nil)
                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Analyzing event impact...") }

                if let r = result, r.success {
                    VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                        HStack {
                            Text("\(r.symbol) — \(r.eventType.capitalized) Impact")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textPrimary)
                            Spacer()
                            Text("\(r.eventsAnalyzed) events")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textTertiary)
                        }

                        HStack(spacing: PythiaTheme.largeSpacing) {
                            MetricBox("Avg Move", String(format: "%+.2f%%", r.avgMovePct),
                                      r.avgMovePct >= 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .large)
                            MetricBox("Pre-Event (5d)", String(format: "%+.2f%%", r.avgPreMove),
                                      r.avgPreMove >= 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .large)
                            MetricBox("Post-Event (5d)", String(format: "%+.2f%%", r.avgPostMove),
                                      r.avgPostMove >= 0 ? PythiaTheme.profit : PythiaTheme.loss, size: .large)
                            MetricBox("Positive Rate", String(format: "%.0f%%", r.positiveRate * 100),
                                      r.positiveRate > 0.5 ? PythiaTheme.profit : PythiaTheme.loss, size: .large)
                        }
                    }
                    .padding()
                    .pythiaCard()

                    // Historical events table
                    if let events = r.historicalEvents, !events.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Historical Events")
                                .font(PythiaTheme.heading())
                                .foregroundColor(PythiaTheme.textPrimary)

                            ForEach(events) { event in
                                HStack {
                                    Text(event.date ?? "")
                                        .frame(width: 100, alignment: .leading)
                                        .foregroundColor(PythiaTheme.textSecondary)
                                    Text(String(format: "%+.2f%%", event.eventReturn ?? 0))
                                        .frame(width: 70, alignment: .trailing)
                                        .foregroundColor((event.eventReturn ?? 0) >= 0 ? PythiaTheme.profit : PythiaTheme.loss)
                                    Text(String(format: "Pre: %+.2f%%", event.pre5d ?? 0))
                                        .frame(width: 100, alignment: .trailing)
                                        .foregroundColor(PythiaTheme.textTertiary)
                                    Text(String(format: "Post: %+.2f%%", event.post5d ?? 0))
                                        .frame(width: 100, alignment: .trailing)
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }
                                .font(.system(size: 12, design: .monospaced))
                            }
                        }
                        .padding()
                        .pythiaCard()
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func analyze() async {
        guard let id = selectedAssetId else { return }
        isLoading = true; defer { isLoading = false }
        do { result = try await db.get("/events/\(id)/impact?event_type=\(eventType)", timeout: 60.0) }
        catch { result = nil }
    }
}
