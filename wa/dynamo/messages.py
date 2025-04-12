import asyncio
import datetime as dt
import itertools
from typing import Any

from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pynamodb import attributes as attr
from pynamodb.models import MetaProtocol, Model

import wa.whats.models as models


def _now() -> dt.datetime:
    """Utility function to get the current UTC time."""
    return dt.datetime.now(dt.UTC)


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


class MessageDocument(Message, discriminator="wa:message:document"):
    @property
    def document(self) -> models.DocumentObject:
        data = self.data.as_dict()
        return models.DocumentObject.model_validate(data)

    @staticmethod
    def from_model(model: models.MessageObject) -> "MessageDocument":
        if model.type != "document":
            raise ValueError("Message type is not document")
        data = model.model_dump(mode="json")
        return MessageDocument(from_=model.from_, timestamp=model.timestamp, data=data)
