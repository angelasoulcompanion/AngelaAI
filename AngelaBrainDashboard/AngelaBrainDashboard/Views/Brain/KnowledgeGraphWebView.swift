//
//  KnowledgeGraphWebView.swift
//  Angela Brain Dashboard
//
//  💜 Interactive Knowledge Graph using D3.js 🧠
//

import SwiftUI
import WebKit

// MARK: - Graph Data Models

struct GraphNode: Codable {
    let id: String
    let name: String
    let category: String?
    let understanding: Double?
    let references: Int
}

struct GraphLink: Codable {
    let source: String
    let target: String
    let strength: Double
}

struct GraphData: Codable {
    let nodes: [GraphNode]
    let links: [GraphLink]
    let totalNodes: Int?
}

// MARK: - WebView Coordinator

class KnowledgeGraphCoordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
    var parent: KnowledgeGraphWebView

    init(_ parent: KnowledgeGraphWebView) {
        self.parent = parent
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "nodeClicked" {
            if let body = message.body as? [String: Any],
               let nodeId = body["id"] as? String,
               let nodeName = body["name"] as? String {

                print("📍 Node clicked: \(nodeName) (ID: \(nodeId))")

                DispatchQueue.main.async {
                    self.parent.onNodeClick?(nodeId, nodeName)
                }
            }
        }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        print("✅ WebView loaded successfully")

        // Check if graph data is ready
        if let graphData = parent.graphData {
            print("📊 Graph data is ready with \(graphData.nodes.count) nodes")

            // Wait for JavaScript to be fully ready, then send data
            waitForJavaScriptReady(webView: webView, graphData: graphData, retryCount: 0)
        } else {
            print("⚠️ No graph data yet - will update when data arrives")
        }
    }

    func waitForJavaScriptReady(webView: WKWebView, graphData: GraphData, retryCount: Int) {
        let maxRetries = 10

        // Check if window.updateGraph function exists
        webView.evaluateJavaScript("typeof window.updateGraph === 'function'") { result, error in
            if let isReady = result as? Bool, isReady {
                print("✅ JavaScript is ready! Sending graph data...")
                self.updateGraphData(in: webView, with: graphData)
            } else if retryCount < maxRetries {
                // Retry after 100ms
                print("⏳ JavaScript not ready yet, retry \(retryCount + 1)/\(maxRetries)...")
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                    self.waitForJavaScriptReady(webView: webView, graphData: graphData, retryCount: retryCount + 1)
                }
            } else {
                print("❌ JavaScript failed to load after \(maxRetries) retries")
            }
        }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        print("❌ WebView failed to load: \(error.localizedDescription)")
    }

    func updateGraphData(in webView: WKWebView, with graphData: GraphData) {
        do {
            let encoder = JSONEncoder()
            let jsonData = try encoder.encode(graphData)
            let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"

            print("🔍 About to send graph data:")
            print("   Nodes: \(graphData.nodes.count)")
            print("   Links: \(graphData.links.count)")
            print("   JSON preview: \(jsonString.prefix(200))...")

            let script = "window.updateGraph(\(jsonString));"

            webView.evaluateJavaScript(script) { result, error in
                if let error = error {
                    print("❌ Failed to update graph: \(error)")
                } else {
                    print("✅ Graph updated with \(graphData.nodes.count) nodes")
                }
            }
        } catch {
            print("❌ Failed to encode graph data: \(error)")
        }
    }
}

// MARK: - SwiftUI WebView

struct KnowledgeGraphWebView: NSViewRepresentable {
    var graphData: GraphData?
    var onNodeClick: ((String, String) -> Void)?

    func makeCoordinator() -> KnowledgeGraphCoordinator {
        KnowledgeGraphCoordinator(self)
    }

    func makeNSView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let contentController = WKUserContentController()

        // Register message handler for node clicks
        contentController.add(context.coordinator, name: "nodeClicked")

        config.userContentController = contentController

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator

        // Enable developer tools in debug builds
        #if DEBUG
        webView.configuration.preferences.setValue(true, forKey: "developerExtrasEnabled")
        #endif

        // Load HTML file
        if let htmlPath = Bundle.main.path(forResource: "knowledge_graph", ofType: "html") {
            let url = URL(fileURLWithPath: htmlPath)
            webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
            print("📄 Loading HTML from: \(htmlPath)")
        } else {
            print("❌ knowledge_graph.html not found in bundle")
        }

        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {
        // Update graph data when it changes
        if let graphData = graphData {
            print("🔄 updateNSView called with \(graphData.nodes.count) nodes")
            // Wait for JavaScript to be ready before updating
            context.coordinator.waitForJavaScriptReady(webView: webView, graphData: graphData, retryCount: 0)
        }
    }
}

// MARK: - Preview Provider

struct KnowledgeGraphWebView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleData = GraphData(
            nodes: [
                GraphNode(id: "1", name: "Angela", category: "person", understanding: 1.0, references: 69),
                GraphNode(id: "2", name: "David", category: "person", understanding: 1.0, references: 43),
                GraphNode(id: "3", name: "SwiftUI", category: "concept", understanding: 0.85, references: 12),
                GraphNode(id: "4", name: "Database", category: "concept", understanding: 0.90, references: 15)
            ],
            links: [
                GraphLink(source: "1", target: "2", strength: 1.0),
                GraphLink(source: "1", target: "3", strength: 0.7),
                GraphLink(source: "2", target: "4", strength: 0.6)
            ],
            totalNodes: 10225
        )

        KnowledgeGraphWebView(graphData: sampleData) { id, name in
            print("Clicked: \(name)")
        }
    }
}
