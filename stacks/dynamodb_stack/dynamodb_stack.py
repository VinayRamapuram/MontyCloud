from aws_cdk import (
Stack,
RemovalPolicy,
aws_dynamodb as dynamodb,
)
from constructs import Construct

class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, id: str, *, table_name: str = "Images", **kwargs):
        super().__init__(scope, id, **kwargs)

        self.table = self.create_image_table(table_name)
    
    def create_image_table(self, table_name):
        table = dynamodb.Table(
        self, "ImagesTable",
        table_name=table_name,
        partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
        sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        time_to_live_attribute="expiresAt",
        encryption=dynamodb.TableEncryption.AWS_MANAGED,
        point_in_time_recovery=True,
        removal_policy=RemovalPolicy.RETAIN,
        )


        table.add_global_secondary_index(
        index_name="imageId-index",
        partition_key=dynamodb.Attribute(name="imageId", type=dynamodb.AttributeType.STRING),
        sort_key=dynamodb.Attribute(name="createdAt", type=dynamodb.AttributeType.STRING),
        projection_type=dynamodb.ProjectionType.ALL,
        )
        return table