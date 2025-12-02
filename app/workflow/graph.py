from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.workflow.nodes_ingest import ingest
from app.workflow.nodes_process import extract, validate, compute_tax, prepare_payload
from app.workflow.nodes_submit import (
    human_approval,
    submit_fbr,
    await_fbr_status,
    notify,
    escalate,
)
from app.workflow.conditions import after_validate, after_prepare, after_await

db = SqliteSaver.from_file("checkpoints.db")

g = StateGraph(dict)

g.add_node("ingest", ingest)
g.add_node("extract", extract)
g.add_node("validate", validate)
g.add_node("compute_tax", compute_tax)
g.add_node("prepare_payload", prepare_payload)
g.add_node("human_approval", human_approval)
g.add_node("submit_fbr", submit_fbr)
g.add_node("await_fbr_status", await_fbr_status)
g.add_node("notify", notify)
g.add_node("escalate", escalate)

g.set_entry_point("ingest")

g.add_edge("ingest", "extract")
g.add_edge("extract", "validate")

g.add_conditional_edges("validate", after_validate, {
    "compute_tax": "compute_tax",
    "escalate": "escalate"
})

g.add_edge("compute_tax", "prepare_payload")

g.add_conditional_edges("prepare_payload", after_prepare, {
    "human_approval": "human_approval",
    "submit_fbr": "submit_fbr",
    "escalate": "escalate",
})

g.add_edge("human_approval", "submit_fbr")

g.add_edge("submit_fbr", "await_fbr_status")

g.add_conditional_edges("await_fbr_status", after_await, {
    "notify": "notify",
    "await_fbr_status": "await_fbr_status"
})

g.add_edge("notify", END)
g.add_edge("escalate", END)

app_graph = g.compile(
    checkpointer=db,
    interrupt_before=["human_approval", "await_fbr_status"]
)
