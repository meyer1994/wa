#!/usr/bin/env python3
from aws_cdk import App, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct

from wa.config import Config


class WhatsAppStack(Stack):
    def __init__(self, scope: Construct, id: str, cfg: Config, **kwargs) -> None:
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
            # meta
            f"{id}-function",
            function_name=f"{id}-function",
            # code
            handler="handler.handler",
            code=lambda_.Code.from_custom_command(
                output="dist/lambda.zip",
                command=["make", "clean", "build"],
            ),
            # runtine
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(10),
            memory_size=1024,
            environment={
                "DYNAMO_DB_TABLE_EVENTS": t_events.table_name,
                "DYNAMO_DB_TABLE_MESSAGES": t_messages.table_name,
                # whatsapp
                "WHATSAPP_SENDER_ID": cfg.WHATSAPP_SENDER_ID,
                "WHATSAPP_SENDER_NUMBER": cfg.WHATSAPP_SENDER_NUMBER,
                "WHATSAPP_ACCESS_TOKEN": cfg.WHATSAPP_ACCESS_TOKEN,
                "WHATSAPP_VERIFY_TOKEN": cfg.WHATSAPP_VERIFY_TOKEN,
                "WHATSAPP_APP_SECRET": cfg.WHATSAPP_APP_SECRET,
                # openai
                "OPENAI_API_KEY": cfg.OPENAI_API_KEY,
            },
            # debugging
            profiling=True,  # not supported in docker image function
            tracing=lambda_.Tracing.ACTIVE,
            # logs
            log_group=logs.LogGroup(
                self,
                f"{id}-function-logs",
                log_group_name=f"{id}-function",
                retention=logs.RetentionDays.THREE_DAYS,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        t_messages.grant_read_write_data(lambda_function)
        t_events.grant_read_write_data(lambda_function)

        # Create API Gateway
        api = apigw.LambdaRestApi(
            self,
            f"{id}-api",
            rest_api_name=f"{id}-api",
            handler=lambda_function,
            proxy=True,
            # deploy
            deploy=True,
            retain_deployments=True,
            # logs
            cloud_watch_role=True,
            cloud_watch_role_removal_policy=RemovalPolicy.DESTROY,
        )

        api.apply_removal_policy(RemovalPolicy.DESTROY)

        stage = apigw.Stage.from_stage_attributes(
            self,
            f"{id}-api-stage",
            rest_api=api,
            stage_name="prod",
        )

        # undocument hack to be able to delete the log group. api gateway only
        # creates the log group on the first request. if the log group is already
        # created, it just uses it. this is the only way to assign a retention policy
        # to the execution logs of the api gateway
        log = logs.LogGroup(
            self,
            f"{id}-api-logs",
            log_group_name=f"API-Gateway-Execution-Logs_{api.rest_api_id}/{stage.stage_name}",
            retention=logs.RetentionDays.THREE_DAYS,
            removal_policy=RemovalPolicy.DESTROY,
        )


app = App()
cfg = Config()  # type: ignore
WhatsAppStack(app, "wa", cfg)
app.synth()
