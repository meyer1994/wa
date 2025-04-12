import asyncio
import datetime as dt
from typing import Any

from pynamodb import attributes as attr
from pynamodb.models import MetaProtocol, Model

import wa.whats.models as models


def _now() -> dt.datetime:
    """Utility function to get the current UTC time."""
    return dt.datetime.now(dt.UTC)


class Tool(Model):
    class Meta(MetaProtocol):
        pass

    id = attr.UnicodeAttribute(hash_key=True)
    timestamp = attr.UTCDateTimeAttribute(range_key=True, default=_now)
    data = attr.MapAttribute[str, Any](default=dict)
    type = attr.DiscriminatorAttribute()

    async def asave(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save)


class ToolTodo(Tool, discriminator="wa:tool:todo"):
    @staticmethod
    def from_model(model: models.MessageObject) -> "ToolTodo":
        if model.type != "todo":
            raise ValueError("Message type is not todo")
        data = model.model_dump(mode="json")
        return ToolTodo(from_=model.from_, timestamp=model.timestamp, data=data)
