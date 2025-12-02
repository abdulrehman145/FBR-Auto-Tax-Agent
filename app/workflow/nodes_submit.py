from app.tools.notify_api import notify_api
from app.tools.fbr_api import fbr_api

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
    msg = f"{state['fbr_submission_id']} → {state['fbr_status']}"
    notify_api.invoke({"message": msg})
    return state

def escalate(state):
    state["logs"].append("escalate")
    return state
