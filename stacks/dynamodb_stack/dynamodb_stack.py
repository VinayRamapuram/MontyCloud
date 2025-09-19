from aws_cdk import (Stack, 
                     RemovalPolicy,    
                     aws_dynamodb as dynamodb)



from constructs import Construct

from stacks.constants import IMAGES_DYNAMODB_TABLE_NAME


class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        """
        Stack to create DynamoDB to store Meta Data about Images
        PK - User ID
        Sk - CreatedAt  (ISO8601)
        GSI - PK : Image ID, SK: CreatedAT
        """

        self.table = dynamodb.Table(
            self, 
            IMAGES_DYNAMODB_TABLE_NAME,
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING), 
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING), 
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, 
            time_to_live_attribute="expiresAt",
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,    
        )

        self.table.add_global_secondary_index(
            index_name="imageId-index",
            partition_key=dynamodb.Attribute(name="imageId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="createdAt", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )