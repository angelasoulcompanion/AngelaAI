//
//  TechStackGraphWebView.swift
//  Angela Brain Dashboard
//
//  💜 Interactive Tech Stack Graph using D3.js 🛠️
//

import SwiftUI
import WebKit

// MARK: - Tech Stack Graph Data Models

struct TechStackNode: Codable {
    let id: String
    let name: String
    let nodeType: String        // "tech" or "project"
    let techType: String?       // "language", "framework", "database", "tool", "library", "service"
    let version: String?
    let purpose: String?
    let projectCount: Int?      // For tech nodes: how many projects use this
    let techCount: Int?         // For project nodes: how many techs it uses
    let projects: [String]?     // List of project names using this tech
    let status: String?         // For project nodes
}

struct TechStackLink: Codable {
    let source: String
    let target: String
    let strength: Double
    let techType: String?       // To color the link
}

struct TechStackGraphData: Codable {
    let nodes: [TechStackNode]
    let links: [TechStackLink]
}

// MARK: - WebView Coordinator

class TechStackGraphCoordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
    var parent: TechStackGraphWebView

    init(_ parent: TechStackGraphWebView) {
        self.parent = parent
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "techNodeClicked" {
            if let body = message.body as? [String: Any],
               let nodeId = body["id"] as? String,
               let nodeName = body["name"] as? String {

                print("📍 Tech node clicked: \(nodeName) (ID: \(nodeId))")

                DispatchQueue.main.async {
                    self.parent.onNodeClick?(nodeId, nodeName)
                }
            }
        }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        print("✅ Tech Stack WebView loaded successfully")

        if let graphData = parent.graphData {
            print("📊 Tech stack data is ready with \(graphData.nodes.count) nodes")
            waitForJavaScriptReady(webView: webView, graphData: graphData, retryCount: 0)
        } else {
            print("⚠️ No tech stack data yet - will update when data arrives")
        }
    }

    func waitForJavaScriptReady(webView: WKWebView, graphData: TechStackGraphData, retryCount: Int) {
        let maxRetries = 10

        webView.evaluateJavaScript("typeof window.updateGraph === 'function'") { result, error in
            if let isReady = result as? Bool, isReady {
                print("✅ JavaScript is ready! Sending tech stack data...")
                self.updateGraphData(in: webView, with: graphData)
            } else if retryCount < maxRetries {
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
        print("❌ Tech Stack WebView failed to load: \(error.localizedDescription)")
    }

    func updateGraphData(in webView: WKWebView, with graphData: TechStackGraphData) {
        do {
            let encoder = JSONEncoder()
            let jsonData = try encoder.encode(graphData)
            let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"

            print("🔍 About to send tech stack data:")
            print("   Nodes: \(graphData.nodes.count)")
            print("   Links: \(graphData.links.count)")

            let script = "window.updateGraph(\(jsonString));"

            webView.evaluateJavaScript(script) { result, error in
                if let error = error {
                    print("❌ Failed to update tech stack graph: \(error)")
                } else {
                    print("✅ Tech stack graph updated with \(graphData.nodes.count) nodes")
                }
            }
        } catch {
            print("❌ Failed to encode tech stack data: \(error)")
        }
    }
}

// MARK: - SwiftUI WebView

struct TechStackGraphWebView: NSViewRepresentable {
    var graphData: TechStackGraphData?
    var onNodeClick: ((String, String) -> Void)?

    func makeCoordinator() -> TechStackGraphCoordinator {
        TechStackGraphCoordinator(self)
    }

    func makeNSView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let contentController = WKUserContentController()

        // Register message handler for node clicks
        contentController.add(context.coordinator, name: "techNodeClicked")

        config.userContentController = contentController

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator

        // Enable developer tools in debug builds
        #if DEBUG
        webView.configuration.preferences.setValue(true, forKey: "developerExtrasEnabled")
        #endif

        // Load HTML file
        if let htmlPath = Bundle.main.path(forResource: "tech_stack_graph", ofType: "html") {
            let url = URL(fileURLWithPath: htmlPath)
            webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
            print("📄 Loading tech stack HTML from: \(htmlPath)")
        } else {
            print("❌ tech_stack_graph.html not found in bundle")
        }

        return webView
    }

    func updateNSView(_ webView: WKWebView, context: Context) {
        if let graphData = graphData {
            print("🔄 updateNSView called with \(graphData.nodes.count) tech stack nodes")
            context.coordinator.waitForJavaScriptReady(webView: webView, graphData: graphData, retryCount: 0)
        }
    }
}

// MARK: - Preview Provider

struct TechStackGraphWebView_Previews: PreviewProvider {
    static var previews: some View {
        let sampleData = TechStackGraphData(
            nodes: [
                TechStackNode(id: "proj-1", name: "AngelaMobileApp", nodeType: "project", techType: nil, version: nil, purpose: nil, projectCount: nil, techCount: 5, projects: nil, status: "active"),
                TechStackNode(id: "tech-swift", name: "Swift", nodeType: "tech", techType: "language", version: "5.9+", purpose: "Main language", projectCount: 3, techCount: nil, projects: ["AngelaMobileApp", "AngelaBrainDashboard"], status: nil),
                TechStackNode(id: "tech-swiftui", name: "SwiftUI", nodeType: "tech", techType: "framework", version: nil, purpose: "UI Framework", projectCount: 2, techCount: nil, projects: ["AngelaMobileApp"], status: nil)
            ],
            links: [
                TechStackLink(source: "proj-1", target: "tech-swift", strength: 0.8, techType: "language"),
                TechStackLink(source: "proj-1", target: "tech-swiftui", strength: 0.8, techType: "framework")
            ]
        )

        TechStackGraphWebView(graphData: sampleData) { id, name in
            print("Clicked: \(name)")
        }
    }
}
