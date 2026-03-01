"""
Pythia helpers — shared utilities for routers and services.
"""
from typing import Any, Optional


class DynamicUpdate:
    """Builder for dynamic SQL UPDATE statements with parameterized queries."""

    def __init__(self) -> None:
        self._sets: list[str] = []
        self._values: list[Any] = []
        self._idx = 0

    def add(self, column: str, value: Any) -> "DynamicUpdate":
        if value is not None:
            self._idx += 1
            self._sets.append(f"{column} = ${self._idx}")
            self._values.append(value)
        return self

    def build(self, table: str, where_col: str, where_val: Any) -> tuple[str, list[Any]]:
        if not self._sets:
            raise ValueError("No fields to update")
        self._idx += 1
        sql = f"UPDATE {table} SET {', '.join(self._sets)}, updated_at = NOW() WHERE {where_col} = ${self._idx}"
        self._values.append(where_val)
        return sql, self._values

    @property
    def has_updates(self) -> bool:
        return len(self._sets) > 0
