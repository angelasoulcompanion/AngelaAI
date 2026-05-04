//
//  VideoStudioAPI.swift
//  AITop
//
//  REST endpoints for the Angelora Video Studio tab.
//  Backend prefix: /api/video-studio
//

import Foundation

extension APIService {

    // MARK: - Projects

    func videoStudioListProjects() async throws -> [VideoProject] {
        let env: VideoProjectListEnvelope = try await get("/video-studio/projects")
        return env.projects
    }

    func videoStudioGetProject(_ projectId: String) async throws -> VideoProjectDetailEnvelope {
        try await get("/video-studio/projects/\(projectId)")
    }

    /// Multipart upload — server stores PDF in Supabase Storage (sha-keyed),
    /// runs the analysis, and persists segments + prompts. Idempotent on sha256.
    func videoStudioUploadPDF(
        fileURL: URL,
        title: String? = nil,
        audience: String? = nil,
        skipLLM: Bool = false
    ) async throws -> VideoUploadResponse {
        let boundary = UUID().uuidString
        let fileData = try Data(contentsOf: fileURL)
        let filename = fileURL.lastPathComponent

        var body = Data()
        let crlf = "\r\n"
        // file part
        body.append("--\(boundary)\(crlf)".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\(crlf)".data(using: .utf8)!)
        body.append("Content-Type: application/pdf\(crlf)\(crlf)".data(using: .utf8)!)
        body.append(fileData)
        body.append(crlf.data(using: .utf8)!)
        body.append("--\(boundary)--\(crlf)".data(using: .utf8)!)

        // Query params: title / audience / skip_llm (FastAPI accepts simple types as query).
        var components = URLComponents(string: "\(APIConfig.apiBaseURL)/video-studio/upload")!
        var qs: [URLQueryItem] = [URLQueryItem(name: "skip_llm", value: skipLLM ? "true" : "false")]
        if let t = title, !t.isEmpty { qs.append(URLQueryItem(name: "title", value: t)) }
        if let a = audience, !a.isEmpty { qs.append(URLQueryItem(name: "audience", value: a)) }
        components.queryItems = qs

        var request = URLRequest(url: components.url!)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        request.timeoutInterval = 600  // analysis can be slow on large decks

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResp = response as? HTTPURLResponse, (200...299).contains(httpResp.statusCode) else {
            let msg = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError((response as? HTTPURLResponse)?.statusCode ?? 0, msg)
        }
        return try decoder.decode(VideoUploadResponse.self, from: data)
    }

    // MARK: - Segments — prompt regeneration only

    func videoStudioRegeneratePrompt(
        _ segmentId: String,
        templateName: String? = nil,
        audience: String? = nil,
        personaName: String? = nil,
        note: String? = nil
    ) async throws -> VideoSegmentRegenerateResponse {
        let req = VideoSegmentRegenerateRequest(
            templateName: templateName,
            audience: audience,
            personaName: personaName,
            note: note
        )
        return try await post("/video-studio/segments/\(segmentId)/regenerate-prompt", body: req, timeout: 60)
    }

    // MARK: - Bootstrap (one-time)

    func videoStudioBootstrap() async throws {
        struct Empty: Codable {}
        let _: Empty = try await post("/video-studio/bootstrap", body: ["": ""])
    }
}
