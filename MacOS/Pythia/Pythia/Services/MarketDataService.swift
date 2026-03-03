//
//  MarketDataService.swift
//  Pythia
//
//  Market data helpers and formatters
//

import Foundation

class MarketDataService: ObservableObject {
    static let shared = MarketDataService()

    private init() {}

    /// Format large number with T/B/M/K suffix, supporting negative values.
    /// Single source of truth — replaces formatMarketCap and FinancialOutlookView.formatLargeNumber.
    func formatLargeNumber(_ value: Double) -> String {
        let abs = Swift.abs(value)
        let sign = value < 0 ? "-" : ""
        if abs >= 1_000_000_000_000 {
            return String(format: "%@%.1fT", sign, abs / 1_000_000_000_000)
        } else if abs >= 1_000_000_000 {
            return String(format: "%@%.1fB", sign, abs / 1_000_000_000)
        } else if abs >= 1_000_000 {
            return String(format: "%@%.1fM", sign, abs / 1_000_000)
        } else if abs >= 1_000 {
            return String(format: "%@%.1fK", sign, abs / 1_000)
        }
        return String(format: "%@%.0f", sign, abs)
    }

    /// Format market cap — convenience wrapper with Optional handling.
    func formatMarketCap(_ value: Double?) -> String {
        guard let value = value else { return "N/A" }
        return formatLargeNumber(value)
    }

    /// Format large number with currency prefix.
    func formatMoney(_ value: Double, currency: String?) -> String {
        let prefix: String
        switch currency?.uppercased() {
        case "THB": prefix = "฿"
        case "USD": prefix = "$"
        case "EUR": prefix = "€"
        case "GBP": prefix = "£"
        case "JPY": prefix = "¥"
        default: prefix = ""
        }
        return "\(prefix)\(formatLargeNumber(value))"
    }

    /// Format volume with suffix
    func formatVolume(_ value: Int?) -> String {
        guard let value = value else { return "N/A" }
        if value >= 1_000_000 {
            return String(format: "%.1fM", Double(value) / 1_000_000)
        } else if value >= 1_000 {
            return String(format: "%.1fK", Double(value) / 1_000)
        }
        return "\(value)"
    }

    /// Format change with sign
    func formatChange(_ value: Double?) -> String {
        guard let value = value else { return "" }
        let sign = value >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", value))"
    }

    /// Format change percent with sign
    func formatChangePercent(_ value: Double?) -> String {
        guard let value = value else { return "" }
        let sign = value >= 0 ? "+" : ""
        return "\(sign)\(String(format: "%.2f", value))%"
    }
}
