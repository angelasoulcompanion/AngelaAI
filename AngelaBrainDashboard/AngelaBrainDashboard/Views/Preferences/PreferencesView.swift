//
//  PreferencesView.swift
//  Angela Brain Dashboard
//
//  💜 Preferences View - David's Learned Preferences ⭐
//

import SwiftUI
import Combine

struct PreferencesView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = PreferencesViewModel()
    @State private var searchText = ""

    var body: some View {
        VStack(spacing: 0) {
            // Header with search
            header

            // Preferences list
            ScrollView {
                LazyVStack(spacing: AngelaTheme.spacing) {
                    ForEach(filteredPreferences) { preference in
                        PreferenceCard(preference: preference)
                    }
                }
                .padding(AngelaTheme.largeSpacing)
            }
        }
        .task {
            await viewModel.loadData(databaseService: databaseService)
        }
        .refreshable {
            await viewModel.loadData(databaseService: databaseService)
        }
    }

    private var filteredPreferences: [DavidPreference] {
        if searchText.isEmpty {
            return viewModel.preferences
        }
        return viewModel.preferences.filter {
            $0.preferenceKey.localizedCaseInsensitiveContains(searchText) ||
            $0.preferenceValue.localizedCaseInsensitiveContains(searchText)
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: AngelaTheme.spacing) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 8) {
                        Text("David's Preferences")
                            .font(AngelaTheme.title())
                            .foregroundColor(AngelaTheme.textPrimary)

                        Image(systemName: "star.fill")
                            .font(.system(size: 18))
                            .foregroundColor(AngelaTheme.accentGold)
                    }

                    Text("\(viewModel.preferences.count) preferences learned")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()
            }

            // Search bar
            HStack(spacing: 12) {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(AngelaTheme.textTertiary)

                TextField("Search preferences...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textPrimary)

                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(AngelaTheme.textTertiary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(12)
            .background(AngelaTheme.backgroundLight)
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }
}

// MARK: - Preference Card Component

struct PreferenceCard: View {
    let preference: DavidPreference

    private var confidenceColor: Color {
        switch preference.confidence {
        case 0.9...1.0: return AngelaTheme.successGreen
        case 0.7..<0.9: return AngelaTheme.emotionMotivated
        case 0.5..<0.7: return AngelaTheme.warningOrange
        default: return AngelaTheme.textTertiary
        }
    }

    private var categoryIcon: String {
        let key = preference.preferenceKey.lowercased()
        if key.contains("coffee") || key.contains("drink") {
            return "cup.and.saucer.fill"
        } else if key.contains("food") || key.contains("vitamin") {
            return "fork.knife"
        } else if key.contains("code") || key.contains("programming") {
            return "chevron.left.forwardslash.chevron.right"
        } else if key.contains("response") || key.contains("communication") {
            return "message.fill"
        } else if key.contains("morning") || key.contains("time") {
            return "clock.fill"
        } else {
            return "star.fill"
        }
    }

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Icon
            ZStack {
                Circle()
                    .fill(AngelaTheme.accentGold.opacity(0.2))
                    .frame(width: 50, height: 50)

                Image(systemName: categoryIcon)
                    .font(.system(size: 20))
                    .foregroundColor(AngelaTheme.accentGold)
            }

            // Content
            VStack(alignment: .leading, spacing: 12) {
                // Preference key (title)
                Text(formatPreferenceKey(preference.preferenceKey))
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textPrimary)

                // Preference value
                if let value = parsePreferenceValue(preference.preferenceValue) {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(Array(value.keys.sorted()), id: \.self) { key in
                            HStack {
                                Text("\(key):")
                                    .font(AngelaTheme.caption())
                                    .foregroundColor(AngelaTheme.textTertiary)

                                Text(value[key] ?? "")
                                    .font(AngelaTheme.body())
                                    .foregroundColor(AngelaTheme.textPrimary)
                            }
                        }
                    }
                } else {
                    Text(preference.preferenceValue)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                // Footer: Confidence + Learned from
                HStack {
                    // Confidence indicator
                    HStack(spacing: 6) {
                        Text("Confidence:")
                            .font(AngelaTheme.caption())
                            .foregroundColor(AngelaTheme.textTertiary)

                        HStack(spacing: 2) {
                            ForEach(0..<5) { index in
                                Image(systemName: index < Int(preference.confidence * 5) ? "star.fill" : "star")
                                    .font(.system(size: 10))
                                    .foregroundColor(confidenceColor)
                            }
                        }

                        Text("\(Int(preference.confidence * 100))%")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(confidenceColor)
                    }

                    Spacer()

                    // Learned from (if available)
                    if let learnedFrom = preference.learnedFrom {
                        HStack(spacing: 4) {
                            Image(systemName: "lightbulb.fill")
                                .font(.system(size: 10))
                            Text(learnedFrom)
                                .font(AngelaTheme.caption())
                        }
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(AngelaTheme.primaryPurple.opacity(0.15))
                        .cornerRadius(6)
                    }
                }

                // Time learned
                Text("Learned \(preference.createdAt, style: .relative)")
                    .font(.system(size: 11))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(
            LinearGradient(
                colors: [AngelaTheme.accentGold.opacity(0.03), AngelaTheme.cardBackground],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(AngelaTheme.cornerRadius)
        .overlay(
            RoundedRectangle(cornerRadius: AngelaTheme.cornerRadius)
                .stroke(AngelaTheme.accentGold.opacity(0.2), lineWidth: 1)
        )
    }

    // MARK: - Helper Functions

    private func formatPreferenceKey(_ key: String) -> String {
        // Convert snake_case to Title Case
        key.replacingOccurrences(of: "_", with: " ")
            .capitalized
    }

    private func parsePreferenceValue(_ value: String) -> [String: String]? {
        // Try to parse JSON value
        guard let data = value.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return nil
        }

        var result: [String: String] = [:]
        for (key, val) in json {
            if let stringVal = val as? String {
                result[key.capitalized] = stringVal
            } else {
                result[key.capitalized] = "\(val)"
            }
        }
        return result.isEmpty ? nil : result
    }
}

// MARK: - View Model

@MainActor
class PreferencesViewModel: ObservableObject {
    @Published var preferences: [DavidPreference] = []
    @Published var isLoading = false

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do {
            preferences = try await databaseService.fetchDavidPreferences(limit: 50)
        } catch {
            print("Error loading preferences: \(error)")
        }

        isLoading = false
    }
}
