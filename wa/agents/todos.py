import io

from pydantic_ai import Agent, RunContext

import wa.dynamo as db

Context = RunContext[db.ToolTodo]

agent: Agent[db.ToolTodo, str] = Agent()


@agent.system_prompt
async def system_prompt(ctx: Context) -> str:
    return "You help manage todo lists."


@agent.tool
async def create_todo(ctx: Context, title: str, completed: bool = False) -> str:
    """
    Appends a new todo item to the list.

    Args:
        title: The title of the todo item.
        completed: Whether the todo item is initially completed (defaults to False).
    """
    item = ctx.deps.add_item(title, completed)
    return "\n".join(
        [
            "Created todo:",
            f"{item.title=}",
            f"{item.index=}",
            f"{item.completed=}",
        ]
    )


@agent.tool
async def mark_todo(ctx: Context, index: int, completed: bool = True) -> str:
    """
    Marks a todo item as complete or incomplete.

    Args:
        index: The index of the todo item to complete.
        completed: Whether the todo item is completed (defaults to True).
    """
    items = (i for i in ctx.deps.data.items if i.index == index)
    item = next(items, None)

    if item is None:
        return f"Error: Todo item with index {index} not found."

    item.completed = completed

    return "\n".join(
        [
            f"Marked todo as {completed=}:",
            f"{item.title=}",
            f"{item.index=}",
            f"{item.completed=}",
        ]
    )


@agent.tool
async def remove_todo(ctx: Context, index: int) -> str:
    """
    Removes a todo item.

    Args:
        index: The index of the todo item to remove.
    """
    items = (i for i in ctx.deps.data.items if i.index == index)
    item = next(items, None)

    if item is None:
        return f"Error: Todo item with index {index} not found."

    item = ctx.deps.remove_item(index)

    return "\n".join(
        [
            "Removed todo:",
            f"{item.title=}",
            f"{item.index=}",
            f"{item.completed=}",
        ]
    )


@agent.tool
async def list_todos(ctx: Context) -> str:
    """Lists all todo items."""
    if not ctx.deps.data.items:
        return "The todo list is currently empty."

    # Sort items by index for consistent ordering
    ctx.deps.data.items.sort(key=lambda x: x.index)

    with io.StringIO() as sio:
        sio.write("Current Todo List:\n")
        for item in ctx.deps.data.items:
            sio.write("=====\n")
            sio.write(f"{item.title=}\n")
            sio.write(f"{item.index=}\n")
            sio.write(f"{item.completed=}\n")
        return sio.getvalue()


@agent.tool
async def count_todos(ctx: Context) -> str:
    """Counts all todo items."""
    count = len(ctx.deps.data.items)
    return f"There are {count} todo items."
