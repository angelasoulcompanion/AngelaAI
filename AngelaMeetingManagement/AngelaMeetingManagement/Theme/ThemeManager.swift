//
//  ThemeManager.swift
//  AngelaMeetingManagement
//
//  Created by น้อง Angela 💜 for ที่รัก David
//  Theme Management for Dark/Light Mode
//

import SwiftUI
import Combine

class ThemeManager: ObservableObject {
    @AppStorage("isDarkMode") var isDarkMode: Bool = false

    static let shared = ThemeManager()

    private init() {
        // AppStorage automatically syncs with UserDefaults
    }

    func toggleTheme() {
        isDarkMode.toggle()
    }
}
