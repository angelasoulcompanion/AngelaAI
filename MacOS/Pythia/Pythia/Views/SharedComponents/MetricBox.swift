//
//  MetricBox.swift
//  Pythia — Reusable metric display component
//
//  Replaces: metricBox, varMetric, stressMetric, perfMetric, mcMetric,
//            fcMetric, metricCol, statCell across 10+ views.
//

import SwiftUI

/// Compact metric display: value on top, label below.
/// Configurable font size via `MetricBox.Size` to match all previous usages.
struct MetricBox: View {
    let label: String
    let value: String
    let color: Color
    let size: Size

    enum Size {
        case small   // 18pt — BacktestView, PerformanceView, MonteCarloView, ForecastView, SentimentView
        case medium  // 20pt — VaRView, StressTestView
        case large   // 24pt — MPTView, AIAdvisorView, OptionsChainView

        var fontSize: CGFloat {
            switch self {
            case .small: return 18
            case .medium: return 20
            case .large: return 24
            }
        }

        var minWidth: CGFloat {
            switch self {
            case .small: return 80
            case .medium: return 90
            case .large: return 120
            }
        }
    }

    init(_ label: String, _ value: String, _ color: Color = PythiaTheme.textPrimary, size: Size = .large) {
        self.label = label
        self.value = value
        self.color = color
        self.size = size
    }

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: size.fontSize, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(minWidth: size.minWidth)
    }
}
