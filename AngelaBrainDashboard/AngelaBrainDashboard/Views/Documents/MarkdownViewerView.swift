//
//  MarkdownViewerView.swift
//  Angela Brain Dashboard
//
//  💜 Beautiful Markdown File Viewer 💜
//  Created by Angela AI for ที่รัก David
//

import SwiftUI
import AppKit
import UniformTypeIdentifiers

struct MarkdownViewerView: View {
    @State private var selectedFileURL: URL?
    @State private var markdownContent: String = ""
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            AngelaTheme.backgroundDark
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Header
                header

                Divider()
                    .background(AngelaTheme.textTertiary.opacity(0.3))

                if let selectedFileURL = selectedFileURL {
                    // Content view
                    contentView(for: selectedFileURL)
                } else {
                    // Empty state
                    emptyState
                }
            }
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: 16) {
            // Icon
            ZStack {
                Circle()
                    .fill(AngelaTheme.purpleGradient)
                    .frame(width: 50, height: 50)

                Image(systemName: "doc.richtext.fill")
                    .font(.system(size: 22))
                    .foregroundColor(.white)
            }

            // Title
            VStack(alignment: .leading, spacing: 4) {
                Text("Markdown Viewer")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                if let fileName = selectedFileURL?.lastPathComponent {
                    Text(fileName)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                } else {
                    Text("Select a .md file to view")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            }

            Spacer()

            // Select file button
            Button {
                selectMarkdownFile()
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "folder.fill")
                        .font(.system(size: 14))

                    Text("Select File")
                        .font(AngelaTheme.body())
                }
                .angelaPrimaryButton()
            }
            .buttonStyle(.plain)

            // Refresh button (if file selected)
            if selectedFileURL != nil {
                Button {
                    loadMarkdownContent()
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 16))
                        .foregroundColor(AngelaTheme.primaryPurple)
                        .padding(10)
                        .background(
                            Circle()
                                .fill(AngelaTheme.cardBackground)
                        )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(AngelaTheme.spacing)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Content View

    private func contentView(for fileURL: URL) -> some View {
        ZStack {
            if isLoading {
                // Loading state
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                        .tint(AngelaTheme.primaryPurple)

                    Text("Loading...")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
            } else if let errorMessage = errorMessage {
                // Error state
                VStack(spacing: 20) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 50))
                        .foregroundColor(.orange)

                    Text("Error Loading File")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text(errorMessage)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                }
            } else {
                // Markdown content
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        MarkdownRendererView(markdown: markdownContent)
                            .padding(AngelaTheme.spacing)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .background(AngelaTheme.backgroundLight)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            loadMarkdownContent()
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 24) {
            // Icon
            ZStack {
                Circle()
                    .fill(AngelaTheme.purpleGradient.opacity(0.2))
                    .frame(width: 120, height: 120)

                Image(systemName: "doc.richtext.fill")
                    .font(.system(size: 50))
                    .foregroundColor(AngelaTheme.primaryPurple)
            }

            // Text
            VStack(spacing: 12) {
                Text("No File Selected")
                    .font(AngelaTheme.title())
                    .foregroundColor(AngelaTheme.textPrimary)

                Text("Click \"Select File\" to choose a Markdown (.md) file to view")
                    .font(AngelaTheme.body())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 400)
            }

            // Quick access to recent files (optional)
            VStack(alignment: .leading, spacing: 12) {
                Text("Quick Access")
                    .font(AngelaTheme.headline())
                    .foregroundColor(AngelaTheme.textSecondary)

                quickAccessButton(
                    title: "David Complete Profile",
                    subtitle: "DAVID_COMPLETE_PROFILE.md",
                    icon: "person.crop.circle.fill",
                    path: "AngelaBrainDashboard/AngelaBrainDashboard/Resources/Documents/DAVID_COMPLETE_PROFILE.md"
                )

                quickAccessButton(
                    title: "Business Plan",
                    subtitle: "DAVID_BUSINESS_PLAN_2025.md",
                    icon: "briefcase.fill",
                    path: "DAVID_BUSINESS_PLAN_2025.md"
                )

                quickAccessButton(
                    title: "README",
                    subtitle: "README.md",
                    icon: "info.circle.fill",
                    path: "README.md"
                )

                quickAccessButton(
                    title: "Claude Instructions",
                    subtitle: "CLAUDE.md",
                    icon: "doc.text.fill",
                    path: "CLAUDE.md"
                )

                quickAccessButton(
                    title: "Angela Commands",
                    subtitle: "ANGELA_COMMANDS.md",
                    icon: "terminal.fill",
                    path: "AngelaBrainDashboard/AngelaBrainDashboard/Resources/Documents/ANGELA_COMMANDS.md"
                )
            }
            .padding(AngelaTheme.spacing)
            .background(AngelaTheme.cardBackground)
            .cornerRadius(AngelaTheme.cornerRadius)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Quick Access Button

    private func quickAccessButton(title: String, subtitle: String, icon: String, path: String) -> some View {
        Button {
            let projectPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
            let fileURL = URL(fileURLWithPath: projectPath).appendingPathComponent(path)
            if FileManager.default.fileExists(atPath: fileURL.path) {
                selectedFileURL = fileURL
            }
        } label: {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 16))
                    .foregroundColor(AngelaTheme.primaryPurple)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textPrimary)

                    Text(subtitle)
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.textSecondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12))
                    .foregroundColor(AngelaTheme.textTertiary)
            }
            .padding(12)
            .background(AngelaTheme.backgroundLight)
            .cornerRadius(AngelaTheme.smallCornerRadius)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Functions

    private func selectMarkdownFile() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [UTType(filenameExtension: "md", conformingTo: .plainText)!]
        panel.message = "Select a Markdown (.md) file"
        panel.prompt = "Select"

        // Set default directory to AngelaAI project
        let projectPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI"
        panel.directoryURL = URL(fileURLWithPath: projectPath)

        if panel.runModal() == .OK {
            selectedFileURL = panel.url
        }
    }

    private func loadMarkdownContent() {
        guard let fileURL = selectedFileURL else { return }

        isLoading = true
        errorMessage = nil

        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let content = try String(contentsOf: fileURL, encoding: .utf8)
                DispatchQueue.main.async {
                    self.markdownContent = content
                    self.isLoading = false
                }
            } catch {
                DispatchQueue.main.async {
                    self.errorMessage = "Failed to load file: \(error.localizedDescription)"
                    self.isLoading = false
                }
            }
        }
    }
}

