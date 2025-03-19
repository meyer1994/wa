from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    WHATSAPP_VERIFY_TOKEN: str
    """The token used to verify/subscribe to the webhook"""
    WHATSAPP_ACCESS_TOKEN: str
    """The access token used to send messages"""
    WHATSAPP_SENDER_ID: str
    """The sender ID used to send messages"""
    WHATSAPP_SENDER_NUMBER: str
    """The sender number used to send messages"""
    WHATSAPP_RECIPIENT_NUMBER: str
    """The recipient number used to send messages"""

    OPENAI_API_KEY: str
    """The API key used to send messages"""


DepConfig = Annotated[Config, Depends(lambda: Config())]
