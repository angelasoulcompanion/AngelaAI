#!/usr/bin/env python3
"""
Backfill AITop + Pythia macOS apps into all project tables.

Creates project entries if missing, then backfills:
tech_stack, patterns, learnings, schemas, flows, technical_decisions, entity_relations

Usage:
    python3 angela_core/scripts/backfill_aitop_pythia.py
    python3 angela_core/scripts/backfill_aitop_pythia.py --dry-run
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# AITop TECH STACK
# ============================================================
AITOP_TECH = [
    ("language", "Swift", "5+", "macOS frontend (SwiftUI)"),
    ("framework", "SwiftUI", None, "Declarative UI framework"),
    ("library", "SwiftUI Charts", None, "Loss graphs, visualizations"),
    ("framework", "FastAPI", ">=0.109.0", "Python backend API"),
    ("language", "Python", "3.13", "Backend"),
    ("library", "httpx", ">=0.27.0", "Async HTTP client"),
    ("library", "psutil", ">=5.9.0", "CPU/Memory/Disk monitoring"),
    ("library", "numpy", ">=1.26.0", "Numerical computing"),
    ("library", "asyncpg", None, "Neon PostgreSQL async client"),
    ("library", "aiohttp", None, "Async HTTP for Ollama/embedding"),
    ("ai", "Ollama", None, "Local LLM inference (localhost:11434)"),
    ("ai", "MLX", None, "Apple Silicon fine-tuning (mlx_lm.lora)"),
    ("embedding", "nomic-embed-text", None, "768 dimensions for RAG"),
    ("database", "Neon PostgreSQL", None, "pgvector, San Junipero/Singapore"),
    ("tool", "system_profiler", None, "Chip/hardware detection"),
    ("tool", "ioreg", None, "GPU renderer/tiler percent"),
    ("tool", "pmset", None, "Thermal pressure monitoring"),
]

# ============================================================
# PYTHIA TECH STACK
# ============================================================
PYTHIA_TECH = [
    ("language", "Swift", "5+", "macOS frontend (SwiftUI)"),
    ("framework", "SwiftUI", None, "Declarative UI framework"),
    ("library", "SwiftUI Charts", None, "Candlestick, breadth, indicators"),
    ("framework", "FastAPI", None, "Python backend API (port 8766)"),
    ("language", "Python", None, "Backend"),
    ("library", "yfinance", None, "Yahoo Finance market data"),
    ("library", "asyncpg", None, "Neon PostgreSQL async pool"),
    ("ai", "Claude API", None, "claude-sonnet-4-20250514, AI advisor"),
    ("ai", "Ollama", None, "typhoon2.5-qwen3-4b local, Thai analysis"),
    ("embedding", "nomic-embed-text", None, "768 dimensions"),
    ("database", "Neon PostgreSQL", None, "Portfolios, assets, watchlists"),
    ("library", "Pydantic", None, "Request/response validation"),
]

# ============================================================
# AITop PATTERNS
# ============================================================
AITOP_PATTERNS = [
    {
        "name": "AITopTheme SSOT",
        "type": "design",
        "description": "Gigabyte-inspired orange+dark theme. accentOrange=#FF6B00, accentCyan=#00D4FF, backgroundDark=#0A0A0F, cardBackground=#1A1A2E. View modifiers: .aiTopCard(), .aiTopPrimaryButton(), .aiTopSecondaryButton(). Gauge colors: <40% green, 40-70% yellow, >70% red.",
        "file_path": "MacOS/AITop/AITop/Utilities/AITopTheme.swift",
    },
    {
        "name": "BackendManager Singleton",
        "type": "architecture",
        "description": "BackendManager.shared manages Python backend process lifecycle. Auto-detects running backend, finds free port (8767-8867 range), health check every 30s. Detects Python at /Library/Frameworks, /opt/homebrew, /usr/local, /usr/bin.",
        "file_path": "MacOS/AITop/AITop/Services/BackendManager.swift",
    },
    {
        "name": "Two-Tier Persistence",
        "type": "architecture",
        "description": "Neon primary (async save) + local JSON/NPY fallback. Both save on every operation. Sync from both on startup. Workspace: ~/.aitop/finetune/ (jobs, datasets), ~/.aitop/rag/ (documents, embeddings).",
    },
    {
        "name": "Hardware Monitor (Apple Silicon)",
        "type": "infrastructure",
        "description": "CPU/GPU/NeuralEngine/Memory/Disk/Thermal via psutil + system_profiler + diskutil + pmset + ioreg. GPU renderer/tiler from ioreg. Neural Engine: 16 cores on M1-M4, estimate usage from power (8000mW=100%). Poll every 3s.",
        "file_path": "MacOS/AITop/services/hardware_monitor.py",
    },
    {
        "name": "GaugeCard Component",
        "type": "component",
        "description": "Reusable circular progress gauge with color-coding: green (<40%), yellow (40-70%), red (>70%). Used for CPU, GPU, Neural Engine, Memory. Theme colors: gaugeLow=#22C55E, gaugeMedium=#F59E0B, gaugeHigh=#EF4444.",
    },
    {
        "name": "Fine-Tune Strategy Presets",
        "type": "architecture",
        "description": "3 presets: fast (1 epoch, lr=5e-4, rank=4, batch=4, ~30min 7B), standard (3 epochs, lr=2e-4, rank=8, batch=2, ~2h), high_precision (5 epochs, lr=1e-4, rank=16, batch=1, ~5h). MLX command: python3 -m mlx_lm.lora.",
        "file_path": "MacOS/AITop/services/finetune_service.py",
    },
    {
        "name": "RAG with Consciousness Context",
        "type": "architecture",
        "description": "Chat pre-injects RAG context from pgvector search (conversations, knowledge_nodes, core_memories tables). Vector search top-K=5, min_score=0.3. Post-chat fires async background learning task.",
        "file_path": "MacOS/AITop/services/consciousness_rag.py",
    },
    {
        "name": "APIConfig SSOT",
        "type": "architecture",
        "description": "host=127.0.0.1, preferredPort=8767, baseURL + apiBaseURL computed. Single source for all network calls.",
        "file_path": "MacOS/AITop/AITop/Utilities/APIConfig.swift",
    },
]

# ============================================================
# PYTHIA PATTERNS
# ============================================================
PYTHIA_PATTERNS = [
    {
        "name": "PythiaTheme SSOT",
        "type": "design",
        "description": "Navy dark theme. primaryBlue=#1E40AF, secondaryBlue=#3B82F6, accentGold=#F59E0B, profit=#059669, loss=#DC2626, backgroundDark=#0F172A, cardBackground=#1E293B. Modifiers: .pythiaCard(), .pythiaPrimaryButton(), .pythiaChartAxes(). Helpers: formatPercent(), formatCurrency(), profitLossColor().",
        "file_path": "MacOS/Pythia/Pythia/PythiaTheme.swift",
    },
    {
        "name": "Global Monitor (Bloomberg-style)",
        "type": "architecture",
        "description": "15 world indices in 3 regions (Americas/Europe/Asia-Pac). Batch yfinance fetch with 2-min cache. Includes: heatmap (7-col grid), 24h UTC timeline bar, risk regime gauge (0-100), yield curve status, FX pairs, cross-asset (Gold/Oil/10Y/BTC/Copper), economic calendar with countdown.",
        "file_path": "MacOS/Pythia/Pythia/Views/Market/GlobalMonitorView.swift",
    },
    {
        "name": "Market Breadth Analysis",
        "type": "algorithm",
        "description": "4 universes (SET50/SET100/SET/Market-wide). 16 indicators: A/D Ratio, % Above 50MA/200MA, McClellan Oscillator/Summation, TRIN (10d avg), Zweig Breadth Thrust, New Highs/Lows. Regime: strong_bull→bull→neutral→bear→strong_bear. 250-point downsampling for large datasets.",
        "file_path": "MacOS/Pythia/Pythia/Views/Market/MarketBreadthView.swift",
    },
    {
        "name": "Technical Analysis (5 Indicators)",
        "type": "algorithm",
        "description": "MACD (12-26-9), RSI (14-period, overbought>70/oversold<30), Bollinger Bands (20-period ±2σ), SMA (20/50/200), EMA. Candlestick via SwiftUI Charts composite Line+Area. TradingView-style: Y-axis trailing, monospaced, crosshair, current price RuleMark.",
    },
    {
        "name": "Risk Analysis Suite",
        "type": "algorithm",
        "description": "VaR (Parametric/Historical/Monte Carlo 10K sims), CVaR (tail risk), Sharpe/Sortino/Calmar/Treynor/Information ratios. Stress testing with scenario impacts. Drawdown analysis. Rolling metrics (window-based volatility + Sharpe). 252 trading days/year.",
    },
    {
        "name": "MPT Portfolio Optimization",
        "type": "algorithm",
        "description": "Efficient Frontier (100 points along risk curve). Min Variance, Max Sharpe, Custom allocation. Correlation/Covariance matrix. Risk-free rates: THB=2.25%, USD=4.35%. Benchmark: ^SET.",
    },
    {
        "name": "Heatmap Color Function",
        "type": "design",
        "description": "+1.5%+: #15803d (dark green), +0.5~1.5%: #4ade80 (light green), ±0.5%: #f3f4f6 (gray), -0.5~-1.5%: #f87171 (light red), -1.5%-: #b91c1c (dark red). Single function reused for all heatmap cells.",
        "file_path": "MacOS/Pythia/Pythia/Views/Market/GlobalMonitorView.swift",
    },
    {
        "name": "250-Point Downsampling",
        "type": "performance",
        "description": "Datasets >1000 points downsampled to 250 for SwiftUI Charts rendering performance. Applied to breadth indicators, historical price data. Median downsampling preserves signal characteristics.",
    },
    {
        "name": "Yield Curve Status Logic",
        "type": "algorithm",
        "description": "Inverted if 10Y-3M spread < -0.1%, Flat if < 0.2%, Normal otherwise. Requires 3M, 5Y, 10Y, 30Y rates. ^TNX for 10Y yield (basis points, not direct %).",
    },
    {
        "name": "Risk Regime Scoring",
        "type": "algorithm",
        "description": "0-100 integer scale. Accumulates: VIX level (±20 pts), term structure (±15), HYG change (±10). Risk-On ≥65, Risk-Off ≤35, Neutral otherwise. Displayed as gauge with gradient coloring.",
    },
    {
        "name": "6-Phase Backend Architecture",
        "type": "architecture",
        "description": "Phase 1: Foundation (assets, portfolios, market, watchlist). Phase 2: Quant (MPT, risk, metrics). Phase 3: Advanced (options, backtest, monte carlo, technical). Phase 4: AI (advisor, sentiment, forecast, research). Phase 5: Breadth. Phase 6: Global Monitor.",
    },
    {
        "name": "APIConfig SSOT (Pythia)",
        "type": "architecture",
        "description": "host=127.0.0.1, preferredPort=8766, baseURL + apiBaseURL computed. Separate from AITop (8767).",
        "file_path": "MacOS/Pythia/Pythia/Services/APIConfig.swift",
    },
]

# ============================================================
# AITop LEARNINGS
# ============================================================
AITOP_LEARNINGS = [
    {"type": "gotcha", "category": "ollama", "title": "Ollama timeout for model pull is infinite",
     "insight": "Pull model uses infinite timeout (streaming download). Default read=30s, overall=120s for normal operations. Model names use / separator (e.g., gemma3:12b)."},
    {"type": "gotcha", "category": "mlx", "title": "MLX fine-tune command uses --iters not --epochs",
     "insight": "mlx_lm.lora uses --iters (epochs * 100), --lora-layers (not --lora-rank), --adapter-path for output. Parse stdout for 'Train loss:' and 'Iter:' for progress."},
    {"type": "gotcha", "category": "hardware", "title": "Neural Engine usage estimated from power draw",
     "insight": "No direct API for NE usage. Estimate: power_mW / 8000 * 100 = usage%. M1-M4 all have 16 NE cores. Available=true if chip starts with 'Apple'."},
    {"type": "gotcha", "category": "hardware", "title": "GPU metrics from ioreg not psutil",
     "insight": "psutil doesn't expose GPU on macOS. Use ioreg for rendererPercent and tilerPercent. system_profiler SPHardwareDataType for chip name. diskutil info / for APFS stats."},
    {"type": "gotcha", "category": "persistence", "title": "AITop job ID is 8-char UUID prefix",
     "insight": "Job IDs are first 8 chars of UUID (not full UUID). Output dir: ~/.aitop/finetune/{job_id}/. Datasets at ~/.aitop/finetune/datasets/{filename}."},
    {"type": "technical", "category": "architecture", "title": "Chat RAG injects consciousness context",
     "insight": "Pre-chat: vector search memories (top-K=5, min_score=0.3) from conversations + knowledge_nodes + core_memories. Context injected into system prompt. Post-chat: async fire-and-forget background learning."},
]

# ============================================================
# PYTHIA LEARNINGS
# ============================================================
PYTHIA_LEARNINGS = [
    {"type": "gotcha", "category": "yfinance", "title": "Yahoo Finance delayed 15-20 min for some indices",
     "insight": "SET (Thai market) operates 10:00-16:30 ICT (Asia/Bangkok). International exchanges have varying UTC offsets handled in EXCHANGE_HOURS dict. Sparklines always pull 5-day max."},
    {"type": "gotcha", "category": "finance", "title": "^TNX is basis points not direct percentage",
     "insight": "^TNX (10Y yield) returns basis points. Cross-asset symbols: GC=F (Gold), CL=F (Crude Oil), BTC-USD (spot), HG=F (Copper). Some FX pairs inverted (JPY=X = USD/JPY)."},
    {"type": "gotcha", "category": "finance", "title": "Economic calendar dates hardcoded not live",
     "insight": "8 FOMC dates/year at 18:00 UTC (irregular schedule). US CPI ~13th at 12:30 UTC. NFP first Friday 12:30 UTC. ECB/BoJ dates hardcoded. Not fetched from API."},
    {"type": "gotcha", "category": "charts", "title": "SwiftUI Charts >1000 points causes rendering lag",
     "insight": "Must downsample to 250 points for datasets >1000. Median downsampling preserves signal. Applied to breadth indicators and historical data. Without this, UI freezes."},
    {"type": "gotcha", "category": "finance", "title": "Risk regime scoring is 0-100 integer not percentage",
     "insight": "Accumulates points: VIX level (±20), term structure (±15), HYG change (±10). Risk-On ≥65, Risk-Off ≤35, Neutral otherwise. Not a direct probability."},
    {"type": "technical", "category": "finance", "title": "Financial constants hardcoded in config.py",
     "insight": "TRADING_DAYS_PER_YEAR=252, RISK_FREE_RATES: THB=2.25% USD=4.35%, VAR_CONFIDENCE_LEVEL=0.95, MC_SIMULATIONS=10000, LLM_TEMPERATURE=0.3 (strict), DEFAULT_BENCHMARK=^SET."},
    {"type": "gotcha", "category": "cache", "title": "Global monitor 2-min in-memory cache clears on restart",
     "insight": "No distributed cache. Batch yfinance fetch (15 indices + cross-asset + FX) in single call with threading=True. Restart clears cache = first request slow."},
    {"type": "technical", "category": "breadth", "title": "Breadth regime scoring logic",
     "insight": "Bullish: A/D>1.2, %>200MA>50%, McClellan>0, TRIN<1.0. Bearish: A/D<0.8, %>200MA<30%, McClellan<-100, TRIN>1.25. Zweig Breadth Thrust: TRIN<0.75 for 10 days (rare, strong buy)."},
]

# ============================================================
# AITop TECHNICAL DECISIONS
# ============================================================
AITOP_DECISIONS = [
    {"title": "Gigabyte AI TOP Orange Theme", "category": "design",
     "context": "AI training studio needs distinctive, high-tech appearance",
     "decision_made": "Orange accent (#FF6B00) + cyan secondary (#00D4FF) on dark background (#0A0A0F). Inspired by Gigabyte AI TOP BIOS.",
     "reasoning": "Differentiates from Angela Purple. Orange conveys power/performance for AI training context."},
    {"title": "MLX over PyTorch for Fine-Tuning", "category": "architecture",
     "context": "Need efficient fine-tuning on Apple Silicon",
     "decision_made": "Use MLX framework (mlx_lm.lora) for LoRA fine-tuning on Apple Silicon",
     "reasoning": "Native Apple Silicon optimization. Unified Memory = no GPU transfer overhead. 3 strategy presets (fast/standard/high_precision)."},
    {"title": "Two-Tier Persistence (Neon + Local)", "category": "architecture",
     "context": "Need reliability for long-running training jobs",
     "decision_made": "Save to both Neon (primary) and local JSON/NPY (fallback) on every operation",
     "reasoning": "Network failure shouldn't lose training progress. Local files ensure recovery. Sync from both on startup."},
    {"title": "Consciousness RAG in Chat", "category": "architecture",
     "context": "Chat should leverage Angela's memory for contextual responses",
     "decision_made": "Pre-chat: vector search top-5 from conversations + knowledge_nodes + core_memories. Post-chat: async background learning.",
     "reasoning": "Makes chat context-aware without blocking response. Fire-and-forget learning doesn't slow UX."},
]

# ============================================================
# PYTHIA TECHNICAL DECISIONS
# ============================================================
PYTHIA_DECISIONS = [
    {"title": "Bloomberg-style Global Monitor", "category": "design",
     "context": "Need real-time overview of 15+ world markets",
     "decision_made": "Single-view dashboard: region cards + heatmap + 24h timeline + risk regime + yield curve + FX + cross-asset + economic calendar. 2-min batch refresh.",
     "reasoning": "Bloomberg Terminal inspiration. Single glance for global market awareness. Batch fetch reduces API calls."},
    {"title": "Navy Blue Theme (not Purple)", "category": "design",
     "context": "Financial app needs serious, professional look",
     "decision_made": "primaryBlue=#1E40AF, backgroundDark=#0F172A, accentGold=#F59E0B, profit=#059669, loss=#DC2626",
     "reasoning": "Navy blue conveys trust/finance. Gold accent for highlights. Green/red profit-loss is universal finance convention."},
    {"title": "6-Phase Modular Backend", "category": "architecture",
     "context": "Complex financial platform with many feature domains",
     "decision_made": "Phase 1: Foundation → Phase 2: Quant → Phase 3: Advanced → Phase 4: AI → Phase 5: Breadth → Phase 6: Global Monitor",
     "reasoning": "Incremental development. Each phase builds on previous. 16+ routers organized by domain."},
    {"title": "yfinance Batch Fetch + 2-min Cache", "category": "performance",
     "context": "15+ indices × individual API calls = slow",
     "decision_made": "Single yf.download() with threading=True for batch fetch. 2-minute in-memory cache.",
     "reasoning": "~14s for batch vs 5+ min for individual calls (from Angela Two-Phase Loading learning). Cache reduces API load."},
    {"title": "16 Market Breadth Indicators", "category": "architecture",
     "context": "Need comprehensive market health analysis",
     "decision_made": "A/D ratio, % above 50MA/200MA, McClellan Oscillator/Summation, TRIN (10d avg), Zweig Breadth Thrust, New Highs/Lows, High/Low Index",
     "reasoning": "Complete breadth picture. Regime detection (strong_bull to strong_bear). Divergence analysis for early warning."},
    {"title": "VaR: 3 Methods (Parametric + Historical + Monte Carlo)", "category": "architecture",
     "context": "Need robust risk measurement",
     "decision_made": "Parametric (normal assumption), Historical (empirical), Monte Carlo (10K simulations). Plus CVaR (tail risk).",
     "reasoning": "Each method has strengths/weaknesses. Cross-validate for confidence. 10K sims is standard for MC VaR."},
]

# ============================================================
# FLOWS
# ============================================================
AITOP_FLOWS = [
    {
        "flow_name": "Fine-Tune Training Pipeline",
        "flow_type": "data",
        "description": "MLX LoRA fine-tuning on Apple Silicon",
        "steps": json.dumps([
            {"step": 1, "action": "Upload Dataset", "detail": "POST /api/finetune/datasets/upload (JSONL format)"},
            {"step": 2, "action": "Create Job", "detail": "POST /api/finetune/jobs (model + dataset + strategy preset)"},
            {"step": 3, "action": "Start Training", "detail": "POST /api/finetune/jobs/{id}/start → spawns subprocess"},
            {"step": 4, "action": "MLX Command", "detail": "python3 -m mlx_lm.lora --model --data --iters --batch-size --lora-layers --learning-rate --adapter-path"},
            {"step": 5, "action": "Monitor", "detail": "Parse stdout: 'Train loss:' → loss_val, 'Iter:' → current_step. Poll every 2s"},
            {"step": 6, "action": "Persist", "detail": "Save to Neon + local JSON on each update"},
            {"step": 7, "action": "Complete", "detail": "status=completed/failed, adapters at ~/.aitop/finetune/{job_id}/adapters"},
        ]),
        "critical_notes": "mlx_lm uses --iters not --epochs. Job ID is 8-char UUID prefix. 3 presets: fast(30min)/standard(2h)/high_precision(5h).",
    },
    {
        "flow_name": "Hardware Dashboard Polling",
        "flow_type": "data",
        "description": "Apple Silicon hardware monitoring every 3s",
        "steps": json.dumps([
            {"step": 1, "action": "Timer", "detail": "SwiftUI onAppear → startPolling() every 3 seconds"},
            {"step": 2, "action": "API Call", "detail": "GET /api/dashboard"},
            {"step": 3, "action": "Collect", "detail": "psutil (CPU/mem/disk), system_profiler (chip), ioreg (GPU), pmset (thermal)"},
            {"step": 4, "action": "Aggregate", "detail": "HardwareStats + OllamaStatus + RunningModels"},
            {"step": 5, "action": "Render", "detail": "GaugeCards (CPU/GPU/NE/Mem), UsageBars, Ollama status, thermal"},
        ]),
    },
    {
        "flow_name": "Chat with RAG Context",
        "flow_type": "data",
        "description": "Consciousness-aware chat with memory injection",
        "steps": json.dumps([
            {"step": 1, "action": "User Message", "detail": "POST /api/chat"},
            {"step": 2, "action": "Pre-Chat RAG", "detail": "pgvector search: conversations + knowledge_nodes + core_memories (top-5, min 0.3)"},
            {"step": 3, "action": "Inject Context", "detail": "Append RAG results to system prompt"},
            {"step": 4, "action": "Ollama Chat", "detail": "Call /api/chat with enriched system prompt"},
            {"step": 5, "action": "Post-Chat", "detail": "Async fire-and-forget background learning task"},
            {"step": 6, "action": "Return", "detail": "Response + rag_context_used flag + token stats"},
        ]),
    },
]

PYTHIA_FLOWS = [
    {
        "flow_name": "Global Monitor Refresh",
        "flow_type": "data",
        "description": "Bloomberg-style world market data (2-min cycle)",
        "steps": json.dumps([
            {"step": 1, "action": "Timer/Manual", "detail": "Auto every 2 min or manual refresh button"},
            {"step": 2, "action": "API Call", "detail": "GET /api/global-monitor"},
            {"step": 3, "action": "Cache Check", "detail": "2-min TTL in-memory cache"},
            {"step": 4, "action": "Batch Fetch", "detail": "Single yf.download() for 15 indices + cross-asset + FX (threading=True)"},
            {"step": 5, "action": "Calculate", "detail": "Sentiment, yield curve status, risk regime score (0-100), FX rates, economic calendar"},
            {"step": 6, "action": "Render", "detail": "Region cards + heatmap + 24h timeline + risk gauge + FX table + calendar"},
        ]),
        "critical_notes": "Yahoo Finance delayed 15-20min for some. SET operates 10:00-16:30 ICT. Restart clears cache.",
    },
    {
        "flow_name": "Market Breadth Analysis",
        "flow_type": "data",
        "description": "16 breadth indicators for SET market health",
        "steps": json.dumps([
            {"step": 1, "action": "Select Universe", "detail": "SET50/SET100/SET/Market-wide + period (3M/6M/1Y/2Y)"},
            {"step": 2, "action": "Fetch History", "detail": "GET /api/market-breadth?universe=SET50&period=3m"},
            {"step": 3, "action": "Calculate", "detail": "A/D ratio, % above 50/200 MA, McClellan Osc/Sum, TRIN, Zweig, New H/L"},
            {"step": 4, "action": "Classify Regime", "detail": "strong_bull/bull/neutral/bear/strong_bear from indicator thresholds"},
            {"step": 5, "action": "Render", "detail": "Regime badge + summary cards + 5 chart sections (downsampled to 250 pts)"},
        ]),
    },
    {
        "flow_name": "Portfolio Risk Analysis",
        "flow_type": "data",
        "description": "VaR + CVaR + stress testing + drawdown",
        "steps": json.dumps([
            {"step": 1, "action": "Select Portfolio", "detail": "Portfolio with holdings and historical prices"},
            {"step": 2, "action": "Calculate Returns", "detail": "Log-returns from historical prices, 252 trading days/year"},
            {"step": 3, "action": "VaR (3 methods)", "detail": "Parametric (z-score × σ), Historical (percentile), Monte Carlo (10K sims)"},
            {"step": 4, "action": "CVaR", "detail": "Average of worst 5% returns (tail risk)"},
            {"step": 5, "action": "Ratios", "detail": "Sharpe, Sortino, Calmar, Treynor, Information + beta/alpha/R²"},
            {"step": 6, "action": "Stress Test", "detail": "Scenario-based portfolio impact analysis"},
        ]),
        "critical_notes": "Risk-free: THB=2.25%, USD=4.35%. MC_SIMULATIONS=10000. VAR_CONFIDENCE=0.95.",
    },
]

# ============================================================
# ENTITY RELATIONS
# ============================================================
AITOP_RELATIONS = [
    ("FineTuneJob", "DatasetFile", "N:1", "FineTuneJob.datasetPath references DatasetFile.path", "Job uses dataset"),
    ("FineTuneJob", "LossPoint", "1:N", "LossPoint embedded in FineTuneJob.lossHistory array", "Job has loss history"),
    ("RAGDocument", "RAGChunk", "1:N", "RAGChunk.docId = RAGDocument.id", "Document has chunks"),
    ("OllamaModel", "ChatMessage", "1:N", "ChatMessage uses OllamaModel.name for inference", "Model serves chat"),
]

PYTHIA_RELATIONS = [
    ("Portfolio", "Holding", "1:N", "Holding.portfolioId = Portfolio.portfolioId", "Portfolio has holdings"),
    ("Portfolio", "Transaction", "1:N", "Transaction.portfolioId = Portfolio.portfolioId", "Portfolio has transactions"),
    ("Asset", "Holding", "1:N", "Holding.assetId = Asset.assetId", "Asset held in portfolios"),
    ("Asset", "Transaction", "1:N", "Transaction.assetId = Asset.assetId", "Asset has transactions"),
    ("Watchlist", "WatchlistItem", "1:N", "WatchlistItem.watchlistId = Watchlist.watchlistId", "Watchlist has items"),
    ("WatchlistItem", "Asset", "N:1", "WatchlistItem.assetId = Asset.assetId", "Item references asset"),
]


async def main(dry_run: bool = False) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        # Create AITop project if missing
        aitop_pid = await db.fetchval(
            "SELECT project_id FROM angela_projects WHERE project_code = 'AITOP'"
        )
        if not aitop_pid:
            aitop_row = await db.fetchrow("""
                INSERT INTO angela_projects (project_code, project_name, description, project_type, status,
                    working_directory, repository_url, started_at, created_at, updated_at)
                VALUES ('AITOP', 'AI TOP - Local AI Training & Inference Studio',
                    'macOS native app for Ollama inference, MLX fine-tuning, RAG, hardware monitoring',
                    'personal', 'active',
                    '/Users/davidsamanyaporn/PycharmProjects/AngelaAI/MacOS/AITop',
                    NULL, NOW(), NOW(), NOW())
                RETURNING project_id
            """)
            aitop_pid = aitop_row['project_id']
            print(f"✅ Created AITOP project: {str(aitop_pid)[:8]}...")
        else:
            print(f"📁 AITOP exists: {str(aitop_pid)[:8]}...")

        # Create Pythia project if missing
        pythia_pid = await db.fetchval(
            "SELECT project_id FROM angela_projects WHERE project_code = 'PYTHIA'"
        )
        if not pythia_pid:
            pythia_row = await db.fetchrow("""
                INSERT INTO angela_projects (project_code, project_name, description, project_type, status,
                    working_directory, repository_url, started_at, created_at, updated_at)
                VALUES ('PYTHIA', 'Pythia - Financial Analytics & Quantitative Platform',
                    'macOS native app for market analysis, portfolio optimization, risk management, market breadth',
                    'personal', 'active',
                    '/Users/davidsamanyaporn/PycharmProjects/AngelaAI/MacOS/Pythia',
                    NULL, NOW(), NOW(), NOW())
                RETURNING project_id
            """)
            pythia_pid = pythia_row['project_id']
            print(f"✅ Created PYTHIA project: {str(pythia_pid)[:8]}...")
        else:
            print(f"📁 PYTHIA exists: {str(pythia_pid)[:8]}...")

        # Helper functions
        async def upsert_tech(pid, stack, label):
            for t, n, v, p in stack:
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_tech_stack (project_id, tech_type, tech_name, version, purpose)
                        VALUES ($1,$2,$3,$4,$5) ON CONFLICT (project_id, tech_type, tech_name) DO UPDATE SET version=$4, purpose=$5
                    """, pid, t, n, v, p)
            c = await db.fetchval("SELECT COUNT(*) FROM project_tech_stack WHERE project_id=$1", pid)
            print(f"  {label}: {c} rows")

        async def upsert_patterns(pid, patterns, label):
            for p in patterns:
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_patterns (project_id, pattern_name, pattern_type, description, file_path)
                        VALUES ($1,$2,$3,$4,$5) ON CONFLICT (project_id, pattern_name) DO UPDATE SET description=$4, file_path=$5
                    """, pid, p['name'], p['type'], p['description'], p.get('file_path'))
                print(f"  ✅ [{label}] {p['name']}")

        async def upsert_learnings(pid, learnings, label):
            for l in learnings:
                ex = await db.fetchval("SELECT COUNT(*) FROM project_learnings WHERE project_id=$1 AND title=$2", pid, l['title'])
                if ex > 0: continue
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_learnings (project_id, learning_type, category, title, insight, confidence)
                        VALUES ($1,$2,$3,$4,$5,0.95)
                    """, pid, l['type'], l['category'], l['title'], l['insight'])
                print(f"  ✅ [{label}] {l['title']}")

        async def upsert_decisions(pid, decisions, label):
            for d in decisions:
                ex = await db.fetchval("SELECT COUNT(*) FROM project_technical_decisions WHERE project_id=$1 AND decision_title=$2", pid, d['title'])
                if ex > 0: continue
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_technical_decisions (project_id, decision_title, category, context, decision_made, reasoning, decided_by)
                        VALUES ($1,$2,$3,$4,$5,$6,'David')
                    """, pid, d['title'], d['category'], d['context'], d['decision_made'], d['reasoning'])
                print(f"  ✅ [{label}] {d['title']}")

        async def upsert_flows(pid, flows, label):
            for f in flows:
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_flows (project_id, flow_name, flow_type, description, steps, critical_notes)
                        VALUES ($1,$2,$3,$4,$5::jsonb,$6) ON CONFLICT (project_id, flow_name) DO UPDATE SET steps=$5::jsonb, critical_notes=$6
                    """, pid, f['flow_name'], f['flow_type'], f['description'], f['steps'], f.get('critical_notes'))
                print(f"  ✅ [{label}] {f['flow_name']}")

        async def upsert_relations(pid, rels, label):
            for from_t, to_t, rel_type, join_cond, name in rels:
                if not dry_run:
                    await db.execute("""
                        INSERT INTO project_entity_relations (project_id, from_table, to_table, relation_type, join_condition, relation_name)
                        VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT (project_id, from_table, to_table, relation_type) DO NOTHING
                    """, pid, from_t, to_t, rel_type, join_cond, name)
                print(f"  ✅ [{label}] {from_t} → {to_t}")

        # === EXECUTE ALL ===
        print("\n=== 1. project_tech_stack ===")
        await upsert_tech(aitop_pid, AITOP_TECH, "AITOP")
        await upsert_tech(pythia_pid, PYTHIA_TECH, "PYTHIA")

        print("\n=== 2. project_patterns ===")
        await upsert_patterns(aitop_pid, AITOP_PATTERNS, "AITOP")
        await upsert_patterns(pythia_pid, PYTHIA_PATTERNS, "PYTHIA")

        print("\n=== 3. project_learnings ===")
        await upsert_learnings(aitop_pid, AITOP_LEARNINGS, "AITOP")
        await upsert_learnings(pythia_pid, PYTHIA_LEARNINGS, "PYTHIA")

        print("\n=== 4. project_technical_decisions ===")
        await upsert_decisions(aitop_pid, AITOP_DECISIONS, "AITOP")
        await upsert_decisions(pythia_pid, PYTHIA_DECISIONS, "PYTHIA")

        print("\n=== 5. project_flows ===")
        await upsert_flows(aitop_pid, AITOP_FLOWS, "AITOP")
        await upsert_flows(pythia_pid, PYTHIA_FLOWS, "PYTHIA")

        print("\n=== 6. project_entity_relations ===")
        await upsert_relations(aitop_pid, AITOP_RELATIONS, "AITOP")
        await upsert_relations(pythia_pid, PYTHIA_RELATIONS, "PYTHIA")

        # FINAL SUMMARY
        print("\n" + "=" * 60)
        print("FINAL COUNTS (ALL PROJECTS)")
        print("=" * 60)
        for table in [
            'project_tech_stack', 'project_patterns', 'project_schemas',
            'project_entity_relations', 'project_learnings',
            'project_technical_decisions', 'project_flows',
            'project_mistakes', 'angela_technical_standards', 'project_milestones',
        ]:
            c = await db.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table:40s} {c:>5} rows")

        # Per-project breakdown
        print("\n  --- Per Project ---")
        projs = await db.fetch("SELECT project_id, project_code FROM angela_projects ORDER BY project_code")
        for p in projs:
            pat = await db.fetchval("SELECT COUNT(*) FROM project_patterns WHERE project_id=$1", p['project_id'])
            tech = await db.fetchval("SELECT COUNT(*) FROM project_tech_stack WHERE project_id=$1", p['project_id'])
            learn = await db.fetchval("SELECT COUNT(*) FROM project_learnings WHERE project_id=$1", p['project_id'])
            if pat > 0 or tech > 0:
                print(f"  {p['project_code']:15s} tech={tech:>3} patterns={pat:>3} learnings={learn:>3}")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
