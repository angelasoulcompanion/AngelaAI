//
//  ChatPDFExporter.swift
//  AITop
//
//  Renders chat history to a multi-page PDF via NSTextView + NSPrintOperation.
//  Thai text renders correctly through NSFont fallback chain.
//

import AppKit
import Foundation

enum ChatPDFExporter {

    /// Multi-page PDF export. Returns the URL that was written.
    @discardableResult
    static func export(
        messages: [ChatMessage],
        model: String,
        systemPrompt: String,
        to url: URL
    ) throws -> URL {
        let attributed = buildAttributedString(
            messages: messages,
            model: model,
            systemPrompt: systemPrompt
        )

        let pageSize = NSSize(width: 612, height: 792)  // US Letter 8.5" × 11"
        let margin: CGFloat = 54                        // 0.75"
        let contentWidth = pageSize.width - margin * 2

        // Lay out text off-screen to discover its total height.
        let container = NSTextContainer(size: NSSize(width: contentWidth,
                                                     height: .greatestFiniteMagnitude))
        container.widthTracksTextView = false
        let layout = NSLayoutManager()
        layout.addTextContainer(container)
        let storage = NSTextStorage(attributedString: attributed)
        storage.addLayoutManager(layout)
        layout.ensureLayout(for: container)
        let contentHeight = ceil(layout.usedRect(for: container).height) + 24

        let textView = NSTextView(frame: NSRect(x: 0, y: 0, width: contentWidth, height: contentHeight))
        textView.textStorage?.setAttributedString(attributed)
        textView.isEditable = false
        textView.isSelectable = false
        textView.drawsBackground = true
        textView.backgroundColor = .white

        let printInfo = NSPrintInfo()
        printInfo.paperSize = pageSize
        printInfo.topMargin = margin
        printInfo.bottomMargin = margin
        printInfo.leftMargin = margin
        printInfo.rightMargin = margin
        printInfo.horizontalPagination = .fit
        printInfo.verticalPagination = .automatic
        printInfo.jobDisposition = .save
        printInfo.dictionary()[NSPrintInfo.AttributeKey.jobSavingURL] = url as NSURL

        let op = NSPrintOperation(view: textView, printInfo: printInfo)
        op.showsPrintPanel = false
        op.showsProgressPanel = false
        if !op.run() {
            throw NSError(
                domain: "ChatPDFExporter",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "NSPrintOperation failed to produce PDF"]
            )
        }
        return url
    }

    // MARK: - Attributed string builder

    private static func buildAttributedString(
        messages: [ChatMessage],
        model: String,
        systemPrompt: String
    ) -> NSAttributedString {
        let out = NSMutableAttributedString()

        let titleFont = NSFont.boldSystemFont(ofSize: 18)
        let headerFont = NSFont.boldSystemFont(ofSize: 12)
        let bodyFont = NSFont.systemFont(ofSize: 11)
        let monoFont = NSFont.monospacedSystemFont(ofSize: 10, weight: .regular)

        let gray = NSColor(calibratedWhite: 0.35, alpha: 1.0)
        let userColor = NSColor(calibratedRed: 0.85, green: 0.45, blue: 0.0, alpha: 1.0)
        let assistantColor = NSColor(calibratedRed: 0.20, green: 0.35, blue: 0.85, alpha: 1.0)

        let paragraph = NSMutableParagraphStyle()
        paragraph.lineSpacing = 2
        paragraph.paragraphSpacing = 4

        // Title
        out.append(NSAttributedString(
            string: "AITop — Chat Export\n",
            attributes: [.font: titleFont, .paragraphStyle: paragraph]
        ))

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        out.append(NSAttributedString(
            string: "Model: \(model)    Exported: \(formatter.string(from: Date()))\n",
            attributes: [.font: monoFont, .foregroundColor: gray, .paragraphStyle: paragraph]
        ))
        out.append(NSAttributedString(
            string: "Messages: \(messages.count)\n\n",
            attributes: [.font: monoFont, .foregroundColor: gray, .paragraphStyle: paragraph]
        ))

        if !systemPrompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            out.append(NSAttributedString(
                string: "System Prompt\n",
                attributes: [.font: headerFont, .paragraphStyle: paragraph]
            ))
            out.append(NSAttributedString(
                string: systemPrompt + "\n\n",
                attributes: [.font: bodyFont, .foregroundColor: gray, .paragraphStyle: paragraph]
            ))
        }

        // Divider line
        let divider = NSAttributedString(
            string: String(repeating: "─", count: 60) + "\n\n",
            attributes: [.font: monoFont, .foregroundColor: gray]
        )
        out.append(divider)

        for (idx, msg) in messages.enumerated() {
            let isUser = msg.role == "user"
            let label = isUser ? "You" : (msg.model ?? model)
            let color = isUser ? userColor : assistantColor

            out.append(NSAttributedString(
                string: "▸ \(label)\n",
                attributes: [.font: headerFont, .foregroundColor: color, .paragraphStyle: paragraph]
            ))
            out.append(NSAttributedString(
                string: msg.content + "\n",
                attributes: [.font: bodyFont, .paragraphStyle: paragraph]
            ))
            if idx < messages.count - 1 {
                out.append(NSAttributedString(string: "\n", attributes: [.font: bodyFont]))
            }
        }

        return out
    }

    // MARK: - Save panel helper

    /// Prompt the user for a location, then export. Returns saved URL or nil if cancelled.
    @discardableResult
    static func promptAndExport(
        messages: [ChatMessage],
        model: String,
        systemPrompt: String
    ) throws -> URL? {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.pdf]
        panel.canCreateDirectories = true
        panel.nameFieldStringValue = defaultFilename(model: model)
        panel.title = "Export Chat to PDF"

        let response = panel.runModal()
        guard response == .OK, let url = panel.url else { return nil }

        return try export(messages: messages, model: model, systemPrompt: systemPrompt, to: url)
    }

    private static func defaultFilename(model: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        let safeModel = model.replacingOccurrences(of: ":", with: "_")
        return "aitop_chat_\(safeModel)_\(formatter.string(from: Date())).pdf"
    }
}
