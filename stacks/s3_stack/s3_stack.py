import os
from aws_cdk import (Stack, RemovalPolicy, Duration, aws_s3 as s3, 
                     aws_lambda as _lambda, aws_sqs as sqs, aws_s3_notifications as s3n, aws_logs)
from constructs import Construct
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion
from stacks.constants import IMAGES_S3_BUCKET_NAME, IMAGE_SERVICE_QUEUE_NAME, IMAGE_SERVICE_DLQ_QUEUE_NAME

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
                            "ImagesBucket",
                            bucket_name=IMAGES_S3_BUCKET_NAME,
                            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                            encryption=s3.BucketEncryption.S3_MANAGED,
                            versioned=True,
                            removal_policy=RemovalPolicy.DESTROY,
                            auto_delete_objects=True)
        return bucket
        
        
    def create_queue(self):
        dlq = sqs.Queue(self, 
                        "ImageProcessorDLQ",
                        queue_name=IMAGE_SERVICE_DLQ_QUEUE_NAME, 
                        retention_period=Duration.days(14))

        queue = sqs.Queue(self, 
                        "ImageProcessorQueue",
                        queue_name=IMAGE_SERVICE_QUEUE_NAME,
                        visibility_timeout=Duration.seconds(300),
                        retention_period=Duration.days(4),
                        dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=5, queue=dlq),
                        )
        return dlq, queue

   
        
    def img_lambda_processor(self, table):

        lambda_layer = PythonLayerVersion(
            self,
            id=f"img-lambda-processor-layer",
            layer_version_name=f"img-lambda-processor-layer",
            entry=os.path.join(os.path.dirname(__file__), "lambdas", "python_layer"),            
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            bundling={
                    "image": _lambda.Runtime.PYTHON_3_11.bundling_image
                }            
        )  

        # Image Processor Lambda
        img_processor_lambda =PythonFunction(
            self,  
            f"image_processor_lambda",
            function_name="image_processor_lambda",
            description="Lambda function to Update image status",
            runtime=_lambda.Runtime.PYTHON_3_11,                      
            entry=os.path.join(os.path.dirname(__file__), "lambdas"),
            index="image_processor.py",
            architecture=_lambda.Architecture.X86_64,
            layers=[lambda_layer],
            timeout=Duration.seconds(300),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
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
        img_processor_lambda.add_event_source(SqsEventSource(
                self.queue,
                batch_size=10,
                max_batching_window=Duration.seconds(30)
            )
        )
        
        return img_processor_lambda
