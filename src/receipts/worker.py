# src/receipts/worker.py
import json, os
def handler(event, context):
    # EventBridge batch; no-op mock for demo.
    _ = os.getenv("EVENT_BUS_NAME", "")
    return {"ok": True, "records": len(event.get("Records", [])) if isinstance(event.get("Records"), list) else 0}