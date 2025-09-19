import os
from aws_cdk import (Stack, RemovalPolicy, Duration, aws_s3 as s3, aws_lambda as _lambda, aws_lambda_event_sources as events)
from constructs import Construct

from stacks.constants import IMAGES_S3_BUCKET_NAME

class S3Stack(Stack):
    def __init__(self, scope: Construct, id: str, table, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.bucket = s3.Bucket(self, 
                                IMAGES_S3_BUCKET_NAME,
                                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                encryption=s3.BucketEncryption.S3_MANAGED,
                                versioned=True,
                                removal_policy=RemovalPolicy.DESTROY,
                                auto_delete_objects=True)
        
        # Image Processor Lambda
        processor_lambda = _lambda.Function(
            self,  id,
            function_name="image_processor_lambda",
            description="Lambda function to Update image status",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="image_processor.handler",
            timeout=Duration.seconds(30),
            environment={
                "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": self.bucket.bucket_name            
            },
        )

        # Grant access to DynamoDB and Bucket
        table.grant_read_write_data(processor_lambda)
        self.bucket.grant_read_write(processor_lambda)


        # S3 Event 
        processor_lambda.add_event_source(events.S3EventSource(self.bucket, events=[s3.EventType.OBJECT_CREATED]))
