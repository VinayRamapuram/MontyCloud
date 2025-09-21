import os, json, boto3
from botocore.exceptions import ClientError
from PIL import Image
import io
from boto3.dynamodb.conditions import Key

IMAGES_TABLE = os.environ.get("IMAGES_TABLE")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET")

S3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(IMAGES_TABLE)

THUMBNAIL_SIZE = (400,400)
THUMBNAIL_PREFIX = "thumbnails/"

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client('s3')
IMAGES_TABLE = os.environ["IMAGES_TABLE"]
BUCKET = os.environ['IMAGES_BUCKET']

THUMBNAIL_SIZE = (400, 400)

def generate_thumbnail_bytes(image_bytes):
    """
    Generate cpmpressed imgage"
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        im.thumbnail(THUMBNAIL_SIZE)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=80)
        buf.seek(0)
        return buf.read()
    
    
def process_s3_event(s3_rec):
    """
    Read s3 event record, validate record having user id and image id.
    Check Initiate img Meta data exists or not (Pending).
    S3 Head object of key.
    Get S3 Object,  Generate Thumnail and save in thumbnails/ folder in S3.
    Update DB record with attributes (Status, Size and Thumbnail Key)

    """
    bucket = s3_rec["s3"]["bucket"]["name"]
    key = s3_rec["s3"]["object"]["key"]
    parts = key.split("/")

    if len(parts) < 3:
        print("invalid_s3_key_format", key=key)
        return
    user_id = parts[1]
    image_id = parts[2]

    resp = table.query(IndexName="imageId-index", KeyConditionExpression=Key("imageId").eq(image_id), Limit=1)
    items = resp.get("Items", [])
    if not items:
        print("metadata_not_found", imageId=image_id, key=key)
        return
    item = items[0]

    try:
        head = S3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        print("s3_head_error", error=str(e), key=key)
        raise

    size = head.get("ContentLength", 0)
    try:
        obj = S3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read()
    except ClientError as e:
        print("s3_get_error", error=str(e), key=key)
        raise

    try:
        thumb_bytes = generate_thumbnail_bytes(body)
        thumb_key = f"{THUMBNAIL_PREFIX}{user_id}/{image_id}.jpg"
        S3.put_object(Bucket=bucket, Key=thumb_key, Body=thumb_bytes, ContentType="image/jpeg", ACL="private")
    except Exception as e:
        print("thumbnail_error", error=str(e), imageId=image_id)
        thumb_key = None

    try:
        table.update_item(Key={"PK": item["PK"], "SK": item["SK"]},
                          UpdateExpression="SET #s = :s, #size = :sz, #thumb = :t",
                          ConditionExpression="#s = :pending",
                          ExpressionAttributeNames={"#s":"status","#size":"size","#thumb":"thumbnailKey"},
                          ExpressionAttributeValues={":s":"AVAILABLE", ":sz":size, ":t":thumb_key, ":pending":"PENDING"})
    except ClientError as e:
        if e.response.get("Error",{}).get("Code") == "ConditionalCheckFailedException":
            print("conditional_check_failed_already_processed", imageId=image_id)
            return
        print("dynamodb_update_error", error=str(e), imageId=image_id)
        raise


def handler(event, context):
    """
    Lambda Handler for each record read from Queue.
    Validates request body type and process to process_s3_event function"

    """
    records = event.get("Records", [])
    if not records:
        print("no_records")
        return {"statusCode":400}
    
    for rec in records:
        body = rec.get("body")
        try:
            payload = json.loads(body)
        except Exception:
            payload = body if isinstance(body, dict) else None

        if not payload:
            print("invalid_sqs_body", body=body)
            raise Exception("invalid SQS body")
        
        s3_records = payload.get("Records", [])

        for s3_rec in s3_records:
            process_s3_event(s3_rec)

    return {"statusCode":200}