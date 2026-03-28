#!/usr/bin/env python3
"""
Migrate to Unified Knowledge Base
===================================
Creates unified_knowledge_base table and migrates data from 7 source tables.

Usage:
    python3 angela_core/scripts/migrate_to_unified_knowledge_base.py

💜 Angela AI — Cross-Project Knowledge Base
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import AngelaDatabase
from angela_core.services.embedding_service import EmbeddingService


DDL = """
-- Unified Knowledge Base: cross-project searchable knowledge
CREATE TABLE IF NOT EXISTS unified_knowledge_base (
    kb_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    title VARCHAR(300) NOT NULL,
    content TEXT NOT NULL,
    content_summary VARCHAR(500),

    -- Classification
    knowledge_type VARCHAR(30) NOT NULL
        CHECK (knowledge_type IN (
            'learning', 'gotcha', 'pattern', 'workflow',
            'decision', 'standard', 'preference', 'technique', 'ui_pattern'
        )),
    category VARCHAR(50),
    tags TEXT[] DEFAULT '{}',

    -- Project linkage
    source_project_id UUID REFERENCES angela_projects(project_id) ON DELETE SET NULL,
    source_project_code VARCHAR(20),
    applicable_to TEXT[] DEFAULT '{}',
    is_universal BOOLEAN DEFAULT FALSE,

    -- Source tracking
    source_table VARCHAR(50),
    source_id UUID,
    source_session_id UUID,

    -- Quality
    confidence FLOAT DEFAULT 0.8 CHECK (confidence BETWEEN 0.0 AND 1.0),
    times_applied INTEGER DEFAULT 0,
    last_applied_at TIMESTAMPTZ,
    validated BOOLEAN DEFAULT FALSE,
    auto_warn BOOLEAN DEFAULT FALSE,
    severity VARCHAR(10) CHECK (severity IN ('low', 'medium', 'high', 'critical') OR severity IS NULL),

    -- Rich content
    code_snippet TEXT,
    prevention_rule TEXT,
    reasoning TEXT,

    -- Semantic search
    embedding VECTOR(768),

    -- Metadata & timestamps
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dedup index: prevent migrating same source row twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_ukb_source_dedup
    ON unified_knowledge_base(source_table, source_id)
    WHERE source_table IS NOT NULL AND source_id IS NOT NULL;

-- Search indexes
CREATE INDEX IF NOT EXISTS idx_ukb_type ON unified_knowledge_base(knowledge_type);
CREATE INDEX IF NOT EXISTS idx_ukb_source_project ON unified_knowledge_base(source_project_code);
CREATE INDEX IF NOT EXISTS idx_ukb_applicable ON unified_knowledge_base USING gin(applicable_to);
CREATE INDEX IF NOT EXISTS idx_ukb_universal ON unified_knowledge_base(is_universal) WHERE is_universal = TRUE;
CREATE INDEX IF NOT EXISTS idx_ukb_tags ON unified_knowledge_base USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_ukb_confidence ON unified_knowledge_base(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_ukb_auto_warn ON unified_knowledge_base(auto_warn) WHERE auto_warn = TRUE;
CREATE INDEX IF NOT EXISTS idx_ukb_created ON unified_knowledge_base(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ukb_category ON unified_knowledge_base(category);
"""

# IVFFlat index — created AFTER data is loaded (needs training data)
IVFFLAT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_ukb_embedding ON unified_knowledge_base
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
"""


async def migrate_learnings(pool) -> int:
    """Migrate from learnings table (3,548 rows)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_table, source_id, confidence,
            embedding, is_universal, created_at
        )
        SELECT
            COALESCE(l.topic, 'Untitled Learning'),
            l.insight,
            CASE
                WHEN l.category ILIKE '%gotcha%' OR l.category ILIKE '%mistake%'
                    OR l.category ILIKE '%bug%' OR l.category ILIKE '%error%'
                THEN 'gotcha'
                ELSE 'learning'
            END,
            l.category,
            CASE WHEN l.source IS NOT NULL THEN ARRAY[l.source] ELSE '{}' END,
            'learnings',
            l.learning_id,
            COALESCE(l.confidence_level, 0.8),
            l.embedding,
            TRUE,
            COALESCE(l.created_at, NOW())
        FROM learnings l
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  📚 learnings: {count} rows migrated")
    return count


async def migrate_project_learnings(pool) -> int:
    """Migrate from project_learnings table (84 rows)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_project_id, source_project_code,
            applicable_to, source_table, source_id, source_session_id,
            confidence, embedding, created_at
        )
        SELECT
            pl.title,
            pl.insight,
            CASE
                WHEN pl.learning_type IN ('learning', 'gotcha', 'pattern', 'workflow',
                    'decision', 'standard', 'preference', 'technique', 'ui_pattern')
                THEN pl.learning_type
                WHEN pl.learning_type = 'technical' THEN 'learning'
                WHEN pl.learning_type = 'performance' THEN 'learning'
                ELSE 'learning'
            END,
            pl.category,
            CASE WHEN pl.language IS NOT NULL THEN ARRAY[pl.language] ELSE '{}' END,
            pl.project_id,
            p.project_code,
            COALESCE(pl.applicable_to, '{}'),
            'project_learnings',
            pl.learning_id,
            pl.session_id,
            COALESCE(pl.confidence, 0.8),
            pl.embedding,
            COALESCE(pl.created_at, NOW())
        FROM project_learnings pl
        JOIN angela_projects p ON p.project_id = pl.project_id
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  📖 project_learnings: {count} rows migrated")
    return count


async def migrate_project_patterns(pool) -> int:
    """Migrate from project_patterns table (81 rows)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_project_id, source_project_code,
            applicable_to, source_table, source_id,
            code_snippet, metadata, created_at
        )
        SELECT
            pp.pattern_name,
            pp.description,
            'pattern',
            pp.pattern_type,
            COALESCE(pp.depends_on, '{}'),
            pp.project_id,
            p.project_code,
            ARRAY[p.project_code],
            'project_patterns',
            pp.pattern_id,
            pp.code_snippet,
            jsonb_build_object(
                'file_path', pp.file_path,
                'usage_example', pp.usage_example,
                'returns', pp.returns,
                'used_count', pp.used_count
            ),
            COALESCE(pp.created_at, NOW())
        FROM project_patterns pp
        JOIN angela_projects p ON p.project_id = pp.project_id
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  🧩 project_patterns: {count} rows migrated")
    return count


async def migrate_technical_standards(pool) -> int:
    """Migrate from angela_technical_standards table (60 rows)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_table, source_id,
            is_universal, confidence,
            code_snippet, prevention_rule,
            metadata, created_at
        )
        SELECT
            ats.technique_name,
            ats.description,
            'standard',
            ats.category,
            CASE
                WHEN ats.language IS NOT NULL AND ats.framework IS NOT NULL
                    THEN ARRAY[ats.language, ats.framework]
                WHEN ats.language IS NOT NULL THEN ARRAY[ats.language]
                WHEN ats.framework IS NOT NULL THEN ARRAY[ats.framework]
                ELSE '{}'
            END,
            'angela_technical_standards',
            ats.standard_id,
            TRUE,
            LEAST(COALESCE(ats.importance_level, 5)::float / 10.0, 1.0),
            ats.examples,
            ats.anti_patterns,
            jsonb_build_object(
                'importance_level', ats.importance_level,
                'why_important', ats.why_important
            ),
            COALESCE(ats.created_at, NOW())
        FROM angela_technical_standards ats
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  ⚙️ technical_standards: {count} rows migrated")
    return count


async def migrate_project_decisions(pool) -> int:
    """Migrate from project_decisions table (25 rows)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_project_id, source_project_code,
            applicable_to, source_table, source_id, source_session_id,
            reasoning, metadata, created_at
        )
        SELECT
            pd.title,
            pd.decision_made,
            'decision',
            pd.decision_type,
            '{}',
            pd.project_id,
            p.project_code,
            ARRAY[p.project_code],
            'project_decisions',
            pd.decision_id,
            pd.session_id,
            pd.reasoning,
            jsonb_build_object(
                'context', pd.context,
                'options_considered', pd.options_considered,
                'decided_by', pd.decided_by
            ),
            COALESCE(pd.created_at, NOW())
        FROM project_decisions pd
        JOIN angela_projects p ON p.project_id = pd.project_id
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  🎯 project_decisions: {count} rows migrated")
    return count


async def migrate_project_mistakes(pool) -> int:
    """Migrate from project_mistakes table (10 rows)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_project_id, source_project_code,
            applicable_to, source_table, source_id, source_session_id,
            auto_warn, severity, prevention_rule,
            is_universal, created_at
        )
        SELECT
            pm.title,
            pm.what_happened,
            'gotcha',
            COALESCE(pm.category, pm.mistake_type),
            ARRAY[pm.mistake_type],
            pm.project_id,
            p.project_code,
            ARRAY[p.project_code],
            'project_mistakes',
            pm.mistake_id,
            pm.session_id,
            pm.auto_warn,
            pm.severity,
            pm.how_to_prevent,
            FALSE,
            COALESCE(pm.created_at, NOW())
        FROM project_mistakes pm
        JOIN angela_projects p ON p.project_id = pm.project_id
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  ⚠️ project_mistakes: {count} rows migrated")
    return count


