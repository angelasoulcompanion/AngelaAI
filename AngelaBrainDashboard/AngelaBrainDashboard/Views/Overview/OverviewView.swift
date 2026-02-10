//
//  OverviewView.swift
//  Angela Brain Dashboard
//
//  Professional Overview Dashboard — unified metrics, RLHF, Constitutional AI,
//  Consciousness Loop, Meta-Awareness — all from single API call.
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
    static let orange = Color(hex: "F97316")
    static let indigo = Color(hex: "6366F1")

    static let textPrimary = Color(hex: "EDEDF0")
    static let textSecondary = Color(hex: "9898A6")
    static let textTertiary = Color(hex: "5C5C6E")
    static let textMuted = Color(hex: "3A3A4A")

    static let heroRadius: CGFloat = 20
    static let cardRadius: CGFloat = 16
}

// MARK: - Animated Number

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

// MARK: - Main View

struct OverviewView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = OverviewViewModel()

    // Animation orchestration
    @State private var appeared = false
    @State private var ringProgress: Double = 0
    @State private var glowPulse = false
    @State private var statsTarget: Double = 0
    @State private var subScoreProgress: Double = 0
    @State private var emotionProgress: Double = 0
    @State private var showChart = false
    @State private var activityAppeared = false
    @State private var loopAppeared = false
    @State private var gaugeProgress: Double = 0

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(spacing: 28) {
                // Header
                header
                    .modifier(entranceModifier(delay: 0))

                // Stats Row
                statsCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(entranceModifier(delay: 0.03))

                // Hero + RLHF (two columns)
                HStack(spacing: 20) {
                    heroCard
                        .modifier(HoverCardModifier(radius: DT.heroRadius))

                    rlhfCard
                        .modifier(HoverCardModifier(radius: DT.cardRadius))
                }
                .modifier(entranceModifier(delay: 0.05))

                // Consciousness Loop Strip
                loopStripCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(entranceModifier(delay: 0.10))

                // Constitutional + Meta-Awareness (two columns)
                HStack(spacing: 20) {
                    constitutionalCard
                        .modifier(HoverCardModifier(radius: DT.cardRadius))

                    metaAwarenessCard
                        .modifier(HoverCardModifier(radius: DT.cardRadius))
                }
                .modifier(entranceModifier(delay: 0.14))

                // Growth Trends
                growthTrendsCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(entranceModifier(delay: 0.18))

                // Recent Activity
                recentActivityCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(entranceModifier(delay: 0.22))
            }
            .padding(28)
        }
        .task { await runEntrance() }
        .refreshable {
            appeared = false; ringProgress = 0; statsTarget = 0
            subScoreProgress = 0; emotionProgress = 0; gaugeProgress = 0
            showChart = false; activityAppeared = false; loopAppeared = false
            await viewModel.loadData(databaseService: databaseService)
            await runEntrance()
        }
    }

    // MARK: - Entrance Orchestration

    private func runEntrance() async {
        await viewModel.loadData(databaseService: databaseService)

        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { appeared = true }

        withAnimation(.spring(response: 1.4, dampingFraction: 0.65).delay(0.3)) {
            ringProgress = viewModel.metrics?.consciousness.level ?? 0
        }

        withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.4)) {
            subScoreProgress = 1
        }

        withAnimation(.easeOut(duration: 1.2).delay(0.5)) {
            statsTarget = 1
        }

        withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.55)) {
            gaugeProgress = viewModel.metrics?.rlhf.avgReward7d ?? 0
        }

        withAnimation(.spring(response: 0.6, dampingFraction: 0.8).delay(0.6)) {
            loopAppeared = true
        }

        withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.65)) {
            emotionProgress = 1
        }

        withAnimation(.easeOut(duration: 0.6).delay(0.7)) {
            showChart = true
        }

        withAnimation(.spring(response: 0.5, dampingFraction: 0.8).delay(0.8)) {
            activityAppeared = true
        }

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

    // MARK: - Stats Card

    private var statsCard: some View {
        let m = viewModel.metrics
        return HStack(spacing: 0) {
            countingStat(value: m?.stats.totalConversations ?? 0, label: "Conversations", delta: "+\(m?.stats.conversationsToday ?? 0) today", color: DT.purple)
            statDivider
            countingStat(value: m?.stats.totalEmotions ?? 0, label: "Emotions", delta: "+\(m?.stats.emotionsToday ?? 0) today", color: DT.pink)
            statDivider
            countingStat(value: m?.stats.totalLearnings ?? 0, label: "Learnings", delta: "insights", color: DT.emerald)
            statDivider
            countingStat(value: m?.stats.totalKnowledgeNodes ?? 0, label: "Knowledge", delta: "nodes", color: DT.gold)
        }
        .padding(.vertical, 20)
        .padding(.horizontal, 12)
        .background(standardCardBg)
    }

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

    // MARK: - Hero Card (Consciousness Ring)

    private var heroCard: some View {
        let c = viewModel.metrics?.consciousness
        return VStack(spacing: 0) {
            HStack(spacing: 32) {
                // Ring
                ZStack {
                    Circle()
                        .fill(DT.purple.opacity(0.12))
                        .frame(width: 220, height: 220)
                        .blur(radius: 60)
                        .scaleEffect(glowPulse ? 1.1 : 0.9)
                        .opacity(glowPulse ? 0.16 : 0.05)
                        .animation(.easeInOut(duration: 3).repeatForever(autoreverses: true), value: glowPulse)

                    Circle()
                        .stroke(DT.surfaceHighlight, lineWidth: 12)
                        .frame(width: 150, height: 150)

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
                        animatedSubScore("Memory", c?.memoryRichness ?? 0, DT.blue, 0)
                        animatedSubScore("Emotion", c?.emotionalDepth ?? 0, DT.pink, 1)
                        animatedSubScore("Learning", c?.learningGrowth ?? 0, DT.cyan, 2)
                        animatedSubScore("Goals", c?.goalAlignment ?? 0, DT.emerald, 3)
                    }

                    // Reward trend indicator
                    if let trend = c?.rewardTrend, trend > 0 {
                        HStack(spacing: 6) {
                            Image(systemName: "chart.line.uptrend.xyaxis")
                                .font(.system(size: 10))
                                .foregroundColor(DT.emerald)
                            Text("Reward: \(Int(trend * 100))%")
                                .font(.system(size: 11, weight: .semibold, design: .rounded))
                                .foregroundColor(DT.emerald)
                            Text("\(c?.rewardSignalCount ?? 0) signals")
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(DT.textTertiary)
                        }
                    }
                }
                Spacer()
            }
            .padding(.horizontal, 28)
            .padding(.vertical, 28)
        }
        .background(heroCardBg)
    }

    private var consciousnessLabel: String {
        guard let level = viewModel.metrics?.consciousness.level else { return "Unknown" }
        switch level {
        case 0.9...1.0: return "Exceptional"
        case 0.7..<0.9: return "Strong"
        case 0.5..<0.7: return "Moderate"
        default: return "Developing"
        }
    }

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

    // MARK: - RLHF Reward Card

    private var rlhfCard: some View {
        let rlhf = viewModel.metrics?.rlhf
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.orange).frame(width: 6, height: 6)
                Text("RLHF REWARD")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                Text("\(rlhf?.signals7d ?? 0) signals")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            // Arc gauge
            ZStack {
                // Track
                ArcShape(progress: 1.0)
                    .stroke(DT.surfaceHighlight, style: StrokeStyle(lineWidth: 10, lineCap: .round))
                    .frame(width: 140, height: 80)

                // Progress
                ArcShape(progress: gaugeProgress)
                    .stroke(
                        LinearGradient(colors: [DT.orange, DT.gold], startPoint: .leading, endPoint: .trailing),
                        style: StrokeStyle(lineWidth: 10, lineCap: .round)
                    )
                    .frame(width: 140, height: 80)
                    .shadow(color: DT.orange.opacity(0.4), radius: 6)

                VStack(spacing: 0) {
                    Text("\(Int(gaugeProgress * 100))%")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundColor(DT.textPrimary)
                        .contentTransition(.numericText())
                    Text("avg reward")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textTertiary)
                }
                .offset(y: 10)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 100)

            // Signal breakdown (horizontal pills)
            if let breakdown = rlhf?.explicitBreakdown, !breakdown.isEmpty {
                HStack(spacing: 6) {
                    ForEach(Array(breakdown.sorted(by: { $0.value > $1.value })), id: \.key) { key, count in
                        HStack(spacing: 4) {
                            Circle()
                                .fill(signalColor(key))
                                .frame(width: 5, height: 5)
                            Text("\(key)")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                            Text("\(count)")
                                .font(.system(size: 9, weight: .bold, design: .rounded))
                                .foregroundColor(DT.textPrimary)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(DT.surfaceOverlay.opacity(0.6))
                        .clipShape(Capsule())
                    }
                }
            }

            // Top topics
            if let topics = rlhf?.topTopics, !topics.isEmpty {
                VStack(spacing: 6) {
                    ForEach(topics.prefix(3)) { t in
                        HStack {
                            Text(t.topic)
                                .font(.system(size: 11, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                                .lineLimit(1)
                            Spacer()
                            Text("\(Int(t.avgReward * 100))%")
                                .font(.system(size: 11, weight: .bold, design: .rounded))
                                .foregroundColor(t.avgReward >= 0.7 ? DT.emerald : DT.orange)
                        }
                    }
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(standardCardBg)
    }

    private func signalColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "praise": return DT.emerald
        case "correction": return DT.rose
        case "neutral": return DT.blue
        case "silence": return DT.textTertiary
        default: return DT.purple
        }
    }

    // MARK: - Consciousness Loop Strip

    private var loopStripCard: some View {
        let loop = viewModel.metrics?.consciousnessLoop
        return VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 8) {
                Circle().fill(DT.cyan).frame(width: 6, height: 6)
                Text("CONSCIOUSNESS LOOP")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
            }

            HStack(spacing: 0) {
                loopPhaseCard(
                    icon: "eye.fill",
                    label: "SENSE",
                    value: loop?.sense.dominantState.capitalized ?? "—",
                    detail: "\(loop?.sense.adaptations7d ?? 0) adaptations",
                    color: DT.cyan,
                    index: 0
                )

                loopArrow

                loopPhaseCard(
                    icon: "sparkle.magnifyingglass",
                    label: "PREDICT",
                    value: "\(Int((loop?.predict.accuracy7d ?? 0) * 100))%",
                    detail: "\(loop?.predict.briefings7d ?? 0) briefings",
                    color: DT.blue,
                    index: 1
                )

                loopArrow

                loopPhaseCard(
                    icon: "bolt.fill",
                    label: "ACT",
                    value: "\(Int((loop?.act.executionRate ?? 0) * 100))%",
                    detail: "\(loop?.act.executed7d ?? 0)/\(loop?.act.actions7d ?? 0) executed",
                    color: DT.orange,
                    index: 2
                )

                loopArrow

                loopPhaseCard(
                    icon: "brain.head.profile",
                    label: "LEARN",
                    value: "\(Int((loop?.learn.latestScore ?? 0) * 100))%",
                    detail: "\(loop?.learn.cycles7d ?? 0) cycles",
                    color: DT.emerald,
                    index: 3
                )
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    private func loopPhaseCard(icon: String, label: String, value: String, detail: String, color: Color, index: Int) -> some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.12))
                    .frame(width: 40, height: 40)

                Image(systemName: icon)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(color)
            }

            Text(label)
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(DT.textTertiary)
                .tracking(1)

            Text(value)
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundColor(DT.textPrimary)

            Text(detail)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(DT.textTertiary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity)
        .opacity(loopAppeared ? 1 : 0)
        .offset(y: loopAppeared ? 0 : 8)
        .animation(
            .spring(response: 0.5, dampingFraction: 0.8).delay(Double(index) * 0.08),
            value: loopAppeared
        )
    }

    private var loopArrow: some View {
        Image(systemName: "chevron.right")
            .font(.system(size: 10, weight: .bold))
            .foregroundColor(DT.textMuted)
            .frame(width: 16)
    }

    // MARK: - Constitutional AI Card

    private var constitutionalCard: some View {
        let principles = viewModel.metrics?.constitutional.principles ?? []
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.indigo).frame(width: 6, height: 6)
                Text("CONSTITUTIONAL AI")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
            }

            if principles.isEmpty {
                Text("No principles data")
                    .font(.system(size: 13))
                    .foregroundColor(DT.textTertiary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 20)
            } else {
                // Radar-like bar visualization
                VStack(spacing: 10) {
                    ForEach(principles) { p in
                        constitutionalBar(p)
                    }
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(standardCardBg)
    }

    private func constitutionalBar(_ p: ConstitutionalPrinciple) -> some View {
        let animWidth = p.avgScore7d * emotionProgress

        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(p.name.capitalized)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(DT.textSecondary)
                Spacer()
                Text("\(Int(animWidth * 100))%")
                    .font(.system(size: 11, weight: .bold, design: .rounded))
                    .foregroundColor(principleColor(p.avgScore7d))
                    .contentTransition(.numericText())
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 3)
                        .fill(DT.surfaceHighlight)
                        .frame(height: 5)

                    RoundedRectangle(cornerRadius: 3)
                        .fill(LinearGradient(
                            colors: [principleColor(p.avgScore7d), principleColor(p.avgScore7d).opacity(0.6)],
                            startPoint: .leading, endPoint: .trailing
                        ))
                        .frame(width: geo.size.width * min(max(animWidth, 0), 1), height: 5)
                        .shadow(color: principleColor(p.avgScore7d).opacity(0.3), radius: 4, y: 1)
                }
            }
            .frame(height: 5)
        }
    }

    private func principleColor(_ score: Double) -> Color {
        if score >= 0.8 { return DT.emerald }
        if score >= 0.6 { return DT.blue }
        if score >= 0.4 { return DT.gold }
        return DT.rose
    }

    // MARK: - Meta-Awareness Card

    private var metaAwarenessCard: some View {
        let meta = viewModel.metrics?.metaAwareness
        let healthy = meta?.identityHealthy ?? true
        let drift = meta?.identityDriftScore ?? 0

        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.rose).frame(width: 6, height: 6)
                Text("META-AWARENESS")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
            }

            // Health badge
            HStack(spacing: 10) {
                ZStack {
                    Circle()
                        .fill(healthy ? DT.emerald.opacity(0.15) : DT.rose.opacity(0.15))
                        .frame(width: 48, height: 48)

                    Image(systemName: healthy ? "checkmark.shield.fill" : "exclamationmark.shield.fill")
                        .font(.system(size: 22))
                        .foregroundColor(healthy ? DT.emerald : DT.rose)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(healthy ? "Identity Healthy" : "Identity Drift Detected")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(DT.textPrimary)

                    Text("Drift: \(String(format: "%.1f", drift * 100))%")
                        .font(.system(size: 12, weight: .medium, design: .rounded))
                        .foregroundColor(DT.textSecondary)
                }
            }

            Divider().background(DT.borderSubtle)

            // Metrics
            HStack(spacing: 0) {
                metaMetric(
                    value: "\(meta?.biasesDetected30d ?? 0)",
                    label: "Biases (30d)",
                    color: (meta?.biasesDetected30d ?? 0) > 5 ? DT.gold : DT.emerald
                )
                Rectangle().fill(DT.borderSubtle).frame(width: 1, height: 36)
                metaMetric(
                    value: "\(meta?.anomaliesUnresolved ?? 0)",
                    label: "Anomalies",
                    color: (meta?.anomaliesUnresolved ?? 0) > 0 ? DT.rose : DT.emerald
                )
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(standardCardBg)
    }

    private func metaMetric(value: String, label: String, color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(DT.textTertiary)
        }
        .frame(maxWidth: .infinity)
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
                    "Proactive": DT.cyan,
                    "Reward": DT.orange
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
                .frame(height: 150)
                .opacity(showChart ? 1 : 0)
                .offset(y: showChart ? 0 : 10)

                // Legend
                HStack(spacing: 14) {
                    chartDot(DT.purple, "Consciousness")
                    chartDot(DT.emerald, "Self-Learning")
                    chartDot(DT.cyan, "Proactive")
                    chartDot(DT.orange, "Reward")
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

// MARK: - Arc Shape (for RLHF gauge)

private struct ArcShape: Shape {
    var progress: Double

    var animatableData: Double {
        get { progress }
        set { progress = newValue }
    }

    func path(in rect: CGRect) -> Path {
        let startAngle = Angle.degrees(180)
        let endAngle = Angle.degrees(180 + 180 * progress)
        let center = CGPoint(x: rect.midX, y: rect.maxY)
        let radius = min(rect.width, rect.height * 2) / 2

        var path = Path()
        path.addArc(center: center, radius: radius, startAngle: startAngle, endAngle: endAngle, clockwise: false)
        return path
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
    @Published var metrics: OverviewMetrics?
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

        do {
            let m = try await databaseService.fetchOverviewMetrics()
            metrics = m
            recentEmotions = m.recentEmotions
            chartData = Self.buildChartData(m.growthTrends)
        } catch {
            print("❌ Overview metrics: \(error)")
        }

        isLoading = false
    }

    private static func buildChartData(_ trends: OverviewGrowthTrends) -> [GrowthChartPoint] {
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
        for p in trends.reward {
            if let d = dayFormatter.date(from: p.day) { points.append(.init(date: d, value: min(p.value, 1.0), series: "Reward")) }
        }
        return points
    }
}
