//
//  PriceStreamService.swift
//  Pythia — WebSocket client for live price updates
//

import Foundation
import Combine

struct PriceUpdateMessage: Codable {
    let type: String
    let timestamp: String?
    let quotes: [WsQuote]?

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
}

class PriceStreamService: ObservableObject {
    static let shared = PriceStreamService()

    @Published var latestQuotes: [String: WatchlistQuote] = [:]
    @Published var isConnected = false
    @Published var updateCounter: Int = 0  // simple counter to trigger onChange

    private var wsTask: URLSessionWebSocketTask?
    private var session: URLSession
    private var isReceiving = false

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

        guard let url = URL(string: urlStr) else { return }

        let task = session.webSocketTask(with: url)
        task.resume()
        wsTask = task
        isReceiving = false
        print("[PriceStream] 🔌 Connecting to \(urlStr)")

        // Start receive loop in detached task to avoid @MainActor issues
        Task.detached { [weak self] in
            await self?.receiveLoop()
        }
    }

    func disconnect() {
        wsTask?.cancel(with: .normalClosure, reason: nil)
        wsTask = nil
        isReceiving = false
        Task { @MainActor in
            self.isConnected = false
        }
    }

    func subscribe(watchlistId: String?) {
        guard let ws = wsTask else { return }
        let msg = "{\"action\":\"subscribe\",\"watchlist_id\":\(watchlistId.map { "\"\($0)\"" } ?? "null")}"
        ws.send(.string(msg)) { _ in }
    }

    // MARK: - Async receive loop

    private func receiveLoop() async {
        guard let ws = wsTask else { return }
        isReceiving = true
        print("[PriceStream] 🔄 Receive loop started")

        while isReceiving {
            do {
                let message = try await ws.receive()

                // Mark connected on first successful receive
                await MainActor.run {
                    if !self.isConnected {
                        self.isConnected = true
                        print("[PriceStream] ✅ Connected and receiving!")
                    }
                }

                switch message {
                case .string(let text):
                    await handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        await handleMessage(text)
                    }
                @unknown default:
                    break
                }
            } catch {
                print("[PriceStream] ❌ Receive error: \(error.localizedDescription)")
                await MainActor.run {
                    self.isConnected = false
                    self.isReceiving = false
                }
                // Auto-reconnect after 5s
                try? await Task.sleep(for: .seconds(5))
                await MainActor.run {
                    print("[PriceStream] 🔄 Reconnecting...")
                    self.connect()
                }
                return
            }
        }
    }

    @MainActor
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
                updateCounter += 1
                print("[PriceStream] 📊 Received \(quotes.count) quotes (update #\(updateCounter))")
            }
        } catch {
            print("[PriceStream] ⚠️ Decode error: \(error)")
        }
    }
}
