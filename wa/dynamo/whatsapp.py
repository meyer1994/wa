import asyncio
import datetime as dt
from typing import Any

from pynamodb import attributes as attr
from pynamodb.models import MetaProtocol, Model

import wa.whats.models as models


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
