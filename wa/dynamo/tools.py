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
    def fetch(cls, id: str) -> Self:
        item = cls(id=id, tool=cls.NAME)
        try:
            item.refresh()
            return item
        except DoesNotExist:
            return item

    @classmethod
    async def afetch(cls, id: str) -> Self:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.fetch, id)


class ToolTodoItem(attr.MapAttribute):
    index = attr.BooleanAttribute(default=False)
    title = attr.UnicodeAttribute()
    completed = attr.BooleanAttribute(default=False)


class ToolTodoState(attr.MapAttribute):
    items = attr.ListAttribute(default=list, of=ToolTodoItem)


class ToolTodo(Tool, discriminator="wa:tool:todo"):
    NAME = "TODO"

    data = ToolTodoState(default=ToolTodoState)

    async def create(self, title: str, completed: bool = False) -> ToolTodoItem:
        index = len(self.data.items)
        item = ToolTodoItem(index=index, title=title, completed=completed)
        self.data.items.append(item)
        await self.asave()
        return item

    async def complete(self, index: int) -> ToolTodoItem:
        item = self.data.items[index]
        item.completed = True
        await self.asave()
        return item

    async def remove(self, index: int) -> ToolTodoItem:
        item = self.data.items.pop(index)
        await self.asave()
        return item
