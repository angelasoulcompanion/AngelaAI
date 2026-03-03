//
//  AIAdvisorView.swift
//  Pythia — AI Portfolio Advisor (Enhanced with LLM + Chat)
//

import SwiftUI

struct AIAdvisorView: View {
    @EnvironmentObject var db: DatabaseService

    @State private var selectedPortfolioId: String?
    @State private var advice: AIAdvisorResponse?
    @State private var isLoading = false
    // Chat
    @State private var chatMessages: [ChatBubble] = []
    @State private var chatInput = ""
    @State private var sessionId: String?
    @State private var isSending = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
                Text("AI Portfolio Advisor")
                    .font(PythiaTheme.title())
                    .foregroundColor(PythiaTheme.textPrimary)

                HStack(spacing: PythiaTheme.spacing) {
                    PortfolioPickerView(selectedId: $selectedPortfolioId)

                    Button("Analyze") { Task { await analyze() } }
                        .pythiaPrimaryButton()
                        .disabled(selectedPortfolioId == nil)

                    Spacer()
                }
                .padding()
                .pythiaCard()

                if isLoading { LoadingView("Analyzing portfolio...") }

                if let a = advice, a.success {
                    adviceCard(a)

                    // LLM Analysis card
                    if let llm = a.llmAnalysis, !llm.isEmpty {
                        llmAnalysisCard(llm, provider: a.llmProvider)
                    }

                    // Chat section
                    chatSection()
                }
            }
            .padding(PythiaTheme.largeSpacing)
        }
        .background(PythiaTheme.backgroundDark)

    }

    private func adviceCard(_ a: AIAdvisorResponse) -> some View {
        VStack(alignment: .leading, spacing: PythiaTheme.spacing) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                    .font(.title2)
                Text(a.portfolio ?? "Portfolio Analysis")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
            }

            HStack(spacing: PythiaTheme.largeSpacing) {
                MetricBox("Diversification", "\(Int((a.diversificationScore ?? 0) * 100))%",
                          (a.diversificationScore ?? 0) > 0.6 ? PythiaTheme.profit : PythiaTheme.warningOrange)
                MetricBox("Holdings", "\(a.holdingsCount ?? 0)", PythiaTheme.secondaryBlue)
                MetricBox("Sectors", "\(a.sectorsCount ?? 0)", PythiaTheme.accentGold)
            }

            PythiaDivider()

            Text("Rule-Based Analysis")
                .font(PythiaTheme.heading())
                .foregroundColor(PythiaTheme.textSecondary)

            ForEach(Array(a.analysis.enumerated()), id: \.offset) { _, item in
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: item.contains("Risk") ? "exclamationmark.triangle" :
                            item.contains("Score") ? "chart.bar" : "lightbulb")
                        .foregroundColor(item.contains("Risk") ? PythiaTheme.warningOrange : PythiaTheme.secondaryBlue)
                        .frame(width: 20)
                    Text(item)
                        .font(PythiaTheme.body())
                        .foregroundColor(PythiaTheme.textPrimary)
                }
                .padding(.vertical, 4)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func llmAnalysisCard(_ analysis: String, provider: String?) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(PythiaTheme.accentGold)
                Text("AI Analysis")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
                Spacer()
                if let p = provider {
                    Text(p.uppercased())
                        .font(PythiaTheme.caption())
                        .foregroundColor(PythiaTheme.accentGold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(PythiaTheme.accentGold.opacity(0.15))
                        .cornerRadius(4)
                }
            }

            Text(analysis)
                .font(PythiaTheme.body())
                .foregroundColor(PythiaTheme.textPrimary)
                .lineSpacing(4)
        }
        .padding()
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(PythiaTheme.accentGold.opacity(0.3), lineWidth: 1)
        )
        .pythiaCard()
    }

    private func chatSection() -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "bubble.left.and.bubble.right.fill")
                    .foregroundColor(PythiaTheme.secondaryBlue)
                Text("Chat with Advisor")
                    .font(PythiaTheme.headline())
                    .foregroundColor(PythiaTheme.textPrimary)
            }

            // Chat messages
            if !chatMessages.isEmpty {
                VStack(spacing: 8) {
                    ForEach(chatMessages) { msg in
                        chatBubble(msg)
                    }
                }
            }

            // Input
            HStack(spacing: 8) {
                TextField("Ask about your portfolio...", text: $chatInput)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { Task { await sendMessage() } }

                Button {
                    Task { await sendMessage() }
                } label: {
                    if isSending {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 30, height: 30)
                    } else {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.title2)
                            .foregroundColor(chatInput.isEmpty ? PythiaTheme.textTertiary : PythiaTheme.secondaryBlue)
                    }
                }
                .disabled(chatInput.isEmpty || isSending || selectedPortfolioId == nil)
                .buttonStyle(.plain)
            }
        }
        .padding()
        .pythiaCard()
    }

    private func chatBubble(_ msg: ChatBubble) -> some View {
        HStack {
            if msg.role == "user" { Spacer() }

            VStack(alignment: msg.role == "user" ? .trailing : .leading, spacing: 4) {
                Text(msg.content)
                    .font(PythiaTheme.body())
                    .foregroundColor(PythiaTheme.textPrimary)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(msg.role == "user"
                        ? PythiaTheme.secondaryBlue.opacity(0.2)
                        : PythiaTheme.surfaceBackground)
                    .cornerRadius(12)
            }

            if msg.role != "user" { Spacer() }
        }
    }

    private func analyze() async {
        guard let pid = selectedPortfolioId else { return }
        isLoading = true
        do {
            advice = try await db.getAIAdvice(portfolioId: pid)
            sessionId = advice?.sessionId
        } catch {}
        isLoading = false
    }

    private func sendMessage() async {
        guard let pid = selectedPortfolioId, !chatInput.isEmpty else { return }
        let message = chatInput
        chatInput = ""
        isSending = true

        // Add user bubble
        chatMessages.append(ChatBubble(role: "user", content: message, timestamp: Date()))

        do {
            let response = try await db.chatWithAdvisor(portfolioId: pid, message: message, sessionId: sessionId)
            sessionId = response.sessionId

            // Add assistant bubble
            let reply = response.llmAnalysis ?? response.analysis.joined(separator: "\n")
            chatMessages.append(ChatBubble(role: "assistant", content: reply, timestamp: Date()))
        } catch {
            chatMessages.append(ChatBubble(role: "assistant", content: "Failed to get response.", timestamp: Date()))
        }

        isSending = false
    }
}
