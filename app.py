import aws_cdk as cdk
from stacks.dynamodb_stack.dynamodb_stack import DynamoDBStack
from stacks.s3_stack.s3_stack import S3Stack
from stacks.api_stack.api_gateway_stack import ApiStack

app = cdk.App()


dynamo_stack = DynamoDBStack(app, "ImagesDynamoStack")
s3_stack = S3Stack(app, "ImagesS3Stack", table=dynamo_stack.table)
api_stack = ApiStack(app, "ImagesApiStack",  table=dynamo_stack.table,  bucket=s3_stack.bucket)

s3_stack.add_dependency(dynamo_stack)
api_stack.add_dependency(s3_stack)

app.synth()
