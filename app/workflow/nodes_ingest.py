from app.tools.erp_api import erp_api

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
