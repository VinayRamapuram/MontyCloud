import os
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
table = dynamodb.Table(os.environ["IMAGES_TABLE"])
bucket_name = os.environ["IMAGES_BUCKET"]

def handler(event, context):
    image_id = str(uuid.uuid4())
    created_at = datetime.now(datetime.timezone.utc)

    # Generate pre-signed URL
    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket_name, "Key": image_id},
        ExpiresIn=3600,
    )

    # Store metadata
    table.put_item(
        Item={
            "PK": f"IMAGE#{image_id}",
            "SK": f"METADATA#{created_at}",
            "imageId": image_id,
            "createdAt": created_at,
        }
    )

    return {
        "statusCode": 200,
        "body": {
            "uploadUrl": presigned_url,
            "imageId": image_id,
        },
    }
