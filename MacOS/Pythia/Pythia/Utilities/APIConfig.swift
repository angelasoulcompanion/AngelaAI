//
//  APIConfig.swift
//  Pythia
//
//  Single source of truth for API host/port/base URL.
//  Port is dynamic — BackendManager picks a free port at launch.
//

import Foundation

enum APIConfig {
    static let host = "127.0.0.1"
    static let preferredPort = 8766
    static var port: Int = 8766

    static var baseURL: String { "http://\(host):\(port)" }
    static var apiBaseURL: String { "\(baseURL)/api" }
}
