//
//  ResumeView.swift
//  Angela Brain Dashboard
//
//  David's Resume/CV Viewer
//  Created: 2026-01-08
//

import SwiftUI
import PDFKit

struct ResumeView: View {
    @State private var pdfDocument: PDFDocument?
    @State private var currentPage = 0
    @State private var totalPages = 1
    @State private var zoomScale: CGFloat = 1.0

    // PDF file path - embedded in app bundle
    private let pdfFileName = "DavidResume"

    var body: some View {
        VStack(spacing: 0) {
            // Header
            header

            // PDF Viewer
            if let document = pdfDocument {
                PDFViewerRepresentable(document: document, zoomScale: $zoomScale)
                    .background(AngelaTheme.backgroundLight)
            } else {
                // Loading or error state
                VStack(spacing: 20) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Loading Resume...")
                        .font(AngelaTheme.body())
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(AngelaTheme.backgroundDark)
            }

            // Footer with controls
            footer
        }
        .onAppear {
            loadPDF()
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "doc.person.fill")
                        .font(.system(size: 20))
                        .foregroundColor(AngelaTheme.primaryPurple)

                    Text("David's Resume")
                        .font(AngelaTheme.title())
                        .foregroundColor(AngelaTheme.textPrimary)
                }

                Text("IT & Digital Technology Expert")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Quick info badges
            HStack(spacing: 12) {
                InfoBadge(icon: "briefcase.fill", text: "30+ Years", color: .blue)
                InfoBadge(icon: "building.2.fill", text: "CEO/CFO/VP", color: .green)
                InfoBadge(icon: "cpu.fill", text: "AI/ML Expert", color: .purple)
            }

            Spacer()

            // Open in Preview button
            Button {
                openInPreview()
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.forward.app")
                        .font(.system(size: 12))
                    Text("Open in Preview")
                        .font(AngelaTheme.caption())
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(AngelaTheme.primaryPurple.opacity(0.2))
                .foregroundColor(AngelaTheme.primaryPurple)
                .cornerRadius(8)
            }
            .buttonStyle(.plain)
        }
        .padding(AngelaTheme.largeSpacing)
        .background(AngelaTheme.backgroundDark)
    }

    // MARK: - Footer

    private var footer: some View {
        HStack {
            // Page info
            if let doc = pdfDocument {
                Text("Page \(currentPage + 1) of \(doc.pageCount)")
                    .font(AngelaTheme.caption())
                    .foregroundColor(AngelaTheme.textSecondary)
            }

            Spacer()

            // Zoom controls
            HStack(spacing: 12) {
                Button {
                    zoomScale = max(0.5, zoomScale - 0.25)
                } label: {
                    Image(systemName: "minus.magnifyingglass")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .buttonStyle(.plain)

                Text("\(Int(zoomScale * 100))%")
                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                    .foregroundColor(AngelaTheme.textSecondary)
                    .frame(width: 50)

                Button {
                    zoomScale = min(3.0, zoomScale + 0.25)
                } label: {
                    Image(systemName: "plus.magnifyingglass")
                        .font(.system(size: 14))
                        .foregroundColor(AngelaTheme.textSecondary)
                }
                .buttonStyle(.plain)

                Divider()
                    .frame(height: 20)

                Button {
                    zoomScale = 1.0
                } label: {
                    Text("Fit")
                        .font(AngelaTheme.caption())
                        .foregroundColor(AngelaTheme.primaryPurple)
                }
                .buttonStyle(.plain)
            }

            Spacer()

            // File info
            Text("DavidResume.pdf")
                .font(.system(size: 11, design: .monospaced))
                .foregroundColor(AngelaTheme.textTertiary)
        }
        .padding(.horizontal, AngelaTheme.largeSpacing)
        .padding(.vertical, 12)
        .background(AngelaTheme.cardBackground)
    }

    // MARK: - Functions

    private func loadPDF() {
        // Try to load from bundle first
        if let url = Bundle.main.url(forResource: pdfFileName, withExtension: "pdf") {
            pdfDocument = PDFDocument(url: url)
        } else {
            // Fallback to outputs folder
            let outputsPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/outputs/David Samanyaporn - IT & Digital Technology Expert.pdf"
            if let doc = PDFDocument(url: URL(fileURLWithPath: outputsPath)) {
                pdfDocument = doc
            }
        }

        if let doc = pdfDocument {
            totalPages = doc.pageCount
        }
    }

    private func openInPreview() {
        let outputsPath = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/outputs/David Samanyaporn - IT & Digital Technology Expert.pdf"
        NSWorkspace.shared.open(URL(fileURLWithPath: outputsPath))
    }
}

// MARK: - Info Badge

struct InfoBadge: View {
    let icon: String
    let text: String
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 12))
            Text(text)
                .font(.system(size: 11, weight: .medium))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(color.opacity(0.15))
        .foregroundColor(color)
        .cornerRadius(6)
    }
}

// MARK: - PDF Viewer Representable

struct PDFViewerRepresentable: NSViewRepresentable {
    let document: PDFDocument
    @Binding var zoomScale: CGFloat

    func makeNSView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.document = document
        pdfView.autoScales = true
        pdfView.displayMode = .singlePageContinuous
        pdfView.displayDirection = .vertical
        pdfView.backgroundColor = NSColor(AngelaTheme.backgroundLight)
        return pdfView
    }

    func updateNSView(_ pdfView: PDFView, context: Context) {
        pdfView.scaleFactor = zoomScale
    }
}

// MARK: - Preview

#Preview {
    ResumeView()
        .frame(width: 1000, height: 800)
        .preferredColorScheme(.dark)
}
