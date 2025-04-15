import asyncio
import datetime as dt
import io
import logging
from dataclasses import dataclass
from typing import Annotated

from croniter import croniter
from pydantic import AfterValidator, BaseModel, Field
from pydantic_ai import Agent, RunContext

import wa.dynamo as db
import wa.whats.models as models

logger = logging.getLogger(__name__)


def _after_validator(v: str) -> str:
    """
    Validates if a given string is a valid cron expression.

    Args:
        v (str): The cron expression string to validate

    Returns:
        str: The validated cron expression

    Raises:
        ValueError: If the cron expression is invalid
    """
    if not croniter.is_valid(v):
        raise ValueError(f"Invalid cron expression: {v}")
    return v


class CronItem(BaseModel):
    """
    Represents a cron job item with its complete state and schedule information.

    Attributes:
        index (int): The unique index identifier of the cron job
        name (str): The human-readable name of the cron job
        description (str): Detailed description of the cron job's purpose
        cron (str): The cron expression defining the job's schedule (validated)
        last_run (datetime | None): Timestamp of the last execution, None if never run
        next_run (datetime): Timestamp of the next scheduled execution
        status (CronJob.Status): Current status of the job (PENDING, RUNNING, etc.)
    """

    index: Annotated[int, Field(description="The index of the cron job.")]
    name: Annotated[str, Field(description="The name of the cron job.")]
    description: Annotated[str, Field(description="The description of the cron job.")]
    cron: Annotated[
        str,
        Field(description="The cron expression of the cron job."),
        AfterValidator(_after_validator),
    ]
    last_run: Annotated[
        dt.datetime | None, Field(description="The last time the cron job was run.")
    ]
    next_run: Annotated[
        dt.datetime, Field(description="The next time the cron job will run.")
    ]
    status: Annotated[
        db.CronJob.Status,
        Field(
            description="The status of the cron job.", default=db.CronJob.Status.PENDING
        ),
    ]


Result = CronItem | list[CronItem] | None | int


@dataclass
class State:
    cron: db.ToolCron
    message: models.MessageObject


Context = RunContext[State]

agent = Agent(deps_type=State)


@agent.system_prompt
def system_prompt(ctx: Context):
    logger.info("system_prompt(%s)", ctx.deps.cron.id)
    return """You help with managing cron jobs"""


@agent.tool
async def create_cron(ctx: Context, name: str, description: str, cron: str) -> str:
    """
    Create a new cron job

    Args:
        name (str): The name of the cron job
        description (str): The description of the cron job
        cron (str): The cron expression of the cron job

    Returns:
        str: The cron job that was created
    """
    logger.info("create_cron(%s): %s", ctx.deps.cron.id, cron)
    now = dt.datetime.now(dt.UTC)
    iter = croniter(cron, now)

    job = db.CronJob(
        id=ctx.deps.cron.id,
        index=len(ctx.deps.cron.data.items),
        cron=cron,
        next_run=iter.get_next(dt.datetime),
        data={"name": name, "description": description},
    )

    await job.asave()
    ctx.deps.cron.data.items.append(
        db.ToolCronItem(
            index=len(ctx.deps.cron.data.items),
            name=name,
            description=description,
            cron=cron,
        )
    )

    return "\n".join(
        [
            "Cron job created:",
            f"- {name=}",
            f"- {description=}",
            f"- {cron=}",
            f"- {job.next_run=}",
        ]
    )


@agent.tool
async def fetch_crons(ctx: Context) -> str:
    """Fetch existing cron jobs"""
    logger.info("fetch_crons(%s)", ctx.deps.cron.id)
    idxs = [item.index for item in ctx.deps.cron.data.items]
    futs = [db.CronJob.aget(ctx.deps.cron.id, idx) for idx in idxs]
    jobs = await asyncio.gather(*futs)

    with io.StringIO() as sio:
        for item, job in zip(ctx.deps.cron.data.items, jobs):
            logger.debug("cronJob(%s): %s", job.id, job.status)
            sio.write(
                "CronJob: "
                f"- {item.index=} "
                f"- {item.name=} "
                f"- {item.description=} "
                f"- {item.cron=} "
                f"- {job.last_run=} "
                f"- {job.next_run=} "
                f"- {job.status=}\n"
            )
        return sio.getvalue()


@agent.tool
async def delete_cron(ctx: Context, index: int) -> str | None:
    """
    Delete a cron job by its index

    Args:
        index (int): The index of the cron job to delete

    Returns:
        str | None: A message confirming the deletion or None if job not found
    """
    logger.info("delete_cron(%s): %s", ctx.deps.cron.id, index)

    if index >= len(ctx.deps.cron.data.items):
        return None

    job = await db.CronJob.aget(ctx.deps.cron.id, index)
    if not job:
        return None

    job_name = ctx.deps.cron.data.items[index].name
    await job.adelete()
    ctx.deps.cron.data.items.pop(index)

    for i, item in enumerate(ctx.deps.cron.data.items):
        if item.index > index:
            item.index -= 1

    return "\n".join(
        [
            "Cron job deleted:",
            f"- {job_name=}",
            f"- {index=}",
        ]
    )


@agent.tool
async def count_crons(ctx: Context) -> str:
    """
    Count the total number of cron jobs

    Returns:
        str: A message with the total count of cron jobs
    """
    logger.info("count_crons(%s)", ctx.deps.cron.id)
    return f"Total number of cron jobs: {len(ctx.deps.cron.data.items)}"


@agent.tool
async def remove_all_crons(ctx: Context) -> str:
    """
    Remove all existing cron jobs

    Returns:
        str: A message confirming the deletion of all cron jobs
    """
    logger.info("remove_all_crons(%s)", ctx.deps.cron.id)

    if not ctx.deps.cron.data.items:
        return "No cron jobs to remove"

    count = len(ctx.deps.cron.data.items)

    futs = [
        db.CronJob.aget(ctx.deps.cron.id, item.index)
        for item in ctx.deps.cron.data.items
    ]
    jobs = await asyncio.gather(*futs)

    await asyncio.gather(*[job.adelete() for job in jobs if job])
    ctx.deps.cron.data.items.clear()

    return f"Successfully removed {count} cron job{'s' if count != 1 else ''}"


@agent.tool
async def fetch_status(ctx: Context, index: int) -> str | None:
    """
    Fetch the status of a cron job by its index

    Args:
        index (int): The index of the cron job to fetch the status of

    Returns:
        str | None: The status of the cron job or None if the index is out of bounds
    """
    logger.info("fetch_status(%s): %s", ctx.deps.cron.id, index)

    if index >= len(ctx.deps.cron.data.items):
        return None

    job = await db.CronJob.aget(ctx.deps.cron.id, index)
    return job.status
