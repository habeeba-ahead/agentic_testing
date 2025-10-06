# src/inventory/handlers.py
import os, json, time, boto3
ddb = boto3.client("dynamodb")
TABLE = os.getenv("INVENTORY_TABLE", "")
BUS   = os.getenv("EVENT_BUS_NAME", "")
events = boto3.client("events")

def reserve(event, context):
    body = json.loads(event.get("body") or "{}")
    sku = body.get("sku"); qty = int(body.get("qty", 0)); req = body.get("request_id")
    if not sku or qty <= 0 or not req:
        return {"statusCode":400,"body":json.dumps({"error":"sku, qty>0, request_id required"})}

    # Idempotency marker: put if not exists
    try:
        ddb.put_item(
          TableName=TABLE,
          Item={"sku":{"S":f"idem#{req}"}, "ttl":{"N": str(int(time.time())+86400)}},
          ConditionExpression="attribute_not_exists(sku)"
        )
    except ddb.exceptions.ConditionalCheckFailedException:
        return {"statusCode":200,"body":json.dumps({"status":"duplicate","request_id":req})}

    # Decrement stock with concurrency guard
    try:
        resp = ddb.update_item(
          TableName=TABLE,
          Key={"sku":{"S":sku}},
          UpdateExpression="SET qty = qty - :q",
          ConditionExpression="qty >= :q",
          ExpressionAttributeValues={":q":{"N": str(qty)}},
          ReturnValues="ALL_NEW"
        )
    except ddb.exceptions.ConditionalCheckFailedException:
        return {"statusCode":409,"body":json.dumps({"error":"insufficient"})}

    remaining = int(resp["Attributes"]["qty"]["N"])
    if BUS:
        events.put_events(Entries=[{
          "Source":"app.inventory",
          "DetailType":"InventoryReserved",
          "EventBusName":BUS,
          "Detail": json.dumps({"sku":sku,"qty":qty,"remaining":remaining,"request_id":req})
        }])
    return {"statusCode":200,"body":json.dumps({"remaining":remaining})}
