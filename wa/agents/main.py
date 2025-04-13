import datetime as dt
import logging
from dataclasses import dataclass

from duckduckgo_search import DDGS
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

import wa.dynamo as db

from . import math, todos

logger = logging.getLogger(__name__)


@dataclass
class State:
    todo: db.ToolTodo


Context = RunContext[State]


agent = Agent(
    result_type=str,
    deps_type=State,
    tools=[duckduckgo_search_tool(DDGS(), max_results=5)],
)


@agent.system_prompt
async def step_todos(ctx: Context) -> str:
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
async def agent_todos(ctx: Context, prompt: str) -> str:
    logger.info("agent_todos(%s)", ctx.deps.todo.id)
    result = await todos.agent.run(prompt, deps=ctx.deps.todo, model=ctx.model)
    return result.data


@agent.tool
async def agent_math(ctx: Context, prompt: str) -> float:
    logger.info("agent_math()")
    result = await math.agent.run(prompt, model=ctx.model)
    return result.data
