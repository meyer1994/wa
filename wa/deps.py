import logging
from dataclasses import dataclass
from typing import Annotated

import boto3
from fastapi import Body, Depends, Header, HTTPException, Request
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from wa.config import Config
from wa.store import Store
from wa.whats.client import WhatsApp
from wa.whats.models import Webhook

logger = logging.getLogger(__name__)


def dep_config() -> Config:
    return Config()  # type: ignore


DepConfig = Annotated[Config, Depends(dep_config)]


def dep_agent(cfg: DepConfig) -> Agent[None, str]:
    return Agent(
        model=OpenAIModel(
            "gpt-4o-mini",
            provider=OpenAIProvider(api_key=cfg.OPENAI_API_KEY),
        ),
    )


def dep_whatsapp(cfg: DepConfig) -> WhatsApp:
    return WhatsApp(
        access_token=cfg.WHATSAPP_ACCESS_TOKEN,
        sender_id=cfg.WHATSAPP_SENDER_ID,
        verify_token=cfg.WHATSAPP_VERIFY_TOKEN,
    )


DepWhatsApp = Annotated[WhatsApp, Depends(dep_whatsapp)]
DepAgent = Annotated[Agent[None, str], Depends(dep_agent)]


@dataclass
class WebhookContext:
    whats: DepWhatsApp
    request: Request
    config: DepConfig
    signature: Annotated[str, Header(alias="x-hub-signature-256")]
    body: Annotated[Webhook, Body()]


_WebhookContext = Annotated[WebhookContext, Depends(WebhookContext)]


async def dep_webhook(ctx: _WebhookContext) -> Webhook:
    signature = ctx.signature.removeprefix("sha256=")
    secret = ctx.config.WHATSAPP_APP_SECRET
    body = await ctx.request.body()

    if not ctx.signature:
        logger.warning("Missing signature")
        raise HTTPException(status_code=400, detail="Missing signature")
    if not WhatsApp.verify(secret, signature, body):
        logger.warning("Invalid signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("Webhook verified")
    return ctx.body


DepWebhook = Annotated[Webhook, Depends(dep_webhook)]


def dep_store(cfg: DepConfig) -> Store:
    s3 = boto3.resource("s3", endpoint_url=cfg.AWS_ENDPOINT_URL)
    bucket = s3.Bucket(cfg.AWS_S3_BUCKET_RAG)
    return Store(bucket=bucket)


DepStore = Annotated[Store, Depends(dep_store)]
