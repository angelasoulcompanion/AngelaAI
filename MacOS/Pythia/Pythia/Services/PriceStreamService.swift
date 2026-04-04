//
//  PriceStreamService.swift
//  Pythia — WebSocket client for live price updates
//

import Foundation
import Combine
import os.log

struct PriceUpdateMessage: Codable {
    let type: String
    let timestamp: String?
    let quotes: [WsQuote]?
    let data: AckData?

    struct WsQuote: Codable {
        let symbol: String
        let name: String?
        let currentPrice: Double?
        let change: Double?
        let changePercent: Double?
        let sparkline: [Double]?
        let currency: String?
        let volume: Int?

        enum CodingKeys: String, CodingKey {
            case symbol, name, sparkline, currency, volume
            case currentPrice = "current_price"
            case change
            case changePercent = "change_percent"
        }
    }

    struct AckData: Codable {
        let watchlistId: String?
        enum CodingKeys: String, CodingKey {
            case watchlistId = "watchlist_id"
        }
    }
}

@MainActor
class PriceStreamService: ObservableObject {
    static let shared = PriceStreamService()

    @Published var latestQuotes: [String: WatchlistQuote] = [:]
    @Published var isConnected = false
    @Published var lastUpdateTime: Date?

    private var wsTask: URLSessionWebSocketTask?
    private var session: URLSession
    private let logger = Logger(subsystem: "com.pythia", category: "PriceStream")
    private var reconnectTask: Task<Void, Never>?

    private init() {
        let config = URLSessionConfiguration.default
        config.waitsForConnectivity = true
        session = URLSession(configuration: config)
    }

    func connect(watchlistId: String? = nil) {
        disconnect()

        let port = APIConfig.port
        var urlStr = "ws://127.0.0.1:\(port)/ws/prices"
        if let wlId = watchlistId {
            urlStr += "?watchlist_id=\(wlId)"
        }

        guard let url = URL(string: urlStr) else {
            logger.error("Invalid WS URL: \(urlStr)")
            return
        }

        let task = session.webSocketTask(with: url)
        task.resume()
        wsTask = task
        isConnected = true
        logger.info("WS connecting to \(urlStr)")

        receiveLoop()
    }

    func disconnect() {
        reconnectTask?.cancel()
        reconnectTask = nil
        wsTask?.cancel(with: .normalClosure, reason: nil)
        wsTask = nil
        isConnected = false
    }

    func subscribe(watchlistId: String?) {
        guard let ws = wsTask else { return }
        let msg: [String: Any?] = ["action": "subscribe", "watchlist_id": watchlistId]
        if let data = try? JSONSerialization.data(withJSONObject: msg.compactMapValues { $0 }) {
            ws.send(.string(String(data: data, encoding: .utf8) ?? "")) { _ in }
        }
    }

    // MARK: - Private

    private func receiveLoop() {
        wsTask?.receive { [weak self] result in
            Task { @MainActor in
                guard let self = self else { return }

                switch result {
                case .success(let message):
                    switch message {
                    case .string(let text):
                        self.handleMessage(text)
                    case .data(let data):
                        if let text = String(data: data, encoding: .utf8) {
                            self.handleMessage(text)
                        }
                    @unknown default:
                        break
                    }
                    self.receiveLoop()

                case .failure(let error):
                    self.logger.error("WS receive error: \(error.localizedDescription)")
                    self.isConnected = false
                    self.scheduleReconnect()
                }
            }
        }
    }

    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }

        do {
            let msg = try JSONDecoder().decode(PriceUpdateMessage.self, from: data)

            if msg.type == "price_update", let quotes = msg.quotes {
                for q in quotes {
                    latestQuotes[q.symbol] = WatchlistQuote(
                        symbol: q.symbol,
                        name: q.name,
                        currentPrice: q.currentPrice,
                        change: q.change,
                        changePercent: q.changePercent,
                        sparkline: q.sparkline ?? [],
                        currency: q.currency,
                        volume: q.volume
                    )
                }
                lastUpdateTime = Date()
                logger.info("Received \(quotes.count) live quotes")
            }
        } catch {
            logger.error("WS decode error: \(error.localizedDescription)")
        }
    }

    private func scheduleReconnect() {
        reconnectTask?.cancel()
        reconnectTask = Task {
            try? await Task.sleep(for: .seconds(5))
            guard !Task.isCancelled else { return }
            logger.info("WS reconnecting...")
            connect()
        }
    }
}
