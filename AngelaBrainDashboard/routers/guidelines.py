"""Guidelines (Coding Preferences & Design Principles) endpoints."""
import json

from fastapi import APIRouter, Depends

from db import get_conn, get_pool

router = APIRouter(prefix="/api/guidelines", tags=["guidelines"])


@router.get("/coding-preferences")
async def get_coding_preferences(conn=Depends(get_conn)):
    """Fetch David's coding preferences with description and reason extracted from preference_value JSON"""
    rows = await conn.fetch("""
        SELECT
            id::text,
            preference_key,
            category,
            preference_value::text,
            confidence
        FROM david_preferences
        WHERE category LIKE 'coding%'
        ORDER BY confidence DESC
    """)

    result = []
    for r in rows:
        pref = dict(r)
        try:
            pv = json.loads(pref.get('preference_value', '{}') or '{}')
            pref['description'] = pv.get('description') or pv.get('rule') or pv.get('source') or ''
            pref['reason'] = pv.get('reason') or pv.get('source_context') or ''
        except (json.JSONDecodeError, TypeError):
            pref['description'] = ''
            pref['reason'] = ''
        result.append(pref)

    return result


@router.get("/design-principles")
async def get_design_principles(conn=Depends(get_conn)):
    """Fetch design principles (importance >= 9)"""
    rows = await conn.fetch("""
        SELECT
            kb_id::text as standard_id,
            title as technique_name,
            content as description,
            category,
            COALESCE((metadata->>'importance_level')::int, ROUND(confidence * 10)::int) as importance_level,
            metadata->>'why_important' as why_important,
            code_snippet as examples,
            prevention_rule as anti_patterns
        FROM unified_knowledge_base
        WHERE knowledge_type = 'standard'
        AND confidence >= 0.9
        ORDER BY confidence DESC, category
    """)
    return [dict(r) for r in rows]
