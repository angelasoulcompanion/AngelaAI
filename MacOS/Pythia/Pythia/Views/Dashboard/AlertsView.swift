//
//  AlertsView.swift
//  Pythia — Alert System (Phase 8.8)
//

import SwiftUI

struct AlertsView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var alerts: [AlertItem] = []
    @State private var isLoading = false
    @State private var showUnreadOnly = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                HStack {
                    Text("Alerts")
                        .font(PythiaTheme.title())
                        .foregroundColor(PythiaTheme.textPrimary)

                    Spacer()

                    Toggle("Unread Only", isOn: $showUnreadOnly)
                        .toggleStyle(.switch)
                        .frame(width: 140)
                        .onChange(of: showUnreadOnly) { _, _ in Task { await loadAlerts() } }

                    Button("Check Now") { Task { await checkAlerts() } }
                        .pythiaPrimaryButton()

                    Button("Mark All Read") { Task { await markAllRead() } }
                        .buttonStyle(.plain)
                        .foregroundColor(PythiaTheme.accentGold)
                }

                if isLoading { LoadingView("Checking alerts...") }

                if alerts.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "bell.slash")
                            .font(.system(size: 36))
                            .foregroundColor(PythiaTheme.textTertiary)
                        Text("No alerts")
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textTertiary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(40)
                } else {
                    ForEach(alerts) { alert in
                        alertCard(alert)
                    }
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task { await loadAlerts() }
    }

    private func alertCard(_ alert: AlertItem) -> some View {
        HStack(alignment: .top, spacing: 12) {
            // Severity icon
            Image(systemName: severityIcon(alert.severity))
                .font(.system(size: 18))
                .foregroundColor(severityColor(alert.severity))
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(alert.title)
                        .font(.system(size: 14, weight: alert.isRead ? .regular : .bold))
                        .foregroundColor(alert.isRead ? PythiaTheme.textSecondary : PythiaTheme.textPrimary)

                    Spacer()

                    Text(alert.alertType.uppercased())
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(4)

                    if !alert.isRead {
                        Circle()
                            .fill(PythiaTheme.secondaryBlue)
                            .frame(width: 8, height: 8)
                    }
                }

                if let msg = alert.message, !msg.isEmpty {
                    Text(msg)
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.textTertiary)
                }

                if let time = alert.triggeredAt {
                    Text(String(time.prefix(19)))
                        .font(.system(size: 10))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
            }

            // Mark read button
            if !alert.isRead {
                Button {
                    Task { await markRead(alert.alertId) }
                } label: {
                    Image(systemName: "checkmark.circle")
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding()
        .background(alert.isRead ? Color.clear : severityColor(alert.severity).opacity(0.05))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(severityColor(alert.severity).opacity(alert.isRead ? 0.1 : 0.25), lineWidth: 1)
        )
        .cornerRadius(12)
    }

    private func severityIcon(_ severity: String) -> String {
        switch severity {
        case "critical": return "exclamationmark.octagon.fill"
        case "warning": return "exclamationmark.triangle.fill"
        case "info": return "info.circle.fill"
        default: return "bell.fill"
        }
    }

    private func severityColor(_ severity: String) -> Color {
        switch severity {
        case "critical": return PythiaTheme.errorRed
        case "warning": return PythiaTheme.warningOrange
        case "info": return PythiaTheme.secondaryBlue
        default: return PythiaTheme.textSecondary
        }
    }

    // MARK: - API

    private func loadAlerts() async {
        do {
            let resp: AlertListResponse = try await db.get("/alerts/?unread_only=\(showUnreadOnly)")
            alerts = resp.alerts
        } catch { alerts = [] }
    }

    private func checkAlerts() async {
        isLoading = true; defer { isLoading = false }
        do {
            let _: CheckAlertsResponse = try await db.post("/alerts/check", body: EmptyBody())
            await loadAlerts()
        } catch {}
    }

    private func markRead(_ id: String) async {
        do {
            let _: [String: Bool] = try await db.put("/alerts/\(id)/read", body: EmptyBody())
            await loadAlerts()
        } catch {}
    }

    private func markAllRead() async {
        do {
            let _: [String: AnyCodable] = try await db.put("/alerts/read-all", body: EmptyBody())
            await loadAlerts()
        } catch {}
    }
}
