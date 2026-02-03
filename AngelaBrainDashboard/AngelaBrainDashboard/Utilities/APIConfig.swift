//
//  APIConfig.swift
//  Angela Brain Dashboard
//
//  Single source of truth for API host/port/base URL.
//

import Foundation

enum APIConfig {
    static let host = "127.0.0.1"
    static let port = 8765
    static let baseURL = "http://\(host):\(port)"
    static let apiBaseURL = "\(baseURL)/api"
}
