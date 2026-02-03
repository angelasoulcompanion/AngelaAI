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
            standard_id::text,
            technique_name,
            description,
            category,
            importance_level,
            why_important,
            examples,
            anti_patterns
        FROM angela_technical_standards
        WHERE importance_level >= 9
        ORDER BY importance_level DESC, category
    """)
    return [dict(r) for r in rows]
