# src/ingestor/process_csv.py
import csv, os, json, boto3
s3 = boto3.client("s3")
events = boto3.client("events")

BUS_NAME = os.getenv("EVENT_BUS_NAME", "")

def handler(event, context):
    rec = (event.get("Records") or [])[0]["s3"]
    bucket = rec["bucket"]["name"]; key = rec["object"]["key"]
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode()
    count = 0
    for row in csv.DictReader(body.splitlines()):
        if not row.get("customer_id") or not row.get("email"):
            continue
        count += 1
        if BUS_NAME:
            events.put_events(Entries=[{
                "Source":"app.crm",
                "DetailType":"CustomerUpserted",
                "EventBusName":BUS_NAME,
                "Detail": json.dumps({
                    "customer_id":row["customer_id"],
                    "email":row["email"],
                    "segment":row.get("segment","")
                })
            }])
    return {"ok": True, "emitted": count}
