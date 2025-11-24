# AutoTax Agent — ERP → FBR e-Filing Orchestrator  
*A minimal, clean, single-file student implementation*

---

## Overview

**AutoTax Agent** is a simplified e-filing orchestrator that processes invoices, validates tax fields, computes totals, prepares an FBR-style payload, waits for human approval, submits to a simulated FBR API, and receives asynchronous webhook status updates.

This implementation lives entirely inside **one Python file**, making it ideal for learning purposes.

---

## Features

-  Invoice upload  
-  Stateful workflow using LangGraph  
-  Tax + totals computation  
-  Human-in-the-loop approval  
-  Mocked FBR submission API  
-  Webhook callback handling  
-  SQLite checkpointing  
-  Uses dummy invoice data exactly as given  

---

## Project Structure
- main.py
- sample_invoice1.json
- sample_invoice2.json
- fbr_reference_rules.json
- fbr_dummy_payload_schema.json
- fbr_status_samples.jsonl
- README.md
