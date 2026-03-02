//
//  ErrorMessageView.swift
//  Pythia — Reusable error display component
//
//  Replaces ad-hoc `Text(error).foregroundColor(PythiaTheme.errorRed).padding()`
//  across 8+ views.
//

import SwiftUI

/// Displays an error message with consistent styling.
struct ErrorMessageView: View {
    let message: String

    var body: some View {
        Text(message)
            .foregroundColor(PythiaTheme.errorRed)
            .padding()
    }
}
