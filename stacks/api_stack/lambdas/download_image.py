import os
import boto3
import json

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
table = dynamodb.Table(os.environ["IMAGES_TABLE"])
bucket_name = os.environ["IMAGES_BUCKET"]

def handler(event, context):
    image_id = event["pathParameters"]["imageId"]

    # Lookup metadata
    response = table.query(
        IndexName="imageId-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("imageId").eq(image_id)
    )

    if not response["Items"]:
        return {"statusCode": 404, "body": json.dumps({"error": "Image not found"})}

    item = response["Items"][0]
    user_id = item["userId"]

    # Generate pre-signed download URL
    download_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": f"{user_id}/{image_id}"},
        ExpiresIn=3600,
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"downloadUrl": download_url, "metadata": item}),
    }
