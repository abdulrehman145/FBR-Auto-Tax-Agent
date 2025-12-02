import json
from langchain_core.tools import tool

with open("./data/sample_invoice1.json") as f:
    INV1 = json.load(f)

with open("./data/sample_invoice2.json") as f:
    INV2 = json.load(f)

@tool
def erp_api(invoice_id: str):
    if invoice_id == "inv1":
        return INV1
    if invoice_id == "inv2":
        return INV2
    raise ValueError("not found")
