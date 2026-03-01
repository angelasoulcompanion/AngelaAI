//
//  DatabaseService.swift
//  Pythia
//
//  REST API client for Pythia backend (port 8766)
//

import Foundation
import Combine

class DatabaseService: ObservableObject {
    static let shared = DatabaseService()

    @Published var isConnected = false
    @Published var errorMessage: String?

    private var baseURL: String { APIConfig.apiBaseURL }
    private let decoder: JSONDecoder

    private init() {
        decoder = JSONDecoder()
        // Support multiple date formats
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            let formats = [
                "yyyy-MM-dd'T'HH:mm:ss.SSSSSSXXXXX",
                "yyyy-MM-dd'T'HH:mm:ss.SSSXXXXX",
                "yyyy-MM-dd'T'HH:mm:ssXXXXX",
                "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
                "yyyy-MM-dd'T'HH:mm:ss.SSS",
                "yyyy-MM-dd'T'HH:mm:ss",
                "yyyy-MM-dd",
            ]

            for format in formats {
                let formatter = DateFormatter()
                formatter.dateFormat = format
                formatter.locale = Locale(identifier: "en_US_POSIX")
                formatter.timeZone = TimeZone(identifier: "Asia/Bangkok")
                if let date = formatter.date(from: dateString) {
                    return date
                }
            }

            // ISO8601 fallback
            if let date = ISO8601DateFormatter().date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(in: container,
                debugDescription: "Cannot decode date: \(dateString)")
        }
    }

    // MARK: - Generic HTTP Methods

    func get<T: Decodable>(_ endpoint: String) async throws -> T {
        let url = URL(string: "\(baseURL)\(endpoint)")!
        var request = URLRequest(url: url)
        request.timeoutInterval = 30.0

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw DatabaseError.httpError(statusCode: statusCode)
        }

        return try decoder.decode(T.self, from: data)
    }

    func post<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T {
        let url = URL(string: "\(baseURL)\(endpoint)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw DatabaseError.httpError(statusCode: statusCode)
        }

        return try decoder.decode(T.self, from: data)
    }

    func put<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T {
        let url = URL(string: "\(baseURL)\(endpoint)")!
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw DatabaseError.httpError(statusCode: statusCode)
        }

        return try decoder.decode(T.self, from: data)
    }

    func delete(_ endpoint: String) async throws {
        let url = URL(string: "\(baseURL)\(endpoint)")!
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.timeoutInterval = 30.0

        let (_, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw DatabaseError.httpError(statusCode: statusCode)
        }
    }

    // MARK: - Health Check

    func checkConnection() async {
        do {
            let _: HealthResponse = try await get("/health")
            await MainActor.run {
                isConnected = true
                errorMessage = nil
            }
        } catch {
            await MainActor.run {
                isConnected = false
                errorMessage = error.localizedDescription
            }
        }
    }

    // MARK: - Portfolio Methods

    func fetchPortfolios() async throws -> [Portfolio] {
        try await get("/portfolios/")
    }

    func fetchPortfolio(id: String) async throws -> PortfolioDetail {
        try await get("/portfolios/\(id)")
    }

    func createPortfolio(_ portfolio: PortfolioCreateRequest) async throws -> PortfolioCreateResponse {
        try await post("/portfolios/", body: portfolio)
    }

    func fetchHoldings(portfolioId: String) async throws -> [Holding] {
        try await get("/portfolios/\(portfolioId)/holdings")
    }

    func fetchTransactions(portfolioId: String, limit: Int = 50) async throws -> [Transaction] {
        try await get("/portfolios/\(portfolioId)/transactions?limit=\(limit)")
    }

    // MARK: - Asset Methods

    func fetchAssets(search: String? = nil) async throws -> [Asset] {
        if let search = search, !search.isEmpty {
            return try await get("/assets/?search=\(search.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? search)")
        }
        return try await get("/assets/")
    }

    func createAssetFromYahoo(symbol: String) async throws -> AssetCreateResponse {
        try await post("/assets/from-yahoo?symbol=\(symbol)", body: EmptyBody())
    }

    // MARK: - Market Methods

    func fetchQuote(symbol: String) async throws -> StockQuote {
        try await get("/market/quote/\(symbol)")
    }

    func fetchHistory(symbol: String, period: String = "1y") async throws -> HistoryResponse {
        try await get("/market/history/\(symbol)?period=\(period)")
    }

    func fetchWatchlistQuotes(watchlistId: String? = nil) async throws -> [WatchlistQuote] {
        if let wlId = watchlistId {
            return try await get("/market/watchlist-quotes?watchlist_id=\(wlId)")
        }
        return try await get("/market/watchlist-quotes")
    }

    func fetchFinancialOutlook(symbol: String) async throws -> FinancialOutlookResponse {
        try await get("/market/outlook/\(symbol)")
    }

    func fetchFinancialStatements(symbol: String, period: String = "annual") async throws -> FinancialStatementsResponse {
        try await get("/market/financials/\(symbol)?period=\(period)")
    }

    func fetchAndStorePrices(assetId: String, days: Int = 365) async throws -> FetchPricesResponse {
        try await get("/market/fetch-prices/\(assetId)?days=\(days)")
    }

    func fetchTechnicalAnalysis(
        symbol: String,
        period: String = "6mo",
        macdFast: Int = 12, macdSlow: Int = 26, macdSignal: Int = 9,
        rsiPeriod: Int = 14,
        smaPeriods: String = "20,50",
        emaPeriods: String = "12,26",
        bbPeriod: Int = 20, bbStd: Double = 2.0
    ) async throws -> TechnicalAnalysisResponse {
        var url = "/technical/\(symbol)?period=\(period)"
        url += "&macd_fast=\(macdFast)&macd_slow=\(macdSlow)&macd_signal=\(macdSignal)"
        url += "&rsi_period=\(rsiPeriod)"
        url += "&sma_periods=\(smaPeriods)&ema_periods=\(emaPeriods)"
        url += "&bb_period=\(bbPeriod)&bb_std=\(bbStd)"
        return try await get(url)
    }

    // MARK: - Watchlist Methods

    func fetchWatchlists() async throws -> [Watchlist] {
        try await get("/watchlists/")
    }

    func fetchWatchlist(id: String) async throws -> WatchlistDetail {
        try await get("/watchlists/\(id)")
    }

    func createWatchlist(name: String, description: String?) async throws -> WatchlistCreateResponse {
        try await post("/watchlists/", body: WatchlistCreateBody(name: name, description: description))
    }

    func deleteWatchlist(id: String) async throws {
        try await delete("/watchlists/\(id)")
    }

    func addWatchlistItem(watchlistId: String, assetId: String, notes: String? = nil) async throws -> WatchlistItemAddResponse {
        try await post("/watchlists/\(watchlistId)/items", body: WatchlistItemAddBody(assetId: assetId, notes: notes))
    }

    func removeWatchlistItem(watchlistId: String, assetId: String) async throws {
        try await delete("/watchlists/\(watchlistId)/items/\(assetId)")
    }

    func addWatchlistItemBySymbol(watchlistId: String, symbol: String) async throws -> WatchlistItemAddResponse {
        try await post("/watchlists/\(watchlistId)/add-by-symbol?symbol=\(symbol.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? symbol)", body: EmptyBody())
    }

    // MARK: - Dashboard

    func fetchDashboardSummary() async throws -> DashboardSummary {
        try await get("/dashboard/summary")
    }

    func fetchPortfolioBreakdown() async throws -> [AssetTypeBreakdown] {
        try await get("/dashboard/portfolio-breakdown")
    }

    // MARK: - Settings

    func fetchSettings() async throws -> [AppSetting] {
        try await get("/settings/")
    }

    // MARK: - MPT (Phase 2)

    func optimizePortfolio(portfolioId: String, type: String = "max_sharpe", riskFreeRate: Double = 0.0225, days: Int = 365) async throws -> OptimizationResponse {
        try await get("/mpt/\(portfolioId)/optimize?optimization_type=\(type)&risk_free_rate=\(riskFreeRate)&days=\(days)")
    }

    func fetchEfficientFrontier(portfolioId: String, nPoints: Int = 50, days: Int = 365) async throws -> EfficientFrontierResponse {
        try await get("/mpt/\(portfolioId)/efficient-frontier?n_points=\(nPoints)&days=\(days)")
    }

    func fetchCorrelationMatrix(portfolioId: String, days: Int = 365) async throws -> CorrelationResponse {
        try await get("/mpt/\(portfolioId)/correlation?days=\(days)")
    }

    // MARK: - Risk (Phase 2)

    func calculateVaR(portfolioId: String, method: String = "historical", confidence: Double = 0.95, holdingPeriod: Int = 1) async throws -> VaRResponse {
        try await get("/risk/\(portfolioId)/var?method=\(method)&confidence=\(confidence)&holding_period=\(holdingPeriod)")
    }

    func fetchComponentVaR(portfolioId: String) async throws -> ComponentVaRResponse {
        try await get("/risk/\(portfolioId)/component-var")
    }

    func fetchStressScenarios() async throws -> StressScenarioListResponse {
        try await get("/risk/scenarios")
    }

    func runStressTest(portfolioId: String, scenario: String) async throws -> StressTestResponse {
        try await get("/risk/\(portfolioId)/stress-test/\(scenario)")
    }

    func runAllStressTests(portfolioId: String) async throws -> StressTestAllResponse {
        try await get("/risk/\(portfolioId)/stress-test-all")
    }

    // MARK: - Metrics (Phase 2)

    func fetchPerformanceMetrics(portfolioId: String, days: Int = 365) async throws -> PerformanceMetricsResponse {
        try await get("/metrics/\(portfolioId)?days=\(days)")
    }

    func fetchDrawdownAnalysis(portfolioId: String, days: Int = 365) async throws -> DrawdownResponse {
        try await get("/metrics/\(portfolioId)/drawdown?days=\(days)")
    }

    func fetchRollingMetrics(portfolioId: String, window: Int = 60, days: Int = 365) async throws -> RollingMetricsResponse {
        try await get("/metrics/\(portfolioId)/rolling?window=\(window)&days=\(days)")
    }

    // MARK: - Options (Phase 3)

    func priceOption(type: String = "call", spot: Double, strike: Double, expiry: Double, vol: Double = 0.2) async throws -> OptionPriceResponse {
        try await get("/options/price?option_type=\(type)&spot=\(spot)&strike=\(strike)&time_to_expiry=\(expiry)&volatility=\(vol)")
    }

    func calcImpliedVol(type: String, price: Double, spot: Double, strike: Double, expiry: Double) async throws -> ImpliedVolResponse {
        try await get("/options/implied-volatility?option_type=\(type)&market_price=\(price)&spot=\(spot)&strike=\(strike)&time_to_expiry=\(expiry)")
    }

    // MARK: - Backtest (Phase 3)

    func runBacktest(assetId: String, shortWindow: Int = 20, longWindow: Int = 50, capital: Double = 1_000_000, days: Int = 730) async throws -> BacktestResponse {
        try await get("/backtest/\(assetId)/sma?short_window=\(shortWindow)&long_window=\(longWindow)&initial_capital=\(capital)&days=\(days)")
    }

    // MARK: - Monte Carlo (Phase 3)

    func runMonteCarlo(assetId: String, simulations: Int = 10000, steps: Int = 252) async throws -> MonteCarloResponse {
        try await get("/monte-carlo/\(assetId)/simulate?n_simulations=\(simulations)&time_steps=\(steps)")
    }

    // MARK: - Statistics (Phase 3)

    func analyzeDistribution(assetId: String, days: Int = 365) async throws -> StatisticsResponse {
        try await get("/statistics/\(assetId)/distribution?days=\(days)")
    }

    // MARK: - AI Advisor (Phase 4)

    func getAIAdvice(portfolioId: String, question: String? = nil) async throws -> AIAdvisorResponse {
        var url = "/ai/advisor/\(portfolioId)/analyze"
        if let q = question, !q.isEmpty {
            url += "?question=\(q.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? q)"
        }
        return try await get(url)
    }

    // MARK: - AI Sentiment (Phase 4)

    func getSentiment(assetId: String, days: Int = 30) async throws -> AISentimentResponse {
        try await get("/ai/sentiment/\(assetId)?days=\(days)")
    }

    // MARK: - AI Forecast (Phase 4)

    func getForecast(assetId: String, method: String = "moving_average", days: Int = 30) async throws -> AIForecastResponse {
        try await get("/ai/forecast/\(assetId)?method=\(method)&forecast_days=\(days)")
    }

    // MARK: - AI Research (Phase 4)

    func searchResearch(query: String) async throws -> ResearchSearchResponse {
        try await get("/ai/research/search?query=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query)")
    }

    func getResearchHistory() async throws -> [ResearchDoc] {
        try await get("/ai/research/history")
    }
}

// MARK: - Error Types

enum DatabaseError: Error, LocalizedError {
    case httpError(statusCode: Int)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .httpError(let code): return "HTTP error: \(code)"
        case .decodingError(let error): return "Decoding error: \(error.localizedDescription)"
        case .networkError(let error): return "Network error: \(error.localizedDescription)"
        }
    }
}

// MARK: - Helper Types

struct HealthResponse: Codable {
    let status: String
    let database: String?
    let app: String?
}

struct EmptyBody: Codable {}
