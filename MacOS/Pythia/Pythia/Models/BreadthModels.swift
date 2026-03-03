//
//  BreadthModels.swift
//  Pythia — Market Breadth Indicator Models
//

import Foundation

struct BreadthUniverse: Codable, Identifiable {
    let id: String
    let name: String
    let type: String
    let size: Int
}

struct BreadthResponse: Codable {
    let universe: String?
    let universeSize: Int
    let period: String?
    let dates: [String]
    let indicators: BreadthIndicators
    let current: BreadthCurrent
    let success: Bool

    enum CodingKeys: String, CodingKey {
        case universe
        case universeSize = "universe_size"
        case period, dates, indicators, current, success
    }
}

struct BreadthIndicators: Codable {
    let advances: [Double?]
    let declines: [Double?]
    let unchanged: [Double?]
    let adLine: [Double?]
    let adRatio: [Double?]
    let pctAbove50ma: [Double?]
    let pctAbove200ma: [Double?]
    let newHighs: [Double?]
    let newLows: [Double?]
    let highLowIndex: [Double?]
    let mcclEllanOscillator: [Double?]
    let mcclEllanSummation: [Double?]
    let trin: [Double?]
    let trin10dAvg: [Double?]
    let zweigBreadthThrust: [Double?]
    let zbtSignal: [Double?]

    enum CodingKeys: String, CodingKey {
        case advances, declines, unchanged
        case adLine = "ad_line"
        case adRatio = "ad_ratio"
        case pctAbove50ma = "pct_above_50ma"
        case pctAbove200ma = "pct_above_200ma"
        case newHighs = "new_highs"
        case newLows = "new_lows"
        case highLowIndex = "high_low_index"
        case mcclEllanOscillator = "mcclellan_oscillator"
        case mcclEllanSummation = "mcclellan_summation"
        case trin
        case trin10dAvg = "trin_10d_avg"
        case zweigBreadthThrust = "zweig_breadth_thrust"
        case zbtSignal = "zbt_signal"
    }
}

struct BreadthCurrent: Codable {
    let regime: String
    let adRatio: Double?
    let pctAbove50ma: Double?
    let pctAbove200ma: Double?
    let mcclEllanOscillator: Double?
    let mcclEllanSummation: Double?
    let trin: Double?
    let newHighs: Double?
    let newLows: Double?
    let divergences: [String]

    enum CodingKeys: String, CodingKey {
        case regime
        case adRatio = "ad_ratio"
        case pctAbove50ma = "pct_above_50ma"
        case pctAbove200ma = "pct_above_200ma"
        case mcclEllanOscillator = "mcclellan_oscillator"
        case mcclEllanSummation = "mcclellan_summation"
        case trin
        case newHighs = "new_highs"
        case newLows = "new_lows"
        case divergences
    }
}
