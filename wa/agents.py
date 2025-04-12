import logging
import math
from dataclasses import dataclass

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
    UserContent,
)
from pydantic_ai.models.openai import OpenAIModel

logger = logging.getLogger(__name__)


def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    logger.info(f"Adding {a} and {b}")
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    logger.info(f"Subtracting {b} from {a}")
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    logger.info(f"Multiplying {a} and {b}")
    return a * b


def divide(a: float, b: float) -> float:
    """Divides the first number by the second."""
    logger.info(f"Dividing {a} by {b}")
    if b == 0:
        raise ModelRetry("Cannot divide by zero")
    return a / b


def sin(a: float) -> float:
    """Returns the sine of a number."""
    logger.info(f"Sine of {a}")
    return math.sin(a)


SYSTEM_PROMPT = """
# Persona

You are a helpful math assistant

## Output Format

The output should aways be PLAIN TEXT. You are allowed to use the following
formatting syntax:

*bold* -> for bold text
_italic_ -> for italic text
~strikethrough~ -> for strikethrough text
```text``` -> for monospace text

YOU MUST NOT USE ANY OTHER FORMATTING SYNTAX.
YOU MUST NOT ESCAPE OUTPUT: eg. write `(` not `\\(`
"""


@dataclass
class Agent:
    agent: PydanticAgent[None, str]

    def run(self, prompt: str | list[UserContent], history: list[ModelMessage]):
        system = ModelRequest(parts=[SystemPromptPart(SYSTEM_PROMPT)])
        messages: list[ModelMessage] = [system, *history]
        return self.agent.run(user_prompt=prompt, message_history=messages)


def build_agent(model: OpenAIModel) -> Agent:
    return Agent(
        agent=PydanticAgent(
            model=model,
            result_type=str,
            tools=[add, subtract, multiply, divide, sin],
            system_prompt=SYSTEM_PROMPT,
        ),
    )
