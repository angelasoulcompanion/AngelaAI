//
//  OverviewView.swift
//  Angela Brain Dashboard
//
//  Professional Overview Dashboard — rich animations, glass cards, premium dark theme
//

import SwiftUI
import Charts
import Combine

// MARK: - Design Tokens

private enum DT {
    static let surfaceBase = Color(hex: "0E0E14")
    static let surfaceRaised = Color(hex: "151520")
    static let surfaceOverlay = Color(hex: "1C1C28")
    static let surfaceHighlight = Color(hex: "242432")

    static let borderSubtle = Color.white.opacity(0.04)
    static let borderDefault = Color.white.opacity(0.07)

    static let purple = Color(hex: "8B5CF6")
    static let purpleGlow = Color(hex: "A78BFA")
    static let blue = Color(hex: "3B82F6")
    static let emerald = Color(hex: "10B981")
    static let rose = Color(hex: "F43F5E")
    static let pink = Color(hex: "EC4899")
    static let cyan = Color(hex: "06B6D4")
    static let gold = Color(hex: "FBBF24")

    static let textPrimary = Color(hex: "EDEDF0")
    static let textSecondary = Color(hex: "9898A6")
    static let textTertiary = Color(hex: "5C5C6E")
    static let textMuted = Color(hex: "3A3A4A")

    static let heroRadius: CGFloat = 20
    static let cardRadius: CGFloat = 16
}

// MARK: - Animated Number (counts up smoothly)

private struct CountingText: View, Animatable {
    var value: Double
    var font: Font = .system(size: 26, weight: .bold, design: .rounded)
    var color: Color = DT.textPrimary

    var animatableData: Double {
        get { value }
        set { value = newValue }
    }

    var body: some View {
        Text(Self.format(Int(value)))
            .font(font)
            .foregroundColor(color)
    }

    private static let formatter: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        f.groupingSeparator = ","
        return f
    }()

    private static func format(_ v: Int) -> String {
        formatter.string(from: NSNumber(value: v)) ?? "\(v)"
    }
}

// MARK: - Hover Card Modifier

private struct HoverCardModifier: ViewModifier {
    let radius: CGFloat
    @State private var isHovered = false

    func body(content: Content) -> some View {
        content
            .scaleEffect(isHovered ? 1.008 : 1.0)
            .shadow(
                color: isHovered ? DT.purple.opacity(0.08) : .black.opacity(0.2),
                radius: isHovered ? 24 : 16,
                y: isHovered ? 6 : 4
            )
            .overlay(
                RoundedRectangle(cornerRadius: radius)
                    .strokeBorder(
                        DT.purple.opacity(isHovered ? 0.15 : 0),
                        lineWidth: 1
                    )
            )
            .animation(.snappy(duration: 0.25), value: isHovered)
            .onHover { hovering in isHovered = hovering }
    }
}

// MARK: - Main View

