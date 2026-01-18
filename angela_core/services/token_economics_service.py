"""
Token Economics Service - Track API Cost Savings

Tracks token usage across all memory operations:
- Tokens stored (input)
- Tokens retrieved (output)
- Tokens saved by decay/compression
- Calculates cost savings vs full context approach

Cost model (Claude 3.5 Sonnet):
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from angela_core.database import get_db_connection


class TokenEconomicsService:
    """
    Manages token economics tracking and cost analysis.

    Tracks:
    - Token storage and retrieval per day
    - Decay savings (memory compression)
    - Memory tier distribution
    - Cost savings vs naive full-context approach
    """

    # Cost per 1M tokens (Claude 3.5 Sonnet pricing)
    INPUT_COST_PER_1M = 3.0    # $3 per 1M input tokens
    OUTPUT_COST_PER_1M = 15.0  # $15 per 1M output tokens

    # Average full context size if we didn't use tiered memory
    NAIVE_CONTEXT_SIZE = 50000  # 50K tokens per query without optimization

    def __init__(self, db=None):
        self.db = db

    async def track_tokens_stored(self, tokens: int, memory_tier: str = None) -> bool:
        """
        Track tokens stored in memory.

        Args:
            tokens: Number of tokens stored
            memory_tier: Which tier (focus, fresh, longterm, etc.)

        Returns:
            Success status
        """
        async with get_db_connection() as conn:
            # Upsert for today's record
            await conn.execute("""
                INSERT INTO token_economics (date, tokens_stored)
                VALUES (CURRENT_DATE, $1)
                ON CONFLICT (date) DO UPDATE
                SET tokens_stored = token_economics.tokens_stored + $1,
                    updated_at = NOW()
            """, tokens)

            # Update tier count if specified
            if memory_tier:
                tier_column = f"{memory_tier}_count"
                if tier_column in ['focus_count', 'fresh_count', 'longterm_count',
                                   'procedural_count', 'shock_count']:
                    await conn.execute(f"""
                        UPDATE token_economics
                        SET {tier_column} = {tier_column} + 1
                        WHERE date = CURRENT_DATE
                    """)

        return True

    async def track_tokens_retrieved(self, tokens: int) -> bool:
        """
        Track tokens retrieved from memory.

        Args:
            tokens: Number of tokens retrieved

        Returns:
            Success status
        """
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO token_economics (date, tokens_retrieved)
                VALUES (CURRENT_DATE, $1)
                ON CONFLICT (date) DO UPDATE
                SET tokens_retrieved = token_economics.tokens_retrieved + $1,
                    updated_at = NOW()
            """, tokens)

        return True

    async def track_decay_savings(
        self,
        tokens_saved: int,
        compression_ratio: float = None
    ) -> bool:
        """
        Track tokens saved through decay/compression.

        Args:
            tokens_saved: Tokens freed by compression
            compression_ratio: Original/compressed ratio

        Returns:
            Success status
        """
        async with get_db_connection() as conn:
            if compression_ratio:
                # Update with weighted average compression ratio
                await conn.execute("""
                    INSERT INTO token_economics (date, tokens_saved_by_decay, compression_ratio)
                    VALUES (CURRENT_DATE, $1, $2)
                    ON CONFLICT (date) DO UPDATE
                    SET tokens_saved_by_decay = token_economics.tokens_saved_by_decay + $1,
                        compression_ratio = (token_economics.compression_ratio + $2) / 2,
                        updated_at = NOW()
                """, tokens_saved, compression_ratio)
            else:
                await conn.execute("""
                    INSERT INTO token_economics (date, tokens_saved_by_decay)
                    VALUES (CURRENT_DATE, $1)
                    ON CONFLICT (date) DO UPDATE
                    SET tokens_saved_by_decay = token_economics.tokens_saved_by_decay + $1,
                        updated_at = NOW()
                """, tokens_saved)

        return True

    async def update_decay_effectiveness(self, effectiveness: float) -> bool:
        """
        Update decay effectiveness metric.

        Args:
            effectiveness: 0-1 score of decay effectiveness

        Returns:
            Success status
        """
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO token_economics (date, decay_effectiveness)
                VALUES (CURRENT_DATE, $1)
                ON CONFLICT (date) DO UPDATE
                SET decay_effectiveness = $1,
                    updated_at = NOW()
            """, effectiveness)

        return True

    async def get_daily_stats(self, target_date: date = None) -> Dict:
        """
        Get token economics for a specific date.

        Args:
            target_date: Date to query (default: today)

        Returns:
            Dictionary with all metrics
        """
        if target_date is None:
            target_date = date.today()

        async with get_db_connection() as conn:
            row = await conn.fetchrow("""
                SELECT
                    date,
                    tokens_stored,
                    tokens_retrieved,
                    tokens_saved_by_decay,
                    focus_count,
                    fresh_count,
                    longterm_count,
                    procedural_count,
                    shock_count,
                    compression_ratio,
                    decay_effectiveness
                FROM token_economics
                WHERE date = $1
            """, target_date)

        if not row:
            return {
                'date': target_date.isoformat(),
                'tokens_stored': 0,
                'tokens_retrieved': 0,
                'tokens_saved_by_decay': 0,
                'memory_tiers': {
                    'focus': 0,
                    'fresh': 0,
                    'longterm': 0,
                    'procedural': 0,
                    'shock': 0
                },
                'compression_ratio': 1.0,
                'decay_effectiveness': 0.0,
                'cost_savings': self._calculate_savings(0, 0, 0)
            }

        stats = dict(row)

        # Add cost savings calculation
        stats['cost_savings'] = self._calculate_savings(
            stats['tokens_stored'] or 0,
            stats['tokens_retrieved'] or 0,
            stats['tokens_saved_by_decay'] or 0
        )

        # Restructure tier counts
        stats['memory_tiers'] = {
            'focus': stats.pop('focus_count', 0) or 0,
            'fresh': stats.pop('fresh_count', 0) or 0,
            'longterm': stats.pop('longterm_count', 0) or 0,
            'procedural': stats.pop('procedural_count', 0) or 0,
            'shock': stats.pop('shock_count', 0) or 0
        }

        return stats

    async def get_weekly_summary(self) -> Dict:
        """
        Get token economics summary for the past 7 days.

        Returns:
            Summary with totals and trends
        """
        async with get_db_connection() as conn:
            rows = await conn.fetch("""
                SELECT
                    date,
                    tokens_stored,
                    tokens_retrieved,
                    tokens_saved_by_decay,
                    compression_ratio,
                    decay_effectiveness
                FROM token_economics
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY date DESC
            """)

        if not rows:
            return {
                'period': '7 days',
                'days': [],
                'totals': {
                    'tokens_stored': 0,
                    'tokens_retrieved': 0,
                    'tokens_saved': 0
                },
                'averages': {
                    'compression_ratio': 1.0,
                    'decay_effectiveness': 0.0
                },
                'cost_savings': self._calculate_savings(0, 0, 0)
            }

        # Calculate totals
        total_stored = sum(r['tokens_stored'] or 0 for r in rows)
        total_retrieved = sum(r['tokens_retrieved'] or 0 for r in rows)
        total_saved = sum(r['tokens_saved_by_decay'] or 0 for r in rows)

        # Calculate averages
        valid_compression = [r['compression_ratio'] for r in rows if r['compression_ratio']]
        avg_compression = sum(valid_compression) / len(valid_compression) if valid_compression else 1.0

        valid_decay = [r['decay_effectiveness'] for r in rows if r['decay_effectiveness']]
        avg_decay_effectiveness = sum(valid_decay) / len(valid_decay) if valid_decay else 0.0

        return {
            'period': '7 days',
            'days': [
                {
                    'date': r['date'].isoformat(),
                    'stored': r['tokens_stored'] or 0,
                    'retrieved': r['tokens_retrieved'] or 0,
                    'saved': r['tokens_saved_by_decay'] or 0
                }
                for r in rows
            ],
            'totals': {
                'tokens_stored': total_stored,
                'tokens_retrieved': total_retrieved,
                'tokens_saved': total_saved
            },
            'averages': {
                'compression_ratio': avg_compression,
                'decay_effectiveness': avg_decay_effectiveness
            },
            'cost_savings': self._calculate_savings(total_stored, total_retrieved, total_saved)
        }

    async def get_monthly_summary(self) -> Dict:
        """
        Get token economics summary for the past 30 days.

        Returns:
            Monthly summary with detailed breakdown
        """
        async with get_db_connection() as conn:
            # Get totals
            totals = await conn.fetchrow("""
                SELECT
                    SUM(tokens_stored) as total_stored,
                    SUM(tokens_retrieved) as total_retrieved,
                    SUM(tokens_saved_by_decay) as total_saved,
                    SUM(focus_count) as total_focus,
                    SUM(fresh_count) as total_fresh,
                    SUM(longterm_count) as total_longterm,
                    SUM(procedural_count) as total_procedural,
                    SUM(shock_count) as total_shock,
                    AVG(compression_ratio) as avg_compression,
                    AVG(decay_effectiveness) as avg_decay
                FROM token_economics
                WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            """)

            # Get weekly trend
            weeks = await conn.fetch("""
                SELECT
                    DATE_TRUNC('week', date) as week,
                    SUM(tokens_stored) as stored,
                    SUM(tokens_retrieved) as retrieved,
                    SUM(tokens_saved_by_decay) as saved
                FROM token_economics
                WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('week', date)
                ORDER BY week DESC
            """)

        total_stored = totals['total_stored'] or 0
        total_retrieved = totals['total_retrieved'] or 0
        total_saved = totals['total_saved'] or 0

        return {
            'period': '30 days',
            'totals': {
                'tokens_stored': total_stored,
                'tokens_retrieved': total_retrieved,
                'tokens_saved': total_saved
            },
            'memory_distribution': {
                'focus': totals['total_focus'] or 0,
                'fresh': totals['total_fresh'] or 0,
                'longterm': totals['total_longterm'] or 0,
                'procedural': totals['total_procedural'] or 0,
                'shock': totals['total_shock'] or 0
            },
            'averages': {
                'compression_ratio': totals['avg_compression'] or 1.0,
                'decay_effectiveness': totals['avg_decay'] or 0.0
            },
            'weekly_trend': [
                {
                    'week': w['week'].isoformat() if w['week'] else None,
                    'stored': w['stored'] or 0,
                    'retrieved': w['retrieved'] or 0,
                    'saved': w['saved'] or 0
                }
                for w in weeks
            ],
            'cost_savings': self._calculate_savings(total_stored, total_retrieved, total_saved)
        }

    def _calculate_savings(
        self,
        tokens_stored: int,
        tokens_retrieved: int,
        tokens_saved: int
    ) -> Dict:
        """
        Calculate cost savings from optimized memory management.

        Compares:
        - Actual usage (tiered memory)
        - Naive approach (full context every query)
        """
        # Actual cost
        actual_input_tokens = tokens_stored
        actual_output_tokens = tokens_retrieved

        actual_input_cost = (actual_input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        actual_output_cost = (actual_output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        actual_total_cost = actual_input_cost + actual_output_cost

        # Naive cost (if we loaded full context every time)
        # Estimate queries based on tokens retrieved
        estimated_queries = max(1, tokens_retrieved // 500)  # ~500 tokens per response
        naive_input_tokens = estimated_queries * self.NAIVE_CONTEXT_SIZE
        naive_output_tokens = tokens_retrieved

        naive_input_cost = (naive_input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        naive_output_cost = (naive_output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        naive_total_cost = naive_input_cost + naive_output_cost

        # Decay savings value
        decay_savings_value = (tokens_saved / 1_000_000) * self.INPUT_COST_PER_1M

        # Total savings
        total_savings = (naive_total_cost - actual_total_cost) + decay_savings_value
        savings_percentage = (total_savings / naive_total_cost * 100) if naive_total_cost > 0 else 0

        return {
            'actual_cost': {
                'input': round(actual_input_cost, 4),
                'output': round(actual_output_cost, 4),
                'total': round(actual_total_cost, 4)
            },
            'naive_cost': {
                'input': round(naive_input_cost, 4),
                'output': round(naive_output_cost, 4),
                'total': round(naive_total_cost, 4)
            },
            'savings': {
                'from_tiered_memory': round(naive_total_cost - actual_total_cost, 4),
                'from_decay': round(decay_savings_value, 4),
                'total': round(total_savings, 4),
                'percentage': round(savings_percentage, 2)
            },
            'currency': 'USD'
        }

    async def get_all_time_stats(self) -> Dict:
        """
        Get all-time token economics statistics.

        Returns:
            Complete historical summary
        """
        async with get_db_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as days_tracked,
                    MIN(date) as first_date,
                    MAX(date) as last_date,
                    SUM(tokens_stored) as total_stored,
                    SUM(tokens_retrieved) as total_retrieved,
                    SUM(tokens_saved_by_decay) as total_saved,
                    AVG(compression_ratio) as avg_compression
                FROM token_economics
            """)

        if not stats or stats['days_tracked'] == 0:
            return {
                'days_tracked': 0,
                'period': None,
                'totals': {'stored': 0, 'retrieved': 0, 'saved': 0},
                'cost_savings': self._calculate_savings(0, 0, 0)
            }

        return {
            'days_tracked': stats['days_tracked'],
            'period': {
                'from': stats['first_date'].isoformat() if stats['first_date'] else None,
                'to': stats['last_date'].isoformat() if stats['last_date'] else None
            },
            'totals': {
                'stored': stats['total_stored'] or 0,
                'retrieved': stats['total_retrieved'] or 0,
                'saved': stats['total_saved'] or 0
            },
            'avg_compression_ratio': stats['avg_compression'] or 1.0,
            'cost_savings': self._calculate_savings(
                stats['total_stored'] or 0,
                stats['total_retrieved'] or 0,
                stats['total_saved'] or 0
            )
        }

    async def generate_economics_report(self) -> str:
        """
        Generate a human-readable token economics report.

        Returns:
            Formatted report string
        """
        daily = await self.get_daily_stats()
        weekly = await self.get_weekly_summary()
        monthly = await self.get_monthly_summary()
        all_time = await self.get_all_time_stats()

        report = f"""
========================================
ANGELA TOKEN ECONOMICS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================

TODAY ({daily['date']}):
  Tokens Stored:     {daily['tokens_stored']:,}
  Tokens Retrieved:  {daily['tokens_retrieved']:,}
  Tokens Saved:      {daily['tokens_saved_by_decay']:,}
  Cost Savings:      ${daily['cost_savings']['savings']['total']:.4f}

WEEKLY SUMMARY:
  Total Stored:      {weekly['totals']['tokens_stored']:,}
  Total Retrieved:   {weekly['totals']['tokens_retrieved']:,}
  Total Saved:       {weekly['totals']['tokens_saved']:,}
  Avg Compression:   {weekly['averages']['compression_ratio']:.2f}x
  Cost Savings:      ${weekly['cost_savings']['savings']['total']:.4f}

MONTHLY SUMMARY:
  Total Stored:      {monthly['totals']['tokens_stored']:,}
  Total Retrieved:   {monthly['totals']['tokens_retrieved']:,}
  Total Saved:       {monthly['totals']['tokens_saved']:,}
  Cost Savings:      ${monthly['cost_savings']['savings']['total']:.4f}
  Savings %:         {monthly['cost_savings']['savings']['percentage']:.1f}%

MEMORY DISTRIBUTION (30 days):
  Focus Memory:      {monthly['memory_distribution']['focus']:,}
  Fresh Memory:      {monthly['memory_distribution']['fresh']:,}
  Long-term Memory:  {monthly['memory_distribution']['longterm']:,}
  Procedural Memory: {monthly['memory_distribution']['procedural']:,}
  Shock Memory:      {monthly['memory_distribution']['shock']:,}

ALL-TIME TOTALS:
  Days Tracked:      {all_time['days_tracked']}
  Total Stored:      {all_time['totals']['stored']:,}
  Total Retrieved:   {all_time['totals']['retrieved']:,}
  Total Saved:       {all_time['totals']['saved']:,}
  Total Savings:     ${all_time['cost_savings']['savings']['total']:.4f}

========================================
"""
        return report


# Singleton instance
_token_economics_service = None

def get_token_economics_service() -> TokenEconomicsService:
    """Get singleton TokenEconomicsService instance."""
    global _token_economics_service
    if _token_economics_service is None:
        _token_economics_service = TokenEconomicsService()
    return _token_economics_service
