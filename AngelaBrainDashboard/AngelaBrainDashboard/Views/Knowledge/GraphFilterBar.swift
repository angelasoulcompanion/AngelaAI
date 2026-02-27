//
//  GraphFilterBar.swift
//  Angela Brain Dashboard
//
//  Search + category filter controls for Knowledge Graph view
//

import SwiftUI

struct GraphFilterBar: View {
    @Binding var searchText: String
    @Binding var selectedCategory: String?
    let categories: [String]
    let onSearch: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // Search field
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                TextField("Search knowledge graph...", text: $searchText)
                    .textFieldStyle(.plain)
                    .onSubmit { onSearch() }
                if !searchText.isEmpty {
                    Button(action: {
                        searchText = ""
                        onSearch()
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(Color(.controlBackgroundColor))
            .cornerRadius(8)
            .frame(maxWidth: 300)

            // Category pills
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    CategoryPill(label: "All", isSelected: selectedCategory == nil) {
                        selectedCategory = nil
                    }
                    ForEach(categories, id: \.self) { cat in
                        CategoryPill(
                            label: cat.capitalized,
                            isSelected: selectedCategory == cat
                        ) {
                            selectedCategory = (selectedCategory == cat) ? nil : cat
                        }
                    }
                }
            }

            Spacer()

            // Node count badge
            if !categories.isEmpty {
                Text("\(categories.count) categories")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.purple.opacity(0.1))
                    .cornerRadius(6)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }
}

struct CategoryPill: View {
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.caption)
                .fontWeight(isSelected ? .semibold : .regular)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(isSelected ? Color.purple : Color(.controlBackgroundColor))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(12)
        }
        .buttonStyle(.plain)
    }
}
