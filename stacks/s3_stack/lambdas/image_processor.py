from PIL import Image
import os, io
import boto3
import json

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client('s3')
IMAGES_TABLE = os.environ["IMAGES_TABLE"]
BUCKET = os.environ['IMAGES_BUCKET']

THUMBNAIL_SIZE = (400, 400)

def handler(event, context):
    print("S3 Event:", json.dumps(event))

    table = dynamodb.Table(IMAGES_TABLE)

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Extract imageId and userId from key (users/{userId}/{imageId}/{filename})
        parts = key.split("/")
        user_id, image_id = parts[1], parts[2]

        # Thubmnail 
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read()
        img = Image.open(io.BytesIO(body))
        img.thumbnail(THUMBNAIL_SIZE)
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)

        thumb_key = f'thumbnails/{user_id}/{image_id}.jpg'
        s3.put_object(Bucket=bucket, Key=thumb_key, Body=buf, ContentType='image/jpeg')

        # Update status in DynamoDB
        response = table.query(
            IndexName="imageId-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("imageId").eq(image_id)
        )

        if response["Items"]:
            item = response["Items"][0]
            table.update_item(
                Key={"PK": item["PK"], "SK": item["SK"]},
                UpdateExpression="SET #st = :s",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":s": "UPLOADED"},
            )

    return {"statusCode": 200}
