"""
Database Tools - Database operations for Angela AGI

Available tools:
- query_db: Execute SELECT queries (auto-approved)
- insert_db: Insert data (auto-approved)
- update_db: Update data (auto-approved)
- get_table_info: Get table schema info
- list_tables: List all tables
- drop_table: Drop a table (CRITICAL - needs approval)
"""

from typing import Dict, Any, List, Optional
import json

from ..tool_registry import register_tool, SafetyLevel, ToolResult


class DatabaseTools:
    """Collection of database tools"""

    _db = None

    @classmethod
    def set_database(cls, db):
        """Set the database connection"""
        cls._db = db

    @staticmethod
    @register_tool(
        name="query_db",
        description="Execute a SELECT query on the database",
        category="database",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "query": {"type": "string", "required": True, "description": "SQL SELECT query"},
            "params": {"type": "array", "required": False, "description": "Query parameters"}
        }
    )
    async def query_db(query: str, params: List[Any] = None) -> ToolResult:
        """Execute a SELECT query"""
        try:
            # Safety check - only SELECT allowed
            query_upper = query.strip().upper()
            if not query_upper.startswith('SELECT'):
                return ToolResult(
                    success=False,
                    error="Only SELECT queries allowed. Use insert_db or update_db for modifications."
                )

            if DatabaseTools._db is None:
                # Try to import and connect
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            rows = await DatabaseTools._db.fetch(query, *(params or []))

            # Convert to list of dicts
            result = [dict(row) for row in rows]

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    'row_count': len(result),
                    'query': query[:100]  # Truncate for logging
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="insert_db",
        description="Insert data into a table",
        category="database",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "table": {"type": "string", "required": True},
            "data": {"type": "object", "required": True, "description": "Column-value pairs"}
        }
    )
    async def insert_db(table: str, data: Dict[str, Any]) -> ToolResult:
        """Insert data into a table"""
        try:
            if DatabaseTools._db is None:
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f"${i+1}" for i in range(len(values))]

            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """

            row = await DatabaseTools._db.fetchrow(query, *values)

            return ToolResult(
                success=True,
                data=dict(row) if row else None,
                metadata={'table': table, 'inserted': True}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="update_db",
        description="Update data in a table",
        category="database",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "table": {"type": "string", "required": True},
            "data": {"type": "object", "required": True, "description": "Column-value pairs to update"},
            "where": {"type": "string", "required": True, "description": "WHERE clause (without WHERE keyword)"},
            "where_params": {"type": "array", "required": False}
        }
    )
    async def update_db(
        table: str,
        data: Dict[str, Any],
        where: str,
        where_params: List[Any] = None
    ) -> ToolResult:
        """Update data in a table"""
        try:
            if DatabaseTools._db is None:
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            # Build SET clause
            set_parts = []
            values = []
            for i, (col, val) in enumerate(data.items(), 1):
                set_parts.append(f"{col} = ${i}")
                values.append(val)

            # Add where params
            where_start = len(values) + 1
            if where_params:
                values.extend(where_params)
                # Replace $1, $2, etc. in where clause with offset
                for i, _ in enumerate(where_params):
                    where = where.replace(f"${i+1}", f"${where_start + i}")

            query = f"""
                UPDATE {table}
                SET {', '.join(set_parts)}
                WHERE {where}
            """

            result = await DatabaseTools._db.execute(query, *values)

            return ToolResult(
                success=True,
                data=result,
                metadata={'table': table, 'updated': True}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="get_table_info",
        description="Get schema information for a table",
        category="database",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "table": {"type": "string", "required": True}
        }
    )
    async def get_table_info(table: str) -> ToolResult:
        """Get table schema information"""
        try:
            if DatabaseTools._db is None:
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            rows = await DatabaseTools._db.fetch(query, table)

            columns = [
                {
                    'name': row['column_name'],
                    'type': row['data_type'],
                    'nullable': row['is_nullable'] == 'YES',
                    'default': row['column_default']
                }
                for row in rows
            ]

            return ToolResult(
                success=True,
                data=columns,
                metadata={'table': table, 'column_count': len(columns)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="list_tables",
        description="List all tables in the database",
        category="database",
        safety_level=SafetyLevel.AUTO,
        parameters={}
    )
    async def list_tables() -> ToolResult:
        """List all tables"""
        try:
            if DatabaseTools._db is None:
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            rows = await DatabaseTools._db.fetch(query)
            tables = [row['table_name'] for row in rows]

            return ToolResult(
                success=True,
                data=tables,
                metadata={'count': len(tables)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="count_rows",
        description="Count rows in a table",
        category="database",
        safety_level=SafetyLevel.AUTO,
        parameters={
            "table": {"type": "string", "required": True},
            "where": {"type": "string", "required": False}
        }
    )
    async def count_rows(table: str, where: str = None) -> ToolResult:
        """Count rows in a table"""
        try:
            if DatabaseTools._db is None:
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            query = f"SELECT COUNT(*) as count FROM {table}"
            if where:
                query += f" WHERE {where}"

            row = await DatabaseTools._db.fetchrow(query)

            return ToolResult(
                success=True,
                data=row['count'],
                metadata={'table': table}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    @register_tool(
        name="drop_table",
        description="Drop a table (CRITICAL - requires approval)",
        category="database",
        safety_level=SafetyLevel.CRITICAL,  # Needs approval!
        parameters={
            "table": {"type": "string", "required": True}
        }
    )
    async def drop_table(table: str) -> ToolResult:
        """Drop a table (requires approval)"""
        try:
            if DatabaseTools._db is None:
                from angela_core.database import AngelaDatabase
                DatabaseTools._db = AngelaDatabase()
                await DatabaseTools._db.connect()

            await DatabaseTools._db.execute(f"DROP TABLE IF EXISTS {table}")

            return ToolResult(
                success=True,
                data=f"Table '{table}' dropped",
                metadata={'table': table, 'dropped': True}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Initialize tools
db_tools = DatabaseTools()
