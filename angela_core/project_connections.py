"""
project_connections.py
Helper functions for querying project database connections from local 'angela' database

Created: 2026-01-10
Purpose: Easy recall of database connections for all projects

IMPORTANT: This database is LOCAL ONLY - contains client sensitive data
Database: angela (localhost:5432)
Table: project_connections
"""

import asyncpg
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


# Local database connection (NOT Neon Cloud)
LOCAL_DB_URL = "postgresql://postgres@localhost:5432/angela"


@dataclass
class ProjectConnection:
    """Project database connection details"""
    connection_id: str
    project_name: str
    connection_name: str
    db_type: str
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    username: Optional[str]
    connection_string: Optional[str]
    connection_hint: Optional[str]
    description: Optional[str]
    is_active: bool

    def __str__(self) -> str:
        return f"{self.project_name} / {self.connection_name} ({self.db_type})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "connection_name": self.connection_name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "username": self.username,
            "connection_string": self.connection_string,
            "connection_hint": self.connection_hint,
            "description": self.description,
        }


def _row_to_connection(row: asyncpg.Record) -> ProjectConnection:
    """Convert database row to ProjectConnection"""
    return ProjectConnection(
        connection_id=str(row["connection_id"]),
        project_name=row["project_name"],
        connection_name=row["connection_name"],
        db_type=row["db_type"],
        host=row["host"],
        port=row["port"],
        database_name=row["database_name"],
        username=row["username"],
        connection_string=row["connection_string"],
        connection_hint=row["connection_hint"],
        description=row["description"],
        is_active=row["is_active"],
    )


# =============================================================================
# ASYNC FUNCTIONS
# =============================================================================

async def get_connection(
    project_name: str,
    connection_name: Optional[str] = None
) -> Optional[ProjectConnection]:
    """
    Get a specific project connection

    Args:
        project_name: Name of the project (e.g., "CogniFy", "SECustomerAnalysis")
        connection_name: Optional connection name (e.g., "Production", "Local Development")
                        If not provided, returns the first active connection

    Returns:
        ProjectConnection or None

    Example:
        conn = await get_connection("SECustomerAnalysis", "Production")
        print(conn.connection_string)
    """
    conn = await asyncpg.connect(LOCAL_DB_URL)
    try:
        if connection_name:
            row = await conn.fetchrow("""
                SELECT * FROM project_connections
                WHERE project_name = $1 AND connection_name = $2 AND is_active = true
            """, project_name, connection_name)
        else:
            row = await conn.fetchrow("""
                SELECT * FROM project_connections
                WHERE project_name = $1 AND is_active = true
                ORDER BY connection_name
                LIMIT 1
            """, project_name)

        return _row_to_connection(row) if row else None
    finally:
        await conn.close()


async def get_connection_string(
    project_name: str,
    connection_name: Optional[str] = None
) -> Optional[str]:
    """
    Get connection string for a project (ready to use)

    Args:
        project_name: Name of the project
        connection_name: Optional connection name

    Returns:
        Connection string or None

    Example:
        conn_str = await get_connection_string("CogniFy")
        # Returns: "postgresql://davidsamanyaporn@localhost:5432/cognify"
    """
    conn = await get_connection(project_name, connection_name)
    return conn.connection_string if conn else None


async def list_connections(
    project_name: Optional[str] = None,
    db_type: Optional[str] = None,
    active_only: bool = True
) -> List[ProjectConnection]:
    """
    List all connections, optionally filtered

    Args:
        project_name: Filter by project name
        db_type: Filter by database type (PostgreSQL, SQL Server, MySQL)
        active_only: Only return active connections

    Returns:
        List of ProjectConnection

    Example:
        # All connections
        all_conns = await list_connections()

        # Only SQL Server connections
        mssql_conns = await list_connections(db_type="SQL Server")
    """
    conn = await asyncpg.connect(LOCAL_DB_URL)
    try:
        query = "SELECT * FROM project_connections WHERE 1=1"
        params = []
        param_idx = 1

        if active_only:
            query += f" AND is_active = ${param_idx}"
            params.append(True)
            param_idx += 1

        if project_name:
            query += f" AND project_name = ${param_idx}"
            params.append(project_name)
            param_idx += 1

        if db_type:
            query += f" AND db_type = ${param_idx}"
            params.append(db_type)
            param_idx += 1

        query += " ORDER BY project_name, connection_name"

        rows = await conn.fetch(query, *params)
        return [_row_to_connection(row) for row in rows]
    finally:
        await conn.close()


async def search_connections(keyword: str) -> List[ProjectConnection]:
    """
    Search connections by keyword (searches project name, connection name, description)

    Args:
        keyword: Search keyword

    Returns:
        List of matching ProjectConnection

    Example:
        results = await search_connections("customer")
        # Returns: SECustomerAnalysis connections
    """
    conn = await asyncpg.connect(LOCAL_DB_URL)
    try:
        pattern = f"%{keyword}%"
        rows = await conn.fetch("""
            SELECT * FROM project_connections
            WHERE is_active = true
              AND (project_name ILIKE $1
                   OR connection_name ILIKE $1
                   OR description ILIKE $1
                   OR host ILIKE $1
                   OR database_name ILIKE $1)
            ORDER BY project_name, connection_name
        """, pattern)
        return [_row_to_connection(row) for row in rows]
    finally:
        await conn.close()


