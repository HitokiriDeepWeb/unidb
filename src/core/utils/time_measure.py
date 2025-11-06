import functools
from collections.abc import Callable
from time import perf_counter
from typing import Any


def async_timed(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = perf_counter()
        print(f"Started {func.__name__} with {args}, {kwargs}")

        try:
            return await func(*args, **kwargs)

        finally:
            time_finished = perf_counter() - start
            print(f"Finished {func.__name__} in {time_finished:.4f} second(s)")

    return wrapper
