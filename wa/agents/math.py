import logging
import math

from pydantic_ai import Agent

logger = logging.getLogger(__name__)

agent: Agent[None, str] = Agent()


@agent.system_prompt
async def system_prompt(*args, **kwargs) -> str:
    return "You are a math expert."


@agent.tool_plain
async def add(a: float, b: float) -> str:
    """Adds two numbers together."""
    logger.info("add(%s, %s)", a, b)
    return f"{a} + {b} = {a + b}"


@agent.tool_plain
async def subtract(a: float, b: float) -> str:
    """Subtracts the second number from the first."""
    logger.info("subtract(%s, %s)", a, b)
    return f"{a} - {b} = {a - b}"


@agent.tool_plain
async def multiply(a: float, b: float) -> str:
    """Multiplies two numbers together."""
    logger.info("multiply(%s, %s)", a, b)
    return f"{a} * {b} = {a * b}"


@agent.tool_plain
async def divide(a: float, b: float) -> str:
    """
    Divides the first number by the second.
    Returns an error message string if the divisor is zero.
    """
    logger.info("divide(%s, %s)", a, b)
    if b == 0:
        # Return an error message instead of raising an exception
        return "Cannot divide by zero. Please provide a non-zero divisor."
    return f"{a} / {b} = {a / b}"


@agent.tool_plain
async def power(base: float, exponent: float) -> str:
    """Calculates the base raised to the power of the exponent."""
    logger.info("power(%s, %s)", base, exponent)
    # Consider edge cases like 0**0 or negative base with fractional exponent if needed
    try:
        return f"{base} ** {exponent} = {math.pow(base, exponent)}"
    except ValueError as e:
        # math.pow can raise ValueError (e.g., negative base to fractional power)
        logger.exception("Error in power function")
        return f"Mathematical error during exponentiation: {e}"


@agent.tool_plain
async def sqrt(number: float) -> str:
    """
    Calculates the square root of a number.
    Returns an error message string for negative input.
    """
    logger.info("sqrt(%s)", number)
    if number < 0:
        return "Cannot calculate the square root of a negative number."
    return f"{number} ** 0.5 = {math.sqrt(number)}"


@agent.tool_plain
async def log(number: float) -> str:
    """
    Calculates the natural logarithm (base e) of a number.
    Returns an error message string for non-positive input.
    """
    logger.info("log(%s)", number)
    if number <= 0:
        return "Cannot calculate the logarithm of a non-positive number."
    return f"log({number}) = {math.log(number)}"


@agent.tool_plain
async def log10(number: float) -> str:
    """
    Calculates the base-10 logarithm of a number.
    Returns an error message string for non-positive input.
    """
    logger.info("log10(%s)", number)
    if number <= 0:
        return "Cannot calculate the logarithm of a non-positive number."
    return f"log10({number}) = {math.log10(number)}"


@agent.tool_plain
async def sin(angle: float) -> str:
    """Calculates the sine of an angle (in radians)."""
    logger.info("sin(%s)", angle)
    return f"sin({angle}) = {math.sin(angle)}"


@agent.tool_plain
async def cos(angle: float) -> str:
    """Calculates the cosine of an angle (in radians)."""
    logger.info("cos(%s)", angle)
    return f"cos({angle}) = {math.cos(angle)}"


@agent.tool_plain
async def tan(angle: float) -> str:
    """
    Calculates the tangent of an angle (in radians).
    Returns an error message string for angles where tangent is undefined.
    """
    logger.info("tan(%s)", angle)
    # Check for angles where tan is undefined (e.g., pi/2 + k*pi)
    if math.isclose(math.cos(angle), 0):
        return "Tangent is undefined for this angle (cosine is zero)."
    return f"tan({angle}) = {math.tan(angle)}"