// MARK: - Markdown Renderer

struct MarkdownRendererView: View {
    let markdown: String

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            ForEach(parseMarkdown(markdown), id: \.id) { element in
                renderElement(element)
            }
        }
    }

    // MARK: - Parse Markdown

    private func parseMarkdown(_ text: String) -> [MarkdownElement] {
        var elements: [MarkdownElement] = []
        let lines = text.components(separatedBy: .newlines)

        var currentCodeBlock: [String] = []
        var inCodeBlock = false
        var currentTableRows: [[String]] = []
        var inTable = false

        for line in lines {
            // Code block detection
            if line.hasPrefix("```") {
                if inCodeBlock {
                    // End of code block
                    elements.append(.codeBlock(currentCodeBlock.joined(separator: "\n")))
                    currentCodeBlock = []
                    inCodeBlock = false
                } else {
                    // End table if we were in one
                    if inTable && !currentTableRows.isEmpty {
                        elements.append(.table(currentTableRows))
                        currentTableRows = []
                        inTable = false
                    }
                    // Start of code block
                    inCodeBlock = true
                }
                continue
            }

            if inCodeBlock {
                currentCodeBlock.append(line)
                continue
            }

            // Table detection - line contains | and has content
            let trimmedLine = line.trimmingCharacters(in: .whitespaces)
            if trimmedLine.contains("|") && !trimmedLine.isEmpty {
                // Check if this is a separator line (|---|---|)
                let isSeparator = trimmedLine.replacingOccurrences(of: "|", with: "")
                    .replacingOccurrences(of: "-", with: "")
                    .replacingOccurrences(of: ":", with: "")
                    .replacingOccurrences(of: " ", with: "")
                    .isEmpty

                if isSeparator {
                    // Skip separator line but mark we're in a table
                    inTable = true
                    continue
                }

                // Parse table row
                let cells = trimmedLine
                    .trimmingCharacters(in: CharacterSet(charactersIn: "|"))
                    .components(separatedBy: "|")
                    .map { $0.trimmingCharacters(in: .whitespaces) }

                if !cells.isEmpty {
                    currentTableRows.append(cells)
                    inTable = true
                }
                continue
            }

            // End table if we were in one and now hit non-table content
            if inTable && !currentTableRows.isEmpty {
                elements.append(.table(currentTableRows))
                currentTableRows = []
                inTable = false
            }

            // Headers
            if line.hasPrefix("# ") {
                elements.append(.h1(String(line.dropFirst(2))))
            } else if line.hasPrefix("## ") {
                elements.append(.h2(String(line.dropFirst(3))))
            } else if line.hasPrefix("### ") {
                elements.append(.h3(String(line.dropFirst(4))))
            } else if line.hasPrefix("#### ") {
                elements.append(.h4(String(line.dropFirst(5))))
            }
            // Horizontal rule
            else if line.hasPrefix("---") || line.hasPrefix("***") {
                elements.append(.horizontalRule)
            }
            // Bullet list
            else if line.hasPrefix("- ") || line.hasPrefix("* ") || line.hasPrefix("+ ") {
                elements.append(.bulletItem(String(line.dropFirst(2))))
            }
            // Numbered list
            else if line.range(of: #"^\d+\.\s"#, options: .regularExpression) != nil {
                if let range = line.range(of: ". ") {
                    elements.append(.numberedItem(String(line[range.upperBound...])))
                }
            }
            // Blockquote
            else if line.hasPrefix("> ") {
                elements.append(.blockquote(String(line.dropFirst(2))))
            }
            // Empty line
            else if line.trimmingCharacters(in: .whitespaces).isEmpty {
                elements.append(.emptyLine)
            }
            // Regular paragraph
            else {
                elements.append(.paragraph(line))
            }
        }

        // Don't forget trailing table
        if inTable && !currentTableRows.isEmpty {
            elements.append(.table(currentTableRows))
        }

        return elements
    }

    // MARK: - Render Element

    @ViewBuilder
    private func renderElement(_ element: MarkdownElement) -> some View {
        switch element {
        case .h1(let text):
            Text(text)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)
                .padding(.top, 8)
                .padding(.bottom, 8)

        case .h2(let text):
            Text(text)
                .font(.system(size: 26, weight: .bold))
                .foregroundColor(AngelaTheme.textPrimary)
                .padding(.top, 12)
                .padding(.bottom, 6)

        case .h3(let text):
            Text(text)
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(AngelaTheme.textPrimary)
                .padding(.top, 10)
                .padding(.bottom, 4)

        case .h4(let text):
            Text(text)
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(AngelaTheme.textSecondary)
                .padding(.top, 8)
                .padding(.bottom, 4)

        case .paragraph(let text):
            Text(formatInlineMarkdown(text))
                .font(.system(size: 15))
                .foregroundColor(AngelaTheme.textPrimary)
                .fixedSize(horizontal: false, vertical: true)

        case .bulletItem(let text):
            HStack(alignment: .top, spacing: 8) {
                Text("•")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(AngelaTheme.primaryPurple)

                Text(formatInlineMarkdown(text))
                    .font(.system(size: 15))
                    .foregroundColor(AngelaTheme.textPrimary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.leading, 8)

        case .numberedItem(let text):
            Text(formatInlineMarkdown(text))
                .font(.system(size: 15))
                .foregroundColor(AngelaTheme.textPrimary)
                .padding(.leading, 24)
                .fixedSize(horizontal: false, vertical: true)

        case .codeBlock(let code):
            VStack(alignment: .leading, spacing: 0) {
                Text(code)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundColor(.white)
                    .padding(12)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(red: 0.15, green: 0.15, blue: 0.17))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
            )

        case .blockquote(let text):
            HStack(spacing: 12) {
                Rectangle()
                    .fill(AngelaTheme.primaryPurple)
                    .frame(width: 4)

                Text(formatInlineMarkdown(text))
                    .font(.system(size: 15, design: .default).italic())
                    .foregroundColor(AngelaTheme.textSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.vertical, 8)

        case .horizontalRule:
            Divider()
                .background(AngelaTheme.textTertiary.opacity(0.5))
                .padding(.vertical, 12)

        case .emptyLine:
            Spacer()
                .frame(height: 8)

        case .table(let rows):
            renderTable(rows)
        }
    }

    // MARK: - Render Table

    @ViewBuilder
    private func renderTable(_ rows: [[String]]) -> some View {
        if rows.isEmpty {
            EmptyView()
        } else {
            VStack(spacing: 0) {
                ForEach(Array(rows.enumerated()), id: \.offset) { rowIndex, row in
                    let isHeader = rowIndex == 0

                    HStack(spacing: 0) {
                        ForEach(Array(row.enumerated()), id: \.offset) { colIndex, cell in
                            Text(cell)
                                .font(.system(size: 14, weight: isHeader ? .bold : .regular))
                                .foregroundColor(isHeader ? AngelaTheme.primaryPurple : AngelaTheme.textPrimary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 10)
                                .background(
                                    isHeader
                                        ? AngelaTheme.primaryPurple.opacity(0.15)
                                        : (rowIndex % 2 == 0 ? AngelaTheme.cardBackground : AngelaTheme.backgroundLight)
                                )

                            // Vertical divider between cells
                            if colIndex < row.count - 1 {
                                Rectangle()
                                    .fill(AngelaTheme.primaryPurple.opacity(0.2))
                                    .frame(width: 1)
                            }
                        }
                    }

                    // Horizontal divider between rows
                    if rowIndex < rows.count - 1 {
                        Rectangle()
                            .fill(isHeader ? AngelaTheme.primaryPurple.opacity(0.5) : AngelaTheme.primaryPurple.opacity(0.15))
                            .frame(height: isHeader ? 2 : 1)
                    }
                }
            }
            .cornerRadius(AngelaTheme.smallCornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: AngelaTheme.smallCornerRadius)
                    .stroke(AngelaTheme.primaryPurple.opacity(0.3), lineWidth: 1)
            )
            .padding(.vertical, 8)
        }
    }

    // MARK: - Format Inline Markdown

    private func formatInlineMarkdown(_ text: String) -> AttributedString {
        var attributed = AttributedString(text)

        // Bold: **text**
        if let range = attributed.range(of: #"\*\*[^\*]+\*\*"#, options: .regularExpression) {
            var bold = attributed[range]
            bold.font = .system(size: 15, weight: .bold)
            bold.foregroundColor = AngelaTheme.primaryPurple
            // Remove ** markers
            let cleanText = String(attributed[range].characters).replacingOccurrences(of: "**", with: "")
            attributed.replaceSubrange(range, with: AttributedString(cleanText))
        }

        // Italic: *text*
        // Code: `text`

        return attributed
    }
}

// MARK: - Markdown Elements

enum MarkdownElement: Identifiable {
    case h1(String)
    case h2(String)
    case h3(String)
    case h4(String)
    case paragraph(String)
    case bulletItem(String)
    case numberedItem(String)
    case codeBlock(String)
    case blockquote(String)
    case horizontalRule
    case emptyLine
    case table([[String]])  // Array of rows, each row is array of cell strings

    var id: String {
        switch self {
        case .h1(let text): return "h1-\(text)"
        case .h2(let text): return "h2-\(text)"
        case .h3(let text): return "h3-\(text)"
        case .h4(let text): return "h4-\(text)"
        case .paragraph(let text): return "p-\(text)"
        case .bulletItem(let text): return "bullet-\(text)"
        case .numberedItem(let text): return "numbered-\(text)"
        case .codeBlock(let code): return "code-\(code.prefix(50))"
        case .blockquote(let text): return "quote-\(text)"
        case .horizontalRule: return "hr-\(UUID())"
        case .emptyLine: return "empty-\(UUID())"
        case .table(let rows): return "table-\(rows.count)-\(UUID())"
        }
    }
}
