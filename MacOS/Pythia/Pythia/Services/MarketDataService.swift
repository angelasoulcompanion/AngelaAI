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

    /// Format market cap with appropriate suffix (B, M, K)
    func formatMarketCap(_ value: Double?) -> String {
        guard let value = value else { return "N/A" }
        if value >= 1_000_000_000_000 {
            return String(format: "%.1fT", value / 1_000_000_000_000)
        } else if value >= 1_000_000_000 {
            return String(format: "%.1fB", value / 1_000_000_000)
        } else if value >= 1_000_000 {
            return String(format: "%.1fM", value / 1_000_000)
        } else if value >= 1_000 {
            return String(format: "%.1fK", value / 1_000)
        }
        return String(format: "%.0f", value)
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
