import functools
import logging
from collections.abc import Callable
from typing import Any

from infrastructure.process_data.exceptions import InvalidRecordError

logger = logging.getLogger("ncbi_parsers")


def ncbi_logger(log_message: str):
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs) -> Any:
            try:
                return func(self, *args, **kwargs)

            except InvalidRecordError:
                logger.exception("%s Current form: %s %s", log_message, args, kwargs)
                raise

            except Exception:
                logger.exception("Unexpected Error happened.")
                raise

        return wrapped

    return wrapper
