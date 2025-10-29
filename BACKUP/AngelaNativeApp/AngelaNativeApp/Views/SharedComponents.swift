//
//  SharedComponents.swift
//  AngelaNativeApp
//
//  Shared UI components used across multiple views
//

import SwiftUI

// MARK: - Info Row

struct InfoRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .frame(width: 24)
                .foregroundColor(.purple)

            Text(label)
                .foregroundColor(.secondary)

            Spacer()

            Text(value)
                .fontWeight(.medium)
        }
    }
}
