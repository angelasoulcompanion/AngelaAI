//
//  SettingsView.swift
//  Pythia
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var db: DatabaseService
    @EnvironmentObject var backend: BackendManager
    @State private var settings: [AppSetting] = []
    @State private var isLoading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.largeSpacing) {
                Text("Settings")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Connection Status
                VStack(alignment: .leading, spacing: 12) {
                    Text("Connection")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)

                    HStack(spacing: 16) {
                        StatusRow(label: "Backend", isConnected: backend.isRunning, detail: backend.statusMessage)
                        StatusRow(label: "Database", isConnected: db.isConnected, detail: db.isConnected ? "Neon Cloud (Singapore)" : "Disconnected")
                    }
                }
                .padding()
                .pythiaCard()

                // App Info
                VStack(alignment: .leading, spacing: 12) {
                    Text("About")
                        .font(PythiaTheme.headline())
                        .foregroundColor(PythiaTheme.textPrimary)

                    HStack {
                        Image(systemName: "building.columns.fill")
                            .font(.system(size: 32))
                            .foregroundColor(PythiaTheme.accentGold)
                        VStack(alignment: .leading) {
                            Text("Pythia")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(PythiaTheme.textPrimary)
                            Text("Quantitative Finance + AI Analysis Platform")
                                .font(PythiaTheme.body())
                                .foregroundColor(PythiaTheme.textSecondary)
                            Text("Version 1.0.0 · Port 8766")
                                .font(PythiaTheme.caption())
                                .foregroundColor(PythiaTheme.textTertiary)
                        }
                    }
                }
                .padding()
                .pythiaCard()

                // Database Settings
                if !settings.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Database Settings")
                            .font(PythiaTheme.headline())
                            .foregroundColor(PythiaTheme.textPrimary)

                        ForEach(settings) { setting in
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(setting.settingKey)
                                        .font(.system(size: 13, weight: .medium, design: .monospaced))
                                        .foregroundColor(PythiaTheme.textPrimary)
                                    if let desc = setting.description {
                                        Text(desc)
                                            .font(PythiaTheme.caption())
                                            .foregroundColor(PythiaTheme.textTertiary)
                                    }
                                }
                                Spacer()
                                Text(setting.settingValue ?? "—")
                                    .font(.system(size: 13, design: .monospaced))
                                    .foregroundColor(PythiaTheme.accentGold)
                                if let cat = setting.category {
                                    Text(cat)
                                        .font(.system(size: 10))
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(PythiaTheme.surfaceBackground)
                                        .cornerRadius(4)
                                        .foregroundColor(PythiaTheme.textTertiary)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .pythiaCard()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
        .task {
            do {
                settings = try await db.fetchSettings()
            } catch { }
            isLoading = false
        }
    }
}

struct StatusRow: View {
    let label: String
    let isConnected: Bool
    let detail: String

    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(isConnected ? PythiaTheme.successGreen : PythiaTheme.errorRed)
                .frame(width: 10, height: 10)
            VStack(alignment: .leading) {
                Text(label)
                    .font(PythiaTheme.heading())
                    .foregroundColor(PythiaTheme.textPrimary)
                Text(detail)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(PythiaTheme.surfaceBackground.opacity(0.3))
        .cornerRadius(PythiaTheme.smallCornerRadius)
    }
}
