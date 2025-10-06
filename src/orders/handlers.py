# src/orders/handlers.py
import os, json, time, uuid, boto3
dynamodb = boto3.resource("dynamodb")
events   = boto3.client("events")

TABLE_NAME = os.getenv("ORDERS_TABLE", "")
BUS_NAME   = os.getenv("EVENT_BUS_NAME", "")

def create_order(event, context):
    body = json.loads(event.get("body") or "{}")
    if "total" not in body:
        return {"statusCode":400,"body":json.dumps({"error":"total required"})}
    order_id = str(uuid.uuid4())
    item = {
        "order_id": order_id,
        "status": "CREATED",
        "total": float(body.get("total", 0.0)),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    dynamodb.Table(TABLE_NAME).put_item(Item=item)
    if BUS_NAME:
        events.put_events(Entries=[{
            "Source":"app.orders",
            "DetailType":"ReceiptGenerated",
            "Detail":json.dumps({"order_id":order_id,"total":item["total"]}),
            "EventBusName": BUS_NAME
        }])
    return {"statusCode":201,"body":json.dumps({"order_id":order_id})}

def get_order(event, context):
    order_id = (event.get("pathParameters") or {}).get("order_id")
    if not order_id:
        return {"statusCode":400,"body":"order_id required"}
    res = dynamodb.Table(TABLE_NAME).get_item(Key={"order_id": order_id})
    if "Item" not in res:
        return {"statusCode":404,"body":"Not found"}
    return {"statusCode":200,"body":json.dumps(res["Item"])}
