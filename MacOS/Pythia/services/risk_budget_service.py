"""
Pythia — Risk Budget Advisor Service
AI-powered risk budget allocation across strategies.
"""
from dataclasses import dataclass, field
from uuid import UUID

import asyncpg

from config import PythiaConfig


@dataclass
class RiskBudgetResult:
    portfolio_id: str
    total_budget: float
    allocations: list[dict] = field(default_factory=list)
    utilization: float = 0.0
    ai_advice: str = ""
    regime: str = ""
    success: bool = True
    message: str = ""


async def allocate_risk_budget(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    total_budget: float = 0.02,
) -> RiskBudgetResult:
    """Allocate risk budget across portfolio with AI advice."""
    # Get regime context
    regime = ""
    try:
        from services.regime_service import detect_regime
        r = await detect_regime(conn, "^SET.BK", days=200)
        if r.success:
            regime = r.regime
    except Exception:
        pass

    # Get active strategies
    strategies = await conn.fetch(
        "SELECT strategy_id, name, strategy_type FROM strategies WHERE is_active = true"
    )

    # Get portfolio holdings count
    holdings_count = await conn.fetchval(
        "SELECT COUNT(*) FROM portfolio_holdings WHERE portfolio_id = $1",
        portfolio_id,
    ) or 0

    # Simple allocation based on regime
    allocations = []
    if regime in ("crisis", "bear"):
        # Conservative: reduce risk
        per_strategy = total_budget * 0.5 / max(len(strategies), 1)
        cash_reserve = total_budget * 0.5
    elif regime == "bull":
        # Aggressive: full allocation
        per_strategy = total_budget * 0.8 / max(len(strategies), 1)
        cash_reserve = total_budget * 0.2
    else:
        per_strategy = total_budget * 0.7 / max(len(strategies), 1)
        cash_reserve = total_budget * 0.3

    for s in strategies:
        allocations.append({
            "strategy_id": str(s["strategy_id"]),
            "strategy_name": s["name"],
            "strategy_type": s["strategy_type"],
            "risk_budget_pct": round(per_strategy * 100, 2),
            "max_position_pct": round(per_strategy / max(holdings_count, 1) * 100, 2),
        })

    allocations.append({
        "strategy_id": "cash_reserve",
        "strategy_name": "Cash Reserve",
        "strategy_type": "buffer",
        "risk_budget_pct": round(cash_reserve * 100, 2),
        "max_position_pct": 0,
    })

    utilization = sum(a["risk_budget_pct"] for a in allocations if a["strategy_id"] != "cash_reserve") / (total_budget * 100)

    result = RiskBudgetResult(
        portfolio_id=str(portfolio_id),
        total_budget=total_budget,
        allocations=allocations,
        utilization=round(utilization, 4),
        regime=regime,
    )

    # AI advice via Claude
    try:
        from services.llm_service import llm_service
        strat_summary = ", ".join(f"{s['name']}({s['strategy_type']})" for s in strategies)
        prompt = f"""Risk budget allocation for portfolio:
Regime: {regime} | Total budget: {total_budget*100:.1f}% | Holdings: {holdings_count}
Strategies: {strat_summary or 'None'}
Utilization: {utilization*100:.0f}%

Write 2-3 sentences of risk management advice: should the trader increase/decrease exposure, which strategy types are favored in this regime, and key risk to watch."""

        resp = await llm_service.complete(
            prompt=prompt,
            system="You are a risk manager at a quantitative fund. Be precise about risk allocation.",
            max_tokens=512,
            conn=conn, cache_ttl=PythiaConfig.CACHE_TTL_SIGNALS, feature="risk_budget",
        )
        if resp.success:
            result.ai_advice = resp.text
    except Exception:
        pass

    return result
