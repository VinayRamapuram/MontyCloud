import os, json, uuid, logging
from datetime import datetime, timezone
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from jsonschema import validate, ValidationError

# LOGGER = logging.getLogger()
# LOGGER.setLevel(logging.INFO)

IMAGES_TABLE = os.environ.get("IMAGES_TABLE")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET")
PRESIGNED_EXPIRES = int(os.environ.get("PRESIGNED_EXPIRES", "300"))

boto_config = Config(retries={"mode":"standard","max_attempts":3})
s3 = boto3.client("s3", config=boto_config)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(IMAGES_TABLE)

ITEM_SCHEMA = {
    "type": "object",
    "required": ["imageId","userId","createdAt","s3Key"],
    "properties": {"imageId":{"type":"string"},"userId":{"type":"string"},"createdAt":{"type":"string"},"s3Key":{"type":"string"},"status":{"type":"string"}},
    "additionalProperties": True
}

def put_item_conditional(item):
    table.put_item(Item=item, ConditionExpression="attribute_not_exists(imageId)")

def http_response(status_code:int, body:dict):
    return { "statusCode": status_code, "body": json.dumps(body) }

def handler(event, context):
    """
    Validate request body format and Existance of userId and filename in request body.
    Generates Pre Signed URL with Server side encryption and Expiration time.
    Validate Item Schema. Put Item on conditional basis (Avoids Multiple uploads filter with PK and SK).
    Handles Client  and ServerSide Exceptions.
    """    
    try:
        body = json.loads(event.get("body") or "{}")
    except Exception:
        return http_response(400, {"error":"invalid JSON body"})

    user_id = body.get("userId")
    filename = body.get("filename")
    content_type = body.get("contentType", "application/octet-stream")
    max_size = int(body.get("maxSize", 20*1024*1024))

    if not user_id or not filename:
        return http_response(400, {"error":"userId and filename are required"})

    image_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    s3_key = f"users/{user_id}/{image_id}/{filename}"

    try:
        presigned_post = s3.generate_presigned_post(
            Bucket=IMAGES_BUCKET,
            Key=s3_key,
            Fields={"Content-Type": content_type, "x-amz-server-side-encryption":"AES256"},
            Conditions=[{"Content-Type": content_type}, ["content-length-range",1,max_size], {"x-amz-server-side-encryption":"AES256"}],
            ExpiresIn=PRESIGNED_EXPIRES,
        )
    except ClientError as e:
        print("s3_presign_error", error=str(e))
        return http_response(500, {"error":"failed to create presigned url"})

    item = {
        "PK": f"user#{user_id}",
        "SK": f"createdAt#{created_at}#{image_id}",
        "imageId": image_id,
        "userId": user_id,
        "createdAt": created_at,
        "s3Key": s3_key,
        "status": "PENDING",
    }

    try:
        validate(instance=item, schema=ITEM_SCHEMA)
    except ValidationError as e:
        return http_response(400, {"error": f"schema validation failed: {e.message}"})

    try:
        put_item_conditional(item)
    except ClientError as e:
        print("dynamodb_put_error", error=str(e))
        if e.response.get("Error",{}).get("Code") == "ConditionalCheckFailedException":
            return http_response(409, {"error":"duplicate image id"})
        return http_response(500, {"error":"failed to persist metadata"})
    except Exception as e:
        print("dynamodb_put_unexpected", error=str(e))
        return http_response(500, {"error":"failed to persist metadata"})

    return http_response(200, {"upload": presigned_post, "imageId": image_id})