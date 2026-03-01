//
//  EmptyStateView.swift
//  Pythia
//

import SwiftUI

struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(PythiaTheme.textTertiary)

            Text(title)
                .font(PythiaTheme.headline())
                .foregroundColor(PythiaTheme.textPrimary)

            Text(message)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 300)

            if let actionTitle = actionTitle, let action = action {
                Button(action: action) {
                    Text(actionTitle)
                        .pythiaPrimaryButton()
                }
                .buttonStyle(.plain)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
