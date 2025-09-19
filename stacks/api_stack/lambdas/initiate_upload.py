import os
import boto3
import uuid
import json
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
IMAGES_TABLE = os.environ["IMAGES_TABLE"]
BUCKET = os.environ["IMAGES_BUCKET"]

def handler(event, context):    
    body = json.loads(event['body'])
    user_id = body['user_id']
    filename = body['filename']
    content_type = body.get('contentType', 'image/jpeg')
    tags = body.get('tags', [])

    image_id = str(uuid.uuid4())
    created_at = datetime.now(datetime.timezone.utc)
    s3_key = f"users/{user_id}/{image_id}"

    item = {
        'PK': f'USER#{user_id}',
        'SK': f'createdAt#{created_at}',
        'imageId': image_id,
        's3Key': s3_key,
        'filename': filename,
        'contentType': content_type,
        'status': 'PENDING',
        'tags': tags,
        'createdAt': created_at,
        'updatedAt': created_at
        }
    
    table = dynamodb.Table(IMAGES_TABLE)
    table.put_item(Item=item)

    # Generate pre-signed URL
    presigned_url = s3.generate_presigned_url(
                "put_object",
                Params={"Bucket": BUCKET, 'Key': s3_key, 'ContentType': content_type},
                ExpiresIn=3600)


    return {
        'statusCode': 200,
        'body': json.dumps({'imageId': image_id, 'uploadUrl': presigned_url, 'expiresIn': 300}) }
