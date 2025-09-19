import os
import boto3
import json

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["IMAGES_TABLE"])

def handler(event, context):
    # Query params for filtering
    params = event.get("queryStringParameters") or {}
    user_id = params.get("userId", "anonymous")
    status_filter = params.get("status")

    # Get items for this user
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(f"USER#{user_id}")
    )

    items = response.get("Items", [])
    if status_filter:
        items = [item for item in items if item.get("status") == status_filter]

    return {
        "statusCode": 200,
        "body": json.dumps(items),
    }
