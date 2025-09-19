import os
import boto3
import json

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["IMAGES_TABLE"])

def handler(event, context):
    print("S3 Event:", json.dumps(event))

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Extract imageId and userId from key (userId/imageId)
        parts = key.split("/")
        if len(parts) != 2:
            continue
        user_id, image_id = parts

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
