import datetime as dt
import itertools
import uuid
from typing import Any

from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pynamodb import attributes as attr
from pynamodb.models import Model

import wa.models as models


class WhatsAppItem(Model):
    class Meta:
        table_name = "whatsapp-events"
        host = "http://localhost:8001"

    id = attr.UnicodeAttribute(
        hash_key=True,
        default=lambda: "whatsapp:%s" % uuid.uuid4(),
    )

    timestamp = attr.UTCDateTimeAttribute(
        range_key=True,
        default=lambda: dt.datetime.now(dt.UTC),
    )

    data = attr.MapAttribute[str, Any]()

    type = attr.DiscriminatorAttribute()


class WhatsAppMessage(WhatsAppItem, discriminator="MESSAGE"):
    id = attr.UnicodeAttribute(
        hash_key=True,
        default=lambda: "whatsapp:message:%s" % uuid.uuid4(),
    )

    @staticmethod
    def from_model(model: models.MessageObject) -> "WhatsAppMessage":
        return WhatsAppMessage(
            id=f"whatsapp:message:{model.id}",
            timestamp=model.timestamp,
            data=model.model_dump(mode="json"),
        )

    def as_model(self) -> models.MessageObject:
        return models.MessageObjectAdapter.validate_python(
            {
                "id": f"whatsapp:message:{self.id}",
                "timestamp": self.timestamp,
                **self.data,
            }
        )


class WhatsAppStatus(WhatsAppItem, discriminator="STATUS"):
    id = attr.UnicodeAttribute(
        hash_key=True,
        default=lambda: "whatsapp:status:%s" % uuid.uuid4(),
    )

    @staticmethod
    def from_model(model: models.StatusObject) -> "WhatsAppStatus":
        return WhatsAppStatus(
            id=f"whatsapp:status:{model.id}",
            timestamp=model.timestamp,
            data=model.model_dump(mode="json"),
        )

    def as_model(self) -> models.StatusObject:
        return models.StatusObject.model_validate(
            {
                "id": f"whatsapp:status:{self.id}",
                "timestamp": self.timestamp,
                **self.data,
            }
        )


ModelRequestAdapter = TypeAdapter(ModelRequest)
ModelResponseAdapter = TypeAdapter(ModelResponse)


class Message(Model):
    class Meta:
        table_name = "messages"
        host = "http://localhost:8001"

    from_ = attr.UnicodeAttribute(hash_key=True)
    timestamp = attr.UTCDateTimeAttribute(range_key=True)
    data = attr.MapAttribute[str, Any]()

    agent = attr.ListAttribute[dict[str, Any]](default=list)

    type = attr.DiscriminatorAttribute()

    def set_messages(self, data: list[ModelMessage]):
        messages: list[dict[str, Any]] = []
        for i in data:
            if i.kind == "response":
                msg = ModelResponseAdapter.dump_python(i, mode="json")
                messages.append(msg)
            elif i.kind == "request":
                msg = ModelRequestAdapter.dump_python(i, mode="json")
                messages.append(msg)
        self.agent = messages


class MessageText(Message, discriminator="TEXT"):
    def latest_messages(self, limit: int = 10) -> list[ModelMessage]:
        query = self.query(hash_key=self.from_, limit=limit, scan_index_forward=False)
        messages = itertools.chain.from_iterable(i.get_messages() for i in query)
        return list(messages)

    def get_messages(self) -> list[ModelMessage]:
        messages: list[ModelMessage] = []
        for i in self.agent:
            if i["kind"] == "response":
                messages.append(ModelResponseAdapter.validate_python(i))
            elif i["kind"] == "request":
                messages.append(ModelRequestAdapter.validate_python(i))
        return messages

    @property
    def body(self) -> str:
        data = self.data.as_dict()
        return data["text"]["body"]

    @staticmethod
    def from_model(model: models.MessageObject) -> "MessageText":
        if model.type != "text":
            raise ValueError("Message type is not text")

        return MessageText(
            from_=model.from_,
            timestamp=model.timestamp,
            data=model.model_dump(mode="json"),
        )
