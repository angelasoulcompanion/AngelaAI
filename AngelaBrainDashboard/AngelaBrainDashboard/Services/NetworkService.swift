//
//  NetworkService.swift
//  Angela Brain Dashboard
//
//  Shared network service for HTTP requests
//  DRY refactor - centralizes URL session and JSON decoding
//

import Foundation

/// Network-related errors
enum NetworkError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int)
    case decodingError(Error)
    case noData

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let code):
            return "HTTP error: \(code)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .noData:
            return "No data received"
        }
    }
}

/// Centralized network service for all HTTP requests
class NetworkService {
    static let shared = NetworkService()

    /// Default base URL for Angela API
    let defaultBaseURL = APIConfig.baseURL

    /// Shared JSON decoder with common date strategies
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    /// Default timeout interval
    private let defaultTimeout: TimeInterval = 30.0

    private init() {}

    // MARK: - Generic GET Request

    /// Performs a GET request and decodes the response
    /// - Parameters:
    ///   - endpoint: API endpoint (e.g., "/api/human-mind/stats")
    ///   - baseURL: Base URL (defaults to defaultBaseURL)
    ///   - timeout: Request timeout (defaults to 30 seconds)
    /// - Returns: Decoded response of type T
    func get<T: Decodable>(
        _ endpoint: String,
        baseURL: String? = nil,
        timeout: TimeInterval? = nil
    ) async throws -> T {
        let base = baseURL ?? defaultBaseURL
        guard let url = URL(string: "\(base)\(endpoint)") else {
            throw NetworkError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = timeout ?? defaultTimeout

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.httpError(statusCode: httpResponse.statusCode)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decodingError(error)
        }
    }

    /// Performs a GET request and returns optional (nil on error)
    /// - Parameters:
    ///   - endpoint: API endpoint
    ///   - baseURL: Base URL
    /// - Returns: Decoded response or nil
    func getOptional<T: Decodable>(
        _ endpoint: String,
        baseURL: String? = nil
    ) async -> T? {
        do {
            return try await get(endpoint, baseURL: baseURL)
        } catch {
            print("NetworkService error (\(endpoint)): \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Generic POST Request

    /// Performs a POST request with JSON body
    /// - Parameters:
    ///   - endpoint: API endpoint
    ///   - body: Encodable body object
    ///   - baseURL: Base URL
    /// - Returns: Decoded response of type T
    func post<T: Decodable, B: Encodable>(
        _ endpoint: String,
        body: B,
        baseURL: String? = nil
    ) async throws -> T {
        let base = baseURL ?? defaultBaseURL
        guard let url = URL(string: "\(base)\(endpoint)") else {
            throw NetworkError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = defaultTimeout
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.httpError(statusCode: httpResponse.statusCode)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw NetworkError.decodingError(error)
        }
    }

    // MARK: - Simple Fetch (Raw Data)

    /// Fetches raw data from URL
    func fetchData(from urlString: String) async throws -> Data {
        guard let url = URL(string: urlString) else {
            throw NetworkError.invalidURL
        }

        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.httpError(statusCode: httpResponse.statusCode)
        }

        return data
    }

    // MARK: - Health Check

    /// Checks if a URL is reachable
    func isReachable(_ urlString: String, timeout: TimeInterval = 5.0) async -> Bool {
        guard let url = URL(string: urlString) else { return false }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = timeout

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse {
                return (200...299).contains(httpResponse.statusCode)
            }
            return false
        } catch {
            return false
        }
    }
}

// MARK: - Convenience Extensions

extension NetworkService {
    /// Ollama API base URL
    var ollamaBaseURL: String { "http://localhost:11434" }

    /// Check if Ollama is running
    func isOllamaAvailable() async -> Bool {
        return await isReachable("\(ollamaBaseURL)/api/tags")
    }

    /// Check if Angela API is running
    func isAngelaAPIAvailable() async -> Bool {
        return await isReachable("\(defaultBaseURL)/api/health")
    }
}
