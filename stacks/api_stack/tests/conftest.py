import os
import boto3
import pytest
from moto import mock_s3, mock_dynamodb

TABLE_NAME = "ImagesTable"
BUCKET_NAME = "images-bucket"

@pytest.fixture(scope="session", autouse=True)
def set_env_vars():
    os.environ["IMAGES_TABLE"] = TABLE_NAME
    os.environ["IMAGES_BUCKET"] = BUCKET_NAME

@pytest.fixture
def aws_env():
    with mock_s3(), mock_dynamodb():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET_NAME)
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName":"PK","KeyType":"HASH"},{"AttributeName":"SK","KeyType":"RANGE"}],
            AttributeDefinitions=[{"AttributeName":"PK","AttributeType":"S"},{"AttributeName":"SK","AttributeType":"S"},{"AttributeName":"imageId","AttributeType":"S"},{"AttributeName":"createdAt","AttributeType":"S"}],
            GlobalSecondaryIndexes=[{
                "IndexName":"imageId-index",
                "KeySchema":[{"AttributeName":"imageId","KeyType":"HASH"},{"AttributeName":"createdAt","KeyType":"RANGE"}],
                "Projection":{"ProjectionType":"ALL"}
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        yield
