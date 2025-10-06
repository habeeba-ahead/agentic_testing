# src/ops/health.py
import json, os, time
def handler(event, context):
    return {
      "statusCode": 200,
      "body": json.dumps({
        "status":"ok",
        "sha": os.getenv("BUILD_SHA","dev"),
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ")
      })
    }