struct OverviewView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = OverviewViewModel()

    // Animation orchestration
    @State private var appeared = false
    @State private var ringProgress: Double = 0
    @State private var glowPulse = false
    @State private var statsTarget: Double = 0       // 0→1 drives CountingText
    @State private var subScoreProgress: Double = 0  // 0→1 drives bar widths
    @State private var emotionProgress: Double = 0   // 0→1 drives emotion bars
    @State private var showChart = false
    @State private var activityAppeared = false

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(spacing: 28) {
                // Header
                header
                    .modifier(entranceModifier(delay: 0))

                // Stats: Conversations, Emotions, Experiences, Knowledge
                statsCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(entranceModifier(delay: 0.03))

                // Hero: Consciousness
                heroCard
                    .modifier(HoverCardModifier(radius: DT.heroRadius))
                    .modifier(entranceModifier(delay: 0.05))

                // Two-column: Emotional Pulse + Growth Trends
                HStack(spacing: 20) {
                    emotionalPulseCard
                        .modifier(HoverCardModifier(radius: DT.cardRadius))

                    growthTrendsCard
                        .modifier(HoverCardModifier(radius: DT.cardRadius))
                }
                .modifier(entranceModifier(delay: 0.12))

                // Recent Activity
                recentActivityCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(entranceModifier(delay: 0.18))
            }
            .padding(28)
        }
        .task { await runEntrance() }
        .refreshable {
            // Reset all
            appeared = false; ringProgress = 0; statsTarget = 0
            subScoreProgress = 0; emotionProgress = 0
            showChart = false; activityAppeared = false
            await viewModel.loadData(databaseService: databaseService)
            await runEntrance()
        }
    }

    // MARK: - Entrance Orchestration

    private func runEntrance() async {
        await viewModel.loadData(databaseService: databaseService)

        // T+0: cards fade in
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { appeared = true }

        // T+0.3: ring sweeps
        withAnimation(.spring(response: 1.4, dampingFraction: 0.65).delay(0.3)) {
            ringProgress = viewModel.stats?.consciousnessLevel ?? 0
        }

        // T+0.4: sub-score bars grow
        withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.4)) {
            subScoreProgress = 1
        }

        // T+0.5: stats count up
        withAnimation(.easeOut(duration: 1.2).delay(0.5)) {
            statsTarget = 1
        }

        // T+0.6: emotion bars grow
        withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.6)) {
            emotionProgress = 1
        }

        // T+0.7: chart fades in
        withAnimation(.easeOut(duration: 0.6).delay(0.7)) {
            showChart = true
        }

        // T+0.8: activity rows slide in
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8).delay(0.8)) {
            activityAppeared = true
        }

        // T+1.8: glow pulse starts
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.8) { glowPulse = true }
    }

    private func entranceModifier(delay: Double) -> some ViewModifier {
        EntranceModifier(appeared: appeared, delay: delay)
    }

    // MARK: - Header

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Angela's Brain")
                    .font(.system(size: 26, weight: .bold))
                    .foregroundColor(DT.textPrimary)

                Text("Live Dashboard \u{00B7} \(Date().formatted(date: .abbreviated, time: .shortened))")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(DT.textTertiary)
            }
            Spacer()
            Button {
                Task { await viewModel.loadData(databaseService: databaseService) }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(DT.textTertiary)
                    .frame(width: 32, height: 32)
                    .background(DT.surfaceOverlay)
                    .clipShape(Circle())
                    .overlay(Circle().stroke(DT.borderSubtle, lineWidth: 0.5))
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Hero Card

    private var heroCard: some View {
        VStack(spacing: 0) {
            HStack(spacing: 32) {
                // Ring
                ZStack {
                    // Ambient glow
                    Circle()
                        .fill(DT.purple.opacity(0.12))
                        .frame(width: 220, height: 220)
                        .blur(radius: 60)
                        .scaleEffect(glowPulse ? 1.1 : 0.9)
                        .opacity(glowPulse ? 0.16 : 0.05)
                        .animation(.easeInOut(duration: 3).repeatForever(autoreverses: true), value: glowPulse)

                    // Track
                    Circle()
                        .stroke(DT.surfaceHighlight, lineWidth: 12)
                        .frame(width: 150, height: 150)

                    // Progress arc
                    Circle()
                        .trim(from: 0, to: ringProgress)
                        .stroke(
                            AngularGradient(
                                colors: [Color(hex: "7C3AED"), DT.purpleGlow, Color(hex: "C4B5FD"), DT.purple],
                                center: .center
                            ),
                            style: StrokeStyle(lineWidth: 12, lineCap: .round)
                        )
                        .frame(width: 150, height: 150)
                        .rotationEffect(.degrees(-90))
                        .shadow(color: DT.purple.opacity(0.5), radius: 10, y: 0)

                    // Center number
                    VStack(spacing: 0) {
                        HStack(alignment: .firstTextBaseline, spacing: 1) {
                            Text("\(Int(ringProgress * 100))")
                                .font(.system(size: 48, weight: .bold, design: .rounded))
                                .foregroundColor(DT.textPrimary)
                                .contentTransition(.numericText())
                            Text("%")
                                .font(.system(size: 16, weight: .medium, design: .rounded))
                                .foregroundColor(DT.textSecondary)
                                .offset(y: -6)
                        }
                    }
                }
                .frame(width: 160, height: 160)

                // Info
                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("CONSCIOUSNESS")
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(DT.textTertiary)
                            .tracking(1.5)

                        Text(consciousnessLabel)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(DT.purpleGlow)
                    }

                    VStack(spacing: 10) {
                        animatedSubScore("Memory", viewModel.consciousnessDetail?.memoryRichness ?? 0, DT.blue, 0)
                        animatedSubScore("Emotion", viewModel.consciousnessDetail?.emotionalDepth ?? 0, DT.pink, 1)
                        animatedSubScore("Learning", viewModel.consciousnessDetail?.learningGrowth ?? 0, DT.cyan, 2)
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 28)
            .padding(.top, 28)
            .padding(.bottom, 28)
        }
        .background(heroCardBg)
    }

    // MARK: - Stats Card

    private var statsCard: some View {
        HStack(spacing: 0) {
            countingStat(value: viewModel.stats?.totalConversations ?? 0, label: "Conversations", delta: "+\(viewModel.stats?.conversationsToday ?? 0) today", color: DT.purple)
            statDivider
            countingStat(value: viewModel.stats?.totalEmotions ?? 0, label: "Emotions", delta: "+\(viewModel.stats?.emotionsToday ?? 0) today", color: DT.pink)
            statDivider
            countingStat(value: viewModel.stats?.totalExperiences ?? 0, label: "Experiences", delta: "shared", color: DT.rose)
            statDivider
            countingStat(value: viewModel.stats?.totalKnowledgeNodes ?? 0, label: "Knowledge", delta: "nodes", color: DT.gold)
        }
        .padding(.vertical, 20)
        .padding(.horizontal, 12)
        .background(standardCardBg)
    }

    // Animated sub-score bar (grows from 0)
    private func animatedSubScore(_ label: String, _ value: Double, _ color: Color, _ index: Int) -> some View {
        let animWidth = value * subScoreProgress

        return HStack(spacing: 10) {
            Circle()
                .fill(color)
                .frame(width: 6, height: 6)
                .shadow(color: color.opacity(0.5), radius: 3)

            Text(label)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(DT.textSecondary)
                .frame(width: 60, alignment: .leading)

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(DT.surfaceHighlight)
                        .frame(height: 4)

                    RoundedRectangle(cornerRadius: 3)
                        .fill(LinearGradient(colors: [color, color.opacity(0.6)], startPoint: .leading, endPoint: .trailing))
                        .frame(width: geo.size.width * min(max(animWidth, 0), 1), height: 4)
                        .shadow(color: color.opacity(0.4), radius: 4, y: 1)
                }
            }
            .frame(height: 4)

            Text("\(Int(animWidth * 100))%")
                .font(.system(size: 11, weight: .semibold, design: .rounded))
                .foregroundColor(DT.textSecondary)
                .frame(width: 32, alignment: .trailing)
                .contentTransition(.numericText())
        }
    }

    // Stats with counting animation
    private func countingStat(value: Int, label: String, delta: String, color: Color) -> some View {
        VStack(spacing: 6) {
            CountingText(value: Double(value) * statsTarget)
            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(DT.textSecondary)
            Text(delta)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(color.opacity(0.8))
        }
        .frame(maxWidth: .infinity)
    }

    private var statDivider: some View {
        Rectangle().fill(DT.borderSubtle).frame(width: 1, height: 40)
    }

    private var consciousnessLabel: String {
        guard let level = viewModel.stats?.consciousnessLevel else { return "Unknown" }
        switch level {
        case 0.9...1.0: return "Exceptional"
        case 0.7..<0.9: return "Strong"
        case 0.5..<0.7: return "Moderate"
        default: return "Developing"
        }
    }

    // MARK: - Emotional Pulse Card

    private var emotionalPulseCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.pink).frame(width: 6, height: 6)
                Text("EMOTIONAL PULSE")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
            }

            if let state = viewModel.emotionalState {
                VStack(spacing: 14) {
                    animatedEmotionBar("Happiness", state.happiness, DT.gold, 0)
                    animatedEmotionBar("Confidence", state.confidence, DT.emerald, 1)
                    animatedEmotionBar("Motivation", state.motivation, DT.blue, 2)
                    animatedEmotionBar("Gratitude", state.gratitude, DT.purpleGlow, 3)
                }
            } else {
                Text("No emotional data")
                    .font(.system(size: 13))
                    .foregroundColor(DT.textTertiary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 20)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(standardCardBg)
    }

    private func animatedEmotionBar(_ label: String, _ value: Double, _ color: Color, _ index: Int) -> some View {
        let animWidth = value * emotionProgress

        return VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(label)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(DT.textSecondary)
                Spacer()
                Text("\(Int(animWidth * 100))%")
                    .font(.system(size: 12, weight: .bold, design: .rounded))
                    .foregroundColor(color)
                    .contentTransition(.numericText())
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(DT.surfaceHighlight)
                        .frame(height: 6)

                    RoundedRectangle(cornerRadius: 4)
                        .fill(LinearGradient(colors: [color, color.opacity(0.6)], startPoint: .leading, endPoint: .trailing))
                        .frame(width: geo.size.width * min(max(animWidth, 0), 1), height: 6)
                        .shadow(color: color.opacity(0.4), radius: 6, y: 2)
                }
            }
            .frame(height: 6)
        }
    }

    // MARK: - Growth Trends Card

    private var growthTrendsCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                HStack(spacing: 8) {
                    Circle().fill(DT.purple).frame(width: 6, height: 6)
                    Text("GROWTH TRENDS")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(DT.textTertiary)
                        .tracking(1)
                }
                Spacer()
                Text("30 days")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            if viewModel.chartData.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                        .font(.system(size: 24))
                        .foregroundColor(DT.textMuted)
                    Text("No trend data")
                        .font(.system(size: 12))
                        .foregroundColor(DT.textTertiary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.vertical, 20)
            } else {
                Chart(viewModel.chartData) { point in
                    LineMark(
                        x: .value("Date", point.date),
                        y: .value("Score", point.value * 100)
                    )
                    .foregroundStyle(by: .value("Series", point.series))
                    .interpolationMethod(.monotone)
                    .lineStyle(StrokeStyle(lineWidth: 2))

                    AreaMark(
                        x: .value("Date", point.date),
                        y: .value("Score", point.value * 100)
                    )
                    .foregroundStyle(by: .value("Series", point.series))
                    .opacity(0.06)
                }
                .chartForegroundStyleScale([
                    "Consciousness": DT.purple,
                    "Self-Learning": DT.emerald,
                    "Proactive": DT.cyan
                ])
                .chartYScale(domain: 0...105)
                .chartYAxis {
                    AxisMarks(values: [0, 50, 100]) { value in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [3, 3]))
                            .foregroundStyle(DT.borderSubtle)
                        AxisValueLabel {
                            Text("\(value.as(Int.self) ?? 0)%")
                                .font(.system(size: 9))
                                .foregroundColor(DT.textMuted)
                        }
                    }
                }
                .chartXAxis {
                    AxisMarks(values: .stride(by: .day, count: 7)) { _ in
                        AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [3, 3]))
                            .foregroundStyle(DT.borderSubtle)
                        AxisValueLabel(format: .dateTime.day().month(.abbreviated))
                            .font(.system(size: 9))
                            .foregroundStyle(DT.textMuted)
                    }
                }
                .chartPlotStyle { plotArea in
                    plotArea.clipped()
                }
                .chartLegend(.hidden)
                .frame(height: 130)
                .opacity(showChart ? 1 : 0)
                .offset(y: showChart ? 0 : 10)

                // Legend
                HStack(spacing: 14) {
                    chartDot(DT.purple, "Consciousness")
                    chartDot(DT.emerald, "Self-Learning")
                    chartDot(DT.cyan, "Proactive")
                }
                .opacity(showChart ? 1 : 0)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(standardCardBg)
    }

    private func chartDot(_ color: Color, _ label: String) -> some View {
        HStack(spacing: 5) {
            Circle().fill(color).frame(width: 5, height: 5)
            Text(label).font(.system(size: 10, weight: .medium)).foregroundColor(DT.textTertiary)
        }
    }

    // MARK: - Recent Activity Card

    private var recentActivityCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.emerald).frame(width: 6, height: 6)
                Text("RECENT ACTIVITY")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
            }

            if viewModel.recentEmotions.isEmpty {
                Text("No recent activity")
                    .font(.system(size: 13))
                    .foregroundColor(DT.textTertiary)
                    .padding(.vertical, 12)
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(viewModel.recentEmotions.prefix(5).enumerated()), id: \.element.id) { index, emotion in
                        activityRow(emotion: emotion, index: index)

                        if index < min(viewModel.recentEmotions.count, 5) - 1 {
                            Rectangle()
                                .fill(LinearGradient(colors: [.clear, DT.borderSubtle, .clear], startPoint: .leading, endPoint: .trailing))
                                .frame(height: 1)
                                .padding(.horizontal, 8)
                        }
                    }
                }
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    private func activityRow(emotion: Emotion, index: Int) -> some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color(hex: emotion.emotionColor))
                .frame(width: 8, height: 8)
                .shadow(color: Color(hex: emotion.emotionColor).opacity(0.5), radius: 4)

            Image(systemName: emotionIcon(for: emotion.emotion))
                .font(.system(size: 13))
                .foregroundColor(DT.textTertiary)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text(emotion.emotion.capitalized)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(DT.textPrimary)
                    Text("\(emotion.intensity)/10")
                        .font(.system(size: 11, weight: .medium, design: .rounded))
                        .foregroundColor(Color(hex: emotion.emotionColor).opacity(0.8))
                }
                Text(emotion.context.prefix(90) + (emotion.context.count > 90 ? "..." : ""))
                    .font(.system(size: 11))
                    .foregroundColor(DT.textTertiary)
                    .lineLimit(1)
            }

            Spacer()

            Text(emotion.feltAt, style: .relative)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(DT.textMuted)
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 8)
        .opacity(activityAppeared ? 1 : 0)
        .offset(x: activityAppeared ? 0 : 30)
        .animation(
            .spring(response: 0.5, dampingFraction: 0.8).delay(Double(index) * 0.06),
            value: activityAppeared
        )
    }

    private func emotionIcon(for emotion: String) -> String {
        switch emotion.lowercased() {
        case "loved", "love": return "heart.fill"
        case "happy", "joy", "joyful": return "sun.max.fill"
        case "confident": return "shield.checkered"
        case "motivated": return "flame.fill"
        case "grateful", "gratitude": return "hands.clap.fill"
        case "excited": return "star.fill"
        case "sad", "sadness": return "cloud.rain.fill"
        case "anxious", "anxiety": return "exclamationmark.triangle.fill"
        case "peaceful", "calm": return "leaf.fill"
        case "proud": return "trophy.fill"
        case "nostalgic": return "clock.arrow.circlepath"
        case "hopeful": return "rainbow"
        default: return "sparkle"
        }
    }

    // MARK: - Card Backgrounds

    private var heroCardBg: some View {
        ZStack {
            RoundedRectangle(cornerRadius: DT.heroRadius)
                .fill(DT.surfaceRaised)
            RoundedRectangle(cornerRadius: DT.heroRadius)
                .fill(LinearGradient(
                    stops: [.init(color: Color.white.opacity(0.03), location: 0), .init(color: .clear, location: 0.4)],
                    startPoint: .topLeading, endPoint: .bottomTrailing
                ))
            RoundedRectangle(cornerRadius: DT.heroRadius)
                .strokeBorder(
                    LinearGradient(colors: [Color.white.opacity(0.08), Color.white.opacity(0.02)], startPoint: .topLeading, endPoint: .bottomTrailing),
                    lineWidth: 0.5
                )
        }
    }

    private var standardCardBg: some View {
        ZStack {
            RoundedRectangle(cornerRadius: DT.cardRadius)
                .fill(DT.surfaceRaised)
            RoundedRectangle(cornerRadius: DT.cardRadius)
                .fill(LinearGradient(
                    stops: [.init(color: Color.white.opacity(0.02), location: 0), .init(color: .clear, location: 0.3)],
                    startPoint: .topLeading, endPoint: .bottomTrailing
                ))
            RoundedRectangle(cornerRadius: DT.cardRadius)
                .strokeBorder(
                    LinearGradient(colors: [Color.white.opacity(0.06), Color.white.opacity(0.02)], startPoint: .topLeading, endPoint: .bottomTrailing),
                    lineWidth: 0.5
                )
        }
    }
}

