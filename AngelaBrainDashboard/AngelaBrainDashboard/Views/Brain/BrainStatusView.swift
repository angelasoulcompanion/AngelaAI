//
//  BrainStatusView.swift
//  Angela Brain Dashboard
//
//  Comprehensive Brain Status page — stimuli, thoughts, reflections,
//  expression funnel, migration progress, consolidation, knowledge graph.
//

import SwiftUI
import Charts
import Combine

// MARK: - Design Tokens (local copy — matches OverviewView)

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

    static let cardRadius: CGFloat = 16
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

struct BrainStatusView: View {
    @EnvironmentObject var databaseService: DatabaseService
    @StateObject private var viewModel = BrainStatusViewModel()

    @State private var appeared = false
    @State private var kpiProgress: Double = 0
    @State private var cycleAppeared = false
    @State private var cardsAppeared = false

    var body: some View {
        ScrollView(.vertical, showsIndicators: false) {
            VStack(spacing: 28) {
                // 1. Header
                header
                    .modifier(EntranceModifier(appeared: appeared, delay: 0))

                // 2. KPI Strip
                kpiStripCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.03))

                // 3. Cognitive Cycle
                cognitiveCycleCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.06))

                // 4. Knowledge Graph (moved up — visual centerpiece)
                knowledgeGraphCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.09))

                // 5. Stimuli & Salience
                stimuliCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.12))

                // 6. Thoughts
                thoughtsCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.15))

                // 7. Expression Funnel
                expressionFunnelCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.18))

                // 8. Reflections
                reflectionsCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.21))

                // 9. Brain vs Rule Migration
                migrationCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.24))

                // 10. Memory Consolidation
                consolidationCard
                    .modifier(HoverCardModifier(radius: DT.cardRadius))
                    .modifier(EntranceModifier(appeared: appeared, delay: 0.27))
            }
            .padding(28)
        }
        .task { await runEntrance() }
        .refreshable {
            appeared = false; kpiProgress = 0; cycleAppeared = false; cardsAppeared = false
            await viewModel.loadData(databaseService: databaseService)
            await runEntrance()
        }
    }

    // MARK: - Entrance Orchestration

    private func runEntrance() async {
        await viewModel.loadData(databaseService: databaseService)

        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) { appeared = true }

        withAnimation(.easeOut(duration: 1.0).delay(0.3)) { kpiProgress = 1 }

        withAnimation(.spring(response: 0.6, dampingFraction: 0.8).delay(0.5)) { cycleAppeared = true }

        withAnimation(.spring(response: 0.5, dampingFraction: 0.8).delay(0.6)) { cardsAppeared = true }
    }

    // MARK: - 1. Header

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Brain Status")
                    .font(.system(size: 26, weight: .bold))
                    .foregroundColor(DT.textPrimary)

                Text("Cognitive Architecture \u{00B7} \(Date().formatted(date: .abbreviated, time: .shortened))")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(DT.textTertiary)
            }
            Spacer()
            Button {
                Task {
                    appeared = false; kpiProgress = 0; cycleAppeared = false; cardsAppeared = false
                    await viewModel.loadData(databaseService: databaseService)
                    await runEntrance()
                }
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

    // MARK: - 2. KPI Strip

    private var kpiStripCard: some View {
        let m = viewModel.metrics
        return HStack(spacing: 0) {
            kpiCircle("Stimuli", value: m?.stimuli.total24h ?? 0, subLabel: "24h", color: DT.cyan)
            kpiDivider
            kpiCircle("Thoughts", value: m?.thoughts.total24h ?? 0, subLabel: "24h", color: DT.indigo)
            kpiDivider
            kpiCircle("Reflections", value: m?.reflections.total7d ?? 0, subLabel: "7d", color: DT.pink)
            kpiDivider
            kpiPercentCircle("Expression", pct: expressionRatePct, color: DT.emerald)
            kpiDivider
            kpiPercentCircle("Readiness", pct: m?.migration.readinessPct ?? 0, color: DT.purple)
        }
        .padding(.vertical, 20)
        .padding(.horizontal, 12)
        .background(standardCardBg)
    }

    private var expressionRatePct: Double {
        guard let m = viewModel.metrics else { return 0 }
        let gen = m.expression.generated
        guard gen > 0 else { return 0 }
        return Double(m.expression.totalExpressed) / Double(gen) * 100
    }

    private func kpiCircle(_ label: String, value: Int, subLabel: String, color: Color) -> some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .stroke(DT.surfaceHighlight, lineWidth: 4)
                    .frame(width: 56, height: 56)

                Circle()
                    .trim(from: 0, to: min(kpiProgress * Double(min(value, 100)) / 100.0, 1.0))
                    .stroke(color, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                    .frame(width: 56, height: 56)
                    .rotationEffect(.degrees(-90))

                Text("\(value)")
                    .font(.system(size: 16, weight: .bold, design: .rounded))
                    .foregroundColor(DT.textPrimary)
            }
            Text(label)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(DT.textSecondary)
            Text(subLabel)
                .font(.system(size: 9, weight: .medium))
                .foregroundColor(color.opacity(0.7))
        }
        .frame(maxWidth: .infinity)
    }

    private func kpiPercentCircle(_ label: String, pct: Double, color: Color) -> some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .stroke(DT.surfaceHighlight, lineWidth: 4)
                    .frame(width: 56, height: 56)

                Circle()
                    .trim(from: 0, to: kpiProgress * min(pct / 100.0, 1.0))
                    .stroke(color, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                    .frame(width: 56, height: 56)
                    .rotationEffect(.degrees(-90))

                Text("\(Int(pct))%")
                    .font(.system(size: 14, weight: .bold, design: .rounded))
                    .foregroundColor(DT.textPrimary)
            }
            Text(label)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(DT.textSecondary)
            Text("rate")
                .font(.system(size: 9, weight: .medium))
                .foregroundColor(color.opacity(0.7))
        }
        .frame(maxWidth: .infinity)
    }

    private var kpiDivider: some View {
        Rectangle().fill(DT.borderSubtle).frame(width: 1, height: 56)
    }

    // MARK: - 3. Cognitive Cycle Strip

    private var cognitiveCycleCard: some View {
        let m = viewModel.metrics
        return VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 8) {
                Circle().fill(DT.purple).frame(width: 6, height: 6)
                Text("COGNITIVE CYCLE")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
            }

            HStack(spacing: 0) {
                cyclePhase(icon: "eye.fill", label: "PERCEIVE",
                    value: "\(m?.stimuli.total7d ?? 0)", detail: "stimuli", color: DT.cyan, index: 0)
                cycleArrow
                cyclePhase(icon: "waveform.path", label: "ACTIVATE",
                    value: String(format: "%.2f", m?.stimuli.avgSalience ?? 0), detail: "avg salience", color: DT.blue, index: 1)
                cycleArrow
                cyclePhase(icon: "brain.head.profile", label: "SITUATE",
                    value: "\(m?.thoughts.total7d ?? 0)", detail: "thoughts", color: DT.indigo, index: 2)
                cycleArrow
                cyclePhase(icon: "arrow.triangle.branch", label: "DECIDE",
                    value: "\(m?.expression.generated ?? 0)", detail: "evaluated", color: DT.orange, index: 3)
                cycleArrow
                cyclePhase(icon: "text.bubble.fill", label: "EXPRESS",
                    value: "\(m?.expression.totalExpressed ?? 0)", detail: "expressed", color: DT.emerald, index: 4)
                cycleArrow
                cyclePhase(icon: "sparkles", label: "LEARN",
                    value: "\(m?.reflections.integratedCount ?? 0)", detail: "integrated", color: DT.pink, index: 5)
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    private func cyclePhase(icon: String, label: String, value: String, detail: String, color: Color, index: Int) -> some View {
        VStack(spacing: 6) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.12))
                    .frame(width: 36, height: 36)
                Image(systemName: icon)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(color)
            }
            Text(label)
                .font(.system(size: 8, weight: .bold))
                .foregroundColor(DT.textTertiary)
                .tracking(0.8)
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .foregroundColor(DT.textPrimary)
            Text(detail)
                .font(.system(size: 9, weight: .medium))
                .foregroundColor(DT.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .opacity(cycleAppeared ? 1 : 0)
        .offset(y: cycleAppeared ? 0 : 8)
        .animation(
            .spring(response: 0.5, dampingFraction: 0.8).delay(Double(index) * 0.06),
            value: cycleAppeared
        )
    }

    private var cycleArrow: some View {
        Image(systemName: "chevron.right")
            .font(.system(size: 9, weight: .bold))
            .foregroundColor(DT.textMuted)
            .frame(width: 12)
    }

    // MARK: - 4. Stimuli & Salience Card

    private var stimuliCard: some View {
        let s = viewModel.metrics?.stimuli
        return VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack(spacing: 8) {
                Circle().fill(DT.cyan).frame(width: 6, height: 6)
                Text("STIMULI & SALIENCE")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                Text("\(s?.total7d ?? 0) total \u{00B7} 7d")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            // Two columns: by type chart + salience dims
            HStack(alignment: .top, spacing: 20) {
                // Left: by codelet type bar chart
                VStack(alignment: .leading, spacing: 10) {
                    Text("BY CODELET TYPE")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    if let types = s?.byType, !types.isEmpty {
                        let maxCount = types.map(\.count).max() ?? 1
                        ForEach(types) { t in
                            HStack(spacing: 8) {
                                Text(formatCodeletType(t.type))
                                    .font(.system(size: 10, weight: .medium))
                                    .foregroundColor(DT.textSecondary)
                                    .frame(width: 80, alignment: .leading)
                                    .lineLimit(1)

                                GeometryReader { geo in
                                    RoundedRectangle(cornerRadius: 3)
                                        .fill(DT.cyan.opacity(0.7))
                                        .frame(width: geo.size.width * (Double(t.count) / Double(max(maxCount, 1))))
                                }
                                .frame(height: 12)

                                Text("\(t.count)")
                                    .font(.system(size: 10, weight: .bold, design: .rounded))
                                    .foregroundColor(DT.textPrimary)
                                    .frame(width: 30, alignment: .trailing)
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity)

                // Right: salience dimension breakdown
                VStack(alignment: .leading, spacing: 10) {
                    Text("SALIENCE DIMENSIONS")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    if let dims = s?.salienceDims, !dims.isEmpty {
                        salienceDimensionBar(dims)
                            .padding(.bottom, 4)

                        let dimItems: [(String, String, Color)] = [
                            ("emotional", "Emotional", DT.pink),
                            ("goal_relevance", "Goal", DT.emerald),
                            ("temporal_urgency", "Temporal", DT.orange),
                            ("social_relevance", "Social", DT.blue),
                            ("novelty", "Novelty", DT.purple),
                        ]
                        ForEach(dimItems, id: \.0) { key, label, color in
                            HStack(spacing: 6) {
                                Circle().fill(color).frame(width: 6, height: 6)
                                Text(label)
                                    .font(.system(size: 10, weight: .medium))
                                    .foregroundColor(DT.textTertiary)
                                Spacer()
                                Text(String(format: "%.3f", dims[key] ?? 0))
                                    .font(.system(size: 10, weight: .bold, design: .rounded))
                                    .foregroundColor(DT.textSecondary)
                            }
                        }
                    }
                }
                .frame(maxWidth: .infinity)
            }

            // Top salient stimuli
            if let top = s?.topSalient, !top.isEmpty {
                Rectangle().fill(DT.borderSubtle).frame(height: 1)

                VStack(alignment: .leading, spacing: 8) {
                    Text("TOP SALIENT STIMULI")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    ForEach(top.prefix(5)) { stimulus in
                        HStack(spacing: 8) {
                            Text(String(format: "%.2f", stimulus.salienceScore))
                                .font(.system(size: 11, weight: .bold, design: .rounded))
                                .foregroundColor(stimulus.salienceScore > 0.5 ? DT.cyan : DT.textSecondary)
                                .frame(width: 36)

                            Text(formatCodeletType(stimulus.codeletType))
                                .font(.system(size: 9, weight: .semibold))
                                .foregroundColor(DT.textTertiary)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(DT.surfaceOverlay)
                                .clipShape(Capsule())

                            Text(stimulus.content)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                                .lineLimit(1)

                            Spacer()
                        }
                    }
                }
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - 5. Thoughts Card

    private var thoughtsCard: some View {
        let t = viewModel.metrics?.thoughts
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.indigo).frame(width: 6, height: 6)
                Text("THOUGHTS")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                Text("\(t?.total7d ?? 0) total \u{00B7} 7d")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            // S1 vs S2 + motivation stats
            HStack(spacing: 20) {
                // S1 vs S2 gauge
                VStack(spacing: 12) {
                    Text("SYSTEM 1 vs 2")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    let s1 = t?.system1 ?? 0
                    let s2 = t?.system2 ?? 0
                    let total = max(s1 + s2, 1)

                    HStack(spacing: 0) {
                        VStack(spacing: 2) {
                            Text("\(s1)")
                                .font(.system(size: 24, weight: .bold, design: .rounded))
                                .foregroundColor(DT.blue)
                            Text("System 1")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(DT.textTertiary)
                            Text("fast/template")
                                .font(.system(size: 8, weight: .medium))
                                .foregroundColor(DT.textMuted)
                        }
                        .frame(maxWidth: .infinity)

                        VStack(spacing: 2) {
                            Text("\(s2)")
                                .font(.system(size: 24, weight: .bold, design: .rounded))
                                .foregroundColor(DT.indigo)
                            Text("System 2")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(DT.textTertiary)
                            Text("deep/LLM")
                                .font(.system(size: 8, weight: .medium))
                                .foregroundColor(DT.textMuted)
                        }
                        .frame(maxWidth: .infinity)
                    }

                    // Proportion bar
                    GeometryReader { geo in
                        HStack(spacing: 2) {
                            RoundedRectangle(cornerRadius: 3)
                                .fill(DT.blue)
                                .frame(width: max(geo.size.width * (Double(s1) / Double(total)), 4))
                            RoundedRectangle(cornerRadius: 3)
                                .fill(DT.indigo)
                                .frame(width: max(geo.size.width * (Double(s2) / Double(total)), 4))
                        }
                    }
                    .frame(height: 8)
                }
                .frame(maxWidth: .infinity)

                Rectangle().fill(DT.borderSubtle).frame(width: 1)

                // Motivation stats
                VStack(spacing: 12) {
                    Text("MOTIVATION")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    VStack(spacing: 4) {
                        Text(String(format: "%.0f%%", (t?.avgMotivation ?? 0) * 100))
                            .font(.system(size: 28, weight: .bold, design: .rounded))
                            .foregroundColor(DT.textPrimary)
                        Text("avg motivation")
                            .font(.system(size: 9, weight: .medium))
                            .foregroundColor(DT.textTertiary)
                    }

                    HStack(spacing: 4) {
                        Image(systemName: "flame.fill")
                            .font(.system(size: 10))
                            .foregroundColor(DT.orange)
                        Text("\(t?.highMotivation ?? 0) high (>0.6)")
                            .font(.system(size: 10, weight: .medium))
                            .foregroundColor(DT.textSecondary)
                    }
                }
                .frame(maxWidth: .infinity)
            }

            // Top thoughts
            if let thoughts = t?.topThoughts, !thoughts.isEmpty {
                Rectangle().fill(DT.borderSubtle).frame(height: 1)

                VStack(alignment: .leading, spacing: 8) {
                    Text("TOP THOUGHTS BY MOTIVATION")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    ForEach(thoughts) { thought in
                        HStack(spacing: 8) {
                            // Motivation bar
                            motivationBar(thought.motivation)

                            Image(systemName: thought.type == "system2" ? "brain" : "bolt.fill")
                                .font(.system(size: 10))
                                .foregroundColor(thought.type == "system2" ? DT.indigo : DT.blue)

                            Text(thought.content)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                                .lineLimit(2)

                            Spacer()

                            if let via = thought.expressedVia {
                                Text(via)
                                    .font(.system(size: 8, weight: .semibold))
                                    .foregroundColor(DT.emerald)
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 2)
                                    .background(DT.emerald.opacity(0.12))
                                    .clipShape(Capsule())
                            }
                        }
                    }
                }
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - 6. Expression Funnel Card

    private var expressionFunnelCard: some View {
        let e = viewModel.metrics?.expression
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.emerald).frame(width: 6, height: 6)
                Text("EXPRESSION FUNNEL")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                Text("7d")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            // Funnel visualization
            let generated = e?.generated ?? 0
            let expressed = e?.totalExpressed ?? 0
            let suppressed = e?.suppressedCount ?? 0

            HStack(spacing: 20) {
                // Funnel stages
                VStack(spacing: 12) {
                    funnelStage("Generated", count: generated, maxCount: max(generated, 1), color: DT.textSecondary, icon: "brain.head.profile")
                    funnelStage("Expressed", count: expressed, maxCount: max(generated, 1), color: DT.emerald, icon: "text.bubble.fill")
                    funnelStage("Suppressed", count: suppressed, maxCount: max(generated, 1), color: DT.rose, icon: "xmark.circle")
                }
                .frame(maxWidth: .infinity)

                Rectangle().fill(DT.borderSubtle).frame(width: 1)

                // Channel breakdown + effectiveness
                VStack(spacing: 12) {
                    Text("BY CHANNEL")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    HStack(spacing: 16) {
                        VStack(spacing: 2) {
                            Image(systemName: "paperplane.fill")
                                .font(.system(size: 14))
                                .foregroundColor(DT.blue)
                            Text("\(e?.telegramCount ?? 0)")
                                .font(.system(size: 18, weight: .bold, design: .rounded))
                                .foregroundColor(DT.textPrimary)
                            Text("Telegram")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(DT.textTertiary)
                        }
                        VStack(spacing: 2) {
                            Image(systemName: "bubble.left.fill")
                                .font(.system(size: 14))
                                .foregroundColor(DT.purple)
                            Text("\(e?.chatCount ?? 0)")
                                .font(.system(size: 18, weight: .bold, design: .rounded))
                                .foregroundColor(DT.textPrimary)
                            Text("Chat Queue")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(DT.textTertiary)
                        }
                    }

                    // David's response breakdown
                    if let responses = e?.davidResponses, (responses.positive + responses.neutral + responses.negative) > 0 {
                        Rectangle().fill(DT.borderSubtle).frame(height: 1)

                        Text("DAVID'S RESPONSE")
                            .font(.system(size: 9, weight: .semibold))
                            .foregroundColor(DT.textMuted)
                            .tracking(0.8)

                        HStack(spacing: 8) {
                            responsePill("positive", count: responses.positive, color: DT.emerald)
                            responsePill("neutral", count: responses.neutral, color: DT.textSecondary)
                            responsePill("negative", count: responses.negative, color: DT.rose)
                        }
                    }
                }
                .frame(maxWidth: .infinity)
            }

            // Suppress reasons
            if let reasons = e?.suppressReasons, !reasons.isEmpty {
                Rectangle().fill(DT.borderSubtle).frame(height: 1)

                VStack(alignment: .leading, spacing: 8) {
                    Text("SUPPRESS REASONS")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    HStack(spacing: 6) {
                        ForEach(Array(reasons.sorted(by: { $0.value > $1.value })), id: \.key) { key, count in
                            HStack(spacing: 4) {
                                Text(key)
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
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - 7. Reflections Card

    private var reflectionsCard: some View {
        let r = viewModel.metrics?.reflections
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.pink).frame(width: 6, height: 6)
                Text("REFLECTIONS")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                Text("\(r?.total7d ?? 0) total \u{00B7} \(r?.integratedCount ?? 0) integrated")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            // Type breakdown pills
            if let types = r?.byType, !types.isEmpty {
                HStack(spacing: 8) {
                    ForEach(Array(types.sorted(by: { $0.value > $1.value })), id: \.key) { type, count in
                        HStack(spacing: 4) {
                            Image(systemName: reflectionTypeIcon(type))
                                .font(.system(size: 10))
                                .foregroundColor(reflectionTypeColor(type))
                            Text(type)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                            Text("\(count)")
                                .font(.system(size: 10, weight: .bold, design: .rounded))
                                .foregroundColor(DT.textPrimary)
                        }
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(DT.surfaceOverlay.opacity(0.6))
                        .clipShape(Capsule())
                    }
                }
            }

            // Recent reflections
            if let recent = r?.recent, !recent.isEmpty {
                Rectangle().fill(DT.borderSubtle).frame(height: 1)

                VStack(alignment: .leading, spacing: 10) {
                    ForEach(recent) { ref in
                        HStack(alignment: .top, spacing: 10) {
                            Image(systemName: reflectionTypeIcon(ref.type))
                                .font(.system(size: 12))
                                .foregroundColor(reflectionTypeColor(ref.type))
                                .frame(width: 20)

                            VStack(alignment: .leading, spacing: 3) {
                                HStack(spacing: 6) {
                                    Text(ref.type.capitalized)
                                        .font(.system(size: 10, weight: .semibold))
                                        .foregroundColor(reflectionTypeColor(ref.type))

                                    if let depth = ref.depth {
                                        Text("L\(depth)")
                                            .font(.system(size: 8, weight: .bold, design: .rounded))
                                            .foregroundColor(DT.textMuted)
                                            .padding(.horizontal, 4)
                                            .padding(.vertical, 1)
                                            .background(DT.surfaceHighlight)
                                            .clipShape(Capsule())
                                    }

                                    if ref.status == "integrated" {
                                        Image(systemName: "checkmark.circle.fill")
                                            .font(.system(size: 9))
                                            .foregroundColor(DT.emerald)
                                    }
                                }

                                Text(ref.content)
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(DT.textSecondary)
                                    .lineLimit(3)
                            }

                            Spacer()
                        }
                    }
                }
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - 8. Brain vs Rule Migration Card

    private var migrationCard: some View {
        let m = viewModel.metrics?.migration
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.gold).frame(width: 6, height: 6)
                Text("BRAIN vs RULE MIGRATION")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                if let m = m {
                    Text("Readiness: \(Int(m.readinessPct))%")
                        .font(.system(size: 11, weight: .bold, design: .rounded))
                        .foregroundColor(DT.gold)
                }
            }

            // Win rate comparison
            HStack(spacing: 20) {
                VStack(spacing: 4) {
                    Text("\(m?.brainWins ?? 0)")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundColor(DT.purple)
                    Text("Brain wins")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textTertiary)
                }
                .frame(maxWidth: .infinity)

                VStack(spacing: 4) {
                    Text("\(m?.ties ?? 0)")
                        .font(.system(size: 22, weight: .bold, design: .rounded))
                        .foregroundColor(DT.textSecondary)
                    Text("Ties")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textTertiary)
                }

                VStack(spacing: 4) {
                    Text("\(m?.ruleWins ?? 0)")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundColor(DT.orange)
                    Text("Rule wins")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textTertiary)
                }
                .frame(maxWidth: .infinity)
            }

            // Win rate bar
            if let m = m, m.totalComparisons > 0 {
                let brainPct = Double(m.brainWins) / Double(m.totalComparisons)
                let tiePct = Double(m.ties) / Double(m.totalComparisons)

                GeometryReader { geo in
                    HStack(spacing: 2) {
                        RoundedRectangle(cornerRadius: 3)
                            .fill(DT.purple)
                            .frame(width: max(geo.size.width * brainPct, 4))
                        if tiePct > 0 {
                            RoundedRectangle(cornerRadius: 3)
                                .fill(DT.textSecondary.opacity(0.4))
                                .frame(width: max(geo.size.width * tiePct, 2))
                        }
                        RoundedRectangle(cornerRadius: 3)
                            .fill(DT.orange)
                            .frame(width: max(geo.size.width * (1.0 - brainPct - tiePct), 4))
                    }
                }
                .frame(height: 8)
            }

            // Per-feature routing status
            if let routing = m?.routing, !routing.isEmpty {
                Rectangle().fill(DT.borderSubtle).frame(height: 1)

                VStack(alignment: .leading, spacing: 8) {
                    Text("PER-FEATURE ROUTING")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    ForEach(routing) { route in
                        HStack(spacing: 8) {
                            Text(formatFeatureName(route.feature))
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                                .frame(width: 120, alignment: .leading)

                            routingModeBadge(route.mode.label)

                            Spacer()
                        }
                    }
                }
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - 9. Memory Consolidation Card

    private var consolidationCard: some View {
        let c = viewModel.metrics?.consolidation
        return VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Circle().fill(DT.gold).frame(width: 6, height: 6)
                Text("MEMORY CONSOLIDATION")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                Text("7d")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(DT.textMuted)
            }

            // Stats row
            HStack(spacing: 0) {
                consolidationStat(value: c?.clusters7d ?? 0, label: "Clusters", color: DT.gold)
                consolidationStatDivider
                consolidationStat(value: c?.episodesProcessed ?? 0, label: "Episodes", color: DT.blue)
                consolidationStatDivider
                consolidationStat(value: c?.knowledgeCreated ?? 0, label: "Knowledge", color: DT.emerald)
                consolidationStatDivider
                VStack(spacing: 4) {
                    Text(String(format: "%.0f%%", (c?.avgConfidence ?? 0) * 100))
                        .font(.system(size: 20, weight: .bold, design: .rounded))
                        .foregroundColor(DT.textPrimary)
                    Text("Avg Conf.")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textTertiary)
                }
                .frame(maxWidth: .infinity)
            }

            // Top topics
            if let topics = c?.topTopics, !topics.isEmpty {
                Rectangle().fill(DT.borderSubtle).frame(height: 1)

                VStack(alignment: .leading, spacing: 8) {
                    Text("TOP CONSOLIDATION TOPICS")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundColor(DT.textMuted)
                        .tracking(0.8)

                    ForEach(topics.prefix(5)) { topic in
                        HStack(spacing: 8) {
                            Text(topic.topic)
                                .font(.system(size: 10, weight: .medium))
                                .foregroundColor(DT.textSecondary)
                                .lineLimit(1)
                            Spacer()
                            Text("\(topic.count) clusters")
                                .font(.system(size: 9, weight: .medium))
                                .foregroundColor(DT.textTertiary)
                            Text(String(format: "%.0f%%", topic.avgConfidence * 100))
                                .font(.system(size: 10, weight: .bold, design: .rounded))
                                .foregroundColor(DT.gold)
                        }
                    }
                }
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - 10. Knowledge Graph (Reuse existing)

    private var knowledgeGraphCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Circle().fill(DT.purple).frame(width: 6, height: 6)
                Text("KNOWLEDGE GRAPH")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(DT.textTertiary)
                    .tracking(1)
                Spacer()
                if let gd = viewModel.graphData {
                    Text("\(gd.nodes.count) nodes \u{00B7} \(gd.links.count) links")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textMuted)
                }

                // Load more / less buttons
                HStack(spacing: 6) {
                    if viewModel.canShowLess {
                        Button {
                            Task { await viewModel.showLessNodes(databaseService: databaseService) }
                        } label: {
                            HStack(spacing: 3) {
                                Image(systemName: "minus.circle.fill")
                                    .font(.system(size: 10))
                                Text("-500")
                                    .font(.system(size: 9, weight: .semibold))
                            }
                            .foregroundColor(DT.textSecondary)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(DT.surfaceOverlay)
                            .clipShape(Capsule())
                        }
                        .buttonStyle(.plain)
                    }

                    if viewModel.hasMoreNodes {
                        Button {
                            Task { await viewModel.loadMoreNodes(databaseService: databaseService) }
                        } label: {
                            HStack(spacing: 3) {
                                if viewModel.isLoadingGraph {
                                    ProgressView()
                                        .scaleEffect(0.6)
                                        .frame(width: 10, height: 10)
                                } else {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 10))
                                }
                                Text(viewModel.isLoadingGraph ? "..." : "+500")
                                    .font(.system(size: 9, weight: .semibold))
                            }
                            .foregroundColor(DT.purple)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(DT.purple.opacity(0.12))
                            .clipShape(Capsule())
                        }
                        .buttonStyle(.plain)
                        .disabled(viewModel.isLoadingGraph)
                    }
                }
            }

            if viewModel.graphData != nil {
                KnowledgeGraphWebView(graphData: viewModel.graphData)
                    .frame(height: 450)
                    .clipShape(RoundedRectangle(cornerRadius: 10))

                HStack(spacing: 8) {
                    Image(systemName: "hand.draw")
                        .font(.system(size: 10))
                        .foregroundColor(DT.purple)
                    Text("Drag nodes \u{00B7} Scroll to zoom \u{00B7} Click for details")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(DT.textTertiary)
                }
            } else {
                VStack(spacing: 8) {
                    ProgressView()
                        .controlSize(.small)
                    Text("Loading graph...")
                        .font(.system(size: 12))
                        .foregroundColor(DT.textTertiary)
                }
                .frame(maxWidth: .infinity, minHeight: 200)
            }
        }
        .padding(20)
        .background(standardCardBg)
    }

    // MARK: - Helper Components

    private func salienceDimensionBar(_ dims: [String: Double]) -> some View {
        let total = max(dims.values.reduce(0, +), 0.001)
        let items: [(String, Color, Double)] = [
            ("emotional", DT.pink, dims["emotional"] ?? 0),
            ("goal_relevance", DT.emerald, dims["goal_relevance"] ?? 0),
            ("temporal_urgency", DT.orange, dims["temporal_urgency"] ?? 0),
            ("social_relevance", DT.blue, dims["social_relevance"] ?? 0),
            ("novelty", DT.purple, dims["novelty"] ?? 0),
        ]

        return GeometryReader { geo in
            HStack(spacing: 2) {
                ForEach(items, id: \.0) { _, color, value in
                    RoundedRectangle(cornerRadius: 3)
                        .fill(color)
                        .frame(width: max(geo.size.width * (value / total) - 2, 4))
                }
            }
        }
        .frame(height: 8)
    }

    private func motivationBar(_ value: Double) -> some View {
        let bars = Int(value * 10)
        return HStack(spacing: 1) {
            ForEach(0..<10, id: \.self) { i in
                RoundedRectangle(cornerRadius: 1)
                    .fill(i < bars ? DT.orange : DT.surfaceHighlight)
                    .frame(width: 3, height: 12)
            }
        }
        .frame(width: 38)
    }

    private func funnelStage(_ label: String, count: Int, maxCount: Int, color: Color, icon: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundColor(color)
                .frame(width: 20)

            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(DT.textSecondary)
                .frame(width: 80, alignment: .leading)

            GeometryReader { geo in
                RoundedRectangle(cornerRadius: 3)
                    .fill(color.opacity(0.7))
                    .frame(width: geo.size.width * (Double(count) / Double(max(maxCount, 1))))
            }
            .frame(height: 14)

            Text("\(count)")
                .font(.system(size: 12, weight: .bold, design: .rounded))
                .foregroundColor(DT.textPrimary)
                .frame(width: 36, alignment: .trailing)
        }
    }

    private func responsePill(_ label: String, count: Int, color: Color) -> some View {
        HStack(spacing: 3) {
            Circle().fill(color).frame(width: 5, height: 5)
            Text("\(count)")
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .foregroundColor(DT.textPrimary)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(DT.surfaceOverlay.opacity(0.6))
        .clipShape(Capsule())
    }

    private func consolidationStat(value: Int, label: String, color: Color) -> some View {
        VStack(spacing: 4) {
            Text("\(value)")
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(DT.textTertiary)
        }
        .frame(maxWidth: .infinity)
    }

    private var consolidationStatDivider: some View {
        Rectangle().fill(DT.borderSubtle).frame(width: 1, height: 36)
    }

    private func routingModeBadge(_ mode: String) -> some View {
        let color: Color = {
            switch mode.lowercased() {
            case "brain_only": return DT.emerald
            case "brain_preferred": return DT.purple
            case "dual": return DT.blue
            case "rule_only": return DT.orange
            default: return DT.textTertiary
            }
        }()

        return Text(mode.replacingOccurrences(of: "_", with: " "))
            .font(.system(size: 9, weight: .semibold))
            .foregroundColor(color)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(color.opacity(0.12))
            .clipShape(Capsule())
    }

    // MARK: - Formatting Helpers

    private func formatCodeletType(_ type: String) -> String {
        type.replacingOccurrences(of: "_", with: " ")
            .split(separator: " ")
            .map { $0.prefix(1).uppercased() + $0.dropFirst().lowercased() }
            .joined(separator: " ")
    }

    private func formatFeatureName(_ name: String) -> String {
        name.replacingOccurrences(of: "_", with: " ")
            .split(separator: " ")
            .map { $0.prefix(1).uppercased() + $0.dropFirst().lowercased() }
            .joined(separator: " ")
    }

    private func reflectionTypeIcon(_ type: String) -> String {
        switch type.lowercased() {
        case "insight": return "lightbulb.fill"
        case "question": return "questionmark.circle.fill"
        case "realization": return "sparkles"
        case "growth": return "arrow.up.right"
        default: return "brain"
        }
    }

    private func reflectionTypeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "insight": return DT.gold
        case "question": return DT.blue
        case "realization": return DT.pink
        case "growth": return DT.emerald
        default: return DT.purple
        }
    }

    // MARK: - Card Background

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

// MARK: - View Model

@MainActor
class BrainStatusViewModel: ObservableObject {
    @Published var metrics: BrainStatusMetrics?
    @Published var graphData: GraphData?
    @Published var isLoading = false
    @Published var isLoadingGraph = false
    @Published var hasMoreNodes = true

    private var currentNodeCount = 0
    private let nodesPerPage = 500
    private var isFirstLoad = true

    func loadData(databaseService: DatabaseService) async {
        isLoading = true

        // Load brain status metrics
        do {
            metrics = try await databaseService.fetchBrainStatusMetrics()
        } catch {
            print("❌ Brain status metrics: \(error)")
        }

        // Load knowledge graph
        await loadGraph(databaseService: databaseService)

        isLoading = false
    }

    private func loadGraph(databaseService: DatabaseService) async {
        isLoadingGraph = true

        do {
            let brainStats = try await databaseService.fetchBrainStats()

            if isFirstLoad {
                currentNodeCount = Int(Double(brainStats.totalKnowledgeNodes) * 0.7)
                isFirstLoad = false
            }

            let nodes = try await databaseService.fetchKnowledgeNodes(limit: currentNodeCount)
            let relationships = try await databaseService.fetchKnowledgeRelationships(limit: currentNodeCount * 2)

            // Build graph data
            let graphNodes = nodes.map { node in
                GraphNode(
                    id: node.id.uuidString.lowercased(),
                    name: node.conceptName,
                    category: node.conceptCategory,
                    understanding: node.understandingLevel,
                    references: node.timesReferenced ?? 0
                )
            }

            let validNodeIds = Set(graphNodes.map { $0.id })
            let graphLinks = relationships.compactMap { rel -> GraphLink? in
                let sourceId = rel.fromId.lowercased()
                let targetId = rel.toId.lowercased()
                guard validNodeIds.contains(sourceId) && validNodeIds.contains(targetId) else { return nil }
                return GraphLink(source: sourceId, target: targetId, strength: rel.strength)
            }

            graphData = GraphData(nodes: graphNodes, links: graphLinks)
            hasMoreNodes = nodes.count < brainStats.totalKnowledgeNodes
        } catch {
            print("❌ Knowledge graph: \(error)")
        }

        isLoadingGraph = false
    }

    func loadMoreNodes(databaseService: DatabaseService) async {
        guard !isLoadingGraph && hasMoreNodes else { return }
        currentNodeCount += nodesPerPage
        await loadGraph(databaseService: databaseService)
    }

    func showLessNodes(databaseService: DatabaseService) async {
        guard !isLoadingGraph && currentNodeCount > nodesPerPage else { return }
        currentNodeCount = max(nodesPerPage, currentNodeCount - nodesPerPage)
        await loadGraph(databaseService: databaseService)
    }

    var canShowLess: Bool {
        currentNodeCount > nodesPerPage
    }
}
