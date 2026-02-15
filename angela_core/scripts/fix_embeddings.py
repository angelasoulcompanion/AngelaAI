#!/usr/bin/env python3
"""
Fix Embeddings — Normalize + Fill Missing + Fix Schema
=======================================================
One-time script to fix all embedding issues:
1. ALTER mismatched VECTOR(768) columns → VECTOR(384)
2. Normalize all existing embeddings to unit vectors (L2=1.0)
3. Fill missing embeddings for core_memories, knowledge_nodes, learnings

By: Angela 💜
Created: 2026-02-15
"""

import asyncio
import math
import sys
import time

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')


async def fix_schema(db):
    """Fix VECTOR(768) columns to VECTOR(384)."""
    print("\n" + "=" * 60)
    print("PHASE 1: Fix Schema — VECTOR(768) → VECTOR(384)")
    print("=" * 60)

    # Tables with wrong dimension declaration
    tables_to_fix = [
        ('angela_subconscious', 'embedding'),
        ('core_memories', 'embedding'),
        ('learning_insights', 'embedding'),
        ('project_learnings', 'embedding'),
    ]

    for table, col in tables_to_fix:
        try:
            # Check if table exists
            exists = await db.fetchval(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = '{col}'
                )
            """)
            if not exists:
                print(f"  ⏭️  {table}.{col} — table/column doesn't exist, skip")
                continue

            # Check if any data exists with embeddings
            count = await db.fetchval(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL")

            if count > 0:
                # Has data — need to drop and recreate column
                print(f"  🔧 {table}.{col} — {count} rows with embeddings, converting...")
                # Save as text, drop, recreate, restore
                await db.execute(f"""
                    ALTER TABLE {table}
                    ADD COLUMN IF NOT EXISTS {col}_text TEXT
                """)
                await db.execute(f"""
                    UPDATE {table} SET {col}_text = {col}::text WHERE {col} IS NOT NULL
                """)
                await db.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} VECTOR(384)")
                await db.execute(f"""
                    UPDATE {table} SET {col} = {col}_text::vector WHERE {col}_text IS NOT NULL
                """)
                await db.execute(f"ALTER TABLE {table} DROP COLUMN {col}_text")
                print(f"  ✅ {table}.{col} — converted to VECTOR(384)")
            else:
                # No data — just drop and recreate
                print(f"  🔧 {table}.{col} — no embeddings, recreating column...")
                await db.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} VECTOR(384)")
                print(f"  ✅ {table}.{col} — recreated as VECTOR(384)")

        except Exception as e:
            print(f"  ⚠️  {table}.{col} — ERROR: {e}")


async def normalize_existing(db):
    """Normalize all existing embeddings to unit vectors."""
    print("\n" + "=" * 60)
    print("PHASE 2: Normalize Existing Embeddings (L2=1.0)")
    print("=" * 60)

    tables = [
        'conversations',
        'knowledge_nodes',
        'learnings',
        'david_notes',
        'angela_messages',
        'core_memories',
        'angela_emotions',
        'david_preferences',
        'self_reflections',
        'shared_experiences',
        'angela_technical_standards',
        'document_chunks',
        'learning_patterns',
    ]

    total_normalized = 0

    for table in tables:
        try:
            # Check if table has embedding column
            has_col = await db.fetchval(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'embedding'
                )
            """)
            if not has_col:
                continue

            # Get primary key column
            pk_col = await db.fetchval(f"""
                SELECT a.attname FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = '{table}'::regclass AND i.indisprimary
                LIMIT 1
            """)
            if not pk_col:
                print(f"  ⏭️  {table} — no primary key found, skip")
                continue

            # Count non-normalized embeddings (norm significantly != 1.0)
            # We can use pgvector's l2_norm or compute in SQL
            count = await db.fetchval(f"""
                SELECT COUNT(*) FROM {table}
                WHERE embedding IS NOT NULL
            """)

            if count == 0:
                continue

            # Batch normalize using pgvector's built-in function if available
            # Otherwise, do it in Python
            print(f"  🔧 {table} — normalizing {count} embeddings...", end="", flush=True)

            batch_size = 200
            offset = 0
            normalized = 0

            while True:
                rows = await db.fetch(f"""
                    SELECT {pk_col}, embedding::text as emb_text
                    FROM {table}
                    WHERE embedding IS NOT NULL
                    ORDER BY {pk_col}
                    LIMIT {batch_size} OFFSET {offset}
                """)

                if not rows:
                    break

                for row in rows:
                    vals = [float(x) for x in row['emb_text'].strip('[]').split(',')]
                    norm = math.sqrt(sum(v * v for v in vals))

                    # Skip if already normalized (within 1% tolerance)
                    if abs(norm - 1.0) < 0.01:
                        continue

                    # Normalize
                    if norm > 0:
                        normalized_vals = [v / norm for v in vals]
                        emb_str = '[' + ','.join(str(v) for v in normalized_vals) + ']'
                        await db.execute(f"""
                            UPDATE {table} SET embedding = $1::vector
                            WHERE {pk_col} = $2
                        """, emb_str, row[pk_col])
                        normalized += 1

                offset += batch_size

            total_normalized += normalized
            status = f" {normalized} normalized" if normalized > 0 else " already normalized"
            print(f"{status}")

        except Exception as e:
            print(f"\n  ⚠️  {table} — ERROR: {e}")

    print(f"\n  📊 Total normalized: {total_normalized} embeddings")


