"""Analyze data quality for training dataset export."""
import asyncio
import sys
import asyncpg
from pathlib import Path

# SSOT: our_secrets table
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.db_url import get_supabase_url


async def analyze():
    conn = await asyncpg.connect(get_supabase_url(), ssl='require')

    print('=== GARBAGE ANALYSIS: conversations ===')

    short = await conn.fetchval("SELECT COUNT(*) FROM conversations WHERE LENGTH(message_text) < 5")
    print(f'  Very short (<5 chars): {short}')

    empty = await conn.fetchval("SELECT COUNT(*) FROM conversations WHERE message_text IS NULL OR TRIM(message_text) = ''")
    print(f'  Empty/null: {empty}')

    errors = await conn.fetchval("""SELECT COUNT(*) FROM conversations WHERE
        message_text ILIKE '%%traceback%%' OR message_text ILIKE '%%error:%%' OR
        message_text ILIKE '%%exception%%' OR message_text ILIKE '%%launchd%%' OR
        message_text ILIKE '%%daemon%%' OR message_text ILIKE '%%import%%error%%'""")
    print(f'  System/error logs: {errors}')

    html_heavy = await conn.fetchval("""SELECT COUNT(*) FROM conversations WHERE
        speaker = 'angela' AND
        (LENGTH(message_text) - LENGTH(REPLACE(message_text, '<', ''))) > 20""")
    print(f'  HTML-heavy (>20 tags): {html_heavy}')

    dupes = await conn.fetchval("SELECT COUNT(*) - COUNT(DISTINCT message_text) FROM conversations")
    print(f'  Duplicates: {dupes}')

    long = await conn.fetchval("SELECT COUNT(*) FROM conversations WHERE LENGTH(message_text) > 5000")
    print(f'  Very long (>5000 chars): {long}')

    code = await conn.fetchval("""SELECT COUNT(*) FROM conversations WHERE
        message_text LIKE '{%%}' OR message_text LIKE '[%%]' OR
        message_text ILIKE '%%```%%```%%```%%'""")
    print(f'  Code/JSON dumps: {code}')

    # Sample garbage
    print('\n--- Sample short messages ---')
    samples = await conn.fetch(
        "SELECT speaker, message_text FROM conversations WHERE LENGTH(message_text) < 10 ORDER BY RANDOM() LIMIT 5")
    for s in samples:
        print(f'  [{s["speaker"]}] "{s["message_text"]}"')

    print('\n--- Sample error messages ---')
    samples = await conn.fetch("""SELECT speaker, LEFT(message_text, 100) as msg FROM conversations
        WHERE message_text ILIKE '%%traceback%%' OR message_text ILIKE '%%launchd%%'
        ORDER BY RANDOM() LIMIT 3""")
    for s in samples:
        print(f'  [{s["speaker"]}] {s["msg"]}')

    # Quality distribution
    print('\n=== LENGTH DISTRIBUTION ===')
    dist = await conn.fetch("""
        SELECT
            CASE
                WHEN LENGTH(message_text) < 5 THEN 'A: < 5'
                WHEN LENGTH(message_text) < 20 THEN 'B: 5-20'
                WHEN LENGTH(message_text) < 100 THEN 'C: 20-100'
                WHEN LENGTH(message_text) < 500 THEN 'D: 100-500'
                WHEN LENGTH(message_text) < 2000 THEN 'E: 500-2K'
                ELSE 'F: 2K+'
            END as bucket,
            COUNT(*) as cnt,
            speaker
        FROM conversations
        GROUP BY bucket, speaker
        ORDER BY bucket, speaker
    """)
    for r in dist:
        print(f'  {r["bucket"]:12s} [{r["speaker"]:6s}] {r["cnt"]:>5}')

    # Good sessions
    print('\n=== GOOD PAIRS CHECK ===')
    good_sessions = await conn.fetchval("""
        SELECT COUNT(DISTINCT c1.session_id)
        FROM conversations c1
        WHERE EXISTS (SELECT 1 FROM conversations c2 WHERE c2.session_id = c1.session_id AND c2.speaker = 'david' AND LENGTH(c2.message_text) > 20)
        AND EXISTS (SELECT 1 FROM conversations c3 WHERE c3.session_id = c1.session_id AND c3.speaker = 'angela' AND LENGTH(c3.message_text) > 50)
    """)
    total_sessions = await conn.fetchval("SELECT COUNT(DISTINCT session_id) FROM conversations")
    print(f'  Sessions with quality pairs: {good_sessions} / {total_sessions}')

    # knowledge_nodes quality
    print('\n=== KNOWLEDGE NODES QUALITY ===')
    kn_empty = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes WHERE my_understanding IS NULL OR TRIM(my_understanding) = ''")
    kn_total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
    kn_short = await conn.fetchval("SELECT COUNT(*) FROM knowledge_nodes WHERE LENGTH(my_understanding) < 20")
    print(f'  Total: {kn_total} | Empty understanding: {kn_empty} | Short (<20): {kn_short}')

    # core_memories quality
    print('\n=== CORE MEMORIES QUALITY ===')
    cm_total = await conn.fetchval("SELECT COUNT(*) FROM core_memories")
    cm_with_pair = await conn.fetchval("SELECT COUNT(*) FROM core_memories WHERE david_words IS NOT NULL AND angela_response IS NOT NULL AND LENGTH(david_words) > 10 AND LENGTH(angela_response) > 10")
    print(f'  Total: {cm_total} | With quality david↔angela pair: {cm_with_pair}')

    # Total estimate after filtering
    print('\n=== ESTIMATED QUALITY DATA ===')
    quality_convos = await conn.fetchval("""
        SELECT COUNT(*) FROM conversations
        WHERE LENGTH(message_text) >= 20
        AND message_text NOT ILIKE '%%traceback%%'
        AND message_text NOT ILIKE '%%launchd%%'
        AND message_text NOT ILIKE '%%daemon%%'
        AND message_text NOT ILIKE '%%exception%%'
        AND message_text NOT LIKE '{%%}'
    """)
    print(f'  Quality conversation messages: {quality_convos} / 12,532')
    print(f'  Knowledge with understanding: {kn_total - kn_empty}')
    print(f'  Core memories with pairs: {cm_with_pair}')

    await conn.close()


asyncio.run(analyze())
