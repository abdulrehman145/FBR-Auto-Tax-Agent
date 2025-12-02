from langchain_core.tools import tool
from app.services.stores import FBR

@tool
def fbr_api(payload: dict):
    sid = "FBR-" + payload["run_id"]
    FBR[sid] = {
        "status": "submitted",
        "payload": payload
    }
    return sid