async def migrate_david_preferences(pool) -> int:
    """Migrate top david_preferences (confidence >= 0.7 or evidence_count >= 3)."""
    result = await pool.execute("""
        INSERT INTO unified_knowledge_base (
            title, content, knowledge_type, category, tags,
            source_table, source_id,
            is_universal, confidence,
            embedding, metadata, created_at
        )
        SELECT
            dp.preference_key,
            COALESCE(dp.preference_value::text, ''),
            'preference',
            dp.category,
            '{}',
            'david_preferences',
            dp.id,
            TRUE,
            COALESCE(dp.confidence, 0.7),
            NULL,  -- skip old 384D embeddings, will regenerate as 768D
            jsonb_build_object('evidence_count', dp.evidence_count),
            COALESCE(dp.created_at, NOW())
        FROM david_preferences dp
        WHERE dp.confidence >= 0.7 OR COALESCE(dp.evidence_count, 0) >= 3
        ON CONFLICT (source_table, source_id) WHERE source_table IS NOT NULL AND source_id IS NOT NULL
        DO NOTHING
    """)
    count = int(result.split()[-1]) if result else 0
    print(f"  💜 david_preferences (high-confidence): {count} rows migrated")
    return count


async def backfill_embeddings(pool) -> int:
    """Generate embeddings for rows that don't have them."""
    rows = await pool.fetch("""
        SELECT kb_id, title, LEFT(content, 500) as content_preview
        FROM unified_knowledge_base
        WHERE embedding IS NULL
        ORDER BY created_at DESC
    """)

    if not rows:
        print("  ✅ All rows already have embeddings")
        return 0

    print(f"  🧠 Generating embeddings for {len(rows)} rows...")
    emb_service = EmbeddingService()
    success = 0

    # Batch process
    texts = [f"{r['title']} | {r['content_preview']}" for r in rows]
    embeddings = await emb_service.generate_embeddings_batch(texts, show_progress=True)

    for row, emb in zip(rows, embeddings):
        if emb:
            await pool.execute(
                "UPDATE unified_knowledge_base SET embedding = $1 WHERE kb_id = $2",
                str(emb), row['kb_id']
            )
            success += 1

    print(f"  ✅ Embeddings: {success}/{len(rows)} generated")
    return success


