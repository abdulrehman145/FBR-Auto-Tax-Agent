from fastapi import APIRouter
from typing import Dict, Any
from app.workflow.graph import app_graph

router = APIRouter(prefix="/admin")

@router.post("/approve/{run_id}")
async def approve(run_id: str, body: Dict[str, Any]):
    cfg = {"configurable": {"thread_id": run_id}}
    st = app_graph.get_state(cfg).values
    st["approval_status"] = body["decision"]

    app_graph.update_state(cfg, st)
    for _ in app_graph.stream(None, cfg):
        pass

    return {"ok": True}
