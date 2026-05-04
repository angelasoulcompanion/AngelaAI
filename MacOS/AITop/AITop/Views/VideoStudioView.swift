//
//  VideoStudioView.swift
//  AITop
//
//  Angelora Video Studio — PDF library + analyzer + prompt generator.
//
//  Layout:
//    ┌─ Project list (left) ─┬─ Selected project detail (right) ──┐
//    │  PDF drop zone        │  Header (title, filename, stats)   │
//    │  Project rows         │  Segment list                      │
//    │  ...                  │  Prompt panel + Copy button        │
//    └───────────────────────┴────────────────────────────────────┘
//
//  After the 2026-05-04 redesign, the NotebookLM submission/QA bridge
//  was removed. The user copies a prompt and runs NotebookLM manually.
//

import AppKit
import SwiftUI
import UniformTypeIdentifiers

// MARK: - Angelora palette

enum AngeloraTheme {
    static let leaf = Color(red: 0x3F / 255, green: 0xB8 / 255, blue: 0xAF / 255)
    static let coral = Color(red: 0xFF / 255, green: 0x8A / 255, blue: 0x65 / 255)
    static let ink = Color(red: 0x0B / 255, green: 0x12 / 255, blue: 0x20 / 255)
    static let surface = Color(red: 0x14 / 255, green: 0x1A / 255, blue: 0x2E / 255)
}

// MARK: - View model

@MainActor
final class VideoStudioVM: ObservableObject {
    @Published var projects: [VideoProject] = []
    @Published var selectedProjectId: String?
    @Published var selectedDetail: VideoProjectDetailEnvelope?
    @Published var selectedSegmentId: String?
    @Published var loadingProjects = false
    @Published var loadingDetail = false
    @Published var uploading = false
    @Published var statusBanner: String?
    @Published var errorBanner: String?

    let api = APIService.shared

    func loadProjects() async {
        loadingProjects = true
        defer { loadingProjects = false }
        do {
            self.projects = try await api.videoStudioListProjects()
            if selectedProjectId == nil, let first = projects.first {
                await select(projectId: first.id)
            }
        } catch {
            errorBanner = "Couldn't load projects: \(error.localizedDescription)"
        }
    }

    func select(projectId: String) async {
        selectedProjectId = projectId
        loadingDetail = true
        defer { loadingDetail = false }
        do {
            self.selectedDetail = try await api.videoStudioGetProject(projectId)
            if let first = selectedDetail?.segments.first {
                self.selectedSegmentId = first.id
            }
        } catch {
            errorBanner = "Couldn't load project: \(error.localizedDescription)"
        }
    }

    func upload(fileURL: URL, audience: String?) async {
        uploading = true
        defer { uploading = false }
        statusBanner = "Uploading & analyzing \(fileURL.lastPathComponent)…"
        do {
            let resp = try await api.videoStudioUploadPDF(
                fileURL: fileURL,
                audience: audience,
                skipLLM: false
            )
            statusBanner = "Analyzed ✓ (sha \(String(resp.pdfSha256.prefix(12)))…)"
            await loadProjects()
            await select(projectId: resp.projectId)
        } catch {
            errorBanner = "Upload failed: \(error.localizedDescription)"
        }
    }

    func refreshSelected() async {
        if let id = selectedProjectId {
            await select(projectId: id)
        }
    }
}

// MARK: - Main view

struct VideoStudioView: View {
    @StateObject private var vm = VideoStudioVM()

    var body: some View {
        HStack(spacing: 0) {
            ProjectListPane(vm: vm)
                .frame(width: 320)
                .background(AITopTheme.cardBackground)

            Divider().background(Color.black.opacity(0.4))

            ProjectDetailPane(vm: vm)
                .frame(maxWidth: .infinity)
                .background(AITopTheme.backgroundDark)
        }
        .background(AITopTheme.backgroundDark)
        .task { await vm.loadProjects() }
        .overlay(alignment: .top) {
            BannerStack(vm: vm)
                .padding(.top, 8)
        }
    }
}

// MARK: - Banner

private struct BannerStack: View {
    @ObservedObject var vm: VideoStudioVM

    var body: some View {
        VStack(spacing: 6) {
            if let s = vm.statusBanner {
                bannerLabel(text: s, tint: AngeloraTheme.leaf, dismiss: { vm.statusBanner = nil })
            }
            if let e = vm.errorBanner {
                bannerLabel(text: e, tint: AITopTheme.error, dismiss: { vm.errorBanner = nil })
            }
        }
        .padding(.horizontal, 16)
    }