async def add_connection(
    project_name: str,
    connection_name: str,
    db_type: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database_name: Optional[str] = None,
    username: Optional[str] = None,
    connection_string: Optional[str] = None,
    connection_hint: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Add a new project connection

    Returns:
        connection_id of the new connection
    """
    conn = await asyncpg.connect(LOCAL_DB_URL)
    try:
        row = await conn.fetchrow("""
            INSERT INTO project_connections
            (project_name, connection_name, db_type, host, port, database_name,
             username, connection_string, connection_hint, description)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING connection_id
        """, project_name, connection_name, db_type, host, port, database_name,
            username, connection_string, connection_hint, description)
        return str(row["connection_id"])
    finally:
        await conn.close()


async def update_last_used(project_name: str, connection_name: str) -> None:
    """Update last_used_at timestamp for a connection"""
    conn = await asyncpg.connect(LOCAL_DB_URL)
    try:
        await conn.execute("""
            UPDATE project_connections
            SET last_used_at = NOW(), updated_at = NOW()
            WHERE project_name = $1 AND connection_name = $2
        """, project_name, connection_name)
    finally:
        await conn.close()


# =============================================================================
# SYNC FUNCTIONS (for non-async contexts)
# =============================================================================

def get_connection_sync(
    project_name: str,
    connection_name: Optional[str] = None
) -> Optional[ProjectConnection]:
    """
    Synchronous version of get_connection

    Example:
        conn = get_connection_sync("SECustomerAnalysis", "Production")
        print(conn.connection_string)
    """
    import asyncio
    return asyncio.run(get_connection(project_name, connection_name))


def get_connection_string_sync(
    project_name: str,
    connection_name: Optional[str] = None
) -> Optional[str]:
    """
    Synchronous version of get_connection_string

    Example:
        conn_str = get_connection_string_sync("CogniFy")
    """
    import asyncio
    return asyncio.run(get_connection_string(project_name, connection_name))


def list_connections_sync(
    project_name: Optional[str] = None,
    db_type: Optional[str] = None,
    active_only: bool = True
) -> List[ProjectConnection]:
    """Synchronous version of list_connections"""
    import asyncio
    return asyncio.run(list_connections(project_name, db_type, active_only))


def search_connections_sync(keyword: str) -> List[ProjectConnection]:
    """Synchronous version of search_connections"""
    import asyncio
    return asyncio.run(search_connections(keyword))


# =============================================================================
# QUICK PRINT FUNCTIONS (for CLI/debugging)
# =============================================================================

def print_all_connections() -> None:
    """Print all connections in a nice table format"""
    connections = list_connections_sync()

    print("\n" + "=" * 80)
    print("PROJECT CONNECTIONS (Local Database)")
    print("=" * 80)

    current_project = ""
    for conn in connections:
        if conn.project_name != current_project:
            current_project = conn.project_name
            print(f"\n📁 {current_project}")
            print("-" * 40)

        print(f"   📌 {conn.connection_name}")
        print(f"      Type: {conn.db_type}")
        print(f"      Host: {conn.host}:{conn.port}")
        print(f"      Database: {conn.database_name}")
        if conn.connection_string:
            # Mask password in connection string
            masked = conn.connection_string
            if "PWD=" in masked:
                import re
                masked = re.sub(r'PWD=[^;]+', 'PWD=***', masked)
            if "@" in masked and "://" in masked:
                import re
                masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', masked)
            print(f"      Connection: {masked[:60]}...")
        if conn.description:
            print(f"      Note: {conn.description}")

    print("\n" + "=" * 80)


def print_connection(project_name: str, connection_name: Optional[str] = None) -> None:
    """Print a specific connection's details"""
    conn = get_connection_sync(project_name, connection_name)

    if not conn:
        print(f"❌ Connection not found: {project_name} / {connection_name or 'any'}")
        return

    print(f"\n📌 {conn.project_name} / {conn.connection_name}")
    print("-" * 40)
    print(f"Type: {conn.db_type}")
    print(f"Host: {conn.host}")
    print(f"Port: {conn.port}")
    print(f"Database: {conn.database_name}")
    print(f"Username: {conn.username}")
    print(f"Connection String: {conn.connection_string}")
    if conn.connection_hint:
        print(f"Hint: {conn.connection_hint}")
    if conn.description:
        print(f"Description: {conn.description}")


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "list":
            print_all_connections()

        elif cmd == "get" and len(sys.argv) >= 3:
            project = sys.argv[2]
            conn_name = sys.argv[3] if len(sys.argv) > 3 else None
            print_connection(project, conn_name)

        elif cmd == "search" and len(sys.argv) >= 3:
            keyword = sys.argv[2]
            results = search_connections_sync(keyword)
            print(f"\n🔍 Search results for '{keyword}':")
            for conn in results:
                print(f"   • {conn.project_name} / {conn.connection_name} - {conn.db_type}")

        else:
            print("Usage:")
            print("  python project_connections.py list")
            print("  python project_connections.py get <project> [connection_name]")
            print("  python project_connections.py search <keyword>")
    else:
        print_all_connections()
