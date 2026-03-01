//
//  ChartViews.swift
//  Pythia — Reusable chart components
//

import SwiftUI
import Charts

// MARK: - Simple Line Chart

struct SimpleLineChart: View {
    let data: [(String, Double)]
    let color: Color
    let showArea: Bool

    init(data: [(String, Double)], color: Color = PythiaTheme.secondaryBlue, showArea: Bool = true) {
        self.data = data
        self.color = color
        self.showArea = showArea
    }

    var body: some View {
        Chart {
            ForEach(data, id: \.0) { item in
                LineMark(
                    x: .value("Date", item.0),
                    y: .value("Value", item.1)
                )
                .foregroundStyle(color)
                .interpolationMethod(.catmullRom)

                if showArea {
                    AreaMark(
                        x: .value("Date", item.0),
                        y: .value("Value", item.1)
                    )
                    .foregroundStyle(color.opacity(0.08))
                    .interpolationMethod(.catmullRom)
                }
            }
        }
        .chartXAxis(.hidden)
        .chartYAxis {
            AxisMarks(position: .leading) { _ in
                AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4]))
                    .foregroundStyle(PythiaTheme.textTertiary.opacity(0.3))
                AxisValueLabel()
                    .foregroundStyle(PythiaTheme.textTertiary)
            }
        }
    }
}

// MARK: - Profit/Loss Bar

struct ProfitLossBar: View {
    let value: Double
    let maxValue: Double

    var body: some View {
        GeometryReader { geometry in
            let width = geometry.size.width
            let barWidth = min(abs(value / maxValue) * width / 2, width / 2)
            let color = PythiaTheme.profitLossColor(value)

            HStack(spacing: 0) {
                if value < 0 {
                    Spacer()
                    Rectangle()
                        .fill(color.opacity(0.6))
                        .frame(width: barWidth, height: 8)
                        .cornerRadius(4)
                    Rectangle()
                        .fill(PythiaTheme.textTertiary.opacity(0.3))
                        .frame(width: 1, height: 16)
                    Spacer()
                } else {
                    Spacer()
                    Rectangle()
                        .fill(PythiaTheme.textTertiary.opacity(0.3))
                        .frame(width: 1, height: 16)
                    Rectangle()
                        .fill(color.opacity(0.6))
                        .frame(width: barWidth, height: 8)
                        .cornerRadius(4)
                    Spacer()
                }
            }
        }
        .frame(height: 16)
    }
}
