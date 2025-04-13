import logging
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition

import wa.dynamo as db

logger = logging.getLogger(__name__)


Context = RunContext[db.ToolTodo]


class TodoItem(BaseModel):
    """Represents a todo item."""

    index: Annotated[int, Field(description="The index of the todo item.")]
    title: Annotated[str, Field(description="The title of the todo item.")]
    completed: Annotated[bool, Field(description="Whether the todo item is completed.")]


Result = TodoItem | list[TodoItem] | None | int

agent: Agent[db.ToolTodo, Result] = Agent(
    result_type=Result,
    deps_type=db.ToolTodo,
    system_prompt="You help with todo lists.",
)


async def prepare(ctx: Context, tool: ToolDefinition):
    logger.info("prepare(%s)", ctx.deps.id)
    await ctx.deps.arefresh()
    return tool


@agent.tool(prepare=prepare)
async def create_todo(ctx: Context, title: str, completed: bool = False) -> TodoItem:
    """Appends a new todo item to the list and returns the item"""
    index = len(ctx.deps.data.items)
    item = db.ToolTodoItem(index=index, title=title, completed=completed)
    ctx.deps.data.items.append(item)
    await ctx.deps.asave()
    return TodoItem(index=index, title=title, completed=completed)


@agent.tool
async def complete_todo(ctx: Context, index: int) -> TodoItem | None:
    """Completes a todo item and returns the item, if it exists."""
    item = next((i for i in ctx.deps.data.items if i.index == index), None)

    if item is None:
        return None

    item.completed = True
    await ctx.deps.asave()
    return TodoItem(index=index, title=item.title, completed=True)


@agent.tool
async def remove_todo(ctx: Context, index: int) -> TodoItem | None:
    """Removes a todo item and returns the item, if it exists."""
    item = next((i for i in ctx.deps.data.items if i.index == index), None)

    if item is None:
        return None

    ctx.deps.data.items = [i for i in ctx.deps.data.items if i.index != index]
    await ctx.deps.asave()
    return TodoItem(index=index, title=item.title, completed=item.completed)


@agent.tool
async def list_todos(ctx: Context) -> list[TodoItem]:
    """Lists all todo items and returns them."""
    items = []
    for i in ctx.deps.data.items:
        item = TodoItem(index=int(i.index), title=i.title, completed=i.completed)
        items.append(item)
    return items


@agent.tool
async def count_todos(ctx: Context) -> int:
    """Counts all todo items and returns the number."""
    return len(ctx.deps.data.items)
