import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated

import pydantic_ai
from fastapi import APIRouter, Depends, HTTPException, Query

import wa.dynamo as db
import wa.whats.models as models
from wa import deps
from wa.store import Store
from wa.whats.client import WhatsApp

logger = logging.getLogger(__name__)
router = APIRouter()


@dataclass
class GetContext:
    whats: deps.DepWhatsApp
    hub_mode: Annotated[str, Query(alias="hub.mode")]
    hub_challenge: Annotated[int, Query(alias="hub.challenge")]
    hub_verify_token: Annotated[str, Query(alias="hub.verify_token")]


_GetContext = Annotated[GetContext, Depends()]


@router.get("/")
async def subscribe(ctx: _GetContext) -> int:
    if ctx.hub_mode != "subscribe":
        logger.error("Invalid hub mode: %s", ctx.hub_mode)
        raise HTTPException(status_code=400, detail="Invalid hub mode")
    if not ctx.whats.validate(ctx.hub_verify_token):
        logger.warning("Invalid verify token: %s", ctx.hub_verify_token)
        raise HTTPException(status_code=400, detail="Invalid verify token")
    return ctx.hub_challenge


@dataclass
class Handler:
    agent: pydantic_ai.Agent[None, str]
    whats: WhatsApp
    store: Store

    async def on_message(self, data: models.MessageObject) -> db.WhatsAppMessage:
        logger.info("on_message(%s): %s", data.id, data.type)
        logger.debug("%s", data.model_dump_json())
        item = db.WhatsAppMessage.from_model(data)
        item.save()
        return item

    async def on_status(self, data: models.StatusObject) -> db.WhatsAppStatus:
        logger.info("on_status(%s): %s", data.id, data.status)
        logger.debug("%s", data.model_dump_json())
        item = db.WhatsAppStatus.from_model(data)
        item.save()
        return item

    async def on_text(self, data: models.TextMessage) -> db.MessageText:
        logger.info("on_text(%s): %s", data.id, data.text)
        logger.debug("%s", data.model_dump_json())
        message = db.MessageText.from_model(data)
        history = message.latest()

        result = await self.agent.run(
            user_prompt=message.body,
            message_history=history,
        )

        message.model_messages = result.new_messages()
        await self.whats.reply(data.from_, data.id, result.data)
        message.save()
        return message

    async def on_image(self, data: models.ImageMessage):
        logger.info("on_image(%s): %s", data.id, data.image.sha256)
        logger.debug("%s", data.model_dump_json())
        media = await self.whats.media(data.image.id)
        key = "/".join(["whatsapp", "user", data.from_, "media", data.image.id])
        await self.store.save(key, media, data.image.mime_type)
        return key


def dep_handler(
    agent: deps.DepAgent,
    whats: deps.DepWhatsApp,
    store: deps.DepStore,
) -> Handler:
    return Handler(
        agent=agent,
        whats=whats,
        store=store,
    )


DepHandler = Annotated[Handler, Depends(dep_handler)]


@dataclass
class PostContext:
    handler: DepHandler
    data: deps.DepWebhook
    config: deps.DepConfig


_PostContext = Annotated[PostContext, Depends()]


@router.post("/")
async def receive(ctx: _PostContext) -> dict[str, bool]:
    for entry in ctx.data.entry:
        logger.info("receive(%s)", entry.id)
        logger.debug("%s", entry.model_dump_json())

    async with asyncio.TaskGroup() as tg:
        # store whatsapp messages
        for msg in ctx.data.messages():
            tg.create_task(ctx.handler.on_message(msg), name="on_message")
        # store whatsapp statuses
        for sts in ctx.data.statuses():
            tg.create_task(ctx.handler.on_status(sts), name="on_status")

        # process messages
        for msg in ctx.data.messages():
            if msg.type == "image":
                tg.create_task(ctx.handler.on_image(msg), name="on_image")
            if msg.type == "text":
                tg.create_task(ctx.handler.on_text(msg), name="on_text")

    return {"success": True}
