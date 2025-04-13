import datetime as dt
import logging
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

import wa.dynamo as db

from . import math, todos

logger = logging.getLogger(__name__)


@dataclass
class State:
    todo: db.ToolTodo


Context = RunContext[State]


agent = Agent(result_type=str, deps_type=State)


@agent.system_prompt
async def step_todos(ctx: Context) -> str:
    now = dt.datetime.now(dt.UTC)
    now = now.isoformat()

    return f"""
    Current time: {now}

    You help with todo lists.
    You help with math problems.
    """


@agent.tool
async def agent_todos(ctx: Context, prompt: str) -> str:
    logger.info("agent_todos(%s)", ctx.deps.todo.id)
    result = await todos.agent.run(
        prompt,
        deps=ctx.deps.todo,
        model=ctx.model,
        message_history=ctx.messages,
    )
    ctx.messages.extend(result.new_messages())
    return result.data


@agent.tool
async def agent_math(ctx: Context, prompt: str) -> float:
    logger.info("agent_math()")
    result = await math.agent.run(
        prompt,
        model=ctx.model,
        message_history=ctx.messages,
    )
    ctx.messages.extend(result.new_messages())
    return result.data
