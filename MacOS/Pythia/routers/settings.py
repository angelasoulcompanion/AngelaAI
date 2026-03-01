"""
Pythia — App settings management
"""
from fastapi import APIRouter, Depends, HTTPException

from db import get_conn
from schemas import SettingUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/")
async def list_settings(conn=Depends(get_conn)):
    """List all app settings."""
    rows = await conn.fetch("""
        SELECT setting_id::text, setting_key, setting_value, value_type,
               description, category, updated_at
        FROM app_settings
        WHERE is_sensitive = false
        ORDER BY category, setting_key
    """)
    return [dict(r) for r in rows]


@router.get("/{key}")
async def get_setting(key: str, conn=Depends(get_conn)):
    """Get a specific setting by key."""
    row = await conn.fetchrow("""
        SELECT setting_key, setting_value, value_type, description, category
        FROM app_settings WHERE setting_key = $1
    """, key)
    if not row:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return dict(row)


@router.put("/{key}")
async def update_setting(key: str, body: SettingUpdate, conn=Depends(get_conn)):
    """Update a setting value."""
    result = await conn.execute("""
        UPDATE app_settings SET setting_value = $1, updated_at = NOW()
        WHERE setting_key = $2
    """, body.setting_value, key)
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"status": "updated", "key": key, "value": body.setting_value}
