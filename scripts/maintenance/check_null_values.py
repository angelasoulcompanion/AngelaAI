#!/usr/bin/env python3
"""
Check all tables in AngelaMemory database for NULL values
"""

import asyncio
import asyncpg
from datetime import datetime
import sys
import os

# Import centralized config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from angela_core.config import config

DATABASE_URL = config.DATABASE_URL


async def check_all_tables():
    """Check all tables for NULL values"""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("=" * 80)
        print("🔍 Checking AngelaMemory Database for NULL Values")
        print("=" * 80)
        print()

        # Get all tables
        tables = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        total_nulls = 0
        tables_with_nulls = []

        for table_record in tables:
            table_name = table_record['tablename']
            print(f"\n📋 Table: {table_name}")
            print("-" * 80)

            # Get all columns for this table
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """, table_name)

            table_has_nulls = False

            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']
                is_nullable = col['is_nullable']

                # Count NULLs in this column
                null_count = await conn.fetchval(f"""
                    SELECT COUNT(*)
                    FROM {table_name}
                    WHERE {col_name} IS NULL
                """)

                if null_count > 0:
                    print(f"   ⚠️  {col_name} ({col_type}): {null_count} NULL values")
                    total_nulls += null_count
                    table_has_nulls = True

                    # Show sample rows with NULLs
                    sample = await conn.fetch(f"""
                        SELECT * FROM {table_name}
                        WHERE {col_name} IS NULL
                        LIMIT 3
                    """)

                    if sample:
                        print(f"       Sample rows:")
                        for row in sample:
                            # Show primary key or first few columns
                            sample_data = dict(row)
                            print(f"         {list(sample_data.items())[:3]}")

            if table_has_nulls:
                tables_with_nulls.append(table_name)
            else:
                print("   ✅ No NULL values found")

        print("\n" + "=" * 80)
        print(f"📊 Summary:")
        print(f"   Total tables checked: {len(tables)}")
        print(f"   Tables with NULLs: {len(tables_with_nulls)}")
        print(f"   Total NULL values: {total_nulls}")

        if tables_with_nulls:
            print(f"\n   Tables needing attention:")
            for t in tables_with_nulls:
                print(f"      - {t}")
        else:
            print("\n   ✅ All tables are clean! No NULL values found.")

        print("=" * 80)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_all_tables())
