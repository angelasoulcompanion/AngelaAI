//
//  PageVisibilityManager.swift
//  Pythia — Manage which sidebar pages are visible
//

import SwiftUI

class PageVisibilityManager: ObservableObject {
    private let storageKey = "hiddenSidebarPages"

    @Published var hiddenPages: Set<String> {
        didSet { save() }
    }

    init() {
        if let data = UserDefaults.standard.data(forKey: storageKey),
           let decoded = try? JSONDecoder().decode(Set<String>.self, from: data) {
            hiddenPages = decoded
        } else {
            hiddenPages = []
        }
    }

    func isVisible(_ item: SidebarItem) -> Bool {
        !hiddenPages.contains(item.rawValue)
    }

    func toggle(_ item: SidebarItem) {
        if hiddenPages.contains(item.rawValue) {
            hiddenPages.remove(item.rawValue)
        } else {
            hiddenPages.insert(item.rawValue)
        }
    }

    func setVisible(_ item: SidebarItem, visible: Bool) {
        if visible {
            hiddenPages.remove(item.rawValue)
        } else {
            hiddenPages.insert(item.rawValue)
        }
    }

    func showAll() {
        hiddenPages.removeAll()
    }

    private func save() {
        if let data = try? JSONEncoder().encode(hiddenPages) {
            UserDefaults.standard.set(data, forKey: storageKey)
        }
    }
}
