#!/usr/bin/env python3
from aws_cdk import (
    App,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigw,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from constructs import Construct


class WhatsAppStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        t_messages = dynamodb.Table(
            self,
            id=f"{id}-table-messages",
            table_name=f"{id}-table-messages",
            partition_key=dynamodb.Attribute(
                name="from_",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        t_events = dynamodb.Table(
            self,
            id=f"{id}-table-events",
            table_name=f"{id}-table-events",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="key",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create Lambda function for FastAPI with Mangum adapter
        lambda_function = lambda_.Function(
            self,
            "WhatsAppFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset(".", exclude=["cdk.out", ".venv", ".git"]),
            handler="handler.handler",
            timeout=Duration.seconds(10),
            memory_size=1024,
            environment={
                "DYNAMO_DB_TABLE_EVENTS": t_events.table_name,
                "DYNAMO_DB_TABLE_MESSAGES": t_messages.table_name,
            },
        )

        # Grant Lambda function permissions to DynamoDB tables
        t_messages.grant_read_write_data(lambda_function)
        t_events.grant_read_write_data(lambda_function)

        # Create API Gateway
        api = apigw.LambdaRestApi(
            self,
            "WhatsAppApi",
            handler=lambda_function,
            proxy=True,  # Use proxy integration to pass all requests to the Lambda function
        )

        # Add API resources and methods
        webhook = api.root.add_resource("webhook")
        webhook.add_method("GET")  # For subscription verification
        webhook.add_method("POST")  # For receiving messages

        # Add optional CORS settings if needed
        webhook.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
        )


app = App()
WhatsAppStack(app, "WhatsAppStack")
app.synth()
