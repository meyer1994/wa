import datetime as dt
import logging
from dataclasses import dataclass

from duckduckgo_search import DDGS
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.models import ModelSettings

import wa.dynamo as db
import wa.whats.models as models

from . import cron, math, todos

logger = logging.getLogger(__name__)


@dataclass
class State:
    """
    Represents the state for the main agent containing message and tool
    information.

    Attributes:
        message (models.MessageObject): The message object being processed
        todo (db.ToolTodo): The todo tool state
        cron (db.ToolCron): The cron tool state
    """

    message: models.MessageObject
    todo: db.ToolTodo
    cron: db.ToolCron


Context = RunContext[State]


agent = Agent(
    result_type=str,
    deps_type=State,
    tools=[
        duckduckgo_search_tool(DDGS(), max_results=2),
    ],
)


@agent.system_prompt
async def system(ctx: Context) -> str:
    now = dt.datetime.now(dt.UTC)
    now = now.isoformat()

    return f"""
    Current time: {now}

    You help with todo lists.
    You help with math problems.

    DO NOT RETURN MARKDOWN, ONLY TEXT.

    You are allowed to format your text using ONLY the following tags:

    - `*TEXT*` for bold text
    - `_TEXT_` for italic text
    - `~TEXT~` for strikethrough text
    """


@agent.tool
async def agent_todos(ctx: Context, prompt: str):
    """
    Handles todo list related operations through the todos agent.

    Tools:
        - create_todo: Create a new todo item
        - complete_todo: Complete a todo item
        - remove_todo: Remove a todo item
        - list_todos: List all todo items
        - count_todos: Count all todo items

    Returns:
        str: The result of processing the todo operation
    """
    logger.info("agent_todos(%s)", ctx.deps.todo.id)
    result = await todos.agent.run(
        prompt,
        deps=ctx.deps.todo,
        model=ctx.model,
        model_settings=ModelSettings(temperature=0.0),
    )
    await ctx.deps.todo.asave()
    return result.data


@agent.tool
async def agent_math(ctx: Context, prompt: str):
    """
    Handles mathematical calculations through the math agent.

    Tools:
        - add: Add two numbers
        - subtract: Subtract two numbers
        - multiply: Multiply two numbers
        - divide: Divide two numbers
        - sin: Calculate the sine of a number

    Returns:
        str: The result of the mathematical calculation
    """
    logger.info("agent_math()")
    result = await math.agent.run(
        prompt,
        model=ctx.model,
        model_settings=ModelSettings(temperature=0.0),
    )
    return result.data


@agent.tool
async def agent_cron(ctx: Context, prompt: str):
    """
    Handles one-off cron jobs manager. EG: every job is executed once and then
    deleted.

    Tools:
        - create_cron: Create a new cron job
        - fetch_crons: Fetch existing cron jobs
        - fetch_status: Fetch the status of a cron job
        - delete_cron: Delete a cron job
        - remove_all_crons: Remove all cron jobs
        - count_crons: Count all cron jobs

    Returns:
        str: The result of processing the cron job operation
    """
    logger.info("agent_cron(%s)", ctx.deps.cron.id)
    result = await cron.agent.run(
        prompt,
        deps=cron.State(cron=ctx.deps.cron, message=ctx.deps.message),
        model=ctx.model,
        model_settings=ModelSettings(temperature=0.0),
    )
    await ctx.deps.cron.asave()
    return result.data
