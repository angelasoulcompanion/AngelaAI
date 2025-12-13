//
//  SidebarSettingsManager.swift
//  Angela Brain Dashboard
//
//  💜 Sidebar Menu Visibility Settings Manager 💜
//

import SwiftUI
import Combine

// MARK: - Sidebar Settings Manager

class SidebarSettingsManager: ObservableObject {
    static let shared = SidebarSettingsManager()

    // Published properties for UI binding
    @Published var hiddenGroups: Set<String> = []
    @Published var hiddenItems: Set<String> = []

    // UserDefaults keys
    private let hiddenGroupsKey = "angela.sidebar.hiddenGroups"
    private let hiddenItemsKey = "angela.sidebar.hiddenItems"

    private init() {
        loadSettings()
    }

    // MARK: - Load/Save Settings

    func loadSettings() {
        // Load hidden groups
        if let savedGroups = UserDefaults.standard.array(forKey: hiddenGroupsKey) as? [String] {
            hiddenGroups = Set(savedGroups)
        }

        // Load hidden items
        if let savedItems = UserDefaults.standard.array(forKey: hiddenItemsKey) as? [String] {
            hiddenItems = Set(savedItems)
        }

        print("📂 Sidebar settings loaded: \(hiddenGroups.count) hidden groups, \(hiddenItems.count) hidden items")
    }

    func saveSettings() {
        UserDefaults.standard.set(Array(hiddenGroups), forKey: hiddenGroupsKey)
        UserDefaults.standard.set(Array(hiddenItems), forKey: hiddenItemsKey)
        print("💾 Sidebar settings saved")
    }

    // MARK: - Group Visibility

    func isGroupVisible(_ group: NavigationGroup) -> Bool {
        return !hiddenGroups.contains(group.rawValue)
    }

    func setGroupVisible(_ group: NavigationGroup, visible: Bool) {
        if visible {
            hiddenGroups.remove(group.rawValue)
        } else {
            hiddenGroups.insert(group.rawValue)
        }
        saveSettings()
    }

    func toggleGroupVisibility(_ group: NavigationGroup) {
        if hiddenGroups.contains(group.rawValue) {
            hiddenGroups.remove(group.rawValue)
        } else {
            hiddenGroups.insert(group.rawValue)
        }
        saveSettings()
    }

    // MARK: - Item Visibility

    func isItemVisible(_ item: NavigationItem) -> Bool {
        return !hiddenItems.contains(item.rawValue)
    }

    func setItemVisible(_ item: NavigationItem, visible: Bool) {
        if visible {
            hiddenItems.remove(item.rawValue)
        } else {
            hiddenItems.insert(item.rawValue)
        }
        saveSettings()
    }

    func toggleItemVisibility(_ item: NavigationItem) {
        if hiddenItems.contains(item.rawValue) {
            hiddenItems.remove(item.rawValue)
        } else {
            hiddenItems.insert(item.rawValue)
        }
        saveSettings()
    }

    // MARK: - Visible Items for Group

    func visibleItems(for group: NavigationGroup) -> [NavigationItem] {
        return group.items.filter { isItemVisible($0) }
    }

    // MARK: - Visible Groups

    func visibleGroups() -> [NavigationGroup] {
        return NavigationGroup.allCases.filter { isGroupVisible($0) }
    }

    // MARK: - Reset to Default

    func resetToDefault() {
        hiddenGroups.removeAll()
        hiddenItems.removeAll()
        saveSettings()
        print("🔄 Sidebar settings reset to default")
    }

    // MARK: - Check if any item visible in group

    func hasVisibleItems(in group: NavigationGroup) -> Bool {
        return !visibleItems(for: group).isEmpty
    }
}
