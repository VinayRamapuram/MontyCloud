import os
from aws_cdk import (Stack, RemovalPolicy, Duration, aws_iam,  aws_s3 as s3, 
                     aws_lambda as _lambda, aws_lambda_event_sources as events,
                     aws_sqs as sqs, aws_s3_notifications as s3n,)
from constructs import Construct

from stacks.constants import IMAGES_S3_BUCKET_NAME

class S3Stack(Stack):
    def __init__(self, scope: Construct, id: str, table, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.bucket = self.create_bucket()
        self.dlq, self.queue = self.create_queue()

        self.bucket.add_event_notification(
                s3.EventType.OBJECT_CREATED_PUT,
                s3n.SqsDestination(self.queue),
                s3.NotificationKeyFilter(prefix="users/")
                )

        self.img_processor_lambda = self.img_lambda_processor(table)

    def create_bucket(self):
        bucket = s3.Bucket(self, 
                            IMAGES_S3_BUCKET_NAME,
                            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                            encryption=s3.BucketEncryption.S3_MANAGED,
                            versioned=True,
                            removal_policy=RemovalPolicy.DESTROY,
                            auto_delete_objects=True)
        return bucket
        
        
    def create_queue(self):
        dlq = sqs.Queue(self, "ImageProcessorDLQ", retention_period=Duration.days(14))

        queue = sqs.Queue(self, 
                        "ImageProcessorQueue",
                        visibility_timeout=Duration.seconds(300),
                        retention_period=Duration.days(4),
                        dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=5, queue=dlq),
                        )
        return dlq, queue

   
        
    def img_lambda_processor(self, table):        
        # Image Processor Lambda
        img_processor_lambda = _lambda.Function(
            self,  
            f"{id}-image_processor_lambda",
            function_name="image_processor_lambda",
            description="Lambda function to Update image status",
            runtime=_lambda.Runtime.PYTHON_3_11,                      
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="image_processor.handler",
            timeout=Duration.seconds(300),
            environment={
                "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": self.bucket.bucket_name,
                "QUEUE_URL": self.queue.queue_url            
            },
        )

        # Permissions
        self.bucket.grant_read_write(img_processor_lambda)
        table.grant_read_write_data(img_processor_lambda)
        self.queue.grant_consume_messages(img_processor_lambda)


        # S3 Event 
        img_processor_lambda.add_event_source_mapping("SqsMapping",
                                                    event_source_arn=self.queue.queue_arn,
                                                    batch_size=10,
                                                    enabled=True,
                                                    max_batching_window=Duration.seconds(30))
        
        return img_processor_lambda
