import logging
from dataclasses import dataclass
from typing import Annotated

import pydantic_ai
import pydantic_ai.models
import pydantic_ai.models.openai
from fastapi import Body, Depends, Header, HTTPException, Request

from wa.config import Config
from wa.models import Webhook
from wa.whatsapp import WhatsApp

logger = logging.getLogger(__name__)


def dep_config() -> Config:
    return Config()  # type: ignore


DepConfig = Annotated[Config, Depends(dep_config)]


def dep_agent(cfg: DepConfig) -> pydantic_ai.Agent[None, str]:
    return pydantic_ai.Agent(
        model=pydantic_ai.models.openai.OpenAIModel(
            model_name="gpt-4o-mini",
            api_key=cfg.OPENAI_API_KEY,
        ),
    )


def dep_whatsapp(cfg: DepConfig) -> WhatsApp:
    return WhatsApp(
        access_token=cfg.WHATSAPP_ACCESS_TOKEN,
        sender_id=cfg.WHATSAPP_SENDER_ID,
        verify_token=cfg.WHATSAPP_VERIFY_TOKEN,
    )


DepWhatsApp = Annotated[WhatsApp, Depends(dep_whatsapp)]
DepAgent = Annotated[pydantic_ai.Agent[None, str], Depends(dep_agent)]


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
