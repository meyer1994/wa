import logging
from typing import Annotated

import pydantic_ai
import pydantic_ai.models
import pydantic_ai.models.openai
from fastapi import Depends

from wa.config import Config
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
