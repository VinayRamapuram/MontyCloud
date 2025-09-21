import json
import boto3
from stacks.api_stack.lambdas.download_image import handler as get_image_handler


def test_get_image_not_found(aws_env):
    event = {"pathParameters": {"imageId": "nonexistent"}}
    resp = get_image_handler.lambda_handler(event, None)
    assert resp["statusCode"] == 404

def test_get_image_success(aws_env):
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    table = ddb.Table("ImagesTable")
    item = {"PK":"user#u1","SK":"createdAt#t#i1","imageId":"i1","s3Key":"users/u1/i1/pic.jpg"}
    table.put_item(Item=item)
    event = {"pathParameters": {"imageId":"i1"}}
    resp = get_image_handler.lambda_handler(event, None)
    assert resp["statusCode"] == 200
    data = json.loads(resp["body"])
    assert "downloadUrl" in data
