import uuid
from fastapi import APIRouter, Form
from app.services.state import new_state
from app.workflow.graph import app_graph

router = APIRouter(prefix="/runs")

@router.post("")
async def new_run(
    doc_id: str = Form(None),
    invoice_id: str = Form(None),
    customer_id: str = Form(None),
    approval_required: bool = Form(True),
):
    state = new_state()
    state["run_id"] = str(uuid.uuid4())
    state["doc_id"] = doc_id
    state["invoice_id"] = invoice_id
    state["customer_id"] = customer_id
    state["approval_required"] = approval_required

    cfg = {"configurable": {"thread_id": state["run_id"]}}

    for _ in app_graph.stream(state, cfg):
        pass

    return {"run_id": state["run_id"]}

@router.get("/{run_id}")
async def get_run(run_id: str):
    cfg = {"configurable": {"thread_id": run_id}}
    s = app_graph.get_state(cfg)
    return {"node": s.next, "state": s.values}
