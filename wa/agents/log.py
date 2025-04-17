import datetime as dt
import logging
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, RootModel
from pydantic_ai import Agent, RunContext

import wa.dynamo as db

logger = logging.getLogger(__name__)

Context = RunContext[db.ToolLog]


class Item(BaseModel):
    """
    A log entry.
    """

    timestamp: Annotated[
        dt.datetime,
        Field(description="The timestamp of the log entry"),
    ]
    message: Annotated[
        str,
        Field(description="The message of the log entry"),
    ]


class Collection(RootModel[list[Item]]):
    """
    An ordered collection of log entries.
    """

    root: Annotated[
        list[Item],
        Field(description="The list of log entries"),
        AfterValidator(lambda x: sorted(x, key=lambda i: i.timestamp, reverse=True)),
    ]


agent: Agent[db.ToolLog, Item | Collection] = Agent(
    deps_type=db.ToolLog,
    result_type=Item | Collection,  # type: ignore
    result_tool_name="agent_logs",
)


@agent.system_prompt
async def system_prompt(_: Context) -> str:
    return """
    You are a helpful assistant that can help with logbook entries.
    """


@agent.tool
async def log_append(ctx: Context, message: str) -> Item:
    """Add a new entry to the logbook.

    Args:
        prompt: The message to be logged. This can be any text that you want to
            record in the logbook. The entry will be timestamped automatically
            with the current UTC time.

    Returns:
        The Item model containing the timestamp and message of the newly added entry.
    """
    entry = ctx.deps.append_entry(message)
    return Item(timestamp=entry.timestamp, message=entry.message)


@agent.tool
async def log_list(ctx: Context, limit: int = 10) -> Collection:
    """List recent log entries.

    Args:
        limit: Maximum number of entries to return (defaults to 10).
            The entries are sorted by timestamp in descending order,
            so the most recent entries are returned first.

    Returns:
        A Collection model containing a list of Item models, each with a timestamp
        and message. If no entries are found, returns an empty Collection.
    """
    items = []
    for i in ctx.deps.data.items:
        items.append(Item(timestamp=i.timestamp, message=i.message))

    return Collection(root=items)


@agent.tool
async def log_clear(ctx: Context) -> Collection:
    """Clear all log entries from the logbook.

    Args:
        None: This function takes no arguments.

    Returns:
        An empty Collection model, confirming that all entries have been cleared.
    """
    ctx.deps.clear_entries()
    return Collection(root=[])
