import logging
import math

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry

logger = logging.getLogger(__name__)


agent: Agent[None, str] = Agent(result_type=str)


@agent.system_prompt
async def system(*args, **kwargs) -> str:
    return """
    You help with math problems.
    
    Available functions:
    - add(a, b): Adds two numbers together
    - subtract(a, b): Subtracts the second number from the first
    - multiply(a, b): Multiplies two numbers together
    - divide(a, b): Divides the first number by the second
    - sin(a): Returns the sine of a number in radians
    """


@agent.tool_plain
async def add(a: float, b: float) -> float:
    """
    Adds two numbers together.

    Args:
        a (float): The first number to add
        b (float): The second number to add

    Returns:
        float: The sum of a and b

    Example:
        >>> add(2.5, 3.7)
        6.2
    """
    logger.info(f"Adding {a} and {b}")
    return a + b


@agent.tool_plain
async def subtract(a: float, b: float) -> float:
    """
    Subtracts the second number from the first.

    Args:
        a (float): The number to subtract from (minuend)
        b (float): The number to subtract (subtrahend)

    Returns:
        float: The difference between a and b

    Example:
        >>> subtract(5.0, 2.3)
        2.7
    """
    logger.info(f"Subtracting {b} from {a}")
    return a - b


@agent.tool_plain
async def multiply(a: float, b: float) -> float:
    """
    Multiplies two numbers together.

    Args:
        a (float): The first factor
        b (float): The second factor

    Returns:
        float: The product of a and b

    Example:
        >>> multiply(4.0, 2.5)
        10.0
    """
    logger.info(f"Multiplying {a} and {b}")
    return a * b


@agent.tool_plain
async def divide(a: float, b: float) -> float:
    """
    Divides the first number by the second.

    Args:
        a (float): The dividend (number to be divided)
        b (float): The divisor (number to divide by)

    Returns:
        float: The quotient of a divided by b

    Raises:
        ModelRetry: If b is zero (division by zero is not allowed)

    Example:
        >>> divide(10.0, 2.0)
        5.0
    """
    logger.info(f"Dividing {a} by {b}")
    if b == 0:
        raise ModelRetry("Cannot divide by zero")
    return a / b


@agent.tool_plain
async def sin(a: float) -> float:
    """
    Returns the sine of a number.

    Args:
        a (float): The angle in radians

    Returns:
        float: The sine of the angle

    Example:
        >>> sin(math.pi/2)
        1.0
    """
    logger.info(f"Sine of {a}")
    return math.sin(a)
