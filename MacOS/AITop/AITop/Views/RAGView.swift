//
//  RAGView.swift
//  AITop
//
//  Read-only dashboard over Angela's domain RAG knowledge bases (rag_* on Supabase).
//  This machine does not embed documents — it only reports corpus state.
//

import SwiftUI

struct RAGView: View {
    @EnvironmentObject var apiService: APIService
    @State private var stats: AngelaRAGStats?
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 0) {
            header
            AITopDivider()
            content
        }
        .background(AITopTheme.backgroundDark)
        .task { await load() }
    }

    // MARK: - Header

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Angela RAG")
                    .font(AITopTheme.title())
                    .foregroundColor(AITopTheme.textPrimary)
                Text("Domain knowledge bases · read-only")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            }
            Spacer()
            Button {
                Task { await load() }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .foregroundColor(AITopTheme.accentOrange)
            }
            .buttonStyle(.plain)
            .disabled(isLoading)
        }
        .padding(AITopTheme.spacing)
    }

    // MARK: - Content

    @ViewBuilder
    private var content: some View {
        if let stats {
            ScrollView {
                VStack(alignment: .leading, spacing: AITopTheme.spacing) {
                    summaryRow(stats)
                    Text("Knowledge Domains")
                        .font(AITopTheme.heading())
                        .foregroundColor(AITopTheme.textPrimary)
                        .padding(.top, 4)
                    let maxChunks = max(stats.domains.map(\.chunks).max() ?? 1, 1)
                    ForEach(stats.domains) { domain in
                        DomainCard(domain: domain, maxChunks: maxChunks)
                    }
                }
                .padding(AITopTheme.spacing)
            }
        } else if let errorMessage {
            errorState(errorMessage)
        } else {
            VStack {
                ProgressView()
                Text("Loading Angela's RAG corpora…")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
                    .padding(.top, 8)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private func summaryRow(_ s: AngelaRAGStats) -> some View {
        VStack(spacing: AITopTheme.smallSpacing) {
            HStack(spacing: AITopTheme.smallSpacing) {
                MetricCard(title: "Total Chunks", value: RAGFormat.count(s.totalChunks),
                           icon: "square.stack.3d.up.fill", tint: AITopTheme.accentOrange)
                MetricCard(title: "Domains", value: "\(s.totalDomains)",
                           icon: "books.vertical.fill", tint: AITopTheme.accentCyan)
                MetricCard(title: "Sources", value: "\(s.totalSources)",
                           icon: "doc.on.doc.fill", tint: AITopTheme.accentTeal)
                MetricCard(title: "Tokens", value: RAGFormat.count(s.totalTokens),
                           icon: "number", tint: AITopTheme.info)
            }
            HStack(spacing: 6) {
                Image(systemName: "cpu.fill")
                    .font(.system(size: 11))
                    .foregroundColor(AITopTheme.success)
                Text("Embedded \(RAGFormat.count(s.totalEmbedded)) / \(RAGFormat.count(s.totalChunks)) · \(s.embedModel) · \(s.embedDims)d")
                    .font(AITopTheme.monospace())
                    .foregroundColor(AITopTheme.textSecondary)
                Spacer()
                if let updated = s.lastUpdated {
                    Text("updated \(String(updated.prefix(10)))")
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                }
            }
            .padding(.horizontal, AITopTheme.smallSpacing)
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity)
            .background(AITopTheme.surfaceBackground)
            .cornerRadius(AITopTheme.smallCornerRadius)
        }
    }

    private func errorState(_ message: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 32))
                .foregroundColor(AITopTheme.warning)
            Text("Couldn't load RAG stats")
                .font(AITopTheme.heading())
                .foregroundColor(AITopTheme.textPrimary)
            Text(message)
                .font(AITopTheme.caption())
                .foregroundColor(AITopTheme.textTertiary)
                .multilineTextAlignment(.center)
            Button("Retry") { Task { await load() } }
                .aiTopSecondaryButton()
                .padding(.top, 4)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }

    // MARK: - Load

    @MainActor
    private func load() async {
        isLoading = true
        errorMessage = nil
        do {
            stats = try await apiService.getAngelaRAGStats()
        } catch {
            if stats == nil { errorMessage = error.localizedDescription }
        }
        isLoading = false
    }
}

// MARK: - Metric card

