import os, json, boto3
from boto3.dynamodb.conditions import Key
IMAGES_TABLE = os.environ.get("IMAGES_TABLE")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(IMAGES_TABLE)


def http_response(status_code:int, body:dict):
    return { "statusCode": status_code, "body": json.dumps(body) }


def handler(event, context):
    """
    Check userId exists in queryStringParameters.
    Optinal status Filter (AVILABLE or PENDING).
    Pagination with 50 records on lastKey.
    """    
    params = event.get("queryStringParameters") or {}
    user_id = params.get("userId")

    if not user_id:
        return http_response(400, {"error":"userId query parameter required"})

    status_filter = params.get("status")
    limit = int(params.get("limit", 50))
    last_key = None

    if params.get("lastKey"):
        try:
            last_key = json.loads(params["lastKey"])
        except Exception:
            return http_response(400, {"error":"invalid lastKey"})
        

    try:
        qargs = {"KeyConditionExpression": Key("PK").eq(f"user#{user_id}"), "Limit": limit}
        if last_key:
            qargs["ExclusiveStartKey"] = last_key
        resp = table.query(**qargs)

    except Exception as e:
        print("dynamodb_query_error", error=str(e), userId=user_id)
        return http_response(500, {"error":"failed to query images"})

    items = resp.get("Items", [])

    if status_filter:
        items = [i for i in items if i.get("status")==status_filter]
    result = {"items": items}

    if resp.get("LastEvaluatedKey"):
        result["lastKey"] = resp["LastEvaluatedKey"]

    return http_response(200, result)