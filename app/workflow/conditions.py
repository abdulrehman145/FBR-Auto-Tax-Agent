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
