//
//  EarningsCalendarView.swift
//  Pythia — Earnings Calendar & Economic Events
//

import SwiftUI

// MARK: - Models

struct EarningsItem: Codable, Identifiable {
    let symbol: String
    let name: String?
    let earningsDate: String
    let daysUntil: Int
    let currency: String?

    var id: String { symbol }

    enum CodingKeys: String, CodingKey {
        case symbol, name, currency
        case earningsDate = "earnings_date"
        case daysUntil = "days_until"
    }
}

struct EarningsResponse: Codable {
    let earnings: [EarningsItem]
    let count: Int
    let periodDays: Int?
    let generatedAt: String?

    enum CodingKeys: String, CodingKey {
        case earnings, count
        case periodDays = "period_days"
        case generatedAt = "generated_at"
    }
}

struct UpcomingEconEvent: Codable, Identifiable {
    let date: String
    let event: String
    let impact: String
    let country: String
    let category: String

    var id: String { "\(date)_\(event)" }
}

struct UpcomingEconEventsResponse: Codable {
    let events: [UpcomingEconEvent]
    let count: Int
    let periodDays: Int?

    enum CodingKeys: String, CodingKey {
        case events, count
        case periodDays = "period_days"
    }
}

// MARK: - View

struct EarningsCalendarView: View {
    @EnvironmentObject var db: DatabaseService
    @EnvironmentObject var backend: BackendManager

    @State private var earnings: [EarningsItem] = []
    @State private var econEvents: [UpcomingEconEvent] = []
    @State private var isLoading = true
    @State private var errorMsg: String?
    @State private var selectedDays = 30

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                // Header
                HStack {
                    Text("Earnings Calendar")
                        .font(PythiaTheme.title())
                        .foregroundColor(PythiaTheme.textPrimary)
                    Spacer()
                    Picker("Period", selection: $selectedDays) {
                        Text("7 Days").tag(7)
                        Text("14 Days").tag(14)
                        Text("30 Days").tag(30)
                        Text("60 Days").tag(60)
                    }
                    .pickerStyle(.segmented)
                    .frame(width: 300)
                    .onChange(of: selectedDays) { _, _ in
                        Task { await loadAll() }
                    }
                }