    private func bannerLabel(text: String, tint: Color, dismiss: @escaping () -> Void) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "info.circle.fill")
            Text(text).font(.system(size: 12)).foregroundColor(.white)
            Spacer(minLength: 6)
            Button(action: dismiss) {
                Image(systemName: "xmark.circle.fill").foregroundColor(.white.opacity(0.8))
            }
            .buttonStyle(.plain)
        }
        .padding(8)
        .background(RoundedRectangle(cornerRadius: 8).fill(tint))
        .shadow(color: .black.opacity(0.3), radius: 6, y: 2)
    }
}

// MARK: - Left pane: project list + drop zone

private struct ProjectListPane: View {
    @ObservedObject var vm: VideoStudioVM
    @State private var droppingHover = false
    @State private var customAudience: String = "Software engineers, developers, CIOs — smart, time-poor, allergic to fluff"
    @State private var showAudienceEditor = false

    var body: some View {
        VStack(spacing: 0) {
            header
            dropZone
            Divider().background(Color.black.opacity(0.3))
            projectList
        }
    }

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "video.badge.waveform.fill")
                .font(.system(size: 18))
                .foregroundColor(AngeloraTheme.leaf)
            VStack(alignment: .leading, spacing: 2) {
                Text("Video Studio").font(.system(size: 14, weight: .bold)).foregroundColor(.white)
                Text("Angelora · NotebookLM").font(.system(size: 10)).foregroundColor(AITopTheme.textTertiary)
            }
            Spacer()
            Button {
                Task { await vm.loadProjects() }
            } label: {
                Image(systemName: "arrow.clockwise").foregroundColor(AITopTheme.textSecondary)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
    }

    private var dropZone: some View {
        VStack(spacing: 8) {
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .stroke(droppingHover ? AngeloraTheme.coral : AngeloraTheme.leaf,
                            style: StrokeStyle(lineWidth: 1.5, dash: [6, 4]))
                    .background(
                        RoundedRectangle(cornerRadius: 10)
                            .fill(droppingHover
                                  ? AngeloraTheme.coral.opacity(0.12)
                                  : AngeloraTheme.leaf.opacity(0.06))
                    )

                VStack(spacing: 6) {
                    if vm.uploading {
                        ProgressView().controlSize(.small)
                        Text("Uploading & analyzing…").font(.system(size: 12)).foregroundColor(.white)
                    } else {
                        Image(systemName: "doc.fill.badge.plus")
                            .font(.system(size: 24))
                            .foregroundColor(AngeloraTheme.leaf)
                        Text("Drop a PDF").font(.system(size: 13, weight: .medium)).foregroundColor(.white)
                        Text("or click to browse")
                            .font(.system(size: 10)).foregroundColor(AITopTheme.textTertiary)
                    }
                }
            }
            .frame(height: 100)
            .onDrop(of: [.fileURL], isTargeted: $droppingHover, perform: handleDrop)
            .onTapGesture(perform: openPanel)

            HStack {
                Button(action: { showAudienceEditor.toggle() }) {
                    HStack(spacing: 4) {
                        Image(systemName: "person.crop.rectangle")
                        Text("Audience").font(.system(size: 11))
                    }
                    .foregroundColor(AITopTheme.textSecondary)
                }
                .buttonStyle(.plain)

                Spacer()
                Text("M3 / Local").font(.system(size: 10)).foregroundColor(AITopTheme.textTertiary)
            }
            .padding(.top, 2)

            if showAudienceEditor {
                TextField("Audience description", text: $customAudience, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(size: 11))
                    .lineLimit(3...6)
            }
        }
        .padding(12)
    }

    private var projectList: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 6) {
                if vm.loadingProjects {
                    ProgressView().controlSize(.small).padding(20)
                } else if vm.projects.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("No projects yet").font(.system(size: 12)).foregroundColor(AITopTheme.textSecondary)
                        Text("Drop a PDF above to start.").font(.system(size: 11)).foregroundColor(AITopTheme.textTertiary)
                    }
                    .padding(16)
                } else {
                    ForEach(vm.projects) { project in
                        ProjectRow(
                            project: project,
                            selected: vm.selectedProjectId == project.id
                        )
                        .onTapGesture {
                            Task { await vm.select(projectId: project.id) }
                        }
                    }
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
        }
    }

    private func handleDrop(_ providers: [NSItemProvider]) -> Bool {
        guard let provider = providers.first else { return false }
        provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, _ in
            guard let data = item as? Data,
                  let url = URL(dataRepresentation: data, relativeTo: nil),
                  url.pathExtension.lowercased() == "pdf" else { return }
            Task { @MainActor in
                await vm.upload(fileURL: url, audience: customAudience.isEmpty ? nil : customAudience)
            }
        }
        return true
    }

    private func openPanel() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.pdf]
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url {
            Task {
                await vm.upload(fileURL: url, audience: customAudience.isEmpty ? nil : customAudience)
            }
        }
    }
}

