//
//  OptionsChainView.swift
//  Pythia — Black-Scholes Options Pricer
//

import SwiftUI

struct OptionsChainView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var optionType = "call"
    @State private var spotStr = "100"
    @State private var strikeStr = "100"
    @State private var expiryStr = "0.25"
    @State private var volStr = "0.20"

    @State private var result: OptionPriceResponse?
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("Options Pricer (Black-Scholes)")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                // Input form
                HStack(spacing: PythiaTheme.largeSpacing) {
                    VStack(alignment: .leading, spacing: 8) {
                        Picker("Type", selection: $optionType) {
                            Text("Call").tag("call")
                            Text("Put").tag("put")
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 160)

                        inputField("Spot Price", $spotStr)
                        inputField("Strike Price", $strikeStr)
                        inputField("Time to Expiry (years)", $expiryStr)
                        inputField("Volatility", $volStr)

                        Button("Calculate") { Task { await calculate() } }
                            .pythiaPrimaryButton()
                    }
                    .frame(width: 280)

                    if let r = result {
                        resultPanel(r)
                    }
                }
                .padding()
                .pythiaCard()
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)
    }

    private func inputField(_ label: String, _ binding: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
            TextField("", text: binding)
                .textFieldStyle(.roundedBorder)
                .frame(width: 160)
        }
    }

    private func resultPanel(_ r: OptionPriceResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            Text("\(r.optionType.capitalized) Option")
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.accentGold)

            HStack(spacing: PythiaTheme.largeSpacing) {
                metricCol("Price", String(format: "%.4f", r.price), PythiaTheme.textPrimary)
                metricCol("Intrinsic", String(format: "%.4f", r.intrinsicValue), PythiaTheme.profit)
                metricCol("Time Value", String(format: "%.4f", r.timeValue), PythiaTheme.secondaryBlue)
            }

            Divider().background(PythiaTheme.textTertiary)

            Text("Greeks")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            HStack(spacing: PythiaTheme.largeSpacing) {
                greekBox("Delta (\u{0394})", r.greeks.delta, PythiaTheme.secondaryBlue)
                greekBox("Gamma (\u{0393})", r.greeks.gamma, PythiaTheme.accentGold)
                greekBox("Theta (\u{0398})", r.greeks.theta, PythiaTheme.loss)
                greekBox("Vega (\u{03BD})", r.greeks.vega, PythiaTheme.profit)
                greekBox("Rho (\u{03C1})", r.greeks.rho, PythiaTheme.textSecondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func metricCol(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
    }

    private func greekBox(_ label: String, _ value: Double, _ color: Color) -> some View {
        VStack(spacing: 4) {
            Text(String(format: "%.6f", value))
                .font(PythiaTheme.monospace())
                .foregroundColor(color)
            Text(label)
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(minWidth: 80)
    }

    private func calculate() async {
        guard let spot = Double(spotStr), let strike = Double(strikeStr),
              let expiry = Double(expiryStr), let vol = Double(volStr) else { return }
        isLoading = true
        do {
            result = try await db.priceOption(type: optionType, spot: spot, strike: strike, expiry: expiry, vol: vol)
        } catch {}
        isLoading = false
    }
}
