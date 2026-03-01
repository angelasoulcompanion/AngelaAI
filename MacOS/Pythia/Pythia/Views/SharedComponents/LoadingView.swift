//
//  LoadingView.swift
//  Pythia
//

import SwiftUI

struct LoadingView: View {
    let message: String

    init(_ message: String = "Loading...") {
        self.message = message
    }

    var body: some View {
        VStack(spacing: 12) {
            ProgressView()
                .scaleEffect(1.2)
                .tint(PythiaTheme.secondaryBlue)

            Text(message)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
