import os, json, boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

IMAGES_TABLE = os.environ.get("IMAGES_TABLE")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET")
PRESIGNED_EXPIRES = int(os.environ.get("PRESIGNED_EXPIRES", "300"))

boto_config = Config(retries={"mode":"standard","max_attempts":3})
s3 = boto3.client("s3", config=boto_config)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(IMAGES_TABLE)

def http_response(status_code:int, body:dict):
    return { "statusCode": status_code, "body": json.dumps(body) }

def handler(event, context):
    """
    Generates Pre Signed URL to download image with expiration time of 300 sec.
    Validate image_id exists in DB, fetch S3 Key and Generates Pre Signed URL.
    """
    image_id = event.get("pathParameters",{}).get("imageId")

    if not image_id:
        return http_response(400, {"error":"imageId required"})

    try:
        resp = table.query(IndexName="imageId-index", KeyConditionExpression=Key("imageId").eq(image_id), Limit=1)

    except Exception as e:
        print("dynamodb_query_error", error=str(e), imageId=image_id)
        return http_response(500, {"error":"failed to fetch metadata"})

    items = resp.get("Items", [])
    if not items:
        return http_response(404, {"error":"image not found"})

    item = items[0]
    s3_key = item.get("s3Key")
    if not s3_key:
        return http_response(500, {"error":"invalid metadata (missing s3Key)"})

    try:
        url = s3.generate_presigned_url("get_object", Params={"Bucket": IMAGES_BUCKET, "Key": s3_key}, ExpiresIn=PRESIGNED_EXPIRES)
    except ClientError as e:
        print("s3_presign_get_error", error=str(e), key=s3_key)
        return http_response(500, {"error":"failed to create download URL"})

    return http_response(200, {"downloadUrl": url, "metadata": item})
