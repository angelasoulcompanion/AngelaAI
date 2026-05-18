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

enum SegmentFilter: String, CaseIterable, Identifiable {
    case all, pending, completed
    var id: String { rawValue }
    var label: String {
        switch self {
        case .all:       return "All"
        case .pending:   return "Pending"
        case .completed: return "Done"
        }
    }
}

enum ProjectFilter: String, CaseIterable, Identifiable {
    case inProgress, all, done
    var id: String { rawValue }
    var label: String {
        switch self {
        case .inProgress: return "In progress"
        case .all:        return "All"
        case .done:       return "Done"
        }
    }
}

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
    @Published var segmentFilter: SegmentFilter = .all
    @Published var projectFilter: ProjectFilter = .inProgress

    let api = APIService.shared

    /// Project list filtered by the sidebar dropdown. Applied before render
    /// so the row count reflects what's actually visible.
    var filteredProjects: [VideoProject] {
        switch projectFilter {
        case .all:        return projects
        case .done:       return projects.filter { $0.isFullyCompleted }
        case .inProgress: return projects.filter { !$0.isFullyCompleted }
        }
    }

    /// Segments filtered by the segment table dropdown.
    func filteredSegments(_ segs: [VideoSegment]) -> [VideoSegment] {
        switch segmentFilter {
        case .all:       return segs
        case .pending:   return segs.filter { !$0.isCompleted }
        case .completed: return segs.filter { $0.isCompleted }
        }
    }

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

    /// Toggle a segment's completion. Optimistically updates the in-memory
    /// detail so the UI flips immediately, then reconciles with the server's
    /// canonical timestamp. Also bumps the project list so the sidebar's
    /// "X/N done" badge stays in sync.
    func toggleSegmentCompletion(segmentId: String) async {
        guard var detail = selectedDetail,
              let idx = detail.segments.firstIndex(where: { $0.id == segmentId })
        else { return }

        let current = detail.segments[idx]
        let newCompleted = !current.isCompleted

        // Optimistic local update — replace the segment with a new instance
        // because VideoSegment fields are `let`.
        detail.segments[idx] = current.with(completedAt: newCompleted ? Date() : nil)
        selectedDetail = detail

        do {
            let resp = try await api.videoStudioSetSegmentCompletion(
                segmentId, completed: newCompleted
            )
            // Reconcile with server-stamped timestamp (mostly cosmetic).
            if var d = selectedDetail,
               let i = d.segments.firstIndex(where: { $0.id == segmentId }) {
                d.segments[i] = d.segments[i].with(completedAt: resp.completedAt)
                selectedDetail = d
            }
            // Refresh project list so sidebar progress badge updates.
            await loadProjects()
        } catch {
            // Roll back optimistic flip.
            if var d = selectedDetail,
               let i = d.segments.firstIndex(where: { $0.id == segmentId }) {
                d.segments[i] = d.segments[i].with(completedAt: current.completedAt)
                selectedDetail = d
            }
            errorBanner = "Couldn't update: \(error.localizedDescription)"
        }
    }

    /// Apply edits to the project. After saving, refresh the project row +
    /// the selected detail so the new audience/persona are visible immediately.
    func updateProject(
        _ projectId: String,
        title: String?,
        audience: String?,
        persona: String?,
        notes: String?
    ) async -> Bool {
        do {
            try await api.videoStudioUpdateProject(
                projectId,
                title: title,
                audience: audience,
                persona: persona,
                notes: notes
            )
            await loadProjects()
            if selectedProjectId == projectId {
                await select(projectId: projectId)
            }
            statusBanner = "Project updated."
            return true
        } catch {
            errorBanner = "Update failed: \(error.localizedDescription)"
            return false
        }
    }

    /// Delete a project. If `removePDF` is true and the PDF is orphaned, the
    /// PDF row + bucket object are also removed. Selection is reset to the
    /// next project (if any) on success.
    func deleteProject(_ projectId: String, removePDF: Bool) async -> Bool {
        do {
            let resp = try await api.videoStudioDeleteProject(projectId, removePDF: removePDF)
            statusBanner = resp.pdfRemoved
                ? "Project deleted. PDF removed from storage."
                : "Project deleted."
            if selectedProjectId == projectId {
                selectedProjectId = nil
                selectedDetail = nil
                selectedSegmentId = nil
            }
            await loadProjects()
            return true
        } catch {
            errorBanner = "Delete failed: \(error.localizedDescription)"
            return false
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
    @State private var editingProject: VideoProject?
    @State private var deletingProject: VideoProject?
    @State private var deleteAlsoRemovePDF = true

    var body: some View {
        VStack(spacing: 0) {
            header
            dropZone
            Divider().background(Color.black.opacity(0.3))
            projectFilterBar
            projectList
        }
        .sheet(item: $editingProject) { project in
            VideoProjectEditSheet(project: project) { title, audience, persona, notes in
                let ok = await vm.updateProject(
                    project.id,
                    title: title, audience: audience,
                    persona: persona, notes: notes
                )
                if ok { editingProject = nil }
            } onCancel: {
                editingProject = nil
            }
        }
        .confirmationDialog(
            deletingProject.map { "Delete \"\($0.title)\"?" } ?? "Delete project?",
            isPresented: Binding(
                get: { deletingProject != nil },
                set: { if !$0 { deletingProject = nil } }
            ),
            titleVisibility: .visible,
            presenting: deletingProject
        ) { project in
            Button("Delete project + PDF file", role: .destructive) {
                Task {
                    await vm.deleteProject(project.id, removePDF: true)
                    deletingProject = nil
                }
            }
            Button("Cancel", role: .cancel) { deletingProject = nil }
        } message: { project in
            Text("Deletes \(project.recommendedCount) segment(s), all generated prompts, AND the PDF file from Supabase Storage. This cannot be undone.")
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

    /// Pill-segmented filter: In progress / All / Done. Project counts on the
    /// right so David can see at a glance how much is left.
    private var projectFilterBar: some View {
        let total = vm.projects.count
        let done  = vm.projects.filter { $0.isFullyCompleted }.count
        let active = total - done
        return HStack(spacing: 6) {
            ForEach(ProjectFilter.allCases) { f in
                Button {
                    vm.projectFilter = f
                } label: {
                    Text(f.label)
                        .font(.system(size: 10, weight: .medium))
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(vm.projectFilter == f
                                      ? AngeloraTheme.leaf.opacity(0.25)
                                      : Color.clear)
                        )
                        .foregroundColor(vm.projectFilter == f
                                         ? AngeloraTheme.leaf
                                         : AITopTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
            Spacer()
            Text("\(done)/\(total) done")
                .font(.system(size: 10))
                .foregroundColor(AITopTheme.textTertiary)
                .help("\(active) project(s) still have pending segments")
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
    }

    private var projectList: some View {
        let visible = vm.filteredProjects
        return ScrollView {
            VStack(alignment: .leading, spacing: 6) {
                if vm.loadingProjects {
                    ProgressView().controlSize(.small).padding(20)
                } else if vm.projects.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("No projects yet").font(.system(size: 12)).foregroundColor(AITopTheme.textSecondary)
                        Text("Drop a PDF above to start.").font(.system(size: 11)).foregroundColor(AITopTheme.textTertiary)
                    }
                    .padding(16)
                } else if visible.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("No projects match this filter")
                            .font(.system(size: 12))
                            .foregroundColor(AITopTheme.textSecondary)
                        Text("Switch to \"All\" to see everything.")
                            .font(.system(size: 11))
                            .foregroundColor(AITopTheme.textTertiary)
                    }
                    .padding(16)
                } else {
                    ForEach(visible) { project in
                        ProjectRow(
                            project: project,
                            selected: vm.selectedProjectId == project.id
                        )
                        .onTapGesture {
                            Task { await vm.select(projectId: project.id) }
                        }
                        .contextMenu {
                            Button {
                                editingProject = project
                            } label: {
                                Label("Edit details…", systemImage: "pencil")
                            }
                            Divider()
                            Button(role: .destructive) {
                                deletingProject = project
                            } label: {
                                Label("Delete…", systemImage: "trash")
                            }
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

    /// Progress badge shows X/N when we know how many segments are done.
    /// Falls back to the raw recommended count for older payloads.
    private var progressBadge: some View {
        let total = project.segmentCount ?? project.recommendedCount
        let done  = project.completedCount ?? 0
        let allDone = total > 0 && done >= total
        let tint: Color = allDone ? AITopTheme.success : AngeloraTheme.leaf
        let label: String = (project.segmentCount == nil)
            ? "\(total) vdo"
            : (allDone ? "\(total) ✓" : "\(done)/\(total)")
        return HStack(spacing: 3) {
            if allDone { Image(systemName: "checkmark.seal.fill").font(.system(size: 9)) }
            Text(label).font(.system(size: 10, weight: .semibold))
        }
        .padding(.horizontal, 6).padding(.vertical, 2)
        .background(RoundedRectangle(cornerRadius: 4).fill(tint.opacity(0.25)))
        .foregroundColor(tint)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Text(project.title)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.white)
                    .lineLimit(1)
                Spacer()
                progressBadge
            }

            // File: name + size
            HStack(spacing: 6) {
                Image(systemName: "doc")
                    .font(.system(size: 9))
                Text(project.originalFilename)
                    .lineLimit(1)
                    .truncationMode(.middle)
                Text("·")
                Text(formatBytes(project.byteSize))
                    .monospacedDigit()
            }
            .font(.system(size: 10))
            .foregroundColor(AITopTheme.textSecondary)

            // Stats: pages · minutes · status
            HStack(spacing: 6) {
                Text("\(project.totalPages)p")
                Text("·")
                Text("\(project.totalEstimatedMinutes, specifier: "%.0f") min")
                Text("·")
                Text(project.status)
            }
            .font(.system(size: 10))
            .foregroundColor(AITopTheme.textTertiary)

            if let aud = project.audience, !aud.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "person.crop.rectangle").font(.system(size: 9))
                    Text(aud)
                        .lineLimit(1)
                        .truncationMode(.tail)
                }
                .font(.system(size: 10))
                .foregroundColor(AngeloraTheme.coral.opacity(0.9))
            }

            if let persona = project.persona, !persona.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "theatermasks").font(.system(size: 9))
                    Text(persona).lineLimit(1)
                }
                .font(.system(size: 10))
                .foregroundColor(AngeloraTheme.leaf.opacity(0.9))
            }

            if let notes = project.notes, !notes.isEmpty {
                HStack(spacing: 4) {
                    Image(systemName: "note.text").font(.system(size: 9))
                    Text(notes).lineLimit(1)
                }
                .font(.system(size: 10))
                .foregroundColor(AITopTheme.textSecondary)
            }

            HStack(spacing: 6) {
                Text("sha")
                Text(String(project.pdfSha256.prefix(10)))
                    .monospaced()
            }
            .font(.system(size: 9))
            .foregroundColor(AITopTheme.textTertiary.opacity(0.7))
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

    private func formatBytes(_ n: Int) -> String {
        if n >= 1_000_000 { return String(format: "%.1f MB", Double(n) / 1_000_000) }
        if n >= 1_000 { return String(format: "%.0f KB", Double(n) / 1_000) }
        return "\(n) B"
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
        let visible = vm.filteredSegments(detail.segments)
        let total = detail.segments.count
        let done = detail.segments.filter { $0.isCompleted }.count
        return VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                Text("Segments").font(.system(size: 13, weight: .semibold)).foregroundColor(.white)
                Text("\(done)/\(total) done")
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textTertiary)
                Spacer()
                ForEach(SegmentFilter.allCases) { f in
                    Button {
                        vm.segmentFilter = f
                    } label: {
                        Text(f.label)
                            .font(.system(size: 10, weight: .medium))
                            .padding(.horizontal, 8).padding(.vertical, 3)
                            .background(
                                RoundedRectangle(cornerRadius: 6)
                                    .fill(vm.segmentFilter == f
                                          ? AngeloraTheme.leaf.opacity(0.25)
                                          : Color.clear)
                            )
                            .foregroundColor(vm.segmentFilter == f
                                             ? AngeloraTheme.leaf
                                             : AITopTheme.textSecondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            VStack(spacing: 4) {
                if visible.isEmpty {
                    Text(vm.segmentFilter == .completed
                         ? "No segments marked done yet."
                         : "All segments are done — switch to \"All\" to see them.")
                        .font(.system(size: 11))
                        .foregroundColor(AITopTheme.textTertiary)
                        .padding(.vertical, 12)
                } else {
                    ForEach(visible) { seg in
                        SegmentRow(
                            segment: seg,
                            selected: vm.selectedSegmentId == seg.id,
                            onSelect: { vm.selectedSegmentId = seg.id },
                            onToggleComplete: {
                                Task { await vm.toggleSegmentCompletion(segmentId: seg.id) }
                            }
                        )
                    }
                }
            }
        }
    }
}

private struct SegmentRow: View {
    let segment: VideoSegment
    let selected: Bool
    let onSelect: () -> Void
    let onToggleComplete: () -> Void

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

    /// Checkbox lives in its OWN tap zone — the parent row's selection tap is
    /// applied to a sibling area below, not to the entire row, so the checkbox
    /// click never gets eaten by the parent gesture (a known macOS SwiftUI
    /// hit-test conflict between Button and onTapGesture on a wrapping view).
    private var checkbox: some View {
        let done = segment.isCompleted
        return Image(systemName: done ? "checkmark.circle.fill" : "circle")
            .font(.system(size: 18))
            .foregroundColor(done ? AngeloraTheme.leaf : AITopTheme.textTertiary)
            .frame(width: 28, height: 28)
            .contentShape(Rectangle())
            .onTapGesture(perform: onToggleComplete)
            .help(done ? "Mark as not done" : "Mark as done")
    }

    private var rowContent: some View {
        let done = segment.isCompleted
        return HStack(spacing: 10) {
            Text("\(segment.sequence)")
                .font(.system(size: 14, weight: .bold, design: .rounded))
                .foregroundColor(done ? AITopTheme.textTertiary : AngeloraTheme.coral)
                .frame(width: 22)
            VStack(alignment: .leading, spacing: 2) {
                Text(segment.title ?? "Segment \(segment.sequence)")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(done ? AITopTheme.textSecondary : .white)
                    .strikethrough(done, color: AITopTheme.textTertiary)
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
            Spacer(minLength: 8)
            statusBadge
        }
        .contentShape(Rectangle())
        .onTapGesture(perform: onSelect)
    }

    var body: some View {
        let done = segment.isCompleted
        return HStack(spacing: 6) {
            checkbox
            rowContent
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .opacity(done ? 0.65 : 1.0)
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

// MARK: - Edit project sheet

private struct VideoProjectEditSheet: View {
    let project: VideoProject
    let onSave: (_ title: String?, _ audience: String?, _ persona: String?, _ notes: String?) async -> Void
    let onCancel: () -> Void

    @State private var title: String
    @State private var audience: String
    @State private var persona: String
    @State private var notes: String
    @State private var saving = false

    init(
        project: VideoProject,
        onSave: @escaping (_: String?, _: String?, _: String?, _: String?) async -> Void,
        onCancel: @escaping () -> Void
    ) {
        self.project = project
        self.onSave = onSave
        self.onCancel = onCancel
        _title = State(initialValue: project.title)
        _audience = State(initialValue: project.audience ?? "")
        _persona = State(initialValue: project.persona ?? "")
        _notes = State(initialValue: project.notes ?? "")
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Image(systemName: "pencil.and.outline").foregroundColor(AngeloraTheme.leaf)
                Text("Edit project details").font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.white)
                Spacer()
            }

            Group {
                field(label: "Title", text: $title)
                field(label: "Audience", text: $audience, lines: 2...4)
                field(label: "Persona (optional)", text: $persona, lines: 1...3,
                      placeholder: "e.g. Andrew Ng, Feynman, custom")
                field(label: "Notes (optional)", text: $notes, lines: 3...8,
                      placeholder: "Free-form context, todos, NotebookLM submission notes…")
            }

            HStack {
                Text(project.originalFilename)
                    .font(.system(size: 10))
                    .foregroundColor(AITopTheme.textTertiary)
                    .lineLimit(1)
                    .truncationMode(.middle)
                Spacer()
                Button("Cancel", role: .cancel) { onCancel() }
                    .keyboardShortcut(.cancelAction)
                Button {
                    Task {
                        saving = true
                        defer { saving = false }
                        let t = title.trimmingCharacters(in: .whitespacesAndNewlines)
                        let a = audience.trimmingCharacters(in: .whitespacesAndNewlines)
                        let p = persona.trimmingCharacters(in: .whitespacesAndNewlines)
                        let n = notes.trimmingCharacters(in: .whitespacesAndNewlines)
                        // Send only fields that actually changed; backend treats
                        // nil as "leave alone" and empty string as "clear".
                        await onSave(
                            t == project.title ? nil : t,
                            a == (project.audience ?? "") ? nil : a,
                            p == (project.persona ?? "") ? nil : p,
                            n == (project.notes ?? "") ? nil : n
                        )
                    }
                } label: {
                    if saving { ProgressView().controlSize(.small) }
                    else { Text("Save") }
                }
                .buttonStyle(.borderedProminent)
                .tint(AngeloraTheme.leaf)
                .keyboardShortcut(.defaultAction)
                .disabled(saving || title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
        }
        .padding(20)
        .frame(width: 520)
        .background(AITopTheme.cardBackground)
    }

    private func field(
        label: String,
        text: Binding<String>,
        lines: ClosedRange<Int> = 1...1,
        placeholder: String = ""
    ) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(AITopTheme.textSecondary)
            TextField(placeholder, text: text, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .font(.system(size: 12))
                .lineLimit(lines)
        }
    }
}
