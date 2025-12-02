from fastapi import APIRouter
from typing import Dict
from app.services.stores import FBR
from app.workflow.graph import app_graph

router = APIRouter(prefix="/webhooks")

@router.post("/fbr")
async def fbr_hook(data: Dict[str, str]):
    sid = data["submission_id"]
    status = data["status"]

    if sid in FBR:
        FBR[sid]["status"] = status

    run_id = sid.replace("FBR-", "")
    cfg = {"configurable": {"thread_id": run_id}}
    st = app_graph.get_state(cfg).values

    st["fbr_status"] = status

    app_graph.update_state(cfg, st)
    for _ in app_graph.stream(None, cfg):
        pass

    return {"ok": True}
