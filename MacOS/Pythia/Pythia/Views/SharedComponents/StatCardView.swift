//
//  StatCardView.swift
//  Pythia
//

import SwiftUI

struct StatCardView: View {
    let title: String
    let value: String
    let subtitle: String?
    let icon: String
    let color: Color
    let trend: Double?

    init(title: String, value: String, subtitle: String? = nil,
         icon: String = "chart.bar.fill", color: Color = PythiaTheme.secondaryBlue,
         trend: Double? = nil) {
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.icon = icon
        self.color = color
        self.trend = trend
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.system(size: 14))
                Text(title)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textSecondary)
                Spacer()
                if let trend = trend {
                    HStack(spacing: 2) {
                        Image(systemName: trend >= 0 ? "arrow.up.right" : "arrow.down.right")
                            .font(.system(size: 10))
                        Text(String(format: "%.1f%%", abs(trend)))
                            .font(.system(size: 11, weight: .medium))
                    }
                    .foregroundColor(PythiaTheme.profitLossColor(trend))
                }
            }

            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(PythiaTheme.textPrimary)

            if let subtitle = subtitle {
                Text(subtitle)
                    .font(PythiaTheme.caption())
                    .foregroundColor(PythiaTheme.textTertiary)
            }
        }
        .padding()
        .pythiaCard()
    }
}
