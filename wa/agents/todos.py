import logging

from pydantic_ai import Agent, RunContext

import wa.dynamo as db

logger = logging.getLogger(__name__)


agent = Agent(
    result_type=str,
    deps_type=db.ToolTodo,
    system_prompt="You help with todo lists.",
)


Context = RunContext[db.ToolTodo]


@agent.tool
async def create_todo(ctx: Context, title: str, completed: bool = False) -> str:
    """Creates a new todo item and returns its index."""
    index = len(ctx.deps.data.items)
    item = db.ToolTodoItem(index=index, title=title, completed=completed)
    ctx.deps.data.items.append(item)
    await ctx.deps.asave()
    await ctx.deps.arefresh()
    return f"Todo {item.index} created."


@agent.tool
async def complete_todo(ctx: Context, index: int):
    """Completes a todo item and returns the item."""
    item = ctx.deps.data.items[index]
    item.completed = True
    await ctx.deps.asave()
    await ctx.deps.arefresh()
    return f"Todo {index} completed."


@agent.tool
async def remove_todo(ctx: Context, index: int):
    """Removes a todo item and returns the item."""
    ctx.deps.data.items.pop(index)
    await ctx.deps.asave()
    await ctx.deps.arefresh()
    return f"Todo {index} removed."


@agent.tool
async def list_todos(ctx: Context):
    """Lists all todo items and returns them."""
    result = ["Here are your todos:", ""]

    for item in ctx.deps.data.items:
        result.append(f"{item.index=}")
        result.append(f"{item.title=}")
        result.append(f"{item.completed=}")
        result.append("")

    return "\n".join(result)
