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
    @State private var showCreateSheet = false

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

                    Button {
                        showCreateSheet = true
                    } label: {
                        Label("Create Alert", systemImage: "plus.circle.fill")
                    }
                    .pythiaPrimaryButton()

                    Button("Check Now") { Task { await checkAlerts() } }
                        .buttonStyle(.plain)
                        .foregroundColor(PythiaTheme.accentGold)

                    Button("Mark All Read") { Task { await markAllRead() } }
                        .buttonStyle(.plain)
                        .foregroundColor(PythiaTheme.textTertiary)
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
        .sheet(isPresented: $showCreateSheet) {
            CreateAlertSheet(db: db) {
                showCreateSheet = false
                Task { await loadAlerts() }
            }
        }
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


// MARK: - Create Alert Sheet

struct CreateAlertSheet: View {
    let db: DatabaseService
    let onDismiss: () -> Void

    @State private var alertType = "custom"
    @State private var title = ""
    @State private var message = ""
    @State private var severity = "info"
    @State private var isSaving = false

    private let alertTypes = [
        ("custom", "Custom", "bell.fill"),
        ("price_alert", "Price Alert", "chart.line.uptrend.xyaxis"),
        ("var_breach", "VaR Breach", "exclamationmark.triangle.fill"),
        ("rebalance", "Rebalance Needed", "scale.3d"),
        ("earnings", "Earnings Reminder", "calendar.badge.clock"),
        ("signal", "Trading Signal", "antenna.radiowaves.left.and.right"),
    ]

    private let severities = [
        ("info", "Info", Color.blue),
        ("warning", "Warning", Color.orange),
        ("critical", "Critical", Color.red),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                Text("Create Alert")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                Button { onDismiss() } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(PythiaTheme.textTertiary)
                }
                .buttonStyle(.plain)
            }
            .padding(20)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Alert Type
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Alert Type")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(PythiaTheme.textTertiary)

                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 8) {
                            ForEach(alertTypes, id: \.0) { type, label, icon in
                                Button {
                                    alertType = type
                                } label: {
                                    HStack(spacing: 8) {
                                        Image(systemName: icon)
                                            .font(.system(size: 14))
                                        Text(label)
                                            .font(.system(size: 12, weight: .medium))
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 10)
                                    .background(alertType == type ? PythiaTheme.accentGold.opacity(0.15) : PythiaTheme.surfaceBackground)
                                    .foregroundColor(alertType == type ? PythiaTheme.accentGold : PythiaTheme.textSecondary)
                                    .cornerRadius(8)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(alertType == type ? PythiaTheme.accentGold : Color.clear, lineWidth: 1)
                                    )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    // Title
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Title")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("e.g., AAPL drops below $200", text: $title)
                            .textFieldStyle(.plain)
                            .padding(10)
                            .background(PythiaTheme.surfaceBackground)
                            .cornerRadius(8)
                            .foregroundColor(PythiaTheme.textPrimary)
                    }

                    // Message
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Message (optional)")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(PythiaTheme.textTertiary)
                        TextField("Additional details...", text: $message, axis: .vertical)
                            .textFieldStyle(.plain)
                            .lineLimit(3...5)
                            .padding(10)
                            .background(PythiaTheme.surfaceBackground)
                            .cornerRadius(8)
                            .foregroundColor(PythiaTheme.textPrimary)
                    }

                    // Severity
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Severity")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(PythiaTheme.textTertiary)

                        HStack(spacing: 10) {
                            ForEach(severities, id: \.0) { sev, label, color in
                                Button {
                                    severity = sev
                                } label: {
                                    HStack(spacing: 6) {
                                        Circle().fill(color).frame(width: 8, height: 8)
                                        Text(label)
                                            .font(.system(size: 12, weight: .medium))
                                    }
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 8)
                                    .background(severity == sev ? color.opacity(0.15) : PythiaTheme.surfaceBackground)
                                    .foregroundColor(severity == sev ? color : PythiaTheme.textSecondary)
                                    .cornerRadius(8)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .stroke(severity == sev ? color : Color.clear, lineWidth: 1)
                                    )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                }
                .padding(20)
            }

            Divider()

            // Footer
            HStack {
                Spacer()
                Button("Cancel") { onDismiss() }
                    .buttonStyle(.plain)
                    .foregroundColor(PythiaTheme.textTertiary)

                Button {
                    Task { await createAlert() }
                } label: {
                    if isSaving {
                        ProgressView().scaleEffect(0.7)
                    } else {
                        Text("Create Alert")
                    }
                }
                .pythiaPrimaryButton()
                .disabled(title.isEmpty || isSaving)
            }
            .padding(20)
        }
        .frame(width: 520, height: 560)
        .background(PythiaTheme.cardBackground)
    }

    private func createAlert() async {
        isSaving = true
        defer { isSaving = false }

        struct CreateBody: Codable {
            let alertType: String
            let title: String
            let message: String
            let severity: String

            enum CodingKeys: String, CodingKey {
                case alertType = "alert_type"
                case title, message, severity
            }
        }

        do {
            let _: [String: AnyCodable] = try await db.post(
                "/alerts/",
                body: CreateBody(alertType: alertType, title: title, message: message, severity: severity)
            )
            onDismiss()
        } catch {
            print("[Alert] Create error: \(error)")
        }
    }
}
