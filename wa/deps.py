import logging
from dataclasses import dataclass
from typing import Annotated

import boto3
from fastapi import Body, Depends, Header, HTTPException, Request
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

import wa.agents as agents
from wa.blob import Store
from wa.config import Config
from wa.whats.client import WhatsApp
from wa.whats.models import Webhook

logger = logging.getLogger(__name__)


def dep_config() -> Config:
    return Config()  # type: ignore


DepConfig = Annotated[Config, Depends(dep_config)]


def dep_model(cfg: DepConfig) -> Model:
    if cfg.GEMINI_API_KEY:
        logger.info("Using Gemini model")
        return GeminiModel(
            model_name="gemini-2.0-flash",
            provider=GoogleGLAProvider(api_key=cfg.GEMINI_API_KEY),
        )

    logger.info("Using OpenAI model")
    return OpenAIModel(
        model_name="gpt-4o-mini",
        provider=OpenAIProvider(
            openai_client=AsyncOpenAI(
                api_key=cfg.OPENAI_API_KEY,
                base_url="https://oai.helicone.ai/v1",
                default_headers={"Helicone-Auth": f"Bearer {cfg.HELICONE_API_KEY}"},
            )
        ),
    )


DepModel = Annotated[Model, Depends(dep_model)]


def dep_agent():
    return agents.agent


DepAgent = Annotated[Agent[agents.State, str], Depends(dep_agent)]


def dep_whatsapp(cfg: DepConfig):
    return WhatsApp(
        access_token=cfg.WHATSAPP_ACCESS_TOKEN,
        sender_id=cfg.WHATSAPP_SENDER_ID,
        verify_token=cfg.WHATSAPP_VERIFY_TOKEN,
    )


DepWhatsApp = Annotated[WhatsApp, Depends(dep_whatsapp)]


@dataclass
class WebhookContext:
    whats: DepWhatsApp
    request: Request
    config: DepConfig
    signature: Annotated[str, Header(alias="x-hub-signature-256")]
    body: Annotated[Webhook, Body()]


_WebhookContext = Annotated[WebhookContext, Depends(WebhookContext)]


async def dep_webhook(ctx: _WebhookContext):
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


def dep_store(cfg: DepConfig):
    s3 = boto3.resource("s3", endpoint_url=cfg.AWS_ENDPOINT_URL)
    bucket = s3.Bucket(cfg.AWS_S3_BUCKET_RAG)
    return Store(bucket=bucket)


DepStore = Annotated[Store, Depends(dep_store)]