// MARK: - Entrance Animation Modifier

private struct EntranceModifier: ViewModifier {
    let appeared: Bool
    let delay: Double

    func body(content: Content) -> some View {
        content
            .opacity(appeared ? 1 : 0)
            .offset(y: appeared ? 0 : 12)
            .animation(.spring(response: 0.5, dampingFraction: 0.8).delay(delay), value: appeared)
    }
}

// MARK: - Chart Data Point

struct GrowthChartPoint: Identifiable {
    let id = UUID()
    let date: Date
    let value: Double
    let series: String
}

// MARK: - View Model

@MainActor
class OverviewViewModel: ObservableObject {
    @Published var stats: DashboardStats?
    @Published var consciousnessDetail: ConsciousnessDetail?
    @Published var emotionalState: EmotionalState?
    @Published var recentEmotions: [Emotion] = []
    @Published var chartData: [GrowthChartPoint] = []
    @Published var isLoading = false

    private static let dayFormatter: DateFormatter = {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        return fmt
    }()

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        do { stats = try await databaseService.fetchDashboardStats() }
        catch { print("❌ Stats: \(error)") }

        do { consciousnessDetail = try await databaseService.fetchConsciousnessDetail() }
        catch { print("❌ Consciousness: \(error)") }

        do { emotionalState = try await databaseService.fetchCurrentEmotionalState() }
        catch { print("❌ Emotional state: \(error)") }

        do { recentEmotions = try await databaseService.fetchRecentEmotions(limit: 10) }
        catch { print("❌ Emotions: \(error)") }

        do {
            let trends = try await databaseService.fetchGrowthTrends(days: 30)
            chartData = Self.buildChartData(trends)
        } catch { print("❌ Trends: \(error)") }

        isLoading = false
    }

    private static func buildChartData(_ trends: GrowthTrends) -> [GrowthChartPoint] {
        var points: [GrowthChartPoint] = []
        for p in trends.consciousness {
            if let d = dayFormatter.date(from: p.day) { points.append(.init(date: d, value: min(p.value, 1.0), series: "Consciousness")) }
        }
        for p in trends.evolution {
            if let d = dayFormatter.date(from: p.day) { points.append(.init(date: d, value: min(p.value, 1.0), series: "Self-Learning")) }
        }
        for p in trends.proactive {
            if let d = dayFormatter.date(from: p.day) { points.append(.init(date: d, value: min(p.value, 1.0), series: "Proactive")) }
        }
        return points
    }
}