private struct ProjectRow: View {
    let project: VideoProject
    let selected: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Text(project.title)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.white)
                    .lineLimit(1)
                Spacer()
                Text("\(project.recommendedCount) vdo")
                    .font(.system(size: 10))
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(RoundedRectangle(cornerRadius: 4).fill(AngeloraTheme.leaf.opacity(0.25)))
                    .foregroundColor(AngeloraTheme.leaf)
            }
            HStack(spacing: 6) {
                Text("\(project.totalPages)p")
                Text("·")
                Text("\(project.totalEstimatedMinutes, specifier: "%.0f") min")
                Text("·")
                Text(project.status)
            }
            .font(.system(size: 10))
            .foregroundColor(AITopTheme.textTertiary)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(selected ? AngeloraTheme.leaf.opacity(0.18) : Color.clear)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(selected ? AngeloraTheme.leaf : Color.clear, lineWidth: 1)
        )
    }
}

// MARK: - Right pane: project detail

private struct ProjectDetailPane: View {
    @ObservedObject var vm: VideoStudioVM

    var body: some View {
        if vm.loadingDetail {
            ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if let detail = vm.selectedDetail {
            ProjectDetailContent(vm: vm, detail: detail)
        } else {
            VStack(spacing: 8) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 36))
                    .foregroundColor(AITopTheme.textTertiary)
                Text("Select a project, or drop a PDF to start.")
                    .font(.system(size: 13))
                    .foregroundColor(AITopTheme.textSecondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

private struct ProjectDetailContent: View {
    @ObservedObject var vm: VideoStudioVM
    let detail: VideoProjectDetailEnvelope

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                projectHeader
                segmentTable
                if let segId = vm.selectedSegmentId,
                   let seg = detail.segments.first(where: { $0.id == segId }) {
                    SegmentDetailPanel(segment: seg)
                }
            }
            .padding(20)
        }
    }

    private var projectHeader: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline) {
                Text(detail.project.title)
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(.white)
                Spacer()
                Text(detail.project.status.uppercased())
                    .font(.system(size: 10, weight: .semibold))
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(RoundedRectangle(cornerRadius: 4).fill(AngeloraTheme.coral.opacity(0.3)))
                    .foregroundColor(AngeloraTheme.coral)
            }
            HStack(spacing: 8) {
                Image(systemName: "doc.fill").foregroundColor(AITopTheme.textTertiary)
                Text(detail.project.originalFilename)
                    .font(.system(size: 11))
                    .foregroundColor(AITopTheme.textSecondary)
                Text("·").foregroundColor(AITopTheme.textTertiary)
                Text(byteSize(detail.project.byteSize))
                    .font(.system(size: 11))
                    .foregroundColor(AITopTheme.textTertiary)
                Text("·").foregroundColor(AITopTheme.textTertiary)
                Text("sha \(String(detail.project.pdfSha256.prefix(10)))…")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(AITopTheme.textTertiary)
            }
            HStack(spacing: 16) {
                stat(label: "Pages", value: "\(detail.project.totalPages)")
                stat(label: "Total speech", value: String(format: "%.1f min", detail.project.totalEstimatedMinutes))
                stat(label: "Videos", value: "\(detail.project.recommendedCount)")
            }
        }
    }

    private func byteSize(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1f MB", Double(n) / 1_000_000) }
        if n >= 1_000 { return String(format: "%.0f KB", Double(n) / 1_000) }
        return "\(n) B"
    }

    private func stat(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label.uppercased())
                .font(.system(size: 9, weight: .semibold))
                .foregroundColor(AITopTheme.textTertiary)
            Text(value)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(AngeloraTheme.leaf)
        }
    }

    private var segmentTable: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Segments").font(.system(size: 13, weight: .semibold)).foregroundColor(.white)
                Spacer()
            }
            VStack(spacing: 4) {
                ForEach(detail.segments) { seg in
                    SegmentRow(
                        segment: seg,
                        selected: vm.selectedSegmentId == seg.id
                    )
                    .onTapGesture { vm.selectedSegmentId = seg.id }
                }
            }
        }
    }
}

