//
//  PeriodPicker.swift
//  Pythia — Reusable period selection picker
//
//  Replaces duplicated "90 Days / 1 Year / 3 Years" picker across
//  PerformanceView, CorrelationView, StatisticsView.
//

import SwiftUI

/// Standard period picker with 90-day, 1-year, and 3-year options.
struct PeriodPicker: View {
    @Binding var days: Int

    var body: some View {
        Picker("Period", selection: $days) {
            Text("90 Days").tag(90)
            Text("1 Year").tag(365)
            Text("3 Years").tag(1095)
        }
        .frame(width: 120)
    }
}
