import os
from aws_cdk import Stack, Duration, aws_apigateway as apigw, aws_lambda as _lambda, aws_iam as iam, aws_logs
from aws_cdk.aws_lambda_python_alpha import PythonFunction, PythonLayerVersion
from constructs import Construct
from aws_cdk import Duration

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, table, bucket, **kwargs):
        super().__init__(scope, id, **kwargs)

        
        lambda_layer = PythonLayerVersion(
            self,
            id=f"{id}-lambda-layer",
            layer_version_name=f"{id}-lambda-layer",
            entry=os.path.join(os.path.dirname(__file__), "lambdas", "python_layer"),            
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11]            
        )
        
        def create_lambda_role(name, actions, resources):
            role = iam.Role(self, f"{name}Role", assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
            role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
            role.add_to_policy(iam.PolicyStatement(actions=actions, resources=resources))
            return role        
        
        initiate_upload_role = create_lambda_role("InitiateUpload",
                                            actions=["s3:PutObject", "s3:CreateMultipartUpload", "s3:AbortMultipartUpload"],
                                            resources=[f"{bucket.bucket_arn}/*"])
        
        initiate_upload_role.add_to_policy(iam.PolicyStatement(actions=["dynamodb:PutItem"], resources=[table.table_arn]))
  


        # Generate Pre Signed URL
        initiate_upload_lambda = PythonFunction(
            self,  
            f"{id}-initiate-upload-lambda",
            function_name="initiate_upload_lambda",
            description="Lambda function to Upload image",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            entry=os.path.join(os.path.dirname(__file__), "lambdas"),
            index="initiate_upload.py",            
            architecture=_lambda.Architecture.X86_64,
            layers=[lambda_layer],
            timeout=Duration.seconds(30),
            role=initiate_upload_role,
            log_retention=aws_logs.RetentionDays.SIX_MONTHS,
            memory_size=512,
            environment={
                "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": bucket.bucket_name               
            },
        )

        list_imag_role = create_lambda_role("ListImages",
                                    actions=["dynamodb:Query", "dynamodb:Scan"],
                                    resources=[table.table_arn, f"{table.table_arn}/index/*"])

        
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
            role=list_imag_role,
            environment={
                "IMAGES_TABLE": table.table_name                
            },
        )

        get_img_role = create_lambda_role("GetImage",
                        actions=["dynamodb:Query", "s3:GetObject", "s3:ListBucket"],
                        resources=[table.table_arn, f"{table.table_arn}/index/*", f"{bucket.bucket_arn}/*"])


        download_image_lambda = _lambda.Function(
            self,  
            f"{id}-get-image-lambda",
            function_name="download_image_lambda",
            description="Lambda function to Download image",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="download_image.handler",
            timeout=Duration.seconds(30),
            role=get_img_role,
            environment={
               "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": bucket.bucket_name                     
            },
        )

        delete_img_role = create_lambda_role( "DeleteImage",
                                        actions=["dynamodb:DeleteItem", "dynamodb:Query", "s3:DeleteObject"],
                                        resources=[table.table_arn, f"{bucket.bucket_arn}/*", f"{table.table_arn}/index/*"])



        delete_image_lambda = _lambda.Function(
            self,  
            f"{id}-delete-image-lambda",
            function_name="delete_image_lambda",
            description="Lambda function to Delete image",
            runtime=_lambda.Runtime.PYTHON_3_11,            
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "lambdas")),
            handler="delete_image.handler",
            timeout=Duration.seconds(30),
            role=delete_img_role,
            environment={
               "IMAGES_TABLE": table.table_name,
                "IMAGES_BUCKET": bucket.bucket_name                     
            },
        )


        # API Resources        
        api = apigw.RestApi(self,             
                            "ImagesApi",
                            rest_api_name="Images Service",
                            default_cors_preflight_options={
                                "allow_origins": apigw.Cors.ALL_ORIGINS,
                                "allow_methods": apigw.Cors.ALL_METHODS,
                            })  

        images = api.root.add_resource("images")
        images.add_method("POST", apigw.LambdaIntegration(initiate_upload_lambda))
        images.add_method("GET", apigw.LambdaIntegration(list_images_lambda))

        image_id = images.add_resource("{imageId}")
        image_id.add_method("GET", apigw.LambdaIntegration(download_image_lambda))
        image_id.add_method("DELETE", apigw.LambdaIntegration(delete_image_lambda))