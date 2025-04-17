import datetime as dt
import logging
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

import wa.dynamo as db

from . import log, math, todos

logger = logging.getLogger(__name__)


@dataclass
class State:
    todo: db.ToolTodo
    log: db.ToolLog


Context = RunContext[State]
agent: Agent[State, str] = Agent()


@agent.system_prompt
async def system_prompt(_: Context) -> str:
    now = dt.datetime.now(dt.UTC)
    now = now.isoformat()

    return f"""
    Current time: {now}

    You help with todo lists, math problems, and maintaining a logbook.
    Your goal is to respond to the user's request, potentially using tools to
    modify or query the todo list, perform math calculations, maintain a logbook,
    or search the web.

    DO NOT RETURN MARKDOWN, ONLY TEXT.

    You are allowed to format your text using ONLY the following tags:

    - `*TEXT*` for bold text
    - `_TEXT_` for italic text
    - `~TEXT~` for strikethrough text
    """


@agent.tool
async def tool_todos(ctx: Context, prompt: str) -> str:
    """
    Helps with todos. Currently has the following tools:

    - create_todo(title: str): Creates a new todo item.
    - remove_todo(index: int): Removes a todo item.
    - mark_todo(index: int): Marks a todo item as done.
    - list_todos(): Lists all todo items.
    - count_todos(): Counts all todo items.
    """
    await ctx.deps.todo.arefresh()
    result = await todos.agent.run(prompt, deps=ctx.deps.todo, model=ctx.model)
    await ctx.deps.todo.asave()
    return result.data


@agent.tool
async def tool_math(ctx: Context, prompt: str) -> str | float:
    """
    Helps with math problems. Currently has the following tools:

    - add(a: float, b: float): Adds two numbers together.
    - subtract(a: float, b: float): Subtracts two numbers.
    - multiply(a: float, b: float): Multiplies two numbers.
    - divide(a: float, b: float): Divides two numbers.
    - power(base: float, exponent: float): Raises a number to a power.
    - sqrt(number: float): Takes the square root of a number.
    - log(number: float): Takes the logarithm of a number.
    - log10(number: float): Takes the base-10 logarithm of a number.
    - sin(angle: float): Calculates the sine of an angle (in radians).
    - cos(angle: float): Calculates the cosine of an angle (in radians).
    - tan(angle: float): Calculates the tangent of an angle (in radians).
    """
    result = await math.agent.run(user_prompt=prompt, model=ctx.model)
    return result.data


@agent.tool
async def tool_log(ctx: Context, prompt: str) -> str:
    """
    Helps with maintaining a logbook. Currently has the following tools:

    - log_append(message: str): Adds a new entry to the logbook.
    - log_list(limit: int = 10): Lists recent log entries.
    - log_clear(): Clears all log entries.
    """
    await ctx.deps.log.arefresh()
    result = await log.agent.run(user_prompt=prompt, deps=ctx.deps.log, model=ctx.model)
    await ctx.deps.log.asave()
    return result.data
