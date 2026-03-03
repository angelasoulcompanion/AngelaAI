//
//  HoldingsView.swift
//  Pythia
//

import SwiftUI

struct HoldingsView: View {
    let holdings: [Holding]
    var onAdd: (() -> Void)?
    var onDelete: ((Holding) -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Holdings")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if let onAdd = onAdd {
                    Button(action: onAdd) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 18))
                            .foregroundColor(PythiaTheme.secondaryBlue)
                    }
                    .buttonStyle(.plain)
                }
            }

            if holdings.isEmpty {
                Text("No holdings yet")
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textTertiary)
                    .padding()
            } else {
                // Header
                HStack {
                    Text("Symbol").frame(width: 80, alignment: .leading)
                    Text("Name").frame(minWidth: 120, alignment: .leading)
                    Text("Weight").frame(width: 70, alignment: .trailing)
                    Text("Quantity").frame(width: 80, alignment: .trailing)
                    Text("Avg Cost").frame(width: 90, alignment: .trailing)
                    Text("Market Value").frame(width: 110, alignment: .trailing)
                    if onDelete != nil {
                        Spacer().frame(width: 36)
                    }
                }
                .font(PythiaTheme.caption())
                .foregroundColor(PythiaTheme.textTertiary)
                .padding(.horizontal)

                Divider().background(PythiaTheme.textTertiary.opacity(0.3))

                ForEach(holdings) { holding in
                    HStack {
                        Text(holding.symbol)
                            .font(.system(size: 13, weight: .semibold, design: .monospaced))
                            .foregroundColor(PythiaTheme.accentGold)
                            .frame(width: 80, alignment: .leading)
                        Text(holding.assetName ?? "")
                            .font(PythiaTheme.body())
                            .foregroundColor(PythiaTheme.textPrimary)
                            .lineLimit(1)
                            .frame(minWidth: 120, alignment: .leading)
                        Text(PythiaTheme.formatPercent(holding.weight))
                            .font(.system(size: 13, design: .monospaced))
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 70, alignment: .trailing)
                        Text(holding.quantity != nil ? String(format: "%.2f", holding.quantity!) : "-")
                            .font(.system(size: 13, design: .monospaced))
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 80, alignment: .trailing)
                        Text(holding.averageCost != nil ? String(format: "%.2f", holding.averageCost!) : "-")
                            .font(.system(size: 13, design: .monospaced))
                            .foregroundColor(PythiaTheme.textSecondary)
                            .frame(width: 90, alignment: .trailing)
                        Text(PythiaTheme.formatCurrency(holding.marketValue ?? 0))
                            .font(.system(size: 13, weight: .medium, design: .monospaced))
                            .foregroundColor(PythiaTheme.textPrimary)
                            .frame(width: 110, alignment: .trailing)
                        if let onDelete = onDelete {
                            Button { onDelete(holding) } label: {
                                Image(systemName: "trash")
                                    .font(.system(size: 12))
                                    .foregroundColor(PythiaTheme.loss.opacity(0.7))
                            }
                            .buttonStyle(.plain)
                            .frame(width: 36)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 4)
                }
            }
        }
        .padding()
        .pythiaCard()
    }
}
