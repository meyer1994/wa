import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic_ai import Agent
from pydantic_ai.messages import DocumentUrl, ImageUrl, UserContent
from pydantic_ai.models import Model

import wa.deps as deps
import wa.dynamo as db
import wa.whats.models as models
from wa.agents import State
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
    agent: Agent[State, str]
    model: Model
    whats: WhatsApp
    store: Store

    async def on_message(self, data: models.MessageObject) -> db.WhatsAppMessage:
        logger.info("on_message(%s): %s", data.id, data.type)
        logger.debug("%s", data.model_dump_json())
        item = db.WhatsAppMessage.from_model(data)
        await item.asave()
        return item

    async def on_status(self, data: models.StatusObject) -> db.WhatsAppStatus:
        logger.info("on_status(%s): %s", data.id, data.status)
        logger.debug("%s", data.model_dump_json())
        item = db.WhatsAppStatus.from_model(data)
        await item.asave()
        return item

    async def on_text(self, data: models.TextMessage):
        logger.info("on_text(%s): %s", data.id, data.text)
        logger.debug("%s", data.model_dump_json())

        message = db.MessageText.from_model(data)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                self.whats.react(
                    data.from_,
                    data.id,
                    self.whats.EMOJI_THINKING,
                )
            )

            history = await tg.create_task(message.alatest())

        tool_todo = await db.ToolTodo.afetch(data.from_)
        logger.info(f"{tool_todo.data=}")

        context = State(todo=tool_todo)

        result = await self.agent.run(
            user_prompt=message.body,
            message_history=history,
            deps=context,
            model=self.model,
        )
        message.model_messages = result.new_messages()

        for msg in result.new_messages():
            for part in msg.parts:
                logger.info("part: %s", part)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(message.asave())
            tg.create_task(self.whats.reply(data.from_, data.id, result.data))

        return result

    async def on_image(self, data: models.ImageMessage):
        logger.info("on_image(%s): %s", data.id, data.image.sha256)
        logger.debug("%s", data.model_dump_json())

        message = db.MessageImage.from_model(data)

        async with asyncio.TaskGroup() as tg:
            t_media = tg.create_task(self.whats.media(data.image.id))
            t_history = tg.create_task(message.alatest())

        media = await t_media
        history = await t_history

        *_, suffix = data.image.mime_type.split("/")
        assert suffix, f"Invalid mime type: {data.image.mime_type}"

        key = "/".join(["whatsapp", "user", data.from_, "media", data.image.id])
        key = f"{key}.{suffix}"

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.store.save(key, media, data.image.mime_type))
            url = await tg.create_task(self.store.presigned(key))

        REPLACE_HOST = "3d8f15ab012cae6a929ddfcf9c5ae32d.serveo.net"
        url = url.replace("localhost:4566", REPLACE_HOST)

        prompt: list[UserContent] = [ImageUrl(url=url)]
        if data.image.caption:
            prompt.append(data.image.caption)

        result = await self.agent.run(
            user_prompt=prompt,
            message_history=history,
            model=self.model,
        )
        message.model_messages = result.new_messages()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(message.asave())
            tg.create_task(self.whats.reply(data.from_, data.id, result.data))

        return result

    async def on_document(self, data: models.DocumentMessage):
        logger.info("on_document(%s): %s", data.id, data.document.id)
        logger.debug("%s", data.model_dump_json())

        message = db.MessageDocument.from_model(data)

        async with asyncio.TaskGroup() as tg:
            t_media = tg.create_task(self.whats.media(data.document.id))
            t_history = tg.create_task(message.alatest())

        media = await t_media
        history = await t_history

        *_, suffix = data.document.mime_type.split("/")
        assert suffix, f"Invalid mime type: {data.document.mime_type}"

        key = "/".join(["whatsapp", "user", data.from_, "media", data.document.id])
        key = f"{key}.{suffix}"

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.store.save(key, media, data.document.mime_type))
            url = await tg.create_task(self.store.presigned(key))

        # stop here as it does not work with openai
        # return

        REPLACE_HOST = "3d8f15ab012cae6a929ddfcf9c5ae32d.serveo.net"
        url = url.replace("localhost:4566", REPLACE_HOST)

        prompt: list[DocumentUrl | str] = [DocumentUrl(url=url)]
        if data.document.caption:
            prompt.append(data.document.caption)

        result = await self.agent.run(
            user_prompt=prompt,
            message_history=history,
            model=self.model,
        )

        message.model_messages = result.new_messages()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(message.asave())
            tg.create_task(self.whats.reply(data.from_, data.id, result.data))

        return result


def dep_handler(
    agent: deps.DepAgent,
    model: deps.DepModel,
    whats: deps.DepWhatsApp,
    store: deps.DepStore,
) -> Handler:
    return Handler(agent=agent, model=model, whats=whats, store=store)


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
            if msg.type == "document":
                tg.create_task(ctx.handler.on_document(msg), name="on_document")

    return {"success": True}