private struct SegmentRow: View {
    let segment: VideoSegment
    let selected: Bool

    var statusBadge: some View {
        let (label, color): (String, Color) = {
            switch segment.status {
            case "prompt_ready": return ("PROMPT", AngeloraTheme.leaf)
            case "analyzed":     return ("ANALYZED", AITopTheme.info)
            default:             return (segment.status.uppercased(), AITopTheme.textTertiary)
            }
        }()
        return Text(label)
            .font(.system(size: 9, weight: .bold))
            .padding(.horizontal, 6).padding(.vertical, 2)
            .background(RoundedRectangle(cornerRadius: 4).fill(color.opacity(0.25)))
            .foregroundColor(color)
    }

    var body: some View {
        HStack(spacing: 10) {
            Text("\(segment.sequence)")
                .font(.system(size: 14, weight: .bold, design: .rounded))
                .foregroundColor(AngeloraTheme.coral)
                .frame(width: 26)
            VStack(alignment: .leading, spacing: 2) {
                Text(segment.title ?? "Segment \(segment.sequence)")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white)
                    .lineLimit(1)
                HStack(spacing: 6) {
                    Text("pp. \(segment.pageRange)")
                    Text("·")
                    Text(String(format: "%.1f min", segment.estMinutes))
                    Text("·")
                    Text("load \(segment.cognitiveLoad, specifier: "%.1f")")
                }
                .font(.system(size: 10))
                .foregroundColor(AITopTheme.textTertiary)
            }
            Spacer()
            statusBadge
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(selected ? AngeloraTheme.leaf.opacity(0.12) : AITopTheme.cardBackground.opacity(0.6))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(selected ? AngeloraTheme.leaf : Color.clear, lineWidth: 1)
        )
    }
}

// MARK: - Segment detail / prompt panel

private struct SegmentDetailPanel: View {
    let segment: VideoSegment
    @State private var copyConfirm = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Video \(segment.sequence): \(segment.title ?? "")")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)
                Spacer()
                if let lp = segment.latestPrompt {
                    Text("\(lp.templateName) · v\(lp.version)")
                        .font(.system(size: 10))
                        .foregroundColor(AITopTheme.textTertiary)
                }
            }

            if let lp = segment.latestPrompt {
                promptHeader(lp)
                promptBody(lp)
            } else {
                Text("No prompt generated for this segment yet.")
                    .font(.system(size: 12))
                    .foregroundColor(AITopTheme.textTertiary)
            }
        }
        .padding(14)
        .background(RoundedRectangle(cornerRadius: 12).fill(AITopTheme.cardBackground))
    }

    private func promptHeader(_ lp: VideoPromptVersion) -> some View {
        HStack(spacing: 8) {
            Label("Format: \(lp.notebooklmFormat)", systemImage: "rectangle.on.rectangle")
                .labelStyle(.titleAndIcon)
            Text("·")
            Label("Style: \(lp.visualStyle)", systemImage: "paintbrush")
                .labelStyle(.titleAndIcon)
            Text("·")
            Text("\(lp.targetMinutes) min target")
            Spacer()
            Button {
                let pasteboard = NSPasteboard.general
                pasteboard.clearContents()
                pasteboard.setString(lp.filledPrompt, forType: .string)
                copyConfirm = true
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) { copyConfirm = false }
            } label: {
                Label(copyConfirm ? "Copied!" : "Copy prompt",
                      systemImage: copyConfirm ? "checkmark" : "doc.on.doc")
            }
            .buttonStyle(.borderedProminent)
            .tint(copyConfirm ? AITopTheme.success : AngeloraTheme.leaf)
        }
        .font(.system(size: 11))
        .foregroundColor(AITopTheme.textSecondary)
    }

    private func promptBody(_ lp: VideoPromptVersion) -> some View {
        ScrollView {
            Text(lp.filledPrompt)
                .font(.system(size: 11, design: .monospaced))
                .foregroundColor(.white)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 8).fill(AITopTheme.surfaceBackground))
                .textSelection(.enabled)
        }
        .frame(maxHeight: 360)
    }
}
