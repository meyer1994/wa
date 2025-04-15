#!/usr/bin/env python3
from aws_cdk import App, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct

from wa.config import Config


def dynamo_graph_widget(table: dynamodb.Table) -> cloudwatch.GraphWidget:
    return cloudwatch.GraphWidget(
        title=f"Capacity - {table.table_name}",
        left=[
            table.metric_consumed_read_capacity_units(),
            table.metric_consumed_write_capacity_units(),
        ],
        right=[
            table.metric_successful_request_latency(
                unit=cloudwatch.Unit.MILLISECONDS,
                dimensions_map={
                    "TableName": table.table_name,
                    "Operation": "GetItem",
                },
            ),
            table.metric_successful_request_latency(
                unit=cloudwatch.Unit.MILLISECONDS,
                dimensions_map={
                    "TableName": table.table_name,
                    "Operation": "PutItem",
                },
            ),
            table.metric_successful_request_latency(
                unit=cloudwatch.Unit.MILLISECONDS,
                dimensions_map={
                    "TableName": table.table_name,
                    "Operation": "UpdateItem",
                },
            ),
            table.metric_successful_request_latency(
                unit=cloudwatch.Unit.MILLISECONDS,
                dimensions_map={
                    "TableName": table.table_name,
                    "Operation": "Query",
                },
            ),
            table.metric_successful_request_latency(
                unit=cloudwatch.Unit.MILLISECONDS,
                dimensions_map={
                    "TableName": table.table_name,
                    "Operation": "Scan",
                },
            ),
        ],
        width=8,
    )


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

        t_tools = dynamodb.Table(
            self,
            id=f"{id}-table-tools",
            table_name=f"{id}-table-tools",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="tool",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        t_cron = dynamodb.Table(
            self,
            id=f"{id}-table-cron",
            table_name=f"{id}-table-cron",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="index",
                type=dynamodb.AttributeType.NUMBER,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        bucket = s3.Bucket(
            self,
            f"{id}-data-bucket",
            bucket_name=f"{id}-data-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=False,
        )

        # Create Lambda function for FastAPI with Mangum adapter
        function = lambda_.Function(
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
                # dynamo
                "DYNAMO_DB_TABLE_EVENTS": t_events.table_name,
                "DYNAMO_DB_TABLE_MESSAGES": t_messages.table_name,
                "DYNAMO_DB_TABLE_TOOLS": t_tools.table_name,
                "DYNAMO_DB_TABLE_CRON": t_cron.table_name,
                # s3
                "AWS_S3_BUCKET_RAG": bucket.bucket_name,
                # helicone
                "HELICONE_API_KEY": cfg.HELICONE_API_KEY,
                # whatsapp
                "WHATSAPP_SENDER_ID": cfg.WHATSAPP_SENDER_ID,
                "WHATSAPP_SENDER_NUMBER": cfg.WHATSAPP_SENDER_NUMBER,
                "WHATSAPP_ACCESS_TOKEN": cfg.WHATSAPP_ACCESS_TOKEN,
                "WHATSAPP_VERIFY_TOKEN": cfg.WHATSAPP_VERIFY_TOKEN,
                "WHATSAPP_APP_SECRET": cfg.WHATSAPP_APP_SECRET,
                # openai
                "OPENAI_API_KEY": cfg.OPENAI_API_KEY,
                # gemini
                "GEMINI_API_KEY": cfg.GEMINI_API_KEY,
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

        t_messages.grant_read_write_data(function)
        t_events.grant_read_write_data(function)
        t_tools.grant_read_write_data(function)
        t_cron.grant_read_write_data(function)
        bucket.grant_read_write(function)

        # Create API Gateway
        api = apigw.LambdaRestApi(
            self,
            f"{id}-api",
            rest_api_name=f"{id}-api",
            handler=function,
            proxy=True,
            # deploy
            deploy=True,
            retain_deployments=False,
            # logs
            cloud_watch_role=True,
            cloud_watch_role_removal_policy=RemovalPolicy.DESTROY,
            # deploy
            deploy_options=apigw.StageOptions(
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                # debugging
                metrics_enabled=True,
                data_trace_enabled=True,
                # logs
                logging_level=apigw.MethodLoggingLevel.INFO,
                access_log_destination=apigw.LogGroupLogDestination(
                    log_group=logs.LogGroup(
                        self,
                        f"{id}-api-logs",
                        log_group_name=f"{id}-api-logs",
                        retention=logs.RetentionDays.THREE_DAYS,
                        removal_policy=RemovalPolicy.DESTROY,
                    ),
                ),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
            ),
        )

        api.apply_removal_policy(RemovalPolicy.DESTROY)

        stage = apigw.Stage.from_stage_attributes(
            self,
            f"{id}-api-stage",
            rest_api=api,
            stage_name="prod",
        )

        # undocument hack to be able to delete the log group. api gateway only
        # creates the log group on the first request. if the log group is
        # already created, it just uses it. this is the only way to assign a
        # retention policy to the execution logs of the api gateway
        log = logs.LogGroup(
            self,
            f"{id}-api-execution-logs",
            log_group_name=f"API-Gateway-Execution-Logs_{api.rest_api_id}/{stage.stage_name}",
            retention=logs.RetentionDays.THREE_DAYS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self,
            f"{id}-dashboard",
            dashboard_name=f"{id}-dashboard",
        )

        # Row 1 - Each call to `add_widgets` adds a new row to the dashboard
        dashboard.add_widgets(
            # Total Requests
            cloudwatch.GraphWidget(
                title="Requests",
                left=[api.metric_count()],
                width=8,
            ),
            # Total Errors
            cloudwatch.GraphWidget(
                title="Errors",
                left=[api.metric_client_error(), api.metric_server_error()],
                width=8,
            ),
            # Latency
            cloudwatch.GraphWidget(
                title="Latency",
                left=[api.metric_latency(), api.metric_integration_latency()],
                width=8,
            ),
        )

        # Row 2
        dashboard.add_widgets(
            dynamo_graph_widget(t_messages),
            dynamo_graph_widget(t_events),
            dynamo_graph_widget(t_tools),
        )

        # Row 3
        dashboard.add_widgets(
            # Logs
            cloudwatch.LogQueryWidget(
                title="Logs",
                log_group_names=[log.log_group_name],
                query_lines=[
                    "fields @timestamp, @message, @logStream, @log",
                    "sort @timestamp desc",
                    "limit 100",
                ],
                width=24,
            )
        )


app = App()
cfg = Config()  # type: ignore
WhatsAppStack(app, "wa", cfg)
app.synth()