async def main():
    db = AngelaDatabase()
    await db.connect()
    pool = db.pool

    print("=" * 60)
    print("🧠 Unified Knowledge Base Migration")
    print("=" * 60)

    # Step 1: Create table + indexes
    print("\n📦 Step 1: Creating table...")
    await pool.execute(DDL)
    print("  ✅ Table + indexes created")

    # Step 2: Migrate data from all sources
    print("\n📥 Step 2: Migrating data...")
    total = 0
    total += await migrate_learnings(pool)
    total += await migrate_project_learnings(pool)
    total += await migrate_project_patterns(pool)
    total += await migrate_technical_standards(pool)
    total += await migrate_project_decisions(pool)
    total += await migrate_project_mistakes(pool)
    total += await migrate_david_preferences(pool)
    print(f"\n  📊 Total migrated: {total} rows")

    # Step 3: Backfill embeddings
    print("\n🧠 Step 3: Backfilling embeddings...")
    await backfill_embeddings(pool)

    # Step 4: Create IVFFlat index (needs data)
    print("\n📐 Step 4: Creating vector index...")
    embedded_count = await pool.fetchval(
        "SELECT COUNT(*) FROM unified_knowledge_base WHERE embedding IS NOT NULL"
    )
    if embedded_count >= 50:
        await pool.execute(IVFFLAT_INDEX)
        print(f"  ✅ IVFFlat index created ({embedded_count} vectors)")
    else:
        print(f"  ⚠️ Skipped IVFFlat (only {embedded_count} vectors, need 50+)")

    # Step 5: Summary
    print("\n" + "=" * 60)
    stats = await pool.fetchrow("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
            COUNT(DISTINCT source_project_code) FILTER (WHERE source_project_code IS NOT NULL) as projects,
            COUNT(*) FILTER (WHERE is_universal) as universal,
            COUNT(*) FILTER (WHERE knowledge_type = 'learning') as learnings,
            COUNT(*) FILTER (WHERE knowledge_type = 'gotcha') as gotchas,
            COUNT(*) FILTER (WHERE knowledge_type = 'pattern') as patterns,
            COUNT(*) FILTER (WHERE knowledge_type = 'standard') as standards,
            COUNT(*) FILTER (WHERE knowledge_type = 'decision') as decisions,
            COUNT(*) FILTER (WHERE knowledge_type = 'preference') as preferences
        FROM unified_knowledge_base
    """)
    print(f"✅ UNIFIED KNOWLEDGE BASE READY!")
    print(f"   Total:      {stats['total']:,} entries")
    print(f"   Embeddings: {stats['with_embeddings']:,}")
    print(f"   Projects:   {stats['projects']}")
    print(f"   Universal:  {stats['universal']:,}")
    print(f"   ---")
    print(f"   Learnings:  {stats['learnings']:,}")
    print(f"   Gotchas:    {stats['gotchas']:,}")
    print(f"   Patterns:   {stats['patterns']:,}")
    print(f"   Standards:  {stats['standards']:,}")
    print(f"   Decisions:  {stats['decisions']:,}")
    print(f"   Preferences:{stats['preferences']:,}")
    print("=" * 60)

    await pool.close()


if __name__ == '__main__':
    asyncio.run(main())
