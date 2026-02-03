"""Shared utilities for Angela Brain Dashboard backend."""
from datetime import date, datetime

from fastapi import HTTPException


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize a dict of scores so values sum to 1.0."""
    total = sum(scores.values())
    return {k: v / total for k, v in scores.items()} if total > 0 else scores


def parse_date(value: str, field_name: str = "date") -> date:
    """Parse YYYY-MM-DD string into date, raising HTTPException on failure."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format. Use YYYY-MM-DD")


class DynamicUpdate:
    """Builder for dynamic UPDATE queries with parameterized placeholders.

    Usage:
        b = DynamicUpdate()
        if body.title is not None:
            b.add("title", body.title)
        if body.priority is not None:
            b.add("priority", body.priority)
        b.add_literal("updated_at = NOW()")
        query, params = b.build("meeting_notes", "meeting_id", meeting_id, cast="::uuid")
        row = await conn.fetchrow(query, *params)
    """

    def __init__(self) -> None:
        self._sets: list[str] = []
        self._params: list = []
        self._idx: int = 1

    def add(self, column: str, value) -> "DynamicUpdate":
        """Add a parameterized SET clause."""
        self._sets.append(f"{column} = ${self._idx}")
        self._params.append(value)
        self._idx += 1
        return self

    def add_literal(self, expr: str) -> "DynamicUpdate":
        """Add a literal SET clause (no parameter)."""
        self._sets.append(expr)
        return self

    @property
    def has_updates(self) -> bool:
        return len(self._sets) > 0

    def build(
        self,
        table: str,
        where_col: str,
        where_val,
        *,
        cast: str = "",
        returning: str = "",
    ) -> tuple[str, list]:
        """Build the UPDATE query and params list.

        Returns (sql, params).
        """
        self._params.append(where_val)
        where_clause = f"WHERE {where_col} = ${self._idx}{cast}"
        ret = f"\nRETURNING {returning}" if returning else ""
        sql = f"UPDATE {table}\nSET {', '.join(self._sets)}\n{where_clause}{ret}"
        return sql, self._params
