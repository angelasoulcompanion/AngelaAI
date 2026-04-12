//
//  DatasetsView.swift
//  AITop — Fine-Tune Studio: Dataset Management
//

import SwiftUI
import UniformTypeIdentifiers

struct DatasetsView: View {
    @EnvironmentObject var apiService: APIService

    @State private var datasets: [DatasetFile] = []
    @State private var batches: [ExportBatch] = []
    @State private var isUploading = false
    @State private var isExporting = false
    @State private var showExportSettings = false
    @State private var exportMinQuality = 7.0
    @State private var exportResult: ExportDatasetResponse?
    @State private var selectedDataset: DatasetFile?
    @State private var preview: DatasetPreviewResponse?
    @State private var validation: DatasetValidationResponse?
    @State private var error: String?
    @State private var showExportPreview = false
    @State private var exportPreviewData: ExportPreviewResponse?
    @State private var previewPage = 0
    @State private var currentPreviewPath = ""

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack {
                    Text("Datasets")
                        .font(.title2.bold())
                        .foregroundColor(.white)
                    Spacer()

                    // Export from DB button + quality picker
                    HStack(spacing: 8) {
                        // Quality picker
                        HStack(spacing: 4) {
                            Text("Min Q:")
                                .font(.caption)
                                .foregroundColor(Color(hex: "9CA3AF"))
                            Picker("", selection: $exportMinQuality) {
                                Text("4.0 (All)").tag(4.0)
                                Text("5.0").tag(5.0)
                                Text("6.0").tag(6.0)
                                Text("7.0 ★").tag(7.0)
                                Text("8.0").tag(8.0)
                                Text("9.0").tag(9.0)
                            }
                            .frame(width: 100)
                        }

                        Button {
                            Task { await exportFromDB() }
                        } label: {
                            HStack(spacing: 4) {
                                if isExporting {
                                    ProgressView().scaleEffect(0.6).tint(.white)
                                } else {
                                    Image(systemName: "arrow.down.doc.fill")
                                }
                                Text(isExporting ? "Exporting..." : "Export from DB")
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color(hex: "00D4FF"))
                            .foregroundColor(.white)
                            .cornerRadius(8)
                        }
                        .buttonStyle(.plain)
                        .disabled(isExporting)
                    }

                    // Upload button
                    Button {
                        browseAndUpload()
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "plus.circle.fill")
                            Text("Upload")
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color(hex: "FF6B00"))
                        .foregroundColor(.white)
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                    .disabled(isUploading)
                }

                if isUploading {
                    HStack {
                        ProgressView().scaleEffect(0.8)
                        Text("Uploading...")
                            .font(.caption)
                            .foregroundColor(Color(hex: "9CA3AF"))
                    }
                }

                // Export Result Card
                if let result = exportResult {
                    exportResultCard(result)
                }

                // Export Batch History
                if !batches.isEmpty {
                    batchHistorySection
                }

                // Dataset List
                if datasets.isEmpty && batches.isEmpty {
                    emptyState
                } else {
                    ForEach(datasets) { ds in
                        datasetRow(ds)
                    }
                }

                // Preview Panel
                if let preview {
                    previewPanel(preview)
                }

                // Validation Panel
                if let validation {
                    validationPanel(validation)
                }
            }
            .padding(24)
        }
        .background(Color(hex: "0A0A0F"))
        .onAppear { loadDatasets() }
        .sheet(isPresented: $showExportPreview) {
            exportPreviewSheet
        }
    }

    // MARK: - Export Preview Sheet

    private var exportPreviewSheet: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Dataset Preview")
                    .font(.title2.bold())
                    .foregroundColor(.white)
                if let data = exportPreviewData {
                    Text("(\(data.showing) of \(data.total) pairs)")
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                }
                Spacer()
                Button { showExportPreview = false } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title3)
                        .foregroundColor(Color(hex: "9CA3AF"))
                }
                .buttonStyle(.plain)
            }
            .padding(16)

            Divider().background(Color(hex: "2A2A4A"))

            // Content
            if let data = exportPreviewData {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(Array(data.rows.enumerated()), id: \.offset) { idx, row in
                            exportPreviewCard(row, index: data.offset + idx + 1)
                        }
                    }
                    .padding(16)
                }

                // Pagination
                HStack {
                    Button("Previous") {
                        if previewPage > 0 {
                            previewPage -= 1
                            Task { await loadExportPreview(path: currentPreviewPath, offset: previewPage * 20) }
                        }
                    }
                    .disabled(previewPage == 0)

                    Spacer()
                    Text("Page \(previewPage + 1) of \(max(1, (data.total + 19) / 20))")
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                    Spacer()

                    Button("Next") {
                        if (previewPage + 1) * 20 < data.total {
                            previewPage += 1
                            Task { await loadExportPreview(path: currentPreviewPath, offset: previewPage * 20) }
                        }
                    }
                    .disabled((previewPage + 1) * 20 >= data.total)
                }
                .padding(16)
            } else {
                ProgressView("Loading preview...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .frame(minWidth: 800, minHeight: 600)
        .background(Color(hex: "0A0A0F"))
    }

    private func exportPreviewCard(_ row: ExportPreviewRow, index: Int) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header with quality badge
            HStack {
                Text("#\(index)")
                    .font(.system(.caption, design: .monospaced).bold())
                    .foregroundColor(Color(hex: "6B7280"))

                if let meta = row.metadata {
                    if let q = meta.qualityScore {
                        Text(String(format: "Q:%.1f", q))
                            .font(.system(size: 10).bold())
                            .padding(.horizontal, 5)
                            .padding(.vertical, 2)
                            .background(qualityColor(q).opacity(0.3))
                            .foregroundColor(qualityColor(q))
                            .cornerRadius(4)
                    }
                    if let source = meta.source {
                        Text(source)
                            .font(.system(size: 9))
                            .padding(.horizontal, 4)
                            .padding(.vertical, 1)
                            .background(Color.blue.opacity(0.2))
                            .foregroundColor(.blue)
                            .cornerRadius(3)
                    }
                    if let topic = meta.topic, !topic.isEmpty {
                        Text(topic)
                            .font(.system(size: 9))
                            .foregroundColor(Color(hex: "6B7280"))
                    }
                }
                Spacer()
            }

            // User message
            if let msgs = row.messages {
                if let userMsg = msgs.first(where: { $0.role == "user" }) {
                    HStack(alignment: .top, spacing: 8) {
                        Text("David")
                            .font(.system(size: 10).bold())
                            .foregroundColor(Color(hex: "00D4FF"))
                            .frame(width: 50, alignment: .trailing)
                        Text(userMsg.content)
                            .font(.system(size: 12))
                            .foregroundColor(Color(hex: "D1D5DB"))
                            .lineLimit(3)
                    }
                }

                // Angela response
                if let angelaMsg = msgs.first(where: { $0.role == "assistant" }) {
                    HStack(alignment: .top, spacing: 8) {
                        Text("Angela")
                            .font(.system(size: 10).bold())
                            .foregroundColor(Color(hex: "FF6B00"))
                            .frame(width: 50, alignment: .trailing)
                        Text(angelaMsg.content)
                            .font(.system(size: 12))
                            .foregroundColor(Color(hex: "D1D5DB"))
                            .lineLimit(5)
                    }
                }
            }
        }
        .padding(12)
        .background(Color(hex: "12121F"))
        .cornerRadius(8)
    }

    private func qualityColor(_ q: Double) -> Color {
        if q >= 8 { return .green }
        if q >= 6 { return .orange }
        return .red
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "doc.text")
                .font(.system(size: 40))
                .foregroundColor(Color(hex: "4A4A6A"))
            Text("No datasets uploaded yet")
                .foregroundColor(Color(hex: "9CA3AF"))
            Text("Upload JSONL, JSON, CSV, or Parquet files")
                .font(.caption)
                .foregroundColor(Color(hex: "6B7280"))
        }
        .frame(maxWidth: .infinity)
        .padding(40)
    }

    // MARK: - Dataset Row

    private func datasetRow(_ ds: DatasetFile) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        Text(ds.filename)
                            .font(.system(.body, design: .monospaced).bold())
                            .foregroundColor(.white)

                        if let type = ds.datasetType {
                            Text(type.uppercased())
                                .font(.system(size: 9).bold())
                                .padding(.horizontal, 5)
                                .padding(.vertical, 2)
                                .background(typeColor(type).opacity(0.3))
                                .foregroundColor(typeColor(type))
                                .cornerRadius(4)
                        }

                        if ds.isValidated == true {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                                .font(.caption)
                        }
                    }

                    HStack(spacing: 12) {
                        if let lines = ds.lines ?? ds.totalExamples {
                            HStack(spacing: 3) {
                                Image(systemName: "doc.text")
                                    .font(.system(size: 9))
                                Text("\(lines) rows")
                                    .font(.system(.caption, design: .monospaced).bold())
                            }
                            .foregroundColor(Color(hex: "00D4FF"))
                        }
                        if let size = ds.sizeBytes {
                            Text(formatBytes(size))
                                .font(.caption)
                                .foregroundColor(Color(hex: "9CA3AF"))
                        }
                    }
                }

                Spacer()

                // Action buttons
                HStack(spacing: 8) {
                    Button("Preview") {
                        Task { await loadPreview(ds) }
                    }
                    .buttonStyle(.plain)
                    .font(.caption)
                    .foregroundColor(Color(hex: "00D4FF"))

                    Button("Validate") {
                        Task { await validateDs(ds) }
                    }
                    .buttonStyle(.plain)
                    .font(.caption)
                    .foregroundColor(Color(hex: "FF6B00"))
                }
            }
            .padding(12)
            .background(selectedDataset?.filename == ds.filename ? Color(hex: "1A1A2E") : Color(hex: "12121F"))
            .cornerRadius(8)
        }
        .onTapGesture {
            selectedDataset = ds
        }
    }

    // MARK: - Preview Panel

    private func previewPanel(_ p: DatasetPreviewResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Preview")
                    .font(.headline.bold())
                    .foregroundColor(.white)
                Text("(\(p.showing) of \(p.totalRows) rows)")
                    .font(.caption)
                    .foregroundColor(Color(hex: "9CA3AF"))
                Spacer()
                Button { preview = nil } label: {
                    Image(systemName: "xmark.circle")
                }
                .buttonStyle(.plain)
                .foregroundColor(Color(hex: "9CA3AF"))
            }

            // Column headers
            HStack {
                ForEach(p.columns.prefix(5), id: \.self) { col in
                    Text(col)
                        .font(.caption.bold())
                        .foregroundColor(Color(hex: "FF6B00"))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding(8)
            .background(Color(hex: "1A1A2E"))
            .cornerRadius(4)

            // Rows
            ForEach(Array(p.rows.prefix(10).enumerated()), id: \.offset) { _, row in
                HStack {
                    ForEach(p.columns.prefix(5), id: \.self) { col in
                        Text(stringValue(row[col]))
                            .font(.caption)
                            .foregroundColor(Color(hex: "D1D5DB"))
                            .lineLimit(2)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
            }
        }
        .padding(16)
        .background(Color(hex: "12121F"))
        .cornerRadius(12)
    }

    // MARK: - Validation Panel

    private func validationPanel(_ v: DatasetValidationResponse) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: v.isValid ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(v.isValid ? .green : .red)
                Text(v.isValid ? "Dataset is valid" : "Validation failed")
                    .font(.headline.bold())
                    .foregroundColor(.white)
                Spacer()
                Button { validation = nil } label: {
                    Image(systemName: "xmark.circle")
                }
                .buttonStyle(.plain)
                .foregroundColor(Color(hex: "9CA3AF"))
            }

            Text("\(v.totalExamples) examples | Type: \(v.datasetType.uppercased())")
                .font(.caption)
                .foregroundColor(Color(hex: "9CA3AF"))

            ForEach(v.errors, id: \.self) { err in
                HStack(spacing: 4) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.red)
                        .font(.caption)
                    Text(err)
                        .font(.caption)
                        .foregroundColor(.red)
                }
            }

            ForEach(v.warnings, id: \.self) { warn in
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.caption)
                    Text(warn)
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }
        }
        .padding(16)
        .background(Color(hex: "12121F"))
        .cornerRadius(12)
    }

    // MARK: - Batch History

    private var batchHistorySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("EXPORT HISTORY")
                .font(.caption.bold())
                .foregroundColor(Color(hex: "9CA3AF"))

            ForEach(batches) { batch in
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 6) {
                            Image(systemName: "doc.text.fill")
                                .foregroundColor(Color(hex: "00D4FF"))
                            Text(batch.batchName)
                                .font(.system(.body, design: .monospaced).bold())
                                .foregroundColor(.white)
                                .lineLimit(1)
                            Text(batch.exportType.uppercased())
                                .font(.system(size: 9).bold())
                                .padding(.horizontal, 4)
                                .padding(.vertical, 1)
                                .background(Color.green.opacity(0.3))
                                .foregroundColor(.green)
                                .cornerRadius(3)
                            if let jobs = batch.usedInJobs, !jobs.isEmpty {
                                Text("TRAINED")
                                    .font(.system(size: 8).bold())
                                    .padding(.horizontal, 4)
                                    .padding(.vertical, 1)
                                    .background(Color(hex: "FF6B00").opacity(0.3))
                                    .foregroundColor(Color(hex: "FF6B00"))
                                    .cornerRadius(3)
                            }
                        }
                        HStack(spacing: 12) {
                            HStack(spacing: 3) {
                                Image(systemName: "doc.text")
                                    .font(.system(size: 9))
                                Text("\(batch.totalPairs) rows")
                                    .font(.system(.caption, design: .monospaced).bold())
                            }
                            .foregroundColor(Color(hex: "00D4FF"))
                            if let q = batch.avgQuality {
                                Text(String(format: "Q:%.1f", q))
                                    .font(.caption)
                                    .foregroundColor(Color(hex: "9CA3AF"))
                            }
                            if let size = batch.fileSizeKb {
                                Text(String(format: "%.0f KB", size))
                                    .font(.caption)
                                    .foregroundColor(Color(hex: "6B7280"))
                            }
                            if let sources = batch.sourceDistribution {
                                ForEach(Array(sources.keys.sorted()), id: \.self) { key in
                                    Text("\(key.prefix(4)): \(sources[key] ?? 0)")
                                        .font(.system(size: 9))
                                        .foregroundColor(Color(hex: "6B7280"))
                                }
                            }
                            if let date = batch.createdAt {
                                Text(String(date.prefix(16)))
                                    .font(.system(size: 9))
                                    .foregroundColor(Color(hex: "6B7280"))
                            }
                        }
                    }
                    Spacer()

                    HStack(spacing: 12) {
                        // Preview button
                        if let previewPath = batch.previewPath {
                            Button {
                                previewPage = 0
                                Task { await loadExportPreview(path: previewPath, offset: 0) }
                                showExportPreview = true
                            } label: {
                                HStack(spacing: 3) {
                                    Image(systemName: "eye")
                                    Text("Preview")
                                }
                            }
                            .buttonStyle(.plain)
                            .font(.caption.bold())
                            .foregroundColor(Color(hex: "00D4FF"))
                        }

                        // Open in Finder
                        if let path = batch.outputPath {
                            Button {
                                NSWorkspace.shared.open(URL(fileURLWithPath: path).deletingLastPathComponent())
                            } label: {
                                HStack(spacing: 3) {
                                    Image(systemName: "folder")
                                    Text("Finder")
                                }
                            }
                            .buttonStyle(.plain)
                            .font(.caption.bold())
                            .foregroundColor(Color(hex: "9CA3AF"))
                        }
                    }
                }
                .padding(12)
                .background(Color(hex: "12121F"))
                .cornerRadius(8)
            }
        }
    }

    // MARK: - Export Result Card

    private func exportResultCard(_ r: ExportDatasetResponse) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
                    .font(.title3)
                Text("Dataset Exported!")
                    .font(.headline.bold())
                    .foregroundColor(.white)
                Spacer()
                Button { exportResult = nil } label: {
                    Image(systemName: "xmark.circle")
                        .foregroundColor(Color(hex: "9CA3AF"))
                }
                .buttonStyle(.plain)
            }

            // Stats Grid
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 120))], spacing: 8) {
                statCard("Total Pairs", "\(r.totalPairs)")
                statCard("Filtered Out", "\(r.filteredOut)")
                statCard("Avg Quality", String(format: "%.1f/10", r.avgQuality))
                statCard("File Size", String(format: "%.1f KB", r.fileSizeKb))
                statCard("Avg User Len", "\(r.avgUserLength) chars")
                statCard("Avg Angela Len", "\(r.avgAngelaLength) chars")
                statCard("Export Time", String(format: "%.1fs", r.exportTimeS))
            }

            // Source distribution
            if let sources = r.sourceDistribution {
                HStack(spacing: 12) {
                    Text("SOURCES:")
                        .font(.system(size: 9).bold())
                        .foregroundColor(Color(hex: "9CA3AF"))
                    ForEach(Array(sources.keys.sorted()), id: \.self) { key in
                        HStack(spacing: 3) {
                            Circle().fill(sourceColor(key)).frame(width: 6, height: 6)
                            Text("\(key): \(sources[key] ?? 0)")
                                .font(.caption)
                                .foregroundColor(.white)
                        }
                    }
                }
            }

            // Quality distribution
            if let qDist = r.qualityDistribution {
                HStack(spacing: 8) {
                    Text("QUALITY:")
                        .font(.system(size: 9).bold())
                        .foregroundColor(Color(hex: "9CA3AF"))
                    ForEach(["0-3", "3-5", "5-7", "7-9", "9-10"], id: \.self) { bucket in
                        VStack(spacing: 2) {
                            Text("\(qDist[bucket] ?? 0)")
                                .font(.system(size: 10, design: .monospaced).bold())
                                .foregroundColor(.white)
                            Text(bucket)
                                .font(.system(size: 8))
                                .foregroundColor(Color(hex: "6B7280"))
                        }
                        .frame(width: 40)
                        .padding(.vertical, 4)
                        .background(Color(hex: "1A1A2E"))
                        .cornerRadius(4)
                    }
                }
            }

            // File path + Open buttons
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("Training file:")
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                    Text(r.outputPath.components(separatedBy: "/").last ?? r.outputPath)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(Color(hex: "00D4FF"))
                    Spacer()
                    Button("Open in Finder") {
                        let url = URL(fileURLWithPath: r.outputPath).deletingLastPathComponent()
                        NSWorkspace.shared.open(url)
                    }
                    .buttonStyle(.plain)
                    .font(.caption.bold())
                    .foregroundColor(Color(hex: "FF6B00"))
                }
                HStack {
                    Text("Preview file:")
                        .font(.caption)
                        .foregroundColor(Color(hex: "9CA3AF"))
                    Text(r.previewPath.components(separatedBy: "/").last ?? r.previewPath)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(Color(hex: "00D4FF"))
                    Spacer()
                    Button("Preview Data") {
                        previewPage = 0
                        Task { await loadExportPreview(path: r.previewPath, offset: 0) }
                        showExportPreview = true
                    }
                    .buttonStyle(.plain)
                    .font(.caption.bold())
                    .foregroundColor(Color(hex: "00D4FF"))
                }
            }
        }
        .padding(16)
        .background(Color(hex: "0D2818"))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.green.opacity(0.3), lineWidth: 1)
        )
    }

    private func statCard(_ label: String, _ value: String) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(.body, design: .monospaced).bold())
                .foregroundColor(.white)
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(Color(hex: "9CA3AF"))
        }
        .frame(maxWidth: .infinity)
        .padding(8)
        .background(Color(hex: "1A1A2E"))
        .cornerRadius(6)
    }

    private func sourceColor(_ source: String) -> Color {
        switch source {
        case "conversations": return .blue
        case "knowledge_nodes": return .green
        case "core_memories": return .orange
        default: return .gray
        }
    }

    // MARK: - Actions

    private func loadExportPreview(path: String, offset: Int) async {
        currentPreviewPath = path
        exportPreviewData = try? await apiService.previewExportedFile(path: path, offset: offset, limit: 20)
    }

    private func exportFromDB() async {
        isExporting = true
        exportResult = nil
        error = nil
        do {
            exportResult = try await apiService.exportDataset(minQuality: exportMinQuality)
            loadDatasets()
        } catch {
            self.error = "Export failed: \(error.localizedDescription)"
        }
        isExporting = false
    }

    private func loadDatasets() {
        Task {
            async let ds = try? apiService.getDatasets()
            async let bt = try? apiService.getExportBatches()
            if let result = await ds { datasets = result.datasets }
            if let result = await bt { batches = result.batches }
        }
    }

    private func browseAndUpload() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [
            .init(filenameExtension: "jsonl")!,
            .init(filenameExtension: "json")!,
            .init(filenameExtension: "csv")!,
            .init(filenameExtension: "parquet")!,
        ]
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url {
            isUploading = true
            Task {
                do {
                    _ = try await apiService.uploadDataset(fileURL: url)
                    loadDatasets()
                } catch {
                    self.error = error.localizedDescription
                }
                isUploading = false
            }
        }
    }

    private func loadPreview(_ ds: DatasetFile) async {
        guard let id = ds.id else { return }
        preview = try? await apiService.previewDataset(id: id)
    }

    private func validateDs(_ ds: DatasetFile) async {
        guard let id = ds.id else { return }
        validation = try? await apiService.validateDataset(id: id)
        loadDatasets() // Refresh status
    }

    // MARK: - Helpers

    private func formatBytes(_ bytes: Int64) -> String {
        if bytes > 1_048_576 { return String(format: "%.1f MB", Double(bytes) / 1_048_576) }
        if bytes > 1024 { return String(format: "%.0f KB", Double(bytes) / 1024) }
        return "\(bytes) B"
    }

    private func typeColor(_ type: String) -> Color {
        switch type {
        case "sft": return .green
        case "dpo": return .blue
        case "orpo": return .purple
        case "chat": return .cyan
        default: return .gray
        }
    }

    private func stringValue(_ val: AnyCodable?) -> String {
        guard let v = val?.value else { return "" }
        if let s = v as? String { return s }
        return String(describing: v)
    }
}
