"""OpenClaw Management endpoints -- Tools, Skills, Cron Jobs.

angela_tool_registry, openclaw_configs, openclaw_cron_runs tables removed.
Tool/Skill/Cron CRUD returns empty. Engine endpoints still work.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from db import get_conn

router = APIRouter(prefix="/api/openclaw", tags=["openclaw"])


# ── Schemas ──

class ExecuteRequest(BaseModel):
    intent: str
    context: str = ""
    tools_filter: Optional[str] = None


class ToolToggleRequest(BaseModel):
    enabled: bool


class SkillCreate(BaseModel):
    name: str
    intent: str
    description: str = ""
    tools_filter: Optional[str] = None
    enabled: bool = True


class SkillUpdate(BaseModel):
    intent: Optional[str] = None
    description: Optional[str] = None
    tools_filter: Optional[str] = None
    enabled: Optional[bool] = None


class CronCreate(BaseModel):
    name: str
    skill_name: Optional[str] = None
    intent: Optional[str] = None
    schedule: str
    enabled: bool = True
    notes: str = ""


class CronUpdate(BaseModel):
    skill_name: Optional[str] = None
    intent: Optional[str] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None


# ── Tool Registry (empty — table removed) ──

@router.get("/tools")
async def list_tools(conn=Depends(get_conn)):
    return []


@router.get("/tools/summary")
async def tools_summary(conn=Depends(get_conn)):
    return {"total_tools": 0, "enabled_tools": 0, "total_executions": 0, "categories": []}


@router.put("/tools/{tool_name}/toggle")
async def toggle_tool(tool_name: str, body: ToolToggleRequest, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Tool registry not available")


# ── Engine Status (still works) ──

@router.get("/engine/status")
async def engine_status():
    try:
        from angela_core.services.openclaw_engine import get_openclaw_engine
        engine = get_openclaw_engine()
        return engine.status()
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@router.post("/engine/execute")
async def execute_intent(body: ExecuteRequest):
    try:
        from angela_core.services.openclaw_engine import get_openclaw_engine
        engine = get_openclaw_engine()
        result = await engine.execute(
            intent=body.intent, context=body.context, tools_filter=body.tools_filter,
        )
        return {"success": result.success, "data": result.data, "error": result.error}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


# ── Skills CRUD (empty — table removed) ──

@router.get("/skills")
async def list_skills(conn=Depends(get_conn)):
    return []


@router.post("/skills")
async def create_skill(body: SkillCreate, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Skills table not available")


@router.put("/skills/{name}")
async def update_skill(name: str, body: SkillUpdate, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Skills table not available")


@router.delete("/skills/{name}")
async def delete_skill(name: str, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Skills table not available")


@router.post("/skills/{name}/run")
async def run_skill(name: str, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Skills table not available")


# ── Cron Jobs CRUD (empty — table removed) ──

@router.get("/crons")
async def list_crons(conn=Depends(get_conn)):
    return []


@router.post("/crons")
async def create_cron(body: CronCreate, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Crons table not available")


@router.put("/crons/{name}")
async def update_cron(name: str, body: CronUpdate, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Crons table not available")


@router.delete("/crons/{name}")
async def delete_cron(name: str, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Crons table not available")


@router.put("/crons/{name}/toggle")
async def toggle_cron(name: str, body: ToolToggleRequest, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Crons table not available")


@router.post("/crons/{name}/run")
async def run_cron_now(name: str, conn=Depends(get_conn)):
    raise HTTPException(status_code=501, detail="Crons table not available")


# ── Execution History (empty) ──

@router.get("/history")
async def execution_history(limit: int = 20, conn=Depends(get_conn)):
    return []
