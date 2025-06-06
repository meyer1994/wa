from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DEBUG: bool = False
    """Enable debug mode. Sends errors back to the sender"""

    WHATSAPP_VERIFY_TOKEN: str
    """The token used to verify/subscribe to the webhook"""

    WHATSAPP_ACCESS_TOKEN: str
    """The access token used to send messages: `Authorization: Bearer <token>`"""

    WHATSAPP_SENDER_ID: str
    """The sender WhatsApp id used to send messages. Not the phone number."""

    WHATSAPP_SENDER_NUMBER: str
    """The sender phone number used to send messages"""

    WHATSAPP_APP_SECRET: str
    """The app secret used to verify webhooks"""

    OPENAI_API_KEY: str
    """OpenAI API key"""

    DYNAMO_DB_TABLE_MESSAGES: str
    """DynamoDB table name for sent/received messages"""

    DYNAMO_DB_TABLE_EVENTS: str
    """DynamoDB table name for WhatsApp events"""

    DYNAMO_DB_TABLE_TOOLS: str
    """DynamoDB table name for tools"""

    HELICONE_API_KEY: str
    """Helicone API key"""

    GEMINI_API_KEY: str
    """Google Gemini API key"""

    DYNAMO_DB_HOST: str | None = None
    """DynamoDB host. Used for local development"""

    AWS_S3_BUCKET_RAG: str
    """S3 bucket name for RAG"""

    AWS_ENDPOINT_URL: str | None = None
    """AWS endpoint URL. Used for local development"""


DepConfig = Annotated[Config, Depends(lambda: Config())]
