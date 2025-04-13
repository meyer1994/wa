import logging
import math

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry

logger = logging.getLogger(__name__)


agent = Agent(
    result_type=float,
    system_prompt="You help with math problems.",
)


@agent.tool_plain
def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    logger.info(f"Adding {a} and {b}")
    return a + b


@agent.tool_plain
def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    logger.info(f"Subtracting {b} from {a}")
    return a - b


@agent.tool_plain
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    logger.info(f"Multiplying {a} and {b}")
    return a * b


@agent.tool_plain
def divide(a: float, b: float) -> float:
    """Divides the first number by the second."""
    logger.info(f"Dividing {a} by {b}")
    if b == 0:
        raise ModelRetry("Cannot divide by zero")
    return a / b


@agent.tool_plain
def sin(a: float) -> float:
    """Returns the sine of a number."""
    logger.info(f"Sine of {a}")
    return math.sin(a)
