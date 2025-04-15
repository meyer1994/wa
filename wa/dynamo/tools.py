import asyncio
import logging
from typing import Any, Self

from pynamodb import attributes as attr
from pynamodb.exceptions import DoesNotExist
from pynamodb.models import MetaProtocol, Model

logger = logging.getLogger(__name__)


class Tool(Model):
    class Meta(MetaProtocol):
        pass

    id = attr.UnicodeAttribute(hash_key=True)
    tool = attr.UnicodeAttribute(range_key=True)
    data = attr.MapAttribute[str, Any](default=dict)
    type = attr.DiscriminatorAttribute()

    @property
    def NAME(self) -> str:
        raise NotImplementedError("Subclass must implement this method")

    async def asave(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save)

    @classmethod
    def upsert(cls, id: str) -> Self:
        item = cls(id=id, tool=cls.NAME)
        try:
            item.refresh()
            return item
        except DoesNotExist:
            return item

    @classmethod
    async def aupsert(cls, id: str) -> Self:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.upsert, id)

    async def arefresh(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.refresh)


class ToolTodoItem(attr.MapAttribute):
    index = attr.NumberAttribute()
    title = attr.UnicodeAttribute()
    completed = attr.BooleanAttribute(default=False)


class ToolTodoState(attr.MapAttribute):
    items = attr.ListAttribute(default=list, of=ToolTodoItem)


class ToolTodo(Tool, discriminator="wa:tool:todo"):
    NAME = "TODO"

    data = ToolTodoState(default=ToolTodoState)


class ToolCronItem(attr.MapAttribute):
    index = attr.NumberAttribute()
    name = attr.UnicodeAttribute()
    description = attr.UnicodeAttribute()
    cron = attr.UnicodeAttribute()


class ToolCronState(attr.MapAttribute):
    items = attr.ListAttribute(default=list, of=ToolCronItem)


class ToolCron(Tool, discriminator="wa:tool:cron"):
    NAME = "CRON"

    data = ToolCronState(default=ToolCronState)
