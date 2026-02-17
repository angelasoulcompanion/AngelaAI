"""
Tool Learning — Track tool effectiveness and auto-escalate.
============================================================
Learns from tool usage patterns:
1. Track success/failure rates per tool
2. Auto-escalate: if Ollama fails for an intent, try Claude next time
3. Recommend tools based on past success for similar intents

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from angela_core.services.base_db_service import BaseDBService

logger = logging.getLogger(__name__)


class ToolLearning(BaseDBService):
    """
    Learns tool effectiveness from execution history.

    Tracks:
    - Success rate per tool
    - Avg execution time per tool
    - Which tools work for which intents
    - Auto-escalation from Ollama → Claude for failed intents
    """

    # Escalation memory: intent patterns that failed on Ollama
    _escalation_cache: Dict[str, int] = {}  # intent_prefix → fail_count

    ESCALATION_THRESHOLD = 2  # After 2 Ollama failures, escalate to Claude

    # ── Learning from Execution ──

    async def learn_from_execution(
        self, tool_name: str, intent: str, success: bool,
        execution_time_ms: float, triggered_by: str = "auto"
    ) -> None:
        """Record a tool execution outcome for learning."""
        await self.connect()

        # Update tool stats
        if success:
            await self.db.execute("""
                UPDATE angela_tool_registry
                SET total_executions = total_executions + 1,
                    total_successes = total_successes + 1
                WHERE tool_name = $1
            """, tool_name)
        else:
            await self.db.execute("""
                UPDATE angela_tool_registry
                SET total_executions = total_executions + 1
                WHERE tool_name = $1
            """, tool_name)

        # Track escalation
        if not success and triggered_by == "ollama":
            intent_prefix = intent[:30].lower()
            self._escalation_cache[intent_prefix] = self._escalation_cache.get(intent_prefix, 0) + 1

    def should_escalate(self, intent: str) -> bool:
        """Check if an intent should be escalated from Ollama to Claude."""
        intent_prefix = intent[:30].lower()
        return self._escalation_cache.get(intent_prefix, 0) >= self.ESCALATION_THRESHOLD

    # ── Tool Recommendations ──

    async def get_tool_stats(self) -> List[Dict[str, Any]]:
        """Get success rates for all tools."""
        await self.connect()

        rows = await self.db.fetch("""
            SELECT tool_name, category, total_executions, total_successes,
                   CASE WHEN total_executions > 0
                        THEN ROUND(total_successes::NUMERIC / total_executions, 2)
                        ELSE 0 END as success_rate
            FROM angela_tool_registry
            WHERE enabled = TRUE
            ORDER BY total_executions DESC
        """)

        return [dict(r) for r in rows]

    async def get_recent_executions(
        self, tool_name: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent tool executions."""
        await self.connect()

        if tool_name:
            rows = await self.db.fetch("""
                SELECT tool_name, parameters, result_summary, success,
                       execution_time_ms, triggered_by, created_at
                FROM tool_execution_log
                WHERE tool_name = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, tool_name, limit)
        else:
            rows = await self.db.fetch("""
                SELECT tool_name, parameters, result_summary, success,
                       execution_time_ms, triggered_by, created_at
                FROM tool_execution_log
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

        return [dict(r) for r in rows]

    async def recommend_tool(self, intent: str) -> Optional[str]:
        """Recommend the best tool for an intent based on past success."""
        await self.connect()

        # Find tools that have been used successfully for similar intents
        rows = await self.db.fetch("""
            SELECT tool_name, COUNT(*) as uses,
                   COUNT(*) FILTER (WHERE success = TRUE) as successes
            FROM tool_execution_log
            WHERE result_summary ILIKE '%' || $1 || '%'
               OR parameters::TEXT ILIKE '%' || $1 || '%'
            GROUP BY tool_name
            HAVING COUNT(*) FILTER (WHERE success = TRUE) > 0
            ORDER BY successes DESC
            LIMIT 1
        """, intent[:30])

        if rows:
            return rows[0]["tool_name"]
        return None

    # ── Summary ──

    async def summary(self) -> Dict[str, Any]:
        """Get learning summary."""
        stats = await self.get_tool_stats()

        return {
            "tools_tracked": len(stats),
            "total_executions": sum(s.get("total_executions", 0) for s in stats),
            "avg_success_rate": (
                sum(float(s.get("success_rate", 0)) for s in stats) / len(stats)
                if stats else 0
            ),
            "escalation_cache_size": len(self._escalation_cache),
            "top_tools": [
                {"name": s["tool_name"], "executions": s["total_executions"], "success_rate": float(s.get("success_rate", 0))}
                for s in stats[:5]
            ],
        }
