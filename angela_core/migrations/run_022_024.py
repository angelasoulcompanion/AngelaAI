#!/usr/bin/env python3
"""Run migrations 022-024 for 3 Major Improvements."""
import asyncio
from angela_core.database import AngelaDatabase


async def run():
    db = AngelaDatabase()
    await db.connect()

    # Migration 022: retrieval_quality_log
    await db.execute("""
        CREATE TABLE IF NOT EXISTS retrieval_quality_log (
            log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            query TEXT NOT NULL,
            query_intent VARCHAR(50),
            total_candidates INT,
            final_count INT,
            top_scores JSONB,
            retrieval_time_ms FLOAT,
            rerank_time_ms FLOAT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_retrieval_quality_log_created "
        "ON retrieval_quality_log (created_at DESC)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_retrieval_quality_log_intent "
        "ON retrieval_quality_log (query_intent)"
    )
    print("✅ Migration 022: retrieval_quality_log")

    # Migration 023: thought_critique_log
    await db.execute("""
        CREATE TABLE IF NOT EXISTS thought_critique_log (
            log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            thought_id UUID REFERENCES angela_thoughts(thought_id),
            original_message TEXT,
            suggested_message TEXT,
            verification_passed BOOLEAN,
            quality_score FLOAT,
            uncertainty_level FLOAT,
            suppress_reason VARCHAR(100),
            checks_detail JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_thought_critique_log_created "
        "ON thought_critique_log (created_at DESC)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_thought_critique_log_passed "
        "ON thought_critique_log (verification_passed)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_thought_critique_log_thought "
        "ON thought_critique_log (thought_id)"
    )
    print("✅ Migration 023: thought_critique_log")

    # Migration 024: angela_plans + plan_steps + plan_execution_log
    await db.execute("""
        CREATE TABLE IF NOT EXISTS angela_plans (
            plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            goal_id UUID,
            plan_name VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            priority INT DEFAULT 5,
            total_steps INT DEFAULT 0,
            completed_steps INT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_angela_plans_status ON angela_plans (status)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_angela_plans_created ON angela_plans (created_at DESC)"
    )

    await db.execute("""
        CREATE TABLE IF NOT EXISTS plan_steps (
            step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID REFERENCES angela_plans(plan_id) ON DELETE CASCADE,
            step_order INT NOT NULL,
            step_name VARCHAR(200) NOT NULL,
            action_type VARCHAR(50),
            action_payload JSONB,
            dependencies UUID[],
            status VARCHAR(20) DEFAULT 'pending',
            result_data JSONB,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            retry_count INT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(plan_id, step_order)
        )
    """)
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_plan_steps_plan_status "
        "ON plan_steps (plan_id, status)"
    )

    await db.execute("""
        CREATE TABLE IF NOT EXISTS plan_execution_log (
            log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID REFERENCES angela_plans(plan_id),
            step_id UUID REFERENCES plan_steps(step_id),
            action_type VARCHAR(50),
            success BOOLEAN,
            result_summary TEXT,
            execution_time_ms FLOAT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_plan_execution_log_plan "
        "ON plan_execution_log (plan_id, created_at DESC)"
    )
    print("✅ Migration 024: angela_plans + plan_steps + plan_execution_log")

    # Verify
    for t in ['retrieval_quality_log', 'thought_critique_log',
              'angela_plans', 'plan_steps', 'plan_execution_log']:
        row = await db.fetchrow(f"SELECT COUNT(*) as cnt FROM {t}")
        print(f"   {t}: exists ({row['cnt']} rows)")

    await db.disconnect()
    print("\n✅ All migrations 022-024 complete!")


if __name__ == "__main__":
    asyncio.run(run())
