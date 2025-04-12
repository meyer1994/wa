import asyncio
import datetime as dt
import itertools
from typing import Any

from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pynamodb import attributes as attr
from pynamodb.models import MetaProtocol, Model

import wa.whats.models as models
from wa.config import Config


def _now() -> dt.datetime:
    """Utility function to get the current UTC time."""
    return dt.datetime.now(dt.UTC)


class WhatsAppItem(Model):
    class Meta(MetaProtocol):
        pass

    id = attr.UnicodeAttribute(hash_key=True, default="whatsapp:item")
    key = attr.UnicodeAttribute(range_key=True)
    timestamp = attr.UTCDateTimeAttribute(default=_now)
    data = attr.MapAttribute[str, Any](default=dict)
    type = attr.DiscriminatorAttribute()

    async def asave(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save)


class WhatsAppMessage(WhatsAppItem, discriminator="whatsapp:item:message"):
    id = attr.UnicodeAttribute(hash_key=True, default="whatsapp:item:message")

    @staticmethod
    def from_model(m: models.MessageObject) -> "WhatsAppMessage":
        data = m.model_dump(mode="json")
        return WhatsAppMessage(key=m.id, timestamp=m.timestamp, data=data)


class WhatsAppStatus(WhatsAppItem, discriminator="whatsapp:item:status"):
    id = attr.UnicodeAttribute(hash_key=True, default="whatsapp:item:status")

    @staticmethod
    def from_model(model: models.StatusObject) -> "WhatsAppStatus":
        data = model.model_dump(mode="json")
        return WhatsAppStatus(key=model.id, timestamp=model.timestamp, data=data)


ModelRequestAdapter = TypeAdapter(ModelRequest)
ModelResponseAdapter = TypeAdapter(ModelResponse)


class Message(Model):
    class Meta(MetaProtocol):
        pass

    from_ = attr.UnicodeAttribute(hash_key=True)
    timestamp = attr.UTCDateTimeAttribute(range_key=True, default=_now)
    data = attr.MapAttribute[str, Any](default=dict)
    agent = attr.MapAttribute[str, Any](default=dict)
    type = attr.DiscriminatorAttribute()

    @property
    def model_messages(self) -> list[ModelMessage]:
        messages: list[ModelMessage] = []
        for i in self.agent["messages"]:
            if i["kind"] == "response":
                messages.append(ModelResponseAdapter.validate_python(i))
            elif i["kind"] == "request":
                messages.append(ModelRequestAdapter.validate_python(i))
            else:
                raise ValueError(f"Unknown message kind: {i['kind']}")
        return messages

    @model_messages.setter
    def model_messages(self, data: list[ModelMessage]):
        messages: list[dict[str, Any]] = []
        for i in data:
            if i.kind == "response":
                msg = ModelResponseAdapter.dump_python(i, mode="json")
                messages.append(msg)
            elif i.kind == "request":
                msg = ModelRequestAdapter.dump_python(i, mode="json")
                messages.append(msg)
            else:
                raise ValueError(f"Unknown message kind: {i.kind}")
        self.agent["messages"] = messages

    def latest(self, limit: int = 10) -> list[ModelMessage]:
        query = self.query(hash_key=self.from_, limit=limit, scan_index_forward=False)
        messages = itertools.chain.from_iterable(i.model_messages for i in query)
        return list(messages)

    async def alatest(self, limit: int = 10) -> list[ModelMessage]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.latest, limit)

    async def asave(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save)


class MessageText(Message, discriminator="wa:message:text"):
    @property
    def body(self) -> str:
        data = self.data.as_dict()
        return data["text"]["body"]

    @staticmethod
    def from_model(model: models.MessageObject) -> "MessageText":
        if model.type != "text":
            raise ValueError("Message type is not text")
        data = model.model_dump(mode="json")
        return MessageText(from_=model.from_, timestamp=model.timestamp, data=data)


class MessageImage(Message, discriminator="wa:message:image"):
    @property
    def image(self) -> models.ImageObject:
        data = self.data.as_dict()
        return models.ImageObject.model_validate(data)

    @staticmethod
    def from_model(model: models.MessageObject) -> "MessageImage":
        if model.type != "image":
            raise ValueError("Message type is not image")
        data = model.model_dump(mode="json")
        return MessageImage(from_=model.from_, timestamp=model.timestamp, data=data)


def init(cfg: Config):
    Message.Meta.table_name = cfg.DYNAMO_DB_TABLE_MESSAGES
    WhatsAppItem.Meta.table_name = cfg.DYNAMO_DB_TABLE_EVENTS

    if cfg.AWS_ENDPOINT_URL:
        Message.Meta.host = cfg.AWS_ENDPOINT_URL
        WhatsAppItem.Meta.host = cfg.AWS_ENDPOINT_URL
