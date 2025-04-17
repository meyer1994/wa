import logging
import math

from pydantic_ai import Agent

logger = logging.getLogger(__name__)

agent: Agent[None, float | str] = Agent()


@agent.system_prompt
async def system_prompt(*args, **kwargs) -> str:
    return "You are a math expert."


@agent.tool_plain
async def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    logger.info(f"Adding {a} and {b}")
    return a + b


@agent.tool_plain
async def subtract(a: float, b: float) -> float:
    """Subtracts the second number from the first."""
    logger.info(f"Subtracting {b} from {a}")
    return a - b


@agent.tool_plain
async def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    logger.info(f"Multiplying {a} and {b}")
    return a * b


@agent.tool_plain
async def divide(a: float, b: float) -> float | str:
    """
    Divides the first number by the second.
    Returns an error message string if the divisor is zero.
    """
    logger.info(f"Dividing {a} by {b}")
    if b == 0:
        # Return an error message instead of raising an exception
        return "Cannot divide by zero. Please provide a non-zero divisor."
    return a / b


@agent.tool_plain
async def power(base: float, exponent: float) -> float | str:
    """Calculates the base raised to the power of the exponent."""
    logger.info(f"Calculating {base} raised to the power of {exponent}")
    # Consider edge cases like 0**0 or negative base with fractional exponent if needed
    try:
        return math.pow(base, exponent)
    except ValueError as e:
        # math.pow can raise ValueError (e.g., negative base to fractional power)
        logger.exception("Error in power function")
        return f"Mathematical error during exponentiation: {e}"


@agent.tool_plain
async def sqrt(number: float) -> float | str:
    """
    Calculates the square root of a number.
    Returns an error message string for negative input.
    """
    logger.info(f"Calculating the square root of {number}")
    if number < 0:
        return "Cannot calculate the square root of a negative number."
    return math.sqrt(number)


@agent.tool_plain
async def log(number: float) -> float | str:
    """
    Calculates the natural logarithm (base e) of a number.
    Returns an error message string for non-positive input.
    """
    logger.info(f"Calculating the natural logarithm of {number}")
    if number <= 0:
        return "Cannot calculate the logarithm of a non-positive number."
    return math.log(number)


@agent.tool_plain
async def log10(number: float) -> float | str:
    """
    Calculates the base-10 logarithm of a number.
    Returns an error message string for non-positive input.
    """
    logger.info(f"Calculating the base-10 logarithm of {number}")
    if number <= 0:
        return "Cannot calculate the logarithm of a non-positive number."
    return math.log10(number)


@agent.tool_plain
async def sin(angle: float) -> float:
    """Calculates the sine of an angle (in radians)."""
    logger.info(f"Calculating the sine of {angle} radians")
    return math.sin(angle)


@agent.tool_plain
async def cos(angle: float) -> float:
    """Calculates the cosine of an angle (in radians)."""
    logger.info(f"Calculating the cosine of {angle} radians")
    return math.cos(angle)


@agent.tool_plain
async def tan(angle: float) -> float | str:
    """
    Calculates the tangent of an angle (in radians).
    Returns an error message string for angles where tangent is undefined.
    """
    logger.info(f"Calculating the tangent of {angle} radians")
    # Check for angles where tan is undefined (e.g., pi/2 + k*pi)
    if math.isclose(math.cos(angle), 0):
        return "Tangent is undefined for this angle (cosine is zero)."
    return math.tan(angle)
