import json
import boto3
from stacks.api_stack.lambdas.initiate_upload import handler as initiate_handler


def test_initiate_upload_success(aws_env):
    event = {"body": json.dumps({"userId":"user123","filename":"pic.jpg"})}
    resp = initiate_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "upload" in body and "imageId" in body

def test_initiate_upload_bad_request(aws_env):
    event = {"body": json.dumps({"userId":"user123"})}
    resp = initiate_handler(event, None)
    assert resp["statusCode"] == 400
