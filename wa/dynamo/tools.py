import asyncio
import datetime as dt
import logging
from typing import Any, Self

from pynamodb import attributes as attr
from pynamodb.exceptions import DoesNotExist
from pynamodb.models import MetaProtocol, Model

logger = logging.getLogger(__name__)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


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
    def fetch(cls, id: str) -> Self:
        item = cls(id=id, tool=cls.NAME)
        try:
            item.refresh()
            return item
        except DoesNotExist:
            item.save()
            return item

    @classmethod
    async def afetch(cls, id: str) -> Self:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.fetch, id)

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

    def add_item(self, title: str, completed: bool = False):
        self.data.items.append(
            ToolTodoItem(
                index=len(self.data.items),
                title=title,
                completed=completed,
            )
        )
        return self.data.items[-1]

    def remove_item(self, index: int):
        return self.data.items.pop(index)

    def complete_item(self, index: int):
        self.data.items[index].completed = True


class ToolLogItem(attr.MapAttribute):
    timestamp = attr.UTCDateTimeAttribute()
    message = attr.UnicodeAttribute()


class ToolLogState(attr.MapAttribute):
    items = attr.ListAttribute(default=list, of=ToolLogItem)


class ToolLog(Tool, discriminator="wa:tool:log"):
    NAME = "LOG"

    data = ToolLogState(default=ToolLogState)

    def append_entry(self, message: str):
        log = ToolLogItem(timestamp=_now(), message=message)
        self.data.items.append(log)
        return log

    def list_entries(self, limit: int = 10):
        self.data.items.sort(key=lambda x: x.timestamp, reverse=True)
        return self.data.items[:limit]

    def clear_entries(self):
        self.data.items = []
