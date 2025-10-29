#!/usr/bin/env python3
"""
Verify that all files have been migrated to use connection pool
"""
import re
from pathlib import Path

def check_file(file_path: str) -> dict:
    """Check if a file has been properly migrated"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for issues
        if 'asyncpg.connect(' in content:
            issues.append("Still contains asyncpg.connect()")

        if 'import asyncpg' in content and 'from asyncpg' not in content:
            # Check if it's actually used
            if 'asyncpg.' in content:
                issues.append("Still imports asyncpg and uses it")

        if 'await conn.close()' in content:
            issues.append("Still has conn.close() calls")

        # Check for good patterns
        has_db_import = 'from angela_core.database import db' in content or 'from ...angela_core.database import db' in content or 'from ..database import db' in content
        uses_db = 'await db.fetch(' in content or 'await db.fetchrow(' in content or 'await db.fetchval(' in content or 'await db.execute(' in content

        return {
            'path': file_path,
            'issues': issues,
            'has_db_import': has_db_import,
            'uses_db': uses_db,
            'status': 'PASS' if len(issues) == 0 else 'FAIL'
        }

    except Exception as e:
        return {
            'path': file_path,
            'issues': [f"Error reading file: {e}"],
            'has_db_import': False,
            'uses_db': False,
            'status': 'ERROR'
        }

def main():
    base_path = Path("/Users/davidsamanyaporn/PycharmProjects/AngelaAI")

    # All files that were supposed to be migrated
    files_to_check = [
        # Angela core services
        "angela_core/services/conversation_summary_service.py",
        "angela_core/services/secrets_service.py",
        "angela_core/services/memory_completeness_check.py",
        "angela_core/services/auto_learning_service.py",
        "angela_core/services/emotional_intelligence_service.py",
        "angela_core/services/semantic_memory_service.py",
        "angela_core/services/emotion_pattern_analyzer.py",
        "angela_core/services/realtime_emotion_tracker.py",
        "angela_core/services/angela_blog_service.py",
        "angela_core/services/love_meter_service.py",

        # Angela core utilities
        "angela_core/claude_conversation_logger.py",
        "angela_core/angela_presence.py",
        "angela_core/fix_null_embeddings.py",
        "angela_core/knowledge_importer.py",
        "angela_core/fill_missing_embeddings.py",
        "angela_core/cleanup_duplicate_emotions.py",
        "angela_core/migrate_emotional_posts.py",
        "angela_core/blog_importer.py",
        "angela_core/notion_logger.py",
        "angela_core/angela_diary.py",
        "angela_core/daily_updates.py",
        "angela_core/angela_blog.py",
        "angela_core/safe_memory_query.py",
        "angela_core/self_teaching_system.py",

        # Admin web routers
        "angela_admin_web/angela_admin_api/routers/chat.py",
        "angela_admin_web/angela_admin_api/routers/emotions.py",
        "angela_admin_web/angela_admin_api/routers/documents.py",
        "angela_admin_web/angela_admin_api/routers/blog.py",
        "angela_admin_web/angela_admin_api/routers/messages.py",
        "angela_admin_web/angela_admin_api/routers/conversations.py",
        "angela_admin_web/angela_admin_api/routers/journal.py",
        "angela_admin_web/angela_admin_api/routers/knowledge_graph.py",
        "angela_admin_web/angela_admin_api/routers/dashboard.py",

        # MCP and tests
        "mcp_servers/angela_mcp_server.py",
        "tests/test_chat_json.py",
    ]

    results = []
    pass_count = 0
    fail_count = 0
    error_count = 0

    print("="*80)
    print("CONNECTION POOL MIGRATION VERIFICATION")
    print("="*80)
    print()

    for file_rel_path in files_to_check:
        file_path = base_path / file_rel_path

        if not file_path.exists():
            results.append({
                'path': str(file_rel_path),
                'issues': ['File not found'],
                'has_db_import': False,
                'uses_db': False,
                'status': 'ERROR'
            })
            error_count += 1
            continue

        result = check_file(str(file_path))
        results.append(result)

        if result['status'] == 'PASS':
            pass_count += 1
        elif result['status'] == 'FAIL':
            fail_count += 1
        else:
            error_count += 1

    # Print results
    for result in results:
        status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
        print(f"{status_icon} {result['path'].split('/')[-1]}")

        if result['issues']:
            for issue in result['issues']:
                print(f"   - {issue}")

        if result['status'] == 'PASS':
            if result['uses_db']:
                print(f"   ✓ Uses db.fetch/fetchrow/fetchval/execute")
            if result['has_db_import']:
                print(f"   ✓ Has db import")

    # Summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Passed: {pass_count}/{len(files_to_check)}")
    print(f"❌ Failed: {fail_count}/{len(files_to_check)}")
    print(f"⚠️  Errors: {error_count}/{len(files_to_check)}")

    if fail_count == 0 and error_count == 0:
        print()
        print("🎉 All files successfully migrated to connection pool!")
    else:
        print()
        print("⚠️  Some files still need attention")

    return fail_count == 0 and error_count == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
