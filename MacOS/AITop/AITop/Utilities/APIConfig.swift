//
//  APIConfig.swift
//  AITop
//
//  Single source of truth for API host/port/base URL.
//

import Foundation

enum APIConfig {
    static let host = "127.0.0.1"
    static let preferredPort = 8767
    static var port: Int = 8767

    static var baseURL: String { "http://\(host):\(port)" }
    static var apiBaseURL: String { "\(baseURL)/api" }
}
