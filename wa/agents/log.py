import io
import logging

from pydantic_ai import Agent, RunContext

import wa.dynamo as db

logger = logging.getLogger(__name__)

Context = RunContext[db.ToolLog]


agent: Agent[db.ToolLog, str] = Agent(deps_type=db.ToolLog)


@agent.system_prompt
async def system_prompt(_: Context) -> str:
    return """
    You are a helpful assistant that can help with logbook entries.
    """


@agent.tool
async def log_append(ctx: Context, message: str) -> str:
    """Add a new entry to the logbook.

    Args:
        prompt: The message to be logged. This can be any text that you want to
            record in the logbook. The entry will be timestamped automatically
            with the current UTC time.

    Returns:
        A message confirming that the entry has been added with the following format:

        ```
        {entry.timestamp=}
        {entry.message=}
        ```
    """
    logger.info("log_append(%s): %s", ctx.deps.id, message)
    entry = ctx.deps.append_entry(message)
    return "\n".join(
        [
            "Appended entry:",
            f"{entry.timestamp=}",
            f"{entry.message=}",
        ]
    )


@agent.tool
async def log_list(ctx: Context, limit: int = 10) -> str:
    """List recent log entries.

    Args:
        limit: Maximum number of entries to return (defaults to 10).
            The entries are sorted by timestamp in descending order,
            so the most recent entries are returned first.

    Returns:
        A message containing a list of log entries with the following format:

        ```
        {entry.timestamp=}
        {entry.message=}
        ===

        {entry.timestamp=}
        {entry.message=}
        ===
        # etc...
        ```
    """
    logger.info("log_list(%s)", ctx.deps.id)

    with io.StringIO() as f:
        f.write("Logbook entries:\n")

        for i, entry in enumerate(ctx.deps.data.items):
            if i >= limit:
                return f.getvalue()

            f.write(f"{entry.timestamp=}\n")
            f.write(f"{entry.message=}\n")
            f.write("===\n")

        return f.getvalue()


@agent.tool
async def log_count(ctx: Context) -> str:
    """Count the number of log entries in the logbook.

    Returns:
        A message containing the number of log entries in the logbook.
    """
    logger.info("log_count(%s)", ctx.deps.id)
    return f"There are {len(ctx.deps.data.items)} log entries."


@agent.tool
async def log_clear(ctx: Context) -> str:
    """Clear all log entries from the logbook.

    Args:
        None: This function takes no arguments.

    Returns:
        A message confirming that all entries have been cleared.
    """
    logger.info("log_clear(%s)", ctx.deps.id)
    ctx.deps.clear_entries()
    return "All entries have been cleared."
