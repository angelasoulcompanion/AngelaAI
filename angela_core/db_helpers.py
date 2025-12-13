"""
db_helpers.py
Database helper utilities for async operations

Created: 2025-11-14
Purpose: Simplify database connection management
"""

from contextlib import asynccontextmanager
import asyncpg
from angela_core.database import get_db_connection


@asynccontextmanager
async def db_connection():
    """
    Async context manager for database connections

    Usage:
        async with db_connection() as conn:
            result = await conn.fetchrow("SELECT * FROM table")
        # Connection automatically released back to pool
    """
    db = get_db_connection()
    async with db.acquire() as conn:
        yield conn


async def execute_query(query: str, *args):
    """
    Execute a query and return results

    Args:
        query: SQL query
        *args: Query parameters

    Returns:
        Query result
    """
    async with db_connection() as conn:
        return await conn.fetch(query, *args)


async def execute_one(query: str, *args):
    """
    Execute a query and return single row

    Args:
        query: SQL query
        *args: Query parameters

    Returns:
        Single row or None
    """
    async with db_connection() as conn:
        return await conn.fetchrow(query, *args)


async def execute_scalar(query: str, *args):
    """
    Execute a query and return single value

    Args:
        query: SQL query
        *args: Query parameters

    Returns:
        Single value
    """
    async with db_connection() as conn:
        return await conn.fetchval(query, *args)
