import json
import uuid
import datetime
from fastapi import FastAPI, UploadFile, Form
from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

app = FastAPI()

db = SqliteSaver.from_file("checkpoints.db")

with open("./data/sample_invoice1.json") as f:
    INV1 = json.load(f)
with open("./data/sample_invoice2.json") as f:
    INV2 = json.load(f)
with open("./data/fbr_reference_rules.json") as f:
    RULES = json.load(f)

STORAGE = {}
FBR = {}
DOCS = {}

def new_state():
    return {
        "run_id": "",
        "doc_id": None,
        "invoice_id": None,
        "customer_id": None,
        "timestamps": {},
        "seller_ntn": None,
        "buyer_ntn": None,
        "invoice_date": None,
        "currency": "PKR",
        "line_items": [],
        "subtotal": 0,
        "tax_amount": 0,
        "grand_total": 0,
        "approval_required": True,
        "approval_status": "pending",
        "fbr_submission_id": None,
        "fbr_status": None,
        "errors": [],
        "logs": [],
        "context": {}
    }

@tool
def erp_api(invoice_id: str):
    if invoice_id == "inv1":
        return INV1
    if invoice_id == "inv2":
        return INV2
    raise ValueError("not found")

@tool
def currency_api(amount: float, from_currency: str, to_currency: str):
    if from_currency == "USD" and to_currency == "PKR":
        return amount * 280
    return amount

@tool
def storage_api(key: str, data: dict):
    STORAGE[key] = data
    return key

@tool
def notify_api(message: str):
    print("NOTIFY:", message)

@tool
def fbr_api(payload: dict):
    sid = "FBR-" + payload["run_id"]
    FBR[sid] = {"status": "submitted", "payload": payload}
    return sid

def ingest(state):
    state["logs"].append("ingest")
    if state["invoice_id"]:
        try:
            inv = erp_api.invoke(state["invoice_id"])
            state["seller_ntn"] = inv.get("seller_ntn")
            state["buyer_ntn"] = inv.get("buyer_ntn")
            state["invoice_date"] = inv.get("invoice_date")
            state["currency"] = inv.get("currency", "PKR")
            state["line_items"] = inv.get("line_items", [])
        except Exception as e:
            state["errors"].append(str(e))
    return state

def extract(state):
    state["logs"].append("extract")
    return state

def validate(state):
    state["logs"].append("validate")
    r = RULES
    if r["require_ids"]:
        if not state["seller_ntn"]:
            state["errors"].append("seller missing")
        if not state["buyer_ntn"]:
            state["errors"].append("buyer missing")
    try:
        datetime.date.fromisoformat(state["invoice_date"])
    except:
        state["errors"].append("date invalid")
    if len(state["line_items"]) < r["min_items"]:
        state["errors"].append("items missing")
    for it in state["line_items"]:
        if it.get("unit_price", -1) < r["min_unit_price"]:
            state["errors"].append("bad price")
        if "tax_rate" not in it:
            it["tax_rate"] = r["default_tax_rate"]
    return state

def compute_tax(state):
    state["logs"].append("compute_tax")
    if state["currency"] != "PKR":
        for it in state["line_items"]:
            it["unit_price"] = currency_api.invoke({
                "amount": it["unit_price"],
                "from_currency": state["currency"],
                "to_currency": "PKR"
            })
        state["currency"] = "PKR"
    s = 0
    t = 0
    for it in state["line_items"]:
        ls = it["qty"] * it["unit_price"]
        lt = ls * it["tax_rate"]
        s += ls
        t += lt
    state["subtotal"] = round(s, 2)
    state["tax_amount"] = round(t, 2)
    state["grand_total"] = state["subtotal"] + state["tax_amount"]
    return state

def prepare_payload(state):
    state["logs"].append("prepare_payload")
    p = {
        "run_id": state["run_id"],
        "seller_ntn": state["seller_ntn"],
        "buyer_ntn": state["buyer_ntn"],
        "invoice_date": state["invoice_date"],
        "currency": state["currency"],
        "line_items": state["line_items"],
        "subtotal": state["subtotal"],
        "tax_amount": state["tax_amount"],
        "grand_total": state["grand_total"]
    }
    k = "p_" + state["run_id"]
    storage_api.invoke({"key": k, "data": p})
    state["context"]["payload"] = p
    return state

