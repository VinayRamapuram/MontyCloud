import json
import io
import boto3
import pytest
from PIL import Image

from stacks.s3_stack.lambdas import image_processor as handler


@pytest.fixture
def sample_s3_event():
    return {
        "s3": {
            "bucket": {"name": "images-bucket"},
            "object": {"key": "users/123/image123.jpg"}
        }
    }


def create_test_image_bytes():
    img = Image.new("RGB", (800, 800), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def test_generate_thumbnail_bytes(aws_env):
    img_bytes = create_test_image_bytes()
    thumb = handler.generate_thumbnail_bytes(img_bytes)
    assert isinstance(thumb, bytes)
    assert len(thumb) > 0


def test_process_s3_event_happy_path(aws_env, sample_s3_event):
    # Insert metadata into DynamoDB
    db = boto3.resource("dynamodb", region_name="us-east-1")
    table = db.Table("ImagesTable")
    table.put_item(Item={
        "PK": "USER#123",
        "SK": "IMAGE#image123",
        "imageId": "image123",
        "createdAt": "2025-01-01T00:00:00Z",
        "status": "PENDING"
    })

    # Upload an image to S3
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="images-bucket",
                  Key="users/123/image123.jpg",
                  Body=create_test_image_bytes())

    # Call function
    handler.process_s3_event(sample_s3_event)

    # Verify thumbnail uploaded
    resp = s3.list_objects_v2(Bucket="images-bucket", Prefix="thumbnails/123/image123.jpg")
    assert "Contents" in resp

    # Verify DynamoDB update
    updated = table.get_item(Key={"PK": "USER#123", "SK": "IMAGE#image123"})
    assert updated["Item"]["status"] == "AVAILABLE"
    assert updated["Item"]["thumbnailKey"].startswith("thumbnails/123/")


def test_process_s3_event_invalid_key(aws_env):
    event = {"s3": {"bucket": {"name": "images-bucket"}, "object": {"key": "badkey"}}}
    assert handler.process_s3_event(event) is None


def test_process_s3_event_metadata_not_found(aws_env, sample_s3_event):
    # No metadata in DynamoDB
    assert handler.process_s3_event(sample_s3_event) is None


def test_handler_with_sqs_event(aws_env):
    db = boto3.resource("dynamodb", region_name="us-east-1")
    table = db.Table("ImagesTable")
    table.put_item(Item={
        "PK": "USER#123",
        "SK": "IMAGE#image123",
        "imageId": "image123",
        "createdAt": "2025-01-01T00:00:00Z",
        "status": "PENDING"
    })

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(Bucket="images-bucket",
                  Key="users/123/image123.jpg",
                  Body=create_test_image_bytes())

    sqs_event = {
        "Records": [
            {"body": json.dumps({
                "Records": [
                    {"s3": {"bucket": {"name": "images-bucket"},
                            "object": {"key": "users/123/image123.jpg"}}}
                ]
            })}
        ]
    }

    resp = handler.handler(sqs_event, None)
    assert resp["statusCode"] == 200