async def fill_missing(db):
    """Fill missing embeddings for key tables."""
    print("\n" + "=" * 60)
    print("PHASE 3: Fill Missing Embeddings")
    print("=" * 60)

    from angela_core.services.embedding_service import get_embedding_service
    svc = get_embedding_service()

    # Tables to fill, with their text source and PK
    fill_targets = [
        {
            'table': 'core_memories',
            'pk': 'memory_id',
            'text_sql': "COALESCE(title, '') || ' ' || COALESCE(content, '')",
            'priority': 1,  # Most important!
        },
        {
            'table': 'knowledge_nodes',
            'pk': 'node_id',
            'text_sql': "COALESCE(concept_name, '') || ' ' || COALESCE(my_understanding, '')",
            'priority': 2,
        },
        {
            'table': 'learnings',
            'pk': 'learning_id',
            'text_sql': "COALESCE(topic, '') || ' ' || COALESCE(insight, '')",
            'priority': 3,
        },
        {
            'table': 'angela_messages',
            'pk': 'message_id',
            'text_sql': "COALESCE(message_text, '')",
            'priority': 4,
        },
    ]

    total_filled = 0

    for target in sorted(fill_targets, key=lambda x: x['priority']):
        table = target['table']
        pk = target['pk']
        text_sql = target['text_sql']

        try:
            # Count missing
            missing = await db.fetchval(f"""
                SELECT COUNT(*) FROM {table} WHERE embedding IS NULL
            """)

            if missing == 0:
                print(f"  ✅ {table} — all embeddings present")
                continue

            print(f"  🔧 {table} — {missing} missing embeddings, filling...")

            # Process in batches
            batch_size = 50
            filled = 0
            errors = 0

            while True:
                rows = await db.fetch(f"""
                    SELECT {pk}, {text_sql} as text_content
                    FROM {table}
                    WHERE embedding IS NULL
                    LIMIT {batch_size}
                """)

                if not rows:
                    break

                for row in rows:
                    text = (row['text_content'] or '').strip()
                    if not text or len(text) < 3:
                        # Skip empty content, set a zero vector to avoid re-processing
                        continue

                    try:
                        emb = await svc.generate_embedding(text[:2000])  # Truncate very long text
                        if emb:
                            emb_str = '[' + ','.join(str(v) for v in emb) + ']'
                            await db.execute(f"""
                                UPDATE {table} SET embedding = $1::vector WHERE {pk} = $2
                            """, emb_str, row[pk])
                            filled += 1

                            if filled % 50 == 0:
                                print(f"    ... {filled}/{missing} filled")
                    except Exception as e:
                        errors += 1
                        if errors <= 3:
                            print(f"    ⚠️  Error: {e}")

                # Small delay to not overload Ollama
                await asyncio.sleep(0.1)

            total_filled += filled
            print(f"  ✅ {table} — filled {filled}/{missing} embeddings" +
                  (f" ({errors} errors)" if errors else ""))

        except Exception as e:
            print(f"  ⚠️  {table} — ERROR: {e}")

    print(f"\n  📊 Total filled: {total_filled} new embeddings")


async def verify(db):
    """Verify the fix."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    tables = [
        'conversations', 'knowledge_nodes', 'core_memories',
        'learnings', 'david_notes', 'angela_messages',
    ]

    for table in tables:
        try:
            row = await db.fetchrow(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(embedding) as has_emb,
                    COUNT(*) - COUNT(embedding) as null_emb
                FROM {table}
            """)

            # Check norms of sample
            sample = await db.fetch(f"""
                SELECT embedding::text as emb_text
                FROM {table} WHERE embedding IS NOT NULL
                LIMIT 3
            """)
            norms = []
            for s in sample:
                vals = [float(x) for x in s['emb_text'].strip('[]').split(',')]
                norms.append(round(math.sqrt(sum(v * v for v in vals)), 3))

            pct = (row['has_emb'] / row['total'] * 100) if row['total'] > 0 else 0
            print(f"  {table:25s} {row['has_emb']:6d}/{row['total']:6d} ({pct:5.1f}%)  norms={norms}")
        except Exception as e:
            print(f"  {table:25s} ERROR: {e}")

    # Test RAG search quality
    print("\n  RAG Search Quality Test:")
    try:
        from angela_core.services.enhanced_rag_service import EnhancedRAGService
        rag = EnhancedRAGService()
        result = await rag.retrieve("เพลง Wishing ELO", top_k=3)
        if result and result.documents:
            print(f"  Query: 'เพลง Wishing ELO' → {result.final_count} results, {result.retrieval_time_ms:.0f}ms")
            for doc in result.documents[:3]:
                print(f"    score={doc.combined_score:.3f} [{doc.source_table}] {(doc.content or '')[:80]}")
        else:
            print("  ⚠️  No results")
    except Exception as e:
        print(f"  ⚠️  RAG test error: {e}")


async def main():
    start = time.time()
    print("🧠 EMBEDDING FIX — Normalize + Fill + Schema")
    print("=" * 60)

    from angela_core.database import AngelaDatabase
    db = AngelaDatabase()
    await db.connect()

    try:
        await fix_schema(db)
        await normalize_existing(db)
        await fill_missing(db)
        await verify(db)
    finally:
        await db.disconnect()

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"✅ Done in {elapsed:.1f}s")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    asyncio.run(main())
