import os
from aws_cdk import Stack, Duration, aws_apigateway as apigw, aws_lambda as _lambda
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, table, bucket, **kwargs):
        super().__init__(scope, id, **kwargs)

        api = apigw.RestApi(
            self,             
            "ImagesApi",
            rest_api_name="Images Service",
            default_cors_preflight_options={
                "allow_origins": apigw.Cors.ALL_ORIGINS,
                "allow_methods": apigw.Cors.ALL_METHODS,
            },
        )    


        # Generate Pre Signed URL
        initiate_upload_lambda = _lambda.Function(
            self,  
            f"{id}-initiate-upload-lambda",
            function_name="initiate_upload_lambda",
            description="Lambda function to Upload image",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="initiate_upload.handler",
            timeout=Duration.seconds(30),
            environment={
                "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": bucket.bucket_name               
            },
        )

        table.grant_write_data(initiate_upload_lambda)
        bucket.grant_put(initiate_upload_lambda)


        
        # List Images on User Id with Filter option
        list_images_lambda = _lambda.Function(
            self, 
            f"{id}-list-images-lambda",
            function_name="list_images_lambda",
            description="Lambda function to List images",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="list_images.handler",
            timeout=Duration.seconds(30),
            environment={
                "IMAGES_TABLE": table.table_name                
            },
        )

        table.grant_read_data(list_images_lambda)


        download_image_lambda = _lambda.Function(
            self,  
            f"{id}-get-image-lambda",
            function_name="download_image_lambda",
            description="Lambda function to Download image",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="download_image.handler",
            timeout=Duration.seconds(30),
            environment={
               "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": bucket.bucket_name                     
            },
        )

        table.grant_read_data(download_image_lambda)
        bucket.grant_read(download_image_lambda)


        delete_image_lambda = _lambda.Function(
            self,  
            f"{id}-delete-image-lambda",
            function_name="delete_image_lambda",
            description="Lambda function to Delete image",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="delete_image.handler",
            timeout=Duration.seconds(30),
            environment={
               "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": bucket.bucket_name                     
            },
        )

        table.grant_read_write_data(delete_image_lambda)
        bucket.grant_delete(delete_image_lambda)


        # API Resources
        images = api.root.add_resource("images")
        images.add_method("GET", apigw.LambdaIntegration(list_images_lambda))

        initiate = images.add_resource("initiate_upload")
        initiate.add_method("POST", apigw.LambdaIntegration(initiate_upload_lambda))

        image_id = images.add_resource("{imageId}")
        image_id.add_method("GET", apigw.LambdaIntegration(download_image_lambda))
        image_id.add_method("DELETE", apigw.LambdaIntegration(delete_image_lambda))