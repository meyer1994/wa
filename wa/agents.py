import logging
from typing import Annotated

from fastapi import Depends
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.models.openai import OpenAIModel

from wa.config import DepConfig

logger = logging.getLogger(__name__)


def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    logger.debug(f"Adding {a} and {b}")
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    logger.debug(f"Subtracting {b} from {a}")
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    logger.debug(f"Multiplying {a} and {b}")
    return a * b


def divide(a: float, b: float) -> float:
    """Divides the first number by the second."""
    logger.debug(f"Dividing {a} by {b}")
    if b == 0:
        raise ModelRetry("Cannot divide by zero")
    return a / b


def dep_model(cfg: DepConfig) -> OpenAIModel:
    return OpenAIModel(api_key=cfg.OPENAI_API_KEY, model_name="gpt-4o-mini")


DepModel = Annotated[OpenAIModel, Depends(dep_model)]


def dep_agent(model: DepModel):
    agent = Agent(
        model=model,
        result_type=str,
        system_prompt=(
            "You are a helpful math assistant that can perform basic calculations.\n"
            "When given a math problem, solve it step by step and provide the final result."
        ),
    )

    agent.tool_plain(add)
    agent.tool_plain(subtract)
    agent.tool_plain(multiply)
    agent.tool_plain(divide)

    return agent


DepAgent = Annotated[Agent[None, str], Depends(dep_agent)]