private struct MetricCard: View {
    let title: String
    let value: String
    let icon: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 12))
                    .foregroundColor(tint)
                Text(title)
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            }
            Text(value)
                .font(.system(size: 26, weight: .bold, design: .rounded))
                .foregroundColor(AITopTheme.textPrimary)
        }
        .padding(AITopTheme.smallSpacing)
        .frame(maxWidth: .infinity, alignment: .leading)
        .aiTopCard()
    }
}

// MARK: - Domain card

private struct DomainCard: View {
    let domain: RAGDomain
    let maxChunks: Int

    private var meta: (icon: String, tint: Color) {
        RAGDomainStyle.style(for: domain.key)
    }

    private var fraction: Double {
        maxChunks > 0 ? Double(domain.chunks) / Double(maxChunks) : 0
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Title row
            HStack(spacing: 10) {
                Image(systemName: meta.icon)
                    .font(.system(size: 18))
                    .foregroundColor(meta.tint)
                    .frame(width: 26)
                Text(domain.label)
                    .font(AITopTheme.headline())
                    .foregroundColor(AITopTheme.textPrimary)
                Spacer()
                Text(RAGFormat.count(domain.chunks))
                    .font(.system(size: 20, weight: .bold, design: .rounded))
                    .foregroundColor(AITopTheme.textPrimary)
                + Text(" chunks")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textTertiary)
            }

            // Bar (relative to largest corpus)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(AITopTheme.surfaceBackground)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(meta.tint.opacity(0.85))
                        .frame(width: max(6, geo.size.width * fraction))
                }
            }
            .frame(height: 8)

            // Meta line: sources · tokens · languages
            HStack(spacing: 12) {
                Label("\(domain.sources) sources", systemImage: "doc.text")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                Label("\(RAGFormat.count(domain.tokens)) tokens", systemImage: "number")
                    .font(AITopTheme.caption())
                    .foregroundColor(AITopTheme.textSecondary)
                ForEach(domain.languages) { lang in
                    Text(lang.language.uppercased())
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(meta.tint)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(meta.tint.opacity(0.15))
                        .cornerRadius(4)
                }
                Spacer()
                if let updated = domain.updatedAt {
                    Text(String(updated.prefix(10)))
                        .font(AITopTheme.caption())
                        .foregroundColor(AITopTheme.textTertiary)
                }
            }

            // Top sources
            if !domain.topSources.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(domain.topSources) { src in
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.right")
                                .font(.system(size: 9))
                                .foregroundColor(AITopTheme.textTertiary)
                            Text(RAGFormat.prettySource(src.source))
                                .font(AITopTheme.caption())
                                .foregroundColor(AITopTheme.textSecondary)
                                .lineLimit(1)
                            Spacer()
                            Text(RAGFormat.count(src.count))
                                .font(AITopTheme.monospace())
                                .foregroundColor(AITopTheme.textTertiary)
                        }
                    }
                }
                .padding(.top, 2)
            }
        }
        .padding(AITopTheme.spacing)
        .aiTopCard()
    }
}

// MARK: - Domain visual style

private enum RAGDomainStyle {
    static func style(for key: String) -> (icon: String, tint: Color) {
        switch key {
        case "quant":        return ("chart.line.uptrend.xyaxis", AITopTheme.accentCyan)
        case "ai":           return ("brain.head.profile.fill", AITopTheme.accentOrange)
        case "bible":        return ("book.closed.fill", AITopTheme.info)
        case "wine":         return ("wineglass.fill", AITopTheme.error)
        case "photography":  return ("camera.fill", AITopTheme.accentTeal)
        default:             return ("books.vertical.fill", AITopTheme.textSecondary)
        }
    }
}

// MARK: - Formatting helpers

private enum RAGFormat {
    /// 36826 → "36.8K", 4495833 → "4.5M"
    static func count(_ n: Int) -> String {
        let d = Double(n)
        if d >= 1_000_000 { return String(format: "%.1fM", d / 1_000_000) }
        if d >= 1_000 { return String(format: "%.1fK", d / 1_000) }
        return "\(n)"
    }

    /// "cqf_2025_ju256_13_excel_xva" → "Cqf 2025 Ju256 13 Excel Xva"
    static func prettySource(_ raw: String) -> String {
        raw.split(separator: "_")
            .map { $0.prefix(1).uppercased() + $0.dropFirst() }
            .joined(separator: " ")
    }
}
