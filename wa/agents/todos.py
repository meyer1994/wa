import io
import logging

from pydantic_ai import Agent, RunContext

import wa.dynamo as db

logger = logging.getLogger(__name__)


Context = RunContext[db.ToolTodo]


agent = Agent(deps_type=db.ToolTodo)


@agent.system_prompt
async def system(*args, **kwargs) -> str:
    return "You help manage todo lists."


@agent.tool
async def create_todo(ctx: Context, title: str, completed: bool = False) -> str:
    """Create a new todo item and append it to the list.

    Args:
        - ctx (Context): The context object containing the todo list data.
        - title (str): The title/description of the todo item to create.
        - completed (bool, optional): Initial completion status of the todo
          item. Defaults to False.

    Returns:
        - str: A new todo item with the following attributes:
            - index: Integer position in the list
            - title: The provided title
            - completed: The completion status
    """
    logger.info("create_todo(%s): %s", ctx.deps.id, title)
    index = len(ctx.deps.data.items)
    item = db.ToolTodoItem(index=index, title=title, completed=completed)
    ctx.deps.data.items.append(item)
    return "\n".join(
        [
            "Todo created:",
            f"- {item.index=}",
            f"- {item.title=}",
            f"- {item.completed=}",
        ]
    )


@agent.tool
async def complete_todo(ctx: Context, index: int) -> str | None:
    """Mark a todo item as completed by its index.

    Args:
        - ctx (Context): The context object containing the todo list data.
        - index (int): The index of the todo item to complete.

    Returns:
        - str | None: The completed todo item if found, None if no item
          exists at the given index. When found, returns TodoItem with:
            - index: Original index
            - title: Original title
            - completed: Always True
    """
    logger.info("complete_todo(%s): %s", ctx.deps.id, index)
    item = next((i for i in ctx.deps.data.items if i.index == index), None)

    if item is None:
        return None

    item.completed = True
    return "\n".join(
        [
            "Todo completed:",
            f"- {item.index=}",
            f"- {item.title=}",
            f"- {item.completed=}",
        ]
    )


@agent.tool
async def remove_todo(ctx: Context, index: int) -> str | None:
    """Remove a todo item from the list by its index.

    Args:
        - ctx (Context): The context object containing the todo list data.
        - index (int): The index of the todo item to remove.

    Returns:
        - str | None: The removed todo item if found, None if no item
          exists at the given index. When found, returns the TodoItem with its
          original attributes before removal.
    """
    logger.info("remove_todo(%s): %s", ctx.deps.id, index)
    item = next((i for i in ctx.deps.data.items if i.index == index), None)

    if item is None:
        return None

    ctx.deps.data.items = [i for i in ctx.deps.data.items if i.index != index]
    return "\n".join(
        [
            "Todo removed:",
            f"- {item.index=}",
            f"- {item.title=}",
            f"- {item.completed=}",
        ]
    )


@agent.tool
async def list_todos(ctx: Context) -> str | None:
    """Retrieve all todo items in the list.

    Args:
        ctx (Context): The context object containing the todo list data.

    Returns:
        str: A list of all todo items. None if there are no todos.
    """
    logger.info("list_todos(%s)", ctx.deps.id)

    if len(ctx.deps.data.items) == 0:
        return None

    with io.StringIO() as sio:
        for i in sorted(ctx.deps.data.items, key=lambda x: x.index):
            sio.write(f"- {i.index=} {i.completed=} {i.title=}\n")

        return sio.getvalue()


@agent.tool
async def count_todos(ctx: Context) -> str:
    """Count the total number of todo items in the list.

    Args:
        - ctx (Context): The context object containing the todo list data.

    Returns:
        - int: The total number of todo items in the list.
    """
    logger.info("count_todos(%s)", ctx.deps.id)
    return f"Total todos: {len(ctx.deps.data.items)}"
