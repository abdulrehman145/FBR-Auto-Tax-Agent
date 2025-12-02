import datetime
from app.tools.currency_api import currency_api
from app.tools.storage_api import storage_api
from app.utils.loader import RULES

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

    key = "p_" + state["run_id"]
    storage_api.invoke({"key": key, "data": p})

    state["context"]["payload"] = p
    return state
