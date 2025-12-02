# AutoTax Agent — ERP → FBR e-Filing Orchestrator

A production-grade **stateful AI agent** built with **FastAPI**, **LangGraph**, and **LangChain Tools**, designed to process ERP invoices, validate tax data, prepare FBR-compliant payloads, perform human-in-the-loop approval, and handle asynchronous FBR status callbacks.

This project simulates an e-filing workflow similar to the Pakistan FBR real-world process.

---

## Features

- **Invoice ingestion** from ERP (mocked)
- **Data extraction & validation** using FBR reference rules
- **Tax computation & currency conversion**
- **FBR-style payload construction** (validates against provided schema)
- **Human approval step** (pauses workflow)
- **Async FBR status simulation** via webhook
- **Checkpointed, crash-safe workflow** using LangGraph + SQLite
- **Storage & notifications** through LangChain tools
- **Full audit logs** in workflow state

---

## 🗂 Project Structure
autotax_agent/
│
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── routes/                 # All API endpoints
│   ├── workflow/               # LangGraph workflow + nodes
│   ├── tools/                  # ERP, currency, storage, FBR tools
│   ├── services/               # In-memory stores (FBR, DOCS, STORAGE)
│   └── utils/                  # Data loading, helper utilities
│
├── data/                       # Provided dummy files (unchanged)
│
├── checkpoints.db              # LangGraph SQLite checkpoint database
├── requirements.txt
└── README.md

2. Install Dependencies
pip install -r requirements.txt

3. Run FastAPI Server
uvicorn app.main:app --reload


- API now available at:

http://localhost:8000


- Interactive docs:

http://localhost:8000/docs

API Endpoints
POST /documents


## Workflow (LangGraph)
ingest → extract → validate → compute_tax → prepare_payload 
        → human_approval? → submit_fbr → await_fbr_status → notify → END

## Branching Rules

Validation errors → escalate → END

Human approval required → pause at human_approval

FBR webhook triggers transition from await_fbr_status → notify

## Dummy Data (Provided)

Located in ./data/:

sample_invoice1.json — happy path

sample_invoice2.json — foreign currency + missing fields

fbr_reference_rules.json — required IDs, min price, default tax

fbr_dummy_payload_schema.json — outgoing payload validation

fbr_status_samples.jsonl — simulate FBR callbacks

You must not modify these files.

## Testing the Workflow
1. Start a run using inv2 (should fail validation)
curl -X POST -F "invoice_id=inv2" http://localhost:8000/runs

2. Start a run requiring approval
curl -X POST -F "invoice_id=inv1" -F "approval_required=true" http://localhost:8000/runs

3. Approve it
curl -X POST -H "Content-Type: application/json" \
-d '{"decision":"approved"}' \
http://localhost:8000/admin/approve/<run_id>

4. Send webhook status
curl -X POST -H "Content-Type: application/json" \
-d '{"submission_id":"FBR-<run_id>", "status":"accepted"}' \
http://localhost:8000/webhooks/fbr

## Architecture Diagram 
ERP → ingest → extract → validate → compute_tax → prepare_payload
 → human_approval → submit_fbr → await_fbr_status → notify → END

Tools:
  - ERP API
  - Currency API
  - Storage API
  - Notify API
  - FBR Submit API

Storage:
  - SQLite checkpoints
  - In-memory FBR registry
  - In-memory document store


