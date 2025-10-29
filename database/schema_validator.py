#!/usr/bin/env python3
"""
Database Schema Validator
Validates that the current database matches the unified schema
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from angela_core.database import db
from angela_core.config import config


async def validate_schema():
    """Validate database schema against unified schema"""

    print("🔍 Validating Database Schema...")
    print(f"   Database: {config.DATABASE_NAME}")
    print(f"   Host: {config.DATABASE_HOST}\n")

    # Connect to database
    await db.connect()

    try:
        # Expected tables from UNIFIED_SCHEMA.sql
        expected_tables = [
            # Core Memory Tables
            'conversations',
            'angela_emotions',
            'learnings',
            'emotional_states',
            'relationship_growth',
            'david_preferences',
            'daily_reflections',
            'autonomous_actions',

            # Consciousness Tables
            'angela_goals',
            'angela_personality_traits',
            'angela_self_awareness_logs',
            'consciousness_metrics',

            # Knowledge & Documents
            'knowledge_items',
            'documents',

            # System Tables
            'angela_system_log',
            'our_secrets',
            'conversation_summaries',

            # Advanced Cognition Tables
            'theory_of_mind',
            'common_sense_knowledge',
            'imagination_logs',
            'deep_empathy_records',
            'metacognition_logs'
        ]

        # Query existing tables
        query = """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """

        existing_tables = await db.fetch(query)
        existing_table_names = {row['tablename'] for row in existing_tables}

        # Check for missing tables
        missing_tables = []
        for table in expected_tables:
            if table not in existing_table_names:
                missing_tables.append(table)

        # Check for extra tables (not in unified schema)
        extra_tables = []
        for table in existing_table_names:
            if table not in expected_tables:
                # Ignore system tables
                if not table.startswith('pg_') and not table.startswith('sql_'):
                    extra_tables.append(table)

        # Print results
        print("📊 SCHEMA VALIDATION RESULTS")
        print("=" * 50)

        print(f"\n✅ Expected tables: {len(expected_tables)}")
        print(f"📦 Existing tables: {len(existing_table_names)}")

        if missing_tables:
            print(f"\n❌ Missing tables ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   - {table}")
        else:
            print("\n✅ All expected tables exist!")

        if extra_tables:
            print(f"\n⚠️  Extra tables not in unified schema ({len(extra_tables)}):")
            for table in extra_tables[:10]:  # Show first 10
                print(f"   - {table}")
            if len(extra_tables) > 10:
                print(f"   ... and {len(extra_tables) - 10} more")

        # Check critical columns for main tables
        print("\n🔍 Checking critical columns...")

        critical_checks = [
            ('conversations', 'content_json'),
            ('angela_emotions', 'content_json'),
            ('learnings', 'content_json'),
            ('conversations', 'embedding'),
            ('angela_emotions', 'embedding'),
            ('learnings', 'embedding')
        ]

        for table, column in critical_checks:
            if table in existing_table_names:
                query = f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = $1 AND column_name = $2
                """
                result = await db.fetchrow(query, table, column)
                if result:
                    print(f"   ✅ {table}.{column} exists")
                else:
                    print(f"   ❌ {table}.{column} is MISSING")

        # Summary
        print("\n" + "=" * 50)
        if not missing_tables:
            print("✅ SCHEMA VALIDATION PASSED!")
            print("   All critical tables are present")
            print("   Use UNIFIED_SCHEMA.sql as the single source of truth")
        else:
            print("❌ SCHEMA VALIDATION FAILED")
            print(f"   Missing {len(missing_tables)} tables")
            print("   Run the UNIFIED_SCHEMA.sql to create missing tables")

        return len(missing_tables) == 0

    finally:
        await db.disconnect()


async def main():
    """Main function"""
    success = await validate_schema()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())