                if isLoading {
                    LoadingView("Loading earnings data...")
                } else if let error = errorMsg {
                    EmptyStateView(
                        icon: "calendar.badge.exclamationmark",
                        title: "Error",
                        message: error,
                        actionTitle: "Retry"
                    ) { Task { await loadAll() } }
                } else {
                    // Economic Events Section
                    if !econEvents.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: "building.columns.fill")
                                    .foregroundColor(.orange)
                                Text("Economic Events")
                                    .font(PythiaTheme.headline())
                                    .foregroundColor(PythiaTheme.textSecondary)
                                Text("\(econEvents.count)")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(PythiaTheme.textTertiary)
                                    .padding(.horizontal, 6)
                                    .padding(.vertical, 2)
                                    .background(PythiaTheme.surfaceBackground)
                                    .cornerRadius(4)
                            }

                            LazyVGrid(columns: [
                                GridItem(.adaptive(minimum: 280, maximum: 400), spacing: 12)
                            ], spacing: 10) {
                                ForEach(econEvents) { event in
                                    econEventCard(event)
                                }
                            }
                        }
                    }

                    // Earnings Section
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Image(systemName: "chart.bar.doc.horizontal.fill")
                                .foregroundColor(.blue)
                            Text("Upcoming Earnings")
                                .font(PythiaTheme.headline())
                                .foregroundColor(PythiaTheme.textSecondary)
                            Text("\(earnings.count)")
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(PythiaTheme.textTertiary)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(PythiaTheme.surfaceBackground)
                                .cornerRadius(4)
                        }

                        if earnings.isEmpty {
                            HStack {
                                Spacer()
                                VStack(spacing: 8) {
                                    Image(systemName: "calendar")
                                        .font(.system(size: 32))
                                        .foregroundColor(PythiaTheme.textTertiary)
                                    Text("No upcoming earnings in \(selectedDays) days")
                                        .font(PythiaTheme.body())
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }
                                .padding(.vertical, 40)
                                Spacer()
                            }
                        } else {
                            // Group by week
                            let grouped = groupByWeek(earnings)
                            ForEach(Array(grouped.keys.sorted()), id: \.self) { week in
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(week)
                                        .font(.system(size: 12, weight: .semibold))
                                        .foregroundColor(PythiaTheme.textTertiary)
                                        .padding(.top, 4)

                                    ForEach(grouped[week] ?? []) { item in
                                        earningsRow(item)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            while !backend.isConnected {
                try? await Task.sleep(nanoseconds: 500_000_000)
            }
            await loadAll()
        }
    }

    // MARK: - Cards

    private func econEventCard(_ event: UpcomingEconEvent) -> some View {
        HStack(spacing: 12) {
            // Impact indicator
            Circle()
                .fill(impactColor(event.impact))
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(event.event)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(PythiaTheme.textPrimary)
                HStack(spacing: 6) {
                    Text(formatEventDate(event.date))
                        .font(.system(size: 11))
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text("·")
                        .foregroundColor(PythiaTheme.textTertiary)
                    Text(event.country)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(PythiaTheme.textSecondary)
                }
            }

            Spacer()

            Text(event.impact.uppercased())
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(impactColor(event.impact))
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(impactColor(event.impact).opacity(0.15))
                .cornerRadius(4)
        }
        .padding(12)
        .background(PythiaTheme.cardBackground)
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }

    private func earningsRow(_ item: EarningsItem) -> some View {
        HStack(spacing: 12) {
            // Days badge
            Text("\(item.daysUntil)d")
                .font(.system(size: 12, weight: .bold, design: .monospaced))
                .foregroundColor(item.daysUntil <= 3 ? .red : item.daysUntil <= 7 ? .orange : .green)
                .frame(width: 36)

            VStack(alignment: .leading, spacing: 2) {
                Text(item.symbol)
                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                    .foregroundColor(PythiaTheme.accentGold)
                Text(item.name ?? "")
                    .font(.system(size: 11))
                    .foregroundColor(PythiaTheme.textTertiary)
                    .lineLimit(1)
            }

            Spacer()

            Text(formatEventDate(item.earningsDate))
                .font(.system(size: 12, design: .monospaced))
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(PythiaTheme.cardBackground)
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }

    // MARK: - Helpers

    private func impactColor(_ impact: String) -> Color {
        switch impact {
        case "high": return .red
        case "medium": return .orange
        default: return .green
        }
    }

    private func formatEventDate(_ iso: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        guard let date = formatter.date(from: String(iso.prefix(10))) else { return iso }
        formatter.dateFormat = "MMM d (EEE)"
        return formatter.string(from: date)
    }

    private func groupByWeek(_ items: [EarningsItem]) -> [String: [EarningsItem]] {
        var groups: [String: [EarningsItem]] = [:]
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let weekFormatter = DateFormatter()
        weekFormatter.dateFormat = "'Week of' MMM d"

        for item in items {
            guard let date = formatter.date(from: String(item.earningsDate.prefix(10))) else { continue }
            let calendar = Calendar.current
            let weekStart = calendar.date(from: calendar.dateComponents([.yearForWeekOfYear, .weekOfYear], from: date)) ?? date
            let key = weekFormatter.string(from: weekStart)
            groups[key, default: []].append(item)
        }
        return groups
    }

    // MARK: - Data Loading

    private func loadAll() async {
        isLoading = true
        errorMsg = nil

        do {
            async let earningsReq: EarningsResponse = db.get("/earnings/calendar?days=\(selectedDays)")
            async let eventsReq: UpcomingEconEventsResponse = db.get("/earnings/economic-events?days=\(selectedDays)")

            let (e, ev) = try await (earningsReq, eventsReq)
            earnings = e.earnings
            econEvents = ev.events
        } catch {
            errorMsg = error.localizedDescription
        }

        isLoading = false
    }
}
