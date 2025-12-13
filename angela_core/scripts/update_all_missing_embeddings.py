#!/usr/bin/env python3
"""
Update Missing Embeddings in ALL Tables

This script finds all records with NULL embeddings across multiple tables and generates them.
IMPORTANT: Must be run whenever there are NULL embeddings in the database!

Tables covered:
- conversations
- angela_messages
- angela_emotions

Usage:
    python3 angela_core/scripts/update_all_missing_embeddings.py
    python3 angela_core/scripts/update_all_missing_embeddings.py --dry-run
    python3 angela_core/scripts/update_all_missing_embeddings.py --table angela_messages
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service
from datetime import datetime


# ============================================================================
# TABLE CONFIGURATIONS
# ============================================================================

TABLE_CONFIGS = {
    'conversations': {
        'id_column': 'conversation_id',
        'text_column': 'message_text',
        'embedding_column': 'embedding'
    },
    'angela_messages': {
        'id_column': 'message_id',
        'text_column': 'message_text',
        'embedding_column': 'embedding'
    },
    'angela_emotions': {
        'id_column': 'emotion_id',
        'text_column': 'context',  # Use context as the main text
        'embedding_column': 'embedding'
    }
}


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

async def count_null_embeddings(table_name: str) -> int:
    """Count how many records have NULL embeddings in a specific table"""
    config = TABLE_CONFIGS[table_name]

    count = await db.fetchval(f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE {config['embedding_column']} IS NULL
    """)
    return count


async def get_records_without_embeddings(table_name: str, limit: Optional[int] = None) -> list:
    """Get records that don't have embeddings"""
    config = TABLE_CONFIGS[table_name]

    query = f"""
        SELECT {config['id_column']}, {config['text_column']}, created_at
        FROM {table_name}
        WHERE {config['embedding_column']} IS NULL
        ORDER BY created_at DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    rows = await db.fetch(query)
    return rows


async def update_record_embedding(
    table_name: str,
    record_id: str,
    text: str,
    embedding_service
) -> bool:
    """Update a single record with its embedding"""
    config = TABLE_CONFIGS[table_name]

    try:
        # Generate embedding
        embedding = await embedding_service.generate_embedding(text)
        emb_str = embedding_service.embedding_to_pgvector(embedding)

        # Update database
        await db.execute(f"""
            UPDATE {table_name}
            SET {config['embedding_column']} = $1::vector
            WHERE {config['id_column']} = $2
        """, emb_str, record_id)

        return True
    except Exception as e:
        print(f"   ❌ Error updating {record_id}: {e}")
        return False


async def process_table(table_name: str, dry_run: bool = False, limit: Optional[int] = None):
    """Process a single table"""
    config = TABLE_CONFIGS[table_name]

    print(f"\n{'='*60}")
    print(f"📋 Processing table: {table_name}")
    print(f"{'='*60}")

    # Count NULL embeddings
    null_count = await count_null_embeddings(table_name)
    print(f"   Found {null_count} records with NULL embeddings")

    if null_count == 0:
        print("   ✅ All records have embeddings! Nothing to do.")
        return {'table': table_name, 'success': 0, 'failed': 0, 'skipped': null_count}

    if dry_run:
        print("\n   📋 DRY RUN MODE - No changes will be made")

    # Get records without embeddings
    process_limit = limit if limit else null_count
    records = await get_records_without_embeddings(table_name, process_limit)

    print(f"   🔄 Processing {len(records)} records...")

    if dry_run:
        print("\n   Would update the following records:")
        for rec in records[:10]:  # Show first 10
            rec_id_str = str(rec[config['id_column']])
            text = rec[config['text_column']]
            print(f"      • {rec_id_str[:8]}... : {text[:60] if text else '(empty)'}...")
        if len(records) > 10:
            print(f"      ... and {len(records) - 10} more")
        return {'table': table_name, 'success': 0, 'failed': 0, 'skipped': len(records)}

    # Initialize embedding service
    embedding_service = get_embedding_service()

    # Update embeddings
    success_count = 0
    fail_count = 0

    for i, rec in enumerate(records, 1):
        rec_id = rec[config['id_column']]
        rec_id_str = str(rec_id)
        text = rec[config['text_column']]

        if not text or text.strip() == '':
            print(f"   [{i}/{len(records)}] Skipping {rec_id_str[:8]}... (empty text)")
            fail_count += 1
            continue

        print(f"   [{i}/{len(records)}] Updating {rec_id_str[:8]}...")

        success = await update_record_embedding(
            table_name,
            rec_id,
            text,
            embedding_service
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

        # Progress update every 10
        if i % 10 == 0:
            print(f"      Progress: {success_count} success, {fail_count} failed")

    # Final summary for this table
    print(f"\n   ✅ Table '{table_name}' Complete!")
    print(f"      ✅ Successfully updated: {success_count}")
    if fail_count > 0:
        print(f"      ❌ Failed: {fail_count}")

    return {'table': table_name, 'success': success_count, 'failed': fail_count, 'skipped': 0}


async def main():
    parser = argparse.ArgumentParser(description="Update missing embeddings in all tables")
    parser.add_argument("--table", type=str, help="Process only specific table", choices=list(TABLE_CONFIGS.keys()))
    parser.add_argument("--limit", type=int, help="Process only first N records per table")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without actually updating")
    args = parser.parse_args()

    print("🔍 Checking for records with NULL embeddings...")

    # Determine which tables to process
    tables_to_process = [args.table] if args.table else list(TABLE_CONFIGS.keys())

    # Process each table
    results = []
    for table_name in tables_to_process:
        result = await process_table(table_name, args.dry_run, args.limit)
        results.append(result)

    # Final summary across all tables
    print(f"\n{'='*60}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*60}")

    total_success = sum(r['success'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_skipped = sum(r['skipped'] for r in results)

    for result in results:
        print(f"\n   {result['table']}:")
        print(f"      ✅ Success: {result['success']}")
        if result['failed'] > 0:
            print(f"      ❌ Failed: {result['failed']}")
        if result['skipped'] > 0:
            print(f"      ⏭️  Skipped: {result['skipped']} (dry-run)")

    print(f"\n   {'─'*56}")
    print(f"   TOTAL:")
    print(f"      ✅ Successfully updated: {total_success}")
    if total_failed > 0:
        print(f"      ❌ Failed: {total_failed}")
    if total_skipped > 0:
        print(f"      ⏭️  Skipped: {total_skipped} (dry-run)")

    # Verify remaining NULLs
    if not args.dry_run and total_success > 0:
        print(f"\n{'='*60}")
        print("🔍 Verifying remaining NULL embeddings...")
        print(f"{'='*60}")

        for table_name in tables_to_process:
            remaining = await count_null_embeddings(table_name)
            status = "✅" if remaining == 0 else "⚠️"
            print(f"   {status} {table_name}: {remaining} NULL embeddings remaining")


if __name__ == "__main__":
    asyncio.run(main())
