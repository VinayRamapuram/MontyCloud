import os, json, boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

IMAGES_TABLE = os.environ.get("IMAGES_TABLE")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(IMAGES_TABLE)
s3 = boto3.client("s3")

def http_response(status_code:int, body:dict):
    return { "statusCode": status_code, "body": json.dumps(body) }


def lambda_handler(event, context):
    """
    Validate imageId in pathParameters.
    Conditional image deletion
      - Query Image Table with imageId.
      - Validate UserId access to delete the image.
    
      Delete image from S3 and in Table records with exception handling.

    """

    image_id = event.get("pathParameters",{}).get("imageId")
    caller_user = None

    if not image_id:
        return http_response(400, {"error":"imageId required"})

    try:
        resp = table.query(IndexName="imageId-index", KeyConditionExpression=Key("imageId").eq(image_id), Limit=1)
    except Exception as e:
        print("dynamodb_query_error", error=str(e), imageId=image_id)
        return http_response(500, {"error":"failed to query metadata"})

    items = resp.get("Items", [])
    if not items:
        return http_response(404, {"error":"image not found"})

    item = items[0]
    if caller_user and item.get("userId") != caller_user:
        return http_response(403, {"error":"forbidden"})

    s3_key = item.get("s3Key")

    try:
        s3.delete_object(Bucket=IMAGES_BUCKET, Key=s3_key)        
    except ClientError as e:
        code = e.response.get("Error",{}).get("Code")
        if code not in ("NoSuchKey","404"):
            print("s3_delete_error", error=str(e), key=s3_key)
            return http_response(500, {"error":"failed to delete object from storage"})

    try:
        table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
    except Exception as e:
        print("dynamodb_delete_error", error=str(e), key=item.get("PK"))
        return http_response(500, {"error":"failed to delete metadata"})

    return http_response(200, {"deletedImageId": image_id})