def human_approval(state):
    state["logs"].append("human_approval")
    return state

def submit_fbr(state):
    state["logs"].append("submit_fbr")
    sid = fbr_api.invoke(state["context"]["payload"])
    state["fbr_submission_id"] = sid
    state["fbr_status"] = "submitted"
    return state

def await_fbr_status(state):
    state["logs"].append("await_fbr_status")
    return state

def notify(state):
    state["logs"].append("notify")
    msg = f"{state['fbr_submission_id']} -> {state['fbr_status']}"
    notify_api.invoke({"message": msg})
    return state

def escalate(state):
    state["logs"].append("escalate")
    return state

def after_validate(state):
    if state["errors"]:
        return "escalate"
    return "compute_tax"

def after_prepare(state):
    if state["approval_required"]:
        if state["approval_status"] == "pending":
            return "human_approval"
        if state["approval_status"] == "approved":
            return "submit_fbr"
        if state["approval_status"] == "rejected":
            return "escalate"
    return "submit_fbr"

def after_await(state):
    if state["fbr_status"] in ["accepted", "rejected"]:
        return "notify"
    return "await_fbr_status"

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
g.add_conditional_edges("validate", after_validate,
    {"compute_tax": "compute_tax", "escalate": "escalate"}
)
g.add_edge("compute_tax", "prepare_payload")
g.add_conditional_edges("prepare_payload", after_prepare,
    {
        "human_approval": "human_approval",
        "submit_fbr": "submit_fbr",
        "escalate": "escalate",
    }
)
g.add_edge("human_approval", "submit_fbr")
g.add_edge("submit_fbr", "await_fbr_status")
g.add_conditional_edges("await_fbr_status", after_await,
    {"notify": "notify", "await_fbr_status": "await_fbr_status"}
)
g.add_edge("notify", END)
g.add_edge("escalate", END)

app_graph = g.compile(checkpointer=db, interrupt_before=["human_approval", "await_fbr_status"])

@app.post("/documents")
async def upload_doc(f: UploadFile):
    d = await f.read()
    id = str(uuid.uuid4())
    DOCS[id] = d.decode()
    return {"doc_id": id}

@app.post("/runs")
async def new_run(
    doc_id: str = Form(None),
    invoice_id: str = Form(None),
    customer_id: str = Form(None),
    approval_required: bool = Form(True),
):
    st = new_state()
    st["run_id"] = str(uuid.uuid4())
    st["doc_id"] = doc_id
    st["invoice_id"] = invoice_id
    st["customer_id"] = customer_id
    st["approval_required"] = approval_required
    cfg = {"configurable": {"thread_id": st["run_id"]}}
    for _ in app_graph.stream(st, cfg):
        pass
    return {"run_id": st["run_id"]}

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    cfg = {"configurable": {"thread_id": run_id}}
    s = app_graph.get_state(cfg)
    return {"node": s.next, "state": s.values}

@app.post("/admin/approve/{run_id}")
async def approve(run_id: str, body: Dict[str, Any]):
    cfg = {"configurable": {"thread_id": run_id}}
    st = app_graph.get_state(cfg).values
    st["approval_status"] = body["decision"]
    app_graph.update_state(cfg, st)
    for _ in app_graph.stream(None, cfg):
        pass
    return {"ok": True}

@app.post("/webhooks/fbr")
async def fbr_hook(data: Dict[str, str]):
    sid = data["submission_id"]
    status = data["status"]
    for r in FBR:
        if r == sid:
            FBR[r]["status"] = status
    run_id = sid.replace("FBR-", "")
    cfg = {"configurable": {"thread_id": run_id}}
    st = app_graph.get_state(cfg).values
    st["fbr_status"] = status
    app_graph.update_state(cfg, st)
    for _ in app_graph.stream(None, cfg):
        pass
    return {"ok": True}

@app.get("/healthz")
async def health():
    return {"ok": True}
