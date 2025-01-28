import asyncio
import functools
from typing import TypeVar, Callable, Awaitable

# Type variables for the function's input arguments and return type
R = TypeVar("R")  # Return type of the synchronous function
P = TypeVar("P")  # Positional arguments
K = TypeVar("K")  # Keyword arguments


def async_wrapper(func: Callable[..., R]) -> Callable[..., Awaitable[R]]:
    """
    Wraps a synchronous function to be executed in a separate thread.

    :param func: The synchronous function to wrap.
    :return: Asynchronous wrapper function.
    """
    if not callable(func):
        raise ValueError("The provided object is not callable.")

    if asyncio.iscoroutinefunction(func):
        raise ValueError("The provided function is already a coroutine function.")

    @functools.wraps(func)
    async def wrapper(*args: P, **kwargs: K) -> R:
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper
